#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <cstring>
#include <vector>

#include "pid_direction.h"

// =============================================================================
// Native test for pid_direction.h (climate R-01: PID drove valves with |error|)
// =============================================================================
// Models the house wiring: two gated template outputs (one wired to the PID's
// heat_output, one to cool_output) forwarding into ONE shared actuator sink,
// driven by a faithful copy of ESPHome 2026.8.0's PIDClimate::write_output_()
// call sequence (esphome/components/pid/pid_climate.cpp):
//
//   if (supports_cool_() && value >= 0) cool_output_->set_level(0.0f);
//   if (supports_heat_() && value <= 0) heat_output_->set_level(0.0f);
//   if (supports_cool_() && value < 0)  cool_output_->set_level(min(1, -value));
//   if (supports_heat_() && value > 0)  heat_output_->set_level(min(1, value));
//
// supports_heat_()/supports_cool_() are "output pointer is wired", mirrored here
// by nullptr. The state the real components keep across calls (the sink level
// persists between PID updates) is kept too, so sequences of values are tested,
// not just single calls.
// =============================================================================

namespace
{

  using pid_direction::Direction;

  constexpr float EPS = 0.0001f;

  bool close(float a, float b)
  {
    return std::fabs(a - b) < EPS;
  }

  // The shared actuator stage (radiant `_radiant_output`, the analog valve
  // output, the fancoil 0-10V channel): remembers the last level written.
  struct Sink
  {
    float level = 0.0f;
    std::vector<float> writes; // every set_level, in order
    void set_level(float v)
    {
      level = v;
      writes.push_back(v);
    }
  };

  // A template float output whose write_action forwards through the gate —
  // exactly what the YAML lambdas do.
  struct GatedOutput
  {
    Direction direction;
    const char *const *hp_mode; // points at the live select option
    Sink *sink;
    void set_level(float level)
    {
      sink->set_level(pid_direction::gated_level(direction, *hp_mode, level));
    }
  };

  // Faithful copy of PIDClimate::write_output_() output routing (see header
  // comment for the source lines). Returns nothing: the action bookkeeping is
  // not part of the actuation path.
  void write_output(GatedOutput *heat_output, GatedOutput *cool_output, float value)
  {
    // first ensure outputs are off (both outputs not active at the same time)
    if (cool_output != nullptr && value >= 0)
      cool_output->set_level(0.0f);
    if (heat_output != nullptr && value <= 0)
      heat_output->set_level(0.0f);

    // value < 0 means cool, > 0 means heat
    if (cool_output != nullptr && value < 0)
      cool_output->set_level(std::min(1.0f, -value));
    if (heat_output != nullptr && value > 0)
      heat_output->set_level(std::min(1.0f, value));
  }

  // One actuator as wired in the YAML: roles pick which outputs exist.
  struct Actuator
  {
    const char *hp_mode = "HEAT";
    Sink sink;
    GatedOutput heat{Direction::HEAT, &hp_mode, &sink};
    GatedOutput cool{Direction::COOL, &hp_mode, &sink};
    bool has_heat;
    bool has_cool;

    Actuator(bool heat_wired, bool cool_wired) : has_heat(heat_wired), has_cool(cool_wired) {}

    void pid_update(float value)
    {
      write_output(has_heat ? &heat : nullptr, has_cool ? &cool : nullptr, value);
    }
  };

  constexpr const char *HP_MODES[] = {"HEAT", "COOL", "SANITARY_ONLY"};
  constexpr float PID_VALUES[] = {0.6f, -0.6f, 0.0f};

  // Expected final sink level for a dual-output actuator (radiant, mixing
  // valve, heat_cool fancoil): |value| iff the sign's direction matches the
  // water being produced, else 0.
  float expected_dual(const char *hp_mode, float value)
  {
    if (value > 0 && std::strcmp(hp_mode, "HEAT") == 0)
      return value;
    if (value < 0 && std::strcmp(hp_mode, "COOL") == 0)
      return -value;
    return 0.0f;
  }

