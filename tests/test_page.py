"""What the page has to be, checked against its source.

The page is a single file of JavaScript with no build step and no test runner,
so these are the checks that catch failures invisible from Python — and every
one of them is a mistake that has already been made once.
"""

from pathlib import Path

import pytest

PAGE = (
    Path(__file__).parent.parent
    / "custom_components/room_thermostat/frontend/room-thermostat-page.js"
)


@pytest.fixture
def source() -> str:
    return PAGE.read_text()


def test_it_defines_the_element_home_assistant_looks_for(source: str):
    """A panel is instantiated as ha-panel-<component_name>. Defining only the
    bare name gives a sidebar entry that opens on nothing."""
    assert 'customElements.define("ha-panel-room-thermostat-page"' in source


def test_the_constructor_sets_no_reflected_dom_property(source: str):
    """A custom element may not gain an attribute in its constructor.
    Assigning to `hidden` reflects to one, which throws NotSupportedError,
    marks the definition failed, and leaves a page that silently never
    renders — which is exactly what it did."""
    constructor = source[source.index("constructor() {") : source.index("set hass(")]
    for reflected in ("this.hidden =", "this.title =", "this.id =", "this.slot ="):
        assert reflected not in constructor


def test_the_fonts_are_injected_into_the_document(source: str):
    """@font-face inside a shadow root is ignored by Chromium, so the page
    would render in whatever face the browser felt like."""
    assert "document.head.appendChild" in source


def test_the_fonts_are_served_by_this_integration(source: str):
    """Copied from the panel manager, where they are served from its own
    folder. Left as they were, every face would 404."""
    assert "/nspanel_companion/frontend/fonts/" not in source
    assert "/room_thermostat/frontend/fonts/" in source


def test_no_divider_or_container_is_outlined_in_the_accent_colour(source: str):
    """From the stylesheet's own header: accent means "this is the thing you
    selected". An accent border on a divider or a card makes the least
    important element the loudest on screen.

    A control whose fill is accent may carry a matching border — that is state
    drawn as a fill, which is the rule rather than a breach of it. What may
    never take one is structure.
    """
    structure = (
        ".app-bar", ".tabs", "main", ".band", ".row", ".room-card", ".chart",
        ".foot", ".rooms-table", ".editor", ".demand", ".legend", ".empty",
    )
    offenders = [
        line.strip()
        for line in source.splitlines()
        if "border" in line
        and "var(--accent)" in line
        and "background:var(--accent)" not in line.replace(" ", "")
        and any(line.lstrip().startswith(selector) for selector in structure)
    ]
    assert offenders == []


def test_no_chart_library_is_loaded(source: str):
    """Home Assistant's own chart component is internal API that moves between
    releases, and a CDN is not reachable from plenty of installs."""
    assert "import(" not in source
    assert "cdn" not in source.lower()


# --- the rooms tab -------------------------------------------------------


def test_every_room_is_drawn_from_the_record_not_from_a_copy(source: str):
    """A card built from a stale copy shows a room that no longer exists."""
    assert "this.rooms.map" in source


def test_live_values_come_from_the_state_machine(source: str):
    """Current temperature and mode are entity state. A command for them would
    be a slower copy of something already in the browser."""
    assert "room_thermostat/rooms/state" not in source
    assert "this._hass?.states" in source or "this._hass.states" in source


def test_a_card_joins_its_room_by_id_rather_than_by_name(source: str):
    """Two rooms may be named alike, and a room being renamed would otherwise
    lose its card mid-edit."""
    assert "attributes?.room_id === room.id" in source


def test_a_card_says_why_a_room_is_idle(source: str):
    """"idle" alone is what made the season lockout look like a fault."""
    assert "out of heating season" in source
    assert "out of cooling season" in source


def test_mode_and_setpoint_are_commands_rather_than_settings(source: str):
    """Changing a mode is not an edit to the record, so it must not be drafted
    or wait for a save."""
    assert '"set_hvac_mode"' in source
    assert '"set_temperature"' in source
    commands = source[source.index("async setMode(") : source.index("roomEditor()")]
    assert "this.draft" not in commands


