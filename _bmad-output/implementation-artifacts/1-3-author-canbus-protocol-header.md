---
status: done
epic: 1
story: 3
story_key: 1-3-author-canbus-protocol-header
baseline_commit: e841ae1bc6ffe03a19bf09303b3ca602135a3825
---

# Story 1.3: Author `canbus_protocol.h` from scratch

Status: done

## Story

As a developer,
I want a complete `canbus_protocol.h` authored from scratch per the PRD wire specification,
so that all CAN frame construction and decoding across both node and gateway firmware uses a single, verified source of truth with no magic numbers.

## Acceptance Criteria

1. `firmware/common/canbus_protocol.h` defines all of the following with no omissions:
   - `PROTO_V1 = 0x01`
   - `CAT_INPUT`, `CAT_STATUS` (category bits for the 11-bit CAN ID)
   - `MSG_BUTTON_EVENT`, `MSG_HEARTBEAT`
   - `EVT_CLICK`, `EVT_DOUBLE_CLICK`, `EVT_TRIPLE_CLICK`, `EVT_LONG_PRESS`, `EVT_EXTRA_LONG_PRESS`
   - `CAN_FRAME_SIZE = 8`
   - `inline uint32_t can_id(uint8_t category, uint16_t node_id)` — constructs 11-bit CAN ID
   - `inline std::vector<uint8_t> button_payload(uint8_t button_index, uint8_t event_type, uint8_t room_id, uint8_t board_id)` — builds 8-byte button event payload per PRD byte layout
   - `inline std::string event_type_str(uint8_t event_type)` — maps EVT_* values to human-readable strings: `"click"`, `"double_click"`, `"triple_click"`, `"long_press"`, `"extra_long_press"`
2. All functions are marked `inline`
3. All constants use `UPPER_SNAKE_CASE`; all functions use `snake_case`
4. Header includes `#pragma once` guard
5. The header compiles without errors or warnings when included in a minimal ESPHome YAML compiled under the `rp2040` platform
6. The header compiles without errors or warnings when included in a minimal ESPHome YAML compiled under the `esp32` / `esp-idf` platform
7. No raw hex values, magic numbers, or bit shifts appear in any YAML lambda — all such logic lives exclusively in this header

## Tasks / Subtasks

- [x] Task 1: Write `firmware/common/canbus_protocol.h` from scratch (AC: 1–4)
  - [x] Add `#pragma once` header guard
  - [x] Add required `#include <vector>`, `#include <string>`, `#include <cstdint>`
  - [x] Define all constants: `PROTO_V1`, `CAT_INPUT`, `CAT_STATUS`, `MSG_BUTTON_EVENT`, `MSG_HEARTBEAT`, all `EVT_*`, `CAN_FRAME_SIZE`
  - [x] Define `inline uint32_t can_id(uint8_t category, uint16_t node_id)`
  - [x] Define `inline std::vector<uint8_t> button_payload(uint8_t button_index, uint8_t event_type, uint8_t room_id, uint8_t board_id)`
  - [x] Define `inline std::string event_type_str(uint8_t event_type)` — return type MUST be `std::string`, not `const char*`
- [x] Task 2: Compile under rp2040 platform (AC: 5)
  - [x] Create a minimal test node YAML that includes the header and run `esphome compile`
  - [x] Confirm zero errors and zero warnings
- [x] Task 3: Compile under esp32/esp-idf platform (AC: 6)
  - [x] Create a minimal test gateway YAML that includes the header and run `esphome compile`
  - [x] Confirm zero errors and zero warnings

### Review Findings

- [x] [Review][Patch] `event_type_str` `std::string` return breaks `%s` format specifiers in gateway.yaml — `ESP_LOGI` (line 132) and `snprintf` (line 146) pass `std::string` to `%s` variadic args; UB on both platforms. Fix: append `.c_str()` at both call sites. [`firmware/gateway.yaml:132,146`]
- [x] [Review][Patch] Self-check logs misleading "protocol self-check" only when check FAILS — message gives no pass/fail indication. Fix: log "protocol self-check FAIL" in the error branch or invert condition to log success. [`firmware/test-node.yaml:10`, `firmware/test-gateway.yaml:10`]
- [x] [Review][Patch] `heartbeat_payload` uses `room`/`board` param names; `button_payload` uses `room_id`/`board_id` — inconsistent naming for the same logical fields. Fix: rename `heartbeat_payload` params to `room_id`/`board_id`. [`firmware/common/canbus_protocol.h`]
- [x] [Review][Patch] test-gateway uses `CAT_STATUS` CAN ID with `button_payload` — semantically inverts the protocol (button events use `CAT_INPUT`). Fix: change `can_id(CAT_STATUS, 1)` to `can_id(CAT_INPUT, 1)`. [`firmware/test-gateway.yaml:11`]
- [x] [Review][Patch] Heartbeat room/board decoding fixed — added heartbeat-specific payload decoders and switched the gateway heartbeat handler to use them. [`firmware/common/canbus_protocol.h`, `firmware/gateway.yaml`]
- [x] [Review][Decision] `button_index` remains enforced at the generator/config layer — Epic 1 does not define a wire-level invalid-button encoding, so no runtime mutation was added inside `button_payload`. [`firmware/common/canbus_protocol.h`, `firmware/generate_nodes.py`]
- [x] [Review][Patch] Header constants promoted from `static const` to `inline constexpr` for safer multi-TU use. [`firmware/common/canbus_protocol.h`]

