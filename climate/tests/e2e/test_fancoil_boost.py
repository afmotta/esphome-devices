"""Behavioral tests for packages/coordinators/fancoil_boost.yaml.

Covers the documented state machine contract:

  Activation (OR logic, each trigger starts the anti-cycling timer):
    1. Reactive temp:     delta > threshold
    2. Reactive humidity: humidity > threshold + hysteresis/2
    3. Predictive:        radiant saturated AND above target AND not cooling down
  Predictive delay input (R-08): a NaN / non-positive minutes value never arms
                 the trigger; a huge one is clamped (harness clamp: 6 s)
  Anti-cycling:  the timer cancels if the condition clears before it elapses
  Deactivation (AND logic): delta <= 0 AND humidity <= threshold - hysteresis/2
  Season override: leaving cooling season ends boost immediately (no delay)
  Sensor loss (R-05): a NaN room temperature ends boost immediately, and no
                 boost starts while it is NaN, whatever the trigger

The harness compresses min_time_in_state to 2 s (prod: 600 s). The radiant
PID target is 24.0 C, so absolute temps map to deltas: 26.0 => +2.0.
With humidity threshold 60 and hysteresis 5, boost activates above 62.5
and may deactivate at or below 57.5.
"""

import asyncio

import pytest
from aioesphomeapi import ClimateMode

NAN = float("nan")

# Object ids exposed by the harness (zone_slug "test_zone", zone_name "Test Zone").
STATE = "test_zone_boost_state"
AUTOMATION = "test_zone_boost_automation_state"
OVERRIDE_SWITCH = "radiant_override"
OVERRIDE_VALUE = "radiant_override_value"
FANCOIL = "fancoil_pid"

pytestmark = pytest.mark.asyncio


async def setup_zone(h, *, cooling: bool):
    """Baseline: comfortable zone, sane thresholds, predictive disarmed."""
    await h.call("set_temp_threshold", value=1.0)
    await h.call("set_humidity_threshold", value=60.0)
    await h.call("set_predictive_minutes", value=999.0)
    await h.call("set_humidity", value=50.0)
    await h.call("set_temperature", value=24.0)
    await h.call("set_cooling_mode", value=cooling)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Idle")


async def reach_boost(h):
    """Drive the zone into Fancoil Boost via the reactive temp trigger."""
    await h.call("set_temperature", value=26.0)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Activating (reactive)")
    await h.wait_for(STATE, lambda s: s.state == "Fancoil Boost", timeout=5)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Boost Active")


async def test_reactive_temp_activation_locks_radiant_and_enables_fancoil(run_harness):
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=False)

    # Hot room, but heating season: must NOT trigger.
    await h.call("set_temperature", value=26.0)
    await asyncio.sleep(0.5)
    assert h.states[AUTOMATION].state == "Idle"
    assert h.states[STATE].state == "Radiant Only"

    # Cooling season starts: trigger fires, anti-cycling timer runs, boost engages.
    await h.call("set_cooling_mode", value=True)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Activating (reactive)")
    await h.wait_for(STATE, lambda s: s.state == "Fancoil Boost", timeout=5)

    # Hardware side effects of the transition:
    await h.wait_for(OVERRIDE_SWITCH, lambda s: s.state is True)
    await h.wait_for_value(OVERRIDE_VALUE, 100.0)
    await h.wait_for(FANCOIL, lambda s: s.mode == ClimateMode.COOL)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Boost Active")


async def test_anti_cycling_timer_cancels_when_condition_clears(run_harness):
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)

    await h.call("set_temperature", value=26.0)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Activating (reactive)")

    # Condition clears before the 2 s anti-cycling delay elapses.
    await h.call("set_temperature", value=23.0)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Idle")

    # Even after the would-be delay, the transition must NOT have happened.
    await asyncio.sleep(2.5)
    assert h.states[STATE].state == "Radiant Only"
    assert h.states[FANCOIL].mode == ClimateMode.OFF
    assert h.states[OVERRIDE_SWITCH].state is False


