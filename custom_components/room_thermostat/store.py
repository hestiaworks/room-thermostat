"""The record the page edits, and the only thing that writes it.

Rooms used to be config entries, one each. They are a list here instead,
because the page is the record: ordering them, duplicating one, or exporting
the lot are edits to a list rather than machinery per operation. Devices and
entities are projected from this, so every write announces itself — a silent
one would leave the house and the record disagreeing.

Saving is immediate rather than debounced. These writes happen when a person
presses Save, not fifteen times a minute, and somebody who has pressed it
expects the file on disk to say so.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .const import SIGNAL_ROOM, SIGNAL_ROOMS, STORE_KEY, STORE_VERSION
from .model import House, Room


class RoomStore:
    """Every room in the house, and what the house decides once."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, STORE_VERSION, STORE_KEY)
        self._rooms: list[Room] = []
        self._house = House()

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self._rooms = [Room.from_dict(room) for room in data.get("rooms", [])]
        self._house = House.from_dict(data.get("house", {}))

    @property
    def rooms(self) -> tuple[Room, ...]:
        return tuple(self._rooms)

    @property
    def house(self) -> House:
        return self._house

    def room(self, room_id: str) -> Room | None:
        return next((room for room in self._rooms if room.id == room_id), None)

    async def async_add_room(self, data: dict[str, Any]) -> Room:
        room = Room.from_dict({**data, "id": data.get("id") or uuid4().hex})
        self._rooms.append(room)
        await self._async_save()
        async_dispatcher_send(self._hass, SIGNAL_ROOMS)
        return room

    async def async_update_room(self, room_id: str, data: dict[str, Any]) -> Room:
        """Change some of a room's settings, leaving the rest as they were."""
        index = next(
            (i for i, room in enumerate(self._rooms) if room.id == room_id), None
        )
        if index is None:
            raise KeyError(room_id)
        room = Room.from_dict({**self._rooms[index].to_dict(), **data, "id": room_id})
        self._rooms[index] = room
        await self._async_save()
        async_dispatcher_send(self._hass, SIGNAL_ROOM, room_id)
        return room

    async def async_delete_room(self, room_id: str) -> None:
        self._rooms = [room for room in self._rooms if room.id != room_id]
        await self._async_save()
        async_dispatcher_send(self._hass, SIGNAL_ROOMS)

    async def async_update_house(self, data: dict[str, Any]) -> House:
        self._house = House.from_dict({**self._house.to_dict(), **data})
        await self._async_save()
        async_dispatcher_send(self._hass, SIGNAL_ROOMS)
        return self._house

    async def async_import(self, rooms: list[Room], house: House) -> None:
        """Take a whole record at once, for the migration.

        Rooms already present are left alone, so a migration interrupted
        halfway can simply be run again.
        """
        known = {room.id for room in self._rooms}
        self._rooms.extend(room for room in rooms if room.id not in known)
        self._house = house
        await self._async_save()
        async_dispatcher_send(self._hass, SIGNAL_ROOMS)

    async def _async_save(self) -> None:
        await self._store.async_save(
            {
                "rooms": [room.to_dict() for room in self._rooms],
                "house": self._house.to_dict(),
            }
        )
