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
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, selector

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

# One definition per field, used by both the add form and the options form:
# they were copies, and copies drift.
TEMPERATURE_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        # A helper is allowed on purpose. An input_number you can drag is how
        # the deadband and the minimum times get exercised without waiting for
        # a real room to change temperature.
        filter=[
            selector.EntityFilterSelectorConfig(
                domain="sensor", device_class="temperature"
            ),
            selector.EntityFilterSelectorConfig(domain=["input_number", "number"]),
        ]
    )
)

HUMIDITY_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        filter=[
            selector.EntityFilterSelectorConfig(
                domain="sensor", device_class="humidity"
            ),
            selector.EntityFilterSelectorConfig(domain=["input_number", "number"]),
        ]
    )
)

COOLER_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="climate")
)

HEATERS_SELECTOR = selector.EntitySelector(
    # Radiator valves are valve entities; a floor loop driven by a relay is a
    # switch. A room may have both.
    selector.EntitySelectorConfig(
        domain=["valve", "switch", "input_boolean"], multiple=True
    )
)

DEVICE_FIELDS = {
    vol.Optional(CONF_TEMPERATURE_SENSOR): TEMPERATURE_SELECTOR,
    vol.Optional(CONF_HUMIDITY_SENSOR): HUMIDITY_SELECTOR,
    vol.Optional(CONF_COOLER): COOLER_SELECTOR,
    vol.Optional(CONF_HEATERS): HEATERS_SELECTOR,
}

ROOM_SCHEMA = vol.Schema(
    {vol.Required("name"): selector.TextSelector(), **DEVICE_FIELDS}
)

DEVICES_SCHEMA = vol.Schema(DEVICE_FIELDS)


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


SOURCE_KEYS = (CONF_TEMPERATURE_SENSOR, CONF_HUMIDITY_SENSOR, CONF_COOLER, CONF_HEATERS)


def sources(entry: Any) -> dict[str, Any]:
    """Which sensors and devices a room uses.

    Sources moved from the entry's data into its options, because a helper
    gets exactly one configuration door in the interface and that door opens
    the options flow. Rooms created before the move still hold theirs in data,
    and are read from there rather than being made to start again.
    """
    found = {key: entry.options.get(key) for key in SOURCE_KEYS}
    if any(found.values()):
        return found
    return {key: entry.data.get(key) for key in SOURCE_KEYS}


def _is_ours(hass: HomeAssistant, entity_id: str) -> bool:
    entry = er.async_get(hass).async_get(entity_id)
    return entry is not None and entry.platform == DOMAIN


def _problems(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, str]:
    if not user_input.get(CONF_TEMPERATURE_SENSOR):
        return {CONF_TEMPERATURE_SENSOR: "required"}
    cooler = user_input.get(CONF_COOLER)
    if cooler and _is_ours(hass, cooler):
        # A room driving one of these would drive itself, and the loop is not
        # visible from the interface.
        return {CONF_COOLER: "own_entity"}
    if not cooler and not user_input.get(CONF_HEATERS):
        # A room that can neither heat nor cool is a thermometer.
        return {"base": "no_devices"}
    return {}


class RoomThermostatConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _problems(self.hass, user_input)
            if not errors:
                return self.async_create_entry(
                    title=user_input["name"],
                    data={"name": user_input["name"]},
                    options={
                        **default_options(),
                        **{k: v for k, v in user_input.items() if k in SOURCE_KEYS},
                    },
                )
        return self.async_show_form(
            step_id="user", data_schema=ROOM_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Change which sensors and devices a room uses.

        Deleting and recreating the room would work, and would also take its
        history, its entity ids and every dashboard card pointing at them. The
        tunables are left alone: they live in the entry's options and are
        edited separately.
        """
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _problems(self.hass, user_input)
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, title=user_input["name"], data=user_input
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                ROOM_SCHEMA, user_input or entry.data
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return RoomThermostatOptionsFlow()


class RoomThermostatOptionsFlow(OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return self.async_show_menu(
            step_id="init", menu_options=["devices", "tuning"]
        )

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """The sensors and devices this room uses."""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _problems(self.hass, user_input)
            if not errors:
                return self.async_create_entry(
                    data={**self.config_entry.options, **user_input}
                )
        current = user_input or sources(self.config_entry)
        return self.async_show_form(
            step_id="devices",
            data_schema=self.add_suggested_values_to_schema(
                DEVICES_SCHEMA, {k: v for k, v in current.items() if v}
            ),
            errors=errors,
        )

    async def async_step_tuning(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={**self.config_entry.options, **user_input}
            )
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
        return self.async_show_form(step_id="tuning", data_schema=vol.Schema(schema))
