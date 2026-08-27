# Room Thermostat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Home Assistant custom integration providing one climate entity per room that cools with an air conditioner and heats with valves, without flattening either device down to a switch.

**Architecture:** All decision-making lives in `control.py`, a pure module with no Home Assistant imports: it takes readings, configuration, the user's request and a clock, and returns what each device should do. Everything else — config flow, climate entity, binary sensor — is a thin adapter over it. That boundary is what makes the interesting behaviour testable in milliseconds without hardware or a running Home Assistant.

**Tech Stack:** Python 3.13, Home Assistant 2025.6.0+, pytest, pytest-homeassistant-custom-component, HACS.

**Spec:** `docs/superpowers/specs/2026-08-27-room-thermostat-design.md`

## Global Constraints

- Integration domain is `room_thermostat`. Repository is `hestiaworks/room-thermostat`. **Neither may be renamed after release** — renaming orphans every config entry.
- `control.py` must import nothing from `homeassistant`. This is checked by a test, not by convention.
- Time is always passed in as a `now: float` monotonic seconds argument. `control.py` must never call `time.monotonic()` itself, or its behaviour cannot be tested.
- No real LAN addresses in tests, docs or defaults. Use RFC 5737 documentation ranges (`192.0.2.0/24`).
- Commits are authored by the directory rule in `~/.gitconfig`. Do **not** set `user.name` or `user.email` in this repository.
- The remote, when added, is `git@github-hestia:hestiaworks/room-thermostat.git`.
- Defaults, verbatim from the spec: parked setpoint 17 °C; gated cool tolerances 0.5 °C either side with a 15-minute minimum run; radiator heat tolerances 0.3 °C either side with 5-minute minimums; floor heat minimums 20–30 minutes; valve travel 180 s; frost protection 5 °C; setpoint offset correction **off** by default; allow-AC-to-heat **off** by default.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `custom_components/room_thermostat/control.py` | **All decision logic.** Pure. No HA imports. |
| `custom_components/room_thermostat/const.py` | Domain, config keys, defaults. No logic. |
| `custom_components/room_thermostat/config_flow.py` | Config and options flow. |
| `custom_components/room_thermostat/climate.py` | The climate entity — reads state, calls `control.decide`, issues service calls. |
| `custom_components/room_thermostat/binary_sensor.py` | The heat demand entity. |
| `custom_components/room_thermostat/__init__.py` | Entry setup and unload, shared runtime data, repair issues. |
| `custom_components/room_thermostat/manifest.json` | Integration metadata. |
| `custom_components/room_thermostat/translations/en.json` | Config flow strings. |
| `hacs.json` | HACS metadata. |
| `.github/workflows/validate.yml` | hassfest + HACS validation + pytest. |
| `tests/test_control.py` | The bulk of the testing. Pure, fast. |
| `tests/test_config_flow.py` | Config flow wiring. |
| `tests/test_climate.py` | Entity wiring over a stubbed `decide`. |

`control.py` is deliberately the largest file and everything else is deliberately thin. Splitting the logic across `climate.py` and `binary_sensor.py` would put the same rules in two places and make neither testable alone.

---

### Task 1: Repository skeleton that validates

**Files:**
- Create: `custom_components/room_thermostat/__init__.py`
- Create: `custom_components/room_thermostat/manifest.json`
- Create: `custom_components/room_thermostat/const.py`
- Create: `hacs.json`
- Create: `.github/workflows/validate.yml`
- Create: `requirements-test.txt`
- Create: `README.md`
- Create: `.gitignore`
- Test: `tests/test_manifest.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `DOMAIN = "room_thermostat"` in `const.py`, imported by every later task.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_manifest.py
"""The manifest is what HACS and hassfest validate; a typo here fails at install."""
import json
from pathlib import Path

MANIFEST = Path(__file__).parents[1] / "custom_components/room_thermostat/manifest.json"


def test_manifest_declares_the_domain_that_must_never_change():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["domain"] == "room_thermostat"
    assert manifest["config_flow"] is True


def test_manifest_keys_are_sorted_as_hassfest_requires():
    # hassfest requires: domain, name, then the rest alphabetically.
    keys = list(json.loads(MANIFEST.read_text()))
    assert keys[:2] == ["domain", "name"]
    assert keys[2:] == sorted(keys[2:])


def test_const_exposes_the_domain():
    from custom_components.room_thermostat.const import DOMAIN

    assert DOMAIN == "room_thermostat"
```

- [ ] **Step 2: Run it to see it fail**

Run: `python -m pytest tests/test_manifest.py -v`
Expected: FAIL — `FileNotFoundError` for the manifest.

- [ ] **Step 3: Create the package**

```json
// custom_components/room_thermostat/manifest.json
{
  "domain": "room_thermostat",
  "name": "Room Thermostat",
  "codeowners": ["@theseus-elysium"],
  "config_flow": true,
  "documentation": "https://github.com/hestiaworks/room-thermostat",
  "integration_type": "helper",
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/hestiaworks/room-thermostat/issues",
  "requirements": [],
  "version": "0.1.0"
}
```

```python
# custom_components/room_thermostat/const.py
"""Names and defaults. No logic lives here."""

DOMAIN = "room_thermostat"

CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_COOLER = "cooler"
CONF_HEATERS = "heaters"
CONF_VALVE_TRAVEL = "valve_travel"
CONF_COOLING_STRATEGY = "cooling_strategy"
CONF_OFFSET_CORRECTION = "offset_correction"
CONF_PARKED_SETPOINT = "parked_setpoint"
CONF_COOL_COLD_TOLERANCE = "cool_cold_tolerance"
CONF_COOL_HOT_TOLERANCE = "cool_hot_tolerance"
CONF_COOL_MIN_ON = "cool_min_on"
CONF_COOL_MIN_OFF = "cool_min_off"
CONF_HEAT_COLD_TOLERANCE = "heat_cold_tolerance"
CONF_HEAT_HOT_TOLERANCE = "heat_hot_tolerance"
CONF_HEAT_MIN_ON = "heat_min_on"
CONF_HEAT_MIN_OFF = "heat_min_off"
CONF_ALLOW_AC_HEAT = "allow_ac_heat"
CONF_FROST_TEMPERATURE = "frost_temperature"

STRATEGY_PASSTHROUGH = "passthrough"
STRATEGY_GATED = "gated"

# Verbatim from the spec.
DEFAULT_VALVE_TRAVEL = 180.0
DEFAULT_PARKED_SETPOINT = 17.0
DEFAULT_COOL_TOLERANCE = 0.5
DEFAULT_COOL_MIN_ON = 900.0
DEFAULT_COOL_MIN_OFF = 900.0
DEFAULT_HEAT_TOLERANCE = 0.3
DEFAULT_HEAT_MIN_ON = 300.0
DEFAULT_HEAT_MIN_OFF = 300.0
DEFAULT_FROST_TEMPERATURE = 5.0
# How far above the frost temperature the room must climb before frost
# protection releases, so it cannot chatter at the threshold.
DEFAULT_FROST_RECOVERY = 1.0
```

```python
# custom_components/room_thermostat/__init__.py
"""Room Thermostat integration."""
```

```json
// hacs.json
{
  "name": "Room Thermostat",
  "render_readme": true,
  "homeassistant": "2025.6.0"
}
```

```
# requirements-test.txt
pytest
pytest-homeassistant-custom-component
```

```
# .gitignore
__pycache__/
*.pyc
.pytest_cache/
.venv/
```

```markdown
<!-- README.md -->
# Room Thermostat

One Home Assistant climate entity per room that **cools with an air
conditioner and heats with something else** — valves, a boiler loop, a heated
floor — without flattening either device down to a switch.

Unlike wrapping an air conditioner in a generic thermostat, this keeps
everything the unit can do: dry and fan-only modes, fan speeds, both swing
axes and presets are mirrored from the underlying climate entity rather than
replaced with a fixed list. Temperature and humidity come from your own room
sensors, not the unit's internal one.

See `docs/superpowers/specs/` for the design and the reasoning behind it.
```

