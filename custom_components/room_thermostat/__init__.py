"""Room Thermostat: one climate entity per room, cooling with an air
conditioner and heating with something else."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    CONF_ENTRY_TYPE,
    SIGNAL_ROOMS,
    DOMAIN,
    ENTRY_HUB,
    ENTRY_ROOM,
)
from .migration import async_migrate
from .page import async_register_page, async_setup_page_assets, async_unregister_page
from .store import RoomStore

# A room's entities belong to the hub now, built from the record. A legacy
# room entry sets up nothing at all: it is waiting to be migrated, and
# building its entities twice over would fight the migration for them.
ROOM_PLATFORMS: list[Platform] = []
HUB_PLATFORMS = [Platform.CLIMATE, Platform.BINARY_SENSOR, Platform.SENSOR]


def entry_type(entry: ConfigEntry) -> str:
    """Which kind of entry this is.

    Rooms predate the key, so its absence means a room. Nothing migrates.
    """
    return entry.data.get(CONF_ENTRY_TYPE, ENTRY_ROOM)


def platforms(entry: ConfigEntry) -> list[Platform]:
    kind = entry_type(entry)
    if kind == ENTRY_HUB:
        return HUB_PLATFORMS
    return ROOM_PLATFORMS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"demand": False}
    if entry_type(entry) == ENTRY_HUB:
        store = RoomStore(hass)
        await store.async_load()
        hass.data[DOMAIN]["store"] = store
        await async_setup_page_assets(hass)
        async_register_page(hass)
        # A callback, not a lambda: an undecorated callable is run in an
        # executor thread, and touching the device registry from one is a data
        # race Home Assistant now refuses outright.
        @callback
        def _rooms_changed() -> None:
            _prune_devices(hass, entry)

        entry.async_on_unload(
            async_dispatcher_connect(hass, SIGNAL_ROOMS, _rooms_changed)
        )
    await hass.config_entries.async_forward_entry_setups(entry, platforms(entry))
    # Editing the options changes the control loop's parameters, and the
    # simplest correct response is to rebuild the entities around them.
    entry.async_on_unload(entry.add_update_listener(_reload))
    if entry_type(entry) == ENTRY_ROOM:
        _ask_for_hub(hass)
    if entry_type(entry) == ENTRY_HUB:
        # Scheduled rather than awaited. A house that predates the hub asks
        # for one *while its rooms are still setting up*, and an entry cannot
        # be unloaded mid-setup — so the migration waits its turn, and the
        # rooms it moves are picked up by the record's own signal.
        hass.async_create_task(async_migrate(hass, entry))
    return True


@callback
def _ask_for_hub(hass: HomeAssistant) -> None:
    """A house with rooms and no hub gets one made for it.

    A fresh install makes its hub when the integration is added. This is for
    the houses that predate it, where adding one by hand would be exactly the
    chore this change removes — and the hub is what runs the migration, so
    without it those rooms would sit as entries forever.

    The flag stops several rooms setting up at once from starting several
    flows; the flow checks again for itself, because the flag does not survive
    a reload.
    """
    store = hass.data.setdefault(DOMAIN, {})
    if store.get("hub_requested"):
        return
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_HUB:
            return
    store["hub_requested"] = True
    hass.async_create_task(
        hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_IMPORT})
    )


@callback
def _prune_devices(hass: HomeAssistant, hub: ConfigEntry) -> None:
    """Take away the device of a room that is no longer in the record.

    Config entries used to do this when one was removed. The record is ours
    now, so this is ours. The device is not deleted directly: its link to the
    hub is removed, and a device left with no config entries is cleared by the
    registry itself.
    """
    store: RoomStore = hass.data[DOMAIN]["store"]
    # The hub's own device carries the season sensors and is identified by the
    # hub rather than by a room, so it is always wanted. Leaving it out took
    # the seasons away the first time the house was edited.
    wanted = {room.id for room in store.rooms} | {hub.entry_id}
    registry = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(registry, hub.entry_id):
        ours = {
            identifier[1]
            for identifier in device.identifiers
            if identifier[0] == DOMAIN
        }
        if ours and not ours & wanted:
            registry.async_update_device(
                device.id, remove_config_entry_id=hub.entry_id
            )


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(
        entry, platforms(entry)
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if entry_type(entry) == ENTRY_HUB:
            async_unregister_page(hass)
            hass.data.get(DOMAIN, {}).pop("store", None)
    return unloaded


