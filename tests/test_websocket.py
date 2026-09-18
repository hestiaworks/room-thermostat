"""The commands the page calls."""

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.room_thermostat.const import (
    CONF_ENTRY_TYPE,
    DOMAIN,
    ENTRY_HUB,
)


# The page's commands arrive over a real websocket, which means the http
# component starts. Sockets are blocked in tests by default, and a server that
# cannot bind leaves its shutdown thread behind.
pytestmark = pytest.mark.usefixtures("socket_enabled")


async def house(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, title="Room Thermostat", data={CONF_ENTRY_TYPE: ENTRY_HUB}
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_listing_gives_the_rooms_and_the_house(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
):
    await house(hass)
    await hass.data[DOMAIN]["store"].async_add_room(
        {"name": "Bedroom", "temperature_sensor": "sensor.bedroom",
         "heaters": ["switch.radiator"]}
    )
    # The record is written through an executor; let it land before the test
    # ends, or its thread outlives the test that started it.
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "room_thermostat/rooms/list"})
    result = (await client.receive_json())["result"]

    assert [room["name"] for room in result["rooms"]] == ["Bedroom"]
    assert result["house"]["heat_limit"] == 16.0


async def test_creating_a_room_puts_it_in_the_record(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
):
    await house(hass)
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 1,
        "type": "room_thermostat/rooms/create",
        "room": {"name": "Kitchen", "temperature_sensor": "sensor.kitchen",
                 "heaters": ["switch.kitchen"]},
    })
    message = await client.receive_json()

    assert message["success"]
    assert message["result"]["name"] == "Kitchen"
    assert [r.name for r in hass.data[DOMAIN]["store"].rooms] == ["Kitchen"]


async def test_a_room_with_no_sensor_is_refused_with_the_field_named(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
):
    """The page renders the problem beside the field, so the field has to be
    in the answer."""
    await house(hass)
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 1,
        "type": "room_thermostat/rooms/create",
        "room": {"name": "Kitchen", "heaters": ["switch.kitchen"]},
    })
    message = await client.receive_json()

    assert not message["success"]
    assert message["error"]["code"] == "invalid_room"
    assert message["error"]["problems"] == {"temperature_sensor": "required"}
    assert hass.data[DOMAIN]["store"].rooms == ()


async def test_a_room_cannot_be_told_to_drive_itself(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
):
    hass.states.async_set("sensor.bedroom_temperature", "21.0")
    await house(hass)
    room = await hass.data[DOMAIN]["store"].async_add_room(
        {"name": "Bedroom", "temperature_sensor": "sensor.bedroom_temperature",
         "heaters": ["switch.radiator"]}
    )
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 1,
        "type": "room_thermostat/rooms/create",
        "room": {"name": "Second", "temperature_sensor": "sensor.other",
                 "cooler": "climate.bedroom"},
    })
    message = await client.receive_json()
    assert message["error"]["problems"] == {"cooler": "own_entity"}
    assert room.id in [r.id for r in hass.data[DOMAIN]["store"].rooms]


async def test_updating_a_room_keeps_what_it_was_not_told(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
):
    await house(hass)
    room = await hass.data[DOMAIN]["store"].async_add_room(
        {"name": "Bedroom", "temperature_sensor": "sensor.bedroom",
         "heaters": ["switch.radiator"], "cooling_strategy": "gated"}
    )
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 1,
        "type": "room_thermostat/rooms/update",
        "room_id": room.id,
        "room": {"name": "Guest room"},
    })
    message = await client.receive_json()

    assert message["success"]
    saved = hass.data[DOMAIN]["store"].room(room.id)
    assert saved.name == "Guest room"
    assert saved.cooling_strategy == "gated"


async def test_updating_a_room_that_is_not_there_says_so(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
):
    await house(hass)
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 1,
        "type": "room_thermostat/rooms/update",
        "room_id": "nobody",
        "room": {"name": "Nowhere"},
    })
    message = await client.receive_json()
    assert message["error"]["code"] == "unknown_room"


async def test_deleting_a_room_removes_it(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
):
    await house(hass)
    room = await hass.data[DOMAIN]["store"].async_add_room(
        {"name": "Bedroom", "temperature_sensor": "sensor.bedroom",
         "heaters": ["switch.radiator"]}
    )
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 1, "type": "room_thermostat/rooms/delete", "room_id": room.id,
    })
    message = await client.receive_json()

    assert message["success"]
    assert hass.data[DOMAIN]["store"].rooms == ()


async def test_the_house_can_be_saved(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
):
    await house(hass)
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 1,
        "type": "room_thermostat/house/update",
        "house": {"outdoor_sensor": "weather.home", "heat_limit": 17.5},
    })
    message = await client.receive_json()

    assert message["success"]
    saved = hass.data[DOMAIN]["store"].house
    assert saved.outdoor_sensor == "weather.home"
    assert saved.heat_limit == 17.5
    assert saved.season_dwell_hours == 6.0


async def test_the_source_can_be_cleared(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
):
    """Clearing it is how seasons are switched off, so null has to travel."""
    await house(hass)
    await hass.data[DOMAIN]["store"].async_update_house(
        {"outdoor_sensor": "weather.home"}
    )
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 1,
        "type": "room_thermostat/house/update",
        "house": {"outdoor_sensor": None},
    })
    await client.receive_json()
    assert hass.data[DOMAIN]["store"].house.outdoor_sensor is None


async def test_a_command_in_flight_when_the_hub_goes_answers_rather_than_raising(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
):
    """The commands only exist once the hub has set up — without one there is
    no page to call them from either. What can still happen is the hub being
    unloaded while the page is open, and that has to answer."""
    entry = await house(hass)
    client = await hass_ws_client(hass)
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await client.send_json({"id": 1, "type": "room_thermostat/rooms/list"})
    message = await client.receive_json()
    assert message["error"]["code"] == "not_configured"
