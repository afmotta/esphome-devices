#include <cstdio>
#include <cstring>
#include <string>

#include "seasonal_demand.h"

// =============================================================================
// Native test for seasonal_demand.h (review 2026-11-10, finding 1: the demand
// tier flipped HEAT <-> COOL on every check with mixed demand and had no
// confirmation or dwell)
// =============================================================================
// Drives step()/tick()/on_mode_changed() the way seasonal_mode.yaml does: one
// tick + one step per coordinator check, on_mode_changed whenever the select
// publishes. CONFIRM = 3 checks, DWELL = 5 checks throughout.
//
// CHECK keeps working under -DNDEBUG (a bare assert() would silently vanish).
// =============================================================================

namespace
{

  using seasonal_demand::State;
  using seasonal_demand::Target;

  constexpr uint16_t CONFIRM = 3;
  constexpr uint16_t DWELL = 5;

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

  // The coordinator around the pure rule: a mode plus the per-check sequence.
  struct House
  {
    State state;
    std::string mode = "SANITARY_ONLY";
    int changes = 0;

    void set_mode(const char *option)
    {
      mode = option;
      ++changes;
      seasonal_demand::on_mode_changed(state);
    }

    // One coordinator check with the demand tier allowed to act.
    Target check(bool heat, bool cool)
    {
      seasonal_demand::tick(state);
      Target target = seasonal_demand::step(state, heat, cool, mode.c_str(), CONFIRM, DWELL);
      if (target != Target::NONE)
        set_mode(target == Target::HEAT ? "HEAT" : "COOL");
      return target;
    }

    // One coordinator check with the tier held off (hold, disabled, lock).
    void held_check()
    {
      seasonal_demand::tick(state);
      seasonal_demand::idle(state);
    }

    void run(int checks, bool heat, bool cool)
    {
      for (int i = 0; i < checks; ++i)
        check(heat, cool);
    }
  };

  House settled(const char *mode)
  {
    House house;
    house.set_mode(mode);
    house.changes = 0;
    for (int i = 0; i < 20; ++i)
      house.held_check(); // dwell long over, no streaks
    return house;
  }

  void test_leaves_sanitary_only_on_confirmed_demand()
  {
    House house = settled("SANITARY_ONLY");
    CHECK(house.check(true, false) == Target::NONE);
    CHECK(house.check(true, false) == Target::NONE);
    CHECK(house.check(true, false) == Target::HEAT); // third consecutive check
    CHECK(house.mode == "HEAT");

    house = settled("SANITARY_ONLY");
    house.run(CONFIRM, false, true);
    CHECK(house.mode == "COOL" && house.changes == 1);
  }

  void test_no_demand_changes_nothing()
  {
    for (const char *mode : {"HEAT", "COOL", "SANITARY_ONLY"})
    {
      House house = settled(mode);
      house.run(50, false, false);
      CHECK(house.changes == 0 && house.mode == mode);
    }
  }

  void test_mixed_demand_never_flips()
  {
    // The old chain alternated HEAT/COOL on every check here.
    for (const char *mode : {"HEAT", "COOL", "SANITARY_ONLY"})
    {
      House house = settled(mode);
      house.run(200, true, true);
      CHECK(house.changes == 0 && house.mode == mode);
    }
  }

  void test_demand_for_the_current_mode_is_a_no_op()
  {
    House house = settled("HEAT");
    house.run(50, true, false);
    CHECK(house.changes == 0);
    house = settled("COOL");
    house.run(50, false, true);
    CHECK(house.changes == 0);
  }

  void test_interrupted_demand_restarts_the_confirmation()
  {
    House house = settled("HEAT");
    house.run(CONFIRM - 1, false, true);
    house.check(false, false); // demand gone for one check
    house.run(CONFIRM - 1, false, true);
    CHECK(house.changes == 0);
    house.check(false, true);
    CHECK(house.mode == "COOL");

    // A conflict and the opposite demand interrupt it too.
    house = settled("SANITARY_ONLY");
    house.run(CONFIRM - 1, true, false);
    house.check(true, true);
    house.run(CONFIRM - 1, true, false);
    CHECK(house.changes == 0);
    house.check(false, true); // opposite side: heat streak dropped, cool streak 1
    house.run(CONFIRM - 1, true, false);
    CHECK(house.changes == 0);
  }

  void test_dwell_after_any_mode_change()
  {
    // Operator (or calendar) just set HEAT: cool demand must wait out the dwell,
    // even though it is confirmed long before.
    House house;
    house.set_mode("HEAT");
    house.changes = 0;
    house.run(DWELL - 1, false, true);
    CHECK(house.changes == 0);
    house.check(false, true);
    CHECK(house.mode == "COOL" && house.changes == 1);

    // The tier's own change restarts the dwell: an immediate opposite demand
    // cannot bounce it back before DWELL checks.
    house.run(DWELL - 1, true, false);
    CHECK(house.mode == "COOL" && house.changes == 1);
    house.check(true, false);
    CHECK(house.mode == "HEAT" && house.changes == 2);
  }

  void test_dwell_runs_while_held_but_streaks_do_not()
  {
    House house;
    house.set_mode("HEAT");
    house.changes = 0;
    for (int i = 0; i < DWELL + 10; ++i)
      house.held_check(); // e.g. manual hold on, demand present all along
    // Released: the dwell is over, but the confirmation starts from zero.
    house.run(CONFIRM - 1, false, true);
    CHECK(house.changes == 0);
    house.check(false, true);
    CHECK(house.mode == "COOL");
  }

  void test_counters_saturate()
  {
    State state;
    state.checks_since_change = UINT16_MAX;
    state.heat_streak = UINT16_MAX;
    seasonal_demand::tick(state);
    CHECK(state.checks_since_change == UINT16_MAX);
    CHECK(seasonal_demand::step(state, true, false, "COOL", CONFIRM, DWELL) == Target::HEAT);
    CHECK(state.heat_streak == UINT16_MAX);
  }

  void test_unknown_mode_text()
  {
    // nullptr / unknown option: treated as "not the wanted mode".
    State state;
    state.checks_since_change = DWELL;
    state.heat_streak = CONFIRM;
    CHECK(seasonal_demand::step(state, true, false, nullptr, CONFIRM, DWELL) == Target::HEAT);
    CHECK(seasonal_demand::step(state, true, false, "heat", CONFIRM, DWELL) == Target::HEAT);
  }

} // namespace

int main()
{
  test_leaves_sanitary_only_on_confirmed_demand();
  test_no_demand_changes_nothing();
  test_mixed_demand_never_flips();
  test_demand_for_the_current_mode_is_a_no_op();
  test_interrupted_demand_restarts_the_confirmation();
  test_dwell_after_any_mode_change();
  test_dwell_runs_while_held_but_streaks_do_not();
  test_counters_saturate();
  test_unknown_mode_text();
  if (failures != 0)
  {
    std::fprintf(stderr, "%d check(s) failed\n", failures);
    return 1;
  }
  return 0;
}
