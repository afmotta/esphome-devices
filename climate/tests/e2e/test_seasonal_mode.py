"""Behavioral tests for the demand tier of seasonal_mode.yaml.

Review 2026-11-10, finding 1. The shoulder-season demand tier used to read the
PIDs' actions and switch on the first check:

  - every zone PID is OFF in SANITARY_ONLY, so the tier could never leave it;
  - with one zone wanting heat and another wanting cool it flipped
    HEAT <-> COOL on every check (no confirmation, no dwell);
  - it moved hp_mode as soon as the manual hold was released, although hp_mode
    is meant to mirror what the heat pump produces.

The harness runs the real coordinator against two real radiant zones (see
harness/seasonal_mode.yaml), pinned to "always shoulder season", with the
timings compressed: one check every 100 ms, confirmation 5 checks, dwell 20.

    | Gates (hold / demand tier) | Demand            | Expected                 |
    |----------------------------|-------------------|--------------------------|
    | ON / any, OFF / OFF        | any               | hp_mode never moves      |
    | OFF / ON                   | heat only         | HEAT after confirmation  |
    | OFF / ON                   | cool only         | COOL after confirmation  |
    | OFF / ON                   | heat AND cool     | hp_mode never moves      |
    | OFF / ON                   | inside deadband   | hp_mode never moves      |
    | OFF / ON                   | shorter than conf.| hp_mode never moves      |
    | OFF / ON                   | right after change| waits out the dwell      |
"""

import asyncio
import time

import pytest

pytestmark = pytest.mark.asyncio

CHECK_S = 0.1  # harness: check_interval
CONFIRM_S = 5 * CHECK_S  # harness: demand_confirm_checks
DWELL_S = 20 * CHECK_S  # harness: demand_min_dwell_checks
# Long enough for the old code to have acted many times over.
QUIET_S = DWELL_S + 4 * CONFIRM_S

TARGET = 20.0  # pid.yaml default_target_temperature; pid_sensors deadband is 1.0
COLD = 17.0
HOT = 23.0
COMFORT = 20.0

HP_MODE = "heat_pump_mode"
REASON = "heat_pump_mode_reason"
CHANGES = "mode_change_count"


async def start(run_harness, mode: str, *, manual_hold: bool, demand_tier: bool):
    h = await run_harness("seasonal_mode")
    await h.call("set_temperatures", bath=COMFORT, bedroom=COMFORT)
    await h.call("set_gates", manual_hold=manual_hold, demand_tier=demand_tier)
    await h.call("set_hp_mode", value=mode)
    await h.wait_for(HP_MODE, lambda s: s.state == mode)
    return h


async def changes(h) -> int:
    """Number of hp_mode publishes so far (settled reading)."""
    await asyncio.sleep(0.2)  # counter sensor publishes every 50 ms
    return int(h.states[CHANGES].state)


async def assert_mode_holds(h, mode: str, seconds: float = QUIET_S):
    """hp_mode stays `mode` and is not even re-published for `seconds`."""
    before = await changes(h)
    await asyncio.sleep(seconds)
    assert h.states[HP_MODE].state == mode
    assert await changes(h) == before, "hp_mode was written during the wait"


async def past_dwell():
    await asyncio.sleep(DWELL_S + 2 * CHECK_S)


async def test_fresh_controller_never_moves_the_mode(run_harness):
    """Power-on defaults: manual hold ON, demand tier OFF."""
    h = await run_harness("seasonal_mode")
    await h.call("set_hp_mode", value="SANITARY_ONLY")
    await h.wait_for(HP_MODE, lambda s: s.state == "SANITARY_ONLY")
    await h.call("set_temperatures", bath=COLD, bedroom=COLD)
    await assert_mode_holds(h, "SANITARY_ONLY")


async def test_releasing_the_hold_alone_does_not_enable_the_demand_tier(run_harness):
    h = await start(run_harness, "SANITARY_ONLY", manual_hold=False, demand_tier=False)
    await h.call("set_temperatures", bath=COLD, bedroom=COLD)
    await assert_mode_holds(h, "SANITARY_ONLY")


async def test_manual_hold_wins_over_the_demand_tier(run_harness):
    h = await start(run_harness, "SANITARY_ONLY", manual_hold=True, demand_tier=True)
    await h.call("set_temperatures", bath=COLD, bedroom=COLD)
    await assert_mode_holds(h, "SANITARY_ONLY")


async def test_heat_demand_leaves_sanitary_only(run_harness):
    """The PIDs are OFF in SANITARY_ONLY; the tier used to be stuck here."""
    h = await start(run_harness, "SANITARY_ONLY", manual_hold=False, demand_tier=True)
    await past_dwell()
    await h.call("set_temperatures", bath=COLD, bedroom=COMFORT)
    await h.wait_for(HP_MODE, lambda s: s.state == "HEAT")
    await h.wait_for(REASON, lambda s: s.state == "DEMAND")


