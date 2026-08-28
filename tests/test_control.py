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
        warm_on=600.0,
        warm_off=3000.0,
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


def cooling_config(**overrides) -> RoomConfig:
    return config(has_cooler=True, has_heater=False, **overrides)


def test_passthrough_forwards_the_target_and_lets_the_unit_modulate():
    """An inverter unit regulates itself; we only tell it what to aim for."""
    decision = decide(
        cooling_config(cooling_strategy="passthrough"),
        Readings(room_temperature=26.0, room_humidity=None, cooler_temperature=24.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler == CoolerCommand(hvac_mode="cool", target=22.0)
    assert decision.hvac_action == "cooling"


def test_offset_correction_is_off_unless_asked_for():
    decision = decide(
        cooling_config(cooling_strategy="passthrough", offset_correction=False),
        Readings(room_temperature=26.0, room_humidity=None, cooler_temperature=24.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler.target == 22.0


def test_offset_correction_aims_at_the_room_not_the_unit():
    """The unit reads 2 degrees cool, so 22 in the room means asking for 20."""
    decision = decide(
        cooling_config(cooling_strategy="passthrough", offset_correction=True),
        Readings(room_temperature=26.0, room_humidity=None, cooler_temperature=24.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler.target == 20.0


def test_offset_correction_is_clamped_so_it_cannot_run_away():
    """A cabinet-mounted unit's offset grows without limit; the clamp is the
    backstop that keeps a misconfigured room merely wrong, not destructive."""
    decision = decide(
        cooling_config(cooling_strategy="passthrough", offset_correction=True),
        Readings(room_temperature=26.0, room_humidity=None, cooler_temperature=18.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler.target == 19.0


def test_gated_parks_the_unit_low_and_runs_it_against_the_room():
    decision = decide(
        cooling_config(cooling_strategy="gated", parked_setpoint=17.0),
        Readings(room_temperature=26.0, room_humidity=None, cooler_temperature=22.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler == CoolerCommand(hvac_mode="cool", target=17.0)
    assert decision.state.cooler_on is True


def test_gated_stops_the_unit_once_the_room_is_cool_enough():
    running = LoopState(
        heaters_on=False, heaters_changed_at=0.0, cooler_on=True, cooler_changed_at=0.0
    )
    decision = decide(
        cooling_config(cooling_strategy="gated"),
        Readings(room_temperature=21.4, room_humidity=None, cooler_temperature=20.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        running,
        now=5000.0,
    )
    assert decision.cooler == CoolerCommand(hvac_mode="off", target=None)
    assert decision.hvac_action == "idle"


def test_a_gated_unit_four_minutes_into_a_fifteen_minute_run_does_not_stop():
    """The whole point of the minimum: these units already cycle every five to
    ten minutes, which is what we are fixing, not reproducing."""
    running = LoopState(
        heaters_on=False, heaters_changed_at=0.0, cooler_on=True, cooler_changed_at=1000.0
    )
    decision = decide(
        cooling_config(cooling_strategy="gated", cool_min_on=900.0),
        Readings(room_temperature=20.0, room_humidity=None, cooler_temperature=18.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        running,
        now=1240.0,
    )
    assert decision.cooler.hvac_mode == "cool"


def test_a_gated_unit_respects_its_minimum_off_time():
    stopped = LoopState(
        heaters_on=False, heaters_changed_at=0.0, cooler_on=False, cooler_changed_at=1000.0
    )
    decision = decide(
        cooling_config(cooling_strategy="gated", cool_min_off=900.0),
        Readings(room_temperature=28.0, room_humidity=None, cooler_temperature=24.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        stopped,
        now=1240.0,
    )
    assert decision.cooler.hvac_mode == "off"


def test_dry_forwards_to_the_unit_and_leaves_the_valves_shut():
    decision = decide(
        config(has_cooler=True, has_heater=True),
        Readings(room_temperature=26.0, room_humidity=58.0, cooler_temperature=24.0),
        Request(hvac_mode="dry", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler == CoolerCommand(hvac_mode="dry", target=None)
    assert decision.heaters_on is False
    assert decision.hvac_action == "drying"


def test_fan_only_forwards_to_the_unit():
    decision = decide(
        config(has_cooler=True, has_heater=True),
        Readings(room_temperature=26.0, room_humidity=None, cooler_temperature=24.0),
        Request(hvac_mode="fan_only", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler == CoolerCommand(hvac_mode="fan_only", target=None)
    assert decision.hvac_action == "fan"


def test_heat_uses_the_valves_and_never_the_unit_by_default():
    decision = decide(
        config(has_cooler=True, has_heater=True, allow_ac_heat=False),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=20.0),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is True
    assert decision.cooler == CoolerCommand(hvac_mode="off", target=None)


def test_allowing_the_unit_to_heat_is_either_or_not_assist():
    """When a room heats with its air conditioner, the valves stay shut."""
    decision = decide(
        config(has_cooler=True, has_heater=True, allow_ac_heat=True),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=20.0),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is False
    assert decision.heat_demand is False
    assert decision.cooler == CoolerCommand(hvac_mode="heat", target=21.0)
    assert decision.hvac_action == "heating"


def test_auto_heats_below_the_low_setpoint():
    decision = decide(
        config(has_cooler=True, has_heater=True),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=20.0),
        Request(hvac_mode="heat_cool", target=None, target_low=20.0, target_high=25.0),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is True
    assert decision.cooler == CoolerCommand(hvac_mode="off", target=None)


def test_auto_cools_above_the_high_setpoint():
    decision = decide(
        config(has_cooler=True, has_heater=True),
        Readings(room_temperature=27.0, room_humidity=None, cooler_temperature=24.0),
        Request(hvac_mode="heat_cool", target=None, target_low=20.0, target_high=25.0),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is False
    assert decision.cooler.hvac_mode == "cool"


def test_auto_does_nothing_inside_the_dead_zone():
    """A room must not be able to fight itself."""
    decision = decide(
        config(has_cooler=True, has_heater=True),
        Readings(room_temperature=22.5, room_humidity=None, cooler_temperature=22.0),
        Request(hvac_mode="heat_cool", target=None, target_low=20.0, target_high=25.0),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is False
    assert decision.cooler == CoolerCommand(hvac_mode="off", target=None)
    assert decision.hvac_action == "idle"


def test_a_room_with_no_cooler_is_never_sent_a_cooler_command():
    decision = decide(
        config(has_cooler=False, has_heater=True),
        Readings(room_temperature=26.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.cooler is None


def test_a_freezing_room_is_heated_even_with_the_thermostat_off():
    """Safety outranks intent. An off thermostat must not freeze a pipe."""
    decision = decide(
        config(frost_temperature=5.0),
        Readings(room_temperature=4.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="off", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.frost_active is True
    assert decision.heaters_on is True
    assert decision.hvac_action == "heating"


def test_frost_protection_holds_until_the_room_recovers():
    """Releasing at exactly the threshold would chatter the valve."""
    frosting = LoopState(
        heaters_on=True, heaters_changed_at=0.0, cooler_on=False, cooler_changed_at=0.0
    )
    still_cold = decide(
        config(frost_temperature=5.0, frost_recovery=1.0),
        Readings(room_temperature=5.4, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="off", target=21.0, target_low=None, target_high=None),
        frosting,
        now=5000.0,
    )
    assert still_cold.frost_active is True

    recovered = decide(
        config(frost_temperature=5.0, frost_recovery=1.0),
        Readings(room_temperature=6.5, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="off", target=21.0, target_low=None, target_high=None),
        frosting,
        now=5000.0,
    )
    assert recovered.frost_active is False
    assert recovered.heaters_on is False


def test_frost_protection_raises_demand_like_any_other_call_for_heat():
    frosting = LoopState(
        heaters_on=True, heaters_changed_at=1000.0, cooler_on=False, cooler_changed_at=0.0
    )
    decision = decide(
        config(valve_travel=180.0),
        Readings(room_temperature=4.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="off", target=21.0, target_low=None, target_high=None),
        frosting,
        now=1200.0,
    )
    assert decision.heat_demand is True


def test_a_room_with_no_heater_cannot_be_frost_protected():
    decision = decide(
        config(has_heater=False, has_cooler=True),
        Readings(room_temperature=4.0, room_humidity=None, cooler_temperature=20.0),
        Request(hvac_mode="off", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.frost_active is False
    assert decision.heaters_on is False


def test_losing_the_sensor_stops_control_without_commanding_anything():
    """Never run a loop against a reading we no longer have."""
    running = LoopState(
        heaters_on=True, heaters_changed_at=0.0, cooler_on=False, cooler_changed_at=0.0
    )
    decision = decide(
        config(),
        Readings(room_temperature=None, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        running,
        now=5000.0,
    )
    assert decision.heaters_on is False
    assert decision.hvac_action == "idle"


def test_a_lost_sensor_is_reported_so_a_human_hears_about_it():
    decision = decide(
        config(),
        Readings(room_temperature=None, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.sensor_lost is True


def test_a_working_sensor_is_not_reported_as_lost():
    decision = decide(
        config(),
        Readings(room_temperature=20.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.sensor_lost is False


def test_a_lost_sensor_warms_the_room_through_periodically():
    """We cannot measure the room, so we cannot leave it cold all winter
    either. A duty cycle is the compromise: it cannot overheat a room quickly
    and it cannot let one freeze slowly."""
    off_long_enough = LoopState(
        heaters_on=False, heaters_changed_at=0.0, cooler_on=False, cooler_changed_at=0.0
    )
    decision = decide(
        config(warm_on=600.0, warm_off=3000.0),
        Readings(room_temperature=None, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        off_long_enough,
        now=3000.0,
    )
    assert decision.heaters_on is True


def test_the_warm_through_stops_after_its_run():
    on_long_enough = LoopState(
        heaters_on=True, heaters_changed_at=1000.0, cooler_on=False, cooler_changed_at=0.0
    )
    decision = decide(
        config(warm_on=600.0, warm_off=3000.0),
        Readings(room_temperature=None, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        on_long_enough,
        now=1700.0,
    )
    assert decision.heaters_on is False


def test_a_room_with_no_heater_has_nothing_to_warm_through():
    decision = decide(
        config(has_heater=False, has_cooler=True),
        Readings(room_temperature=None, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=5000.0,
    )
    assert decision.heaters_on is False
    assert decision.sensor_lost is True


def test_a_held_decision_says_when_to_come_back():
    """A minimum time that blocks a change has to schedule its own retry, or
    the change waits for whatever happens to wake the loop next."""
    just_stopped = LoopState(
        heaters_on=False, heaters_changed_at=1000.0, cooler_on=False, cooler_changed_at=0.0
    )
    decision = decide(
        config(heat_min_off=300.0),
        Readings(room_temperature=10.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        just_stopped,
        now=1100.0,
    )
    assert decision.heaters_on is False
    assert decision.retry_after == 200.0


def test_nothing_held_means_nothing_to_come_back_for():
    decision = decide(
        config(),
        Readings(room_temperature=18.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        idle(),
        now=1000.0,
    )
    assert decision.heaters_on is True
    assert decision.retry_after is None


def test_a_gated_cooler_held_open_also_says_when():
    running = LoopState(
        heaters_on=False, heaters_changed_at=0.0, cooler_on=True, cooler_changed_at=1000.0
    )
    decision = decide(
        cooling_config(cooling_strategy="gated", cool_min_on=900.0),
        Readings(room_temperature=20.0, room_humidity=None, cooler_temperature=18.0),
        Request(hvac_mode="cool", target=22.0, target_low=None, target_high=None),
        running,
        now=1240.0,
    )
    assert decision.cooler.hvac_mode == "cool"
    assert decision.retry_after == 660.0


def test_the_soonest_hold_is_the_one_to_come_back_for():
    """With both sides held, waking at the later one would leave the earlier
    change waiting past its own release."""
    both = LoopState(
        heaters_on=False, heaters_changed_at=1000.0, cooler_on=True, cooler_changed_at=1000.0
    )
    decision = decide(
        config(has_cooler=True, has_heater=True, heat_min_off=100.0, cool_min_on=500.0),
        Readings(room_temperature=10.0, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="heat", target=21.0, target_low=None, target_high=None),
        both,
        now=1050.0,
    )
    assert decision.retry_after == 50.0


def test_a_room_switched_off_is_still_warmed_through_when_blind():
    """Frost protection overrides off when the room can be measured. The blind
    duty cycle is what stands in for it when the room cannot be, so excluding
    off leaves exactly the case the fallback exists for uncovered."""
    off_long_enough = LoopState(
        heaters_on=False, heaters_changed_at=0.0, cooler_on=False, cooler_changed_at=0.0
    )
    decision = decide(
        config(warm_on=600.0, warm_off=3000.0),
        Readings(room_temperature=None, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="off", target=21.0, target_low=None, target_high=None),
        off_long_enough,
        now=3000.0,
    )
    assert decision.sensor_lost is True
    assert decision.heaters_on is True


def test_the_blind_cycle_still_rests_when_the_room_is_off():
    on_long_enough = LoopState(
        heaters_on=True, heaters_changed_at=1000.0, cooler_on=False, cooler_changed_at=0.0
    )
    decision = decide(
        config(warm_on=600.0, warm_off=3000.0),
        Readings(room_temperature=None, room_humidity=None, cooler_temperature=None),
        Request(hvac_mode="off", target=21.0, target_low=None, target_high=None),
        on_long_enough,
        now=1700.0,
    )
    assert decision.heaters_on is False
