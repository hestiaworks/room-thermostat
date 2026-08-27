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
