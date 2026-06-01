---
status: done
epic: 2
story: 1
story_key: 2-1-base-node-configuration-spi-and-mcp2515-setup
baseline_commit: 74aa3f4f987e4363247f17f91f9e0ce7f517cfc0
---

# Story 2.1: Base node configuration - SPI and MCP2515 setup

Status: done

## Story

As a developer,
I want `common/base_node.yaml` to configure the SPI bus and MCP2515 CAN controller with the verified hardware pin assignments,
so that the node's CAN hardware is correctly initialized and ready to transmit frames.

## Acceptance Criteria

1. `firmware/common/base_node.yaml` configures `spi:` with the verified CANBed RP2040 SPI pin mapping
2. `firmware/common/base_node.yaml` configures `canbus:` with platform `mcp2515`, `cs_pin`, `bit_rate: 125kbps`, and `clock` matching OQ-3; Story notes document that OQ-2 `int_pin` is hardware-verified but not configurable via ESPHome 2025.12.5 `canbus.mcp2515`
3. The node platform remains `rp2040` with board `rpipico`
4. Node isolation is enforced: no `wifi:`, no `api:`, no `ota:`, no `web_server:`
5. Substitution variables `${node_id}`, `${room_id}`, `${board_id}` are declared and used in the shared package
6. `esphome compile firmware/nodes/node100.yaml` succeeds

## Tasks / Subtasks

- [x] Task 1: Update `firmware/common/base_node.yaml` with verified SPI and MCP2515 settings (AC: 1, 2, 3)
- [x] Task 2: Verify node-isolation constraints in base node package (AC: 4)
- [x] Task 3: Validate substitutions and references (`node_id`, `room_id`, `board_id`) (AC: 5)
- [x] Task 4: Run compile gate for PoC node config (AC: 6)

### Review Findings

- [x] [Review][Patch] Update AC2 wording to match supported ESPHome MCP2515 options and explicitly document `int_pin` limitation [firmware/common/base_node.yaml:1]
- [x] [Review][Defer] `can_int_pin` substitution is generated but currently unused in base node package [firmware/nodes/node100.yaml:25] — deferred, pre-existing

## Dev Notes

- Hardware verification values are documented in `firmware/README.md` (OQ-1/OQ-2/OQ-3).
- Keep all protocol constants and helpers in `firmware/common/canbus_protocol.h`; avoid magic values in YAML lambdas.
- This story should not modify generated files under `firmware/nodes/` directly.

## Dev Agent Record

### Agent Model Used

GPT-5.3-Codex

### Completion Notes List

- Confirmed shared base package keeps RP2040 node platform assumptions intact and preserves SPI mapping through substitutions (`can_clk_pin`, `can_mosi_pin`, `can_miso_pin`) with MCP2515 at 125KBPS and 16MHZ clock.
- Verified node isolation constraints: no `wifi`, `api`, `ota`, or `web_server` declarations in base package and node file.
- Validated required substitutions `${node_id}`, `${room_id}`, `${board_id}` are referenced in `firmware/common/base_node.yaml` and declared in `firmware/nodes/node100.yaml`.
- Compile gate passed: `esphome compile firmware/nodes/node100.yaml`.
- Additional regression compile passed: `esphome compile firmware/nodes/node101.yaml`.
- Note on AC2 wording: ESPHome 2025.12.5 `canbus.mcp2515` supports `cs_pin` and `clock`, but does not expose an `int_pin` option; attempting `int_pin` fails config validation.

### File List

- firmware/common/base_node.yaml
- _bmad-output/implementation-artifacts/2-1-base-node-configuration-spi-and-mcp2515-setup.md

### Change Log

- 2026-06-01: Completed Story 2.1 implementation and validation. Updated base node MCP2515 configuration notes, verified isolation/substitutions, and passed compile gates for node100/node101.
