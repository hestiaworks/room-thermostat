"""Names and defaults. No logic lives here."""

DOMAIN = "room_thermostat"

# Which kind of config entry this is. Rooms created before seasons existed
# carry no such key, and are rooms.
CONF_ENTRY_TYPE = "entry_type"
ENTRY_ROOM = "room"
ENTRY_HUB = "hub"

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
CONF_INVERTED_HEATERS = "inverted_heaters"
CONF_VISIBLE_CONTROLS = "visible_controls"
CONF_ALLOW_AC_HEAT = "allow_ac_heat"
CONF_FROST_TEMPERATURE = "frost_temperature"

# The air conditioner controls a room may show. A unit can report a capability
# its owner never uses, or does not really have.
CONTROLS = ("fan_mode", "swing_mode", "swing_horizontal_mode", "preset_mode")

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

SIGNAL_DEMAND = "room_thermostat_demand"
# The blind duty cycle used when a room's sensor is unavailable: ten minutes of
# heat an hour, which cannot overheat a room quickly nor let one freeze slowly.
DEFAULT_WARM_ON = 600.0
DEFAULT_WARM_OFF = 3000.0

# --- the house's seasons -------------------------------------------------

CONF_OUTDOOR_SENSOR = "outdoor_sensor"
CONF_DAMPING_HOURS = "damping_hours"
CONF_SEASON_DWELL = "season_dwell_hours"
CONF_HEAT_LIMIT = "heat_limit"
CONF_HEAT_LIMIT_HYSTERESIS = "heat_limit_hysteresis"
CONF_COOL_LIMIT = "cool_limit"
CONF_COOL_LIMIT_HYSTERESIS = "cool_limit_hysteresis"
CONF_HEAT_OVERRIDE = "heat_override"
CONF_COOL_OVERRIDE = "cool_override"

# Verbatim from the spec, as amended on 15 September: a thirty-hour average
# leaves 0.9 of daily ripple, which a mild autumn's one degree of margin can
# absorb, and the dwell is what stops a few hours of anything counting as a
# season.
DEFAULT_DAMPING_HOURS = 30.0
DEFAULT_SEASON_DWELL_HOURS = 6.0
DEFAULT_HEAT_LIMIT = 16.0
DEFAULT_COOL_LIMIT = 15.0
DEFAULT_LIMIT_HYSTERESIS = 1.0
DEFAULT_SEASON_OVERRIDE = 4.0

# Readings outside this band are a fault, not a preference: a sensor in
# October sun reads 40, and one that has failed reads nonsense. Not an option,
# because a house where -50 is a real reading is not this one.
SANE_OUTDOOR = (-50.0, 60.0)
# How long an outdoor source may be missing before a human is told.
OUTDOOR_LOST_SECONDS = 3600.0

# --- the record the page edits -------------------------------------------

STORE_KEY = "room_thermostat.rooms"
STORE_VERSION = 1

# The set of rooms changed: something has to be built or taken away.
SIGNAL_ROOMS = "room_thermostat_rooms"
# One room's settings changed, by id. Its entities re-read and re-subscribe.
SIGNAL_ROOM = "room_thermostat_room"

# --- the page ------------------------------------------------------------

PAGE_COMPONENT = "room-thermostat-page"
PAGE_URL_PATH = "room-thermostat"
# Keep the query string in step with the manifest version: a browser serves
# the cached page until it changes, so a drift ships code nobody loads.
PAGE_MODULE_URL = "/room_thermostat/frontend/room-thermostat-page.js?v=0.14.0"
