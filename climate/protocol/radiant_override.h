#pragma once
#include <algorithm>
#include <cmath>

// =============================================================================
// radiant_override.h — final-stage rule of a radiant zone (override vs PID)
// =============================================================================
// Every radiant zone ends in one "final stage" output
// (${room_slug}_radiant_output in heat_only_radiant.yaml) that drives the slow
// PWM of the zone valve. It is fed by the direction-gated PID outputs
// (pid_direction.h) AND directly by the fancoil_boost coordinator, and it
// honours the zone's override: with the override switch on, the override value
// (0-100 %) is the valve level and the PID is ignored. The boost coordinator
// holds the valve at 100 % through exactly this switch; HA can use it by hand.
//
// Sensor loss (review R-05). The PID writes 0 when the room temperature is NaN
// ("sensor lost => shut down"), but an active override used to win over that 0
// and keep the valve at its override level indefinitely. The override is a
// convenience on top of the control loop, not a safety bypass, so a zone whose
// temperature is NaN is forced closed whatever the override says:
//   - cooling: the room dew point is derived from the same sensors, so a blind
//     zone held open is a condensation risk the dew-point protection can no
//     longer judge;
//   - the override switch itself is left untouched (it is restored across
//     reboots and the sensor is NaN until its first reading), so the valve
//     simply returns to the override level when the sensor comes back.
//
// Pump demand. The circulation pump of a floor follows the zones whose valves
// are open. A valve held open by an override has no PID action behind it, so
// the floor demand sums need holds_open() as a second input per zone
// (`${room_slug}_radiant_override_active`, exposed by heat_only_radiant.yaml).
// holds_open() is derived from final_level() so the demand can never disagree
// with what the valve is commanded to do.
//
// Pure helper code with no ESPHome dependency, so it is native-testable
// (climate/tests/test_radiant_override.cpp).
// =============================================================================

namespace radiant_override
{

  // Level (0-1) the final stage commands, given the override switch/value, the
  // zone's room temperature and the level written to the stage (PID or direct).
  inline float final_level(bool override_on, float override_pct, float room_temperature, float written_level)
  {
    if (std::isnan(room_temperature))
      return 0.0f;
    if (!override_on)
      return written_level;
    // An unset (NaN) override value commands nothing rather than something random.
    if (std::isnan(override_pct))
      return 0.0f;
    return std::min(1.0f, std::max(0.0f, override_pct / 100.0f));
  }

  // True while the override is what keeps the zone valve open (pump demand).
  inline bool holds_open(bool override_on, float override_pct, float room_temperature)
  {
    return override_on && final_level(true, override_pct, room_temperature, 0.0f) > 0.0f;
  }

} // namespace radiant_override
