"""The rules, tested without Home Assistant or hardware."""

from custom_components.room_thermostat.control import (
    CoolerCommand,
    LoopState,
    Readings,
    Request,
    RoomConfig,
    decide,
)


def config(**overrides) -> RoomConfig:
    """A radiator room with no cooler, unless a test says otherwise."""
    base = dict(
        has_cooler=False,
        has_heater=True,
        cooling_strategy="passthrough",
        offset_correction=False,
        parked_setpoint=17.0,
        cool_cold_tolerance=0.5,
        cool_hot_tolerance=0.5,
        cool_min_on=900.0,
        cool_min_off=900.0,
        heat_cold_tolerance=0.3,
        heat_hot_tolerance=0.3,
        heat_min_on=300.0,
        heat_min_off=300.0,
        valve_travel=180.0,
        allow_ac_heat=False,
        frost_temperature=5.0,
        frost_recovery=1.0,
    )
    return RoomConfig(**{**base, **overrides})


def idle(now: float = 0.0) -> LoopState:
    return LoopState(
        heaters_on=False, heaters_changed_at=now, cooler_on=False, cooler_changed_at=now
    )


def heating_since(when: float) -> LoopState:
    return LoopState(
        heaters_on=True, heaters_changed_at=when, cooler_on=False, cooler_changed_at=when
    )


def test_control_module_stays_free_of_home_assistant():
    """The boundary that makes everything above testable in milliseconds."""
    import inspect

    from custom_components.room_thermostat import control

    source = inspect.getsource(control)
    assert "homeassistant" not in source


def test_a_cold_room_calls_for_heat():
    decision = decide(
        config(),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is True
    assert decision.hvac_action == "heating"


def test_a_room_inside_the_deadband_is_left_alone():
    # 20.9 is above target minus the 0.3 cold tolerance, so nothing starts.
    decision = decide(
        config(),
        Readings(room_temperature=20.9, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is False
    assert decision.hvac_action == "idle"


def test_heat_releases_only_above_the_hot_tolerance():
    warm = decide(
        config(),
        Readings(room_temperature=21.4, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        heating_since(0.0),
        now=1000.0,
    )
    assert warm.heaters_on is False

    not_yet = decide(
        config(),
        Readings(room_temperature=21.2, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        heating_since(0.0),
        now=1000.0,
    )
    assert not_yet.heaters_on is True


def test_a_minimum_run_time_outranks_the_temperature():
    """A slab that has just started must not be stopped by a passing draught."""
    decision = decide(
        config(heat_min_on=1800.0),
        Readings(room_temperature=25.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        heating_since(900.0),
        now=1200.0,
    )
    assert decision.heaters_on is True


def test_a_minimum_off_time_outranks_the_temperature():
    just_stopped = LoopState(
        heaters_on=False, heaters_changed_at=1100.0, cooler_on=False, cooler_changed_at=0.0
    )
    decision = decide(
        config(heat_min_off=1800.0),
        Readings(room_temperature=10.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        just_stopped,
        now=1200.0,
    )
    assert decision.heaters_on is False


def test_the_state_records_when_the_valves_last_changed():
    decision = decide(
        config(),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(now=0.0),
        now=1000.0,
    )
    assert decision.state.heaters_on is True
    assert decision.state.heaters_changed_at == 1000.0


def test_state_is_carried_forward_when_nothing_changes():
    decision = decide(
        config(),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        heating_since(400.0),
        now=1000.0,
    )
    assert decision.state.heaters_changed_at == 400.0


def test_demand_waits_for_the_valve_to_travel():
    """A boiler that fires when the switch closes pushes into a shut circuit."""
    opening = decide(
        config(valve_travel=180.0),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        heating_since(1000.0),
        now=1090.0,
    )
    assert opening.heaters_on is True
    assert opening.heat_demand is False

    opened = decide(
        config(valve_travel=180.0),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        heating_since(1000.0),
        now=1200.0,
    )
    assert opened.heat_demand is True


def test_off_closes_the_valves():
    decision = decide(
        config(),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="off", target=21.0, target_low=None, target_high=None),
        heating_since(0.0),
        now=1000.0,
    )
    assert decision.heaters_on is False
    assert decision.heat_demand is False
    assert decision.hvac_action == "off"


def test_unused_import_guard():
    """CoolerCommand and Request are used by later tasks; keep the import honest."""
    assert CoolerCommand(hvac_mode="off", target=None).target is None
