"""Whether this room wants heat, and whether the house is in season.

The demand sensor is the interface to the boiler controller. The two season
sensors travel the other way — one answer for the house that every room obeys
— and they are here rather than in a module of their own because this is the
binary_sensor platform and that is what they are.

Original docstring follows.

This is the whole interface between a room and the boiler controller that will
later aggregate every room. Demand means the room's valves are open *and* have
had time to travel, not merely that a switch was energised — a boiler that
fires on the switch is pushing water into a circuit that has not opened yet.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_conversion import TemperatureConverter

from . import entry_type
from .control import damp, in_season, settled
from .const import (
    CONF_COOL_LIMIT,
    CONF_COOL_LIMIT_HYSTERESIS,
    CONF_DAMPING_HOURS,
    CONF_HEAT_LIMIT,
    CONF_HEAT_LIMIT_HYSTERESIS,
    CONF_OUTDOOR_SENSOR,
    CONF_SEASON_DWELL,
    DOMAIN,
    ENTRY_SEASONS,
    OUTDOOR_LOST_SECONDS,
    SANE_OUTDOOR,
    SIGNAL_DEMAND,
)

# The loop is driven by the source reporting, but the average has to keep
# integrating while a quiet source says nothing.
TICK = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    if entry_type(entry) == ENTRY_SEASONS:
        async_add_entities([HeatingSeason(entry), CoolingSeason(entry)])
        return
    async_add_entities([HeatDemand(entry)])


class HeatDemand(BinarySensorEntity):
    # Named explicitly, for the same reason as the thermostat.
    _attr_has_entity_name = False

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_heat_demand"
        self._attr_name = f"{entry.title} heat demand"
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


def outdoor_reading(hass: HomeAssistant, entity_id: str | None) -> float | None:
    """The outdoor temperature in °C, or None if there is not one.

    A weather entity keeps its temperature in an attribute rather than in its
    state, and either kind may report °F. A reading outside the sane band is a
    fault — a sensor in October sun reads 40, a failed one reads nonsense — and
    is treated exactly like a missing one.
    """
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None or state.state in ("unknown", "unavailable"):
        return None
    if entity_id.startswith("weather."):
        raw = state.attributes.get("temperature")
        unit = state.attributes.get("temperature_unit", "°C")
    else:
        raw = state.state
        unit = state.attributes.get("unit_of_measurement", "°C")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if unit == "°F":
        value = TemperatureConverter.convert(value, "°F", "°C")
    low, high = SANE_OUTDOOR
    return value if low <= value <= high else None


class _Season(BinarySensorEntity):
    """One half of the house's answer.

    On means the season is in: equipment may run. Off is the only state that
    stops anything, so everything that can go wrong — no source, a source that
    has gone, a reading that cannot be believed — reports on.
    """

    _attr_has_entity_name = False
    _attr_should_poll = False
    key = ""
    label = ""

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{self.key}"
        self._attr_name = self.label
        self._attr_is_on = True
        self._outdoor: float | None = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Room Thermostat",
        )

    @property
    def _options(self) -> dict[str, Any]:
        return self._entry.options

    @property
    def _source(self) -> str | None:
        return self._options.get(CONF_OUTDOOR_SENSOR)

    def _decide(self, reading: float | None) -> None:
        raise NotImplementedError

    async def _restore(self) -> None:
        return None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await self._restore()

        @callback
        def _changed(_: Event) -> None:
            self._update()

        # Both have to be callbacks: an undecorated function is run in an
        # executor thread, and writing entity state from one is a data race.
        @callback
        def _ticked(_now) -> None:
            self._update()

        if self._source:
            self.async_on_remove(
                async_track_state_change_event(self.hass, [self._source], _changed)
            )
        self.async_on_remove(async_track_time_interval(self.hass, _ticked, TICK))
        self._update()

    @callback
    def _update(self) -> None:
        self._decide(outdoor_reading(self.hass, self._source))
        self.async_write_ha_state()


class HeatingSeason(_Season, RestoreEntity):
    """Decided on a damped average, because heating tracks the building's
    energy balance over days rather than this afternoon's sun — and then held
    until the answer has lasted, because a mild autumn dips below the limit for
    a few hours every night however hard the average is damped."""

    key = "heating_season"
    label = "Heating season"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry)
        self._damped: float | None = None
        self._last: float | None = None
        self._pending_since: float | None = None
        self._lost_since: float | None = None

    async def _restore(self) -> None:
        """A restart must not reseed the average from whatever the weather
        happens to be doing at the moment Home Assistant comes back."""
        if (last := await self.async_get_last_state()) is None:
            return
        stored = last.attributes.get("damped")
        if isinstance(stored, (int, float)):
            self._damped = float(stored)
        if last.state in ("on", "off"):
            self._attr_is_on = last.state == "on"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "outdoor": self._outdoor,
            "damped": None if self._damped is None else round(self._damped, 2),
            "limit": self._options[CONF_HEAT_LIMIT],
            "hysteresis": self._options[CONF_HEAT_LIMIT_HYSTERESIS],
            "averaging_hours": self._options[CONF_DAMPING_HOURS],
            "dwell_hours": self._options[CONF_SEASON_DWELL],
        }

    def _decide(self, reading: float | None) -> None:
        now = dt_util.utcnow().timestamp()
        self._outdoor = reading
        if reading is None:
            # Frozen, not poisoned: a missing reading is not a cold one, so the
            # average keeps what it had and the season falls open.
            self._last = None
            self._pending_since = None
            self._report_lost(now)
            self._attr_is_on = True
            return
        self._report_lost(None)
        elapsed = 0.0 if self._last is None else now - self._last
        self._last = now
        self._damped = damp(
            self._damped, reading, elapsed, self._options[CONF_DAMPING_HOURS] * 3600.0
        )
        candidate = in_season(
            self._attr_is_on,
            self._damped,
            self._options[CONF_HEAT_LIMIT],
            self._options[CONF_HEAT_LIMIT_HYSTERESIS],
            rising=False,
        )
        self._attr_is_on, self._pending_since = settled(
            self._attr_is_on,
            candidate,
            self._pending_since,
            now,
            self._options[CONF_SEASON_DWELL] * 3600.0,
        )

    def _report_lost(self, now: float | None) -> None:
        """A heating decision made on a source nobody noticed had gone is the
        silent failure this integration refuses to allow elsewhere."""
        if now is None or self._source is None:
            self._lost_since = None
            ir.async_delete_issue(self.hass, DOMAIN, "outdoor_lost")
            return
        if self._lost_since is None:
            self._lost_since = now
            return
        if now - self._lost_since < OUTDOOR_LOST_SECONDS:
            return
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            "outdoor_lost",
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="outdoor_lost",
            translation_placeholders={"sensor": self._source or ""},
        )


class CoolingSeason(_Season):
    """Decided on the live reading, and not made to wait.

    Cooling demand is dominated by instantaneous gain: one sunny afternoon in
    an otherwise cold week genuinely overheats a room, and either a damped
    threshold or a dwell would refuse the air conditioner on exactly that day.
    """

    key = "cooling_season"
    label = "Cooling season"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "outdoor": self._outdoor,
            "limit": self._options[CONF_COOL_LIMIT],
            "hysteresis": self._options[CONF_COOL_LIMIT_HYSTERESIS],
        }

    def _decide(self, reading: float | None) -> None:
        self._outdoor = reading
        if reading is None:
            self._attr_is_on = True
            return
        self._attr_is_on = in_season(
            self._attr_is_on,
            reading,
            self._options[CONF_COOL_LIMIT],
            self._options[CONF_COOL_LIMIT_HYSTERESIS],
            rising=True,
        )
