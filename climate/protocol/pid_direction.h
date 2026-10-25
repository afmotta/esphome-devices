#pragma once
#include <cstring>

// =============================================================================
// pid_direction.h — heat/cool direction gating for PID-driven actuators
// =============================================================================
// ESPHome's `pid` climate does not use its HEAT/COOL mode to pick an output:
// PIDClimate::write_output_() (esphome/components/pid/pid_climate.cpp, 2026.8.0)
// only special-cases OFF, and otherwise routes value > 0 to heat_output and
// value < 0 to cool_output (as -value). In this house heat_output and
// cool_output end up on the SAME physical actuator (one radiant valve, one
// mixing valve, one fancoil 0-10V channel), so an ungated PID drives the
// actuator with |error| — a room above target in winter opens its valve.
//
// The fix gates each direction on the WATER the heat pump is producing right
// now (hp_mode, climate/packages/coordinators/seasonal_mode.yaml): the heat
// direction may actuate only while hp_mode == "HEAT", the cool direction only
// while hp_mode == "COOL" ("SANITARY_ONLY" produces neither, so both are held
// at 0). Each actuator gets two template float outputs, one wired to the PID's
// heat_output and one to its cool_output; each forwards through
// pid_direction::gated_level() to the shared stage.
//
// Why this is correct for every write order. write_output_(value) issues
//   1. cool_output.set_level(0)   if value >= 0
//   2. heat_output.set_level(0)   if value <= 0
//   3. cool_output.set_level(-value) if value < 0   } at most one of these two
//   4. heat_output.set_level(value)  if value > 0   } runs, and always last
// so the sequence ends with the one nonzero write (or only zeroing writes).
// gated_level() returns either the level or 0, so the shared stage sees only
// zeros plus, at most, that last write forwarded unchanged or as 0:
//   - the nonzero write's direction is active   -> final level = |value|
//   - the nonzero write's direction is inactive -> final level = 0
// The zeroing writes can never leave a stale nonzero level behind because they
// always precede the last write and a zero is forwarded as a zero by BOTH
// directions. The PID's own `action`/is_heating/is_cooling diagnostics are not
// gated on purpose: they report the controller's intent, which the seasonal
// demand-driven mode selection relies on.
//
// Pump demand must follow what the valves actually do, not the intent: the
// circulation pumps are demanded by each PID's `_is_active` binary sensor
// (climate/packages/components/pid_sensors.yaml), and a room above target in
// HEAT season reports action == COOLING while its gated valve stays shut — a
// pump against closed valves. actuating() is that sensor's rule: the PID's
// action counts only while the matching direction passes the gate.
//
// Pure helper code with no ESPHome dependency, so it is native-testable
// (climate/tests/test_pid_direction.cpp); the YAML lambdas in
// climate/packages/components/{heat_only_radiant,radiant,mixing_pump,fancoil}*.yaml
// only call into this header.
// =============================================================================

namespace pid_direction
{

  enum class Direction
  {
    HEAT,
    COOL
  };

  // True when the heat pump currently produces the water this direction needs.
  // `hp_mode` is the seasonal select's current option; anything other than the
  // exact option text (including nullptr) deactivates both directions.
  inline bool is_active(Direction direction, const char *hp_mode)
  {
    if (hp_mode == nullptr)
      return false;
    return std::strcmp(hp_mode, direction == Direction::HEAT ? "HEAT" : "COOL") == 0;
  }

  // The level a gated output forwards to the shared actuator stage: its own
  // level when its direction is active, 0 otherwise.
  inline float gated_level(Direction direction, const char *hp_mode, float level)
  {
    return is_active(direction, hp_mode) ? level : 0.0f;
  }

  // True when a PID whose action is heating/cooling is really moving water: the
  // heating action needs the heat direction active, the cooling action the cool
  // direction. Takes the two action flags (not the ESPHome enum) to stay free of
  // ESPHome headers; at most one is ever true, both false means idle/off.
  inline bool actuating(bool action_is_heating, bool action_is_cooling, const char *hp_mode)
  {
    return (action_is_heating && is_active(Direction::HEAT, hp_mode)) ||
           (action_is_cooling && is_active(Direction::COOL, hp_mode));
  }

  // ---------------------------------------------------------------------------
  // Integral windup bounds (review R-13)
  // ---------------------------------------------------------------------------
  // ESPHome's PIDController::calculate_integral_term_() accumulates
  // error * dt * ki on EVERY sensor update — "irrespective of current mode"
  // (pid_climate.cpp update_pid_) — and clamps it to [min_integral, max_integral]
  // (default -1..1). The accumulator already includes ki, so the bounds are in
  // OUTPUT units (the actuator span 0..1), independent of ki.
  //
  // Symmetric bounds let the direction the heat pump is NOT producing wind up
  // to a full actuator span: a room above target on a winter afternoon drives
  // the integral to -1 (cool side, gated shut), and once the room drops below
  // target the PID output stays <= 0 until the integral has crawled back up,
  // at ki * error per second. Likewise a cool-only fancoil that is OFF all
  // winter (room below target) sits at +1 when the season flips.
  //
  // The integral may therefore only represent demand in the direction the
  // water flows right now: HEAT -> [0, limit], COOL -> [-limit, 0]. This needs
  // no per-loop knowledge: heat-only, cool-only and dual loops all behave
  // correctly because a loop that cannot act in the active direction is simply
  // OFF. Its accumulator still tracks the (clamped) error while OFF, and it is
  // clamped to 0 on the next update after a season flip — the integral of the
  // old season is dropped without an explicit reset, while a re-published
  // identical hp_mode (HA, restore) leaves a legitimate integral alone.
  //
  // SANITARY_ONLY (or an unknown option / nullptr) produces neither direction
  // but is not a season of its own; it can be brief and must not wipe the
  // steady-state offset a loop has learned, so it returns false and the caller
  // keeps the previous bounds.
  inline bool integral_bounds(const char *hp_mode, float limit, float &min_integral, float &max_integral)
  {
    if (is_active(Direction::HEAT, hp_mode))
    {
      min_integral = 0.0f;
      max_integral = limit;
      return true;
    }
    if (is_active(Direction::COOL, hp_mode))
    {
      min_integral = -limit;
      max_integral = 0.0f;
      return true;
    }
    return false;
  }

} // namespace pid_direction
