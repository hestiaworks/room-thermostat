"""Adding and editing a room.

Sources live in the entry's data, tunables in its options, so the tunables can
be changed later without rebuilding the entry.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
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
    ENTRY_SEASONS,
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


OUTDOOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        # A weather entity is as good as a sensor for an average measured in
        # days, and an input_number is how the behaviour gets exercised without
        # waiting for a season.
        filter=[
            selector.EntityFilterSelectorConfig(
                domain="sensor", device_class="temperature"
            ),
            selector.EntityFilterSelectorConfig(
                domain=["weather", "input_number", "number"]
            ),
        ]
    )
)


def season_options() -> dict[str, Any]:
    """What the Seasons entry holds when the integration creates it.

    No outdoor source, so it gates nothing until someone chooses one. An
    existing house gains a row and no behaviour change at all.
    """
    return {
        CONF_OUTDOOR_SENSOR: None,
        CONF_DAMPING_HOURS: DEFAULT_DAMPING_HOURS,
        CONF_SEASON_DWELL: DEFAULT_SEASON_DWELL_HOURS,
        CONF_HEAT_LIMIT: DEFAULT_HEAT_LIMIT,
        CONF_HEAT_LIMIT_HYSTERESIS: DEFAULT_LIMIT_HYSTERESIS,
        CONF_COOL_LIMIT: DEFAULT_COOL_LIMIT,
        CONF_COOL_LIMIT_HYSTERESIS: DEFAULT_LIMIT_HYSTERESIS,
        CONF_HEAT_OVERRIDE: DEFAULT_SEASON_OVERRIDE,
        CONF_COOL_OVERRIDE: DEFAULT_SEASON_OVERRIDE,
    }


def _hours(maximum: float) -> Any:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0, max=maximum, step=1,
            unit_of_measurement="hours", mode=selector.NumberSelectorMode.BOX,
        )
    )


def seasons_schema(current: dict[str, Any]) -> vol.Schema:
    """Everything the house decides once, on one form."""
    return vol.Schema(
        {
            vol.Optional(CONF_OUTDOOR_SENSOR): OUTDOOR_SELECTOR,
            vol.Required(
                CONF_DAMPING_HOURS, default=current[CONF_DAMPING_HOURS]
            ): _hours(48),
            vol.Required(
                CONF_SEASON_DWELL, default=current[CONF_SEASON_DWELL]
            ): _hours(72),
            vol.Required(
                CONF_HEAT_LIMIT, default=current[CONF_HEAT_LIMIT]
            ): _degrees(0, 30),
            vol.Required(
                CONF_HEAT_LIMIT_HYSTERESIS,
                default=current[CONF_HEAT_LIMIT_HYSTERESIS],
            ): _degrees(0, 5),
            vol.Required(
                CONF_COOL_LIMIT, default=current[CONF_COOL_LIMIT]
            ): _degrees(0, 30),
            vol.Required(
                CONF_COOL_LIMIT_HYSTERESIS,
                default=current[CONF_COOL_LIMIT_HYSTERESIS],
            ): _degrees(0, 5),
            vol.Required(
                CONF_HEAT_OVERRIDE, default=current[CONF_HEAT_OVERRIDE]
            ): _degrees(0, 15),
            vol.Required(
                CONF_COOL_OVERRIDE, default=current[CONF_COOL_OVERRIDE]
            ): _degrees(0, 15),
        }
    )


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
        """Create the one Seasons entry.

        Reachable only from code. A house-level setting offered next to a
        per-room one invites the reading that you make one per room, and a
        singleton guarded only by an abort still advertises itself as something
        to create. A row that cannot be created cannot be created twice.
        """
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_SEASONS:
                return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(
            title="Seasons",
            data={CONF_ENTRY_TYPE: ENTRY_SEASONS},
            options=season_options(),
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
        if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_SEASONS:
            return SeasonsOptionsFlow()
        return RoomThermostatOptionsFlow()


class RoomThermostatOptionsFlow(OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        flat: dict[str, Any] | None = None
        if user_input is not None:
            flat = {
                key: value
                for group in user_input.values()
                for key, value in group.items()
            }
            # Every source key is written, including the ones left empty, so
            # clearing a device clears it rather than falling back to what the
            # room used before.
            flat.update({key: flat.get(key) for key in SOURCE_KEYS})
            # The inversion ticks list the room's own heaters, so a tick for a
            # heater that has just been removed is the removal seen from the
            # other side, not a mistake to report. It goes with the heater.
            flat[CONF_INVERTED_HEATERS] = [
                heater
                for heater in (flat.get(CONF_INVERTED_HEATERS) or [])
                if heater in (flat.get(CONF_HEATERS) or [])
            ]
            errors = _problems(self.hass, flat)
            if not errors:
                return self.async_create_entry(
                    data={**self.config_entry.options, **flat}
                )

        # A refused form comes back as it was filled in. Redrawing it from the
        # stored configuration threw the edit away, and the field someone had
        # just cleared reappeared with its old value — which reads as the form
        # ignoring them rather than as a refusal.
        chosen = {key: flat[key] for key in SOURCE_KEYS} if flat else sources(self.config_entry)
        current = {**default_options(), **self.config_entry.options}
        suggested = user_input if user_input is not None else {
            "sensors": {k: v for k, v in chosen.items() if v and "sensor" in k},
            "devices": {
                k: v
                for k, v in chosen.items()
                if v and k in (CONF_COOLER, CONF_HEATERS, CONF_INVERTED_HEATERS)
            },
        }
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                room_schema(self.hass, current, chosen), suggested
            ),
            errors=errors,
        )


class SeasonsOptionsFlow(OptionsFlow):
    """The house's own settings. There is exactly one of these."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        # Its own step id, not the room form's: they would otherwise share a
        # title, and this form is not about a room.
        return await self.async_step_seasons(user_input)

    async def async_step_seasons(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            # The source is written even when it is absent, so clearing it
            # clears it rather than falling back to the previous choice —
            # clearing the source is how seasons are switched off.
            return self.async_create_entry(
                data={
                    **season_options(),
                    **user_input,
                    CONF_OUTDOOR_SENSOR: user_input.get(CONF_OUTDOOR_SENSOR),
                }
            )
        current = {**season_options(), **self.config_entry.options}
        return self.async_show_form(
            step_id="seasons",
            data_schema=self.add_suggested_values_to_schema(
                seasons_schema(current), current
            ),
        )
