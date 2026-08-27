"""Whether this room wants heat.

This is the whole interface between a room and the boiler controller that will
later aggregate every room. Demand means the room's valves are open *and* have
had time to travel, not merely that a switch was energised — a boiler that
fires on the switch is pushing water into a circuit that has not opened yet.
"""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_DEMAND


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([HeatDemand(entry)])


class HeatDemand(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Heat demand"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_heat_demand"
        self._attr_is_on = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Room Thermostat",
        )

    async def async_added_to_hass(self) -> None:
        self._attr_is_on = bool(
            self.hass.data[DOMAIN][self._entry.entry_id].get("demand")
        )

        @callback
        def _demand(entry_id: str, demand: bool) -> None:
            if entry_id != self._entry.entry_id:
                return
            self._attr_is_on = demand
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_DEMAND, _demand)
        )