```yaml
# .github/workflows/validate.yml
name: Validate

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  hassfest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: home-assistant/actions/hassfest@master

  hacs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hacs/action@main
        with:
          category: integration

  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: pip install -r requirements-test.txt
      - run: python -m pytest -v
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python -m pytest tests/test_manifest.py -v`
Expected: PASS, 3 tests.

- [ ] **Step 5: Commit**

```bash
git add custom_components hacs.json .github requirements-test.txt README.md .gitignore tests
git commit -m "Add the integration skeleton and its validation"
```

---

### Task 2: Heating — hysteresis with minimum times

**Files:**
- Create: `custom_components/room_thermostat/control.py`
- Test: `tests/test_control.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces, all used by every later task:
  - `RoomConfig` frozen dataclass (fields as written below)
  - `Readings` frozen dataclass: `room_temperature: float | None`, `room_humidity: float | None`, `cooler_temperature: float | None`
  - `Request` frozen dataclass: `hvac_mode: str`, `target: float | None`, `target_low: float | None`, `target_high: float | None`
  - `LoopState` frozen dataclass: `heaters_on: bool`, `heaters_changed_at: float`, `cooler_on: bool`, `cooler_changed_at: float`
  - `Decision` frozen dataclass: `heaters_on: bool`, `cooler: CoolerCommand | None`, `heat_demand: bool`, `frost_active: bool`, `hvac_action: str`, `state: LoopState`
  - `CoolerCommand` frozen dataclass: `hvac_mode: str`, `target: float | None`
  - `decide(config: RoomConfig, readings: Readings, request: Request, state: LoopState, now: float) -> Decision`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_control.py
"""The rules, tested without Home Assistant or hardware."""
import pytest

from custom_components.room_thermostat.control import (
    CoolerCommand,
    Decision,
    LoopState,
    Readings,
    Request,
    RoomConfig,
    decide,
)


def config(**overrides) -> RoomConfig:
    """A radiator room with no cooler, unless a test says otherwise."""
    base = dict(
        has_cooler=False,
        has_heater=True,
        cooling_strategy="passthrough",
        offset_correction=False,
        parked_setpoint=17.0,
        cool_cold_tolerance=0.5,
        cool_hot_tolerance=0.5,
        cool_min_on=900.0,
        cool_min_off=900.0,
        heat_cold_tolerance=0.3,
        heat_hot_tolerance=0.3,
        heat_min_on=300.0,
        heat_min_off=300.0,
        valve_travel=180.0,
        allow_ac_heat=False,
        frost_temperature=5.0,
        frost_recovery=1.0,
    )
    return RoomConfig(**{**base, **overrides})


def idle(now: float = 0.0) -> LoopState:
    return LoopState(
        heaters_on=False, heaters_changed_at=now, cooler_on=False, cooler_changed_at=now
    )


def heating_since(when: float) -> LoopState:
    return LoopState(
        heaters_on=True, heaters_changed_at=when, cooler_on=False, cooler_changed_at=when
    )


def test_control_module_stays_free_of_home_assistant():
    """The boundary that makes everything above testable in milliseconds."""
    import inspect

    from custom_components.room_thermostat import control

    source = inspect.getsource(control)
    assert "homeassistant" not in source


def test_a_cold_room_calls_for_heat():
    decision = decide(
        config(),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is True
    assert decision.hvac_action == "heating"


def test_a_room_inside_the_deadband_is_left_alone():
    # 20.9 is above target minus the 0.3 cold tolerance, so nothing starts.
    decision = decide(
        config(),
        Readings(room_temperature=20.9, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is False
    assert decision.hvac_action == "idle"


def test_heat_releases_only_above_the_hot_tolerance():
    warm = decide(
        config(),
        Readings(room_temperature=21.4, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        heating_since(0.0),
        now=1000.0,
    )
    assert warm.heaters_on is False

    not_yet = decide(
        config(),
        Readings(room_temperature=21.2, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        heating_since(0.0),
        now=1000.0,
    )
    assert not_yet.heaters_on is True


def test_a_minimum_run_time_outranks_the_temperature():
    """A slab that has just started must not be stopped by a passing draught."""
    decision = decide(
        config(heat_min_on=1800.0),
        Readings(room_temperature=25.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        heating_since(900.0),
        now=1200.0,
    )
    assert decision.heaters_on is True


def test_a_minimum_off_time_outranks_the_temperature():
    just_stopped = LoopState(
        heaters_on=False, heaters_changed_at=1100.0, cooler_on=False, cooler_changed_at=0.0
    )
    decision = decide(
        config(heat_min_off=1800.0),
        Readings(room_temperature=10.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        just_stopped,
        now=1200.0,
    )
    assert decision.heaters_on is False


def test_the_state_records_when_the_valves_last_changed():
    decision = decide(
        config(),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(now=0.0),
        now=1000.0,
    )
    assert decision.state.heaters_on is True
    assert decision.state.heaters_changed_at == 1000.0


def test_state_is_carried_forward_when_nothing_changes():
    decision = decide(
        config(),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        heating_since(400.0),
        now=1000.0,
    )
    assert decision.state.heaters_changed_at == 400.0


def test_demand_waits_for_the_valve_to_travel():
    """A boiler that fires when the switch closes pushes into a shut circuit."""
    opening = decide(
        config(valve_travel=180.0),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        heating_since(1000.0),
        now=1090.0,
    )
    assert opening.heaters_on is True
    assert opening.heat_demand is False

    opened = decide(
        config(valve_travel=180.0),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        heating_since(1000.0),
        now=1200.0,
    )
    assert opened.heat_demand is True


def test_off_closes_the_valves():
    decision = decide(
        config(),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="off", target=21.0, target_low=None, target_high=None),
        heating_since(0.0),
        now=1000.0,
    )
    assert decision.heaters_on is False
    assert decision.heat_demand is False
    assert decision.hvac_action == "off"
```

- [ ] **Step 2: Run them to see them fail**

Run: `python -m pytest tests/test_control.py -v`
Expected: FAIL — `ModuleNotFoundError: custom_components.room_thermostat.control`.

- [ ] **Step 3: Write the module**

```python
# custom_components/room_thermostat/control.py
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


def decide(
    config: RoomConfig,
    readings: Readings,
    request: Request,
    state: LoopState,
    now: float,
) -> Decision:
    room = readings.room_temperature
    heaters_on = False

    if request.hvac_mode == "heat" and config.has_heater and room is not None:
        target = request.target if request.target is not None else 21.0
        heaters_on = _switch(
            _wants_heat(room, target, state.heaters_on, config),
            state.heaters_on,
            state.heaters_changed_at,
            now,
            config.heat_min_on,
            config.heat_min_off,
        )

    changed_at = (
        now if heaters_on != state.heaters_on else state.heaters_changed_at
    )
    next_state = replace(
        state, heaters_on=heaters_on, heaters_changed_at=changed_at
    )

    # Demand means the valve has had time to physically open, not that its
    # switch was energised.
    demand = heaters_on and (now - changed_at) >= config.valve_travel

    if request.hvac_mode == "off":
        action = ACTION_OFF
    elif heaters_on:
        action = ACTION_HEATING
    else:
        action = ACTION_IDLE

    return Decision(
        heaters_on=heaters_on,
        cooler=None,
        heat_demand=demand,
        frost_active=False,
        hvac_action=action,
        state=next_state,
    )
```

- [ ] **Step 4: Run them to see them pass**

Run: `python -m pytest tests/test_control.py -v`
Expected: PASS, 10 tests.

- [ ] **Step 5: Commit**

```bash
git add custom_components/room_thermostat/control.py tests/test_control.py
git commit -m "Decide heating from hysteresis, minimum times and valve travel"
```

