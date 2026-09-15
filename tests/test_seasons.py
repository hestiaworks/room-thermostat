"""The house-level Seasons entry: created by the integration, never offered."""

from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.room_thermostat.config_flow import default_options, season_options
from custom_components.room_thermostat.const import (
    CONF_ENTRY_TYPE,
    CONF_HEAT_LIMIT,
    CONF_HEATERS,
    CONF_OUTDOOR_SENSOR,
    CONF_TEMPERATURE_SENSOR,
    DEFAULT_HEAT_LIMIT,
    DOMAIN,
    ENTRY_SEASONS,
)


def seasons(hass: HomeAssistant, **options) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Seasons",
        data={CONF_ENTRY_TYPE: ENTRY_SEASONS},
        options={**season_options(), **options},
    )
    entry.add_to_hass(hass)
    return entry


def room(hass: HomeAssistant, name: str = "Bedroom") -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=name,
        data={
            "name": name,
            CONF_TEMPERATURE_SENSOR: f"sensor.{name.lower()}_temperature",
            CONF_HEATERS: ["switch.radiator"],
        },
        options=default_options(),
    )
    entry.add_to_hass(hass)
    return entry


def test_it_is_created_with_no_source_and_the_spec_defaults():
    options = season_options()
    assert options[CONF_OUTDOOR_SENSOR] is None
    assert options[CONF_HEAT_LIMIT] == DEFAULT_HEAT_LIMIT


async def test_the_import_flow_creates_exactly_one(hass: HomeAssistant):
    first = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}
    )
    assert first["type"] == "create_entry"
    assert first["data"][CONF_ENTRY_TYPE] == ENTRY_SEASONS

    second = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}
    )
    assert second["type"] == "abort"
    assert second["reason"] == "single_instance_allowed"


async def test_a_seasons_entry_creates_only_its_two_sensors(hass: HomeAssistant):
    entry = seasons(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.heating_season") is not None
    assert hass.states.get("binary_sensor.cooling_season") is not None
    assert hass.states.get("climate.seasons") is None


async def test_its_settings_are_editable(hass: HomeAssistant):
    entry = seasons(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    flow = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        user_input={
            **{
                key: value
                for key, value in season_options().items()
                if key != CONF_OUTDOOR_SENSOR
            },
            CONF_OUTDOOR_SENSOR: "sensor.outdoor_temperature",
            CONF_HEAT_LIMIT: 18.0,
        },
    )
    await hass.async_block_till_done()
    assert result["type"] == "create_entry"
    assert entry.options[CONF_HEAT_LIMIT] == 18.0
    assert entry.options[CONF_OUTDOOR_SENSOR] == "sensor.outdoor_temperature"


async def test_clearing_the_source_is_how_seasons_are_switched_off(
    hass: HomeAssistant,
):
    entry = seasons(hass, **{CONF_OUTDOOR_SENSOR: "sensor.outdoor_temperature"})
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    flow = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        flow["flow_id"],
        user_input={
            key: value
            for key, value in season_options().items()
            if key != CONF_OUTDOOR_SENSOR
        },
    )
    await hass.async_block_till_done()
    assert entry.options[CONF_OUTDOOR_SENSOR] is None
