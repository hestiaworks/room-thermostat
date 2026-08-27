"""pytest-homeassistant-custom-component needs custom integrations enabled."""
import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield
