"""Reducing a month of readings to something a chart can draw."""

from custom_components.room_thermostat.history import (
    balance_point,
    bucket,
    daily,
    spans_of,
)


def test_a_bucket_is_the_mean_of_what_falls_in_it():
    points = [(0.0, 10.0), (1.0, 20.0), (5.0, 30.0), (6.0, 40.0)]
    assert bucket(points, 0.0, 10.0, 2) == [15.0, 35.0]


def test_a_bucket_with_nothing_in_it_is_a_gap_not_a_zero():
    """A sensor that was offline did not read zero degrees, and a chart that
    draws it as zero is worse than one that draws nothing."""
    points = [(0.0, 10.0)]
    assert bucket(points, 0.0, 10.0, 2) == [10.0, None]


def test_a_point_on_the_boundary_belongs_to_the_bucket_it_starts():
    points = [(5.0, 99.0)]
    assert bucket(points, 0.0, 10.0, 2) == [None, 99.0]


def test_points_outside_the_window_are_ignored():
    points = [(-5.0, 1.0), (5.0, 20.0), (50.0, 1.0)]
    assert bucket(points, 0.0, 10.0, 2) == [None, 20.0]


def test_an_empty_series_is_all_gaps():
    assert bucket([], 0.0, 10.0, 3) == [None, None, None]


def test_the_on_intervals_of_a_switching_series():
    """The season bands are drawn from these, so an interval that never ends
    has to run to the end of the window rather than vanish."""
    points = [(0.0, 0.0), (2.0, 1.0), (4.0, 0.0), (8.0, 1.0)]
    assert spans_of(points, 0.0, 10.0) == [(2.0, 4.0), (8.0, 10.0)]


def test_a_series_that_starts_on_starts_its_span_at_the_window():
    points = [(0.0, 1.0), (3.0, 0.0)]
    assert spans_of(points, 0.0, 10.0) == [(0.0, 3.0)]


def test_a_series_that_never_switches_on_has_no_spans():
    assert spans_of([(0.0, 0.0), (5.0, 0.0)], 0.0, 10.0) == []


def test_a_day_is_an_outdoor_mean_and_a_count_of_heating_hours():
    """The energy signature's dot. Demand is a fraction of each hour, so a
    day's heating hours is the sum of those fractions."""
    outdoor = {"2026-01-01": [4.0, 6.0], "2026-01-02": [10.0, 12.0]}
    demand = {"2026-01-01": [1.0, 0.5], "2026-01-02": [0.0, 0.25]}
    assert daily(outdoor, demand) == [
        {"date": "2026-01-01", "outdoor": 5.0, "hours": 1.5},
        {"date": "2026-01-02", "outdoor": 11.0, "hours": 0.25},
    ]


def test_a_day_with_no_outdoor_reading_is_not_a_dot():
    assert daily({}, {"2026-01-01": [1.0]}) == []


def test_the_balance_point_is_where_the_heating_line_reaches_zero():
    """A straight line through days that used heat: 12 hours at 0 degrees,
    none at 16. It crosses zero at 16."""
    days = [
        {"date": "a", "outdoor": 0.0, "hours": 12.0},
        {"date": "b", "outdoor": 4.0, "hours": 9.0},
        {"date": "c", "outdoor": 8.0, "hours": 6.0},
        {"date": "d", "outdoor": 12.0, "hours": 3.0},
    ]
    assert round(balance_point(days), 1) == 16.0


def test_days_that_used_no_heat_do_not_drag_the_line_down():
    """Summer days sit flat on zero. Including them bends a line that is only
    meaningful where heating actually ran."""
    days = [
        {"date": "a", "outdoor": 0.0, "hours": 12.0},
        {"date": "b", "outdoor": 4.0, "hours": 9.0},
        {"date": "c", "outdoor": 8.0, "hours": 6.0},
        # A fortnight of summer, sitting flat on zero.
        *[
            {"date": f"s{i}", "outdoor": 24.0 + i, "hours": 0.0}
            for i in range(14)
        ],
    ]
    assert round(balance_point(days), 1) == 16.0


def test_too_few_heating_days_is_no_answer_rather_than_a_wrong_one():
    assert balance_point([{"date": "a", "outdoor": 0.0, "hours": 12.0}]) is None
    assert balance_point([]) is None


def test_a_flat_line_has_no_crossing():
    days = [
        {"date": "a", "outdoor": 0.0, "hours": 6.0},
        {"date": "b", "outdoor": 5.0, "hours": 6.0},
        {"date": "c", "outdoor": 9.0, "hours": 6.0},
    ]
    assert balance_point(days) is None


# --- the command the page calls ------------------------------------------


async def test_the_history_command_answers_with_every_part_the_page_draws(
    hass, hass_ws_client, socket_enabled
):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.room_thermostat.const import (
        CONF_ENTRY_TYPE,
        DOMAIN,
        ENTRY_HUB,
    )

    entry = MockConfigEntry(
        domain=DOMAIN, title="Room Thermostat", data={CONF_ENTRY_TYPE: ENTRY_HUB}
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await hass.data[DOMAIN]["store"].async_add_room(
        {"name": "Bedroom", "temperature_sensor": "sensor.bedroom",
         "heaters": ["switch.radiator"]}
    )
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "room_thermostat/history", "span": "24h"})
    result = (await client.receive_json())["result"]

    assert result["buckets"] == 96
    assert len(result["series"]["outdoor"]) == 96
    assert len(result["series"]["rooms"]) == 1
    assert result["seasons"] == []
    assert result["daily"] == []
    assert result["balance_point"] is None


async def test_an_unknown_span_is_refused(hass, hass_ws_client, socket_enabled):
    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "room_thermostat/history", "span": "forever"}
    )
    message = await client.receive_json()
    assert not message["success"]