  void test_predicate_exact_option_text_only()
  {
    assert(pid_direction::is_active(Direction::HEAT, "HEAT"));
    assert(!pid_direction::is_active(Direction::HEAT, "COOL"));
    assert(!pid_direction::is_active(Direction::HEAT, "SANITARY_ONLY"));
    assert(pid_direction::is_active(Direction::COOL, "COOL"));
    assert(!pid_direction::is_active(Direction::COOL, "HEAT"));
    assert(!pid_direction::is_active(Direction::COOL, "SANITARY_ONLY"));

    // Anything that is not the exact option fails closed in both directions.
    for (const char *odd : {"", "heat", "cool", "HEAT ", "HEAT_COOL", "OFF", "unknown"})
    {
      assert(!pid_direction::is_active(Direction::HEAT, odd));
      assert(!pid_direction::is_active(Direction::COOL, odd));
    }
    assert(!pid_direction::is_active(Direction::HEAT, nullptr));
    assert(!pid_direction::is_active(Direction::COOL, nullptr));
  }

  void test_gated_level_forwards_or_zeroes()
  {
    assert(close(pid_direction::gated_level(Direction::HEAT, "HEAT", 0.6f), 0.6f));
    assert(close(pid_direction::gated_level(Direction::HEAT, "COOL", 0.6f), 0.0f));
    assert(close(pid_direction::gated_level(Direction::COOL, "COOL", 0.6f), 0.6f));
    assert(close(pid_direction::gated_level(Direction::COOL, "SANITARY_ONLY", 0.6f), 0.0f));
    // A zero is a zero in every direction/mode: the PID's zeroing writes can
    // never leave a stale level.
    for (const char *mode : HP_MODES)
    {
      assert(close(pid_direction::gated_level(Direction::HEAT, mode, 0.0f), 0.0f));
      assert(close(pid_direction::gated_level(Direction::COOL, mode, 0.0f), 0.0f));
    }
  }

  // Radiant (heat_only + radiant cool), mixing valve, heat_cool fancoil: both
  // outputs wired to one sink.
  void test_dual_output_matrix()
  {
    for (const char *mode : HP_MODES)
    {
      for (float value : PID_VALUES)
      {
        Actuator a(true, true);
        a.hp_mode = mode;
        a.pid_update(value);
        assert(close(a.sink.level, expected_dual(mode, value)));
      }
    }

    // The two cases the bug got wrong, spelled out.
    {
      // Winter, room 5 degC over target: PID value is negative. Must not open.
      Actuator radiant(true, true);
      radiant.hp_mode = "HEAT";
      radiant.pid_update(-0.6f);
      assert(close(radiant.sink.level, 0.0f));
    }
    {
      // Summer, supply colder than the dew-point minimum: mixing-valve PID
      // value is positive (target - supply > 0). Must not open further.
      Actuator valve(true, true);
      valve.hp_mode = "COOL";
      valve.pid_update(0.6f);
      assert(close(valve.sink.level, 0.0f));
      // Supply warmer than the minimum: value negative, chilled valve opens.
      valve.pid_update(-0.6f);
      assert(close(valve.sink.level, 0.6f));
    }
  }

  // Value clamping happens in the PID (min(1, |value|)); the gate must pass the
  // clamped level through untouched.
  void test_saturated_value_passes_through()
  {
    Actuator a(true, true);
    a.hp_mode = "HEAT";
    a.pid_update(7.5f);
    assert(close(a.sink.level, 1.0f));
    a.hp_mode = "COOL";
    a.pid_update(-7.5f);
    assert(close(a.sink.level, 1.0f));
  }

  // The PID keeps running across updates and the sink keeps its last level, so
  // a stale nonzero level must be impossible for ANY value -> value transition
  // in ANY season (all ordered pairs, including repeated values).
  void test_no_stale_level_across_transitions()
  {
    constexpr float values[] = {0.6f, -0.6f, 0.0f, 1.0f, -1.0f, 0.25f, -0.25f};
    for (const char *mode : HP_MODES)
    {
      for (float first : values)
      {
        for (float second : values)
        {
          Actuator a(true, true);
          a.hp_mode = mode;
          a.pid_update(first);
          a.pid_update(second);
          assert(close(a.sink.level, expected_dual(mode, second)));
        }
      }
    }
  }

