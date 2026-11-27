"""room_thermostat.link / unlink: the boiler links to this module (heating-modules contract)."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.loader import async_get_integration

from .const import DOMAIN

LINKABLE = ("ebus_boiler",)


@callback
def async_register_link_services(hass: HomeAssistant, hub: ConfigEntry) -> None:
    async def link(call: ServiceCall) -> dict:
        if call.data["domain"] not in LINKABLE:
            raise ServiceValidationError(f"Room Thermostat links only to {', '.join(LINKABLE)}")
        store = hass.data[DOMAIN]["store"]
        await store.async_update_house({"boiler_link": {"entry_id": call.data["entry_id"], "version": call.data["version"]}})
        version = (await async_get_integration(hass, DOMAIN)).version
        return {"entry_id": hub.entry_id, "version": str(version)}

    async def unlink(call: ServiceCall) -> dict:
        await hass.data[DOMAIN]["store"].async_update_house({"boiler_link": None})
        return {"unlinked": call.data["domain"]}

    hass.services.async_register(DOMAIN, "link", link, schema=vol.Schema({
        vol.Required("domain"): cv.string, vol.Required("entry_id"): cv.string, vol.Required("version"): cv.string,
    }), supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "unlink", unlink, schema=vol.Schema({vol.Required("domain"): cv.string}),
                                 supports_response=SupportsResponse.ONLY)
