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
        numbers = (
            CONF_PARKED_SETPOINT,
            CONF_COOL_COLD_TOLERANCE,
            CONF_COOL_HOT_TOLERANCE,
            CONF_COOL_MIN_ON,
            CONF_COOL_MIN_OFF,
            CONF_HEAT_COLD_TOLERANCE,
            CONF_HEAT_HOT_TOLERANCE,
            CONF_HEAT_MIN_ON,
            CONF_HEAT_MIN_OFF,
            CONF_VALVE_TRAVEL,
            CONF_FROST_TEMPERATURE,
        )
        schema: dict[Any, Any] = {
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
                CONF_ALLOW_AC_HEAT, default=current[CONF_ALLOW_AC_HEAT]
            ): selector.BooleanSelector(),
        }
        for key in numbers:
            schema[vol.Required(key, default=current[key])] = vol.Coerce(float)
        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema))