  // The nonzero write is always the LAST write of an update (this is what makes
  // the final level independent of the zeroing writes): check the recorded
  // order for the faithful copy.
  void test_write_order_matches_pid_source()
  {
    {
      Actuator a(true, true);
      a.hp_mode = "HEAT";
      a.pid_update(0.6f); // cool zero, then heat 0.6
      assert((a.sink.writes == std::vector<float>{0.0f, 0.6f}));
    }
    {
      Actuator a(true, true);
      a.hp_mode = "COOL";
      a.pid_update(-0.6f); // heat zero, then cool 0.6
      assert((a.sink.writes == std::vector<float>{0.0f, 0.6f}));
    }
    {
      Actuator a(true, true);
      a.hp_mode = "HEAT";
      a.pid_update(-0.6f); // heat zero, then cool 0.6 -> gated to 0
      assert((a.sink.writes == std::vector<float>{0.0f, 0.0f}));
    }
    {
      Actuator a(true, true);
      a.pid_update(0.0f); // both zeroing writes only
      assert((a.sink.writes == std::vector<float>{0.0f, 0.0f}));
    }
  }

  // Heat-only radiant (heat_only_radiant.yaml): only a heat output is wired, so
  // PIDClimate::supports_cool_() is false and value < 0 only zeroes the heat
  // output.
  void test_heat_only_radiant()
  {
    for (const char *mode : HP_MODES)
    {
      for (float value : PID_VALUES)
      {
        Actuator a(true, false);
        a.hp_mode = mode;
        a.pid_update(value);
        const float expected = (value > 0 && std::strcmp(mode, "HEAT") == 0) ? value : 0.0f;
        assert(close(a.sink.level, expected));
      }
    }
  }

  // Fancoil roles (fancoil.yaml / fancoil_role_*.yaml):
  //   cool_only, boost: only a cool output is wired.
  //   heat_cool:        both are wired (covered by the dual matrix above).
  // For the cool-only wiring a positive PID value (room colder than target)
  // must never actuate — that was the "fancoil heats the wrong way / runs when
  // too warm in winter" half of the bug.
  void test_fancoil_cool_only_wiring()
  {
    for (const char *mode : HP_MODES)
    {
      for (float value : PID_VALUES)
      {
        Actuator a(false, true);
        a.hp_mode = mode;
        a.pid_update(value);
        const float expected = (value < 0 && std::strcmp(mode, "COOL") == 0) ? -value : 0.0f;
        assert(close(a.sink.level, expected));
      }
    }

    // Winter, room too WARM (value < 0): the old wiring ran the fan at |error|.
    Actuator winter(false, true);
    winter.hp_mode = "HEAT";
    winter.pid_update(-0.6f);
    assert(close(winter.sink.level, 0.0f));
  }

  void test_fancoil_heat_cool_follows_season()
  {
    Actuator a(true, true); // sottotetto: heat_cool
    a.hp_mode = "HEAT";
    a.pid_update(0.6f); // too cold in winter -> heats
    assert(close(a.sink.level, 0.6f));
    a.pid_update(-0.6f); // too warm in winter -> no fan
    assert(close(a.sink.level, 0.0f));
    a.hp_mode = "COOL";
    a.pid_update(-0.6f); // too warm in summer -> cools
    assert(close(a.sink.level, 0.6f));
    a.pid_update(0.6f); // too cold in summer -> no fan
    assert(close(a.sink.level, 0.0f));
    a.hp_mode = "SANITARY_ONLY";
    a.pid_update(0.6f);
    assert(close(a.sink.level, 0.0f));
    a.pid_update(-0.6f);
    assert(close(a.sink.level, 0.0f));
  }