## Dev Notes

### CRITICAL: The Existing File Is Non-Authoritative

`docs/esphome_canbus/common/canbus_protocol.h` (now at `firmware/common/canbus_protocol.h` after Story 1.1) EXISTS but **MUST be treated as a reference only, not as the authoritative implementation** (FR-4.1 explicitly states this). It contains several deviations from the PRD spec that must be corrected:

| Issue             | Existing File                                                          | Required by PRD                                                                  |
| ----------------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Missing constant  | ❌ No `CAN_FRAME_SIZE`                                                  | ✅ `CAN_FRAME_SIZE = 8` required                                                  |
| Wrong EVT names   | `EVT_DOUBLE`, `EVT_TRIPLE`, `EVT_LONG`, `EVT_EXTRA_LONG`               | `EVT_DOUBLE_CLICK`, `EVT_TRIPLE_CLICK`, `EVT_LONG_PRESS`, `EVT_EXTRA_LONG_PRESS` |
| Wrong return type | `event_type_str` returns `const char*`                                 | Must return `std::string`                                                        |
| Extra constants   | Has `CAT_SYSTEM`, `CAT_OUTPUT`, `MSG_CONFIG_WRITE`, etc.               | Fine to keep — not prohibited                                                    |
| Extra functions   | Has `heartbeat_payload`, `payload_*` decoders, `can_id_category`, etc. | Fine to keep — not prohibited                                                    |

**The corrected file may retain the extra constants and functions from the existing version — they are not wrong, just not explicitly required by the PRD.** The three issues above MUST be fixed.

### Required Constant and Function Definitions

**Exact constant values from the PRD wire spec:**

```cpp
#pragma once
#include <vector>
#include <string>
#include <cstdint>

// Protocol version
inline constexpr uint8_t PROTO_V1 = 0x01;

// Category bits (bits 10:9 of 11-bit CAN ID)
inline constexpr uint8_t CAT_INPUT  = 1;   // node → gateway (button events)
inline constexpr uint8_t CAT_STATUS = 3;   // node → gateway (heartbeat)

// Message types (payload byte 1)
inline constexpr uint8_t MSG_BUTTON_EVENT = 0x01;
inline constexpr uint8_t MSG_HEARTBEAT    = 0x01;  // same value, distinguished by CAN ID category

// Frame size — MUST be a named constant, never inline integer literal
inline constexpr uint8_t CAN_FRAME_SIZE = 8;

// Button event types (payload byte 3)
inline constexpr uint8_t EVT_CLICK            = 0x01;
inline constexpr uint8_t EVT_DOUBLE_CLICK     = 0x02;
inline constexpr uint8_t EVT_TRIPLE_CLICK     = 0x03;
inline constexpr uint8_t EVT_LONG_PRESS       = 0x04;
inline constexpr uint8_t EVT_EXTRA_LONG_PRESS = 0x05;
```

**Required payload byte layout (from PRD wire spec):**

Button event frame (8 bytes):

```
Byte 0: PROTO_V1       (protocol version)
Byte 1: MSG_BUTTON_EVENT
Byte 2: button_index   (0-5)
Byte 3: event_type     (EVT_*)
Byte 4: room_id        (0-255)
Byte 5: board_id       (0-255)
Byte 6: 0x00           (reserved)
Byte 7: 0x00           (reserved)
```

So `button_payload` must return: `{PROTO_V1, MSG_BUTTON_EVENT, button_index, event_type, room_id, board_id, 0x00, 0x00}`

**`event_type_str` return type MUST be `std::string`** (the gateway lambda assigns it to a `std::string` local variable):

```cpp
inline std::string event_type_str(uint8_t event_type) {
    switch (event_type) {
        case EVT_CLICK:            return "click";
        case EVT_DOUBLE_CLICK:     return "double_click";
        case EVT_TRIPLE_CLICK:     return "triple_click";
        case EVT_LONG_PRESS:       return "long_press";
        case EVT_EXTRA_LONG_PRESS: return "extra_long_press";
        default:                   return "unknown";
    }
}
```

**`can_id` function** — category occupies bits 10:9, node_id occupies bits 8:0:

```cpp
inline uint32_t can_id(uint8_t category, uint16_t node_id) {
    return ((uint32_t)(category & 0x03) << 9) | (node_id & 0x1FF);
}
```

