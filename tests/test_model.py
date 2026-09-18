"""The records the page edits, and what makes one invalid."""

from custom_components.room_thermostat.const import CONTROLS
from custom_components.room_thermostat.model import House, Room, room_problems


def test_a_room_keeps_the_defaults_it_was_not_given():
    room = Room.from_dict({"id": "abc", "name": "Bedroom",
                           "temperature_sensor": "sensor.bedroom"})
    assert room.cooling_strategy == "passthrough"
    assert room.frost_temperature == 5.0
    assert room.heaters == ()


def test_a_room_survives_a_round_trip():
    data = {"id": "abc", "name": "Bedroom",
            "temperature_sensor": "sensor.bedroom",
            "heaters": ["switch.radiator"], "cooling_strategy": "gated"}
    assert Room.from_dict(Room.from_dict(data).to_dict()) == Room.from_dict(data)


def test_a_key_this_version_has_never_heard_of_is_ignored():
    """A record written by a later version, or a page sending something new,
    is not worth failing a house over."""
    room = Room.from_dict({"id": "abc", "name": "Bedroom", "moon_phase": "waxing"})
    assert room.id == "abc"


def test_the_house_carries_the_season_defaults():
    house = House.from_dict({})
    assert house.outdoor_sensor is None
    assert house.damping_hours == 30.0
    assert house.season_dwell_hours == 6.0
    assert house.heat_limit == 16.0
    assert house.cool_limit == 15.0
    assert house.heat_override == 4.0


def test_a_room_needs_a_temperature_sensor():
    problems = room_problems({"name": "Bedroom"}, own_entity_ids=set())
    assert problems == {"temperature_sensor": "required"}


def test_a_room_that_can_neither_heat_nor_cool_is_a_thermometer():
    problems = room_problems(
        {"name": "Bedroom", "temperature_sensor": "sensor.bedroom"},
        own_entity_ids=set(),
    )
    assert problems == {"base": "no_devices"}


def test_a_room_may_not_drive_one_of_our_own_entities():
    """A room driving one of these would drive itself, and the loop is not
    visible from the page."""
    problems = room_problems(
        {"name": "Bedroom", "temperature_sensor": "sensor.bedroom",
         "cooler": "climate.bedroom"},
        own_entity_ids={"climate.bedroom"},
    )
    assert problems == {"cooler": "own_entity"}


def test_a_room_needs_a_name():
    problems = room_problems(
        {"temperature_sensor": "sensor.bedroom", "heaters": ["switch.rad"]},
        own_entity_ids=set(),
    )
    assert problems == {"name": "required"}


def test_a_name_of_only_spaces_is_not_a_name():
    problems = room_problems(
        {"name": "   ", "temperature_sensor": "sensor.bedroom",
         "heaters": ["switch.rad"]},
        own_entity_ids=set(),
    )
    assert problems == {"name": "required"}


def test_a_complete_room_has_no_problems():
    assert room_problems(
        {"name": "Bedroom", "temperature_sensor": "sensor.bedroom",
         "heaters": ["switch.radiator"]},
        own_entity_ids=set(),
    ) == {}


def test_a_source_written_as_null_falls_back_to_none_of_them():
    """A room's form wrote every source key, including the ones left empty, so
    a real room has heaters: null rather than no heaters key at all. Carrying
    the null through makes a record that cannot be written back out."""
    room = Room.from_dict(
        {"id": "abc", "name": "Living Room", "heaters": None,
         "inverted_heaters": None, "visible_controls": None}
    )
    assert room.heaters == ()
    assert room.inverted_heaters == ()
    assert room.visible_controls == CONTROLS
    assert room.to_dict()["heaters"] == []
