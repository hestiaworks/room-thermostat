# Room Thermostat — design

A Home Assistant custom integration providing one climate entity per room that
**cools with an air conditioner and heats with something else**, without
flattening either device down to a switch.

## The problem

The house has three Cooper&Hunter (Gree) air conditioners, three radiator
valves across two upstairs rooms, heated floors in five downstairs rooms, and
an independent temperature and humidity sensor in every room. Heating is to be
driven by the boiler and valves, never by the air conditioners.

Home Assistant already exposes the air conditioners faithfully. The Gree
Climate integration reports every mode the units have — `auto`, `cool`, `dry`,
`fan_only`, `heat`, `off` — six fan speeds, five presets, twelve vertical swing
positions, seven horizontal ones, and separate entities for panel light, quiet
mode and extra fan. Nothing about the hardware is missing.

What is missing is a thermostat that can use it. `dual_smart_thermostat` routes
heating and cooling to different devices, which is why it is in use, but it
treats both as switches. Wrapping an air conditioner in it costs every mode
except cooling: no dry, no fan-only, no fan speed, no swing, no presets. It
also offers heating *through the air conditioner*, which is unwanted. The
result is a thermostat that both hides capabilities the units have and offers
ones they should not use.

Two further facts shape the design:

- The units' internal temperature sensors are not the room. Two of the three
  sit behind furniture cabinetry. Airflow is adequate — they cool the rooms —
  but the sensor reads its own recirculated cold air, so a unit set to 22 °C
  satisfies itself and stops after five to ten minutes while the room is still
  at 26 °C.
- The protocol offers no fix. `TemSen` is read-only and there is no "I Feel"
  field, so an external temperature cannot be pushed over WiFi. The Gree
  Climate integration's external-sensor option only changes what Home Assistant
  displays; it never reaches the unit. The remote's I Feel works over infrared
  only.

## Scope

This spec covers the **room thermostat** alone. Two related projects are
deliberately out of scope and are described only where they touch the
interface:

| | | |
| --- | --- | --- |
| 1 | **Room thermostat** | This spec. Buildable now — everything it needs is already in Home Assistant. |
| 2 | **Boiler demand controller** | When the boiler is connected. Same repository, separate config entry type. Consumes this project's demand signals. |
| 3 | **Panel UI** | During the panel redesign. Fan, swing, preset and dry controls, which the panel does not show today. |

They meet at one narrow interface: **project 1 publishes "this room wants
heat", project 2 consumes it.** Nothing else crosses.

## Architecture

A HACS custom integration, domain `room_thermostat`, one **config entry per
room**. Each entry creates:

- a `climate` entity — the room's thermostat
- a `binary_sensor` entity — that room's heat demand

All decision-making lives in a pure module with no Home Assistant imports: it
takes readings, configuration and a clock, and returns what each device should
do. The Home Assistant layer is a thin adapter that reads state, calls that
module, and issues service calls. This is what makes the behaviour testable
without hardware.

### Configuration

Per room, through a config flow with a matching options flow so everything
remains editable:

| Setting | Required | Notes |
| --- | --- | --- |
| Room temperature sensor | yes | The reason this project exists |
| Humidity sensor | no | Feeds `current_humidity` |
| Cooler — a `climate` entity | no | The Gree entity |
| Heaters — one or more `switch` entities | no | Two radiators in a room, two floor loops in a room; they share a setpoint and open together |
| Valve travel time | no | Default 180 s; see below |
| Cooling strategy | yes if a cooler is set | `passthrough` or `gated` |
| Setpoint offset correction | no | `passthrough` only. Default **off** — plain pass-through |
| Parked setpoint | no | `gated` only. Default 17 °C |
| Cool tolerances and minimum times | no | `gated` only. Default 0.5 °C either side, 15 min minimum run |
| Heat tolerances and minimum times | no | Separate defaults for radiator and floor |
| Allow air conditioner to heat | no | Default **off** |
| Frost protection temperature | no | Default 5 °C |

A room with no cooler exposes no cooling modes; a room with no heater exposes no
heat mode. The entity advertises only what the room can actually do.

## Modes

| Panel | Home Assistant | What runs |
| --- | --- | --- |
| COOL | `cool` | Air conditioner only |
| HEAT | `heat` | The room's valves; the air conditioner only if explicitly allowed |
| AUTO | `heat_cool` | Both, against two setpoints, never simultaneously |
| MORE → Dry | `dry` | Air conditioner only |
| MORE → Fan | `fan_only` | Air conditioner only |
| OFF | `off` | Everything off, except frost protection |

`current_temperature` and `current_humidity` come from the room's own sensors,
never from the air conditioner.

`fan_mode`, `swing_mode`, `swing_horizontal_mode` and `preset_mode` are
**mirrored from the cooler**: the entity republishes whatever lists that entity
reports rather than maintaining its own, so a firmware or integration change
that adds a fan speed appears without a release here. Setting any of them
forwards to the cooler in every mode; the value takes effect whenever the
cooler next runs.

**Allowing the air conditioner to heat is either/or, not assist.** When
enabled for a room, heating in that room uses the air conditioner and the
valves stay shut. There is no logic that brings the air conditioner in to help
a struggling floor; that is a plausible future feature and explicitly not built
now.

## Cooling

Two strategies, chosen per room, because the units differ physically.

### `passthrough`

For a unit whose sensor sees real room air. The entity forwards the target
temperature and lets the air conditioner regulate itself, preserving inverter
modulation — the compressor varies its speed rather than switching on and off,
which is quieter, more efficient and easier on the hardware.

