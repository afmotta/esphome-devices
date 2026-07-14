// Formatting helpers for the on-device LVGL climate UI
// (climate/packages/ui/climate_touch_ui.yaml). Header-only; included via the UI
// package's `esphome: includes:` the same way the CAN receiver headers are.
#pragma once

#include <string>
#include <cmath>
#include <cstdio>

namespace climate_ui {

// One zone row: "<name>  <temp>C  <heat|cool|idle>" (temp shown as "--" on NaN,
// i.e. the emergency failover tier). Fixed-width name padding keeps columns
// roughly aligned even though the LVGL Montserrat font is proportional.
inline std::string fmt_zone(const char *name, float temp, bool heating, bool cooling) {
  const char *state = heating ? "heat" : (cooling ? "cool" : "idle");
  char buf[56];
  if (std::isnan(temp)) {
    std::snprintf(buf, sizeof(buf), "%-16s   --   %s", name, state);
  } else {
    std::snprintf(buf, sizeof(buf), "%-16s %4.1fC  %s", name, temp, state);
  }
  return std::string(buf);
}

}  // namespace climate_ui
