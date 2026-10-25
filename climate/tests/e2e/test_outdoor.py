"""Behavioral tests for the HA tier of climate/outdoor.yaml (R-12).

Same rule and same stand-in as test_room_sensors.py (R-04), applied to the
outdoor temperature that feeds the heating curve (weather_compensation.yaml).
The harness runs the real outdoor.yaml with the grace period compressed to 2 s:

    | HA side                              | Expected tier | Expected output |
    |--------------------------------------|---------------|-----------------|
    | numeric state                        | HA            | that value      |
    | `unavailable` / `unknown`            | Emergency     | NaN             |
    | disconnected, within grace           | HA            | last value      |
    | disconnected, past grace             | Emergency     | NaN             |
    | reconnected, state re-pushed         | HA            | value           |
"""

import asyncio

import pytest

NAN = float("nan")

pytestmark = pytest.mark.asyncio

GRACE_S = 2.0  # harness: ha_outdoor_staleness_grace_s
OUTDOOR_ENTITY = "sensor.test_outdoor_temperature"


class HomeAssistantStandIn:
    """Plays Home Assistant's side of the native API (see test_room_sensors.py)."""

    def __init__(self, harness) -> None:
        self.harness = harness
        self.entity_states: dict[str, str] = {}

    def attach(self) -> None:
        """Start answering state subscriptions. Call after every (re)connect."""
        self.harness.client.subscribe_home_assistant_states(self._on_subscription)

    def _on_subscription(self, entity_id: str, attribute: str | None) -> None:
        if entity_id in self.entity_states:
            self.harness.client.send_home_assistant_state(
                entity_id, attribute or None, self.entity_states[entity_id]
            )

    def push(self, entity_id: str, state: str) -> None:
        """Set an entity's state and send it (what HA does on a state change)."""
        self.entity_states[entity_id] = state
        self.harness.client.send_home_assistant_state(entity_id, None, state)


async def _start(run_harness):
    h = await run_harness("outdoor")
    ids = {
        "temp": h.object_id("Outdoor Temperature (Abstracted)"),
        "tier": h.object_id("Outdoor Temperature (Abstracted) Active Sensor Tier"),
        "nan_seen": h.object_id("NaN Seen"),
    }
    ha = HomeAssistantStandIn(h)
    ha.attach()
    return h, ha, ids


async def _reset_nan_latch(h, ids) -> None:
    await h.call("reset_nan_seen")
    await h.wait_for(ids["nan_seen"], lambda s: s.state is False)


async def test_numeric_ha_state_is_ha_tier(run_harness):
    h, ha, ids = await _start(run_harness)

    # Connected, but HA has sent nothing yet -> raw sensor NaN -> Emergency.
    await h.wait_for(ids["tier"], lambda s: s.state == "Emergency")

    ha.push(OUTDOOR_ENTITY, "7.5")
    await h.wait_for(ids["tier"], lambda s: s.state == "HA")
    await h.wait_for_value(ids["temp"], 7.5)

    # Negative values and updates are followed while HA stays connected.
    ha.push(OUTDOOR_ENTITY, "-3.2")
    await h.wait_for_value(ids["temp"], -3.2)


async def test_unavailable_ha_state_is_nan(run_harness):
    h, ha, ids = await _start(run_harness)

    ha.push(OUTDOOR_ENTITY, "7.5")
    await h.wait_for(ids["tier"], lambda s: s.state == "HA")

    # Used to be swallowed by `filter_out: nan` (last value kept forever).
    ha.push(OUTDOOR_ENTITY, "unavailable")
    await h.wait_for(ids["tier"], lambda s: s.state == "Emergency")
    await h.wait_for_value(ids["temp"], NAN)

    ha.push(OUTDOOR_ENTITY, "8.0")
    await h.wait_for(ids["tier"], lambda s: s.state == "HA")
    ha.push(OUTDOOR_ENTITY, "unknown")
    await h.wait_for(ids["tier"], lambda s: s.state == "Emergency")
    ha.push(OUTDOOR_ENTITY, "9.0")
    await h.wait_for_value(ids["temp"], 9.0)


async def test_disconnect_within_grace_keeps_value(run_harness):
    h, ha, ids = await _start(run_harness)

    ha.push(OUTDOOR_ENTITY, "7.5")
    await h.wait_for(ids["tier"], lambda s: s.state == "HA")
    await _reset_nan_latch(h, ids)

    # An HA restart shorter than the grace period must not trip Emergency.
    await h.disconnect()
    await asyncio.sleep(GRACE_S / 2)
    await h.reconnect()
    ha.attach()

    await h.wait_for(ids["tier"], lambda s: s.state == "HA")
    await h.wait_for_value(ids["temp"], 7.5)
    nan_seen = await h.wait_for(ids["nan_seen"], lambda s: True)
    assert nan_seen.state is False, "outdoor temperature went NaN during a disconnect shorter than the grace"


async def test_disconnect_past_grace_is_nan_then_recovers(run_harness):
    h, ha, ids = await _start(run_harness)

    ha.push(OUTDOOR_ENTITY, "7.5")
    await h.wait_for(ids["tier"], lambda s: s.state == "HA")
    await _reset_nan_latch(h, ids)

    # No HA client for well beyond the grace period: the frozen 7.5 must have
    # been dropped to NaN while we were away.
    await h.disconnect()
    await asyncio.sleep(GRACE_S + 1.5)
    await h.reconnect()
    nan_seen = await h.wait_for(ids["nan_seen"], lambda s: True)
    assert nan_seen.state is True, "HA outdoor tier kept its frozen value after the grace period"

    # HA comes back: it answers the resubscription and the tier recovers.
    ha.attach()
    await h.wait_for(ids["tier"], lambda s: s.state == "HA")
    await h.wait_for_value(ids["temp"], 7.5)
