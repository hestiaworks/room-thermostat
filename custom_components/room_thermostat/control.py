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
    warm_on: float
    warm_off: float


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
    sensor_lost: bool
    # Seconds until a change held back by a minimum time could be made.
    # Nothing else would wake the loop at that moment.
    retry_after: float | None
    state: LoopState


def _switch(
    wants_on: bool,
    currently_on: bool,
    changed_at: float,
    now: float,
    min_on: float,
    min_off: float,
) -> tuple[bool, float]:
    """Apply minimum on and off times to a desired state.

    Temperature decides what we want; these decide whether we are allowed to
    act on it yet. Without them a sensor that wobbles by a tenth of a degree
    chatters a valve or short-cycles a compressor.

    Returns what to do and, when a change was refused, how long until it would
    be allowed — so the caller can come back rather than leaving the change
    waiting for whatever happens to run the loop next.
    """
    if wants_on == currently_on:
        return currently_on, 0.0
    elapsed = now - changed_at
    if currently_on and elapsed < min_on:
        return True, min_on - elapsed
    if not currently_on and elapsed < min_off:
        return False, min_off - elapsed
    return wants_on, 0.0


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


def _warm_through(state: LoopState, now: float, config: RoomConfig) -> bool:
    """A blind duty cycle for a room whose sensor has gone.

    Deliberately slow in both directions: without a reading we cannot tell
    whether the room is at 4 degrees or 24, so this must be incapable of doing
    much harm either way while still being incapable of letting a pipe freeze.
    """
    elapsed = now - state.heaters_changed_at
    if state.heaters_on:
        return elapsed < config.warm_on
    return elapsed >= config.warm_off


def _cool(
    config: RoomConfig,
    readings: Readings,
    target: float,
    state: LoopState,
    now: float,
) -> tuple[bool, CoolerCommand, float]:
    room = readings.room_temperature
    if config.cooling_strategy == "gated":
        on, held = _switch(
            _wants_cool(room, target, state.cooler_on, config),
            state.cooler_on,
            state.cooler_changed_at,
            now,
            config.cool_min_on,
            config.cool_min_off,
        )
        if on:
            return (
                True,
                CoolerCommand(hvac_mode="cool", target=config.parked_setpoint),
                held,
            )
        return False, CoolerCommand(hvac_mode="off", target=None), held
    return (
        True,
        CoolerCommand(hvac_mode="cool", target=_corrected_target(target, readings, config)),
        0.0,
    )


def decide(
    config: RoomConfig,
    readings: Readings,
    request: Request,
    state: LoopState,
    now: float,
) -> Decision:
    room = readings.room_temperature
    sensor_lost = room is None
    heaters_on = False
    cooler: CoolerCommand | None = None
    cooler_on = False
    mode = request.hvac_mode
    holds: list[float] = []

    if mode in ("dry", "fan_only") and config.has_cooler:
        cooler = CoolerCommand(hvac_mode=mode, target=None)

    elif mode == "heat" and room is not None:
        target = request.target if request.target is not None else 21.0
        wants = _wants_heat(room, target, state.heaters_on, config)
        if config.has_cooler and config.allow_ac_heat:
            # Either/or: the unit heats this room, so the valves stay shut.
            cooler_on, held = _switch(
                wants,
                state.cooler_on,
                state.cooler_changed_at,
                now,
                config.cool_min_on,
                config.cool_min_off,
            )
            holds.append(held)
            cooler = (
                CoolerCommand(hvac_mode="heat", target=target)
                if cooler_on
                else CoolerCommand(hvac_mode="off", target=None)
            )
        elif config.has_heater:
            heaters_on, held = _switch(
                wants,
                state.heaters_on,
                state.heaters_changed_at,
                now,
                config.heat_min_on,
                config.heat_min_off,
            )
            holds.append(held)

    elif mode == "cool" and config.has_cooler and room is not None:
        target = request.target if request.target is not None else 24.0
        cooler_on, cooler, held = _cool(config, readings, target, state, now)
        holds.append(held)

    elif mode == "heat_cool" and room is not None:
        low = request.target_low if request.target_low is not None else 20.0
        high = request.target_high if request.target_high is not None else 25.0
        # Below the low setpoint we heat, above the high one we cool, and
        # between them neither runs — so the two can never oppose each other.
        if config.has_heater and _wants_heat(room, low, state.heaters_on, config):
            heaters_on, held = _switch(
                True,
                state.heaters_on,
                state.heaters_changed_at,
                now,
                config.heat_min_on,
                config.heat_min_off,
            )
            holds.append(held)
        elif config.has_cooler and _wants_cool(room, high, state.cooler_on, config):
            cooler_on, cooler, held = _cool(config, readings, high, state, now)
            holds.append(held)

    if sensor_lost and config.has_heater and request.hvac_mode != "off":
        heaters_on = _warm_through(state, now, config)

    # Frost protection overrides intent, which is the point of it: a
    # thermostat switched off must not be able to freeze a pipe. It applies in
    # every mode, and only a room with a heater can be protected.
    frost_active = False
    if config.has_heater and room is not None:
        release = config.frost_temperature + config.frost_recovery
        below = room < config.frost_temperature
        recovering = state.heaters_on and room < release
        if below or recovering:
            frost_active = True
            heaters_on = True

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

    if frost_active:
        action = ACTION_HEATING
    elif mode == "off":
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
        frost_active=frost_active,
        hvac_action=action,
        sensor_lost=sensor_lost,
        # The soonest release, so a change is not left waiting past it.
        retry_after=min((h for h in holds if h > 0), default=None),
        state=next_state,
    )
