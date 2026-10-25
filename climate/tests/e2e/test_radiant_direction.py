"""Behavioral tests for PID heat/cool direction gating (review item R-01).

ESPHome's PID routes a positive value to heat_output and a negative one to
cool_output (as -value) without looking at its HEAT/COOL mode, and in this house
both outputs end at the same actuator. Ungated, an actuator therefore followed
|error|: a room above target in winter opened its valve, the mixing valve opened
MORE when the supply was below the dew-point minimum, and fancoils ran when the
room was too warm in winter and never heated.

The fix gates each direction on the water the heat pump produces (hp_mode):
heat only while HEAT, cool only while COOL (climate/protocol/pid_direction.h).
These tests drive the real actuator packages through the host harness
(harness/radiant_direction.yaml) and check no actuator moves in the wrong
direction:

  heat_only_radiant  bath      heats in HEAT only
  radiant            bedroom   heats in HEAT, cools in COOL
  fancoil boost      living    never started by the season, only by the boost
                               coordinator (stubbed by boost_start/boost_stop)
  fancoil cool_only  techroom  cools in COOL only
  fancoil heat_cool  attic     heats in HEAT, cools in COOL
  mixing_pump        mix       supply-temperature valve: opens toward the
                               direction the heat pump produces

All room PIDs share one temperature stub and the default 20.0 degC target:
25.0 => 5 degC over target, 15.0 => 5 degC under. Every PID output saturates, so
"actuates" means level 1.0 / relay held on.
"""

import asyncio
import math

import pytest
from aioesphomeapi import ClimateMode

pytestmark = pytest.mark.asyncio

HP_MODE = "heat_pump_mode"
# Slow PWM period is 1 s in the harness: waiting longer than that proves a
# relay that "never turned on" really never did.
RELAY_SETTLE = 1.6
LEVEL_SETTLE = 0.5

HOT = 25.0  # 5 degC over the 20 degC target
COLD = 15.0  # 5 degC under it


async def set_season(h, mode: str):
    """Pick the heat pump mode and wait for the seasonal handlers to apply."""
    await h.call("set_hp_mode", value=mode)
    await h.wait_for(HP_MODE, lambda s: s.state == mode)


async def read_room(h, temperature: float):
    """Publish a room temperature (every PID recomputes and writes its outputs)."""
    await h.call("set_temperature", value=temperature)


def relay_count(h, name: str) -> int:
    state = h.states.get(f"{name}_relay_on_count")
    assert state is not None, f"{name}_relay_on_count never published"
    return int(state.state)


def relay_on(h, name: str) -> bool:
    state = h.states.get(f"{name}_relay")
    return state is not None and state.state is True


def level(h, object_id: str) -> float:
    state = h.states.get(object_id)
    assert state is not None, f"{object_id} was never written"
    assert not math.isnan(state.state)
    return state.state


async def assert_level(h, object_id: str, expected: float):
    """Level settles on `expected`: wait for it, or (for 0) check it holds.

    A PID update writes zero first and the effective level last, so for 0 the
    LAST value after the settle time is what matters, not the first sample.
    """
    if expected == 0.0:
        await asyncio.sleep(LEVEL_SETTLE)
        assert level(h, object_id) == pytest.approx(0.0), f"{object_id} actuated"
    else:
        await h.wait_for_value(object_id, expected)


