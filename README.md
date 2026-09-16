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
Add Integration → Room Thermostat**, once for the house.

Everything else happens on the **Room Thermostat** page in the sidebar: adding
rooms, configuring them, setting the heating and cooling seasons, and looking
at what the house has been doing. There is nothing to configure under Helpers,
and a room is never edited in two places.

Upgrading from an earlier version moves your existing rooms onto that page by
itself. Entity ids do not change, so dashboards, automations and panels keep
working.

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

## Not heating a room in mild weather

A room set to 22 °C calls for heat at 20 °C in September exactly as it does in
January, because the only question it asks is whether it is below its setpoint.

A **Seasons** entry appears alongside your rooms the first time one is set up.
Give it an outdoor temperature — a sensor or a weather entity — and it decides
once for the whole house whether heating and cooling are in season. Rooms obey
it and have no seasonal settings of their own.

Heating is decided on an **average** of the outdoor temperature rather than the
reading, over 30 hours by default, so one warm afternoon does not end the
heating season. On top of that an answer has to **last** — six hours by default
— because a mild autumn dips below the heating limit for a few hours every night
whatever the averaging, and heating that arrives before dawn and leaves by
mid-morning is worse than none.

Cooling is decided on the live reading with neither the average nor the wait: a
sunny afternoon in an otherwise cold week still overheats a room that afternoon.

Out of season a room still heats if it falls more than 4 °C below its setpoint,
and still cools more than 4 °C above it — the weather is a guess and the room's
own thermometer is not. Frost protection is never affected by any of this.

Until you choose an outdoor source the entry does nothing at all and every room
behaves as it did before. Clearing the source again is how you switch seasons
off; the entry itself is created by the integration and comes back if deleted.

**Where to put an outdoor sensor:** in shade, on a north wall, under an eave,
away from the air conditioners' exhaust. One in October afternoon sun reads
40 °C, which drags the average up and holds the heating off on a cold day.

## Licence

MIT.
