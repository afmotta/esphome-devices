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

The `<pid>_is_active` binary sensors drive the circulation-pump demand, so they
must agree with the valves: true only while the PID's action matches the water
produced (pid_direction::actuating), while `_is_cooling`/`_is_heating` keep
reporting the PID's intent for the seasonal demand tier.

The radiant override (review R-05) is the other thing that opens a valve: the
fancoil_boost coordinator holds it at 100 % through the override switch, HA can
do the same by hand. The final stage must follow the override, close the valve
while the room temperature is NaN (the override used to win over the PID's own
"sensor lost => 0"), and `<room>_radiant_override_active` must tell the floor
pump-demand sums that a valve is held open without any PID action.

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


# --- pump demand (the `_is_active` sensors) ----------------------------------

def active(h, object_id: str) -> bool:
    state = h.states.get(object_id)
    assert state is not None, f"{object_id} was never published"
    return state.state is True


async def assert_active(h, object_id: str, expected: bool):
    """`_is_active` settles on `expected`.

    The template sensor re-evaluates every loop and only publishes changes, so
    a flip is awaited; "stays false" is checked after the PID had time to update.
    """
    if expected:
        await h.wait_for(object_id, lambda s: s.state is True)
    else:
        await asyncio.sleep(LEVEL_SETTLE)
        assert not active(h, object_id), f"{object_id} demands the pump with no water direction to match"


# (hp_mode, room temperature) -> expected `_is_active` per room. A PID that is
# not moving its valve in the water direction must not ask for the pump:
# the circulation pump would run against closed valves.
ACTIVE_MATRIX = [
    # Winter, room too warm: the PID's action is COOLING but every valve is
    # gated shut -> no pump demand (the bug: is_active was the raw action).
    ("HEAT", HOT, dict(bath=False, bedroom=False, living=False, techroom=False, attic=False)),
    # Winter, room too cold: heating zones demand the pump; cooling-only
    # fancoils (boost, cool_only) have no heat output and stay idle.
    ("HEAT", COLD, dict(bath=True, bedroom=True, living=False, techroom=False, attic=True)),
    # Summer, room too warm: cooling zones demand the pump; the heat-only bath
    # is off and the boost fancoil waits for the coordinator.
    ("COOL", HOT, dict(bath=False, bedroom=True, living=False, techroom=True, attic=True)),
    # Summer, room too cold: only a (gated) heating action, no pump.
    ("COOL", COLD, dict(bath=False, bedroom=False, living=False, techroom=False, attic=False)),
    # No heating/cooling water: nothing may ask for the pump.
    ("SANITARY_ONLY", HOT, dict(bath=False, bedroom=False, living=False, techroom=False, attic=False)),
    ("SANITARY_ONLY", COLD, dict(bath=False, bedroom=False, living=False, techroom=False, attic=False)),
]

ACTIVE_IDS = dict(
    bath="bath_radiant_pid_is_active",
    bedroom="bedroom_radiant_pid_is_active",
    living="living_fancoil_pid_is_active",
    techroom="techroom_fancoil_pid_is_active",
    attic="attic_fancoil_pid_is_active",
)


@pytest.mark.parametrize("hp_mode,temperature,expected", ACTIVE_MATRIX)
async def test_pump_demand_follows_the_water_direction(run_harness, hp_mode, temperature, expected):
    h = await run_harness("radiant_direction")
    await set_season(h, hp_mode)
    await read_room(h, temperature)
    # Same wait as the actuator matrix so the PIDs have computed their action.
    await asyncio.sleep(RELAY_SETTLE)

    for room, want in expected.items():
        await assert_active(h, ACTIVE_IDS[room], want)


async def test_pump_demand_keeps_the_intent_sensors_ungated(run_harness):
    """Winter, room too warm: is_active is false but is_cooling still says COOLING.

    The seasonal demand tier reads is_heating/is_cooling as the PID's intent
    (a room wanting cooling in HEAT season is a signal, not a command).
    """
    h = await run_harness("radiant_direction")
    await set_season(h, "HEAT")
    await read_room(h, HOT)
    await h.wait_for("bedroom_radiant_pid_is_cooling", lambda s: s.state is True)
    assert not active(h, "bedroom_radiant_pid_is_active")
    assert not h.states["bedroom_radiant_pid_is_heating"].state

    await read_room(h, COLD)
    await h.wait_for("bedroom_radiant_pid_is_heating", lambda s: s.state is True)
    await assert_active(h, "bedroom_radiant_pid_is_active", True)


async def test_pump_demand_drops_when_the_season_flips(run_harness):
    """Heating in progress, then the heat pump flips to chilled water.

    The sensor re-evaluates on the season change itself (it reads hp_mode), so
    the pump demand ends at once instead of waiting for the next PID update.
    """
    h = await run_harness("radiant_direction")
    await set_season(h, "HEAT")
    await read_room(h, COLD)
    await assert_active(h, "bedroom_radiant_pid_is_active", True)

    await set_season(h, "SANITARY_ONLY")
    await h.wait_for("bedroom_radiant_pid_is_active", lambda s: s.state is False)


# Mixing-valve PID (target 20 degC): supply 10 is under it (heating action),
# supply 30 over it (cooling action).
@pytest.mark.parametrize("hp_mode,supply,expected", [
    ("HEAT", 10.0, True),
    ("HEAT", 30.0, False),
    ("COOL", 30.0, True),
    ("COOL", 10.0, False),
    ("SANITARY_ONLY", 10.0, False),
    ("SANITARY_ONLY", 30.0, False),
])
async def test_mixing_valve_pump_demand_follows_the_water_direction(run_harness, hp_mode, supply, expected):
    h = await run_harness("radiant_direction")
    await set_season(h, hp_mode)
    await h.call("set_supply_temperature", value=supply)
    await asyncio.sleep(RELAY_SETTLE)
    await assert_active(h, "mix_mixing_valve_pid_is_active", expected)