# (hp_mode, room temperature) -> which actuators may move.
#   bath/bedroom: radiant relay held on?   living/techroom/attic: fan level.
ROOM_MATRIX = [
    # Winter, room too warm: the bug opened every radiant valve here.
    ("HEAT", HOT, dict(bath=False, bedroom=False, living=0.0, techroom=0.0, attic=0.0)),
    # Winter, room too cold: radiant and the heat_cool fancoil heat; the
    # cooling-only fancoils (boost, cool_only) stay off.
    ("HEAT", COLD, dict(bath=True, bedroom=True, living=0.0, techroom=0.0, attic=1.0)),
    # Summer, room too warm: radiant cools (heat-only bath is off), cooling
    # fancoils run — except the boost one, which only the coordinator starts.
    ("COOL", HOT, dict(bath=False, bedroom=True, living=0.0, techroom=1.0, attic=1.0)),
    # Summer, room too cold: nothing may heat.
    ("COOL", COLD, dict(bath=False, bedroom=False, living=0.0, techroom=0.0, attic=0.0)),
    # No heating/cooling water: nothing moves at all.
    ("SANITARY_ONLY", HOT, dict(bath=False, bedroom=False, living=0.0, techroom=0.0, attic=0.0)),
    ("SANITARY_ONLY", COLD, dict(bath=False, bedroom=False, living=0.0, techroom=0.0, attic=0.0)),
]


@pytest.mark.parametrize("hp_mode,temperature,expected", ROOM_MATRIX)
async def test_room_actuators_follow_the_water_direction(run_harness, hp_mode, temperature, expected):
    h = await run_harness("radiant_direction")
    await set_season(h, hp_mode)
    await read_room(h, temperature)

    for room in ("bath", "bedroom"):
        if expected[room]:
            await h.wait_for(f"{room}_relay", lambda s: s.state is True)
        else:
            await asyncio.sleep(RELAY_SETTLE)
            assert relay_count(h, room) == 0, f"{room} relay turned on in {hp_mode} at {temperature}"
            assert not relay_on(h, room)

    for fan in ("living", "techroom", "attic"):
        await assert_level(h, f"{fan}_fan_level", expected[fan])


async def test_season_flip_closes_a_stale_radiant_valve_on_next_update(run_harness):
    """Winter heating, then the heat pump flips to chilled water.

    A season flip is not itself a write: the relay keeps its last state until
    the next PID update (sensor-driven, seconds). That update must close it,
    because a too-cold room must not heat from chilled-water supply.
    """
    h = await run_harness("radiant_direction")
    await set_season(h, "HEAT")
    await read_room(h, COLD)
    await h.wait_for("bedroom_relay", lambda s: s.state is True)

    await set_season(h, "COOL")
    await read_room(h, COLD)  # same reading: the PID recomputes on every update
    await h.wait_for("bedroom_relay", lambda s: s.state is False)


# Seasonal handler results per fancoil role / radiant type.
MODE_MATRIX = [
    ("HEAT", dict(bath=ClimateMode.HEAT, bedroom=ClimateMode.HEAT, living=ClimateMode.OFF,
                  techroom=ClimateMode.OFF, attic=ClimateMode.HEAT)),
    ("COOL", dict(bath=ClimateMode.OFF, bedroom=ClimateMode.COOL, living=ClimateMode.OFF,
                  techroom=ClimateMode.COOL, attic=ClimateMode.COOL)),
    ("SANITARY_ONLY", dict(bath=ClimateMode.OFF, bedroom=ClimateMode.OFF, living=ClimateMode.OFF,
                           techroom=ClimateMode.OFF, attic=ClimateMode.OFF)),
]


@pytest.mark.parametrize("hp_mode,expected", MODE_MATRIX)
async def test_seasonal_handlers_set_pid_modes_per_role(run_harness, hp_mode, expected):
    h = await run_harness("radiant_direction")
    # Walk through another season first so the handlers must actually change
    # the mode (not just keep a boot default).
    await set_season(h, "COOL" if hp_mode != "COOL" else "HEAT")
    await set_season(h, hp_mode)

    for room, mode in expected.items():
        pid = "_radiant_pid" if room in ("bath", "bedroom") else "_fancoil_pid"
        await h.wait_for(f"{room}{pid}", lambda s, mode=mode: s.mode == mode)


# --- boost-role fancoil -----------------------------------------------------