async def test_cool_demand_leaves_sanitary_only(run_harness):
    h = await start(run_harness, "SANITARY_ONLY", manual_hold=False, demand_tier=True)
    await past_dwell()
    await h.call("set_temperatures", bath=COMFORT, bedroom=HOT)
    await h.wait_for(HP_MODE, lambda s: s.state == "COOL")
    await h.wait_for(REASON, lambda s: s.state == "DEMAND")


async def test_heat_only_zone_too_warm_is_not_cool_demand(run_harness):
    """The bath cannot cool, so its overheating must not ask for chilled water."""
    h = await start(run_harness, "HEAT", manual_hold=False, demand_tier=True)
    await h.call("set_temperatures", bath=HOT, bedroom=COMFORT)
    await assert_mode_holds(h, "HEAT")


@pytest.mark.parametrize("mode", ["HEAT", "COOL", "SANITARY_ONLY"])
async def test_mixed_demand_never_flips(run_harness, mode):
    """One zone wants heat, another wants cool: used to flip on every check."""
    h = await start(run_harness, mode, manual_hold=False, demand_tier=True)
    await h.call("set_temperatures", bath=COLD, bedroom=HOT)
    await assert_mode_holds(h, mode)


async def test_error_inside_the_deadband_is_not_demand(run_harness):
    """An ordinary overshoot around the setpoint must not change the season."""
    h = await start(run_harness, "HEAT", manual_hold=False, demand_tier=True)
    await h.call("set_temperatures", bath=TARGET + 0.8, bedroom=TARGET + 0.8)
    await assert_mode_holds(h, "HEAT")
    await h.call("set_hp_mode", value="COOL")
    await h.wait_for(HP_MODE, lambda s: s.state == "COOL")
    await h.call("set_temperatures", bath=TARGET - 0.8, bedroom=TARGET - 0.8)
    await assert_mode_holds(h, "COOL")


async def test_short_demand_is_not_confirmed(run_harness):
    h = await start(run_harness, "HEAT", manual_hold=False, demand_tier=True)
    await past_dwell()
    before = await changes(h)
    for _ in range(4):
        await h.call("set_temperatures", bath=COMFORT, bedroom=HOT)
        await asyncio.sleep(CONFIRM_S / 2)
        await h.call("set_temperatures", bath=COMFORT, bedroom=COMFORT)
        await asyncio.sleep(2 * CHECK_S)
    assert h.states[HP_MODE].state == "HEAT"
    assert await changes(h) == before


async def test_demand_waits_out_the_dwell_after_a_mode_change(run_harness):
    """An operator (or calendar) change is not overruled right away."""
    h = await start(run_harness, "SANITARY_ONLY", manual_hold=False, demand_tier=True)
    await past_dwell()
    await h.call("set_temperatures", bath=COMFORT, bedroom=HOT)
    await h.call("set_hp_mode", value="HEAT")
    await h.wait_for(HP_MODE, lambda s: s.state == "HEAT")
    changed_at = time.monotonic()
    # Confirmed after 0.5 s, but held until the dwell is over.
    await asyncio.sleep(DWELL_S / 2)
    assert h.states[HP_MODE].state == "HEAT"
    await h.wait_for(HP_MODE, lambda s: s.state == "COOL")
    assert time.monotonic() - changed_at >= DWELL_S - 2 * CHECK_S

    # The tier's own change starts a new dwell: opposite demand cannot bounce it.
    switched_at = time.monotonic()
    await h.call("set_temperatures", bath=COLD, bedroom=COMFORT)
    await asyncio.sleep(DWELL_S / 2)
    assert h.states[HP_MODE].state == "COOL"
    await h.wait_for(HP_MODE, lambda s: s.state == "HEAT")
    assert time.monotonic() - switched_at >= DWELL_S - 2 * CHECK_S


async def test_demand_present_while_held_is_confirmed_from_scratch(run_harness):
    """Releasing the hold does not fire on a streak collected while held."""
    h = await start(run_harness, "HEAT", manual_hold=True, demand_tier=True)
    await h.call("set_temperatures", bath=COMFORT, bedroom=HOT)
    await past_dwell()
    await h.call("set_gates", manual_hold=False, demand_tier=True)
    released_at = time.monotonic()
    await h.wait_for(HP_MODE, lambda s: s.state == "COOL")
    assert time.monotonic() - released_at >= CONFIRM_S - 2 * CHECK_S
