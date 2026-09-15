"""Room Thermostat: one climate entity per room, cooling with an air
conditioner and heating with something else."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback

from .const import CONF_ENTRY_TYPE, DOMAIN, ENTRY_ROOM, ENTRY_SEASONS

ROOM_PLATFORMS = [Platform.CLIMATE, Platform.BINARY_SENSOR]
SEASONS_PLATFORMS = [Platform.BINARY_SENSOR]


def entry_type(entry: ConfigEntry) -> str:
    """Which kind of entry this is.

    Rooms predate the key, so its absence means a room. Nothing migrates.
    """
    return entry.data.get(CONF_ENTRY_TYPE, ENTRY_ROOM)


def platforms(entry: ConfigEntry) -> list[Platform]:
    return SEASONS_PLATFORMS if entry_type(entry) == ENTRY_SEASONS else ROOM_PLATFORMS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"demand": False}
    await hass.config_entries.async_forward_entry_setups(entry, platforms(entry))
    # Editing the options changes the control loop's parameters, and the
    # simplest correct response is to rebuild the entities around them.
    entry.async_on_unload(entry.add_update_listener(_reload))
    if entry_type(entry) == ENTRY_ROOM:
        _ask_for_seasons(hass)
    else:
        # Rooms subscribe to the two sensors by entity id, so a house that has
        # just gained them has to look again.
        _reload_rooms(hass)
    return True


@callback
def _ask_for_seasons(hass: HomeAssistant) -> None:
    """Bring the one Seasons entry into being if it is not there.

    It is never offered in the helper flow, so this is the only way it comes to
    exist — and the reason a deleted one returns at the next startup. Deleting
    it is not how seasons are switched off; clearing its outdoor source is, and
    that leaves the row in place to be pointed at a sensor again later.

    The flag stops two rooms setting up at once from starting two flows. The
    flow checks again for itself, because the flag does not survive a reload.
    """
    store = hass.data.setdefault(DOMAIN, {})
    if store.get("seasons_requested"):
        return
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_SEASONS:
            return
    store["seasons_requested"] = True
    hass.async_create_task(
        hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_IMPORT})
    )


@callback
def _reload_rooms(hass: HomeAssistant) -> None:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry_type(entry) == ENTRY_ROOM and entry.state.recoverable:
            hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(
        entry, platforms(entry)
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """A room that has lost its seasons must stop obeying them."""
    if entry_type(entry) != ENTRY_SEASONS:
        return
    hass.data.setdefault(DOMAIN, {})["seasons_requested"] = False
    _reload_rooms(hass)
