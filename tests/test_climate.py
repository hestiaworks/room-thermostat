from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.room_thermostat.config_flow import default_options
from custom_components.room_thermostat.const import (
    CONF_COOLER,
    CONF_HEATERS,
    CONF_TEMPERATURE_SENSOR,
    DOMAIN,
)


async def add_room(hass: HomeAssistant, **data) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bedroom",
        data={"name": "Bedroom", **data},
        options=default_options(),
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_a_room_offers_only_the_modes_it_can_actually_do(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_HEATERS: ["switch.bedroom_radiator"],
        },
    )
    state = hass.states.get("climate.bedroom")
    assert set(state.attributes["hvac_modes"]) == {"off", "heat"}


async def test_a_room_with_an_air_conditioner_offers_its_modes(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    hass.states.async_set(
        "climate.bedroom_ac",
        "off",
        {"fan_modes": ["auto", "low", "high"], "swing_modes": ["default", "full_swing"]},
    )
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
        },
    )
    state = hass.states.get("climate.bedroom")
    assert set(state.attributes["hvac_modes"]) == {"off", "cool", "dry", "fan_only"}


async def test_the_fan_and_swing_lists_are_mirrored_from_the_unit(hass: HomeAssistant):
    """Published rather than maintained, so a firmware change that adds a fan
    speed appears without a release here."""
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    hass.states.async_set(
        "climate.bedroom_ac",
        "off",
        {
            "fan_modes": ["auto", "low", "medium", "high"],
            "swing_modes": ["default", "full_swing", "fixed_upper"],
        },
    )
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
        },
    )
    state = hass.states.get("climate.bedroom")
    assert state.attributes["fan_modes"] == ["auto", "low", "medium", "high"]
    assert state.attributes["swing_modes"] == ["default", "full_swing", "fixed_upper"]


async def test_the_room_reads_its_own_sensors_not_the_units(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "26.2")
    hass.states.async_set("sensor.bedroom_humidity", "58")
    hass.states.async_set("climate.bedroom_ac", "off", {"current_temperature": 24.0})
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            "humidity_sensor": "sensor.bedroom_humidity",
            CONF_COOLER: "climate.bedroom_ac",
        },
    )
    state = hass.states.get("climate.bedroom")
    assert state.attributes["current_temperature"] == 26.2
    assert state.attributes["current_humidity"] == 58


async def test_asking_for_heat_opens_every_valve_in_the_room(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "18.0")
    hass.states.async_set("switch.radiator_a", "off")
    hass.states.async_set("switch.radiator_b", "off")
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_HEATERS: ["switch.radiator_a", "switch.radiator_b"],
        },
    )
    turn_on = async_mock_service(hass, "switch", "turn_on")
    async_mock_service(hass, "switch", "turn_off")

    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": "climate.bedroom", "temperature": 21.0},
        blocking=True,
    )
    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": "climate.bedroom", "hvac_mode": "heat"},
        blocking=True,
    )
    await hass.async_block_till_done()

    targets = {entity for call in turn_on for entity in call.data["entity_id"]}
    assert targets == {"switch.radiator_a", "switch.radiator_b"}


async def test_setting_a_fan_mode_forwards_to_the_unit(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    hass.states.async_set("climate.bedroom_ac", "off", {"fan_modes": ["auto", "high"]})
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
        },
    )
    # Not a mock service: replacing climate.set_fan_mode would swallow the
    # call to our own entity, which is in the same domain. Watch the bus.
    forwarded = []
    hass.bus.async_listen("call_service", lambda event: forwarded.append(event.data))

    await hass.services.async_call(
        "climate",
        "set_fan_mode",
        {"entity_id": "climate.bedroom", "fan_mode": "high"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert any(
        call["domain"] == "climate"
        and call["service"] == "set_fan_mode"
        and "climate.bedroom_ac" in str(call["service_data"].get("entity_id"))
        for call in forwarded
    )


async def test_the_temperature_limits_come_from_the_unit(hass: HomeAssistant):
    """Advertising 7 to 35 when the unit accepts 8 to 30 offers setpoints it
    would refuse — the same class of fault this integration exists to fix."""
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    hass.states.async_set(
        "climate.bedroom_ac", "off", {"min_temp": 8, "max_temp": 30}
    )
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
        },
    )
    state = hass.states.get("climate.bedroom")
    assert state.attributes["min_temp"] == 8
    assert state.attributes["max_temp"] == 30


async def test_a_room_with_no_unit_keeps_sensible_limits(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_HEATERS: ["switch.radiator"],
        },
    )
    state = hass.states.get("climate.bedroom")
    assert state.attributes["min_temp"] == 7
    assert state.attributes["max_temp"] == 35
