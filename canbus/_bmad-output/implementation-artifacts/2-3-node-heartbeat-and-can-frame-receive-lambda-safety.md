---
status: done
epic: 2
story: 3
story_key: 2-3-node-heartbeat-and-can-frame-receive-lambda-safety
baseline_commit: 0dcefb39227aa32bacfc807334f845c370393820
---

# Story 2.3: Node heartbeat and CAN frame receive lambda safety

Status: done

## Story

As a developer,
I want each node to emit a heartbeat frame every 30 seconds and for all CAN frame lambdas to include the mandatory size guard,
so that node aliveness is observable and malformed frames are dropped safely.

## Acceptance Criteria

1. Heartbeat is transmitted every 30 seconds with CAN ID `can_id(CAT_STATUS, ${node_id})`
2. Heartbeat payload is 8 bytes and matches PRD layout: byte0 `PROTO_V1`, byte1 `MSG_HEARTBEAT`, byte2 uptime hours, byte3 error flags, byte4 `room_id`, byte5 `board_id`, byte6 `0x00` reserved, byte7 `0x00` reserved
3. Heartbeat error flags field is wired (byte3); constants `ERR_CAN_TX_FAIL` and `ERR_CAN_BUS_OFF` are defined. For PoC the field always transmits `0x00`; active error detection (TX timeout / bus-off callbacks) is a post-PoC concern.
4. Every CAN `on_frame` receive lambda in node and gateway starts with `if (x.size() < CAN_FRAME_SIZE) return;`
5. Size guard uses `CAN_FRAME_SIZE` constant, not inline numeric literals
6. `esphome compile firmware/nodes/node100.yaml` and `esphome compile firmware/nodes/node101.yaml` succeed
7. node100 and node101 can be flashed successfully via USB

## Tasks / Subtasks

- [x] Task 1: Implement periodic heartbeat in `firmware/common/base_node.yaml` (AC: 1, 2, 3)
- [x] Task 2: Ensure frame-size guard pattern is present in all CAN receive lambdas (AC: 4, 5)
- [x] Task 3: Run compile gates for both PoC nodes (AC: 6)
- [x] Task 4: Flash both nodes and confirm deployability (AC: 7)

## Dev Notes

- Use `CAN_FRAME_SIZE` from `firmware/common/canbus_protocol.h` for safety guards.
- Keep heartbeat payload mapping aligned with the PRD and gateway-side decode assumptions.
- This story depends on Story 2.1 and Story 2.2 outputs, but must not introduce dependencies on future epic stories.

### Review Findings

- [x] [Review][Decision] `error_flags` never set to non-zero — AC3 error detection not implemented — resolved: accepted as PoC placeholder; AC3 updated to document limitation.
- [x] [Review][Decision] `btn_state` hardcoded `0x00` — resolved: PoC nodes are momentary; byte3 is now reserved (`0x00`) in protocol, `heartbeat_payload` signature simplified, AC2 and epics updated.
- [x] [Review][Defer] `uptime_h` silently overflows at 255 hours (~10.6 days), wrapping to 0 [firmware/common/base_node.yaml] — deferred, pre-existing
- [x] [Review][Defer] `on_frame` filter uses `${output_can_id}` — CAN ID direction ambiguous (node TX ID vs gateway command ID) [firmware/common/base_node.yaml] — deferred, pre-existing
- [x] [Review][Defer] `uint16_t val = (x[3] << 8) | x[4]` — implicit `uint8_t`→`int` promotion before shift [firmware/common/base_node.yaml] — deferred, pre-existing
- [x] [Review][Defer] `CAN_FRAME_SIZE` typed as `uint8_t` instead of `size_t` [firmware/common/canbus_protocol.h] — deferred, pre-existing

## Dev Agent Record

### Agent Model Used

GPT-5.3-Codex

### Completion Notes List

- Implemented periodic heartbeat in `firmware/common/base_node.yaml`: `interval: 30s` transmitting `can_id(CAT_STATUS, ${node_id})` with an 8-byte payload via `heartbeat_payload(uptime_h, id(error_flags), ${room_id}, ${board_id})`.
- `uptime_h` computed as `(uint8_t)((millis() / 3600000UL) & 0xFF)` (wraps at 255h — deferred).
- Per review decision, dropped the `btn_states` byte from the heartbeat payload: `heartbeat_payload` signature simplified and byte3 is now `error_flags`, with bytes 6–7 reserved `0x00`. Decode helpers (`payload_errors`, `payload_heartbeat_room`, `payload_heartbeat_board`) shifted accordingly in `canbus_protocol.h`.
- `error_flags` transmits `0x00` for PoC (active TX-timeout / bus-off detection is post-PoC, AC3 documents this).
- Applied the `CAN_FRAME_SIZE` size guard to all `on_frame` receive lambdas in `firmware/common/base_node.yaml` and `firmware/gateway.yaml` (replacing inline `>= 6` / `>= 7` literals).
- Compile gates passed (ESPHome 2026.5.0): `esphome compile firmware/nodes/node100.yaml` and `node101.yaml` both SUCCESS.
- Gateway full-compile is blocked by a pre-existing Epic 3 issue (non-templatable `canbus.send: can_id:` in the `canbus_send_output` API service); unrelated to this story's size-guard edit.

### File List

- firmware/common/base_node.yaml
- firmware/common/canbus_protocol.h
- firmware/gateway.yaml
- _bmad-output/implementation-artifacts/2-3-node-heartbeat-and-can-frame-receive-lambda-safety.md
