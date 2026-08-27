"""The manifest is what HACS and hassfest validate; a typo here fails at install."""
import json
from pathlib import Path

MANIFEST = Path(__file__).parents[1] / "custom_components/room_thermostat/manifest.json"


def test_manifest_declares_the_domain_that_must_never_change():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["domain"] == "room_thermostat"
    assert manifest["config_flow"] is True


def test_manifest_keys_are_sorted_as_hassfest_requires():
    # hassfest requires: domain, name, then the rest alphabetically.
    keys = list(json.loads(MANIFEST.read_text()))
    assert keys[:2] == ["domain", "name"]
    assert keys[2:] == sorted(keys[2:])


def test_const_exposes_the_domain():
    from custom_components.room_thermostat.const import DOMAIN

    assert DOMAIN == "room_thermostat"


def test_manifest_version_is_a_release_shaped_version():
    """The release workflow refuses to publish a tag that disagrees with this,
    so it has to be something a tag could match."""
    import re

    version = json.loads(MANIFEST.read_text())["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?", version), version
