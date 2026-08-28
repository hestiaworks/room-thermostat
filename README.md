# Room Thermostat

One Home Assistant climate entity per room that **cools with an air
conditioner and heats with something else** — valves, a boiler loop, a heated
floor — without flattening either device down to a switch.

Unlike wrapping an air conditioner in a generic thermostat, this keeps
everything the unit can do: dry and fan-only modes, fan speeds, both swing
axes and presets are mirrored from the underlying climate entity rather than
replaced with a fixed list. Temperature and humidity come from your own room
sensors, not the unit's internal one.

## Installing

Add this repository to HACS as a custom repository of type **Integration**,
download it, and restart Home Assistant. Then **Settings → Devices & Services →
Add Integration → Room Thermostat**, once per room.

Rooms appear under the **Helpers** tab, not Integrations: this wraps entities
you already have rather than talking to hardware of its own.

## What a room needs

| | |
| --- | --- |
| Temperature sensor | Required. A `sensor`, or an `input_number` for testing |
| Humidity sensor | Optional, shown on the thermostat |
| Air conditioner | Optional. Any `climate` entity |
| Heating valves | Optional. `valve`, `switch` or `input_boolean` entities |

A room with only an air conditioner offers no heat mode; one with only valves
offers no cooling. Nothing is advertised that the room cannot do.

## Cooling an air conditioner that misreads the room

Units mounted inside cabinetry sense their own recirculated air and stop long
before the room is cool. Set that room's cooling strategy to **gated**: the
unit is parked at a setpoint it can never satisfy, and the room's own sensor
decides when it runs. Rooms whose units sense correctly should stay on
**passthrough**, which forwards the setpoint and lets the compressor modulate.

## Licence

MIT.
