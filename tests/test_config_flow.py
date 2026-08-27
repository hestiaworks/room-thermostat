from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.room_thermostat.const import (
    CONF_COOLER,
    CONF_HEATERS,
    CONF_TEMPERATURE_SENSOR,
    DEFAULT_PARKED_SETPOINT,
    DOMAIN,
)


async def test_a_room_can_be_added_with_a_sensor_and_both_devices(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
            CONF_HEATERS: ["switch.bedroom_radiator_a", "switch.bedroom_radiator_b"],
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Bedroom"
    assert result["data"][CONF_HEATERS] == [
        "switch.bedroom_radiator_a",
        "switch.bedroom_radiator_b",
    ]


async def test_a_room_needs_a_temperature_sensor(hass: HomeAssistant):
    """It is the reason the integration exists; without it there is nothing to
    control against."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Bedroom", CONF_HEATERS: ["switch.a"]}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_TEMPERATURE_SENSOR: "required"}


async def test_a_room_needs_at_least_one_device(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "Bedroom", CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature"},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "no_devices"}


async def test_tunables_start_at_their_documented_defaults(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
        },
    )
    assert result["options"]["parked_setpoint"] == DEFAULT_PARKED_SETPOINT


async def test_a_rooms_devices_can_be_changed_after_it_is_created(hass: HomeAssistant):
    """Adding a valve to an existing room must not mean deleting the room:
    that would take its history, its entity ids and its dashboard cards."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.room_thermostat.config_flow import default_options

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bedroom",
        data={
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
        },
        options=default_options(),
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
            CONF_HEATERS: ["switch.bedroom_radiator"],
        },
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HEATERS] == ["switch.bedroom_radiator"]

    # Reconfiguring reloads the room, which starts its control loop. Let the
    # reload finish before unloading, or it recreates the entity afterwards.
    await hass.async_block_till_done()
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_reconfiguring_still_insists_on_a_temperature_sensor(hass: HomeAssistant):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.room_thermostat.config_flow import default_options

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bedroom",
        data={
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
        },
        options=default_options(),
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Bedroom", CONF_COOLER: "climate.bedroom_ac"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_TEMPERATURE_SENSOR: "required"}


async def test_reconfiguring_keeps_the_tunables_it_was_not_asked_about(
    hass: HomeAssistant,
):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.room_thermostat.config_flow import default_options

    options = {**default_options(), "parked_setpoint": 16.0}
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bedroom",
        data={
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
        },
        options=options,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
            CONF_HEATERS: ["switch.bedroom_radiator"],
        },
    )
    assert entry.options["parked_setpoint"] == 16.0

    await hass.async_block_till_done()
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
