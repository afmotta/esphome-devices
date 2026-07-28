// Formatting helpers and the button-event log for the on-device LVGL lighting UI
// (lighting/packages/ui/light_touch_ui.yaml). Header-only; included via the UI
// package's `esphome: includes:` the same way climate's touch_ui_format.h is.
//
// Deliberately free of LVGL and ESPHome types, matching climate's header:
// colours are chosen inline in the YAML lambdas via lv_color_hex(), and the
// relay tally is computed in YAML from relay_store(), so this stays compilable
// on its own.
#pragma once

#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

namespace light_ui {

// ---------------------------------------------------------------------------
// Button-event log
// ---------------------------------------------------------------------------
// The Buttons tab is the commissioning surface: you press a wall button and
// need to see which node/button/gesture the controller actually decoded. One
// "last event" line was not enough — a double-click arrives as click+click+
// double_click, and a hold as hold+hold_release, so the interesting part had
// already been overwritten by the time you looked up. Keeping a short history
// makes those sequences readable.
//
// Newest first, so row 0 is always the most recent press.
inline constexpr std::size_t BUTTON_LOG_MAX = 8;

struct BtnEvent {
  uint32_t node_id = 0;
  uint32_t button = 0;
  std::string event;  // event_type_str() spelling: "click", "hold", ...
  uint32_t ms = 0;    // millis() at capture, for the age column
};

// Header accessor rather than an ESPHome `globals:` entry: globals storage is
// emitted before user includes, so it cannot hold this type. Same shape as
// pending_acks_store() in ha_arbitration.h and relay_store() in relay_store.h.
inline std::vector<BtnEvent> &button_log_store() {
  static std::vector<BtnEvent> log;
  return log;
}

inline void button_log_push(uint32_t node_id, uint32_t button,
                            const std::string &event, uint32_t ms) {
  auto &log = button_log_store();
  if (log.capacity() < BUTTON_LOG_MAX)
    log.reserve(BUTTON_LOG_MAX);
  log.insert(log.begin(), BtnEvent{node_id, button, event, ms});
  if (log.size() > BUTTON_LOG_MAX)
    log.pop_back();
}

// nullptr for a row past the end of the log — the row fragments render those
// as blank rather than as a stale entry.
inline const BtnEvent *button_log_at(std::size_t i) {
  auto &log = button_log_store();
  return i < log.size() ? &log[i] : nullptr;
}

// ---------------------------------------------------------------------------
// Column formatters
// ---------------------------------------------------------------------------

// Gesture column. Abbreviated for the same reason climate's state_text() is
// four characters: "double_click" and "hold_release" are ~90px of a 480px-wide
// panel that also has to fit a node name, and the node name is what you are
// actually reading.
inline std::string gesture_short(const std::string &event) {
  if (event == "click") return "1x";
  if (event == "double_click") return "2x";
  if (event == "triple_click") return "3x";
  if (event == "hold") return "hold";
  if (event == "hold_release") return "rel";
  return "?";
}

// Button column: "btn3".
inline std::string fmt_button_col(uint32_t button) {
  char buf[12];
  std::snprintf(buf, sizeof(buf), "btn%u", (unsigned) button);
  return std::string(buf);
}

// Age column, one unit and no decimals: "4s", "47s", "12m", "3h", "2d".
inline std::string fmt_age(uint32_t age_s) {
  char buf[12];
  if (age_s < 60)
    std::snprintf(buf, sizeof(buf), "%us", (unsigned) age_s);
  else if (age_s < 3600)
    std::snprintf(buf, sizeof(buf), "%um", (unsigned) (age_s / 60));
  else if (age_s < 86400)
    std::snprintf(buf, sizeof(buf), "%uh", (unsigned) (age_s / 3600));
  else
    std::snprintf(buf, sizeof(buf), "%ud", (unsigned) (age_s / 86400));
  return std::string(buf);
}

// Home tab's one-line summary of the newest press: "Last  Cucina btn3 1x  12s".
// The no-events-yet case is handled by the caller, which has to null-check
// button_log_at(0) anyway.
inline std::string fmt_last_button(const char *name, uint32_t button,
                                   const std::string &event, uint32_t age_s) {
  char buf[72];
  std::snprintf(buf, sizeof(buf), "Last  %s btn%u %s  %s", name,
                (unsigned) button, gesture_short(event).c_str(),
                fmt_age(age_s).c_str());
  return std::string(buf);
}

}  // namespace light_ui
