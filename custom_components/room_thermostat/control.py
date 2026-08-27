"""Every decision this integration makes, with nothing else in the way.

This module imports nothing from Home Assistant and never reads the clock. It
is given readings, configuration, what the user asked for and the current time,
and it returns what each device should do. That is what lets the interesting
behaviour — minimum run times, valve travel, frost protection — be tested in
milliseconds instead of against a house.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

# hvac_action values, matching Home Assistant's climate constants without
# importing them.
ACTION_OFF = "off"
ACTION_IDLE = "idle"
ACTION_HEATING = "heating"
ACTION_COOLING = "cooling"
ACTION_DRYING = "drying"
ACTION_FAN = "fan"

# The largest sensor error the offset correction will believe. Beyond this a
# unit is not merely miscalibrated — it is sensing its own return air — and
# correcting for it feeds back on itself.
MAX_OFFSET = 3.0


@dataclass(frozen=True)
class RoomConfig:
    has_cooler: bool
    has_heater: bool
    cooling_strategy: str
    offset_correction: bool
    parked_setpoint: float
    cool_cold_tolerance: float
    cool_hot_tolerance: float
    cool_min_on: float
    cool_min_off: float
    heat_cold_tolerance: float
    heat_hot_tolerance: float
    heat_min_on: float
    heat_min_off: float
    valve_travel: float
    allow_ac_heat: bool
    frost_temperature: float
    frost_recovery: float


@dataclass(frozen=True)
class Readings:
    room_temperature: float | None
    room_humidity: float | None
    cooler_temperature: float | None


@dataclass(frozen=True)
class Request:
    hvac_mode: str
    target: float | None
    target_low: float | None
    target_high: float | None


@dataclass(frozen=True)
class LoopState:
    heaters_on: bool
    heaters_changed_at: float
    cooler_on: bool
    cooler_changed_at: float


@dataclass(frozen=True)
class CoolerCommand:
    hvac_mode: str
    target: float | None


@dataclass(frozen=True)
class Decision:
    heaters_on: bool
    cooler: CoolerCommand | None
    heat_demand: bool
    frost_active: bool
    hvac_action: str
    state: LoopState


def _switch(
    wants_on: bool,
    currently_on: bool,
    changed_at: float,
    now: float,
    min_on: float,
    min_off: float,
) -> bool:
    """Apply minimum on and off times to a desired state.

    Temperature decides what we want; these decide whether we are allowed to
    act on it yet. Without them a sensor that wobbles by a tenth of a degree
    chatters a valve or short-cycles a compressor.
    """
    if wants_on == currently_on:
        return currently_on
    elapsed = now - changed_at
    if currently_on and elapsed < min_on:
        return True
    if not currently_on and elapsed < min_off:
        return False
    return wants_on


def _wants_heat(
    room: float, target: float, currently_on: bool, config: RoomConfig
) -> bool:
    """Hysteresis: separate tolerances, because floors overshoot far more than
    they undershoot."""
    if currently_on:
        return room < target + config.heat_hot_tolerance
    return room <= target - config.heat_cold_tolerance


def _wants_cool(
    room: float, target: float, currently_on: bool, config: RoomConfig
) -> bool:
    if currently_on:
        return room > target - config.cool_hot_tolerance
    return room >= target + config.cool_cold_tolerance


def _corrected_target(target: float, readings: Readings, config: RoomConfig) -> float:
    """Aim the unit at the room rather than at its own sensor."""
    if not config.offset_correction or readings.cooler_temperature is None:
        return target
    if readings.room_temperature is None:
        return target
    offset = readings.room_temperature - readings.cooler_temperature
    offset = max(-MAX_OFFSET, min(MAX_OFFSET, offset))
    return target - offset


def _cool(
    config: RoomConfig,
    readings: Readings,
    target: float,
    state: LoopState,
    now: float,
) -> tuple[bool, CoolerCommand]:
    room = readings.room_temperature
    if config.cooling_strategy == "gated":
        on = _switch(
            _wants_cool(room, target, state.cooler_on, config),
            state.cooler_on,
            state.cooler_changed_at,
            now,
            config.cool_min_on,
            config.cool_min_off,
        )
        if on:
            return True, CoolerCommand(hvac_mode="cool", target=config.parked_setpoint)
        return False, CoolerCommand(hvac_mode="off", target=None)
    return True, CoolerCommand(
        hvac_mode="cool", target=_corrected_target(target, readings, config)
    )


def decide(
    config: RoomConfig,
    readings: Readings,
    request: Request,
    state: LoopState,
    now: float,
) -> Decision:
    room = readings.room_temperature
    heaters_on = False
    cooler: CoolerCommand | None = None
    cooler_on = False
    mode = request.hvac_mode

    if mode in ("dry", "fan_only") and config.has_cooler:
        cooler = CoolerCommand(hvac_mode=mode, target=None)

    elif mode == "heat" and room is not None:
        target = request.target if request.target is not None else 21.0
        wants = _wants_heat(room, target, state.heaters_on, config)
        if config.has_cooler and config.allow_ac_heat:
            # Either/or: the unit heats this room, so the valves stay shut.
            cooler_on = _switch(
                wants,
                state.cooler_on,
                state.cooler_changed_at,
                now,
                config.cool_min_on,
                config.cool_min_off,
            )
            cooler = (
                CoolerCommand(hvac_mode="heat", target=target)
                if cooler_on
                else CoolerCommand(hvac_mode="off", target=None)
            )
        elif config.has_heater:
            heaters_on = _switch(
                wants,
                state.heaters_on,
                state.heaters_changed_at,
                now,
                config.heat_min_on,
                config.heat_min_off,
            )

    elif mode == "cool" and config.has_cooler and room is not None:
        target = request.target if request.target is not None else 24.0
        cooler_on, cooler = _cool(config, readings, target, state, now)

    elif mode == "heat_cool" and room is not None:
        low = request.target_low if request.target_low is not None else 20.0
        high = request.target_high if request.target_high is not None else 25.0
        # Below the low setpoint we heat, above the high one we cool, and
        # between them neither runs — so the two can never oppose each other.
        if config.has_heater and _wants_heat(room, low, state.heaters_on, config):
            heaters_on = _switch(
                True,
                state.heaters_on,
                state.heaters_changed_at,
                now,
                config.heat_min_on,
                config.heat_min_off,
            )
        elif config.has_cooler and _wants_cool(room, high, state.cooler_on, config):
            cooler_on, cooler = _cool(config, readings, high, state, now)

    if config.has_cooler and cooler is None:
        cooler = CoolerCommand(hvac_mode="off", target=None)

    changed_at = now if heaters_on != state.heaters_on else state.heaters_changed_at
    cooler_changed_at = (
        now if cooler_on != state.cooler_on else state.cooler_changed_at
    )
    next_state = replace(
        state,
        heaters_on=heaters_on,
        heaters_changed_at=changed_at,
        cooler_on=cooler_on,
        cooler_changed_at=cooler_changed_at,
    )

    # Demand means the valve has had time to physically open, not that its
    # switch was energised.
    demand = heaters_on and (now - changed_at) >= config.valve_travel

    if mode == "off":
        action = ACTION_OFF
    elif mode == "dry":
        action = ACTION_DRYING
    elif mode == "fan_only":
        action = ACTION_FAN
    elif heaters_on or (cooler is not None and cooler.hvac_mode == "heat"):
        action = ACTION_HEATING
    elif cooler_on and cooler is not None and cooler.hvac_mode == "cool":
        action = ACTION_COOLING
    else:
        action = ACTION_IDLE

    return Decision(
        heaters_on=heaters_on,
        cooler=cooler,
        heat_demand=demand,
        frost_active=False,
        hvac_action=action,
        state=next_state,
    )
