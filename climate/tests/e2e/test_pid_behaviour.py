"""Behavioral tests for the PID wiring of the real actuator packages.

Harness: harness/pid_behaviour.yaml (heat-only radiant, heat_cool and cool_only
fancoils, a mixing valve, all with time-compressed gains: kp 0.5, ki 1.0).

R-13 — integral windup. ESPHome integrates the error on every sensor update,
whatever the PID mode, clamped to +-1. With the outputs gated on hp_mode (R-01)
the direction the heat pump is NOT producing wound up to a full actuator span:
a room above target on a winter afternoon drove the integral to -1 on the gated
cool side, and after it fell below target the PID stayed at output <= 0 until
ki * error had climbed the integral back. pid.yaml now confines the integral to
the active direction on every hp_mode change (HEAT => [0, limit], COOL =>
[-limit, 0]; SANITARY_ONLY keeps the previous bounds).

The recovery tests wind the loop up the WRONG way for 1.5 s, then flip the room
to the right side of target by 0.5 degC and require output within 0.5 s. With
the fix the P term acts at once (0.25); with the old +-1 bounds the integral
sits at -1 and needs ~1.9 s to climb back, so they fail without it.

R-14 — window guard vs a boost fancoil. The guard forced the fancoil OFF while
a window was open and restored a SNAPSHOT of the running mode at the end of
recovery, so a boost that ended meanwhile left the `boost` fancoil in COOL as a
permanent cooler (bypassing the coordinator and the {zone}_boost_enabled gate).
The guard now asks the fancoil's owner to re-derive the mode from its current
desire (${room}_fancoil_resume_mode). Tests (real guard with 1 s / 1 s timeouts
and a 100 ms poll, real coordinator, hot room):
  boost ended / gate closed / season left COOL during the open window => OFF
  boost still running after the window closes                          => COOL

R-16 — boot state of fancoil PIDs. A PID with only a cool_output starts in COOL
when it has no saved state, and the PID's restore (setup, priority DATA) runs
AFTER the hp_mode select's restore has already fired the role handlers (HARDWARE),
overwriting what they did. The roles now re-run their handler once everything is
set up (esphome.on_boot, priority -100, in the same merged trigger as the boost
coordinator's boot replay). Tests boot the harness on a fresh preference store
with hp_mode restored as COOL:
  boost      OFF (the real fancoil_boost coordinator is in the harness; its
             replay of a restored "Fancoil Boost" must still win)
  cool_only  COOL
  heat_cool  COOL (follows hp_mode)
"""

import asyncio
import os
import subprocess
import tempfile

import pytest
import pytest_asyncio
from aioesphomeapi import APIClient, ClimateMode
from conftest import API_PORT, HARNESS_DIR, Harness, _compile

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
    await h.wait_for_value(integral, expected * PCT, timeout=3.0)  # ki * |error| = 1.0 per second
    await asyncio.sleep(0.5)
    assert value(h, integral) == pytest.approx(expected * PCT, abs=0.1)  # saturates, not beyond


async def test_season_flip_drops_the_old_seasons_integral(run_harness):
    """A heat_cool fancoil that wound up +1 heating must not carry it into
    cooling: the COOL bounds clamp it on the next update, no reset call."""
    h = await run_harness("pid_behaviour")
    integral = h.object_id(LOOPS["attic"][0])
    await set_season(h, "HEAT")
    await h.call("set_temperature", value=TARGET - 1.0)
    await h.wait_for_value(integral, PCT, timeout=3.0)
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
    await h.wait_for_value(integral, PCT, timeout=3.0)
    await h.call("set_temperature", value=TARGET)  # error 0: the integral holds
    await set_season(h, republished)
    await asyncio.sleep(0.5)
    assert value(h, integral) == pytest.approx(PCT, abs=0.1)


# --------------------------------------------------------------------------
# R-16: deterministic boot state of the fancoil PIDs
# --------------------------------------------------------------------------


class Boot:
    """One run of the harness binary against a given preference store.

    The shared run_harness fixture hands out a fresh process per call; restart
    tests need to stop one binary and start the next on the SAME store (the host
    platform flushes preferences on SIGTERM), so they drive the process here.
    """

    def __init__(self, prefdir: str) -> None:
        self.prefdir = prefdir
        self.proc: subprocess.Popen | None = None
        self.harness: Harness | None = None

    async def start(self, name: str = "pid_behaviour") -> Harness:
        binary = await asyncio.to_thread(_compile, HARNESS_DIR / f"{name}.yaml")
        env = {**os.environ, "ESPHOME_PREFDIR": self.prefdir}
        self.proc = subprocess.Popen(
            [str(binary)], cwd=tempfile.mkdtemp(prefix="climate-e2e-boot-"), env=env,
            stdout=open(os.environ.get("BOOT_LOG", os.devnull), "ab"), stderr=subprocess.STDOUT,
        )
        async with asyncio.timeout(10):
            while True:
                try:
                    _, writer = await asyncio.open_connection("127.0.0.1", API_PORT)
                    writer.close()
                    break
                except OSError:
                    await asyncio.sleep(0.05)
        self.harness = Harness(client=APIClient("127.0.0.1", API_PORT, password=None))
        await self.harness.start()
        return self.harness

    async def stop(self) -> None:
        if self.harness is not None:
            await self.harness.client.disconnect()
            self.harness = None
        if self.proc is not None:
            self.proc.terminate()  # SIGTERM: the host platform flushes preferences
            await asyncio.to_thread(self.proc.wait, 5)
            self.proc = None


