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

SIGNAL_DEMAND = "room_thermostat_demand"
# The blind duty cycle used when a room's sensor is unavailable: ten minutes of
# heat an hour, which cannot overheat a room quickly nor let one freeze slowly.
DEFAULT_WARM_ON = 600.0
DEFAULT_WARM_OFF = 3000.0
