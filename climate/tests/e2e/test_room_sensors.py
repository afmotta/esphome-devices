"""Behavioral tests for the HA tier of climate/room_sensors.yaml (R-04).

The harness runs the real room_sensors.yaml with the grace period compressed to
2 s. The test client plays Home Assistant: it answers the device's
`subscribe_home_assistant_states` request with entity states and pushes changes
with `send_home_assistant_state`. Cases:

    | HA side                              | Expected tier | Expected output |
    |--------------------------------------|---------------|-----------------|
    | numeric state                        | HA            | that value      |
    | `unavailable`                        | Emergency     | NaN             |
    | disconnected, within grace           | HA            | last value      |
    | disconnected, past grace             | Emergency     | NaN             |
    | reconnected, state re-pushed         | HA            | value           |

While the client is disconnected nothing is observable over the API, so the
harness latches "the abstracted temperature went NaN" in `nan_seen`; the test
reads the latch after reconnecting.
"""

import asyncio

import pytest

NAN = float("nan")

pytestmark = pytest.mark.asyncio

GRACE_S = 2.0  # harness: ha_staleness_grace_s
TEMP_ENTITY = "sensor.test_room_temperature"
HUMIDITY_ENTITY = "sensor.test_room_humidity"


class HomeAssistantStandIn:
    """Plays Home Assistant's side of the native API.

    HA's ESPHome integration, on every (re)connect, subscribes to the device's
    entity subscriptions and answers each with the entity's current state, then
    pushes changes. The stand-in does the same from a dict of entity states.
    """

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
    h = await run_harness("room_sensors")
    ids = {
        "temp": h.object_id("Test Room Temperature (Abstracted)"),
        "temp_tier": h.object_id("Test Room Temperature (Abstracted) Active Sensor Tier"),
        "humidity": h.object_id("Test Room Humidity (Abstracted)"),
        "humidity_tier": h.object_id("Test Room Humidity (Abstracted) Active Sensor Tier"),
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

    # Connected, but HA has sent nothing yet -> raw sensors are NaN -> Emergency.
    await h.wait_for(ids["temp_tier"], lambda s: s.state == "Emergency")

    ha.push(TEMP_ENTITY, "21.5")
    ha.push(HUMIDITY_ENTITY, "48.0")
    await h.wait_for(ids["temp_tier"], lambda s: s.state == "HA")
    await h.wait_for_value(ids["temp"], 21.5)
    await h.wait_for(ids["humidity_tier"], lambda s: s.state == "HA")
    await h.wait_for_value(ids["humidity"], 48.0)

    # A new value is followed while HA stays connected.
    ha.push(TEMP_ENTITY, "22.0")
    await h.wait_for_value(ids["temp"], 22.0)


async def test_unavailable_ha_state_is_emergency(run_harness):
    h, ha, ids = await _start(run_harness)

    ha.push(TEMP_ENTITY, "21.5")
    await h.wait_for(ids["temp_tier"], lambda s: s.state == "HA")

    # HA reports the entity as unavailable: used to be swallowed by
    # `filter_out: nan` (last good value kept), must now reach the failover as NaN.
    ha.push(TEMP_ENTITY, "unavailable")
    await h.wait_for(ids["temp_tier"], lambda s: s.state == "Emergency")
    await h.wait_for_value(ids["temp"], NAN)

    # `unknown` behaves the same; a numeric state recovers.
    ha.push(TEMP_ENTITY, "21.0")
    await h.wait_for(ids["temp_tier"], lambda s: s.state == "HA")
    ha.push(TEMP_ENTITY, "unknown")
    await h.wait_for(ids["temp_tier"], lambda s: s.state == "Emergency")
    ha.push(TEMP_ENTITY, "20.5")
    await h.wait_for(ids["temp_tier"], lambda s: s.state == "HA")
    await h.wait_for_value(ids["temp"], 20.5)


async def test_disconnect_within_grace_keeps_value(run_harness):
    h, ha, ids = await _start(run_harness)

    ha.push(TEMP_ENTITY, "21.5")
    await h.wait_for(ids["temp_tier"], lambda s: s.state == "HA")
    await _reset_nan_latch(h, ids)

    # An HA restart shorter than the grace period must not trip Emergency.
    await h.disconnect()
    await asyncio.sleep(GRACE_S / 2)
    await h.reconnect()
    ha.attach()

    await h.wait_for(ids["temp_tier"], lambda s: s.state == "HA")
    await h.wait_for_value(ids["temp"], 21.5)
    nan_seen = await h.wait_for(ids["nan_seen"], lambda s: True)
    assert nan_seen.state is False, "temperature went NaN during a disconnect shorter than the grace"


async def test_disconnect_past_grace_is_nan_then_recovers(run_harness):
    h, ha, ids = await _start(run_harness)

    ha.push(TEMP_ENTITY, "21.5")
    ha.push(HUMIDITY_ENTITY, "48.0")
    await h.wait_for(ids["temp_tier"], lambda s: s.state == "HA")
    await h.wait_for(ids["humidity_tier"], lambda s: s.state == "HA")
    await _reset_nan_latch(h, ids)

    # No HA client for well beyond the grace period (+ evaluation interval margin):
    # the frozen 21.5 must have been dropped to NaN while we were away.
    await h.disconnect()
    await asyncio.sleep(GRACE_S + 1.5)
    await h.reconnect()
    nan_seen = await h.wait_for(ids["nan_seen"], lambda s: True)
    assert nan_seen.state is True, "HA tier kept its frozen value after the grace period"

    # Reconnected and subscribed to states (the gate is open again), but HA answers
    # with no state: only the reset of the raw sensors on expiry can explain
    # Emergency/NaN here. If they still held the frozen 21.5 / 48.0 the tiers would
    # read HA. Humidity is checked too: it feeds the dew-point protection.
    ha.entity_states.clear()
    ha.attach()
    await h.wait_for(ids["temp_tier"], lambda s: s.state == "Emergency")
    await h.wait_for_value(ids["temp"], NAN)
    await h.wait_for(ids["humidity_tier"], lambda s: s.state == "Emergency")
    await h.wait_for_value(ids["humidity"], NAN)

    # HA publishes different values: the tier follows them, not the pre-outage ones.
    ha.push(TEMP_ENTITY, "22.0")
    ha.push(HUMIDITY_ENTITY, "50.0")
    await h.wait_for(ids["temp_tier"], lambda s: s.state == "HA")
    await h.wait_for_value(ids["temp"], 22.0)
    await h.wait_for(ids["humidity_tier"], lambda s: s.state == "HA")
    await h.wait_for_value(ids["humidity"], 50.0)
