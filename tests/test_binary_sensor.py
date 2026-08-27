from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.room_thermostat.config_flow import default_options
from custom_components.room_thermostat.const import (
    CONF_HEATERS,
    CONF_TEMPERATURE_SENSOR,
    DOMAIN,
    SIGNAL_DEMAND,
)


async def test_a_room_publishes_whether_it_wants_heat(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
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
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.bedroom_heat_demand").state == "off"

    async_dispatcher_send(hass, SIGNAL_DEMAND, entry.entry_id, True)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.bedroom_heat_demand").state == "on"


async def test_one_rooms_demand_does_not_move_another(hass: HomeAssistant):
    """The boiler controller reads one of these per room; crossed wiring here
    would fire the boiler for a room that is warm."""
    hass.states.async_set("sensor.a_temperature", "22.0")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Room A",
        data={
            "name": "Room A",
            CONF_TEMPERATURE_SENSOR: "sensor.a_temperature",
            CONF_HEATERS: ["switch.a"],
        },
        options=default_options(),
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    async_dispatcher_send(hass, SIGNAL_DEMAND, "some-other-entry-id", True)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.room_a_heat_demand").state == "off"