async def test_reactive_humidity_activation(run_harness):
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)

    # Temp at target; humidity above threshold + hysteresis/2 (62.5).
    await h.call("set_humidity", value=64.0)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Activating (reactive)")
    await h.wait_for(STATE, lambda s: s.state == "Fancoil Boost", timeout=5)


async def test_predictive_activation_on_sustained_saturation(run_harness):
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)

    # Reactive temp trigger out of reach; predictive delay 0.05 min = 3 s.
    await h.call("set_temp_threshold", value=5.0)
    await h.call("set_predictive_minutes", value=0.05)

    # Above target (delta +2 < threshold 5) with the radiant PID saturated.
    await h.call("set_temperature", value=26.0)
    await h.call("set_radiant_cool_output", value=0.96)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Activating (predictive)")
    await h.wait_for(STATE, lambda s: s.state == "Fancoil Boost", timeout=6)


async def test_deactivation_requires_temp_and_humidity(run_harness):
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)
    await reach_boost(h)

    # Temp back at target, but humidity above the lower band (57.5):
    # AND logic must keep boost active.
    await h.call("set_humidity", value=70.0)
    await h.call("set_temperature", value=23.0)
    await asyncio.sleep(1.0)
    assert h.states[STATE].state == "Fancoil Boost"
    assert h.states[AUTOMATION].state == "Boost Active"

    # Humidity drops below the band: both conditions met, deactivation runs.
    await h.call("set_humidity", value=50.0)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Deactivating")
    await h.wait_for(STATE, lambda s: s.state == "Radiant Only", timeout=5)

    # Hardware released: override off, fancoil off, automation idle.
    await h.wait_for(OVERRIDE_SWITCH, lambda s: s.state is False)
    await h.wait_for(FANCOIL, lambda s: s.mode == ClimateMode.OFF)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Idle")


async def test_season_change_ends_boost_immediately(run_harness):
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)
    await reach_boost(h)

    # Cooling season ends: safety override bypasses the anti-cycling delay.
    await h.call("set_cooling_mode", value=False)
    await h.wait_for(STATE, lambda s: s.state == "Radiant Only", timeout=1.5)
    await h.wait_for(OVERRIDE_SWITCH, lambda s: s.state is False)
    await h.wait_for(FANCOIL, lambda s: s.mode == ClimateMode.OFF)


async def test_commissioning_gate_suppresses_activation(run_harness):
    """Gate off: a zone that would otherwise boost stays radiant-only.

    The gate defaults OFF in production so a freshly flashed controller runs
    radiant-only until the zone is explicitly cleared for hybrid operation.
    """
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)
    await h.call("set_boost_enabled", value=False)

    # Same stimulus reach_boost() uses; must not even start the timer.
    await h.call("set_temperature", value=26.0)
    await asyncio.sleep(3)  # > min_time_in_state (2 s): a timer would have fired
    assert h.states[STATE].state == "Radiant Only"
    assert h.states[AUTOMATION].state == "Idle"
    assert h.states[OVERRIDE_SWITCH].state is False


async def test_disabling_gate_during_boost_drops_to_radiant(run_harness):
    """Gate switched off mid-boost releases the hardware immediately."""
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)
    await reach_boost(h)

    # Same override path as the end-of-season safety: no anti-cycling delay.
    await h.call("set_boost_enabled", value=False)
    await h.wait_for(STATE, lambda s: s.state == "Radiant Only", timeout=1.5)
    await h.wait_for(OVERRIDE_SWITCH, lambda s: s.state is False)
    await h.wait_for(FANCOIL, lambda s: s.mode == ClimateMode.OFF)


