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

from .const import DOMAIN
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


@callback
def async_register(hass: HomeAssistant) -> None:
    for command in (ws_list, ws_create, ws_update, ws_delete, ws_house):
        websocket_api.async_register_command(hass, command)
