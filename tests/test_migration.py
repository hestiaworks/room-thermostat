"""Moving the rooms that already exist into the record, once.

The dangerous part of this whole change: one shot, a live system, and real
history behind every entity id.
"""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.room_thermostat.const import (
    CONF_ENTRY_TYPE,
    DOMAIN,
    ENTRY_HUB,
)


def legacy_room(hass: HomeAssistant, name: str = "Bedroom", **extra) -> MockConfigEntry:
    """A room as it was made before any of this: its own config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=name,
        data={"name": name},
        options={
            "temperature_sensor": f"sensor.{name.lower()}_temperature",
            "heaters": ["switch.radiator"],
            "cooling_strategy": "passthrough",
            "frost_temperature": 5.0,
            **extra,
        },
    )
    entry.add_to_hass(hass)
    return entry


def registered(hass: HomeAssistant, entry: MockConfigEntry, name: str) -> None:
    """The entities that room would have had, as the registry would hold them."""
    registry = er.async_get(hass)
    devices = dr.async_get(hass)
    device = devices.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=name,
    )
    registry.async_get_or_create(
        "climate",
        DOMAIN,
        entry.entry_id,
        config_entry=entry,
        device_id=device.id,
        suggested_object_id=name.lower().replace(" ", "_"),
    )
    registry.async_get_or_create(
        "binary_sensor",
        DOMAIN,
        f"{entry.entry_id}_heat_demand",
        config_entry=entry,
        device_id=device.id,
        suggested_object_id=f"{name.lower().replace(' ', '_')}_heat_demand",
    )


async def hub(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, title="Room Thermostat", data={CONF_ENTRY_TYPE: ENTRY_HUB}
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_a_legacy_room_keeps_its_entity_id_and_its_unique_id(
    hass: HomeAssistant,
):
    """The whole point. Dashboards, automations and the panel layouts all
    point at climate.bedroom."""
    hass.states.async_set("sensor.bedroom_temperature", "21.0")
    room = legacy_room(hass)
    registered(hass, room, "Bedroom")
    was = er.async_get(hass).async_get("climate.bedroom")
    assert was is not None

    hub_entry = await hub(hass)

    now = er.async_get(hass).async_get("climate.bedroom")
    assert now is not None
    assert now.unique_id == was.unique_id == room.entry_id
    assert now.config_entry_id == hub_entry.entry_id


async def test_the_room_is_in_the_record_with_its_settings(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "21.0")
    room = legacy_room(hass, cooling_strategy="gated")
    registered(hass, room, "Bedroom")
    await hub(hass)

    store = hass.data[DOMAIN]["store"]
    assert [r.id for r in store.rooms] == [room.entry_id]
    moved = store.rooms[0]
    assert moved.name == "Bedroom"
    assert moved.temperature_sensor == "sensor.bedroom_temperature"
    assert moved.heaters == ("switch.radiator",)
    assert moved.cooling_strategy == "gated"


async def test_a_room_made_before_sources_moved_still_finds_them(
    hass: HomeAssistant,
):
    """The earliest rooms kept their sources in the entry's data rather than
    its options. They must arrive with their devices, not without them."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living Room",
        data={
            "name": "Living Room",
            "temperature_sensor": "sensor.old_place",
            "cooler": "climate.living_room_ac",
        },
        options={},
    )
    entry.add_to_hass(hass)
    registered(hass, entry, "Living Room")
    await hub(hass)

    moved = hass.data[DOMAIN]["store"].rooms[0]
    assert moved.temperature_sensor == "sensor.old_place"
    assert moved.cooler == "climate.living_room_ac"


async def test_the_legacy_entry_is_gone_and_the_device_is_not(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "21.0")
    room = legacy_room(hass)
    registered(hass, room, "Bedroom")
    before = dr.async_get(hass).async_get_device({(DOMAIN, room.entry_id)})
    assert before is not None

    hub_entry = await hub(hass)

    assert room.entry_id not in [
        entry.entry_id for entry in hass.config_entries.async_entries(DOMAIN)
    ]
    after = dr.async_get(hass).async_get_device({(DOMAIN, room.entry_id)})
    assert after is not None
    assert after.id == before.id
    assert hub_entry.entry_id in after.config_entries


