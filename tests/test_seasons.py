"""The house-level Seasons entry: created by the integration, never offered."""

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.room_thermostat.const import (
    CONF_DAMPING_HOURS,
    CONF_ENTRY_TYPE,
    ENTRY_HUB,
    DEFAULT_HEAT_LIMIT,
    CONF_HEATERS,
    CONF_OUTDOOR_SENSOR,
    CONF_TEMPERATURE_SENSOR,
    DEFAULT_HEAT_LIMIT,
    DOMAIN,
)


async def seasons(hass: HomeAssistant, **settings) -> MockConfigEntry:
    """A house with its seasons configured.

    The settings used to live in an entry of their own; they are part of the
    hub's record now, which is where the page edits them.
    """
    entry = next(
        (
            existing
            for existing in hass.config_entries.async_entries(DOMAIN)
            if existing.data.get(CONF_ENTRY_TYPE) == ENTRY_HUB
        ),
        None,
    )
    if entry is None:
        entry = MockConfigEntry(
            domain=DOMAIN, title="Room Thermostat", data={CONF_ENTRY_TYPE: ENTRY_HUB}
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    if settings:
        await hass.data[DOMAIN]["store"].async_update_house(settings)
        await hass.async_block_till_done()
    return entry


async def room(hass: HomeAssistant, name: str = "Bedroom") -> MockConfigEntry:
    """A house with one room in the record.

    A room is a line in the hub's record now rather than a config entry of its
    own, so a test that wants a room wants a hub.
    """
    entry = next(
        (
            existing
            for existing in hass.config_entries.async_entries(DOMAIN)
            if existing.data.get(CONF_ENTRY_TYPE) == ENTRY_HUB
        ),
        None,
    )
    if entry is None:
        entry = MockConfigEntry(
            domain=DOMAIN, title="Room Thermostat", data={CONF_ENTRY_TYPE: ENTRY_HUB}
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    await hass.data[DOMAIN]["store"].async_add_room(
        {
            "name": name,
            "temperature_sensor": f"sensor.{name.lower()}_temperature",
            "heaters": ["switch.radiator"],
        }
    )
    await hass.async_block_till_done()
    return entry


async def test_the_house_starts_with_no_source_and_the_spec_defaults(
    hass: HomeAssistant,
):
    await seasons(hass)
    house = hass.data[DOMAIN]["store"].house
    assert house.outdoor_sensor is None
    assert house.heat_limit == DEFAULT_HEAT_LIMIT


async def test_a_seasons_entry_creates_only_its_two_sensors(hass: HomeAssistant):
    await seasons(hass)
    assert hass.states.get("binary_sensor.heating_season") is not None
    assert hass.states.get("binary_sensor.cooling_season") is not None
    assert hass.states.get("climate.seasons") is None


async def test_its_settings_are_editable(hass: HomeAssistant):
    await seasons(hass)
    store = hass.data[DOMAIN]["store"]
    await store.async_update_house(
        {"outdoor_sensor": "sensor.outdoor_temperature", "heat_limit": 18.0}
    )
    await hass.async_block_till_done()
    assert store.house.heat_limit == 18.0
    assert store.house.outdoor_sensor == "sensor.outdoor_temperature"
    # And the sensor is using the new limit rather than the one it started on.
    assert hass.states.get("binary_sensor.heating_season").attributes["limit"] == 18.0


async def test_clearing_the_source_is_how_seasons_are_switched_off(
    hass: HomeAssistant, freezer
):
    hass.states.async_set("sensor.outdoor", "22.0")
    await seasons(hass, outdoor_sensor="sensor.outdoor")
    await _advance(hass, freezer, hours=7)
    assert hass.states.get("binary_sensor.heating_season").state == "off"

    await hass.data[DOMAIN]["store"].async_update_house({"outdoor_sensor": None})
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.heating_season").state == "on"


# --- the two sensors, and the damping loop -------------------------------


async def _advance(hass: HomeAssistant, freezer, hours: float) -> None:
    """Let the loop tick through `hours` of clock, ten minutes at a time."""
    for _ in range(int(hours * 6)):
        freezer.tick(timedelta(minutes=10))
        async_fire_time_changed(hass, dt_util.utcnow())
        await hass.async_block_till_done()


async def test_with_no_outdoor_source_both_seasons_are_on(hass: HomeAssistant):
    """Fail open: the created state gates nothing."""
    await seasons(hass)
    assert hass.states.get("binary_sensor.heating_season").state == "on"
    assert hass.states.get("binary_sensor.cooling_season").state == "on"


async def test_the_average_seeds_from_the_first_reading(hass: HomeAssistant):
    hass.states.async_set("sensor.outdoor", "8.0")
    await seasons(hass, outdoor_sensor="sensor.outdoor")
    state = hass.states.get("binary_sensor.heating_season")
    assert state.attributes["damped"] == 8.0
    assert state.state == "on"  # 8 is below the 16 limit


async def test_a_warm_average_holds_heating_out_of_season(
    hass: HomeAssistant, freezer
):
    hass.states.async_set("sensor.outdoor", "20.0")
    await seasons(hass, outdoor_sensor="sensor.outdoor")
    # It starts in season and leaves once the dwell has passed.
    await _advance(hass, freezer, hours=7)
    assert hass.states.get("binary_sensor.heating_season").state == "off"


async def test_a_few_hours_of_cold_is_not_a_season(hass: HomeAssistant, freezer):
    """The dwell: a night that dips below the limit changes nothing."""
    hass.states.async_set("sensor.outdoor", "20.0")
    await seasons(hass, outdoor_sensor="sensor.outdoor", damping_hours=1.0)
    await _advance(hass, freezer, hours=7)
    assert hass.states.get("binary_sensor.heating_season").state == "off"

    hass.states.async_set("sensor.outdoor", "2.0")
    await _advance(hass, freezer, hours=3)
    assert hass.states.get("binary_sensor.heating_season").state == "off"


async def test_a_cold_spell_that_lasts_turns_heating_season_on(
    hass: HomeAssistant, freezer
):
    hass.states.async_set("sensor.outdoor", "20.0")
    await seasons(hass, outdoor_sensor="sensor.outdoor", damping_hours=1.0)
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
    await seasons(hass, outdoor_sensor="sensor.outdoor")
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
    await seasons(hass, outdoor_sensor="sensor.outdoor")
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
    await seasons(hass, outdoor_sensor="sensor.outdoor")

    hass.states.async_set("sensor.outdoor", "95.0")
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.heating_season").attributes["damped"] == 20.0


async def test_fahrenheit_is_converted(hass: HomeAssistant):
    hass.states.async_set("sensor.outdoor", "68.0", {"unit_of_measurement": "°F"})
    await seasons(hass, outdoor_sensor="sensor.outdoor")
    assert hass.states.get("binary_sensor.heating_season").attributes["damped"] == 20.0


async def test_a_weather_entity_may_be_the_source(hass: HomeAssistant):
    hass.states.async_set("weather.home", "cloudy", {"temperature": 8.0})
    entry = await seasons(hass, outdoor_sensor="weather.home")
    assert hass.states.get("binary_sensor.heating_season").attributes["damped"] == 8.0


async def test_a_long_lost_source_asks_a_human_for_help(
    hass: HomeAssistant, freezer
):
    from homeassistant.helpers import issue_registry as ir

    hass.states.async_set("sensor.outdoor", "20.0")
    await seasons(hass, outdoor_sensor="sensor.outdoor")

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
    await room(hass)
    await _heat_to(hass, 22.0)
    assert hass.states.get("climate.bedroom").attributes["hvac_action"] == "heating"


async def test_a_seasons_entry_with_no_source_changes_nothing(hass: HomeAssistant):
    hass.states.async_set("sensor.bedroom_temperature", "20.0")
    hass.states.async_set("switch.radiator", "off")
    await seasons(hass)
    await room(hass)
    await _heat_to(hass, 22.0)
    assert hass.states.get("climate.bedroom").attributes["hvac_action"] == "heating"


async def test_out_of_season_a_room_stops_heating_and_says_why(
    hass: HomeAssistant, freezer
):
    hass.states.async_set("sensor.bedroom_temperature", "20.0")
    hass.states.async_set("switch.radiator", "off")
    hass.states.async_set("sensor.outdoor", "22.0")
    await seasons(hass, outdoor_sensor="sensor.outdoor")
    await room(hass)
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
    await seasons(hass, outdoor_sensor="sensor.outdoor")
    await room(hass)
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
    seasons_entry = await seasons(hass, outdoor_sensor="sensor.outdoor")
    er.async_get(hass).async_update_entity(
        "binary_sensor.heating_season", new_entity_id="binary_sensor.winter_is_here"
    )
    await hass.async_block_till_done()

    await room(hass)
    await _heat_to(hass, 22.0)
    await _advance(hass, freezer, hours=7)

    assert hass.states.get("climate.bedroom").attributes["hvac_action"] == "idle"
