from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.room_thermostat.const import (
    CONF_COOLER,
    CONF_HEATERS,
    CONF_TEMPERATURE_SENSOR,
    DEFAULT_PARKED_SETPOINT,
    DOMAIN,
)


async def test_a_room_can_be_added_with_a_sensor_and_both_devices(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
            CONF_HEATERS: ["switch.bedroom_radiator_a", "switch.bedroom_radiator_b"],
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Bedroom"
    # Sources live in the options, which is the only door a helper offers.
    assert result["options"][CONF_HEATERS] == [
        "switch.bedroom_radiator_a",
        "switch.bedroom_radiator_b",
    ]


async def test_a_room_needs_a_temperature_sensor(hass: HomeAssistant):
    """It is the reason the integration exists; without it there is nothing to
    control against."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Bedroom", CONF_HEATERS: ["switch.a"]}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_TEMPERATURE_SENSOR: "required"}


async def test_a_room_needs_at_least_one_device(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "Bedroom", CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature"},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "no_devices"}


async def test_tunables_start_at_their_documented_defaults(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
        },
    )
    assert result["options"]["parked_setpoint"] == DEFAULT_PARKED_SETPOINT


async def test_a_rooms_devices_can_be_changed_after_it_is_created(hass: HomeAssistant):
    """Adding a valve to an existing room must not mean deleting the room:
    that would take its history, its entity ids and its dashboard cards."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.room_thermostat.config_flow import default_options

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bedroom",
        data={
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
        },
        options=default_options(),
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
            CONF_HEATERS: ["switch.bedroom_radiator"],
        },
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HEATERS] == ["switch.bedroom_radiator"]

    # Reconfiguring reloads the room, which starts its control loop. Let the
    # reload finish before unloading, or it recreates the entity afterwards.
    await hass.async_block_till_done()
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_reconfiguring_still_insists_on_a_temperature_sensor(hass: HomeAssistant):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.room_thermostat.config_flow import default_options

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bedroom",
        data={
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
        },
        options=default_options(),
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Bedroom", CONF_COOLER: "climate.bedroom_ac"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_TEMPERATURE_SENSOR: "required"}


async def test_reconfiguring_keeps_the_tunables_it_was_not_asked_about(
    hass: HomeAssistant,
):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.room_thermostat.config_flow import default_options

    options = {**default_options(), "parked_setpoint": 16.0}
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bedroom",
        data={
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
        },
        options=options,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Bedroom",
            CONF_TEMPERATURE_SENSOR: "sensor.bedroom_temperature",
            CONF_COOLER: "climate.bedroom_ac",
            CONF_HEATERS: ["switch.bedroom_radiator"],
        },
    )
    assert entry.options["parked_setpoint"] == 16.0

    await hass.async_block_till_done()
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_a_room_created_before_the_move_still_finds_its_devices(
    hass: HomeAssistant,
):
    """Early rooms kept their sources in the entry's data. They must keep
    working without being recreated."""
    from custom_components.room_thermostat.config_flow import sources

    class Entry:
        data = {
            "name": "Living Room",
            CONF_TEMPERATURE_SENSOR: "sensor.old_place",
            CONF_COOLER: "climate.living_room_ac",
        }
        options = {}

    assert sources(Entry())[CONF_TEMPERATURE_SENSOR] == "sensor.old_place"


async def test_a_room_cannot_be_its_own_air_conditioner(hass: HomeAssistant):
    """Selecting one of these thermostats as the unit makes a room drive
    itself, and the loop is not obvious from the interface."""
    from homeassistant.helpers import entity_registry as er
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.room_thermostat.config_flow import default_options

    existing = MockConfigEntry(domain=DOMAIN, title="Study", data={"name": "Study"})
    existing.add_to_hass(hass)
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "climate", DOMAIN, "study-unique", suggested_object_id="study"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Study Two",
            CONF_TEMPERATURE_SENSOR: "sensor.study_temperature",
            CONF_COOLER: "climate.study",
        },
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_COOLER: "own_entity"}


def test_a_helper_can_be_offered_as_a_temperature_source():
    """Selecting an input_number is what makes the behaviour testable without
    a real room, so the picker has to offer one."""
    from custom_components.room_thermostat.config_flow import DEVICES_SCHEMA
    from custom_components.room_thermostat.const import CONF_TEMPERATURE_SENSOR

    for key, value in DEVICES_SCHEMA.schema.items():
        if key.schema == CONF_TEMPERATURE_SENSOR:
            domains = {
                domain
                for entry in value.config["filter"]
                for domain in (
                    entry["domain"]
                    if isinstance(entry["domain"], list)
                    else [entry["domain"]]
                )
            }
            assert {"sensor", "input_number", "number"} <= domains
            return
    raise AssertionError("no temperature sensor field in the schema")


