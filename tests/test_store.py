"""The store: the only writer of the record the page edits."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from custom_components.room_thermostat.const import SIGNAL_ROOM, SIGNAL_ROOMS
from custom_components.room_thermostat.store import RoomStore


async def test_an_empty_house_loads_with_no_rooms_and_the_defaults(
    hass: HomeAssistant,
):
    store = RoomStore(hass)
    await store.async_load()
    assert store.rooms == ()
    assert store.house.heat_limit == 16.0


async def test_a_room_can_be_added_and_read_back(hass: HomeAssistant):
    store = RoomStore(hass)
    await store.async_load()
    room = await store.async_add_room(
        {"name": "Bedroom", "temperature_sensor": "sensor.bedroom",
         "heaters": ["switch.radiator"]}
    )
    assert room.name == "Bedroom"
    assert store.room(room.id) == room
    assert len(store.rooms) == 1


async def test_an_added_room_gets_an_id_of_its_own(hass: HomeAssistant):
    store = RoomStore(hass)
    await store.async_load()
    first = await store.async_add_room({"name": "A", "temperature_sensor": "sensor.a"})
    second = await store.async_add_room({"name": "B", "temperature_sensor": "sensor.b"})
    assert first.id != second.id


async def test_what_is_saved_survives_a_reload(hass: HomeAssistant):
    store = RoomStore(hass)
    await store.async_load()
    room = await store.async_add_room(
        {"name": "Bedroom", "temperature_sensor": "sensor.bedroom"}
    )
    await store.async_update_house({"heat_limit": 18.0})

    again = RoomStore(hass)
    await again.async_load()
    assert [r.id for r in again.rooms] == [room.id]
    assert again.house.heat_limit == 18.0


async def test_updating_a_room_keeps_its_id_and_its_untouched_settings(
    hass: HomeAssistant,
):
    store = RoomStore(hass)
    await store.async_load()
    room = await store.async_add_room(
        {"name": "Bedroom", "temperature_sensor": "sensor.bedroom",
         "cooling_strategy": "gated"}
    )
    changed = await store.async_update_room(room.id, {"name": "Guest room"})
    assert changed.id == room.id
    assert changed.name == "Guest room"
    assert changed.cooling_strategy == "gated"


async def test_a_deleted_room_is_gone(hass: HomeAssistant):
    store = RoomStore(hass)
    await store.async_load()
    room = await store.async_add_room(
        {"name": "Bedroom", "temperature_sensor": "sensor.bedroom"}
    )
    await store.async_delete_room(room.id)
    assert store.rooms == ()
    assert store.room(room.id) is None


async def test_adding_and_deleting_announce_themselves(hass: HomeAssistant):
    """Entities are created and removed from these, so a silent write would
    leave the house and the record disagreeing."""
    structural: list = []
    changed: list = []
    async_dispatcher_connect(hass, SIGNAL_ROOMS, lambda: structural.append(True))
    async_dispatcher_connect(hass, SIGNAL_ROOM, changed.append)

    store = RoomStore(hass)
    await store.async_load()
    room = await store.async_add_room(
        {"name": "Bedroom", "temperature_sensor": "sensor.bedroom"}
    )
    await hass.async_block_till_done()
    assert len(structural) == 1

    await store.async_update_room(room.id, {"name": "Guest room"})
    await hass.async_block_till_done()
    assert changed == [room.id]
    assert len(structural) == 1  # settings are not structural

    await store.async_delete_room(room.id)
    await hass.async_block_till_done()
    assert len(structural) == 2


async def test_updating_a_room_that_is_not_there_raises(hass: HomeAssistant):
    store = RoomStore(hass)
    await store.async_load()
    with pytest.raises(KeyError):
        await store.async_update_room("nobody", {"name": "Nowhere"})


async def test_importing_leaves_rooms_it_already_has_alone(hass: HomeAssistant):
    """A migration interrupted halfway has to be safe to run again."""
    from custom_components.room_thermostat.model import House, Room

    store = RoomStore(hass)
    await store.async_load()
    await store.async_import(
        [Room.from_dict({"id": "abc", "name": "Bedroom"})], House()
    )
    await store.async_import(
        [Room.from_dict({"id": "abc", "name": "Renamed"})], House()
    )
    assert [(r.id, r.name) for r in store.rooms] == [("abc", "Bedroom")]