def test_a_room_with_no_reading_says_so_rather_than_drawing_nothing(source: str):
    assert "No reading" in source


# --- the editor ----------------------------------------------------------


def test_the_editor_edits_a_draft_rather_than_the_record(source: str):
    """Typing into the record would save half a room on every keystroke."""
    assert "this.draft" in source


def test_typing_does_not_redraw_the_form(source: str):
    """A redraw on every keystroke puts the caret at the end of the field."""
    take = source[source.index("  take(field) {") : source.index("/*\n * Home Assistant")]
    assert "this.render()" not in take


def test_a_refused_save_shows_the_problem_beside_the_field(source: str):
    assert "this.problems[name]" in source
    assert "PROBLEMS[problem]" in source


def test_every_refusal_the_server_can_send_has_words_here(source: str):
    """A code the page cannot translate reaches somebody as "own_entity"."""
    for code in ("required", "own_entity", "no_devices"):
        assert f"  {code}:" in source


def test_deleting_a_room_is_confirmed_and_names_what_goes(source: str):
    """It takes the room, its device and its entities. A misclick that does
    that silently is not acceptable."""
    assert "window.confirm(" in source
    assert "its device go with it" in source


# --- the house tab -------------------------------------------------------


def test_the_house_tab_explains_what_the_numbers_currently_mean(source: str):
    """A threshold whose far side you cannot see is what went wrong with
    bright and dark on the panel: the setting was right and nobody could
    tell."""
    assert "out of season" in source
    assert "damped" in source
    assert "The outdoor average is" in source


def test_the_dwell_is_explained_rather_than_only_labelled(source: str):
    """Six hours of nothing happening looks broken unless it is named."""
    assert "the dwell" in source
    assert "dips below the limit for a few hours" in source


def test_an_empty_outdoor_source_saves_as_null(source: str):
    """Clearing it is how seasons are switched off, so the empty string must
    not be written where a null belongs."""
    payload = source[source.index("housePayload()") : source.index("async saveHouse()")]
    assert "= null" in payload


def test_the_house_says_when_it_has_nothing_to_hold_back(source: str):
    assert "nothing is held back" in source


# --- the timeline --------------------------------------------------------


def test_the_hysteresis_is_drawn_as_a_band(source: str):
    """A line cannot show an average that entered the band and did not leave
    it, which is the whole behaviour the band exists to explain."""
    assert "hysteresis-band" in source
    assert 'y="${y(limit + hysteresis)' in source


def test_a_gap_in_a_series_breaks_the_line(source: str):
    """A sensor that was offline did not read zero. Joining across the gap
    draws a plunge that never happened."""
    path = source[source.index("  path(points, x, y) {") : source.index("timelineSeries(")]
    assert "value === null" in path
    assert "open = false" in path


def test_the_time_axis_is_labelled_at_both_ends(source: str):
    assert "when(data.start" in source
    assert "when(data.end" in source


def test_a_span_with_nothing_recorded_says_so(source: str):
    assert "Nothing recorded over this span yet" in source


# --- the energy signature ------------------------------------------------


def test_the_signature_says_what_it_needs_before_it_can_speak(source: str):
    """Weeks of heating weather. An empty chart with no explanation reads as
    broken."""
    assert "before it can say anything" in source
    assert "day${days.length === 1" in source


def test_the_measured_balance_point_is_shown_against_the_setting(source: str):
    """The number on its own is trivia; beside the limit it is a decision."""
    assert "balance_point" in source
    assert "heat_limit" in source
    assert "Measured balance point" in source


def test_the_verdict_says_which_way_the_limit_is_wrong(source: str):
    assert "heating runs on days it need not" in source
    assert "held back on days it would use it" in source


def test_only_days_that_used_heat_are_fitted(source: str):
    """Summer days sit flat on zero and would bend a line that is only
    meaningful where heating ran."""
    fit = source[source.index("hoursAt(days, outdoor)") : source.index("signature(data)")]
    assert "day.hours > 0" in fit
