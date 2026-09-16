"""One door for the integration.

Rooms used to be made here, one config flow each. They are made on the page
now, which is the record — so all this flow does is bring the integration into
being, once, so that the page exists to make them on.

What the old flow's tests protected has not been thrown away: the validation
they exercised is `model.room_problems`, tested in test_model.py, and the rule
that a room created before sources moved out of entry data still finds them is
the migration's job, tested in test_migration.py.
"""

from homeassistant.core import HomeAssistant

from custom_components.room_thermostat.const import CONF_ENTRY_TYPE, DOMAIN, ENTRY_HUB


async def test_adding_the_integration_creates_the_hub(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "Room Thermostat"
    assert result["data"] == {CONF_ENTRY_TYPE: ENTRY_HUB}


async def test_there_is_only_ever_one(hass: HomeAssistant):
    await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    again = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert again["type"] == "abort"
    assert again["reason"] == "single_instance_allowed"


async def test_no_room_form_is_offered_here_any_more(hass: HomeAssistant):
    """A form would be a second place to make a room, and the page is the
    record."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] != "form"
