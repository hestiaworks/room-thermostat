"""Asking the boiler for heat (heating-modules contract, room_thermostat side)."""

import logging

import pytest
from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.helpers.dispatcher import async_dispatcher_send
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from homeassistant.util import dt as dt_util
from datetime import timedelta

from custom_components.room_thermostat.boiler_link import heat_kind
from custom_components.room_thermostat.const import CONF_ENTRY_TYPE, DOMAIN, ENTRY_HUB, SIGNAL_DEMAND
from custom_components.room_thermostat.model import Room


async def house(hass: HomeAssistant, heaters=("switch.radiator",), name="Bedroom"):
    entry = MockConfigEntry(domain=DOMAIN, title="Room Thermostat", data={CONF_ENTRY_TYPE: ENTRY_HUB})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    room = await hass.data[DOMAIN]["store"].async_add_room(
        {"name": name, "temperature_sensor": "sensor.t", "heaters": list(heaters)})
    await hass.async_block_till_done()
    return entry, room


def fake_boiler(hass):
    calls = []

    async def record(call):
        calls.append((call.service, dict(call.data)))

    hass.services.async_register("ebus_boiler", "request_heat", record)
    hass.services.async_register("ebus_boiler", "cancel_heat", record)
    return calls


async def link(hass):
    return await hass.services.async_call(DOMAIN, "link", {"domain": "ebus_boiler", "entry_id": "boiler", "version": "0.1.0"},
                                          blocking=True, return_response=True)


def test_heat_kind():
    assert heat_kind(Room(id="a", heaters=("switch.under_floor_heating_relay_6",))) == "floor"
    assert heat_kind(Room(id="b", heaters=("climate.bedroom_radiator",))) == "radiator"


async def test_link_stores_boiler_entry(hass):
    entry, _ = await house(hass)
    response = await link(hass)
    assert response["entry_id"] == entry.entry_id
    assert response["version"] == "0.17.0"
    assert hass.data[DOMAIN]["store"].house.boiler_link == {"entry_id": "boiler", "version": "0.1.0"}


async def test_link_refuses_other_domains(hass):
    await house(hass)
    with pytest.raises(Exception, match="ebus_boiler"):
        await hass.services.async_call(DOMAIN, "link", {"domain": "something", "entry_id": "x", "version": "1"},
                                       blocking=True, return_response=True)


async def test_sends_request_on_demand(hass):
    hass.states.async_set("sensor.t", "19.0")
    _, room = await house(hass)
    calls = fake_boiler(hass)
    await link(hass)
    async_dispatcher_send(hass, SIGNAL_DEMAND, room.id, True)
    await hass.async_block_till_done()
    service, data = calls[-1]
    assert service == "request_heat"
    assert data["source"] == f"room_thermostat.{room.id}"
    assert data["kind"] == "radiator"
    assert data["label"] == "Bedroom"


async def test_floor_room_sends_floor_kind(hass):
    _, room = await house(hass, heaters=("switch.under_floor_heating_relay_6",), name="Bathroom")
    calls = fake_boiler(hass)
    await link(hass)
    async_dispatcher_send(hass, SIGNAL_DEMAND, room.id, True)
    await hass.async_block_till_done()
    service, data = calls[-1]
    assert (data["source"], data["kind"], data["label"]) == (f"room_thermostat.{room.id}_floor", "floor", "Bathroom floor")


async def test_cancels_when_demand_ends(hass):
    _, room = await house(hass)
    calls = fake_boiler(hass)
    await link(hass)
    async_dispatcher_send(hass, SIGNAL_DEMAND, room.id, True)
    async_dispatcher_send(hass, SIGNAL_DEMAND, room.id, False)
    await hass.async_block_till_done()
    assert calls[-1] == ("cancel_heat", {"source": f"room_thermostat.{room.id}"})


async def test_renews_every_60s(hass):
    _, room = await house(hass)
    calls = fake_boiler(hass)
    await link(hass)
    async_dispatcher_send(hass, SIGNAL_DEMAND, room.id, True)
    await hass.async_block_till_done()
    before = len([c for c in calls if c[0] == "request_heat"])
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=61))
    await hass.async_block_till_done()
    assert len([c for c in calls if c[0] == "request_heat"]) == before + 1


async def test_nothing_sent_when_not_linked(hass):
    _, room = await house(hass)
    calls = fake_boiler(hass)
    async_dispatcher_send(hass, SIGNAL_DEMAND, room.id, True)
    await hass.async_block_till_done()
    assert calls == []


async def test_boiler_missing_is_logged_once_not_raised(hass, caplog):
    _, room = await house(hass)
    await link(hass)
    with caplog.at_level(logging.WARNING):
        for _ in range(3):
            async_dispatcher_send(hass, SIGNAL_DEMAND, room.id, True)
            await hass.async_block_till_done()
    assert caplog.text.count("could not ask the boiler for heat") == 1


async def test_unlink_clears_the_link(hass):
    await house(hass)
    await link(hass)
    await hass.services.async_call(DOMAIN, "unlink", {"domain": "ebus_boiler"}, blocking=True, return_response=True)
    assert hass.data[DOMAIN]["store"].house.boiler_link is None