async def test_running_it_twice_changes_nothing(hass: HomeAssistant):
    """An interruption halfway has to be recoverable by running it again."""
    from custom_components.room_thermostat.migration import async_migrate

    hass.states.async_set("sensor.bedroom_temperature", "21.0")
    room = legacy_room(hass)
    registered(hass, room, "Bedroom")
    hub_entry = await hub(hass)

    store = hass.data[DOMAIN]["store"]
    assert len(store.rooms) == 1
    assert await async_migrate(hass, hub_entry) == 0
    assert len(store.rooms) == 1


async def test_three_rooms_all_arrive(hass: HomeAssistant):
    for name in ("Bedroom", "Kitchen", "Office"):
        hass.states.async_set(f"sensor.{name.lower()}_temperature", "21.0")
        registered(hass, legacy_room(hass, name), name)
    await hub(hass)

    store = hass.data[DOMAIN]["store"]
    assert {room.name for room in store.rooms} == {"Bedroom", "Kitchen", "Office"}
    for name in ("bedroom", "kitchen", "office"):
        assert hass.states.get(f"climate.{name}") is not None


async def test_a_house_with_no_legacy_rooms_migrates_nothing(hass: HomeAssistant):
    from custom_components.room_thermostat.migration import async_migrate

    hub_entry = await hub(hass)
    assert await async_migrate(hass, hub_entry) == 0


async def test_a_migrated_room_still_works(hass: HomeAssistant):
    """It is not enough that the ids survive: the room has to run."""
    hass.states.async_set("sensor.bedroom_temperature", "18.0")
    hass.states.async_set("switch.radiator", "off")
    registered(hass, legacy_room(hass), "Bedroom")
    await hub(hass)

    from pytest_homeassistant_custom_component.common import async_mock_service

    async_mock_service(hass, "switch", "turn_on")
    async_mock_service(hass, "switch", "turn_off")
    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": "climate.bedroom", "temperature": 22.0},
        blocking=True,
    )
    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": "climate.bedroom", "hvac_mode": "heat"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("climate.bedroom").attributes["hvac_action"] == "heating"


async def test_a_house_with_rooms_and_no_hub_gets_one(hass: HomeAssistant):
    """Nobody would think to add a hub by hand, and without one those rooms
    would sit as entries forever."""
    hass.states.async_set("sensor.bedroom_temperature", "21.0")
    room = legacy_room(hass)
    registered(hass, room, "Bedroom")

    await hass.config_entries.async_setup(room.entry_id)
    await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert [e.data.get(CONF_ENTRY_TYPE) for e in entries] == [ENTRY_HUB]
    assert hass.states.get("climate.bedroom") is not None
    assert er.async_get(hass).async_get("climate.bedroom").unique_id == room.entry_id


async def test_a_seasons_entry_folds_into_the_record(hass: HomeAssistant):
    """0.12.0 put the house's settings in an entry of their own. A house that
    ran it has one, with a source somebody chose, and losing that would be
    losing the only setting they had made."""
    seasons = MockConfigEntry(
        domain=DOMAIN,
        title="Seasons",
        data={CONF_ENTRY_TYPE: "seasons"},
        options={
            "outdoor_sensor": "weather.forecast_home",
            "heat_limit": 17.5,
            "damping_hours": 30.0,
            "season_dwell_hours": 6.0,
        },
    )
    seasons.add_to_hass(hass)

    await hub(hass)

    house = hass.data[DOMAIN]["store"].house
    assert house.outdoor_sensor == "weather.forecast_home"
    assert house.heat_limit == 17.5
    assert seasons.entry_id not in [
        entry.entry_id for entry in hass.config_entries.async_entries(DOMAIN)
    ]


async def test_the_folded_settings_reach_the_sensors(hass: HomeAssistant):
    hass.states.async_set("sensor.outdoor", "8.0")
    seasons = MockConfigEntry(
        domain=DOMAIN,
        title="Seasons",
        data={CONF_ENTRY_TYPE: "seasons"},
        options={"outdoor_sensor": "sensor.outdoor", "heat_limit": 17.5},
    )
    seasons.add_to_hass(hass)

    await hub(hass)

    state = hass.states.get("binary_sensor.heating_season")
    assert state.attributes["limit"] == 17.5
    assert state.attributes["damped"] == 8.0