async def test_changing_one_source_does_not_wipe_the_others(hass: HomeAssistant):
    """A room created before sources moved into options keeps them in data.
    Writing a single key into options must not orphan the rest."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.room_thermostat.config_flow import default_options, sources
    from custom_components.room_thermostat.const import CONF_INVERTED_HEATERS

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living Room",
        data={
            "name": "Living Room",
            CONF_TEMPERATURE_SENSOR: "sensor.living_room_temperature",
            CONF_COOLER: "climate.living_room_ac",
            CONF_HEATERS: ["valve.radiator"],
        },
        options={**default_options(), CONF_INVERTED_HEATERS: ["valve.radiator"]},
    )
    entry.add_to_hass(hass)

    found = sources(entry)
    assert found[CONF_TEMPERATURE_SENSOR] == "sensor.living_room_temperature"
    assert found[CONF_COOLER] == "climate.living_room_ac"
    assert found[CONF_HEATERS] == ["valve.radiator"]
    assert found[CONF_INVERTED_HEATERS] == ["valve.radiator"]



async def room(hass: HomeAssistant, **options):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.room_thermostat.config_flow import default_options

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living Room",
        data={"name": "Living Room"},
        options={**default_options(), **options},
    )
    entry.add_to_hass(hass)
    return entry


async def test_everything_is_configured_on_one_form(hass: HomeAssistant):
    """Two nested dialogs to reach a setting was ceremony. One form, grouped."""
    entry = await room(
        hass,
        temperature_sensor="sensor.t",
        cooler="climate.ac",
    )
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    groups = {key.schema for key in result["data_schema"].schema}
    assert groups == {"sensors", "devices", "cooling", "heating", "safety"}


async def test_the_one_form_saves_sources_and_tuning_together(hass: HomeAssistant):
    entry = await room(hass, temperature_sensor="sensor.t", cooler="climate.ac")
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "sensors": {"temperature_sensor": "sensor.better", "humidity_sensor": "sensor.h"},
            "devices": {"cooler": "climate.ac", "heaters": ["valve.radiator"]},
            "cooling": {"cooling_strategy": "gated", "offset_correction": False,
                        "parked_setpoint": 16.0, "cool_cold_tolerance": 0.5,
                        "cool_hot_tolerance": 0.5, "cool_min_on": 900.0,
                        "cool_min_off": 900.0},
            "heating": {"allow_ac_heat": False, "heat_cold_tolerance": 0.3,
                        "heat_hot_tolerance": 0.3, "heat_min_on": 300.0,
                        "heat_min_off": 300.0, "valve_travel": 180.0},
            "safety": {"frost_temperature": 5.0},
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["temperature_sensor"] == "sensor.better"
    assert entry.options["heaters"] == ["valve.radiator"]
    assert entry.options["cooling_strategy"] == "gated"
    assert "sensors" not in entry.options
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_the_one_form_still_insists_on_a_temperature_sensor(hass: HomeAssistant):
    entry = await room(hass, temperature_sensor="sensor.t", cooler="climate.ac")
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "sensors": {},
            "devices": {"cooler": "climate.ac"},
            "cooling": {}, "heating": {}, "safety": {},
        },
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_TEMPERATURE_SENSOR: "required"}


async def test_an_inverted_heater_is_listed_by_its_name(hass: HomeAssistant):
    """A checklist of raw entity ids cannot be read at a glance."""
    from custom_components.room_thermostat.const import CONF_INVERTED_HEATERS

    hass.states.async_set(
        "valve.c0393798c82e_radiator", "closed", {"friendly_name": "Bedroom radiator"}
    )
    entry = await room(
        hass,
        temperature_sensor="sensor.t",
        heaters=["valve.c0393798c82e_radiator"],
    )
    result = await hass.config_entries.options.async_init(entry.entry_id)
    for key, value in result["data_schema"].schema.items():
        if key.schema != "devices":
            continue
        for inner, selector_ in value.schema.schema.items():
            if inner.schema == CONF_INVERTED_HEATERS:
                options = selector_.config["options"]
                assert options == [
                    {"value": "valve.c0393798c82e_radiator", "label": "Bedroom radiator"}
                ]
                return
    raise AssertionError("no inverted-heaters field was offered")
