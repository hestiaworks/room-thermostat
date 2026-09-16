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
