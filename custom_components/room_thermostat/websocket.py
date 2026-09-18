"""The commands the page calls.

Only what has no entity to read. Current temperature, mode, what a room is
doing and whether it wants heat are all entity state, which the page is handed
by Home Assistant and which updates itself — asking for those over a command
would be a slower copy of something already in the browser.

So this is the record, and nothing else: what the page writes, and what it
needs in order to draw the fields.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from . import history
from .const import CONF_ENTRY_TYPE, DOMAIN, ENTRY_HUB
from .model import room_problems
from .store import RoomStore


def _store(hass: HomeAssistant) -> RoomStore:
    store = hass.data.get(DOMAIN, {}).get("store")
    if store is None:
        raise ValueError("Room Thermostat is not configured")
    return store


def _ours(hass: HomeAssistant) -> set[str]:
    """Every entity this integration publishes.

    A room told to drive one of these would drive itself, and the loop is not
    visible from the page.
    """
    return {
        entry.entity_id
        for entry in er.async_get(hass).entities.values()
        if entry.platform == DOMAIN
    }


def _record(store: RoomStore) -> dict[str, Any]:
    return {
        "rooms": [room.to_dict() for room in store.rooms],
        "house": store.house.to_dict(),
    }


@callback
def _send_problems(connection, message_id: int, problems: dict[str, str]) -> None:
    """Refuse a save, naming the field.

    The page renders each problem beside its own field, so "invalid" on its
    own would be a dialog that says no and does not say where.
    """
    connection.send_message({
        "id": message_id,
        "type": "result",
        "success": False,
        "error": {
            "code": "invalid_room",
            "message": "That room cannot be saved",
            "problems": problems,
        },
    })


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command({vol.Required("type"): "room_thermostat/rooms/list"})
async def ws_list(hass, connection, msg) -> None:
    try:
        connection.send_result(msg["id"], _record(_store(hass)))
    except ValueError as err:
        connection.send_error(msg["id"], "not_configured", str(err))


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command({
    vol.Required("type"): "room_thermostat/rooms/create",
    vol.Required("room"): dict,
})
async def ws_create(hass, connection, msg) -> None:
    try:
        store = _store(hass)
    except ValueError as err:
        connection.send_error(msg["id"], "not_configured", str(err))
        return
    problems = room_problems(msg["room"], own_entity_ids=_ours(hass))
    if problems:
        _send_problems(connection, msg["id"], problems)
        return
    room = await store.async_add_room(msg["room"])
    connection.send_result(msg["id"], room.to_dict())


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command({
    vol.Required("type"): "room_thermostat/rooms/update",
    vol.Required("room_id"): str,
    vol.Required("room"): dict,
})
async def ws_update(hass, connection, msg) -> None:
    try:
        store = _store(hass)
    except ValueError as err:
        connection.send_error(msg["id"], "not_configured", str(err))
        return
    current = store.room(msg["room_id"])
    if current is None:
        connection.send_error(msg["id"], "unknown_room", "No such room")
        return
    # Validated as it will be saved, not as it arrived: the page may send one
    # field, and a single field cannot be judged on its own.
    merged = {**current.to_dict(), **msg["room"]}
    problems = room_problems(merged, own_entity_ids=_ours(hass))
    if problems:
        _send_problems(connection, msg["id"], problems)
        return
    room = await store.async_update_room(msg["room_id"], msg["room"])
    connection.send_result(msg["id"], room.to_dict())


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command({
    vol.Required("type"): "room_thermostat/rooms/delete",
    vol.Required("room_id"): str,
})
async def ws_delete(hass, connection, msg) -> None:
    try:
        store = _store(hass)
    except ValueError as err:
        connection.send_error(msg["id"], "not_configured", str(err))
        return
    if store.room(msg["room_id"]) is None:
        connection.send_error(msg["id"], "unknown_room", "No such room")
        return
    await store.async_delete_room(msg["room_id"])
    connection.send_result(msg["id"], {"deleted": msg["room_id"]})


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command({
    vol.Required("type"): "room_thermostat/house/update",
    vol.Required("house"): dict,
})
async def ws_house(hass, connection, msg) -> None:
    try:
        store = _store(hass)
    except ValueError as err:
        connection.send_error(msg["id"], "not_configured", str(err))
        return
    house = await store.async_update_house(msg["house"])
    connection.send_result(msg["id"], house.to_dict())


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command({
    vol.Required("type"): "room_thermostat/history",
    vol.Required("span"): vol.In(list(history.SPANS)),
})
async def ws_history(hass, connection, msg) -> None:
    """Everything the history tab draws, in one answer.

    One command rather than one per series: they share a window and a bucket
    width, and a chart drawn from six separately-bucketed answers would have
    six subtly different time axes.
    """
    try:
        store = _store(hass)
    except ValueError as err:
        connection.send_error(msg["id"], "not_configured", str(err))
        return

    span = msg["span"]
    end = dt_util.utcnow().timestamp()
    start = end - history.SPANS[span]
    count = history.BUCKETS[span]

    hub = next(
        (
            entry
            for entry in hass.config_entries.async_entries(DOMAIN)
            if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_HUB
        ),
        None,
    )
    if hub is None:
        connection.send_error(msg["id"], "not_configured", "No hub")
        return

    registry = er.async_get(hass)

    def _entity(domain: str, unique: str) -> str | None:
        return registry.async_get_entity_id(domain, DOMAIN, unique)

    average = _entity("sensor", f"{hub.entry_id}_outdoor_average")
    season = _entity("binary_sensor", f"{hub.entry_id}_heating_season")
    outdoor = store.house.outdoor_sensor
    rooms = {
        room.id: {
            "name": room.name,
            "temperature": room.temperature_sensor,
            "demand": _entity("sensor", f"{room.id}_heat_demand_number"),
        }
        for room in store.rooms
    }

    wanted = [
        entity_id
        for entity_id in [
            outdoor,
            average,
            season,
            *[room["temperature"] for room in rooms.values()],
            *[room["demand"] for room in rooms.values()],
        ]
        if entity_id
    ]
    series = await history.async_series(hass, wanted, start, end)

    def _bucket(entity_id: str | None) -> list[float | None]:
        return history.bucket(series.get(entity_id or "", []), start, end, count)

    # The energy signature always reads hourly statistics, whatever span the
    # chart above it is showing: a dot is a whole day either way.
    day_start = end - history.SPANS["90d"]
    day_source = average or outdoor
    day_series = await history.async_series(
        hass,
        [
            entity_id
            for entity_id in [day_source, *[room["demand"] for room in rooms.values()]]
            if entity_id
        ],
        day_start,
        end,
    )
    outdoor_days = history.hourly_by_day(day_series.get(day_source or "", []))
    demand_days: dict[str, list[float]] = {}
    for room in rooms.values():
        for date, values in history.hourly_by_day(
            day_series.get(room["demand"] or "", [])
        ).items():
            demand_days.setdefault(date, []).extend(values)
    days = history.daily(outdoor_days, demand_days)

    connection.send_result(msg["id"], {
        "start": start,
        "end": end,
        "buckets": count,
        "series": {
            "outdoor": _bucket(outdoor),
            "damped": _bucket(average),
            "rooms": {
                room_id: {"name": room["name"], "points": _bucket(room["temperature"])}
                for room_id, room in rooms.items()
            },
        },
        "seasons": history.spans_of(series.get(season or "", []), start, end),
        "demand": {room_id: _bucket(room["demand"]) for room_id, room in rooms.items()},
        "daily": days,
        "balance_point": history.balance_point(days),
    })


@callback
def async_register(hass: HomeAssistant) -> None:
    for command in (ws_list, ws_create, ws_update, ws_delete, ws_house, ws_history):
        websocket_api.async_register_command(hass, command)