Where the unit's sensor is *consistently* offset from the room, an optional
correction adjusts the forwarded setpoint by the difference between the two
readings, smoothed over several minutes and clamped to ±3 °C. **It is off by
default**: a plain pass-through is predictable and cannot run away, and the
correction should be switched on only for a unit observed to have a steady
offset.

**This correction must not be used on a unit inside a cabinet.** There the
offset is not a fixed sensor error: it grows the longer the unit runs, as the
enclosure fills with the unit's own cold return air. Correcting for it feeds
back on itself — the target drops, the unit runs longer, the enclosure gets
colder, the measured offset grows — until the setpoint reaches the unit's
minimum. The clamp only delays that. Such a unit needs `gated`.

### `gated`

For a unit whose sensor cannot be trusted. The air conditioner is parked at a
setpoint low enough that it never satisfies itself (16–18 °C) and **this
integration** starts and stops it against the room sensor, with a wide deadband
and a long minimum run time.

This is bang-bang control of an inverter machine, which is a real cost and is
accepted knowingly: the affected units already cycle every five to ten minutes
without cooling the room, so a fifteen-minute minimum run driven by a sensor
that is actually in the room is gentler than the status quo and, unlike the
status quo, reaches the target.

### The infrared alternative, not built

ESPHome's `climate_ir` `greeyac` protocol can transmit an I Feel report from a
Home Assistant sensor, which would give a cabinet-mounted unit correct sensing
*and* keep inverter modulation. Reports must repeat at under ten minutes or the
unit reverts to its internal sensor.

It is not part of this design, because it is unverified on this hardware — the
protocol variant differs between remotes and at least one user with a similar
remote could control the unit over WiFi but could not get iFeel reports
accepted. If it is proven later, a room moves from `gated` to `passthrough`.
That is a configuration change, which is why the strategy is per-room.

## Heating

A room's heaters are a list of switches driven together.

**Demand is not the same as the switch being on.** Thermal actuators on floor
manifolds take two to four minutes to physically open. A valve is considered
open, and the room considered to be demanding heat, only once its travel time
has elapsed since it was energised. A boiler that fires the moment a switch
closes is pushing water into a circuit that has not opened.

Control is hysteresis against the room sensor:

- calls for heat when `room ≤ target − cold_tolerance`
- releases when `room ≥ target + hot_tolerance`
- `min_on` and `min_off` bound how quickly that can change, independent of
  temperature

Cold and hot tolerances are **separate numbers**, because a heated floor
overshoots far more than it undershoots: a slab that has absorbed heat keeps
releasing it long after the valve shuts. Defaults differ by emitter — a
radiator around 0.3 °C either side with five-minute minimums; a floor a wider
band with twenty- to thirty-minute minimums.

`gated` cooling uses the same shape with its own numbers.

## Frost protection

Per room, default 5 °C. When the room falls below it, the room's heaters run
regardless of mode — **including when the entity is `off`** — until the room
recovers past a small margin. The room reports demand while this is happening,
so the boiler controller treats it like any other call for heat.

Safety overrides intent here, which is the point: an `off` thermostat must not
be able to freeze a pipe.

## Failure behaviour

The entity drives real hardware from other entities' state, so degradation is
part of the design, not an afterthought.

- **Room sensor unavailable** — normal control stops rather than running a loop
  against a stale reading, and the entity reports unavailable. Frost protection
  does **not** stop: the room falls back to a conservative periodic warm-through
  and the integration raises a Home Assistant repair issue. A heating system
  that fails silent in winter is not acceptable.
- **Cooler or heater unavailable** — the affected side stops being commanded;
  the other continues. The entity surfaces which side is degraded.
- **After a restart** — mode and setpoints are restored, and the control loops
  resume from what the devices actually report rather than from an assumption
  about what was commanded before.

## Interface to the boiler controller

Each room publishes a `binary_sensor`, on whenever that room wants heat, using
the valve-travel definition above. The boiler controller — later, same
repository, separate config entry type — reads those and nothing else.

Two rules belong to that project and are recorded here so they are not lost:
the boiler must stop **before** the last valve closes, never after, or it fires
into a dead circuit; and the pump runs on afterwards to dissipate residual
heat.

## Testing

The pure control module is driven by explicit inputs and an injectable clock,
so its behaviour is unit-testable with no hardware and no running Home
Assistant. Cases that must be covered include:

- a `gated` cooler four minutes into a fifteen-minute minimum run does not stop,
  even once the room is below target
- a floor valve energised ninety seconds ago does not yet count as demand
- a room at 4 °C with the entity `off` calls for heat
- a room whose sensor is unavailable stops normal control but keeps frost
  protection
- crossing from heating to cooling in `heat_cool` requires leaving the dead
  zone, so a room cannot fight itself
- mode, fan, swing and preset lists reported by the entity match whatever the
  cooler currently reports

The Home Assistant layer is thin enough to be covered by a smaller number of
integration tests over the config flow and entity wiring.

## Explicitly not built

- Humidity **control**. Humidity is displayed. There is no humidistat, no
  target humidity, and no logic that selects dry mode on its own. `dry` is a
  mode the user chooses, forwarded to the unit.
- Assist heating — the air conditioner helping a slow floor.
- Scheduling. Home Assistant already schedules.
- Talking to the air conditioners directly. Gree Climate holds the units'
  sessions and does the job; a second controller would fight it for control.
