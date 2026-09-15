"""The house-level Seasons entry: created by the integration, never offered."""

from datetime import timedelta

from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.room_thermostat.config_flow import default_options, season_options
from custom_components.room_thermostat.const import (
    CONF_DAMPING_HOURS,
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


def _seasons_entries(hass: HomeAssistant) -> list:
    return [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_SEASONS
    ]


async def test_setting_up_a_room_brings_the_seasons_entry_into_being(
    hass: HomeAssistant,
):
    hass.states.async_set("sensor.bedroom_temperature", "21.0")
    entry = room(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert len(_seasons_entries(hass)) == 1


async def test_two_rooms_do_not_bring_two(hass: HomeAssistant):
    """Setting the component up sets up every room at once, which is exactly
    the race the request has to survive."""
    hass.states.async_set("sensor.bedroom_temperature", "21.0")
    hass.states.async_set("sensor.kitchen_temperature", "21.0")
    first, second = room(hass), room(hass, "Kitchen")
    await hass.config_entries.async_setup(first.entry_id)
    await hass.async_block_till_done()
    assert str(second.state) == "ConfigEntryState.LOADED"  # alongside the first
    assert len(_seasons_entries(hass)) == 1


async def test_a_house_that_already_has_one_gains_no_second(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "21.0")
    seasons(hass)
    entry = room(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert len(_seasons_entries(hass)) == 1


# --- the two sensors, and the damping loop -------------------------------


async def _advance(hass: HomeAssistant, freezer, hours: float) -> None:
    """Let the loop tick through `hours` of clock, ten minutes at a time."""
    for _ in range(int(hours * 6)):
        freezer.tick(timedelta(minutes=10))
        async_fire_time_changed(hass, dt_util.utcnow())
        await hass.async_block_till_done()


async def test_with_no_outdoor_source_both_seasons_are_on(hass: HomeAssistant):
    """Fail open: the created state gates nothing."""
    entry = seasons(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.heating_season").state == "on"
    assert hass.states.get("binary_sensor.cooling_season").state == "on"


async def test_the_average_seeds_from_the_first_reading(hass: HomeAssistant):
    hass.states.async_set("sensor.outdoor", "8.0")
    entry = seasons(hass, **{CONF_OUTDOOR_SENSOR: "sensor.outdoor"})
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.heating_season")
    assert state.attributes["damped"] == 8.0
    assert state.state == "on"  # 8 is below the 16 limit


async def test_a_warm_average_holds_heating_out_of_season(
    hass: HomeAssistant, freezer
):
    hass.states.async_set("sensor.outdoor", "20.0")
    entry = seasons(hass, **{CONF_OUTDOOR_SENSOR: "sensor.outdoor"})
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    # It starts in season and leaves once the dwell has passed.
    await _advance(hass, freezer, hours=7)
    assert hass.states.get("binary_sensor.heating_season").state == "off"


async def test_a_few_hours_of_cold_is_not_a_season(hass: HomeAssistant, freezer):
    """The dwell: a night that dips below the limit changes nothing."""
    hass.states.async_set("sensor.outdoor", "20.0")
    entry = seasons(
        hass, **{CONF_OUTDOOR_SENSOR: "sensor.outdoor", CONF_DAMPING_HOURS: 1.0}
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _advance(hass, freezer, hours=7)
    assert hass.states.get("binary_sensor.heating_season").state == "off"

    hass.states.async_set("sensor.outdoor", "2.0")
    await _advance(hass, freezer, hours=3)
    assert hass.states.get("binary_sensor.heating_season").state == "off"


async def test_a_cold_spell_that_lasts_turns_heating_season_on(
    hass: HomeAssistant, freezer
):
    hass.states.async_set("sensor.outdoor", "20.0")
    entry = seasons(
        hass, **{CONF_OUTDOOR_SENSOR: "sensor.outdoor", CONF_DAMPING_HOURS: 1.0}
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _advance(hass, freezer, hours=7)
    assert hass.states.get("binary_sensor.heating_season").state == "off"

    hass.states.async_set("sensor.outdoor", "2.0")
    await _advance(hass, freezer, hours=8)
    assert hass.states.get("binary_sensor.heating_season").state == "on"


async def test_cooling_follows_the_live_reading_not_the_average(
    hass: HomeAssistant, freezer
):
    """A hot afternoon in a cold week is still a hot afternoon, and is not
    made to wait for a dwell."""
    hass.states.async_set("sensor.outdoor", "2.0")
    entry = seasons(hass, **{CONF_OUTDOOR_SENSOR: "sensor.outdoor"})
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.cooling_season").state == "off"

    hass.states.async_set("sensor.outdoor", "28.0")
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.cooling_season").state == "on"
    # The average has barely moved, so heating is still in season.
    assert hass.states.get("binary_sensor.heating_season").state == "on"


async def test_an_unavailable_source_fails_open_and_freezes_the_average(
    hass: HomeAssistant, freezer
):
    hass.states.async_set("sensor.outdoor", "20.0")
    entry = seasons(hass, **{CONF_OUTDOOR_SENSOR: "sensor.outdoor"})
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _advance(hass, freezer, hours=7)
    assert hass.states.get("binary_sensor.heating_season").state == "off"

    hass.states.async_set("sensor.outdoor", "unavailable")
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.heating_season")
    assert state.state == "on"
    assert state.attributes["damped"] == 20.0  # frozen, not poisoned
    assert hass.states.get("binary_sensor.cooling_season").state == "on"


async def test_a_sun_baked_reading_is_treated_as_a_fault(hass: HomeAssistant):
    hass.states.async_set("sensor.outdoor", "20.0")
    entry = seasons(hass, **{CONF_OUTDOOR_SENSOR: "sensor.outdoor"})
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("sensor.outdoor", "95.0")
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.heating_season").attributes["damped"] == 20.0


async def test_fahrenheit_is_converted(hass: HomeAssistant):
    hass.states.async_set("sensor.outdoor", "68.0", {"unit_of_measurement": "°F"})
    entry = seasons(hass, **{CONF_OUTDOOR_SENSOR: "sensor.outdoor"})
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.heating_season").attributes["damped"] == 20.0


async def test_a_weather_entity_may_be_the_source(hass: HomeAssistant):
    hass.states.async_set("weather.home", "cloudy", {"temperature": 8.0})
    entry = seasons(hass, **{CONF_OUTDOOR_SENSOR: "weather.home"})
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.heating_season").attributes["damped"] == 8.0


async def test_a_long_lost_source_asks_a_human_for_help(
    hass: HomeAssistant, freezer
):
    from homeassistant.helpers import issue_registry as ir

    hass.states.async_set("sensor.outdoor", "20.0")
    entry = seasons(hass, **{CONF_OUTDOOR_SENSOR: "sensor.outdoor"})
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("sensor.outdoor", "unavailable")
    await _advance(hass, freezer, hours=1.5)
    assert ir.async_get(hass).async_get_issue(DOMAIN, "outdoor_lost") is not None


# --- a room obeying ------------------------------------------------------


async def _heat_to(hass: HomeAssistant, target: float) -> None:
    """Ask the room for heat. The radiator's own services are mocked, as in
    every other test here: what matters is whether it is asked."""
    async_mock_service(hass, "switch", "turn_on")
    async_mock_service(hass, "switch", "turn_off")
    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": "climate.bedroom", "temperature": target},
        blocking=True,
    )
    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": "climate.bedroom", "hvac_mode": "heat"},
        blocking=True,
    )
    await hass.async_block_till_done()


async def test_a_room_with_no_seasons_entry_behaves_as_before(hass: HomeAssistant):
    """The upgrade path: a room is unchanged until a source is chosen."""
    hass.states.async_set("sensor.bedroom_temperature", "20.0")
    hass.states.async_set("switch.radiator", "off")
    entry = room(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _heat_to(hass, 22.0)
    assert hass.states.get("climate.bedroom").attributes["hvac_action"] == "heating"


async def test_a_seasons_entry_with_no_source_changes_nothing(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "20.0")
    hass.states.async_set("switch.radiator", "off")
    seasons(hass)
    entry = room(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _heat_to(hass, 22.0)
    assert hass.states.get("climate.bedroom").attributes["hvac_action"] == "heating"


async def test_out_of_season_a_room_stops_heating_and_says_why(
    hass: HomeAssistant, freezer
):
    hass.states.async_set("sensor.bedroom_temperature", "20.0")
    hass.states.async_set("switch.radiator", "off")
    hass.states.async_set("sensor.outdoor", "22.0")
    seasons(hass, **{CONF_OUTDOOR_SENSOR: "sensor.outdoor"})
    entry = room(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _heat_to(hass, 22.0)
    # It takes the dwell for the house to decide it is out of season.
    await _advance(hass, freezer, hours=7)

    state = hass.states.get("climate.bedroom")
    assert state.attributes["hvac_action"] == "idle"
    assert state.attributes["heating_season"] is False


async def test_out_of_season_a_cold_room_still_heats(hass: HomeAssistant, freezer):
    hass.states.async_set("sensor.bedroom_temperature", "17.0")
    hass.states.async_set("switch.radiator", "off")
    hass.states.async_set("sensor.outdoor", "22.0")
    seasons(hass, **{CONF_OUTDOOR_SENSOR: "sensor.outdoor"})
    entry = room(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _heat_to(hass, 22.0)
    await _advance(hass, freezer, hours=7)

    state = hass.states.get("climate.bedroom")
    assert state.attributes["heating_season"] is False
    assert state.attributes["hvac_action"] == "heating"


async def test_a_renamed_season_sensor_is_still_obeyed(
    hass: HomeAssistant, freezer
):
    """Rooms find the sensors by unique id, so renaming one does not quietly
    release every room in the house."""
    from homeassistant.helpers import entity_registry as er

    hass.states.async_set("sensor.bedroom_temperature", "20.0")
    hass.states.async_set("switch.radiator", "off")
    hass.states.async_set("sensor.outdoor", "22.0")
    seasons_entry = seasons(hass, **{CONF_OUTDOOR_SENSOR: "sensor.outdoor"})
    await hass.config_entries.async_setup(seasons_entry.entry_id)
    await hass.async_block_till_done()
    er.async_get(hass).async_update_entity(
        "binary_sensor.heating_season", new_entity_id="binary_sensor.winter_is_here"
    )
    await hass.async_block_till_done()

    entry = room(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _heat_to(hass, 22.0)
    await _advance(hass, freezer, hours=7)

    assert hass.states.get("climate.bedroom").attributes["hvac_action"] == "idle"
