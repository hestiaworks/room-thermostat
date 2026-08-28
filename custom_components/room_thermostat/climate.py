"""The room's thermostat.

This is an adapter and nothing more: it reads the source entities, hands their
values to control.decide, and carries out what comes back. Every rule lives in
control.py, where it can be tested without a house.
"""

from __future__ import annotations

from datetime import timedelta
from collections.abc import Callable
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, UnitOfTemperature
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from . import control
from .config_flow import sources
from .const import (
    CONF_ALLOW_AC_HEAT,
    CONF_COOL_COLD_TOLERANCE,
    CONF_COOL_HOT_TOLERANCE,
    CONF_COOL_MIN_OFF,
    CONF_COOL_MIN_ON,
    CONF_COOLER,
    CONF_COOLING_STRATEGY,
    CONF_FROST_TEMPERATURE,
    CONF_HEAT_COLD_TOLERANCE,
    CONF_HEAT_HOT_TOLERANCE,
    CONF_HEAT_MIN_OFF,
    CONF_HEAT_MIN_ON,
    CONF_HEATERS,
    CONF_INVERTED_HEATERS,
    CONF_VISIBLE_CONTROLS,
    CONTROLS,
    CONF_HUMIDITY_SENSOR,
    CONF_OFFSET_CORRECTION,
    CONF_PARKED_SETPOINT,
    CONF_TEMPERATURE_SENSOR,
    CONF_VALVE_TRAVEL,
    DEFAULT_FROST_RECOVERY,
    DEFAULT_WARM_OFF,
    DEFAULT_WARM_ON,
    DOMAIN,
    SIGNAL_DEMAND,
)

# The loops are driven by source changes, but minimum on and off times expire
# on the clock rather than on an event, so something has to come back and look.
TICK = timedelta(seconds=30)

# What each kind of heater is told, and what it says when it is doing it. A
# radiator valve is a valve entity, not a switch — assuming otherwise made the
# only selectable heaters things like an air conditioner's panel light.
HEATERS = {
    "valve": {
        True: ("open_valve", ("open", "opening")),
        False: ("close_valve", ("closed", "closing")),
    },
    "switch": {
        True: ("turn_on", ("on",)),
        False: ("turn_off", ("off",)),
    },
    "input_boolean": {
        True: ("turn_on", ("on",)),
        False: ("turn_off", ("off",)),
    },
}

