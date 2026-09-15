"""Finding the house's answer, from a room.

The season travels house → room as entity state, the opposite direction from
heat demand and by a different mechanism. A room already reads every one of its
inputs as entity state, so this is not a second mechanism; the recorder keeps
the history, so "why did heating not run on the 14th" is a graph rather than a
guess; and the damped average has to survive a restart, which RestoreEntity
does for an entity and nothing does for a dispatcher signal.

Everything here fails open. A lockout that engages by accident is a cold house
with no visible cause.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_COOL_OVERRIDE,
    CONF_ENTRY_TYPE,
    CONF_HEAT_OVERRIDE,
    DEFAULT_SEASON_OVERRIDE,
    DOMAIN,
    ENTRY_SEASONS,
)


def seasons_entry(hass: HomeAssistant) -> ConfigEntry | None:
    """The one house-level entry, or None before it has been created."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_SEASONS:
            return entry
    return None


def season_entity_ids(hass: HomeAssistant) -> tuple[str | None, str | None]:
    """The two sensors, found by unique id rather than by assumed entity id.

    Either may have been renamed, and a room that quietly stopped obeying
    because of a rename would look exactly like one the season had released.
    """
    entry = seasons_entry(hass)
    if entry is None:
        return None, None
    registry = er.async_get(hass)
    return (
        registry.async_get_entity_id(
            "binary_sensor", DOMAIN, f"{entry.entry_id}_heating_season"
        ),
        registry.async_get_entity_id(
            "binary_sensor", DOMAIN, f"{entry.entry_id}_cooling_season"
        ),
    )


def allowed(hass: HomeAssistant) -> tuple[bool, bool]:
    """Whether heating and cooling may run, as far as the house is concerned.

    Anything missing means yes: no Seasons entry, no sensors yet, or a source
    that has gone all leave a room exactly as it was before seasons existed.
    """
    answers = []
    for entity_id in season_entity_ids(hass):
        state = None if entity_id is None else hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            answers.append(True)
        else:
            answers.append(state.state == "on")
    return answers[0], answers[1]


def overrides(hass: HomeAssistant) -> tuple[float, float]:
    """How far from setpoint a room may stray, out of season, before it runs."""
    entry = seasons_entry(hass)
    if entry is None:
        return DEFAULT_SEASON_OVERRIDE, DEFAULT_SEASON_OVERRIDE
    return (
        entry.options.get(CONF_HEAT_OVERRIDE, DEFAULT_SEASON_OVERRIDE),
        entry.options.get(CONF_COOL_OVERRIDE, DEFAULT_SEASON_OVERRIDE),
    )
