"""The real house's registry, migrated in a test.

Not part of the suite: it reads a copy of a live .storage and is skipped
wherever that copy is not present.
"""

import json
import os

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.room_thermostat.const import (
    CONF_ENTRY_TYPE,
    DOMAIN,
    ENTRY_HUB,
)

COPY = os.environ.get("RT_DRY_RUN_STORAGE", "")
pytestmark = pytest.mark.skipif(not COPY, reason="no .storage copy given")


def _load(name: str) -> dict:
    return json.load(open(f"{COPY}/core.{name}"))


async def test_the_real_house_migrates_with_every_id_intact(hass: HomeAssistant):
    entries = _load("config_entries")["data"]["entries"]
    devices = _load("device_registry")["data"]["devices"]
    entities = _load("entity_registry")["data"]["entities"]

    ours = [e for e in entries if e["domain"] == DOMAIN]
    by_id = {}
    for entry in ours:
        mock = MockConfigEntry(
            domain=DOMAIN,
            title=entry["title"],
            data=entry["data"],
            options=entry["options"],
            entry_id=entry["entry_id"],
        )
        mock.add_to_hass(hass)
        by_id[entry["entry_id"]] = mock

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    made: dict[str, str] = {}
    for device in devices:
        identifiers = {tuple(i) for i in device["identifiers"]}
        owner = device.get("config_entry_id") or device.get("primary_config_entry")
        if owner not in by_id:
            owner = None
        if owner is None:
            continue
        created = device_registry.async_get_or_create(
            config_entry_id=owner,
            identifiers=identifiers,
            name=device["name"],
        )
        made[device["id"]] = created.id

    before = {}
    for entity in entities:
        if entity["platform"] != DOMAIN:
            continue
        owner = entity["config_entry_id"]
        if owner not in by_id:
            continue
        created = entity_registry.async_get_or_create(
            entity["entity_id"].split(".")[0],
            DOMAIN,
            entity["unique_id"],
            config_entry=by_id[owner],
            device_id=made.get(entity["device_id"]),
            suggested_object_id=entity["entity_id"].split(".", 1)[1],
        )
        before[created.entity_id] = entity["unique_id"]

    print("\nBEFORE")
    for entity_id, unique in sorted(before.items()):
        print(f"  {entity_id:<48} {unique}")

    hub = MockConfigEntry(
        domain=DOMAIN, title="Room Thermostat", data={CONF_ENTRY_TYPE: ENTRY_HUB}
    )
    hub.add_to_hass(hass)
    await hass.config_entries.async_setup(hub.entry_id)
    await hass.async_block_till_done()

    after = {
        entity.entity_id: entity.unique_id
        for entity in er.async_entries_for_config_entry(
            entity_registry, hub.entry_id
        )
    }
    print("\nAFTER")
    for entity_id, unique in sorted(after.items()):
        print(f"  {entity_id:<48} {unique}")

    store = hass.data[DOMAIN]["store"]
    print("\nRECORD")
    for room in store.rooms:
        print(f"  {room.name:<20} {room.id}  sensor={room.temperature_sensor}")
        print(f"  {'':<20} cooler={room.cooler} heaters={list(room.heaters)}")
    print(f"  house outdoor_sensor={store.house.outdoor_sensor}")
    print(f"  house heat_limit={store.house.heat_limit}")

    # Every room's thermostat and demand sensor must come through unchanged.
    rooms_before = {
        entity_id: unique
        for entity_id, unique in before.items()
        if not entity_id.endswith("_season")
    }
    for entity_id, unique in rooms_before.items():
        assert entity_id in after, f"{entity_id} did not survive"
        assert after[entity_id] == unique, f"{entity_id} changed its unique_id"

    assert len(store.rooms) == len(
        [e for e in ours if e["data"].get(CONF_ENTRY_TYPE) is None]
    )
    assert [e.entry_id for e in hass.config_entries.async_entries(DOMAIN)] == [
        hub.entry_id
    ]
