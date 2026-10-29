"""Behavioral tests for the PID wiring of the real actuator packages.

Harness: harness/pid_behaviour.yaml (heat-only radiant, heat_cool and cool_only
fancoils, a mixing valve, all with time-compressed gains: kp 0.5, ki 1.0).

R-13 — integral windup: pid.yaml confines the integral to the active direction
on every hp_mode change (rationale: pid_direction::integral_bounds).

The recovery tests wind the loop up the WRONG way for 1.5 s, then flip the room
to the right side of target by 0.5 degC and require output within 0.5 s. With
the fix the P term acts at once (0.25); with the old +-1 bounds the integral
sits at -1 and needs ~1.9 s to climb back, so they fail without it.
"""

import asyncio

import pytest

pytestmark = pytest.mark.asyncio

TARGET = 20.0
WIND_UP_S = 1.5  # wrong-direction exposure (old bounds reach -1 in 0.2 s at 5 degC)
RECOVER_S = 0.5  # output must act within this after the room crosses the target (old: ~1.9 s)
ACT = 0.2  # "the actuator acts": above P-only output (0.25) minus margin
# The pid sensor platform publishes percent (value * 100); 0-10V level sensors are 0..1.
PCT = 100.0


@pytest.fixture(autouse=True)
def isolated_preferences(tmp_path, monkeypatch):
    """The host platform keeps preferences (PID mode, restored selects) under
    ESPHOME_PREFDIR or ~/.esphome/prefs; give every test a fresh store so no
    state leaks between runs."""
    monkeypatch.setenv("ESPHOME_PREFDIR", str(tmp_path))


async def set_season(h, mode: str):
    await h.call("set_hp_mode", value=mode)
    await h.wait_for("heat_pump_mode", lambda s: s.state == mode)


def value(h, object_id: str) -> float:
    state = h.states.get(object_id)
    assert state is not None, f"{object_id} never published"
    return state.state


# loop -> (integral sensor name, "acting" signal object id, signal scale, temperature action)
#   bath is a slow-PWM radiant relay, so its PID Result (percent) is observed;
#   the fancoils and the valve are observed at their 0-10V level (0..1, after
#   the gate).
LOOPS = {
    "bath": ("Bath Radiant PID Integral", "bath_radiant_pid_result", PCT, "set_temperature"),
    "attic": ("Attic Fancoil PID Integral", "attic_fan_level", 1.0, "set_temperature"),
    "techroom": ("Techroom Fancoil PID Integral", "techroom_fan_level", 1.0, "set_temperature"),
    "loft": ("Loft Fancoil PID Integral", "loft_fan_level", 1.0, "set_temperature"),
    "mix": ("Mix Mixing Valve PID Integral", "valve_level", 1.0, "set_supply_temperature"),
}


async def wind_up_wrong_way_then_recover(h, loop: str, season: str):
    """Hold the loop on the wrong side of target for WIND_UP_S, then 0.5 degC on
    the right side; return the integral measured at the end of the wind-up."""
    integral_name, signal, scale, action = LOOPS[loop]
    integral = h.object_id(integral_name)
    await set_season(h, season)

    # HEAT wants warmth: the wrong side is "too warm" (error < 0). COOL: too cold.
    wrong, right = (TARGET + 5.0, TARGET - 0.5) if season == "HEAT" else (TARGET - 5.0, TARGET + 0.5)
    await h.call(action, value=wrong)
    await asyncio.sleep(WIND_UP_S)
    wound = value(h, integral) / PCT

    await h.call(action, value=right)
    await h.wait_for(signal, lambda s: s.state > ACT * scale, timeout=RECOVER_S)
    return wound


# (loop, season) pairs where the loop can act: a heat-only loop never cools,
# a cool-only loop never heats.
RECOVERY_CASES = [
    ("bath", "HEAT"),
    ("attic", "HEAT"),
    ("attic", "COOL"),
    ("techroom", "COOL"),
    ("mix", "HEAT"),
    ("mix", "COOL"),
]


@pytest.mark.parametrize("loop,season", RECOVERY_CASES)
async def test_no_windup_in_the_direction_the_water_does_not_flow(run_harness, loop, season):
    h = await run_harness("pid_behaviour")
    wound = await wind_up_wrong_way_then_recover(h, loop, season)
    # Wrong-way exposure leaves the integral at 0, not at the old -1/+1 bound.
    assert wound == pytest.approx(0.0, abs=1e-3)  # old bounds: -1.0 / +1.0


@pytest.mark.parametrize(
    "loop,season,expected",
    [("attic", "HEAT", 1.0), ("attic", "COOL", -1.0), ("loft", "HEAT", 0.5), ("loft", "COOL", -0.5)],
)
async def test_active_direction_keeps_its_range(run_harness, loop, season, expected):
    """The bound only removes the wrong side: demand in the active direction
    still integrates up to the limit (1.0 by default, overridable per loop)."""
    h = await run_harness("pid_behaviour")
    integral = h.object_id(LOOPS[loop][0])
    await set_season(h, season)
    await h.call("set_temperature", value=TARGET - 1.0 if season == "HEAT" else TARGET + 1.0)
    await h.wait_for_value(integral, expected * PCT, timeout=10.0)  # ki * |error| = 1.0 per second
    await asyncio.sleep(0.5)
    assert value(h, integral) == pytest.approx(expected * PCT, abs=0.1), (  # saturates, not beyond
        f"integral {value(h, integral)} after saturating"
    )


async def test_season_flip_drops_the_old_seasons_integral(run_harness):
    """A heat_cool fancoil that wound up +1 heating must not carry it into
    cooling: the COOL bounds clamp it on the next update, no reset call."""
    h = await run_harness("pid_behaviour")
    integral = h.object_id(LOOPS["attic"][0])
    await set_season(h, "HEAT")
    await h.call("set_temperature", value=TARGET - 1.0)
    await h.wait_for_value(integral, PCT, timeout=10.0)
    await set_season(h, "COOL")
    await h.wait_for_value(integral, 0.0, timeout=RECOVER_S)


@pytest.mark.parametrize("republished", ["HEAT", "SANITARY_ONLY"])
async def test_legitimate_integral_survives_a_republished_or_idle_mode(run_harness, republished):
    """Re-publishing the same hp_mode (HA, restore) or a short SANITARY_ONLY
    spell must not wipe the steady-state offset a loop has learned."""
    h = await run_harness("pid_behaviour")
    integral = h.object_id(LOOPS["attic"][0])
    await set_season(h, "HEAT")
    await h.call("set_temperature", value=TARGET - 1.0)
    await h.wait_for_value(integral, PCT, timeout=10.0)
    await h.call("set_temperature", value=TARGET)  # error 0: the integral holds
    await set_season(h, republished)
    await asyncio.sleep(0.5)
    assert value(h, integral) == pytest.approx(PCT, abs=0.1), f"integral {value(h, integral)} after {republished}"
