"""Numbers, so the recorder keeps them.

Home Assistant keeps two records: states, which are exact and purged after ten
days, and long-term statistics, which are hourly and kept forever — but only
for entities with a state_class, and never for attributes.

The damped outdoor average was an attribute and heat demand was a binary
sensor, so neither survived long enough to draw a thirty-day picture with.
Both appear here as numbers as well, which is all the recorder needs.

The hourly mean of a 0/1 series is exactly the fraction of that hour a room
was heating, so the statistics engine does the aggregation — forever, and with
no bookkeeping of our own.
"""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import entry_type
from .const import (
    DOMAIN,
    ENTRY_HUB,
    SIGNAL_DEMAND,
    SIGNAL_OUTDOOR_AVERAGE,
    SIGNAL_ROOMS,
)
from .store import RoomStore


class OutdoorAverage(SensorEntity):
    """The damped outdoor temperature, as a number with a history.

    The season sensor owns the filter and sends the value here: one place
    computes it, and two implementations of it would disagree by small amounts
    and be impossible to reason about.
    """

    _attr_has_entity_name = False
    _attr_name = "Outdoor average"
    _attr_should_poll = False
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_outdoor_average"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Room Thermostat",
        )

    async def async_added_to_hass(self) -> None:
        # Whatever the season sensor last worked out, in case it set up first.
        held = self.hass.data.get(DOMAIN, {}).get("outdoor_average")
        if isinstance(held, (int, float)):
            self._attr_native_value = round(float(held), 2)

        @callback
        def _average(value: float | None) -> None:
            self._attr_native_value = (
                None if value is None else round(float(value), 2)
            )
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_OUTDOOR_AVERAGE, _average)
        )


class HeatDemandNumber(SensorEntity):
    """One if this room is calling for heat, zero if it is not."""

    _attr_has_entity_name = False
    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, room_id: str) -> None:
        self.hass = hass
        self.room_id = room_id
        room = hass.data[DOMAIN]["store"].room(room_id)
        self._attr_unique_id = f"{room_id}_heat_demand_number"
        self._attr_name = f"{room.name} heat demand"
        self._attr_native_value = 0.0
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, room_id)},
            name=room.name,
            manufacturer="Room Thermostat",
        )

    async def async_added_to_hass(self) -> None:
        self._attr_native_value = (
            1.0 if self.hass.data[DOMAIN].get(self.room_id, {}).get("demand") else 0.0
        )

        @callback
        def _demand(room_id: str, demand: bool) -> None:
            if room_id != self.room_id:
                return
            self._attr_native_value = 1.0 if demand else 0.0
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_DEMAND, _demand)
        )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    if entry_type(entry) != ENTRY_HUB:
        return
    store: RoomStore = hass.data[DOMAIN]["store"]
    known: dict[str, HeatDemandNumber] = {}

    @callback
    def _sync() -> None:
        wanted = {room.id for room in store.rooms}
        added = [HeatDemandNumber(hass, room_id) for room_id in wanted - known.keys()]
        for entity in added:
            known[entity.room_id] = entity
        if added:
            async_add_entities(added)
        for room_id in list(known.keys() - wanted):
            entity = known.pop(room_id)
            hass.async_create_task(entity.async_remove(force_remove=True))

    async_add_entities([OutdoorAverage(hass, entry)])
    _sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_ROOMS, _sync))
