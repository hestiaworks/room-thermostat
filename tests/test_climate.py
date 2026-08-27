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


async def test_a_room_reports_one_kind_of_setpoint_at_a_time(hass: HomeAssistant):
    """Reporting a single target and a range together leaves the card unable
    to tell which control to show, and a setpoint sent to the wrong one is
    silently ignored."""
    hass.states.async_set("sensor.bedroom_temperature", "24.0")
    hass.states.async_set("climate.bedroom_ac", "off")
    hass.states.async_set("switch.radiator", "off")
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
            CONF_HEATERS: ["switch.radiator"],
        },
    )
    async_mock_service(hass, "switch", "turn_on")
    async_mock_service(hass, "switch", "turn_off")

    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": "climate.bedroom", "hvac_mode": "cool"},
        blocking=True,
    )
    await hass.async_block_till_done()
    single = hass.states.get("climate.bedroom").attributes
    assert single.get("temperature") is not None
    assert single.get("target_temp_low") is None
    assert single.get("target_temp_high") is None

    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": "climate.bedroom", "hvac_mode": "heat_cool"},
        blocking=True,
    )
    await hass.async_block_till_done()
    ranged = hass.states.get("climate.bedroom").attributes
    assert ranged.get("temperature") is None
    assert ranged.get("target_temp_low") is not None
    assert ranged.get("target_temp_high") is not None


async def test_the_room_reports_what_it_is_working_with(hass: HomeAssistant):
    """Diagnosing 'nothing happened' from outside means guessing at which
    entities the room actually holds and whether it can see them."""
    hass.states.async_set("sensor.bedroom_temperature", "24.2")
    hass.states.async_set("climate.bedroom_ac", "off")
    hass.states.async_set("switch.radiator_a", "off")
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
            CONF_HEATERS: ["switch.radiator_a", "switch.missing"],
        },
    )
    attributes = hass.states.get("climate.bedroom").attributes
    assert attributes["temperature_sensor"] == "sensor.bedroom_temperature"
    assert attributes["cooler"] == "climate.bedroom_ac"
    assert attributes["heaters"] == ["switch.radiator_a", "switch.missing"]
    assert attributes["heat_demand"] is False
    assert attributes["frost_protection"] is False
    # The one that matters when a room seems inert: a device it cannot see.
    assert attributes["unavailable_devices"] == ["switch.missing"]


async def test_a_radiator_valve_is_opened_with_valve_services(hass: HomeAssistant):
    """Radiator valves are valve entities, not switches. Assuming switches
    left the only selectable 'heaters' being things like an air conditioner's
    panel light."""
    hass.states.async_set("sensor.bedroom_temperature", "18.0")
    hass.states.async_set("valve.radiator_a", "closed")
    hass.states.async_set("valve.radiator_b", "closed")
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_HEATERS: ["valve.radiator_a", "valve.radiator_b"],
        },
    )
    opened = async_mock_service(hass, "valve", "open_valve")
    async_mock_service(hass, "valve", "close_valve")

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

    targets = {entity for call in opened for entity in call.data["entity_id"]}
    assert targets == {"valve.radiator_a", "valve.radiator_b"}


async def test_a_valve_already_open_is_left_alone(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "18.0")
    hass.states.async_set("valve.radiator_a", "open")
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_HEATERS: ["valve.radiator_a"],
        },
    )
    opened = async_mock_service(hass, "valve", "open_valve")
    async_mock_service(hass, "valve", "close_valve")

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
    assert opened == []


async def test_a_valve_still_travelling_is_not_told_again(hass: HomeAssistant):
    """A valve reports opening for minutes; re-commanding it every tick would
    fill the log without changing anything."""
    hass.states.async_set("sensor.bedroom_temperature", "18.0")
    hass.states.async_set("valve.radiator_a", "opening")
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_HEATERS: ["valve.radiator_a"],
        },
    )
    opened = async_mock_service(hass, "valve", "open_valve")
    async_mock_service(hass, "valve", "close_valve")

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
    assert opened == []


async def test_valves_and_switches_can_heat_the_same_room(hass: HomeAssistant):
    """A room may have a radiator valve and a relay-driven loop at once."""
    hass.states.async_set("sensor.bedroom_temperature", "18.0")
    hass.states.async_set("valve.radiator_a", "closed")
    hass.states.async_set("switch.floor_loop", "off")
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_HEATERS: ["valve.radiator_a", "switch.floor_loop"],
        },
    )
    opened = async_mock_service(hass, "valve", "open_valve")
    async_mock_service(hass, "valve", "close_valve")
    turned_on = async_mock_service(hass, "switch", "turn_on")
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

    assert {e for c in opened for e in c.data["entity_id"]} == {"valve.radiator_a"}
    assert {e for c in turned_on for e in c.data["entity_id"]} == {"switch.floor_loop"}