### Platform Compatibility Notes

This header must compile under two incompatible toolchains:

- **RP2040 (nodes):** GCC for ARM Cortex-M0+, C++17, `rp2040` platform in ESPHome
- **ESP32-S3 (gateway):** GCC via esp-idf, C++17, `esp-idf` framework in ESPHome

Both support `std::vector`, `std::string`, `#pragma once`. No platform-specific includes or `#ifdef` guards are needed for the required API. `to_string()` is NOT used in this header (it's used in lambdas where needed).

### Downstream Impact — Constant Renames

The EVT_* renames break the existing `button.yaml` and `base_node.yaml`:

- `EVT_TRIPLE` → `EVT_TRIPLE_CLICK`
- `EVT_DOUBLE` → `EVT_DOUBLE_CLICK`
- `EVT_LONG` → `EVT_LONG_PRESS`

**These files are rewritten in Stories 2.1 and 2.2** using the new names. Do NOT update `button.yaml` or `base_node.yaml` in this story — that is out of scope. The existing files will temporarily not compile (with the new header) until Story 2.2 fixes them. This is acceptable since compile gates are per-story.

### Compile Verification Approach

To satisfy AC #5 and AC #6 without modifying the existing `base_node.yaml` or `button.yaml` (which use the old EVT_ names), create **minimal test YAMLs** that include only the header:

**Minimal rp2040 test YAML:**

```yaml
esphome:
  name: test-node
  includes:
    - common/canbus_protocol.h

rp2040:
  board: rpipico

logger:
  level: INFO
```

**Minimal esp32/esp-idf test YAML:**

```yaml
esphome:
  name: test-gateway
  includes:
    - common/canbus_protocol.h

esp32:
  variant: esp32s3
  framework:
    type: esp-idf

logger:
  baud_rate: 0
```

Run from `firmware/`:

```bash
esphome compile test-node.yaml
esphome compile test-gateway.yaml
```

These minimal YAMLs are temporary scaffolding — they can be deleted after the compile gate passes.

### Lambda Safety Reminder (for later stories)

This header defines `CAN_FRAME_SIZE = 8`. Every `on_frame` lambda in both nodes and gateway **MUST** start with:

```cpp
if (x.size() < CAN_FRAME_SIZE) return;
```

This constant being defined here is what makes that pattern possible. Do not add `on_frame` handlers to any YAML without this guard.

### References

- [Source: epics.md#Story 1.3] — exact AC including required constants and function signatures
- [Source: architecture.md#Protocol Constants Pattern] — correct vs wrong patterns
- [Source: architecture.md#Lambda Safety Pattern] — why `CAN_FRAME_SIZE` must be a named constant
- [Source: architecture.md#Gateway on_frame Handler Pattern] — shows `event_type_str` used as std::string
- [Source: docs/esphome_canbus/common/canbus_protocol.h] — existing reference (non-authoritative)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- `git rev-parse HEAD` → baseline commit `e841ae1bc6ffe03a19bf09303b3ca602135a3825`
- `esphome compile test-node.yaml` → success on `rp2040` (ESPHome 2025.12.5)
- `esphome compile test-gateway.yaml` → success on `esp32` / `esp-idf` (ESPHome 2025.12.5)
- `python3 _bmad/scripts/tests/test_resolve_customization.py` → pass
- `python3 .claude/skills/bmad-customize/scripts/tests/test_list_customizable_skills.py` → pass

### Completion Notes List

- Authored the shared protocol header in `firmware/common/canbus_protocol.h` with the required PRD API: `CAN_FRAME_SIZE`, `can_id(...)`, `button_payload(...)`, and `std::string event_type_str(...)`.
- Promoted the PRD-aligned event constant names (`EVT_DOUBLE_CLICK`, `EVT_TRIPLE_CLICK`, `EVT_LONG_PRESS`, `EVT_EXTRA_LONG_PRESS`) and kept compatibility aliases for older packages still using the legacy names.
- Added heartbeat-specific payload decoders and updated the gateway heartbeat handler so room/board bytes are decoded from the heartbeat layout instead of the button layout.
- Promoted the shared protocol constants from `static const` to `inline constexpr` after verifying both ESPHome toolchains compile the header cleanly.
- Added minimal `rp2040` and `esp32` compile fixtures to prove the header compiles cleanly under both required ESPHome toolchains.
- Validated the story with both ESPHome compile checks plus the repo's existing Python unittest scripts.

### File List

- `_bmad-output/implementation-artifacts/1-3-author-canbus-protocol-header.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `firmware/common/canbus_protocol.h`
- `firmware/test-gateway.yaml`
- `firmware/test-node.yaml`

### Change Log

- `2026-06-01`: Authored the shared CAN protocol header API, added dual-platform compile fixtures, and validated the repo tests.
- `2026-06-01`: Deferred-work follow-up fixed heartbeat room/board decoding and promoted protocol constants to `inline constexpr`.