---

### Task 3: Cooling — pass-through and gated

**Files:**
- Modify: `custom_components/room_thermostat/control.py`
- Test: `tests/test_control.py`

**Interfaces:**
- Consumes: everything Task 2 produced.
- Produces: `decide` now returns a `CoolerCommand` in cooling modes. No new types.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_control.py`:

```python
def cooling_config(**overrides) -> RoomConfig:
    return config(has_cooler=True, has_heater=False, **overrides)


def test_passthrough_forwards_the_target_and_lets_the_unit_modulate():
    """An inverter unit regulates itself; we only tell it what to aim for."""
    decision = decide(
        cooling_config(cooling_strategy="passthrough"),
        Readings(room_temperature=26.0, room_humidity=None, cooler_temperature=24.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler == CoolerCommand(hvac_mode="cool", target=22.0)
    assert decision.hvac_action == "cooling"


def test_offset_correction_is_off_unless_asked_for():
    decision = decide(
        cooling_config(cooling_strategy="passthrough", offset_correction=False),
        Readings(room_temperature=26.0, room_humidity=None, cooler_temperature=24.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler.target == 22.0


def test_offset_correction_aims_at_the_room_not_the_unit():
    """The unit reads 2 degrees cool, so 22 in the room means asking for 20."""
    decision = decide(
        cooling_config(cooling_strategy="passthrough", offset_correction=True),
        Readings(room_temperature=26.0, room_humidity=None, cooler_temperature=24.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler.target == 20.0


def test_offset_correction_is_clamped_so_it_cannot_run_away():
    """A cabinet-mounted unit's offset grows without limit; the clamp is the
    backstop that keeps a misconfigured room merely wrong, not destructive."""
    decision = decide(
        cooling_config(cooling_strategy="passthrough", offset_correction=True),
        Readings(room_temperature=26.0, room_humidity=None, cooler_temperature=18.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler.target == 19.0


def test_gated_parks_the_unit_low_and_runs_it_against_the_room():
    decision = decide(
        cooling_config(cooling_strategy="gated", parked_setpoint=17.0),
        Readings(room_temperature=26.0, room_humidity=None, cooler_temperature=22.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler == CoolerCommand(hvac_mode="cool", target=17.0)
    assert decision.state.cooler_on is True


def test_gated_stops_the_unit_once_the_room_is_cool_enough():
    running = LoopState(
        heaters_on=False, heaters_changed_at=0.0, cooler_on=True, cooler_changed_at=0.0
    )
    decision = decide(
        cooling_config(cooling_strategy="gated"),
        Readings(room_temperature=21.4, room_humidity=None, cooler_temperature=20.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        running,
        now=5000.0,
    )
    assert decision.cooler == CoolerCommand(hvac_mode="off", target=None)
    assert decision.hvac_action == "idle"


def test_a_gated_unit_four_minutes_into_a_fifteen_minute_run_does_not_stop():
    """The whole point of the minimum: these units already cycle every five to
    ten minutes, which is what we are fixing, not reproducing."""
    running = LoopState(
        heaters_on=False, heaters_changed_at=0.0, cooler_on=True, cooler_changed_at=1000.0
    )
    decision = decide(
        cooling_config(cooling_strategy="gated", cool_min_on=900.0),
        Readings(room_temperature=20.0, room_humidity=None, cooler_temperature=18.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        running,
        now=1240.0,
    )
    assert decision.cooler.hvac_mode == "cool"


def test_a_gated_unit_respects_its_minimum_off_time():
    stopped = LoopState(
        heaters_on=False, heaters_changed_at=0.0, cooler_on=False, cooler_changed_at=1000.0
    )
    decision = decide(
        cooling_config(cooling_strategy="gated", cool_min_off=900.0),
        Readings(room_temperature=28.0, room_humidity=None, cooler_temperature=24.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        stopped,
        now=1240.0,
    )
    assert decision.cooler.hvac_mode == "off"
```

- [ ] **Step 2: Run them to see them fail**

Run: `python -m pytest tests/test_control.py -v`
Expected: FAIL — the eight new tests fail with `decision.cooler is None`.

- [ ] **Step 3: Add cooling to `control.py`**

Add the clamp constant near the action constants:

```python
# The largest sensor error the offset correction will believe. Beyond this a
# unit is not merely miscalibrated — it is sensing its own return air — and
# correcting for it feeds back on itself.
MAX_OFFSET = 3.0
```

Add these helpers below `_wants_heat`:

```python
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
```

Replace the body of `decide` between the heating block and the `return` with:

```python
    cooler: CoolerCommand | None = None
    cooler_on = False

    if request.hvac_mode == "cool" and config.has_cooler and room is not None:
        target = request.target if request.target is not None else 24.0
        if config.cooling_strategy == "gated":
            cooler_on = _switch(
                _wants_cool(room, target, state.cooler_on, config),
                state.cooler_on,
                state.cooler_changed_at,
                now,
                config.cool_min_on,
                config.cool_min_off,
            )
            cooler = (
                CoolerCommand(hvac_mode="cool", target=config.parked_setpoint)
                if cooler_on
                else CoolerCommand(hvac_mode="off", target=None)
            )
        else:
            cooler_on = True
            cooler = CoolerCommand(
                hvac_mode="cool", target=_corrected_target(target, readings, config)
            )

    cooler_changed_at = (
        now if cooler_on != state.cooler_on else state.cooler_changed_at
    )
    next_state = replace(
        next_state, cooler_on=cooler_on, cooler_changed_at=cooler_changed_at
    )
```

and extend the action decision:

```python
    if request.hvac_mode == "off":
        action = ACTION_OFF
    elif heaters_on:
        action = ACTION_HEATING
    elif cooler_on:
        action = ACTION_COOLING
    else:
        action = ACTION_IDLE
```

and return `cooler=cooler` instead of `cooler=None`.

- [ ] **Step 4: Run the whole file to see it pass**

Run: `python -m pytest tests/test_control.py -v`
Expected: PASS, 18 tests.

- [ ] **Step 5: Commit**

```bash
git add custom_components/room_thermostat/control.py tests/test_control.py
git commit -m "Cool by pass-through or by gating, chosen per room"
```

---

### Task 4: The remaining modes — dry, fan, auto, and heating with the air conditioner

**Files:**
- Modify: `custom_components/room_thermostat/control.py`
- Test: `tests/test_control.py`

**Interfaces:**
- Consumes: everything Tasks 2 and 3 produced.
- Produces: no new types. `decide` handles `dry`, `fan_only` and `heat_cool`, and honours `allow_ac_heat`.

- [ ] **Step 1: Write the failing tests**

```python
def test_dry_forwards_to_the_unit_and_leaves_the_valves_shut():
    decision = decide(
        config(has_cooler=True, has_heater=True),
        Readings(room_temperature=26.0, room_humidity=58.0, cooler_temperature=24.0),
        Request(hvac_mode="dry", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler == CoolerCommand(hvac_mode="dry", target=None)
    assert decision.heaters_on is False
    assert decision.hvac_action == "drying"


def test_fan_only_forwards_to_the_unit():
    decision = decide(
        config(has_cooler=True, has_heater=True),
        Readings(room_temperature=26.0, room_humidity=None, cooler_temperature=24.0),
        Request(hvac_mode="fan_only", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler == CoolerCommand(hvac_mode="fan_only", target=None)
    assert decision.hvac_action == "fan"


def test_heat_uses_the_valves_and_never_the_unit_by_default():
    decision = decide(
        config(has_cooler=True, has_heater=True, allow_ac_heat=False),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=20.0),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is True
    assert decision.cooler == CoolerCommand(hvac_mode="off", target=None)


def test_allowing_the_unit_to_heat_is_either_or_not_assist():
    """When a room heats with its air conditioner, the valves stay shut."""
    decision = decide(
        config(has_cooler=True, has_heater=True, allow_ac_heat=True),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=20.0),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is False
    assert decision.heat_demand is False
    assert decision.cooler == CoolerCommand(hvac_mode="heat", target=21.0)
    assert decision.hvac_action == "heating"


def test_auto_heats_below_the_low_setpoint():
    decision = decide(
        config(has_cooler=True, has_heater=True),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=20.0),
        Request(hvac_mode="heat_cool", target=None, target_low=20.0, target_high=25.0),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is True
    assert decision.cooler == CoolerCommand(hvac_mode="off", target=None)


def test_auto_cools_above_the_high_setpoint():
    decision = decide(
        config(has_cooler=True, has_heater=True),
        Readings(room_temperature=27.0, room_humidity=None, cooler_temperature=24.0),
        Request(hvac_mode="heat_cool", target=None, target_low=20.0, target_high=25.0),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is False
    assert decision.cooler.hvac_mode == "cool"


def test_auto_does_nothing_inside_the_dead_zone():
    """A room must not be able to fight itself."""
    decision = decide(
        config(has_cooler=True, has_heater=True),
        Readings(room_temperature=22.5, room_humidity=None, cooler_temperature=22.0),
        Request(hvac_mode="heat_cool", target=None, target_low=20.0, target_high=25.0),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is False
    assert decision.cooler == CoolerCommand(hvac_mode="off", target=None)
    assert decision.hvac_action == "idle"


def test_a_room_with_no_cooler_is_never_sent_a_cooler_command():
    decision = decide(
        config(has_cooler=False, has_heater=True),
        Readings(room_temperature=26.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler is None
```

- [ ] **Step 2: Run them to see them fail**

Run: `python -m pytest tests/test_control.py -v`
Expected: FAIL — eight failures; `dry` and `fan_only` currently produce no cooler command and `heat_cool` heats nothing.

- [ ] **Step 3: Restructure `decide` around the mode**

Replace the heating and cooling blocks with a single mode dispatch. The whole function body after `room = readings.room_temperature` becomes:

```python
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
                wants, state.cooler_on, state.cooler_changed_at, now,
                config.cool_min_on, config.cool_min_off,
            )
            cooler = (
                CoolerCommand(hvac_mode="heat", target=target)
                if cooler_on
                else CoolerCommand(hvac_mode="off", target=None)
            )
        elif config.has_heater:
            heaters_on = _switch(
                wants, state.heaters_on, state.heaters_changed_at, now,
                config.heat_min_on, config.heat_min_off,
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
                True, state.heaters_on, state.heaters_changed_at, now,
                config.heat_min_on, config.heat_min_off,
            )
        elif config.has_cooler and _wants_cool(room, high, state.cooler_on, config):
            cooler_on, cooler = _cool(config, readings, high, state, now)

    if config.has_cooler and cooler is None:
        cooler = CoolerCommand(hvac_mode="off", target=None)
```

Extract the cooling branch from Task 3 into a helper so `cool` and `heat_cool` share it:

```python
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
            state.cooler_on, state.cooler_changed_at, now,
            config.cool_min_on, config.cool_min_off,
        )
        if on:
            return True, CoolerCommand(hvac_mode="cool", target=config.parked_setpoint)
        return False, CoolerCommand(hvac_mode="off", target=None)
    return True, CoolerCommand(
        hvac_mode="cool", target=_corrected_target(target, readings, config)
    )
```

Extend the action decision to cover the new modes:

```python
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
```

- [ ] **Step 4: Run the whole file to see it pass**

Run: `python -m pytest tests/test_control.py -v`
Expected: PASS, 26 tests.

- [ ] **Step 5: Commit**

```bash
git add custom_components/room_thermostat/control.py tests/test_control.py
git commit -m "Route dry, fan, auto and optional air-conditioner heating"
```

---

### Task 5: Frost protection and losing the sensor

**Files:**
- Modify: `custom_components/room_thermostat/control.py`
- Test: `tests/test_control.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `Decision.frost_active`, and `decide` tolerating `room_temperature=None`.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_freezing_room_is_heated_even_with_the_thermostat_off():
    """Safety outranks intent. An off thermostat must not freeze a pipe."""
    decision = decide(
        config(frost_temperature=5.0),
        Readings(room_temperature=4.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="off", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.frost_active is True
    assert decision.heaters_on is True
    assert decision.hvac_action == "heating"


def test_frost_protection_holds_until_the_room_recovers():
    """Releasing at exactly the threshold would chatter the valve."""
    frosting = LoopState(
        heaters_on=True, heaters_changed_at=0.0, cooler_on=False, cooler_changed_at=0.0
    )
    still_cold = decide(
        config(frost_temperature=5.0, frost_recovery=1.0),
        Readings(room_temperature=5.4, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="off", target=21.0, target_low=None, target_high=None),
        frosting,
        now=5000.0,
    )
    assert still_cold.frost_active is True

    recovered = decide(
        config(frost_temperature=5.0, frost_recovery=1.0),
        Readings(room_temperature=6.5, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="off", target=21.0, target_low=None, target_high=None),
        frosting,
        now=5000.0,
    )
    assert recovered.frost_active is False
    assert recovered.heaters_on is False


def test_frost_protection_raises_demand_like_any_other_call_for_heat():
    frosting = LoopState(
        heaters_on=True, heaters_changed_at=1000.0, cooler_on=False, cooler_changed_at=0.0
    )
    decision = decide(
        config(valve_travel=180.0),
        Readings(room_temperature=4.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="off", target=21.0, target_low=None, target_high=None),
        frosting,
        now=1200.0,
    )
    assert decision.heat_demand is True


def test_a_room_with_no_heater_cannot_be_frost_protected():
    decision = decide(
        config(has_heater=False, has_cooler=True),
        Readings(room_temperature=4.0, room_humidity=None, cooler_temperature=20.0),
        Request(hvac_mode="off", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.frost_active is False
    assert decision.heaters_on is False


def test_losing_the_sensor_stops_control_without_commanding_anything():
    """Never run a loop against a reading we no longer have."""
    running = LoopState(
        heaters_on=True, heaters_changed_at=0.0, cooler_on=False, cooler_changed_at=0.0
    )
    decision = decide(
        config(),
        Readings(room_temperature=None, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        running,
        now=5000.0,
    )
    assert decision.heaters_on is False
    assert decision.hvac_action == "idle"
```

- [ ] **Step 2: Run them to see them fail**

Run: `python -m pytest tests/test_control.py -v`
Expected: FAIL — five failures; `frost_active` is hardcoded `False`.

- [ ] **Step 3: Add frost protection**

Insert immediately before the `cooler is None` fallback, so it overrides every mode including `off`:

```python
    # Frost protection overrides intent, which is the point of it: a
    # thermostat switched off must not be able to freeze a pipe. It applies
    # in every mode, and only a room with a heater can be protected.
    frost_active = False
    if config.has_heater and room is not None:
        release = config.frost_temperature + config.frost_recovery
        if room < config.frost_temperature or (state.heaters_on and room < release):
            if room < release:
                frost_active = True
                heaters_on = True
```

Then make the action reflect it by moving the frost check above the mode
checks in the action decision:

```python
    if frost_active:
        action = ACTION_HEATING
    elif mode == "off":
        action = ACTION_OFF
    ...
```

and return `frost_active=frost_active`.

The "losing the sensor" case needs no new code: every branch is already
guarded by `room is not None`, so a missing reading falls through to
`heaters_on = False` and no cooler command beyond the `off` fallback. The test
exists to hold that guarantee in place.

- [ ] **Step 4: Run the whole file to see it pass**

Run: `python -m pytest tests/test_control.py -v`
Expected: PASS, 31 tests.

- [ ] **Step 5: Commit**

```bash
git add custom_components/room_thermostat/control.py tests/test_control.py
git commit -m "Protect a freezing room whatever the thermostat is set to"
```

---

### Task 6: Warm-through when the sensor is lost

The spec requires that losing the room sensor stops normal control **without**
disabling frost protection. Task 5 satisfied the first half. This task
satisfies the second: with no reading, the room cannot be measured, so it falls
back to a conservative duty cycle and asks for human attention.

**Files:**
- Modify: `custom_components/room_thermostat/control.py`
- Test: `tests/test_control.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `RoomConfig.warm_on: float` and `RoomConfig.warm_off: float`; `Decision.sensor_lost: bool`, which Task 10 turns into a Home Assistant repair issue.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_lost_sensor_is_reported_so_a_human_hears_about_it():
    decision = decide(
        config(),
        Readings(room_temperature=None, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.sensor_lost is True


def test_a_working_sensor_is_not_reported_as_lost():
    decision = decide(
        config(),
        Readings(room_temperature=20.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.sensor_lost is False


def test_a_lost_sensor_warms_the_room_through_periodically():
    """We cannot measure the room, so we cannot leave it cold all winter
    either. A duty cycle is the compromise: it cannot overheat a room quickly
    and it cannot let one freeze slowly."""
    off_long_enough = LoopState(
        heaters_on=False, heaters_changed_at=0.0, cooler_on=False, cooler_changed_at=0.0
    )
    decision = decide(
        config(warm_on=600.0, warm_off=3000.0),
        Readings(room_temperature=None, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        off_long_enough,
        now=3000.0,
    )
    assert decision.heaters_on is True


def test_the_warm_through_stops_after_its_run():
    on_long_enough = LoopState(
        heaters_on=True, heaters_changed_at=1000.0, cooler_on=False, cooler_changed_at=0.0
    )
    decision = decide(
        config(warm_on=600.0, warm_off=3000.0),
        Readings(room_temperature=None, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        on_long_enough,
        now=1700.0,
    )
    assert decision.heaters_on is False


def test_a_room_with_no_heater_has_nothing_to_warm_through():
    decision = decide(
        config(has_heater=False, has_cooler=True),
        Readings(room_temperature=None, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=5000.0,
    )
    assert decision.heaters_on is False
    assert decision.sensor_lost is True
```

- [ ] **Step 2: Run them to see them fail**

Run: `python -m pytest tests/test_control.py -v`
Expected: FAIL — `Decision` has no attribute `sensor_lost`.

- [ ] **Step 3: Add the fallback**

Add to `RoomConfig`:

```python
    warm_on: float
    warm_off: float
```

Add to `Decision`:

```python
    sensor_lost: bool
```

Add near the other helpers:

```python
def _warm_through(state: LoopState, now: float, config: RoomConfig) -> bool:
    """A blind duty cycle for a room whose sensor has gone.

    Deliberately slow in both directions: without a reading we cannot tell
    whether the room is at 4 degrees or 24, so this must be incapable of doing
    much harm in either direction while still being incapable of letting a
    pipe freeze.
    """
    elapsed = now - state.heaters_changed_at
    if state.heaters_on:
        return elapsed < config.warm_on
    return elapsed >= config.warm_off
```

Insert immediately after `room = readings.room_temperature`, replacing nothing:

```python
    sensor_lost = room is None
```

and immediately before the frost-protection block:

```python
    if sensor_lost and config.has_heater and request.hvac_mode != "off":
        heaters_on = _warm_through(state, now, config)
```

Return `sensor_lost=sensor_lost`. Update the two `config()` helpers in the
test file to include `warm_on=600.0, warm_off=3000.0` in their defaults.

- [ ] **Step 4: Run the whole file to see it pass**

Run: `python -m pytest tests/test_control.py -v`
Expected: PASS, 36 tests.

- [ ] **Step 5: Commit**

```bash
git add custom_components/room_thermostat/control.py tests/test_control.py
git commit -m "Warm a room through blindly rather than abandon it when its sensor dies"
```

---

### Task 7: Config and options flow

**Files:**
- Create: `custom_components/room_thermostat/config_flow.py`
- Create: `custom_components/room_thermostat/translations/en.json`
- Test: `tests/test_config_flow.py`
- Create: `tests/conftest.py`

**Interfaces:**
- Consumes: the `CONF_*` and `DEFAULT_*` names from `const.py`.
- Produces: config entries whose `data` holds the room's name and sources, and whose `options` holds every tunable. Tasks 8, 9 and 10 read them by those key names.

- [ ] **Step 1: Write the failing test**

```python
# tests/conftest.py
"""pytest-homeassistant-custom-component needs custom integrations enabled."""
import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield
```

```python
# tests/test_config_flow.py
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.room_thermostat.const import (
    CONF_COOLER,
    CONF_HEATERS,
    CONF_TEMPERATURE_SENSOR,
    DEFAULT_PARKED_SETPOINT,
    DOMAIN,
)


async def test_a_room_can_be_added_with_a_sensor_and_both_devices(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
            CONF_HEATERS: ["switch.bedroom_radiator_a", "switch.bedroom_radiator_b"],
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Bedroom"
    assert result["data"][CONF_HEATERS] == [
        "switch.bedroom_radiator_a",
        "switch.bedroom_radiator_b",
    ]


async def test_a_room_needs_a_temperature_sensor(hass: HomeAssistant):
    """It is the reason the integration exists; without it there is nothing to
    control against."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Bedroom", CONF_HEATERS: ["switch.a"]}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_TEMPERATURE_SENSOR: "required"}


async def test_a_room_needs_at_least_one_device(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "Bedroom", CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature"},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "no_devices"}


async def test_tunables_start_at_their_documented_defaults(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
        },
    )
    assert result["options"]["parked_setpoint"] == DEFAULT_PARKED_SETPOINT
```

- [ ] **Step 2: Run it to see it fail**

Run: `python -m pytest tests/test_config_flow.py -v`
Expected: FAIL — no `config_flow.py`.

- [ ] **Step 3: Write the flow**

```python
# custom_components/room_thermostat/config_flow.py
"""Adding and editing a room.

Sources live in the entry's data, tunables in its options, so the tunables can
be changed later without rebuilding the entry.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

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
    CONF_HUMIDITY_SENSOR,
    CONF_OFFSET_CORRECTION,
    CONF_PARKED_SETPOINT,
    CONF_TEMPERATURE_SENSOR,
    CONF_VALVE_TRAVEL,
    DEFAULT_COOL_MIN_OFF,
    DEFAULT_COOL_MIN_ON,
    DEFAULT_COOL_TOLERANCE,
    DEFAULT_FROST_TEMPERATURE,
    DEFAULT_HEAT_MIN_OFF,
    DEFAULT_HEAT_MIN_ON,
    DEFAULT_HEAT_TOLERANCE,
    DEFAULT_PARKED_SETPOINT,
    DEFAULT_VALVE_TRAVEL,
    DOMAIN,
    STRATEGY_GATED,
    STRATEGY_PASSTHROUGH,
)

ROOM_SCHEMA = vol.Schema(
    {
        vol.Required("name"): selector.TextSelector(),
        vol.Optional(CONF_TEMPERATURE_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
        ),
        vol.Optional(CONF_HUMIDITY_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
        ),
        vol.Optional(CONF_COOLER): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="climate")
        ),
        vol.Optional(CONF_HEATERS): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch", multiple=True)
        ),
    }
)


def default_options() -> dict[str, Any]:
    return {
        CONF_COOLING_STRATEGY: STRATEGY_PASSTHROUGH,
        CONF_OFFSET_CORRECTION: False,
        CONF_PARKED_SETPOINT: DEFAULT_PARKED_SETPOINT,
        CONF_COOL_COLD_TOLERANCE: DEFAULT_COOL_TOLERANCE,
        CONF_COOL_HOT_TOLERANCE: DEFAULT_COOL_TOLERANCE,
        CONF_COOL_MIN_ON: DEFAULT_COOL_MIN_ON,
        CONF_COOL_MIN_OFF: DEFAULT_COOL_MIN_OFF,
        CONF_HEAT_COLD_TOLERANCE: DEFAULT_HEAT_TOLERANCE,
        CONF_HEAT_HOT_TOLERANCE: DEFAULT_HEAT_TOLERANCE,
        CONF_HEAT_MIN_ON: DEFAULT_HEAT_MIN_ON,
        CONF_HEAT_MIN_OFF: DEFAULT_HEAT_MIN_OFF,
        CONF_VALVE_TRAVEL: DEFAULT_VALVE_TRAVEL,
        CONF_ALLOW_AC_HEAT: False,
        CONF_FROST_TEMPERATURE: DEFAULT_FROST_TEMPERATURE,
    }


class RoomThermostatConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_TEMPERATURE_SENSOR):
                errors[CONF_TEMPERATURE_SENSOR] = "required"
            elif not user_input.get(CONF_COOLER) and not user_input.get(CONF_HEATERS):
                # A room that can neither heat nor cool is a thermometer.
                errors["base"] = "no_devices"
            else:
                return self.async_create_entry(
                    title=user_input["name"],
                    data=user_input,
                    options=default_options(),
                )
        return self.async_show_form(
            step_id="user", data_schema=ROOM_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return RoomThermostatOptionsFlow()


class RoomThermostatOptionsFlow(OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = {**default_options(), **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_COOLING_STRATEGY, default=current[CONF_COOLING_STRATEGY]
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[STRATEGY_PASSTHROUGH, STRATEGY_GATED]
                    )
                ),
                vol.Required(
                    CONF_OFFSET_CORRECTION, default=current[CONF_OFFSET_CORRECTION]
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_PARKED_SETPOINT, default=current[CONF_PARKED_SETPOINT]
                ): vol.Coerce(float),
                vol.Required(
                    CONF_COOL_COLD_TOLERANCE, default=current[CONF_COOL_COLD_TOLERANCE]
                ): vol.Coerce(float),
                vol.Required(
                    CONF_COOL_HOT_TOLERANCE, default=current[CONF_COOL_HOT_TOLERANCE]
                ): vol.Coerce(float),
                vol.Required(
                    CONF_COOL_MIN_ON, default=current[CONF_COOL_MIN_ON]
                ): vol.Coerce(float),
                vol.Required(
                    CONF_COOL_MIN_OFF, default=current[CONF_COOL_MIN_OFF]
                ): vol.Coerce(float),
                vol.Required(
                    CONF_HEAT_COLD_TOLERANCE, default=current[CONF_HEAT_COLD_TOLERANCE]
                ): vol.Coerce(float),
                vol.Required(
                    CONF_HEAT_HOT_TOLERANCE, default=current[CONF_HEAT_HOT_TOLERANCE]
                ): vol.Coerce(float),
                vol.Required(
                    CONF_HEAT_MIN_ON, default=current[CONF_HEAT_MIN_ON]
                ): vol.Coerce(float),
                vol.Required(
                    CONF_HEAT_MIN_OFF, default=current[CONF_HEAT_MIN_OFF]
                ): vol.Coerce(float),
                vol.Required(
                    CONF_VALVE_TRAVEL, default=current[CONF_VALVE_TRAVEL]
                ): vol.Coerce(float),
                vol.Required(
                    CONF_ALLOW_AC_HEAT, default=current[CONF_ALLOW_AC_HEAT]
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_FROST_TEMPERATURE, default=current[CONF_FROST_TEMPERATURE]
                ): vol.Coerce(float),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
```

```json
// custom_components/room_thermostat/translations/en.json
{
  "config": {
    "step": {
      "user": {
        "title": "Add a room",
        "description": "The temperature sensor is required; it is what this thermostat controls against instead of the air conditioner's internal sensor.",
        "data": {
          "name": "Room name",
          "temperature_sensor": "Room temperature sensor",
          "humidity_sensor": "Room humidity sensor",
          "cooler": "Air conditioner",
          "heaters": "Heating valves"
        }
      }
    },
    "error": {
      "required": "A room temperature sensor is required.",
      "no_devices": "Choose an air conditioner, one or more heating valves, or both."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Room settings",
        "data": {
          "cooling_strategy": "Cooling strategy",
          "offset_correction": "Correct the unit's setpoint for its sensor error",
          "parked_setpoint": "Parked setpoint when gating (°C)",
          "cool_cold_tolerance": "Cool: degrees above target before starting",
          "cool_hot_tolerance": "Cool: degrees below target before stopping",
          "cool_min_on": "Cool: minimum run (seconds)",
          "cool_min_off": "Cool: minimum rest (seconds)",
          "heat_cold_tolerance": "Heat: degrees below target before starting",
          "heat_hot_tolerance": "Heat: degrees above target before stopping",
          "heat_min_on": "Heat: minimum run (seconds)",
          "heat_min_off": "Heat: minimum rest (seconds)",
          "valve_travel": "Valve travel time (seconds)",
          "allow_ac_heat": "Heat this room with the air conditioner instead of the valves",
          "frost_temperature": "Frost protection temperature (°C)"
        }
      }
    }
  }
}
```

- [ ] **Step 4: Run it to see it pass**

Run: `python -m pytest tests/test_config_flow.py -v`
Expected: PASS, 4 tests.

- [ ] **Step 5: Commit**

```bash
git add custom_components/room_thermostat/config_flow.py custom_components/room_thermostat/translations tests/conftest.py tests/test_config_flow.py
git commit -m "Add and edit a room through the user interface"
```

---

### Task 8: The climate entity

**Files:**
- Create: `custom_components/room_thermostat/climate.py`
- Modify: `custom_components/room_thermostat/const.py`
- Test: `tests/test_climate.py`

**Interfaces:**
- Consumes: `control.decide` and its dataclasses; the `CONF_*` keys.
- Produces:
  - `RoomThermostat` entity class
  - `SIGNAL_DEMAND = "room_thermostat_demand"` in `const.py` — a dispatcher signal carrying `(entry_id: str, demand: bool)`, which Task 9 subscribes to
  - `hass.data[DOMAIN][entry_id]["demand"]: bool`, the value a newly added binary sensor reads before the first dispatch

- [ ] **Step 1: Write the failing test**

```python
# tests/test_climate.py
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.room_thermostat.const import (
    CONF_COOLER,
    CONF_HEATERS,
    CONF_TEMPERATURE_SENSOR,
    DOMAIN,
)
from custom_components.room_thermostat.config_flow import default_options


async def add_room(hass: HomeAssistant, **data) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bedroom",
        data={"name": "Bedroom", **data},
        options=default_options(),
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_a_room_offers_only_the_modes_it_can_actually_do(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    await add_room(
        hass,
        **{CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
           CONF_HEATERS: ["switch.bedroom_radiator"]},
    )
    state = hass.states.get("climate.bedroom")
    assert set(state.attributes["hvac_modes"]) == {"off", "heat"}


async def test_a_room_with_an_air_conditioner_offers_its_modes(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    hass.states.async_set(
        "climate.bedroom_ac", "off",
        {"fan_modes": ["auto", "low", "high"], "swing_modes": ["default", "full_swing"]},
    )
    await add_room(
        hass,
        **{CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
           CONF_COOLER: "climate.bedroom_ac"},
    )
    state = hass.states.get("climate.bedroom")
    assert set(state.attributes["hvac_modes"]) == {"off", "cool", "dry", "fan_only"}


async def test_the_fan_and_swing_lists_are_mirrored_from_the_unit(hass: HomeAssistant):
    """Published rather than maintained, so a firmware change that adds a fan
    speed appears without a release here."""
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    hass.states.async_set(
        "climate.bedroom_ac", "off",
        {"fan_modes": ["auto", "low", "medium", "high"],
         "swing_modes": ["default", "full_swing", "fixed_upper"]},
    )
    await add_room(
        hass,
        **{CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
           CONF_COOLER: "climate.bedroom_ac"},
    )
    state = hass.states.get("climate.bedroom")
    assert state.attributes["fan_modes"] == ["auto", "low", "medium", "high"]
    assert state.attributes["swing_modes"] == ["default", "full_swing", "fixed_upper"]


async def test_the_room_reads_its_own_sensors_not_the_units(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "26.2")
    hass.states.async_set("sensor.bedroom_humidity", "58")
    hass.states.async_set("climate.bedroom_ac", "off", {"current_temperature": 24.0})
    await add_room(
        hass,
        **{CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
           "humidity_sensor": "sensor.bedroom_humidity",
           CONF_COOLER: "climate.bedroom_ac"},
    )
    state = hass.states.get("climate.bedroom")
    assert state.attributes["current_temperature"] == 26.2
    assert state.attributes["current_humidity"] == 58


async def test_asking_for_heat_opens_every_valve_in_the_room(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "18.0")
    hass.states.async_set("switch.radiator_a", "off")
    hass.states.async_set("switch.radiator_b", "off")
    await add_room(
        hass,
        **{CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
           CONF_HEATERS: ["switch.radiator_a", "switch.radiator_b"]},
    )
    calls = []
    hass.bus.async_listen("call_service", lambda event: calls.append(event.data))

    await hass.services.async_call(
        "climate", "set_temperature",
        {"entity_id": "climate.bedroom", "temperature": 21.0}, blocking=True,
    )
    await hass.services.async_call(
        "climate", "set_hvac_mode",
        {"entity_id": "climate.bedroom", "hvac_mode": "heat"}, blocking=True,
    )
    await hass.async_block_till_done()

    turned_on = [
        call for call in calls
        if call["domain"] == "switch" and call["service"] == "turn_on"
    ]
    targets = {entity for call in turned_on for entity in call["service_data"]["entity_id"]}
    assert targets == {"switch.radiator_a", "switch.radiator_b"}


async def test_setting_a_fan_mode_forwards_to_the_unit(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    hass.states.async_set("climate.bedroom_ac", "off", {"fan_modes": ["auto", "high"]})
    await add_room(
        hass,
        **{CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
           CONF_COOLER: "climate.bedroom_ac"},
    )
    calls = []
    hass.bus.async_listen("call_service", lambda event: calls.append(event.data))

    await hass.services.async_call(
        "climate", "set_fan_mode",
        {"entity_id": "climate.bedroom", "fan_mode": "high"}, blocking=True,
    )
    await hass.async_block_till_done()

    forwarded = [
        call for call in calls
        if call["domain"] == "climate" and call["service"] == "set_fan_mode"
        and "climate.bedroom_ac" in str(call["service_data"].get("entity_id"))
    ]
    assert forwarded
```

- [ ] **Step 2: Run it to see it fail**

Run: `python -m pytest tests/test_climate.py -v`
Expected: FAIL — no `climate.py`, so the entry sets up nothing.

- [ ] **Step 3: Write the entity**

Add to `const.py`:

```python
SIGNAL_DEMAND = "room_thermostat_demand"
DEFAULT_WARM_ON = 600.0
DEFAULT_WARM_OFF = 3000.0
```

```python
# custom_components/room_thermostat/climate.py
"""The room's thermostat.

This is an adapter and nothing more: it reads the source entities, hands their
values to control.decide, and carries out what comes back. Every rule lives in
control.py, where it can be tested without a house.
"""

from __future__ import annotations

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
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from datetime import timedelta

from . import control
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
        self._sensor = entry.data.get(CONF_TEMPERATURE_SENSOR)
        self._humidity = entry.data.get(CONF_HUMIDITY_SENSOR)
        self._cooler = entry.data.get(CONF_COOLER)
        self._heaters: list[str] = list(entry.data.get(CONF_HEATERS) or [])
        self._mode = HVACMode.OFF
        self._target = 21.0
        self._target_low = 20.0
        self._target_high = 25.0
        self._action = HVACAction.OFF
        self._state = control.LoopState(
            heaters_on=False, heaters_changed_at=0.0,
            cooler_on=False, cooler_changed_at=0.0,
        )
        self._demand = False

    # --- what this room can do -------------------------------------------

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
        for attribute, flag in (
            ("fan_modes", ClimateEntityFeature.FAN_MODE),
            ("swing_modes", ClimateEntityFeature.SWING_MODE),
            ("swing_horizontal_modes", ClimateEntityFeature.SWING_HORIZONTAL_MODE),
            ("preset_modes", ClimateEntityFeature.PRESET_MODE),
        ):
            if self._cooler_attribute(attribute):
                features |= flag
        return features

    def _cooler_attribute(self, name: str) -> Any:
        """Whatever the unit says about itself, republished unchanged."""
        if not self._cooler:
            return None
        state = self.hass.states.get(self._cooler)
        return state.attributes.get(name) if state else None

    @property
    def fan_modes(self): return self._cooler_attribute("fan_modes")

    @property
    def fan_mode(self): return self._cooler_attribute("fan_mode")

    @property
    def swing_modes(self): return self._cooler_attribute("swing_modes")

    @property
    def swing_mode(self): return self._cooler_attribute("swing_mode")

    @property
    def swing_horizontal_modes(self): return self._cooler_attribute("swing_horizontal_modes")

    @property
    def swing_horizontal_mode(self): return self._cooler_attribute("swing_horizontal_mode")

    @property
    def preset_modes(self): return self._cooler_attribute("preset_modes")

    @property
    def preset_mode(self): return self._cooler_attribute("preset_mode")

    # --- what the room is doing ------------------------------------------

    @property
    def current_temperature(self): return _number(self.hass, self._sensor)

    @property
    def current_humidity(self):
        value = _number(self.hass, self._humidity)
        return None if value is None else int(value)

    @property
    def hvac_mode(self): return self._mode

    @property
    def hvac_action(self): return self._action

    @property
    def target_temperature(self): return self._target

    @property
    def target_temperature_low(self): return self._target_low

    @property
    def target_temperature_high(self): return self._target_high

    @property
    def available(self) -> bool:
        return _number(self.hass, self._sensor) is not None

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
            "climate", service, {ATTR_ENTITY_ID: self._cooler, key: value},
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

    @property
    def _options(self) -> dict[str, Any]:
        return self._entry.options

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
                    self._cooler_attribute("current_temperature") if self._cooler else None
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

        if self._heaters:
            service = "turn_on" if decision.heaters_on else "turn_off"
            await self.hass.services.async_call(
                "switch", service, {ATTR_ENTITY_ID: self._heaters}, blocking=False
            )

        if decision.cooler is not None and self._cooler:
            await self.hass.services.async_call(
                "climate", "set_hvac_mode",
                {ATTR_ENTITY_ID: self._cooler, "hvac_mode": decision.cooler.hvac_mode},
                blocking=False,
            )
            if decision.cooler.target is not None:
                await self.hass.services.async_call(
                    "climate", "set_temperature",
                    {ATTR_ENTITY_ID: self._cooler, "temperature": decision.cooler.target},
                    blocking=False,
                )

        if decision.heat_demand != self._demand:
            self._demand = decision.heat_demand
            self.hass.data[DOMAIN][self._entry.entry_id]["demand"] = self._demand
            async_dispatcher_send(
                self.hass, SIGNAL_DEMAND, self._entry.entry_id, self._demand
            )

        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            if last.state in self.hvac_modes:
                self._mode = HVACMode(last.state)
            self._target = last.attributes.get("temperature") or self._target

        sources = [entity for entity in (self._sensor, self._humidity, self._cooler) if entity]

        @callback
        def _changed(_: Event) -> None:
            self.hass.async_create_task(self._apply())

        self.async_on_remove(
            async_track_state_change_event(self.hass, sources, _changed)
        )
        self.async_on_remove(
            async_track_time_interval(self.hass, lambda _: _changed(None), TICK)
        )
        await self._apply()
```

- [ ] **Step 4: Run it to see it pass**

Run: `python -m pytest tests/test_climate.py -v`
Expected: PASS, 6 tests. (This task depends on Task 10's `__init__.py` wiring to set up the platform; run Task 10 first if the entry does not load.)

- [ ] **Step 5: Commit**

```bash
git add custom_components/room_thermostat/climate.py custom_components/room_thermostat/const.py tests/test_climate.py
git commit -m "Add the room's climate entity over the control module"
```

---

### Task 9: The heat demand sensor

**Files:**
- Create: `custom_components/room_thermostat/binary_sensor.py`
- Test: `tests/test_binary_sensor.py`

**Interfaces:**
- Consumes: `SIGNAL_DEMAND` and `hass.data[DOMAIN][entry_id]["demand"]` from Task 8.
- Produces: `binary_sensor.<room>_heat_demand`, the entire interface the boiler controller will consume.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_binary_sensor.py
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.room_thermostat.config_flow import default_options
from custom_components.room_thermostat.const import (
    CONF_HEATERS,
    CONF_TEMPERATURE_SENSOR,
    DOMAIN,
    SIGNAL_DEMAND,
)


async def test_a_room_publishes_whether_it_wants_heat(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    entry = MockConfigEntry(
        domain=DOMAIN, title="Bedroom",
        data={"name": "Bedroom",
              CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
              CONF_HEATERS: ["switch.radiator"]},
        options=default_options(),
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.bedroom_heat_demand").state == "off"

    async_dispatcher_send(hass, SIGNAL_DEMAND, entry.entry_id, True)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.bedroom_heat_demand").state == "on"


async def test_one_rooms_demand_does_not_move_another(hass: HomeAssistant):
    """The boiler controller reads one of these per room; crossed wiring here
    would fire the boiler for a room that is warm."""
    hass.states.async_set("sensor.a_temperature", "22.0")
    entry = MockConfigEntry(
        domain=DOMAIN, title="Room A",
        data={"name": "Room A",
              CONF_TEMPERATURE_SENSOR: "sensor.a_temperature",
              CONF_HEATERS: ["switch.a"]},
        options=default_options(),
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    async_dispatcher_send(hass, SIGNAL_DEMAND, "some-other-entry-id", True)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.room_a_heat_demand").state == "off"
```

- [ ] **Step 2: Run it to see it fail**

Run: `python -m pytest tests/test_binary_sensor.py -v`
Expected: FAIL — no such entity.

- [ ] **Step 3: Write the sensor**

```python
# custom_components/room_thermostat/binary_sensor.py
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
```

- [ ] **Step 4: Run it to see it pass**

Run: `python -m pytest tests/test_binary_sensor.py -v`
Expected: PASS, 2 tests.

- [ ] **Step 5: Commit**

```bash
git add custom_components/room_thermostat/binary_sensor.py tests/test_binary_sensor.py
git commit -m "Publish each room's call for heat"
```

---

### Task 10: Entry wiring and the repair issue

**Files:**
- Modify: `custom_components/room_thermostat/__init__.py`
- Modify: `custom_components/room_thermostat/climate.py`
- Modify: `custom_components/room_thermostat/translations/en.json`
- Test: `tests/test_init.py`

**Interfaces:**
- Consumes: everything above.
- Produces: a loadable, unloadable, reloadable integration.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_init.py
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.room_thermostat.config_flow import default_options
from custom_components.room_thermostat.const import (
    CONF_HEATERS,
    CONF_TEMPERATURE_SENSOR,
    DOMAIN,
)


def bedroom(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, title="Bedroom",
        data={"name": "Bedroom",
              CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
              CONF_HEATERS: ["switch.radiator"]},
        options=default_options(),
    )
    entry.add_to_hass(hass)
    return entry


async def test_a_room_loads_both_of_its_entities(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    entry = bedroom(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("climate.bedroom") is not None
    assert hass.states.get("binary_sensor.bedroom_heat_demand") is not None


async def test_a_room_unloads_cleanly(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    entry = bedroom(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_a_lost_sensor_asks_a_human_for_help(hass: HomeAssistant):
    """Failing silent is not acceptable for a heating system: the room is now
    on a blind duty cycle and somebody needs to know."""
    hass.states.async_set("sensor.bedroom_temperature", "22.0")
    entry = bedroom(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("sensor.bedroom_temperature", "unavailable")
    await hass.async_block_till_done()

    registry = ir.async_get(hass)
    assert registry.async_get_issue(DOMAIN, f"sensor_lost_{entry.entry_id}") is not None
```

- [ ] **Step 2: Run it to see it fail**

Run: `python -m pytest tests/test_init.py -v`
Expected: FAIL — `async_setup_entry` is not defined in `__init__.py`.

- [ ] **Step 3: Wire the entry up**

```python
# custom_components/room_thermostat/__init__.py
"""Room Thermostat: one climate entity per room, cooling with an air
conditioner and heating with something else."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS = [Platform.CLIMATE, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"demand": False}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Editing the options changes the control loop's parameters, and the
    # simplest correct response is to rebuild the entities around them.
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
```

In `climate.py`, raise and clear the repair issue inside `_apply`, immediately
after `self._action = ...`:

```python
        if decision.sensor_lost:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                f"sensor_lost_{self._entry.entry_id}",
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="sensor_lost",
                translation_placeholders={
                    "room": self._entry.title,
                    "sensor": self._sensor or "",
                },
            )
        else:
            ir.async_delete_issue(
                self.hass, DOMAIN, f"sensor_lost_{self._entry.entry_id}"
            )
```

with `from homeassistant.helpers import issue_registry as ir` added to its imports.

Add to `translations/en.json`, as a sibling of `"config"` and `"options"`:

```json
  "issues": {
    "sensor_lost": {
      "title": "{room} has lost its temperature sensor",
      "description": "{sensor} is unavailable, so {room} cannot be controlled against a reading. It has fallen back to warming through periodically so it cannot freeze, but it is no longer holding a temperature. Restore the sensor, or reconfigure the room to use a different one."
    }
  }
```

- [ ] **Step 4: Run everything**

Run: `python -m pytest -v`
Expected: PASS — 36 control tests, 3 manifest, 4 config flow, 6 climate, 2 binary sensor, 3 init.

- [ ] **Step 5: Commit**

```bash
git add custom_components/room_thermostat tests/test_init.py
git commit -m "Load, unload and reload a room, and speak up when its sensor goes"
```

---

## Self-review

**Spec coverage.** Every section maps to a task: modes and mirroring → Tasks 4 and 8; pass-through and gated cooling → Task 3; multi-valve heating, tolerances and valve travel → Task 2; frost protection → Task 5; sensor-loss behaviour and the repair issue → Tasks 6 and 10; configuration → Task 7; the demand interface → Task 9; the pure-module testing strategy → the `test_control_module_stays_free_of_home_assistant` test in Task 2.

**Two gaps found and closed while reviewing.** The spec's sensor-loss rule promised a warm-through that Task 5 did not provide — that became Task 6. And `DEFAULT_WARM_ON` / `DEFAULT_WARM_OFF` were used by `climate.py` before being defined, so they are added in Task 8's `const.py` step.

**One deliberate ordering wrinkle.** Task 8's tests need Task 10's `__init__.py` to load the platform. Doing Task 10 before Task 8's step 4 is expected; the note is in the task.

**Not covered here, by design.** The boiler controller (project 2) and the panel UI (project 3). This plan produces working, useful software without either: rooms regulate themselves through their valves and air conditioners as soon as it is installed.
