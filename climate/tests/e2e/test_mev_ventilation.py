"""Behavioral tests for the MEV ventilation coordinators (R-08b).

The harness runs the real mev_ventilation.yaml (cascade, "MEV Cascade") and
mev_ventilation_fan_only.yaml ("MEV Fan Only") side by side with stubbed
inputs and NO Home Assistant. Their minimum fan speed, cascade thresholds and
delays are local persisted numbers; this pins:

  final fan speed rule (both coordinators)
    | enabled | alarm | demand            | final fan speed          |
    |---------|-------|-------------------|--------------------------|
    | off     | -     | any               | 0                        |
    | on      | on    | any               | 0                        |
    | on      | off   | NaN               | min                      |
    | on      | off   | below min         | min                      |
    | on      | off   | between min..100  | demand                   |
    | on      | off   | above 100         | 100                      |
  the minimum is the number's value: retuning it moves the floor.

  local defaults (no HA needed): min 20 %, escalation 80 %, de-escalation 40 %,
  escalation delay 10 min, de-escalation delay 15 min.

  cascade without HA: a rising humidity at a fan speed >= the escalation
  threshold starts the "Escalating (Dehum)" delay -- impossible while the
  threshold was a `homeassistant` sensor reading NaN.
"""

import pytest

NAN = float("nan")

pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
def isolated_preferences(tmp_path, monkeypatch):
    """Give every test its own preference store.

    The host platform persists `restore_value` numbers and the `Enabled` switch
    under $ESPHOME_PREFDIR (default ~/.esphome/prefs, shared across runs), so a
    value one test leaves behind would be restored into the next one and the
    first-boot defaults could never be observed.
    """
    monkeypatch.setenv("ESPHOME_PREFDIR", str(tmp_path))


UNITS = [
    # (id prefix used by the api actions, entity-name prefix)
    ("casc", "MEV Cascade"),
    ("fan", "MEV Fan Only"),
]


async def _start(run_harness, name: str):
    h = await run_harness("mev_ventilation")
    ids = {
        "min": h.object_id(f"{name} Minimum Fan Speed"),
        "final": h.object_id(f"{name} Final Fan Speed"),
        "enabled": h.object_id(f"{name} Enabled"),
        "output": h.object_id("Cascade Fan Output" if name == "MEV Cascade" else "Fan Only Fan Output"),
        "state": h.object_id(f"{name} Automation State"),
    }
    return h, ids


def _set_number(h, object_id: str, value: float) -> None:
    h.client.number_command(h._entities[object_id].key, value)


def _set_switch(h, object_id: str, value: bool) -> None:
    h.client.switch_command(h._entities[object_id].key, value)


@pytest.mark.parametrize("prefix,name", UNITS)
async def test_gate_alarm_and_minimum_floor(run_harness, prefix, name):
    h, ids = await _start(run_harness, name)

    # Commissioning gate defaults OFF: fan forced to 0 whatever the demand.
    await h.call(f"set_{prefix}_demand", value=60.0)
    await h.wait_for_value(ids["final"], 0.0)

    _set_switch(h, ids["enabled"], True)
    await h.wait_for_value(ids["final"], 60.0)
    await h.wait_for_value(ids["output"], 60.0)  # the DAC-side number follows

    # Demand below the floor is raised to the floor (default 20 %).
    await h.call(f"set_{prefix}_demand", value=5.0)
    await h.wait_for_value(ids["final"], 20.0)

    # Above 100 is clamped.
    await h.call(f"set_{prefix}_demand", value=140.0)
    await h.wait_for_value(ids["final"], 100.0)

    # Alarm is a deliberate hard-off, and recovers when it clears.
    await h.call(f"set_{prefix}_demand", value=60.0)
    await h.wait_for_value(ids["final"], 60.0)
    await h.call(f"set_{prefix}_alarm", value=True)
    await h.wait_for_value(ids["final"], 0.0)
    await h.call(f"set_{prefix}_alarm", value=False)
    await h.wait_for_value(ids["final"], 60.0)

    # Gate switched off again: back to 0.
    _set_switch(h, ids["enabled"], False)
    await h.wait_for_value(ids["final"], 0.0)


@pytest.mark.parametrize("prefix,name", UNITS)
async def test_minimum_fan_speed_is_the_local_number(run_harness, prefix, name):
    h, ids = await _start(run_harness, name)

    # Default, with no Home Assistant anywhere.
    await h.wait_for_value(ids["min"], 20.0)

    _set_switch(h, ids["enabled"], True)
    await h.call(f"set_{prefix}_demand", value=10.0)
    await h.wait_for_value(ids["final"], 20.0)

    # Retuning the number moves the floor ...
    _set_number(h, ids["min"], 35.0)
    await h.wait_for_value(ids["min"], 35.0)
    await h.wait_for_value(ids["final"], 35.0)

    # ... down to 0, where demand passes straight through ...
    _set_number(h, ids["min"], 0.0)
    await h.wait_for_value(ids["final"], 10.0)

    # ... and a missing demand reading falls back to the floor, not to 0 or 100.
    _set_number(h, ids["min"], 25.0)
    await h.call(f"set_{prefix}_demand", value=NAN)
    await h.wait_for_value(ids["final"], 25.0)


async def test_cascade_tuning_defaults_are_local(run_harness):
    h, _ = await _start(run_harness, "MEV Cascade")
    for label, expected in [
        ("Minimum Fan Speed", 20.0),
        ("Escalation Fan Threshold", 80.0),
        ("De-escalation Fan Threshold", 40.0),
        ("Escalation Delay", 10.0),
        ("De-escalation Delay", 15.0),
    ]:
        await h.wait_for_value(h.object_id(f"MEV Cascade {label}"), expected)


async def test_cascade_starts_without_home_assistant(run_harness):
    h, ids = await _start(run_harness, "MEV Cascade")
    threshold = h.object_id("MEV Cascade Escalation Fan Threshold")

    _set_switch(h, ids["enabled"], True)
    await h.call("set_casc_humidity_rate", value=1.0)  # humidity rising

    # Fan below the (default 80 %) threshold: no escalation timer.
    await h.call("set_casc_demand", value=70.0)
    await h.wait_for_value(ids["final"], 70.0)
    assert (ids["state"] not in h.states) or h.states[ids["state"]].state != "Escalating (Dehum)"

    # Fan at/above it: the escalation delay starts.
    await h.call("set_casc_demand", value=85.0)
    await h.wait_for(ids["state"], lambda s: s.state == "Escalating (Dehum)")

    # Retuning the threshold below the fan speed is honoured too: drop the
    # fan below the threshold again (cancelling the timer), then lower the
    # threshold under the current speed and the timer restarts.
    await h.call("set_casc_demand", value=60.0)
    await h.wait_for(ids["state"], lambda s: s.state == "Idle")
    _set_number(h, threshold, 55.0)
    await h.wait_for_value(threshold, 55.0)
    await h.wait_for(ids["state"], lambda s: s.state == "Escalating (Dehum)")