async def test_a_helper_can_stand_in_for_a_temperature_sensor(hass: HomeAssistant):
    """An input_number you can drag is how the deadband and the minimum times
    get exercised without waiting for a real room to change temperature."""
    hass.states.async_set("input_number.fake_room_temperature", "24.0")
    hass.states.async_set("valve.radiator_a", "closed")
    await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "input_number.fake_room_temperature",
            CONF_HEATERS: ["valve.radiator_a"],
        },
    )
    assert hass.states.get("climate.bedroom").attributes["current_temperature"] == 24.0

    opened = async_mock_service(hass, "valve", "open_valve")
    async_mock_service(hass, "valve", "close_valve")
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
    assert opened == []

    # Drag the helper below the target and the room must respond to it.
    hass.states.async_set("input_number.fake_room_temperature", "18.0")
    await hass.async_block_till_done()
    assert {e for c in opened for e in c.data["entity_id"]} == {"valve.radiator_a"}


async def test_an_inverted_valve_is_closed_to_let_heat_through(hass: HomeAssistant):
    """Thermal actuators come normally-open as well as normally-closed. On a
    normally-open valve, energising it shuts the radiator off."""
    hass.states.async_set("sensor.bedroom_temperature", "18.0")
    hass.states.async_set("valve.radiator_inverted", "open")
    entry = await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_HEATERS: ["valve.radiator_inverted"],
        },
    )
    hass.config_entries.async_update_entry(
        entry,
        options={**entry.options, "inverted_heaters": ["valve.radiator_inverted"]},
    )
    await hass.async_block_till_done()

    opened = async_mock_service(hass, "valve", "open_valve")
    closed = async_mock_service(hass, "valve", "close_valve")
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

    # Everything above may have emitted calls while the mode was still off.
    # Only what the loop does once it is heating is being asserted.
    opened.clear()
    closed.clear()
    hass.states.async_set("sensor.bedroom_temperature", "17.9")
    await hass.async_block_till_done()

    assert {e for c in closed for e in c.data["entity_id"]} == {"valve.radiator_inverted"}
    assert opened == []


async def test_a_room_can_mix_inverted_and_normal_valves(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "18.0")
    hass.states.async_set("valve.normal", "closed")
    hass.states.async_set("valve.inverted", "open")
    entry = await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_HEATERS: ["valve.normal", "valve.inverted"],
        },
    )
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, "inverted_heaters": ["valve.inverted"]}
    )
    await hass.async_block_till_done()

    opened = async_mock_service(hass, "valve", "open_valve")
    closed = async_mock_service(hass, "valve", "close_valve")
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

    # Everything above may have emitted calls while the mode was still off.
    # Only what the loop does once it is heating is being asserted.
    opened.clear()
    closed.clear()
    hass.states.async_set("sensor.bedroom_temperature", "17.9")
    await hass.async_block_till_done()

    assert {e for c in opened for e in c.data["entity_id"]} == {"valve.normal"}
    assert {e for c in closed for e in c.data["entity_id"]} == {"valve.inverted"}


async def test_an_inverted_valve_already_in_the_right_place_is_left_alone(
    hass: HomeAssistant,
):
    hass.states.async_set("sensor.bedroom_temperature", "18.0")
    hass.states.async_set("valve.radiator_inverted", "closed")
    entry = await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_HEATERS: ["valve.radiator_inverted"],
        },
    )
    hass.config_entries.async_update_entry(
        entry,
        options={**entry.options, "inverted_heaters": ["valve.radiator_inverted"]},
    )
    await hass.async_block_till_done()

    opened = async_mock_service(hass, "valve", "open_valve")
    closed = async_mock_service(hass, "valve", "close_valve")
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

    # Everything above may have emitted calls while the mode was still off.
    # Only what the loop does once it is heating is being asserted.
    opened.clear()
    closed.clear()
    hass.states.async_set("sensor.bedroom_temperature", "17.9")
    await hass.async_block_till_done()
    assert opened == [] and closed == []


async def test_a_change_held_by_a_minimum_time_applies_itself_later(
    hass: HomeAssistant, freezer
):
    """Turn heating on, change your mind straight away, and the minimum run
    time refuses. That refusal has to expire on its own — otherwise the loop
    next runs on a source change or the thirty second tick, and the room looks
    like it ignored you until you ask a second time."""
    from datetime import timedelta

    from homeassistant.util import dt as dt_util
    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    hass.states.async_set("sensor.bedroom_temperature", "18.0")
    hass.states.async_set("valve.radiator", "closed")
    entry = await add_room(
        hass,
        **{
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_HEATERS: ["valve.radiator"],
        },
    )
    # Long enough that the thirty second tick cannot be what rescues it.
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, "heat_min_on": 120.0}
    )
    await hass.async_block_till_done()

    async_mock_service(hass, "valve", "open_valve")
    closed = async_mock_service(hass, "valve", "close_valve")

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
    hass.states.async_set("valve.radiator", "open")
    await hass.async_block_till_done()
    closed.clear()

    # Change your mind immediately: the minimum run time refuses.
    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": "climate.bedroom", "temperature": 15.0},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert closed == []

    # Nothing else happens — no source changes, no interaction.
    freezer.tick(timedelta(seconds=125))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert {e for c in closed for e in c.data["entity_id"]} == {"valve.radiator"}

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