async def test_boost_fancoil_is_not_started_by_the_season(run_harness):
    """Switching hp_mode to COOL must NOT start a boost-role fancoil.

    Before the fix the seasonal handler set every fancoil PID to COOL on COOL,
    bypassing the coordinator and its {zone}_boost_enabled commissioning gate.
    """
    h = await run_harness("radiant_direction")
    await set_season(h, "HEAT")
    await set_season(h, "COOL")
    await h.wait_for("living_fancoil_pid", lambda s: s.mode == ClimateMode.OFF)

    await read_room(h, HOT)  # too warm for the room, but the boost is not running
    await assert_level(h, "living_fan_level", 0.0)
    assert h.states["living_fancoil_pid"].mode == ClimateMode.OFF


async def test_boost_fancoil_runs_only_under_the_coordinator(run_harness):
    h = await run_harness("radiant_direction")
    await set_season(h, "COOL")
    await h.wait_for("living_fancoil_pid", lambda s: s.mode == ClimateMode.OFF)

    await h.call("boost_start")  # what the coordinator's set_action does
    await h.wait_for("living_fancoil_pid", lambda s: s.mode == ClimateMode.COOL)
    await read_room(h, HOT)
    await h.wait_for_value("living_fan_level", 1.0)

    # hp_mode re-published as COOL (e.g. an HA refresh) must not cut a running
    # boost short: the coordinator would not restart it.
    await set_season(h, "COOL")
    await asyncio.sleep(LEVEL_SETTLE)
    assert h.states["living_fancoil_pid"].mode == ClimateMode.COOL
    await read_room(h, HOT)
    await h.wait_for_value("living_fan_level", 1.0)

    # End of cooling season: the fancoil is forced off (the coordinator's own
    # season override ends the boost; the handler is the backstop).
    await set_season(h, "HEAT")
    await h.wait_for("living_fancoil_pid", lambda s: s.mode == ClimateMode.OFF)
    await read_room(h, HOT)
    await assert_level(h, "living_fan_level", 0.0)


async def test_boost_fancoil_never_heats_a_cold_room(run_harness):
    """Winter, boost running by mistake, room too cold: no heating output exists."""
    h = await run_harness("radiant_direction")
    await set_season(h, "HEAT")
    await h.call("boost_start")
    await h.wait_for("living_fancoil_pid", lambda s: s.mode == ClimateMode.COOL)
    await read_room(h, COLD)
    await assert_level(h, "living_fan_level", 0.0)


# --- mixing valve -----------------------------------------------------------

# Valve PID target is the default 20 degC; supply 30 is 10 degC above it.
# (hp_mode, supply temperature) -> valve level.
VALVE_MATRIX = [
    # Heating: supply too cold => open the (hot) valve; too hot => close.
    ("HEAT", 10.0, 1.0),
    ("HEAT", 30.0, 0.0),
    # Cooling: supply warmer than the dew-point minimum target => open the
    # chilled valve; supply BELOW the minimum => close it. The bug inverted
    # this second case (dew-point protection opened the valve more).
    ("COOL", 30.0, 1.0),
    ("COOL", 10.0, 0.0),
    ("SANITARY_ONLY", 10.0, 0.0),
    ("SANITARY_ONLY", 30.0, 0.0),
]


@pytest.mark.parametrize("hp_mode,supply,expected", VALVE_MATRIX)
async def test_mixing_valve_follows_the_water_direction(run_harness, hp_mode, supply, expected):
    h = await run_harness("radiant_direction")
    await set_season(h, hp_mode)
    await h.call("set_supply_temperature", value=supply)
    await assert_level(h, "valve_level", expected)


async def test_mixing_valve_closes_when_supply_drops_below_dew_point_minimum(run_harness):
    """Cooling in progress, then the supply gets colder than the minimum."""
    h = await run_harness("radiant_direction")
    await set_season(h, "COOL")
    await h.call("set_supply_temperature", value=30.0)
    await h.wait_for_value("valve_level", 1.0)

    await h.call("set_supply_temperature", value=10.0)
    await h.wait_for_value("valve_level", 0.0)
    await asyncio.sleep(LEVEL_SETTLE)
    assert level(h, "valve_level") == pytest.approx(0.0)
