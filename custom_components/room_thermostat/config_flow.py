"""Adding and editing a room.

Sources live in the entry's data, tunables in its options, so the tunables can
be changed later without rebuilding the entry.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult, section
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, selector

from .const import (
    CONF_ALLOW_AC_HEAT,
    CONF_COOL_LIMIT,
    CONF_COOL_LIMIT_HYSTERESIS,
    CONF_COOL_OVERRIDE,
    CONF_DAMPING_HOURS,
    CONF_ENTRY_TYPE,
    CONF_HEAT_LIMIT,
    CONF_HEAT_LIMIT_HYSTERESIS,
    CONF_HEAT_OVERRIDE,
    CONF_OUTDOOR_SENSOR,
    CONF_SEASON_DWELL,
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
    CONF_INVERTED_HEATERS,
    CONF_VISIBLE_CONTROLS,
    CONTROLS,
    CONF_HUMIDITY_SENSOR,
    CONF_OFFSET_CORRECTION,
    CONF_PARKED_SETPOINT,
    CONF_TEMPERATURE_SENSOR,
    CONF_VALVE_TRAVEL,
    DEFAULT_COOL_LIMIT,
    DEFAULT_COOL_MIN_OFF,
    DEFAULT_DAMPING_HOURS,
    DEFAULT_COOL_MIN_ON,
    DEFAULT_COOL_TOLERANCE,
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
    DOMAIN,
    ENTRY_HUB,
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


def inverted_field(hass: HomeAssistant, heaters: list[str]) -> dict[Any, Any]:
    """Offer inversion only for heaters the room actually drives.

    A free entity picker could name something the room does not control, and
    the only thing to do about it was refuse the form. Offering the room's own
    heaters makes that mistake unavailable rather than rejected.
    """
    if not heaters:
        return {}

    def label(entity_id: str) -> str:
        state = hass.states.get(entity_id)
        name = state.attributes.get("friendly_name") if state else None
        # The id is unreadable at a glance; fall back to it only when the
        # entity is gone and there is no name to show.
        return name or entity_id

    return {
        vol.Optional(CONF_INVERTED_HEATERS): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[{"value": h, "label": label(h)} for h in heaters],
                multiple=True,
                mode=selector.SelectSelectorMode.LIST,
            )
        )
    }

ROOM_SCHEMA = vol.Schema(
    {vol.Required("name"): selector.TextSelector(), **DEVICE_FIELDS}
)

DEVICES_SCHEMA = vol.Schema(DEVICE_FIELDS)


def _degrees(minimum: float, maximum: float, step: float = 0.1) -> Any:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=minimum, max=maximum, step=step,
            unit_of_measurement="°C", mode=selector.NumberSelectorMode.BOX,
        )
    )


def _seconds(maximum: float = 7200) -> Any:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0, max=maximum, step=10,
            unit_of_measurement="seconds", mode=selector.NumberSelectorMode.BOX,
        )
    )


def _group(fields: dict[Any, Any], collapsed: bool) -> Any:
    return section(vol.Schema(fields), {"collapsed": collapsed})


def room_schema(
    hass: HomeAssistant, current: dict[str, Any], chosen: dict[str, Any]
) -> vol.Schema:
    """Everything about a room, on one form, grouped by what it is about.

    Reaching a setting used to mean a menu and then a second dialog. The
    groups do that job without the nesting.
    """
    return vol.Schema(
        {
            vol.Required("sensors"): _group(
                {
                    vol.Optional(CONF_TEMPERATURE_SENSOR): TEMPERATURE_SELECTOR,
                    vol.Optional(CONF_HUMIDITY_SENSOR): HUMIDITY_SELECTOR,
                },
                collapsed=False,
            ),
            vol.Required("devices"): _group(
                {
                    vol.Optional(CONF_COOLER): COOLER_SELECTOR,
                    vol.Optional(CONF_HEATERS): HEATERS_SELECTOR,
                    **inverted_field(hass, chosen.get(CONF_HEATERS) or []),
                    vol.Optional(
                        CONF_VISIBLE_CONTROLS,
                        default=list(current.get(CONF_VISIBLE_CONTROLS) or CONTROLS),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=list(CONTROLS),
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                            translation_key="visible_controls",
                        )
                    ),
                },
                collapsed=False,
            ),
            vol.Required("cooling"): _group(
                {
                    vol.Required(
                        CONF_COOLING_STRATEGY, default=current[CONF_COOLING_STRATEGY]
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[STRATEGY_PASSTHROUGH, STRATEGY_GATED],
                            translation_key="cooling_strategy",
                        )
                    ),
                    vol.Required(
                        CONF_OFFSET_CORRECTION, default=current[CONF_OFFSET_CORRECTION]
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_PARKED_SETPOINT, default=current[CONF_PARKED_SETPOINT]
                    ): _degrees(5, 30, 0.5),
                    vol.Required(
                        CONF_COOL_COLD_TOLERANCE,
                        default=current[CONF_COOL_COLD_TOLERANCE],
                    ): _degrees(0.1, 5),
                    vol.Required(
                        CONF_COOL_HOT_TOLERANCE,
                        default=current[CONF_COOL_HOT_TOLERANCE],
                    ): _degrees(0.1, 5),
                    vol.Required(
                        CONF_COOL_MIN_ON, default=current[CONF_COOL_MIN_ON]
                    ): _seconds(),
                    vol.Required(
                        CONF_COOL_MIN_OFF, default=current[CONF_COOL_MIN_OFF]
                    ): _seconds(),
                },
                collapsed=False,
            ),
            vol.Required("heating"): _group(
                {
                    vol.Required(
                        CONF_ALLOW_AC_HEAT, default=current[CONF_ALLOW_AC_HEAT]
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_HEAT_COLD_TOLERANCE,
                        default=current[CONF_HEAT_COLD_TOLERANCE],
                    ): _degrees(0.1, 5),
                    vol.Required(
                        CONF_HEAT_HOT_TOLERANCE,
                        default=current[CONF_HEAT_HOT_TOLERANCE],
                    ): _degrees(0.1, 5),
                    vol.Required(
                        CONF_HEAT_MIN_ON, default=current[CONF_HEAT_MIN_ON]
                    ): _seconds(),
                    vol.Required(
                        CONF_HEAT_MIN_OFF, default=current[CONF_HEAT_MIN_OFF]
                    ): _seconds(),
                    vol.Required(
                        CONF_VALVE_TRAVEL, default=current[CONF_VALVE_TRAVEL]
                    ): _seconds(900),
                },
                collapsed=True,
            ),
            vol.Required("safety"): _group(
                {
                    vol.Required(
                        CONF_FROST_TEMPERATURE, default=current[CONF_FROST_TEMPERATURE]
                    ): _degrees(2, 15, 0.5),
                },
                collapsed=True,
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


SOURCE_KEYS = (
    CONF_TEMPERATURE_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_COOLER,
    CONF_HEATERS,
    CONF_INVERTED_HEATERS,
)


def sources(entry: Any) -> dict[str, Any]:
    """Which sensors and devices a room uses.

    Sources moved from the entry's data into its options, because a helper
    gets exactly one configuration door in the interface and that door opens
    the options flow. Rooms created before the move still hold theirs in data,
    and are read from there rather than being made to start again.
    """
    # Decided per key, not wholesale. Choosing one place for all of them meant
    # that writing a single source into the options orphaned every source a
    # legacy room still kept in its data.
    return {
        key: entry.options[key] if key in entry.options else entry.data.get(key)
        for key in SOURCE_KEYS
    }


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
        """Add the integration. There is one of these, and it is the door.

        Rooms are not made here any more: they are made on the page, which is
        the record. This only brings the integration into being, so that the
        page exists to make them on.
        """
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_HUB:
                return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(
            title="Room Thermostat", data={CONF_ENTRY_TYPE: ENTRY_HUB}
        )

    async def async_step_import(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Make the hub for a house that predates it.

        Reachable only from code, when rooms are found with nowhere to live.
        """
        return await self.async_step_user()
