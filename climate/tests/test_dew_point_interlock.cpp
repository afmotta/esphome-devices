#include <cmath>
#include <cstdio>

#include "dew_point_interlock.h"

// =============================================================================
// Native test for dew_point_interlock.h (review N-01: the dew-point "minimum"
// was only a PID target, nothing stopped the supply water going below it)
// =============================================================================
// With minimum 20 and margin 2 (dew point 18): the cool output passes through
// above 19, is forced to 0 below 19, and stays at 0 until the supply is back at
// 20. Any NaN input (or a negative margin) blocks.
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
  constexpr float MIN = 20.0f;
  constexpr float MARGIN = 2.0f;

  void test_supply_above_the_trip_point_passes_the_level()
  {
    bool blocked = false;
    CHECK(dew_point_interlock::cool_level(blocked, 25.0f, MIN, MARGIN, 0.7f) == 0.7f);
    CHECK(!blocked);
    // Between trip (19) and minimum (20): still passing, the PID owns this band.
    CHECK(dew_point_interlock::cool_level(blocked, 19.5f, MIN, MARGIN, 0.4f) == 0.4f);
    CHECK(dew_point_interlock::cool_level(blocked, 19.0f, MIN, MARGIN, 0.4f) == 0.4f);
    CHECK(!blocked);
  }

  void test_supply_below_the_trip_point_blocks()
  {
    bool blocked = false;
    CHECK(dew_point_interlock::cool_level(blocked, 18.9f, MIN, MARGIN, 1.0f) == 0.0f);
    CHECK(blocked);
  }

  void test_release_needs_the_supply_back_at_the_minimum()
  {
    bool blocked = false;
    dew_point_interlock::update(blocked, 18.0f, MIN, MARGIN);
    CHECK(blocked);
    // Hysteresis: back above the trip point is not enough.
    CHECK(dew_point_interlock::cool_level(blocked, 19.5f, MIN, MARGIN, 1.0f) == 0.0f);
    CHECK(dew_point_interlock::cool_level(blocked, 19.99f, MIN, MARGIN, 1.0f) == 0.0f);
    CHECK(blocked);
    CHECK(dew_point_interlock::cool_level(blocked, 20.0f, MIN, MARGIN, 1.0f) == 1.0f);
    CHECK(!blocked);
  }

  void test_rising_minimum_trips_without_a_supply_change()
  {
    // The room dew point rises while the supply stays put.
    bool blocked = false;
    CHECK(!dew_point_interlock::update(blocked, 21.0f, MIN, MARGIN));
    CHECK(dew_point_interlock::update(blocked, 21.0f, 23.0f, MARGIN));
  }

  void test_any_nan_blocks()
  {
    bool blocked = false;
    CHECK(dew_point_interlock::update(blocked, NaN, MIN, MARGIN));
    blocked = false;
    CHECK(dew_point_interlock::update(blocked, 25.0f, NaN, MARGIN));
    blocked = false;
    CHECK(dew_point_interlock::update(blocked, 25.0f, MIN, NaN));
    // ...and a NaN-latched block releases like any other once data is back.
    CHECK(!dew_point_interlock::update(blocked, 25.0f, MIN, MARGIN));
  }

  void test_negative_margin_blocks()
  {
    bool blocked = false;
    CHECK(dew_point_interlock::update(blocked, 25.0f, MIN, -1.0f));
  }

  void test_zero_level_stays_zero()
  {
    bool blocked = false;
    CHECK(dew_point_interlock::cool_level(blocked, 25.0f, MIN, MARGIN, 0.0f) == 0.0f);
    CHECK(!blocked);
  }

} // namespace

int main()
{
  test_supply_above_the_trip_point_passes_the_level();
  test_supply_below_the_trip_point_blocks();
  test_release_needs_the_supply_back_at_the_minimum();
  test_rising_minimum_trips_without_a_supply_change();
  test_any_nan_blocks();
  test_negative_margin_blocks();
  test_zero_level_stays_zero();
  if (failures != 0)
  {
    std::fprintf(stderr, "%d check(s) failed\n", failures);
    return 1;
  }
  std::puts("dew_point_interlock: all checks passed");
  return 0;
}
