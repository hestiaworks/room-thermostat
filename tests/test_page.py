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