  // Season flips are NOT a write event: the sink holds its level until the next
  // PID update (sensor-driven). Pin the behaviour so a change is deliberate.
  void test_season_flip_holds_level_until_next_update()
  {
    Actuator a(true, true);
    a.hp_mode = "HEAT";
    a.pid_update(0.6f);
    assert(close(a.sink.level, 0.6f));
    a.hp_mode = "COOL";
    assert(close(a.sink.level, 0.6f)); // stale until the next update...
    a.pid_update(0.6f);
    assert(close(a.sink.level, 0.0f)); // ...which closes it
  }

  // Pump demand (pid_sensors.yaml `_is_active`): the PID's action counts only
  // while the matching direction passes the gate. Exhaustive over action x mode.
  void test_actuating_follows_the_gate()
  {
    for (const char *mode : HP_MODES)
    {
      const bool heat_ok = std::strcmp(mode, "HEAT") == 0;
      const bool cool_ok = std::strcmp(mode, "COOL") == 0;
      // idle/off action: never demands water
      assert(!pid_direction::actuating(false, false, mode));
      assert(pid_direction::actuating(true, false, mode) == heat_ok);
      assert(pid_direction::actuating(false, true, mode) == cool_ok);
    }
    // Winter, room over target (action COOLING): valve shut, so no pump.
    assert(!pid_direction::actuating(false, true, "HEAT"));
    // Winter, room under target (action HEATING): valve open, pump on.
    assert(pid_direction::actuating(true, false, "HEAT"));
    // Summer mirror image.
    assert(!pid_direction::actuating(true, false, "COOL"));
    assert(pid_direction::actuating(false, true, "COOL"));
    // No heating/cooling water: nothing is active whatever the PID wants.
    assert(!pid_direction::actuating(true, false, "SANITARY_ONLY"));
    assert(!pid_direction::actuating(false, true, "SANITARY_ONLY"));
    // Unknown / missing option fails closed, like the gate.
    for (const char *odd : {"", "heat", "HEAT ", "OFF"})
    {
      assert(!pid_direction::actuating(true, false, odd));
      assert(!pid_direction::actuating(false, true, odd));
    }
    assert(!pid_direction::actuating(true, false, nullptr));
    assert(!pid_direction::actuating(false, true, nullptr));
  }

