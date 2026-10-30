#pragma once
#include <cmath>

// =============================================================================
// dew_point_interlock.h — hard low limit on radiant-cooling supply water (N-01)
// =============================================================================
// A floor's dew-point protection (ground-floor.yaml / first-floor.yaml) writes
// `supply_temp_minimum` = max room dew point + safe margin as the COOL target
// of the mixing-valve PID. A target is not a limit: the PID regulates the supply
// AROUND it, so an overshoot (or a bad tuning) takes the water below the
// minimum, and with a small margin below the dew point itself -- condensation
// on the floor, or dripping from the first floor's radiant CEILING.
//
// This interlock sits on the valve's cool-direction output, after the hp_mode
// gate (pid_direction.h), and forces it to 0 (no chilled water mixed in) when
// the supply gets too close to the dew point, independent of the PID:
//
//   trip    supply <  minimum - margin/2   (i.e. dew point + margin/2)
//   release supply >= minimum              (back at the protection target)
//
// The hysteresis band (margin/2) keeps the valve from chattering around the
// trip point; with the valve shut the loop recirculates and the supply warms
// back up to the minimum, where the PID takes over again.
//
// Fail-safe: a NaN supply, minimum or margin (no Dallas reading, no dew point
// known since boot, every member room's humidity lost) blocks -- cooling blind
// is the condensation risk this exists for, the same reasoning as a NaN zone
// closing its radiant valve (radiant_override.h, R-05). A negative margin is a
// misconfiguration and blocks too.
//
// Cadence: it is evaluated on every write the PID makes, i.e. on every supply
// sensor publish -- the same moment the PID itself can act on the water.
//
// `blocked` is the caller's latch (a bool `globals` per valve). Pure helper code
// with no ESPHome dependency, so it is native-testable
// (climate/tests/test_dew_point_interlock.cpp).
// =============================================================================

namespace dew_point_interlock
{

  // Advance the latch with one sample; true while chilled water must not flow.
  inline bool update(bool &blocked, float supply, float minimum, float margin)
  {
    if (std::isnan(supply) || std::isnan(minimum) || std::isnan(margin) || margin < 0.0f)
    {
      blocked = true;
      return blocked;
    }
    if (blocked)
    {
      if (supply >= minimum)
        blocked = false;
    }
    else if (supply < minimum - margin / 2.0f)
    {
      blocked = true;
    }
    return blocked;
  }

  // The level the valve's cool output forwards: `level` unless the interlock
  // holds, 0 otherwise. Always advances the latch, so it tracks the supply
  // even while the cool direction is gated off.
  inline float cool_level(bool &blocked, float supply, float minimum, float margin, float level)
  {
    return update(blocked, supply, minimum, margin) ? 0.0f : level;
  }

} // namespace dew_point_interlock
