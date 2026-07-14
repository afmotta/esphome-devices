// Formatting helpers for the on-device LVGL lighting UI
// (lighting/packages/ui/light_touch_ui.yaml). Header-only; included via the UI
// package's `esphome: includes:` the same way climate's touch_ui_format.h is.
#pragma once

#include <string>
#include <cstdint>
#include <cstdio>

namespace light_ui {

// Relay-cell background colour: green when the coil is on, grey when off.
// ESPHome's Switch exposes no per-entity availability flag reachable from a
// lambda, so there is no distinct "unavailable" colour — a bank that stops
// updating on a Modbus timeout simply keeps its last-known colours (the "No
// connectivity status register" reality noted in climate/CLAUDE.md App. A).
inline uint32_t relay_rgb(bool on) {
  return on ? 0x2F6F4F : 0x2A2E33;
}

// Buttons-tab feed (multi-line): "<name>\nbutton N  <event>\n<age>s ago".
// Before the first press, a waiting placeholder.
inline std::string fmt_button(bool seen, const char *name, uint32_t button,
                              const std::string &event, uint32_t age_s) {
  if (!seen)
    return std::string("No button events yet");
  char buf[96];
  std::snprintf(buf, sizeof(buf), "%s\nbutton %u  %s\n%us ago", name,
                (unsigned) button, event.c_str(), (unsigned) age_s);
  return std::string(buf);
}

// Status-tab one-liner: "Last: <name> btnN <event>" (placeholder before any press).
inline std::string fmt_button_short(bool seen, const char *name, uint32_t button,
                                    const std::string &event) {
  if (!seen)
    return std::string("Last button: --");
  char buf[80];
  std::snprintf(buf, sizeof(buf), "Last: %s btn%u %s", name, (unsigned) button,
                event.c_str());
  return std::string(buf);
}

}  // namespace light_ui
