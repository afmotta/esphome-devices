---
status: done
epic: 2
story: 2
story_key: 2-2-per-button-package-5-event-types-via-on-multi-click
baseline_commit: 74aa3f4f987e4363247f17f91f9e0ce7f517cfc0
---

# Story 2.2: Per-button package - 5 event types via on_multi_click

Status: done

## Story

As a developer,
I want `common/button.yaml` to detect all 5 button event types and transmit the correct CAN frame on each event,
so that any button press produces a well-formed CAN frame on the bus using protocol header helpers only.

## Acceptance Criteria

1. `firmware/common/button.yaml` implements exactly 5 event types via `on_multi_click`: single click, double click, triple click, long press (1-3 s), extra-long press (3+ s)
2. Pattern order is longest-first: triple -> double -> single -> long -> extra-long
3. Event handlers use `can_id(CAT_INPUT, ${node_id})` and `button_payload(${button_index}, EVT_*, ${room_id}, ${board_id})`
4. No raw bit shifts, magic hex values, or inline integer literals in lambdas
5. Package stays parameterized with `button_index` and `button_gpio`
6. `esphome compile firmware/nodes/node100.yaml` succeeds
7. `esphome compile firmware/nodes/node101.yaml` succeeds

## Tasks / Subtasks

- [x] Task 1: Implement and verify all 5 `on_multi_click` patterns in `firmware/common/button.yaml` (AC: 1, 2)
- [x] Task 2: Wire frame construction to `canbus_protocol.h` helpers only (AC: 3, 4)
- [x] Task 3: Confirm package parameterization remains reusable across buttons and nodes (AC: 5)
- [x] Task 4: Run compile gates for node100 and node101 (AC: 6, 7)

### Review Findings

- [x] [Review][Patch] Stale `input_can_id` substitutions still declared in node100.yaml and node101.yaml — `button.yaml` no longer references `${input_can_id}` but both node files still declare it; silent but misleads future maintainers about the CAN ID computation path [firmware/nodes/node100.yaml, firmware/nodes/node101.yaml]
- [x] [Review][Defer] Long/extra-long press share exact 3s boundary — ESPHome always fires long, never extra-long at exactly 3s [firmware/common/button.yaml] — deferred, pre-existing
- [x] [Review][Defer] Single-click can fire during slow double-click (0.3–0.4s inter-press gap overlaps single's ≥0.3s OFF threshold) [firmware/common/button.yaml] — deferred, pre-existing
- [x] [Review][Defer] `send_data()` return value silently discarded — TX failures on a busy bus produce no log output [firmware/common/button.yaml] — deferred, pre-existing
- [x] [Review][Defer] node_id ≥ 512 silently produces colliding CAN IDs via `can_id()` 9-bit mask; constrained to 0–399 by generate_nodes.py validation [firmware/common/canbus_protocol.h] — deferred, pre-existing

## Dev Notes

- Keep protocol logic centralized in `firmware/common/canbus_protocol.h`.
- Ensure event string semantics remain compatible with gateway decoding expectations.
- Avoid introducing behavior that depends on future stories in the same epic.

## Dev Agent Record

### Agent Model Used

GPT-5.3-Codex

### Completion Notes List

- Replaced separate `canbus.send:` actions with single `lambda:` per event that calls `id(can0).send_data(can_id(CAT_INPUT, ${node_id}), false, button_payload(...))` directly — required because ESPHome's `canbus.send:can_id:` field is not templatable.
- Updated all 5 event handlers to use canonical EVT_* constant names: `EVT_TRIPLE_CLICK`, `EVT_DOUBLE_CLICK`, `EVT_CLICK`, `EVT_LONG_PRESS`, `EVT_EXTRA_LONG_PRESS`.
- Removed `${input_can_id}` dependency from button.yaml; CAN ID is now computed at runtime via `can_id(CAT_INPUT, ${node_id})`.
- All 5 patterns ordered longest-first (triple → double → single → long → extra-long) per ESPHome requirement.
- `esphome compile` succeeded for both node100 and node101 (ESPHome 2026.5.0, RP2040/rpipico, Arduino framework).

### File List

- _bmad-output/implementation-artifacts/2-2-per-button-package-5-event-types-via-on-multi-click.md
- firmware/common/button.yaml

## Change Log

- 2026-06-01: Implemented all 5 on_multi_click event types in button.yaml using id(can0).send_data(can_id(CAT_INPUT, ${node_id}), ...) and canonical EVT_* constants; compile gates passed for node100 and node101.
