---
status: todo
epic: 2
story: 3
story_key: 2-3-node-heartbeat-and-can-frame-receive-lambda-safety
baseline_commit: 74aa3f4f987e4363247f17f91f9e0ce7f517cfc0
---

# Story 2.3: Node heartbeat and CAN frame receive lambda safety

Status: todo

## Story

As a developer,
I want each node to emit a heartbeat frame every 30 seconds and for all CAN frame lambdas to include the mandatory size guard,
so that node aliveness is observable and malformed frames are dropped safely.

## Acceptance Criteria

1. Heartbeat is transmitted every 30 seconds with CAN ID `can_id(CAT_STATUS, ${node_id})`
2. Heartbeat payload is 8 bytes and matches PRD layout: byte0 `PROTO_V1`, byte1 `MSG_HEARTBEAT`, byte2 uptime hours, byte3 button states bitmask, byte4 error flags, byte5 `room_id`, byte6 `board_id`, byte7 `0x00`
3. Heartbeat error flags set bit0 for TX error/timeout and bit1 for bus-off; `0x00` when healthy
4. Every CAN `on_frame` receive lambda in node and gateway starts with `if (x.size() < CAN_FRAME_SIZE) return;`
5. Size guard uses `CAN_FRAME_SIZE` constant, not inline numeric literals
6. `esphome compile firmware/nodes/node100.yaml` and `esphome compile firmware/nodes/node101.yaml` succeed
7. node100 and node101 can be flashed successfully via USB

## Tasks / Subtasks

- [ ] Task 1: Implement periodic heartbeat in `firmware/common/base_node.yaml` (AC: 1, 2, 3)
- [ ] Task 2: Ensure frame-size guard pattern is present in all CAN receive lambdas (AC: 4, 5)
- [ ] Task 3: Run compile gates for both PoC nodes (AC: 6)
- [ ] Task 4: Flash both nodes and confirm deployability (AC: 7)

## Dev Notes

- Use `CAN_FRAME_SIZE` from `firmware/common/canbus_protocol.h` for safety guards.
- Keep heartbeat payload mapping aligned with the PRD and gateway-side decode assumptions.
- This story depends on Story 2.1 and Story 2.2 outputs, but must not introduce dependencies on future epic stories.

## Dev Agent Record

### Agent Model Used

GPT-5.3-Codex

### Completion Notes List

- Pending implementation.

### File List

- _bmad-output/implementation-artifacts/2-3-node-heartbeat-and-can-frame-receive-lambda-safety.md
