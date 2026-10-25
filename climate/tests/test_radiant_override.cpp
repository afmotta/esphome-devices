#include <cmath>
#include <cstdio>

#include "radiant_override.h"

// =============================================================================
// Native test for radiant_override.h (climate R-05: override beat the NaN stop)
// =============================================================================
// The final stage of a radiant zone must (1) pass the PID level through when no
// override is set, (2) command the override level when it is, and (3) command 0
// whenever the room temperature is NaN — even with an override on, because the
// PID's "sensor lost => 0" used to be overridden. holds_open() (the floor pump
// demand input) must agree with (2)/(3).
//
// CHECK keeps working under -DNDEBUG (a bare assert() would silently vanish).
// =============================================================================

namespace
{

  int failures = 0;

#define CHECK(cond)                                                                   \
  do                                                                                  \
  {                                                                                   \
    if (!(cond))                                                                      \
    {                                                                                 \
      std::fprintf(stderr, "%s:%d: CHECK failed: %s\n", __FILE__, __LINE__, #cond);   \
      ++failures;                                                                     \
    }                                                                                 \
  } while (0)

  const float NaN = std::nanf("");
  constexpr float TEMP = 24.0f;

  bool near(float a, float b)
  {
    return std::fabs(a - b) < 0.0001f;
  }

  void test_no_override_passes_the_pid_level()
  {
    CHECK(near(radiant_override::final_level(false, 0.0f, TEMP, 0.4f), 0.4f));
    CHECK(near(radiant_override::final_level(false, 100.0f, TEMP, 0.0f), 0.0f));
    CHECK(near(radiant_override::final_level(false, 100.0f, TEMP, 1.0f), 1.0f));
  }

  void test_override_replaces_the_pid_level()
  {
    // The override wins in both directions: it can open a valve the PID wants
    // shut (boost) and shut one the PID wants open.
    CHECK(near(radiant_override::final_level(true, 100.0f, TEMP, 0.0f), 1.0f));
    CHECK(near(radiant_override::final_level(true, 40.0f, TEMP, 0.9f), 0.4f));
    CHECK(near(radiant_override::final_level(true, 0.0f, TEMP, 0.9f), 0.0f));
  }

  void test_override_value_is_clamped_and_nan_safe()
  {
    CHECK(near(radiant_override::final_level(true, 250.0f, TEMP, 0.0f), 1.0f));
    CHECK(near(radiant_override::final_level(true, -10.0f, TEMP, 0.9f), 0.0f));
    CHECK(near(radiant_override::final_level(true, NaN, TEMP, 0.9f), 0.0f));
  }

  void test_sensor_loss_closes_the_valve_whatever_the_override_says()
  {
    for (bool override_on : {false, true})
    {
      for (float pct : {0.0f, 40.0f, 100.0f, NaN})
      {
        for (float written : {0.0f, 0.5f, 1.0f})
        {
          CHECK(near(radiant_override::final_level(override_on, pct, NaN, written), 0.0f));
        }
      }
    }
  }

  void test_holds_open_follows_the_commanded_level()
  {
    CHECK(radiant_override::holds_open(true, 100.0f, TEMP));
    CHECK(radiant_override::holds_open(true, 1.0f, TEMP));
    // Switch on but value 0: the valve is commanded shut, no demand.
    CHECK(!radiant_override::holds_open(true, 0.0f, TEMP));
    CHECK(!radiant_override::holds_open(true, NaN, TEMP));
    // Override off: the PID owns the valve and the PID's own demand input applies.
    CHECK(!radiant_override::holds_open(false, 100.0f, TEMP));
    // Blind zone: valve forced closed, so no pump demand.
    CHECK(!radiant_override::holds_open(true, 100.0f, NaN));
  }

  void test_holds_open_agrees_with_final_level()
  {
    for (bool override_on : {false, true})
    {
      for (float pct : {0.0f, 10.0f, 100.0f, NaN})
      {
        for (float temp : {TEMP, NaN})
        {
          const bool open = radiant_override::final_level(override_on, pct, temp, 0.0f) > 0.0f;
          CHECK(radiant_override::holds_open(override_on, pct, temp) == (override_on && open));
        }
      }
    }
  }

} // namespace

int main()
{
  test_no_override_passes_the_pid_level();
  test_override_replaces_the_pid_level();
  test_override_value_is_clamped_and_nan_safe();
  test_sensor_loss_closes_the_valve_whatever_the_override_says();
  test_holds_open_follows_the_commanded_level();
  test_holds_open_agrees_with_final_level();
  if (failures != 0)
  {
    std::fprintf(stderr, "%d check(s) failed\n", failures);
    return 1;
  }
  std::puts("radiant_override: all checks passed");
  return 0;
}
