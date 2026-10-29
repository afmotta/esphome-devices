#include <cassert>
#include <cmath>
#include <cstdint>

#include "ha_tier.h"

namespace
{

  constexpr uint32_t GRACE_MS = 300000; // 5 min, the room_sensors.yaml default

  void assert_close(float actual, float expected)
  {
    assert(std::fabs(actual - expected) < 0.001f);
  }

  void test_connected_passes_raw()
  {
    HaTierTracker t;
    assert_close(ha_tier_gate(t, true, 1000, GRACE_MS, 21.5f), 21.5f);
    // Value changes are followed while connected.
    assert_close(ha_tier_gate(t, true, 11000, GRACE_MS, 22.0f), 22.0f);
  }

  void test_boot_before_any_client_is_closed()
  {
    HaTierTracker t;
    // Never connected: closed regardless of the raw value or how long we wait.
    assert(std::isnan(ha_tier_gate(t, false, 0, GRACE_MS, 21.5f)));
    assert(std::isnan(ha_tier_gate(t, false, 10000, GRACE_MS, 21.5f)));
    assert(!t.seen);
    // First connection opens it.
    assert_close(ha_tier_gate(t, true, 20000, GRACE_MS, 21.5f), 21.5f);
    assert(t.seen);
  }

  void test_disconnected_within_grace_passes_raw()
  {
    HaTierTracker t;
    assert_close(ha_tier_gate(t, true, 1000, GRACE_MS, 21.5f), 21.5f);
    assert_close(ha_tier_gate(t, false, 1000 + 60000, GRACE_MS, 21.5f), 21.5f);
    // Grace is inclusive: exactly grace_ms after the last connected sample.
    assert_close(ha_tier_gate(t, false, 1000 + GRACE_MS, GRACE_MS, 21.5f), 21.5f);
    assert(!t.expired);
  }

  void test_disconnected_past_grace_is_nan()
  {
    HaTierTracker t;
    assert_close(ha_tier_gate(t, true, 1000, GRACE_MS, 21.5f), 21.5f);
    assert(std::isnan(ha_tier_gate(t, false, 1000 + GRACE_MS + 1, GRACE_MS, 21.5f)));
    assert(t.expired);
    // Stays NaN for as long as the client stays away.
    assert(std::isnan(ha_tier_gate(t, false, 1000 + 3600000, GRACE_MS, 21.5f)));
  }

  void test_reconnect_restores_raw()
  {
    HaTierTracker t;
    assert_close(ha_tier_gate(t, true, 1000, GRACE_MS, 21.5f), 21.5f);
    assert(std::isnan(ha_tier_gate(t, false, 1000 + GRACE_MS + 10000, GRACE_MS, 21.5f)));
    // Reconnect after expiry: raw again, expiry cleared, grace restarts from here.
    const uint32_t back = 1000 + 2 * GRACE_MS;
    assert_close(ha_tier_gate(t, true, back, GRACE_MS, 19.0f), 19.0f);
    assert(!t.expired);
    assert_close(ha_tier_gate(t, false, back + 10000, GRACE_MS, 19.0f), 19.0f);
    assert(std::isnan(ha_tier_gate(t, false, back + GRACE_MS + 1, GRACE_MS, 19.0f)));
  }

  void test_short_blip_does_not_expire()
  {
    // An HA restart shorter than the grace period never reaches NaN.
    HaTierTracker t;
    assert_close(ha_tier_gate(t, true, 0, GRACE_MS, 20.0f), 20.0f);
    assert_close(ha_tier_gate(t, false, 10000, GRACE_MS, 20.0f), 20.0f);
    assert_close(ha_tier_gate(t, false, 100000, GRACE_MS, 20.0f), 20.0f);
    assert_close(ha_tier_gate(t, true, 120000, GRACE_MS, 20.5f), 20.5f);
    assert_close(ha_tier_gate(t, false, 130000, GRACE_MS, 20.5f), 20.5f);
  }

  void test_nan_raw_passes_through()
  {
    HaTierTracker t;
    // HA `unavailable`/`unknown` reaches the gate as NaN and stays NaN, connected or not.
    assert(std::isnan(ha_tier_gate(t, true, 1000, GRACE_MS, NAN)));
    assert(std::isnan(ha_tier_gate(t, false, 2000, GRACE_MS, NAN)));
    // ... and does not poison the tracker: the next good value is passed.
    assert_close(ha_tier_gate(t, true, 3000, GRACE_MS, 21.0f), 21.0f);
  }

  void test_millis_wraparound()
  {
    // Last connected shortly before the uint32 wrap; samples straddle it.
    HaTierTracker t;
    const uint32_t before_wrap = 0xFFFFFF00u;
    assert_close(ha_tier_gate(t, true, before_wrap, GRACE_MS, 21.5f), 21.5f);
    // 0x100 ms to the wrap + 1000 ms after: 1256 ms elapsed, inside grace.
    assert_close(ha_tier_gate(t, false, 1000, GRACE_MS, 21.5f), 21.5f);
    // Exactly at the grace boundary across the wrap: still trusted ...
    assert_close(ha_tier_gate(t, false, static_cast<uint32_t>(before_wrap + GRACE_MS), GRACE_MS, 21.5f), 21.5f);
    // ... one ms later: expired.
    assert(std::isnan(ha_tier_gate(t, false, static_cast<uint32_t>(before_wrap + GRACE_MS + 1), GRACE_MS, 21.5f)));
  }

  void test_expiry_survives_a_full_counter_wrap()
  {
    // A disconnect that outlasts the whole ~49.7 day millis() period must not make
    // (now - last_connected) small again and resurrect the frozen value: the latch holds.
    HaTierTracker t;
    assert_close(ha_tier_gate(t, true, 5000, GRACE_MS, 21.5f), 21.5f);
    assert(std::isnan(ha_tier_gate(t, false, 5000 + GRACE_MS + 1, GRACE_MS, 21.5f)));
    // now - last == 2^32 + 100 ms (mod 2^32 -> 100 ms): looks fresh without the latch.
    assert(std::isnan(ha_tier_gate(t, false, 5000 + 100, GRACE_MS, 21.5f)));
    assert(t.expired);
  }

} // namespace

int main()
{
  test_connected_passes_raw();
  test_boot_before_any_client_is_closed();
  test_disconnected_within_grace_passes_raw();
  test_disconnected_past_grace_is_nan();
  test_reconnect_restores_raw();
  test_short_blip_does_not_expire();
  test_nan_raw_passes_through();
  test_millis_wraparound();
  test_expiry_survives_a_full_counter_wrap();
  return 0;
}