# --- radiant override: valve hold, sensor loss, pump demand (R-05) -----------

AT_TARGET = 20.0  # the PID's default target: no PID action at all
NAN = float("nan")


async def assert_relay_stays_off(h, room: str):
    await asyncio.sleep(RELAY_SETTLE)
    assert not relay_on(h, room), f"{room} relay is on"


async def test_override_holds_the_valve_open_without_pid_action(run_harness):
    """Boost-style hold: room at target, no water season, override 100 %.

    Nothing but the override asks for the valve, so this is the case where pump
    demand has no PID action to follow.
    """
    h = await run_harness("radiant_direction")
    await set_season(h, "SANITARY_ONLY")
    await read_room(h, AT_TARGET)
    await assert_relay_stays_off(h, "bath")
    await assert_active(h, "bath_radiant_pid_is_active", False)
    await assert_active(h, "bath_radiant_override_active", False)
    await assert_active(h, "floor_demand", False)

    await h.call("set_bath_override", enabled=True, value=100.0)
    await h.wait_for("bath_relay", lambda s: s.state is True)
    await h.wait_for("bath_radiant_override_active", lambda s: s.state is True)
    # PID idle, override holding: the floor pump must still run.
    assert not active(h, "bath_radiant_pid_is_active")
    await h.wait_for("floor_demand", lambda s: s.state is True)

    # The other zone is untouched.
    assert not relay_on(h, "bedroom")
    assert not active(h, "bedroom_radiant_override_active")

    await h.call("set_bath_override", enabled=False, value=100.0)
    await h.wait_for("bath_relay", lambda s: s.state is False)
    await h.wait_for("bath_radiant_override_active", lambda s: s.state is False)
    await h.wait_for("floor_demand", lambda s: s.state is False)


async def test_override_at_zero_percent_holds_nothing(run_harness):
    """Switch on with value 0 commands the valve shut: no hold, no demand."""
    h = await run_harness("radiant_direction")
    await set_season(h, "SANITARY_ONLY")
    await read_room(h, AT_TARGET)
    await h.call("set_bath_override", enabled=True, value=0.0)
    await assert_relay_stays_off(h, "bath")
    await assert_active(h, "bath_radiant_override_active", False)
    await assert_active(h, "floor_demand", False)


async def test_override_hold_applies_to_heat_cool_zones_too(run_harness):
    """radiant.yaml includes heat_only_radiant.yaml: the bedroom behaves alike."""
    h = await run_harness("radiant_direction")
    await set_season(h, "SANITARY_ONLY")
    await read_room(h, AT_TARGET)
    await h.call("set_bedroom_override", enabled=True, value=100.0)
    await h.wait_for("bedroom_relay", lambda s: s.state is True)
    await h.wait_for("bedroom_radiant_override_active", lambda s: s.state is True)
    await h.wait_for("floor_demand", lambda s: s.state is True)


async def test_override_does_not_survive_sensor_loss(run_harness):
    """Room temperature NaN with the override on: valve closed, no pump demand.

    The PID writes 0 for a NaN sensor, but the override used to win over it. The
    switch itself stays on, so the hold resumes when the sensor comes back.
    """
    h = await run_harness("radiant_direction")
    await set_season(h, "COOL")
    await read_room(h, AT_TARGET)
    await h.call("set_bath_override", enabled=True, value=100.0)
    await h.call("set_bedroom_override", enabled=True, value=100.0)
    await h.wait_for("bath_relay", lambda s: s.state is True)
    await h.wait_for("bedroom_relay", lambda s: s.state is True)
    await h.wait_for("floor_demand", lambda s: s.state is True)

    await read_room(h, NAN)
    await h.wait_for("bath_relay", lambda s: s.state is False)
    await h.wait_for("bedroom_relay", lambda s: s.state is False)
    await h.wait_for("bath_radiant_override_active", lambda s: s.state is False)
    await h.wait_for("bedroom_radiant_override_active", lambda s: s.state is False)
    await h.wait_for("floor_demand", lambda s: s.state is False)
    # The override itself was not cleared.
    assert h.states["bath_radiant_override"].state is True

    # Still closed a while later (no periodic write may re-open it).
    await assert_relay_stays_off(h, "bath")
    await assert_relay_stays_off(h, "bedroom")

    # Sensor recovers: the override hold resumes.
    await read_room(h, AT_TARGET)
    await h.wait_for("bath_relay", lambda s: s.state is True)
    await h.wait_for("bath_radiant_override_active", lambda s: s.state is True)
    await h.wait_for("floor_demand", lambda s: s.state is True)


async def test_direct_boost_style_write_cannot_open_a_blind_zone(run_harness):
    """The boost coordinator also writes the final stage directly (level 1.0).

    Switching the override on while the sensor is NaN is the same situation as a
    boost replayed at boot before the first reading: the valve must stay shut.
    """
    h = await run_harness("radiant_direction")
    await set_season(h, "COOL")
    await read_room(h, NAN)
    await h.call("set_bath_override", enabled=True, value=100.0)
    await assert_relay_stays_off(h, "bath")
    await assert_active(h, "bath_radiant_override_active", False)
    assert relay_count(h, "bath") == 0
