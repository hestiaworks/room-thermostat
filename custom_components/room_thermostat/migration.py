"""Moving the rooms that already exist into the record, once.

Rooms were config entries, one each, and their entities are identified by the
entry's id. So a room's id in the record is **its old entry id**: every
unique_id is unchanged, and climate.living_room stays where every dashboard
card, automation and panel layout expects it.

The order is the safety. Removing a config entry deletes entities whose
config_entry_id still points at it, and deletes devices left with no config
entries. Both belong to the hub before the removal happens, so neither is true
by the time it does.
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import CONF_ENTRY_TYPE, DOMAIN, ENTRY_ROOM
from .model import Room
from .store import RoomStore

_LOGGER = logging.getLogger(__name__)

# Where a room's sources could be found. They moved from an entry's data into
# its options partway through this integration's life, and rooms made before
# that still keep theirs in data — so each key is looked for in both,
# separately. Choosing one place wholesale is what orphaned sources the last
# time this was done.
_SOURCE_KEYS = (
    "temperature_sensor",
    "humidity_sensor",
    "cooler",
    "heaters",
    "inverted_heaters",
)


def as_room(entry: ConfigEntry) -> Room:
    """A legacy entry read as a room."""
    merged = {**entry.data, **entry.options}
    for key in _SOURCE_KEYS:
        if key in entry.options:
            merged[key] = entry.options[key]
        elif key in entry.data:
            merged[key] = entry.data[key]
    merged["id"] = entry.entry_id
    merged["name"] = entry.title
    return Room.from_dict(merged)


async def async_migrate(hass: HomeAssistant, hub: ConfigEntry) -> int:
    """Move every legacy room entry into the record. Returns how many moved.

    Safe to run again: a room already in the record is skipped and an entry
    already gone is not there to find, so an interruption halfway is
    recoverable rather than fatal.
    """
    store: RoomStore = hass.data[DOMAIN]["store"]
    legacy = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.entry_id != hub.entry_id
        and entry.data.get(CONF_ENTRY_TYPE, ENTRY_ROOM) == ENTRY_ROOM
    ]
    if not legacy:
        return 0

    known = {room.id for room in store.rooms}
    rooms = [as_room(entry) for entry in legacy if entry.entry_id not in known]
    if rooms:
        await store.async_import(rooms, store.house)

    entities = er.async_get(hass)
    devices = dr.async_get(hass)
    moved = 0
    for entry in legacy:
        # Entities can only be moved while unloaded. One that never got as far
        # as its platforms has none to unload, and asking would be refused.
        if entry.state is ConfigEntryState.LOADED:
            await hass.config_entries.async_unload(entry.entry_id)
        elif entry.state is ConfigEntryState.SETUP_IN_PROGRESS:
            # Still being built. Leave it for the next time around rather than
            # pulling it apart underneath whoever is building it.
            continue

        device = devices.async_get_device({(DOMAIN, entry.entry_id)})
        if device is not None:
            devices.async_update_device(device.id, add_config_entry_id=hub.entry_id)

        for registered in list(
            er.async_entries_for_config_entry(entities, entry.entry_id)
        ):
            entities.async_update_entity_platform(
                registered.entity_id,
                DOMAIN,
                new_config_entry_id=hub.entry_id,
                new_device_id=None if device is None else device.id,
            )

        # Last, and only now safe: its entities and its device belong to the
        # hub, so neither is taken with it.
        await hass.config_entries.async_remove(entry.entry_id)
        moved += 1

    _LOGGER.info(
        "Moved %s room%s into the Room Thermostat record",
        moved,
        "" if moved == 1 else "s",
    )
    return moved
