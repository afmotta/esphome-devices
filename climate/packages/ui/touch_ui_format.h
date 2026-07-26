// Formatting helpers for the on-device LVGL climate UI
// (climate/packages/ui/climate_touch_ui.yaml). Header-only; included via the UI
// package's `esphome: includes:` the same way the CAN receiver headers are.
//
// Deliberately free of LVGL types: colours are chosen inline in the YAML
// lambdas via lv_color_hex(), so this header stays compilable without the LVGL
// headers and testable on its own.
#pragma once

#include <cstddef>
#include <string>
#include <cmath>
#include <cstdio>

namespace climate_ui {

// Current temperature for a zone row's temp column: "21.3C", or "--" when the
// reading is NAN (the emergency failover tier).
inline std::string fmt_temp(float temp) {
  if (std::isnan(temp)) return "--";
  char buf[16];
  std::snprintf(buf, sizeof(buf), "%.1fC", temp);
  return std::string(buf);
}

// A zone row's action column. Kept to four characters so the column stays
// narrow on a 480px-wide panel that has to fit eight rows.
inline std::string state_text(bool heating, bool cooling) {
  if (heating) return "heat";
  if (cooling) return "cool";
  return "idle";
}

// Setpoint row for the floor tabs' adjust control: "<name>  set <target>C".
inline std::string fmt_setpoint(const char *name, float target) {
  char buf[48];
  if (std::isnan(target)) {
    std::snprintf(buf, sizeof(buf), "%s  set --", name);
  } else {
    std::snprintf(buf, sizeof(buf), "%s  set %.1fC", name, target);
  }
  return std::string(buf);
}

// One float with NaN shown as "--" (setpoint column, dew-point diagnostics).
inline std::string fmt_or_dashes(float v) {
  if (std::isnan(v)) return "--";
  char buf[16];
  std::snprintf(buf, sizeof(buf), "%.1f", v);
  return std::string(buf);
}

// Tally of which failover tier each zone's temperature is currently coming
// from. `emergency` counts zones on neither CAN nor HA — i.e. running blind.
struct TierCounts {
  int can = 0;
  int ha = 0;
  int emergency = 0;
};

// A tier string is empty before the failover component has published for the
// first time; those zones are counted as emergency so a controller that never
// heard from a zone at boot does not read as healthy.
inline TierCounts count_tiers(const std::string *tiers, std::size_t n) {
  TierCounts c;
  for (std::size_t i = 0; i < n; i++) {
    if (tiers[i] == "CAN") {
      c.can++;
    } else if (tiers[i] == "HA") {
      c.ha++;
    } else {
      c.emergency++;
    }
  }
  return c;
}

}  // namespace climate_ui