async def test_sensor_loss_ends_boost_immediately(run_harness):
    """Room temperature NaN mid-boost: radiant only at once, no anti-cycling delay.

    should_end_boost cannot end it (a NaN delta never reaches "target"), which used
    to leave the zone at 100 % radiant cooling plus fancoil COOL indefinitely.
    """
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)
    await reach_boost(h)
    await h.wait_for(OVERRIDE_SWITCH, lambda s: s.state is True)

    await h.call("set_temperature", value=NAN)
    # Well under the 2 s anti-cycling delay: the same immediate path as the
    # season / gate override.
    await h.wait_for(STATE, lambda s: s.state == "Radiant Only", timeout=1.0)
    await h.wait_for(OVERRIDE_SWITCH, lambda s: s.state is False, timeout=1.0)
    await h.wait_for(FANCOIL, lambda s: s.mode == ClimateMode.OFF, timeout=1.0)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Idle", timeout=1.0)

    # And it stays down: neither the delay timers nor the triggers revive it.
    await asyncio.sleep(3)
    assert h.states[STATE].state == "Radiant Only"
    assert h.states[OVERRIDE_SWITCH].state is False
    assert h.states[FANCOIL].mode == ClimateMode.OFF

    # The sensor returns and the room is still hot: boost may be earned again,
    # but only through the normal anti-cycling delay.
    await h.call("set_temperature", value=26.0)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Activating (reactive)")
    assert h.states[STATE].state == "Radiant Only"
    await h.wait_for(STATE, lambda s: s.state == "Fancoil Boost", timeout=5)


async def test_no_boost_starts_while_the_temperature_is_lost(run_harness):
    """Every trigger is blocked for a NaN temperature, humidity included.

    Otherwise a humidity-triggered boost would start and be cancelled again by
    the sensor-loss stop after each anti-cycling delay.
    """
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)
    await h.call("set_temperature", value=NAN)

    # Humidity trigger (above 62.5) with the temperature unknown.
    await h.call("set_humidity", value=70.0)
    await asyncio.sleep(3)  # > min_time_in_state (2 s): a timer would have fired
    assert h.states[STATE].state == "Radiant Only"
    assert h.states[AUTOMATION].state == "Idle"
    assert h.states[OVERRIDE_SWITCH].state is False

    # Predictive trigger: saturated radiant output, delay compressed to 3 s.
    await h.call("set_humidity", value=50.0)
    await h.call("set_predictive_minutes", value=0.05)
    await h.call("set_radiant_cool_output", value=0.96)
    await asyncio.sleep(4)
    assert h.states[STATE].state == "Radiant Only"
    assert h.states[AUTOMATION].state == "Idle"


async def _saturate(h):
    """Predictive stimulus: reactive trigger out of reach, radiant saturated, room above target."""
    await h.call("set_temp_threshold", value=5.0)
    await h.call("set_temperature", value=26.0)
    await h.call("set_radiant_cool_output", value=0.96)


@pytest.mark.parametrize("minutes", [NAN, 0.0, -5.0, float("inf")])
async def test_predictive_not_armed_for_an_invalid_delay(run_harness, minutes):
    """NaN / zero / negative / infinite minutes used to become an undefined uint32 delay.

    The trigger must refuse to arm (no "Activating (predictive)", no boost) and
    must arm again once the value is sane and the trigger is re-asserted.
    """
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)
    await h.call("set_predictive_minutes", value=minutes)
    await _saturate(h)

    # Past the harness clamp (6 s) and the anti-cycling delay: any armed
    # delay, however it was computed, would have fired by now.
    await asyncio.sleep(8)
    assert h.states[STATE].state == "Radiant Only"
    assert h.states[AUTOMATION].state == "Idle"
    assert h.states[OVERRIDE_SWITCH].state is False

    # Recovery: valid minutes, trigger released and asserted again (on_press).
    await h.call("set_predictive_minutes", value=0.05)
    await h.call("set_radiant_cool_output", value=0.0)
    await asyncio.sleep(0.3)
    await h.call("set_radiant_cool_output", value=0.96)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Activating (predictive)")
    await h.wait_for(STATE, lambda s: s.state == "Fancoil Boost", timeout=6)


async def test_predictive_delay_is_clamped(run_harness):
    """999 minutes would be ~16 h; the (compressed) clamp caps it at 6 s."""
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)  # leaves predictive minutes at 999
    await _saturate(h)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Activating (predictive)")
    await asyncio.sleep(3)
    assert h.states[STATE].state == "Radiant Only"  # still waiting, not yet clamped out
    await h.wait_for(STATE, lambda s: s.state == "Fancoil Boost", timeout=8)
