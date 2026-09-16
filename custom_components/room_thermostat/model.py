"""What a room is, and what a house is, with nothing else in the way.

These are the records the page edits and the store holds. Like control.py this
module imports nothing from Home Assistant: a room is a description, and
describing one badly is something that can be checked without a running house.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any

from .const import (
    CONTROLS,
    DEFAULT_COOL_LIMIT,
    DEFAULT_COOL_MIN_OFF,
    DEFAULT_COOL_MIN_ON,
    DEFAULT_COOL_TOLERANCE,
    DEFAULT_DAMPING_HOURS,
    DEFAULT_FROST_TEMPERATURE,
    DEFAULT_HEAT_LIMIT,
    DEFAULT_HEAT_MIN_OFF,
    DEFAULT_HEAT_MIN_ON,
    DEFAULT_HEAT_TOLERANCE,
    DEFAULT_LIMIT_HYSTERESIS,
    DEFAULT_PARKED_SETPOINT,
    DEFAULT_SEASON_DWELL_HOURS,
    DEFAULT_SEASON_OVERRIDE,
    DEFAULT_VALVE_TRAVEL,
    STRATEGY_PASSTHROUGH,
)

# The keys that are lists in the record and tuples in the record class, because
# a frozen dataclass that hashes is worth more than the convenience.
_SEQUENCES = ("heaters", "inverted_heaters", "visible_controls")


def _known(cls: type, data: dict[str, Any]) -> dict[str, Any]:
    """Only the keys this record has.

    A record read back from the store may carry a key a later version dropped,
    and a page may send one this version has never heard of. Neither is worth
    failing a house over.
    """
    names = {field.name for field in fields(cls)}
    return {key: value for key, value in data.items() if key in names}


@dataclass(frozen=True)
class Room:
    """One room, exactly as the page describes it."""

    id: str
    name: str = ""
    temperature_sensor: str | None = None
    humidity_sensor: str | None = None
    cooler: str | None = None
    heaters: tuple[str, ...] = ()
    inverted_heaters: tuple[str, ...] = ()
    visible_controls: tuple[str, ...] = CONTROLS
    cooling_strategy: str = STRATEGY_PASSTHROUGH
    offset_correction: bool = False
    parked_setpoint: float = DEFAULT_PARKED_SETPOINT
    cool_cold_tolerance: float = DEFAULT_COOL_TOLERANCE
    cool_hot_tolerance: float = DEFAULT_COOL_TOLERANCE
    cool_min_on: float = DEFAULT_COOL_MIN_ON
    cool_min_off: float = DEFAULT_COOL_MIN_OFF
    heat_cold_tolerance: float = DEFAULT_HEAT_TOLERANCE
    heat_hot_tolerance: float = DEFAULT_HEAT_TOLERANCE
    heat_min_on: float = DEFAULT_HEAT_MIN_ON
    heat_min_off: float = DEFAULT_HEAT_MIN_OFF
    valve_travel: float = DEFAULT_VALVE_TRAVEL
    allow_ac_heat: bool = False
    frost_temperature: float = DEFAULT_FROST_TEMPERATURE

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Room:
        known = _known(cls, data)
        for key in _SEQUENCES:
            if known.get(key) is not None:
                known[key] = tuple(known[key])
        return cls(**known)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in _SEQUENCES:
            data[key] = list(data[key])
        return data


@dataclass(frozen=True)
class House:
    """What the whole house decides once."""

    outdoor_sensor: str | None = None
    damping_hours: float = DEFAULT_DAMPING_HOURS
    season_dwell_hours: float = DEFAULT_SEASON_DWELL_HOURS
    heat_limit: float = DEFAULT_HEAT_LIMIT
    heat_limit_hysteresis: float = DEFAULT_LIMIT_HYSTERESIS
    cool_limit: float = DEFAULT_COOL_LIMIT
    cool_limit_hysteresis: float = DEFAULT_LIMIT_HYSTERESIS
    heat_override: float = DEFAULT_SEASON_OVERRIDE
    cool_override: float = DEFAULT_SEASON_OVERRIDE

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> House:
        return cls(**_known(cls, data))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def room_problems(data: dict[str, Any], *, own_entity_ids: set[str]) -> dict[str, str]:
    """What is wrong with a room the page is trying to save.

    Field name to error key, for the page to render beside the field. The
    checks are the ones the config flow made, with the "is this one of ours"
    question turned into a set so this stays free of Home Assistant.
    """
    if not str(data.get("name") or "").strip():
        return {"name": "required"}
    if not data.get("temperature_sensor"):
        return {"temperature_sensor": "required"}
    cooler = data.get("cooler")
    if cooler and cooler in own_entity_ids:
        # A room driving one of these would drive itself, and the loop is not
        # visible from the page.
        return {"cooler": "own_entity"}
    if not cooler and not data.get("heaters"):
        # A room that can neither heat nor cool is a thermometer.
        return {"base": "no_devices"}
    return {}