@pytest_asyncio.fixture
async def boot(tmp_path):
    b = Boot(str(tmp_path))
    yield b
    await b.stop()


def mode(h, name: str):
    return h.states[h.object_id(name)].mode


async def hold(h, name: str, expected, seconds: float = 0.6):
    """The PID mode is `expected` as soon as the boot states are in, and stays so."""
    await h.wait_for(h.object_id(name), lambda s: True)
    assert mode(h, name) == expected
    await asyncio.sleep(seconds)
    assert mode(h, name) == expected


async def test_fresh_boot_in_cool_has_deterministic_fancoil_modes(boot):
    h = await boot.start()
    await h.wait_for("heat_pump_mode", lambda s: s.state == "COOL")
    await hold(h, "Living Fancoil PID", ClimateMode.OFF)  # boost: only the coordinator starts it
    await hold(h, "Techroom Fancoil PID", ClimateMode.COOL)  # cool_only follows hp_mode
    await hold(h, "Attic Fancoil PID", ClimateMode.COOL)  # heat_cool follows hp_mode
    await hold(h, "Loft Fancoil PID", ClimateMode.COOL)


async def test_fresh_boot_does_not_run_the_boost_fancoil_in_cool(boot):
    """The consequence of the mode: a hot room on a fresh boot in COOL must not
    start the boost-role fancoil (it used to, behind the boost_enabled gate)."""
    h = await boot.start()
    await h.call("set_temperature", value=TARGET + 5.0)
    await h.wait_for("techroom_fan_level", lambda s: s.state == pytest.approx(1.0))  # cool_only does cool
    await asyncio.sleep(0.5)
    assert value(h, "living_fan_level") == pytest.approx(0.0)


SENSOR_LOST_GRACE = 5.0  # sensor_lost_grace in the harness (prod default 120 s)
LIVING_BOOST = "living_boost_state"
# A room still above target, so the boost is not ended by "target reached" meanwhile.
HOT = TARGET + 3.0


async def start_boost_then_restart(boot, *, fancoil_off: bool = False):
    """Run a boost with a valid room reading, then reboot the controller on the same
    preference store. Returns the new harness: the boost is restored from flash,
    the room temperature is NaN until the test publishes one (as after a real
    reboot, where the first CAN frame / HA connection takes a while)."""
    h = await boot.start()
    await h.call("set_boost_enabled", value=True)  # else the gate drops the boost at once
    await h.call("set_temperature", value=HOT)
    await h.call("boost_start")
    await h.wait_for(LIVING_BOOST, lambda s: s.state == "Fancoil Boost")
    await h.wait_for(h.object_id("Living Fancoil PID"), lambda s: s.mode == ClimateMode.COOL)
    await h.wait_for(h.object_id("Living Relay"), lambda s: s.state is True)  # valve held open
    if fancoil_off:
        await h.call("living_fancoil_mode", value="OFF")
        await h.wait_for(h.object_id("Living Fancoil PID"), lambda s: s.mode == ClimateMode.OFF)
    await boot.stop()
    return await boot.start()


async def test_restart_during_boost_replays_the_boost(boot):
    """The boot sync must not stomp the coordinator's replay of a boost that was
    running when the controller rebooted (both live in the one -100 trigger).

    The PID is switched OFF behind the coordinator's back before the restart, so
    only the replay (select.set of the restored "Fancoil Boost") can bring COOL
    back: a dropped replay AND a sync that wins over it both leave it OFF.

    The first room reading arrives right after the restart, well inside the
    sensor-loss grace, like the first CAN frame on a healthy controller.
    """
    h = await start_boost_then_restart(boot, fancoil_off=True)
    await h.call("set_temperature", value=HOT)
    await h.wait_for(LIVING_BOOST, lambda s: s.state == "Fancoil Boost")
    await hold(h, "Living Fancoil PID", ClimateMode.COOL)


async def test_restart_during_boost_keeps_it_if_the_reading_arrives_within_the_grace(boot):
    """Boot-time NaN is not a sensor loss: the restored boost runs through the
    grace, the valve is shut meanwhile (NaN), and reopens with the first reading."""
    h = await start_boost_then_restart(boot)
    await h.wait_for(LIVING_BOOST, lambda s: s.state == "Fancoil Boost")
    await hold(h, "Living Fancoil PID", ClimateMode.COOL)
    # No reading yet: the final stage keeps the valve closed whatever the override says.
    assert h.states[h.object_id("Living Relay")].state is False

    await asyncio.sleep(SENSOR_LOST_GRACE * 0.4)
    await h.call("set_temperature", value=HOT)  # inside the grace
    await h.wait_for(h.object_id("Living Relay"), lambda s: s.state is True)

    # Past the point where the grace would have expired had the reading not come.
    await asyncio.sleep(SENSOR_LOST_GRACE)
    assert h.states[LIVING_BOOST].state == "Fancoil Boost"
    assert mode(h, "Living Fancoil PID") == ClimateMode.COOL
    assert h.states[h.object_id("Living Relay")].state is True


