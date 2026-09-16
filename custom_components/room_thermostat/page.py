"""Serve and register the Room Thermostat page.

A helper's cog is the wrong door for a heating system: it makes a room look
like a small thing you keep several of, and leaves nowhere for anything that
is not per-room. This is the door instead.
"""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import PAGE_COMPONENT, PAGE_MODULE_URL, PAGE_URL_PATH


async def async_setup_page_assets(hass: HomeAssistant) -> None:
    static_dir = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [StaticPathConfig("/room_thermostat/frontend", str(static_dir), True)]
    )
    frontend.add_extra_js_url(hass, PAGE_MODULE_URL)


def async_register_page(hass: HomeAssistant) -> None:
    frontend.async_register_built_in_panel(
        hass,
        PAGE_COMPONENT,
        sidebar_title="Room Thermostat",
        sidebar_icon="mdi:home-thermometer",
        frontend_url_path=PAGE_URL_PATH,
        require_admin=True,
    )


def async_unregister_page(hass: HomeAssistant) -> None:
    """Take the sidebar entry away, leaving the static route in place."""
    frontend.async_remove_panel(hass, PAGE_URL_PATH)
