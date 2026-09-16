"""What a room publishes for the boiler controller to read."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.room_thermostat.const import (
    CONF_ENTRY_TYPE,
    DOMAIN,
    ENTRY_HUB,
    SIGNAL_DEMAND,
)


async def add_room(hass: HomeAssistant, name: str, sensor: str, heater: str) -> str:
    """A room in the record, and the id the demand signal travels under."""
    entry = next(
        (
            existing
            for existing in hass.config_entries.async_entries(DOMAIN)
            if existing.data.get(CONF_ENTRY_TYPE) == ENTRY_HUB
        ),
        None,
    )
    if entry is None:
        entry = MockConfigEntry(
            domain=DOMAIN, title="Room Thermostat", data={CONF_ENTRY_TYPE: ENTRY_HUB}
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    room = await hass.data[DOMAIN]["store"].async_add_room(
        {"name": name, "temperature_sensor": sensor, "heaters": [heater]}
    )
    await hass.async_block_till_done()
    return room.id


async def test_a_room_publishes_whether_it_wants_heat(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    room_id = await add_room(
        hass, "Bedroom", "sensor.bedroom_temperature", "switch.radiator"
    )

    assert hass.states.get("binary_sensor.bedroom_heat_demand").state == "off"

    async_dispatcher_send(hass, SIGNAL_DEMAND, room_id, True)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.bedroom_heat_demand").state == "on"


async def test_one_rooms_demand_does_not_move_another(hass: HomeAssistant):
    """The boiler controller reads one of these per room; crossed wiring here
    would fire the boiler for a room that is warm."""
    hass.states.async_set("sensor.a_temperature", "22.0")
    await add_room(hass, "Room A", "sensor.a_temperature", "switch.a")

    async_dispatcher_send(hass, SIGNAL_DEMAND, "some-other-room-id", True)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.room_a_heat_demand").state == "off"


async def test_a_room_taken_out_of_the_record_takes_its_sensor_with_it(
    hass: HomeAssistant,
):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    room_id = await add_room(
        hass, "Bedroom", "sensor.bedroom_temperature", "switch.radiator"
    )
    assert hass.states.get("binary_sensor.bedroom_heat_demand") is not None

    await hass.data[DOMAIN]["store"].async_delete_room(room_id)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.bedroom_heat_demand") is None
    assert hass.states.get("climate.bedroom") is None
