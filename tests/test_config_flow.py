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
