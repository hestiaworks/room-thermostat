"""Asking the boiler for heat (heating-modules contract, this side).

While the boiler is linked, every room that wants heat calls
`ebus_boiler.request_heat` at once and again every 60 s, and
`ebus_boiler.cancel_heat` when it stops wanting heat. The boiler decides the
flow; a room only says it wants heat, and whether that is from radiators or
from the floor.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Literal

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, SIGNAL_DEMAND
from .model import Room
from .store import RoomStore

_LOGGER = logging.getLogger(__name__)
BOILER = "ebus_boiler"
RENEW = timedelta(seconds=60)


def heat_kind(room: Room) -> Literal["radiator", "floor"]:
    """Floor if any heater is an underfloor loop relay.

    A stopgap: the Room Thermostat redesign gives each heater an explicit kind.
    """
    return "floor" if any("under_floor" in heater for heater in room.heaters) else "radiator"


class BoilerLink:
    def __init__(self, hass: HomeAssistant, store: RoomStore) -> None:
        self.hass = hass
        self.store = store
        self._demand: dict[str, bool] = {}
        self._unsubs = []
        self._warned = False

    @property
    def linked(self) -> bool:
        return bool(self.store.house.boiler_link)

    async def async_start(self) -> None:
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_DEMAND, self._changed))
        self._unsubs.append(async_track_time_interval(self.hass, self._renew, RENEW))

    async def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    def _source(self, room: Room) -> str:
        return f"{DOMAIN}.{room.id}" + ("_floor" if heat_kind(room) == "floor" else "")

    def _reason(self, room: Room) -> str:
        entity_id = er.async_get(self.hass).async_get_entity_id("climate", DOMAIN, room.id)
        state = self.hass.states.get(entity_id) if entity_id else None
        now, target = (state.attributes.get("current_temperature"), state.attributes.get("temperature")) if state else (None, None)
        if isinstance(now, (int, float)) and isinstance(target, (int, float)) and target > now:
            return f"{target - now:.1f} °C below target"
        return "wants heat"

    async def _call(self, service: str, data: dict) -> None:
        try:
            await self.hass.services.async_call(BOILER, service, data, blocking=True)
        except HomeAssistantError as err:
            if not self._warned:
                self._warned = True
                _LOGGER.warning("Room Thermostat could not ask the boiler for heat: %s", err)

    async def _request(self, room: Room) -> None:
        kind = heat_kind(room)
        await self._call("request_heat", {
            "source": self._source(room), "kind": kind,
            "label": room.name + (" floor" if kind == "floor" else ""), "reason": self._reason(room),
        })

    @callback
    def _changed(self, room_id: str, demand: bool) -> None:
        was = self._demand.get(room_id, False)
        self._demand[room_id] = demand
        room = self.store.room(room_id)
        if not self.linked or room is None:
            return
        if demand:
            self.hass.async_create_task(self._request(room))
        elif was:
            self.hass.async_create_task(self._call("cancel_heat", {"source": self._source(room)}))

    async def _renew(self, _now=None) -> None:
        if not self.linked:
            return
        for room_id, demand in self._demand.items():
            room = self.store.room(room_id)
            if demand and room is not None:
                await self._request(room)