ACTIONS = {
    control.ACTION_OFF: HVACAction.OFF,
    control.ACTION_IDLE: HVACAction.IDLE,
    control.ACTION_HEATING: HVACAction.HEATING,
    control.ACTION_COOLING: HVACAction.COOLING,
    control.ACTION_DRYING: HVACAction.DRYING,
    control.ACTION_FAN: HVACAction.FAN,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([RoomThermostat(hass, entry)])


def _number(hass: HomeAssistant, entity_id: str | None) -> float | None:
    """A source reading, or None if it is missing or not a number."""
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None or state.state in ("unknown", "unavailable"):
        return None
    try:
        return float(state.state)
    except ValueError:
        return None


class RoomThermostat(ClimateEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        chosen = sources(entry)
        self._sensor = chosen.get(CONF_TEMPERATURE_SENSOR)
        self._humidity = chosen.get(CONF_HUMIDITY_SENSOR)
        self._cooler = chosen.get(CONF_COOLER)
        self._heaters: list[str] = list(chosen.get(CONF_HEATERS) or [])
        self._inverted = set(entry.options.get(CONF_INVERTED_HEATERS) or [])
        self._mode = HVACMode.OFF
        self._target = 21.0
        self._target_low = 20.0
        self._target_high = 25.0
        self._action = HVACAction.OFF
        self._state = control.LoopState(
            heaters_on=False,
            heaters_changed_at=0.0,
            cooler_on=False,
            cooler_changed_at=0.0,
        )
        self._demand = False
        self._frost = False
        self._retry: Callable[[], None] | None = None
        # A device per room, so its thermostat and its demand sensor group
        # together and both take the room's name.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Room Thermostat",
        )

    # --- what this room can do -------------------------------------------

    @property
    def _options(self) -> dict[str, Any]:
        return self._entry.options

    @property
    def hvac_modes(self) -> list[HVACMode]:
        modes = [HVACMode.OFF]
        if self._heaters or (self._cooler and self._options[CONF_ALLOW_AC_HEAT]):
            modes.append(HVACMode.HEAT)
        if self._cooler:
            modes += [HVACMode.COOL, HVACMode.DRY, HVACMode.FAN_ONLY]
        if self._heaters and self._cooler:
            modes.append(HVACMode.HEAT_COOL)
        return modes

    @property
    def supported_features(self) -> ClimateEntityFeature:
        features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        if self._heaters and self._cooler:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        for control, attribute, flag in (
            ("fan_mode", "fan_modes", ClimateEntityFeature.FAN_MODE),
            ("swing_mode", "swing_modes", ClimateEntityFeature.SWING_MODE),
            ("swing_horizontal_mode", "swing_horizontal_modes",
             ClimateEntityFeature.SWING_HORIZONTAL_MODE),
            ("preset_mode", "preset_modes", ClimateEntityFeature.PRESET_MODE),
        ):
            if self._shows(control) and self._cooler_attribute(attribute):
                features |= flag
        return features

    def _shows(self, control: str) -> bool:
        """Whether this room offers one of the unit's controls.

        Absent means show everything the unit reports, which is what a room
        configured before this existed expects.
        """
        chosen = self._options.get(CONF_VISIBLE_CONTROLS)
        return control in chosen if chosen is not None else True

    def _cooler_attribute(self, name: str) -> Any:
        """Whatever the unit says about itself, republished unchanged."""
        if not self._cooler:
            return None
        state = self.hass.states.get(self._cooler)
        return state.attributes.get(name) if state else None

    @property
    def fan_modes(self):
        return self._cooler_attribute("fan_modes") if self._shows("fan_mode") else None

    @property
    def fan_mode(self):
        return self._cooler_attribute("fan_mode") if self._shows("fan_mode") else None

    @property
    def swing_modes(self):
        return self._cooler_attribute("swing_modes") if self._shows("swing_mode") else None

    @property
    def swing_mode(self):
        return self._cooler_attribute("swing_mode") if self._shows("swing_mode") else None

    @property
    def swing_horizontal_modes(self):
        return self._cooler_attribute("swing_horizontal_modes") if self._shows("swing_horizontal_mode") else None

    @property
    def swing_horizontal_mode(self):
        return self._cooler_attribute("swing_horizontal_mode") if self._shows("swing_horizontal_mode") else None

    @property
    def preset_modes(self):
        return self._cooler_attribute("preset_modes") if self._shows("preset_mode") else None

    @property
    def preset_mode(self):
        return self._cooler_attribute("preset_mode") if self._shows("preset_mode") else None

    # --- what the room is doing ------------------------------------------

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """What this room is working with, so 'nothing happened' can be
        diagnosed from one state dump rather than from guesswork."""
        watched = [
            entity
            for entity in (self._sensor, self._humidity, self._cooler, *self._heaters)
            if entity
        ]
        missing = [
            entity
            for entity in watched
            if (state := self.hass.states.get(entity)) is None
            or state.state in ("unavailable", "unknown")
        ]
        return {
            "temperature_sensor": self._sensor,
            "humidity_sensor": self._humidity,
            "cooler": self._cooler,
            "heaters": self._heaters,
            "inverted_heaters": sorted(self._inverted),
            "heat_demand": self._demand,
            "frost_protection": self._frost,
            "unavailable_devices": missing,
        }

    @property
    def min_temp(self) -> float:
        """The unit's own limit, so we never offer a setpoint it would refuse.
        A room heated only by valves keeps Home Assistant's default range,
        which a valve does not care about either way."""
        limit = self._cooler_attribute("min_temp")
        return float(limit) if limit is not None else super().min_temp

    @property
    def max_temp(self) -> float:
        limit = self._cooler_attribute("max_temp")
        return float(limit) if limit is not None else super().max_temp

    @property
    def current_temperature(self):
        return _number(self.hass, self._sensor)

    @property
    def current_humidity(self):
        value = _number(self.hass, self._humidity)
        return None if value is None else int(value)

    @property
    def hvac_mode(self):
        return self._mode

    @property
    def hvac_action(self):
        return self._action

    # Exactly one kind of setpoint is reported at a time. Home Assistant
    # decides which control to draw from these, and offering both leaves the
    # card showing a single dial whose value heat_cool never reads.
    @property
    def target_temperature(self):
        return None if self._mode == HVACMode.HEAT_COOL else self._target

    @property
    def target_temperature_low(self):
        return self._target_low if self._mode == HVACMode.HEAT_COOL else None

    @property
    def target_temperature_high(self):
        return self._target_high if self._mode == HVACMode.HEAT_COOL else None

    # --- commands ---------------------------------------------------------

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        self._mode = hvac_mode
        await self._apply()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (value := kwargs.get("temperature")) is not None:
            self._target = float(value)
        if (value := kwargs.get("target_temp_low")) is not None:
            self._target_low = float(value)
        if (value := kwargs.get("target_temp_high")) is not None:
            self._target_high = float(value)
        await self._apply()

    async def _forward(self, service: str, key: str, value: str) -> None:
        if not self._cooler:
            return
        await self.hass.services.async_call(
            "climate",
            service,
            {ATTR_ENTITY_ID: self._cooler, key: value},
            blocking=True,
        )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        await self._forward("set_fan_mode", "fan_mode", fan_mode)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        await self._forward("set_swing_mode", "swing_mode", swing_mode)

    async def async_set_swing_horizontal_mode(self, swing_horizontal_mode: str) -> None:
        await self._forward(
            "set_swing_horizontal_mode", "swing_horizontal_mode", swing_horizontal_mode
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self._forward("set_preset_mode", "preset_mode", preset_mode)

    # --- the loop ---------------------------------------------------------

    def _config(self) -> control.RoomConfig:
        options = self._options
        return control.RoomConfig(
            has_cooler=bool(self._cooler),
            has_heater=bool(self._heaters),
            cooling_strategy=options[CONF_COOLING_STRATEGY],
            offset_correction=options[CONF_OFFSET_CORRECTION],
            parked_setpoint=options[CONF_PARKED_SETPOINT],
            cool_cold_tolerance=options[CONF_COOL_COLD_TOLERANCE],
            cool_hot_tolerance=options[CONF_COOL_HOT_TOLERANCE],
            cool_min_on=options[CONF_COOL_MIN_ON],
            cool_min_off=options[CONF_COOL_MIN_OFF],
            heat_cold_tolerance=options[CONF_HEAT_COLD_TOLERANCE],
            heat_hot_tolerance=options[CONF_HEAT_HOT_TOLERANCE],
            heat_min_on=options[CONF_HEAT_MIN_ON],
            heat_min_off=options[CONF_HEAT_MIN_OFF],
            valve_travel=options[CONF_VALVE_TRAVEL],
            allow_ac_heat=options[CONF_ALLOW_AC_HEAT],
            frost_temperature=options[CONF_FROST_TEMPERATURE],
            frost_recovery=DEFAULT_FROST_RECOVERY,
            warm_on=DEFAULT_WARM_ON,
            warm_off=DEFAULT_WARM_OFF,
        )

    async def _apply(self) -> None:
        decision = control.decide(
            self._config(),
            control.Readings(
                room_temperature=_number(self.hass, self._sensor),
                room_humidity=_number(self.hass, self._humidity),
                cooler_temperature=(
                    self._cooler_attribute("current_temperature")
                    if self._cooler
                    else None
                ),
            ),
            control.Request(
                hvac_mode=str(self._mode),
                target=self._target,
                target_low=self._target_low,
                target_high=self._target_high,
            ),
            self._state,
            now=dt_util.utcnow().timestamp(),
        )
        self._state = decision.state
        self._action = ACTIONS[decision.hvac_action]
        self._schedule_retry(decision.retry_after)
        self._frost = decision.frost_active
        self._report_sensor(decision.sensor_lost)

        await self._command(decision)

        if decision.heat_demand != self._demand:
            self._demand = decision.heat_demand
            self.hass.data[DOMAIN][self._entry.entry_id]["demand"] = self._demand
            async_dispatcher_send(
                self.hass, SIGNAL_DEMAND, self._entry.entry_id, self._demand
            )

        self.async_write_ha_state()

    async def _command(self, decision: control.Decision) -> None:
        """Issue only the calls that would change something.

        The loop runs every thirty seconds whether or not anything moved, so
        commanding unconditionally would fill the log with service calls and
        keep re-sending a setpoint the unit already has. Comparing against what
        the devices actually report also means a valve someone flipped by hand
        is put back rather than quietly ignored.
        """
        # Grouped by domain, because a room may mix a radiator valve with a
        # relay-driven loop and they take different services.
        stale: dict[tuple[str, bool], list[str]] = {}
        for heater in self._heaters:
            domain = heater.split(".")[0]
            if domain not in HEATERS:
                continue
            state = self.hass.states.get(heater)
            # A device that is missing or unavailable is not commanded at all:
            # driving a side that has gone shouts into the void, and the call
            # would fail anyway.
            if state is None or state.state in ("unavailable", "unknown"):
                continue
            # A normally-open actuator is energised to *stop* heat, so heating
            # the room means telling it the opposite of everything else.
            energise = decision.heaters_on != (heater in self._inverted)
            _, settled = HEATERS[domain][energise]
            # "opening" counts as already told: a valve reports it for minutes.
            if state.state in settled:
                continue
            stale.setdefault((domain, energise), []).append(heater)

        for (domain, energise), entities in stale.items():
            service, _ = HEATERS[domain][energise]
            await self.hass.services.async_call(
                domain, service, {ATTR_ENTITY_ID: entities}, blocking=False
            )

        if decision.cooler is None or not self._cooler:
            return
        current = self.hass.states.get(self._cooler)
        if current is None or current.state in ("unavailable", "unknown"):
            return
        if current.state != decision.cooler.hvac_mode:
            await self.hass.services.async_call(
                "climate",
                "set_hvac_mode",
                {ATTR_ENTITY_ID: self._cooler, "hvac_mode": decision.cooler.hvac_mode},
                blocking=False,
            )
        target = decision.cooler.target
        if target is not None and current.attributes.get("temperature") != target:
            await self.hass.services.async_call(
                "climate",
                "set_temperature",
                {ATTR_ENTITY_ID: self._cooler, "temperature": target},
                blocking=False,
            )

    def _schedule_retry(self, after: float | None) -> None:
        """Come back when a held change becomes allowed.

        Without this the loop next runs on a source change or the thirty
        second tick, so a change refused by a minimum time sits there until
        something unrelated wakes it — which looks like the room ignoring you
        until you ask a second time.
        """
        if self._retry is not None:
            self._retry()
            self._retry = None
        if after is None:
            return

        # A second's grace, so the minimum has certainly elapsed on arrival.
        self._retry = async_call_later(self.hass, after + 1, self._wake)

    @callback
    def _wake(self, _now=None) -> None:
        """Run the loop from the event loop.

        Decorated, and passed as itself rather than wrapped in a lambda: an
        undecorated callable is run in an executor thread, and creating a task
        from there is not safe.
        """
        self._retry = None
        self.hass.async_create_task(self._apply())

    def _report_sensor(self, lost: bool) -> None:
        """A heating system that fails silent in winter is not acceptable."""
        issue = f"sensor_lost_{self._entry.entry_id}"
        if lost:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                issue,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="sensor_lost",
                translation_placeholders={
                    "room": self._entry.title,
                    "sensor": self._sensor or "",
                },
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, issue)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            if last.state in self.hvac_modes:
                self._mode = HVACMode(last.state)
            self._target = last.attributes.get("temperature") or self._target

        sources = [
            entity
            for entity in (self._sensor, self._humidity, self._cooler)
            if entity
        ]

        @callback
        def _changed(_: Event) -> None:
            self.hass.async_create_task(self._apply())

        if sources:
            self.async_on_remove(
                async_track_state_change_event(self.hass, sources, _changed)
            )
        self.async_on_remove(
            async_track_time_interval(self.hass, self._wake, TICK)
        )
        self.async_on_remove(lambda: self._schedule_retry(None))
        await self._apply()
