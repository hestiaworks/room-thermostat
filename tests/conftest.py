"""pytest-homeassistant-custom-component needs custom integrations enabled."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True, scope="session")
def _start_the_dns_resolvers_thread():
    """Let pycares start its thread before any test counts the threads.

    The websocket tests open a real connection, which resolves a name, which
    has aiohttp's DNS resolver spawn a daemon thread that lives for the
    process. It is created once, so exactly one test sees a thread appear
    underneath it and fails a cleanup check it had nothing to do with.

    Starting it here means every test's before-and-after count agrees.
    """
    try:
        import pycares
    except ImportError:
        yield
        return
    channel = pycares.Channel()
    try:
        yield
    finally:
        channel.cancel()
