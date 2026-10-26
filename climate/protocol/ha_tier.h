#pragma once
#include <cmath>
#include <cstdint>

// =============================================================================
// HA-tier staleness gate (R-04) — when may the Home Assistant sensor value count?
// =============================================================================
//
// Tier 2 of the room-sensor failover (climate/room_sensors.yaml) is a
// `homeassistant` sensor. That platform has no staleness of its own: when the API
// connection to HA drops it keeps publishing nothing and the sensor keeps its last
// value forever, so the PID, the dew-point protection and the fancoil boost would
// run on a frozen reading indefinitely. This header is the rule that turns "HA
// went away" into NaN, which the failover resolves to Emergency and ESPHome's PID
// answers by driving its outputs to 0 at once.
//
//   trusted = an HA-capable API client is connected now
//             || it was connected within the last grace_ms
//
// Deliberately NOT "time since the last value arrived": HA only pushes state
// *changes*, so a perfectly healthy but stable room temperature would expire.
// Connection liveness is the staleness signal; the grace period covers only a
// missing client. Entities HA reports as unavailable/unknown (e.g. while it
// restarts) still arrive as NaN and are Emergency immediately, by design.
//
// Boot: before any client has ever been seen the gate is closed (NaN). That costs
// nothing in practice — the raw HA sensor has no value until HA connects and
// pushes one — and it is the fail-safe default if that ever stops being true.
//
// A tracker is per gated sensor and is sampled by the template sensor's periodic
// lambda (10 s, same cadence as the failover), so staleness is detected even when
// HA never sends anything again. last_connected_ms is the last *sampled* connected
// instant, so the effective grace is grace_ms minus at most one sample period.
//
// Pure logic, no ESPHome includes — natively tested in tests/test_ha_tier.cpp.
// Time math is unsigned uint32_t subtraction, so millis() wraparound (~49.7 days)
// is harmless while grace_ms stays far below 2^31 ms. `expired` latches once the
// grace is exceeded and clears only on a reconnect, so a disconnect that outlasts a
// full wrap cannot make (now - last_connected_ms) small again and resurrect a
// frozen value.
// =============================================================================

struct HaTierTracker
{
  bool seen = false;               // a client has been connected at least once
  bool expired = false;            // grace exceeded since the last connection (latched)
  uint32_t last_connected_ms = 0;  // last sample at which a client was connected
};

// Advance the tracker with one sample and say whether the HA tier is trusted.
// `connected` is the caller's "an HA-capable API client is connected right now".
inline bool ha_tier_update(HaTierTracker &t, bool connected, uint32_t now_ms, uint32_t grace_ms)
{
  if (connected)
  {
    t.seen = true;
    t.expired = false;
    t.last_connected_ms = now_ms;
    return true;
  }
  if (!t.seen || t.expired)
    return false;
  if ((uint32_t) (now_ms - t.last_connected_ms) > grace_ms)
  {
    t.expired = true;
    return false;
  }
  return true;
}

// The gated value: the raw HA reading while trusted, NaN otherwise. A NaN raw
// (HA reported `unavailable`/`unknown`) passes through as NaN either way.
inline float ha_tier_gate(HaTierTracker &t, bool connected, uint32_t now_ms,
                          uint32_t grace_ms, float raw)
{
  return ha_tier_update(t, connected, now_ms, grace_ms) ? raw : NAN;
}