async def test_restart_during_boost_ends_it_if_no_reading_arrives_within_the_grace(boot):
    """A restored boost whose room temperature never comes back is a real sensor
    loss: it survives the grace, then ends (valve closed all along)."""
    h = await start_boost_then_restart(boot)
    await h.wait_for(LIVING_BOOST, lambda s: s.state == "Fancoil Boost")
    await asyncio.sleep(SENSOR_LOST_GRACE * 0.4)
    assert h.states[LIVING_BOOST].state == "Fancoil Boost"
    assert h.states[h.object_id("Living Relay")].state is False

    await h.wait_for(LIVING_BOOST, lambda s: s.state == "Radiant Only", timeout=SENSOR_LOST_GRACE + 2)
    await h.wait_for(h.object_id("Living Fancoil PID"), lambda s: s.mode == ClimateMode.OFF)
    await h.wait_for(h.object_id("Living Radiant Override"), lambda s: s.state is False)
    assert h.states[h.object_id("Living Relay")].state is False


async def test_restart_without_a_boost_does_not_resurrect_a_manual_cool(boot):
    """A boost-role fancoil comes up OFF unless a boost is running, even if the
    PID was left in COOL (e.g. a manual HA change): only the coordinator starts it."""
    h = await boot.start()
    await h.call("living_fancoil_mode", value="COOL")
    await h.wait_for(h.object_id("Living Fancoil PID"), lambda s: s.mode == ClimateMode.COOL)
    await boot.stop()

    h = await boot.start()
    await h.wait_for("living_boost_state", lambda s: s.state == "Radiant Only")
    await hold(h, "Living Fancoil PID", ClimateMode.OFF)


# --------------------------------------------------------------------------
# R-14: the window guard hands the fancoil back to its owner
# --------------------------------------------------------------------------

LIVING = "Living Fancoil PID"
OPEN_AND_CLOSED_S = 1.0  # harness: recovery_timeout (window_timeout is 1 s too)


async def boost_running(h):
    """Gate open, boost started, room hot: the boost fancoil is cooling."""
    await h.call("set_temperature", value=TARGET + 5.0)
    await h.call("set_boost_enabled", value=True)
    await h.call("boost_start")
    await h.wait_for(h.object_id(LIVING), lambda s: s.mode == ClimateMode.COOL)
    await h.wait_for("living_fan_level", lambda s: s.state == pytest.approx(1.0))


async def window_open_until_guard_acts(h):
    await h.call("set_window", value=True)
    await h.wait_for(h.object_id(LIVING), lambda s: s.mode == ClimateMode.OFF, timeout=3.0)
    await h.wait_for(h.object_id("Living Window Guard"), lambda s: s.state == "Active")


async def close_window_and_recover(h):
    await h.call("set_window", value=False)
    await h.wait_for(h.object_id("Living Window Guard"), lambda s: s.state == "Normal", timeout=4.0)
    await asyncio.sleep(0.5)  # a wrongly restored mode would show up now


async def end_boost_by_stop(h):
    # The boost ends because the room reached its target. (In a still-hot room
    # the coordinator would legitimately start the next boost at once.)
    await h.call("set_temperature", value=TARGET - 1.0)
    await h.call("boost_stop")


async def end_boost_by_gate(h):
    await h.call("set_boost_enabled", value=False)  # coordinator's override ends the boost


async def end_boost_by_season(h):
    await set_season(h, "HEAT")  # cooling season over: override ends the boost


@pytest.mark.parametrize("end_boost", [end_boost_by_stop, end_boost_by_gate, end_boost_by_season])
async def test_window_guard_does_not_resurrect_a_boost_that_ended(run_harness, end_boost):
    h = await run_harness("pid_behaviour")
    await boost_running(h)
    await window_open_until_guard_acts(h)
    await end_boost(h)
    await h.wait_for("living_boost_state", lambda s: s.state == "Radiant Only", timeout=3.0)
    await close_window_and_recover(h)

    assert mode(h, LIVING) == ClimateMode.OFF
    assert value(h, "living_fan_level") == pytest.approx(0.0)


async def test_window_guard_restores_a_boost_that_is_still_running(run_harness):
    h = await run_harness("pid_behaviour")
    await boost_running(h)
    await window_open_until_guard_acts(h)
    await h.wait_for("living_fan_level", lambda s: s.state == pytest.approx(0.0))  # shut for the airing
    await close_window_and_recover(h)

    assert h.states["living_boost_state"].state == "Fancoil Boost"
    assert mode(h, LIVING) == ClimateMode.COOL
    await h.wait_for("living_fan_level", lambda s: s.state == pytest.approx(1.0))
