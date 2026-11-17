#pragma once
#include <cstdint>
#include <cstring>

// =============================================================================
// seasonal_demand.h — demand tier of the seasonal mode coordinator
// =============================================================================
// Decides whether the shoulder-season demand tier of
// climate/packages/coordinators/seasonal_mode.yaml may move hp_mode. One call
// to step() per coordinator check (check_interval, 1 min by default).
//
// Inputs are the two house-wide aggregates "some zone wants heat" / "some zone
// wants cool" (any_zone_wants_heat/_cool, built from each PID's _wants_heat /
// _wants_cool: room temperature beyond the setpoint by a deadband, see
// pid_direction::wants). They are deliberately NOT the PIDs' actions: every
// zone PID is OFF while hp_mode is SANITARY_ONLY, so an action-based demand
// could never leave that mode.
//
// Rules (review 2026-11-10, finding 1):
//   - Conflict (heat AND cool wanted) and no demand both mean "leave hp_mode
//     alone" and restart the confirmation. The heat pump serves one kind of
//     water house-wide, so a mixed house has no right answer; the old
//     if/else-if chain answered by flipping HEAT <-> COOL on every check.
//   - A single-sided demand must persist for `confirm_checks` consecutive
//     checks before it counts (a door left open, a setpoint nudged and put
//     back).
//   - No demand-driven change within `min_dwell_checks` checks of the last
//     hp_mode change, whoever made it (operator, calendar, this tier): the
//     emitters are slow and the source takes time to change over.
//
// Pure helper code with no ESPHome dependency, so it is native-testable
// (climate/tests/test_seasonal_demand.cpp).
// =============================================================================

namespace seasonal_demand
{

  enum class Target
  {
    NONE, // leave hp_mode alone
    HEAT,
    COOL
  };

  struct State
  {
    uint16_t heat_streak = 0;        // consecutive checks with heat-only demand
    uint16_t cool_streak = 0;        // consecutive checks with cool-only demand
    uint16_t checks_since_change = 0; // checks since the last hp_mode change (saturating)
  };

  // The coordinator's one State. A header accessor instead of an ESPHome
  // `globals:` entry: ESPHome declares globals before the `esphome: includes:`
  // headers are visible, so a global cannot have a type from this header (same
  // pattern as canbus' pending_acks_store). One seasonal_mode coordinator per
  // device, so one instance is enough.
  inline State &state()
  {
    static State instance;
    return instance;
  }

  inline void bump(uint16_t &counter)
  {
    if (counter < UINT16_MAX)
      ++counter;
  }

  // hp_mode changed (any cause): restart the dwell and the confirmation.
  inline void on_mode_changed(State &state) { state = State{}; }

  // Advance the dwell clock by one check. Call on EVERY coordinator check,
  // also while the demand tier is held off, so the dwell reflects real time.
  inline void tick(State &state) { bump(state.checks_since_change); }

  // The demand tier is not allowed to act on this check (manual hold, tier
  // disabled, calendar lock, no valid time): drop the confirmation so stale
  // streaks cannot fire the moment it is released.
  inline void idle(State &state)
  {
    state.heat_streak = 0;
    state.cool_streak = 0;
  }

  // One demand-tier evaluation. Returns the mode to switch to, or NONE.
  inline Target step(State &state, bool wants_heat, bool wants_cool, const char *hp_mode,
                     uint16_t confirm_checks, uint16_t min_dwell_checks)
  {
    if (wants_heat == wants_cool)
    {
      idle(state);
      return Target::NONE;
    }
    uint16_t &streak = wants_heat ? state.heat_streak : state.cool_streak;
    (wants_heat ? state.cool_streak : state.heat_streak) = 0;
    bump(streak);

    const char *wanted = wants_heat ? "HEAT" : "COOL";
    if (hp_mode != nullptr && std::strcmp(hp_mode, wanted) == 0)
      return Target::NONE;
    if (streak < confirm_checks || state.checks_since_change < min_dwell_checks)
      return Target::NONE;
    return wants_heat ? Target::HEAT : Target::COOL;
  }

} // namespace seasonal_demand
