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
    """"Idle" alone is what made the season lockout look like a fault."""
    assert "Idle — heating is out of season" in source
    assert "Idle — cooling is out of season" in source
    assert "frost protection still holds at" in source


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
    assert "this.problems.temperature_sensor" in source
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
    assert "LANE.band" in source
    assert "y(model.limit + model.hysteresis)" in source


def test_a_gap_in_a_series_breaks_the_line(source: str):
    """A sensor that was offline did not read zero. Joining across the gap
    draws a plunge that never happened."""
    lane = source[source.index("laneOne(model) {") : source.index("laneTwo(model) {")]
    assert "value === null" in lane
    assert "open = false" in lane


def test_the_time_axis_is_labelled_at_both_ends(source: str):
    assert "when(model.data.start" in source
    assert "when(model.data.end" in source


def test_a_span_with_nothing_recorded_says_so(source: str):
    assert "Nothing recorded over this span yet" in source


# --- the energy signature ------------------------------------------------


def test_the_signature_says_what_it_needs_before_it_can_speak(source: str):
    """Weeks of heating weather. An empty chart with no explanation reads as
    broken."""
    assert "before it can say anything" in source
    assert "not enough heating weather to fit a line" in source


def test_the_measured_balance_point_is_shown_against_the_setting(source: str):
    """The number on its own is trivia; beside the limit it is a decision."""
    assert "balance_point" in source
    assert "heat_limit" in source
    assert "the balance point lands at" in source
    assert "against your limit of" in source


def test_the_what_if_table_says_which_way_each_limit_moves_things(source: str):
    """A row of numbers is trivia; the sentence beside it is the decision."""
    assert "warmer, and the equipment runs more" in source
    assert "colder, and it runs less" in source
    assert "what you have now" in source


def test_only_days_that_used_heat_are_fitted(source: str):
    """Summer days sit flat on zero and would bend a line that is only
    meaningful where heating ran."""
    fit = source[source.index("signature(model) {") :]
    assert "day.hours > 0" in fit


# --- what the first look at it on real hardware turned up ----------------


def test_every_select_carries_the_wrapper_that_draws_its_arrow(source: str):
    """The stylesheet sets appearance:none and supplies the chevron from
    .select-wrap::after. A bare select is a box with no sign it opens."""
    import re

    for match in re.finditer(r"<select\b", source):
        before = source[max(0, match.start() - 400) : match.start()]
        assert "select-wrap" in before, source[match.start() : match.start() + 60]


def test_the_editor_hides_the_tab_bar(source: str):
    """A room's settings is somewhere you went into. Tabs say you are still
    choosing between three peers."""
    assert "tabs.hidden = Boolean(this.editing)" in source


def test_an_entity_is_chosen_by_searching_rather_than_typed(source: str):
    """Typing an entity id from memory is how you get a room pointed at
    something that does not exist."""
    assert "chooser(" in source
    assert "data-entity-search" in source
    assert 'this.chooser("temperature_sensor"' in source


def test_a_picker_only_ever_yields_an_entity_somebody_chose(source: str):
    """The search box is not a field: nothing is written to the draft until a
    result is clicked, so a half-typed search can never be saved as an id."""
    picker = source[source.index("bindPicker(root) {") : source.index("customElements.get")]
    assert "this.chose(name, option.dataset.entityOption)" in picker
    assert "this.take(" not in picker


def test_the_lanes_answer_a_pointer(source: str):
    """A chart you cannot interrogate is a picture, and a still design cannot
    draw a pointer. The numbers are the reason to open it."""
    assert "pointermove" in source
    assert "data-crosshair" in source
    assert "data-readout" in source
    assert "bindLanes(root)" in source


def test_the_page_uses_the_width_it_is_given(source: str):
    """1180px came from the panel manager, whose workspace was three narrow
    columns. This page is cards and charts."""
    assert "max-width:var(--content-max)" not in source


# --- what the design asked for -------------------------------------------


def test_the_chrome_is_drawn_once_and_only_the_body_is_replaced(source: str):
    """Replacing the whole page — bar, tabs and all — with "Reading the
    record…" is what made every navigation flash."""
    assert "renderShell()" in source
    assert "[data-body]" in source
    assert "renderBody()" in source


def test_a_reading_does_not_redraw_the_page(source: str):
    """A state arrives every few seconds. Redrawing for each one closed
    pickers mid-search and threw away the scroll position."""
    setter = source[source.index("set hass(value) {") : source.index("set narrow(")]
    assert "refreshLive()" in setter
    assert "renderBody()" not in setter
    refresh = source[source.index("refreshLive() {") : source.index("async setMode(")]
    assert "innerHTML" not in refresh.split("icon.innerHTML")[0].replace("icon.innerHTML", "")


def test_a_field_being_typed_in_is_left_alone_by_a_refresh(source: str):
    refresh = source[source.index("refreshLive() {") : source.index("async setMode(")]
    assert "root.activeElement" in refresh


def test_a_room_that_is_off_is_not_counted_as_held_back(source: str):
    """Off is a choice. Counting it as what the season rule cost would paint
    the whole lane red on a house with the heating away."""
    assert "asking &&" in source
    assert '["heat", "heat_cool"].includes' in source


def test_the_what_if_table_replays_the_window_against_other_limits(source: str):
    assert "whatIf(model)" in source
    assert "dwell ignored" in source


# --- drawn to the design, not near it ------------------------------------


def test_every_tab_shares_one_container(source: str):
    """The design gives all four screens the same 1180 px and the same 32 px
    of padding. Two tabs at different widths is the thing that reads as
    unfinished."""
    assert ".page { padding:32px; max-width:1180px; margin:0 auto; }" in source
    assert "page wide" not in source
    assert "max-width:1680px" not in source


def test_the_history_page_is_a_column_with_one_gap(source: str):
    """The design separates its blocks with a 26 px column gap rather than
    with margins on each block."""
    assert ".page.stack { display:flex; flex-direction:column; gap:26px; }" in source
    assert '<div class="page stack">' in source


def test_a_heading_inside_a_column_carries_no_margin_of_its_own(source: str):
    """It would add to the gap that already separates it."""
    assert ".column .page-head { margin-bottom:0; }" in source


def test_save_and_revert_live_in_the_app_bar(source: str):
    """Where the design puts them: the state, then Revert, then Save, on
    every screen that has something to save."""
    chrome = source[source.index("renderChrome() {") : source.index("bindChrome(root)")]
    assert "save-bar" in chrome
    assert "Revert" in chrome
    assert "Save room" in chrome and "Save the house" in chrome
    body = source[source.index("roomEditor() {") : source.index("roomInspector(")]
    assert "Save room" not in body


def test_the_corner_says_the_season_when_there_is_nothing_to_save(source: str):
    chrome = source[source.index("renderChrome() {") : source.index("bindChrome(root)")]
    assert "this.seasonWord()" in chrome


def test_the_chosen_range_is_a_primary_button(source: str):
    """The design fills it with the accent rather than tinting it."""
    assert 'data-span="${span}" class="${span === this.span ? "primary" : ""}"' in source