  // The sensor and the valve must agree: for every wiring, season and PID value
  // the sensor is true exactly when the shared actuator ends up nonzero.
  void test_actuating_agrees_with_the_sink()
  {
    constexpr float values[] = {0.6f, -0.6f, 0.0f, 1.0f, -1.0f};
    for (const char *mode : HP_MODES)
    {
      for (float value : values)
      {
        for (int wiring = 0; wiring < 3; ++wiring) // dual, heat-only, cool-only
        {
          Actuator a(wiring != 2, wiring != 1);
          a.hp_mode = mode;
          a.pid_update(value);
          // ESPHome's action: COOLING for value < 0 if cool is wired, HEATING
          // for value > 0 if heat is wired (pid_climate.cpp write_output_()).
          const bool cooling = a.has_cool && value < 0;
          const bool heating = a.has_heat && value > 0;
          assert(pid_direction::actuating(heating, cooling, mode) == (a.sink.level > EPS));
        }
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Integral windup bounds (R-13)
  // ---------------------------------------------------------------------------

  // The accumulator of ESPHome 2026.8.0's PIDController::calculate_integral_term_
  // (esphome/components/pid/pid_controller.cpp), deadband off: add error*dt*ki,
  // then clamp to [min, max]. ki is inside the accumulator, so bounds are in
  // output units.
  struct Integrator
  {
    float acc = 0.0f;
    float lo = -1.0f; // ESPHome's defaults
    float hi = 1.0f;
    void step(float error, float dt, float ki)
    {
      acc += error * dt * ki;
      acc = std::min(std::max(acc, lo), hi);
    }
    void apply_season(const char *hp_mode, float limit)
    {
      float l, h;
      if (pid_direction::integral_bounds(hp_mode, limit, l, h))
      {
        lo = l;
        hi = h;
      }
    }
  };

  void test_integral_bounds_follow_the_water()
  {
    float lo = 99.0f, hi = 99.0f;
    assert(pid_direction::integral_bounds("HEAT", 1.0f, lo, hi));
    assert(close(lo, 0.0f) && close(hi, 1.0f));
    assert(pid_direction::integral_bounds("COOL", 1.0f, lo, hi));
    assert(close(lo, -1.0f) && close(hi, 0.0f));
    // The limit scales the active side only.
    assert(pid_direction::integral_bounds("HEAT", 0.4f, lo, hi));
    assert(close(lo, 0.0f) && close(hi, 0.4f));
    assert(pid_direction::integral_bounds("COOL", 0.4f, lo, hi));
    assert(close(lo, -0.4f) && close(hi, 0.0f));

    // Not a season: report "keep the old bounds" and leave the outputs alone.
    lo = 7.0f;
    hi = 8.0f;
    for (const char *mode : {"SANITARY_ONLY", "heat", "", "UNKNOWN"})
    {
      assert(!pid_direction::integral_bounds(mode, 1.0f, lo, hi));
      assert(close(lo, 7.0f) && close(hi, 8.0f));
    }
    assert(!pid_direction::integral_bounds(nullptr, 1.0f, lo, hi));
    assert(close(lo, 7.0f) && close(hi, 8.0f));
  }

  // A room above target all afternoon in HEAT season, then below target: the
  // old symmetric bounds left the integral at -1 (output <= 0 for minutes);
  // the HEAT bounds keep it at 0 so the P term heats at once.
  void test_no_winter_windup_on_the_gated_cool_side()
  {
    const float kp = 0.8f, ki = 0.005f, dt = 10.0f;
    for (bool bounded : {false, true})
    {
      Integrator i;
      if (bounded)
        i.apply_season("HEAT", 1.0f);
      for (int n = 0; n < 6 * 3600 / 10; n++) // six hours, 2 degC over target
        i.step(-2.0f, dt, ki);
      assert(close(i.acc, bounded ? 0.0f : -1.0f));
      // Room drops 0.5 degC below target.
      const float output = kp * 0.5f + i.acc;
      if (bounded)
        assert(output > 0.0f);
      else
        assert(output < 0.0f); // the bug: still no heat
    }
  }

  // The active direction keeps its full range (limit), and the integral of the
  // previous season is gone one update after the flip, without a reset call.
  void test_active_side_keeps_its_range_and_flip_drops_the_old_season()
  {
    const float ki = 0.005f;
    Integrator i;
    i.apply_season("HEAT", 1.0f);
    for (int n = 0; n < 1000; n++) // cold room for a long time
      i.step(+3.0f, 10.0f, ki);
    assert(close(i.acc, 1.0f)); // saturates at the limit, not beyond

    i.apply_season("HEAT", 1.0f); // identical re-publish: nothing is wiped
    i.step(0.0f, 10.0f, ki);
    assert(close(i.acc, 1.0f));

    i.apply_season("SANITARY_ONLY", 1.0f); // keeps the bounds, keeps the integral
    i.step(0.0f, 10.0f, ki);
    assert(close(i.acc, 1.0f));

    i.apply_season("COOL", 1.0f);
    i.step(0.0f, 10.0f, ki); // next sensor update
    assert(close(i.acc, 0.0f));
  }

} // namespace

int main()
{
  test_predicate_exact_option_text_only();
  test_gated_level_forwards_or_zeroes();
  test_dual_output_matrix();
  test_saturated_value_passes_through();
  test_no_stale_level_across_transitions();
  test_write_order_matches_pid_source();
  test_heat_only_radiant();
  test_fancoil_cool_only_wiring();
  test_fancoil_heat_cool_follows_season();
  test_season_flip_holds_level_until_next_update();
  test_actuating_follows_the_gate();
  test_actuating_agrees_with_the_sink();
  test_integral_bounds_follow_the_water();
  test_no_winter_windup_on_the_gated_cool_side();
  test_active_side_keeps_its_range_and_flip_drops_the_old_season();
  return 0;
}
