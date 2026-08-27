from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.room_thermostat.config_flow import default_options
from custom_components.room_thermostat.const import (
    CONF_HEATERS,
    CONF_TEMPERATURE_SENSOR,
    DOMAIN,
)


def bedroom(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bedroom",
        data={
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_HEATERS: ["switch.radiator"],
        },
        options=default_options(),
    )
    entry.add_to_hass(hass)
    return entry


async def test_a_room_loads_both_of_its_entities(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    entry = bedroom(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("climate.bedroom") is not None
    assert hass.states.get("binary_sensor.bedroom_heat_demand") is not None


async def test_a_room_unloads_cleanly(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    entry = bedroom(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_a_lost_sensor_asks_a_human_for_help(hass: HomeAssistant):
    """Failing silent is not acceptable for a heating system: the room is now
    on a blind duty cycle and somebody needs to know."""
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    entry = bedroom(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("sensor.bedroom_temperature", "unavailable")
    await hass.async_block_till_done()

    registry = ir.async_get(hass)
    assert registry.async_get_issue(DOMAIN, f"sensor_lost_{entry.entry_id}") is not None
