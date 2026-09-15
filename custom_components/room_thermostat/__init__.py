"""Room Thermostat: one climate entity per room, cooling with an air
conditioner and heating with something else."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

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
    return True


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(
        entry, platforms(entry)
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
