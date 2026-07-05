# Story 4.3: Button event acceptance matrix — node 101 (room 8, board 0) and PoC sign-off

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want all 5 button event types on node 101 to produce correctly decoded events in HA — with artifacts captured — completing the 10-combination matrix and the official PoC sign-off,
so that the full stack is validated with a repeatable, documented baseline before production hardware procurement.

## ⚠️ Critical Context — READ FIRST

**This is a HARDWARE VALIDATION + SIGN-OFF story, not a code-implementation story.** Two deliverables: (1) the node-101 half of the acceptance matrix captured as logged artifacts, and (2) the **PoC sign-off record** committed to `firmware/VALIDATION.md`. The only file this story *writes* is `firmware/VALIDATION.md` (new) plus artifact files under `validation/`. **No firmware changes are expected** — if one is needed to pass, that is an Epic 2/3 regression to raise, not patch here. [Source: epics.md#Story-4.3; sprint-status.yaml]

**This story is the LAST in Epic 4 and gates the PoC.** It depends on Story 4.2 being complete: the 5 node-100 artifacts must already exist under `validation/`. Together with the 5 node-101 artifacts produced here, that is the full **10-combination matrix (5 event types × 2 nodes)**. [Source: epics.md#Story-4.3; FR-9.5]

**"Node 101" = (room 8, board 0) under ADR-0001.** No flat `node_id`. The node's identity on the bus is **room=8, board=0** (`firmware/nodes/node-r8-b0.yaml`, "Ground floor living room"). The differentiator from node 100 is the **`room` field: `"8"` vs node 100's `"7"`** — this is exactly FR-9.4 ("each event's room value is distinct from node 100's value"). All node-101 evidence is keyed on `room=8`. [Source: ADR-0001; firmware/nodes.csv; firmware/nodes/node-r8-b0.yaml:15-16]

**Identity rides the CAN ID; the HA event has 4 string fields.** Same mechanics as Story 4.2: the gateway fires `esphome.canbus_button` with `room/board/button/event` each re-decoded from `can_id` via a per-field `!lambda`. Values are strings (`room:"8"`, never `8`). The button payload is `[PROTO_V1]` only. [Source: firmware/gateway.yaml:108-114; firmware/common/canbus_protocol.h:19-26,158-159]

**The sign-off record is a precise artifact, not prose.** `firmware/VALIDATION.md` must document: ESPHome version used, hardware confirmed (OQ-1/OQ-2/OQ-3 values), all 10 acceptance combinations verified with their artifact file locations, and the date of sign-off. Exact required values are listed in Task 4. [Source: epics.md#Story-4.3 final AC]

**Observation surface & gateway-log access:** identical to Story 4.2 — HA Developer Tools → Events → `esphome.canbus_button`, plus the gateway network log (`esphome logs firmware/gateway.yaml`) for the CAN-error watch and `Button R08B0 ...` secondary confirmation. USB serial is off (`logger: baud_rate: 0`); use the network stream. `level: DEBUG` is set. [Source: firmware/gateway.yaml:22-24,98-102]

## Acceptance Criteria

1. **AC1 — All 5 node-101 event types produce HA events (FR-9.2):** Triggering each of the 5 event types on node 101 (room 8, board 0) produces one corresponding `esphome.canbus_button` event in HA Developer Tools. All 5 observed. [Source: epics.md#Story-4.3]

2. **AC2 — `room` distinct from node 100 (FR-9.4):** Every node-101 event has `room` = `"8"`, distinct from node 100's `"7"`, confirming the two nodes are differentiated by location address. [Source: epics.md#Story-4.3; firmware/nodes.csv]

3. **AC3 — All fields correctly populated, none blank:** Each node-101 event's fields are exactly `room="8"`, `board="0"`, `button` = pressed button index as a decimal string (`"0"` for GPIO20, `"1"` for GPIO21), `event` = the correct event-type string; all four present and non-empty. [Source: epics.md#Story-4.3; firmware/common/canbus_protocol.h:185-202]

4. **AC4 — Node-101 evidence captured & committed:** The HA event log for all 5 node-101 combinations is captured as an artifact (screenshot or export) and committed under `validation/`. [Source: epics.md#Story-4.3; architecture.md:221-222]

5. **AC5 — All 10 artifacts present (FR-9.5, NFR-9):** The repository contains all 10 acceptance artifacts under `validation/` — 5 × node 100 (from Story 4.2) + 5 × node 101. [Source: epics.md#Story-4.3]

6. **AC6 — Zero CAN error frames across the run (FR-9.6):** The gateway ESPHome log shows zero CAN/TWAI error frames across the entire validation run. [Source: epics.md#Story-4.3; firmware/gateway.yaml:130-135; architecture.md:223]

7. **AC7 — PoC sign-off committed:** A PoC sign-off record is committed to `firmware/VALIDATION.md` documenting: ESPHome version used, hardware confirmed (OQ-1/OQ-2/OQ-3 values), all 10 acceptance combinations verified with artifact locations, and the date of sign-off. [Source: epics.md#Story-4.3]

## Tasks / Subtasks

- [x] **Task 1: Prerequisite & desk readiness checks (no hardware)** (AC: 1,2,3,5)
  - [x] 1.1: Confirm Story 4.2 is complete and the **5 node-100 artifacts already exist** under `validation/`. If they are missing, STOP — 4.3's "all 10 present" (AC5) cannot pass; finish 4.2 first. [sprint-status.yaml; validation/]
  - [x] 1.2: Confirm node 101 (`node-r8-b0`) is flashed (Epic 2 `done`) and present on the bench, and the gateway is connected to HA. Story 4.1 already verified node 101 heartbeats as `R08B0`. [4-1-...md AC3; firmware/nodes/node-r8-b0.yaml]
  - [x] 1.3: Record expected node-101 field values: `room="8"`, `board="0"`, `button="0"` (GPIO20, the matrix button) or `"1"` (GPIO21). Confirm `room="8"` is distinct from node 100's `"7"` (AC2). [firmware/nodes/node-r8-b0.yaml:15,40-41]
  - [x] 1.4: Re-confirm (verification only, do not modify) the gateway CAT_INPUT handler and `event_type_str` mapping — identical to Story 4.2. [firmware/gateway.yaml:88-114; firmware/common/canbus_protocol.h:185-202]

- [x] **Task 2: Arm observation surfaces & execute the 5-event matrix on node 101 (button 0 / GPIO20)** (AC: 1,2,3,6)
  - [x] 2.1: HA Developer Tools → Events → listen to `esphome.canbus_button`; start `esphome logs firmware/gateway.yaml` (DEBUG, network) for the CAN-error watch. [firmware/gateway.yaml:22-24]
  - [x] 2.2: Single click → expect `{room:"8", board:"0", button:"0", event:"click"}` + `Button R08B0 btn0 click` log.
  - [x] 2.3: Double click → `event:"double_click"`.
  - [x] 2.4: Triple click → `event:"triple_click"`.
  - [x] 2.5: Long press (hold 1–2.9 s) → `event:"long_press"`.
  - [x] 2.6: Extra-long press (hold ≥3 s) → `event:"extra_long_press"`.
  - [x] 2.7: For each, verify all four fields present, non-blank, `room="8"`, and equal to expected (AC2/AC3). Watch the gateway log for zero CAN errors throughout (AC6).

- [x] **Task 3: Capture node-101 evidence & verify the full matrix** (AC: 4,5)
  - [x] 3.1: Capture the HA Developer Tools event log showing all 5 node-101 combinations (screenshot and/or exported JSON). Save under `validation/` (e.g. `validation/node-r8-b0-button-matrix.png` / `.json`). Commit it. [architecture.md:221-222]
  - [x] 3.2: Verify `validation/` now holds all **10** artifacts (5 node 100 + 5 node 101). List them; if any of the 10 is missing or unreadable, AC5 fails — re-capture before signing off. [epics.md#Story-4.3 FR-9.5]

- [x] **Task 4: Author and commit the PoC sign-off record** (AC: 7)
  - [x] 4.1: Create `firmware/VALIDATION.md` documenting all required fields:
    - **ESPHome version:** `2026.5.0` (known-good baseline) — confirm against the version actually used to build/flash. [firmware/README.md "ESPHome Version"]
    - **Hardware confirmed (OQ values):** OQ-1 button GPIOs = GPIO20–GPIO27 (matrix uses GPIO20/21); OQ-2 MCP2515 INT pin = **GPIO11**; OQ-3 MCP2515 oscillator = **16 MHz**. Source: CANBed RP2040 V1.1 Eagle schematic (pinned commit `fdefed9`). [firmware/README.md OQ-1/2/3]
    - **All 10 combinations verified:** table of (node, room, board, button, event) → artifact path, for node 100 (room 7) × 5 events and node 101 (room 8) × 5 events.
    - **Date of sign-off:** the actual completion date.
    - **Protocol baseline:** PROTO_V1 = 0x01, Extended IDs / location-as-address (ADR-0001); note the protocol is frozen as the regression baseline before production hardware swap. [architecture.md:480; canbus_protocol.h:39-44]
  - [x] 4.2: Commit `firmware/VALIDATION.md` together with the `validation/` artifacts.

- [x] **Task 5: Record results & close Epic 4** (AC: 1-7)
  - [x] 5.1: Record pass/fail per AC in Dev Agent Record → Completion Notes, referencing artifact paths and the `firmware/VALIDATION.md` commit. Note any anomalies. This story completing marks the PoC validated; Epic 4 can move to `done` and the (optional) Epic 4 retrospective becomes available. [sprint-status.yaml]

## Dev Notes

### What "done" means here

Five `esphome.canbus_button` events captured for node 101 (room 8, board 0), one per event type, each `room="8" board="0" button="0" event=<correct string>`, no blank fields; a committed node-101 artifact under `validation/`; all 10 artifacts present; zero CAN errors across the run; and a committed `firmware/VALIDATION.md` sign-off with ESPHome version, OQ-1/2/3 values, the 10-combination table with artifact locations, and the date. The only files written are `firmware/VALIDATION.md` and `validation/` artifacts — no firmware code changes.

### Why node 101 differs from node 100 only by `room`

Both nodes are board 0 with buttons on GPIO20/21; they are distinguished purely by **room** (8 vs 7) — the location-as-address scheme from ADR-0001. `board` is `"0"` for both. So FR-9.4's "distinct room value" is the cross-node differentiator, and AC2 checks exactly that. [Source: firmware/nodes.csv; ADR-0001; canbus_protocol.h:7-37]

### Identity & field decode (current protocol — same as 4.2)

- Payload = `[PROTO_V1]` only; room/board/button/event are in the 29-bit extended ID. [canbus_protocol.h:158-159]
- Gateway match `can_id: 0x04000000` mask `0x1C000000` `use_extended_id: true`; gate `x[0] == PROTO_V1` with `x.size() >= INPUT_PAYLOAD_MIN`. [gateway.yaml:90-96]
- HA event fields = `to_string(id_room/id_board/id_button(can_id))` + `std::string(event_type_str(id_event(can_id)))`; only fired when `event_type_str(...) != "unknown"`. [gateway.yaml:104-114]

### `firmware/VALIDATION.md` — required content (AC7)

Minimum sections so the sign-off is auditable and reproducible:
1. **Title + date of sign-off.**
2. **ESPHome version** — `2026.5.0` (or actual build version). [firmware/README.md]
3. **Hardware confirmed** — OQ-1 (button GPIOs GPIO20–27), OQ-2 (INT = GPIO11), OQ-3 (osc = 16 MHz), with the schematic source/commit. [firmware/README.md OQ-1/2/3]
4. **Protocol baseline** — PROTO_V1 = 0x01, Extended IDs / location-as-address (ADR-0001). [canbus_protocol.h:39-44]
5. **10-combination acceptance table** — rows for node 100 (room 7) and node 101 (room 8), each × {click, double_click, triple_click, long_press, extra_long_press}, mapping each to its `validation/` artifact path and pass status.
6. **Bus health** — zero CAN error frames across the run (FR-9.6).

This is the regression baseline referenced before any production hardware swap. [Source: architecture.md:221-223; epics.md:42]

### Gesture timing (reproduce each event)

Same `on_multi_click` thresholds as node 100 (shared `button.yaml`): triple/double/single, long = hold 1–2.999 s, extra-long = hold ≥3 s; patterns ordered longest-first. [firmware/common/button.yaml:38-90]

### Diagnosing failures

- **No node-101 event but node-100 worked:** node 101 not powered/flashed, or its bus drop is bad. Story 4.1 confirmed `R08B0` heartbeats — if those stopped, fix the node/bus first. The gateway `Button R08B0 ...` log line localizes node→gateway vs gateway→HA. [4-1-...md AC3]
- **`room` shows `"7"` for node 101:** a real address collision / mis-flashed node — node 101 must be `(room 8, board 0)`. `generate_nodes.py` rejects duplicate `(room, board)`, so this would mean the wrong binary was flashed to the node. [canbus_protocol.h:10-15]
- **CAN errors (AC6):** termination / bit-rate / CAN-H-L swap / INT pin — see Story 4.1 diagnosis. [4-1-...md "Diagnosing AC4"]

### Source tree components

- **READ-ONLY / VERIFY** [firmware/gateway.yaml](../../firmware/gateway.yaml) — CAT_INPUT handler, logger, CAN config. Do not modify.
- **READ-ONLY** [firmware/common/canbus_protocol.h](../../firmware/common/canbus_protocol.h), [firmware/common/button.yaml](../../firmware/common/button.yaml).
- **READ-ONLY** [firmware/nodes/node-r8-b0.yaml](../../firmware/nodes/node-r8-b0.yaml) — node 101 identity (room 8, board 0). Generated; never hand-edit. [project-context.md]
- **READ-ONLY** [firmware/README.md](../../firmware/README.md) — ESPHome version + OQ-1/2/3 values for the sign-off.
- **NEW (artifact)** `validation/` node-101 button-matrix capture (AC4).
- **NEW (write)** [firmware/VALIDATION.md](../../firmware/VALIDATION.md) — PoC sign-off record (AC7). This is the one file this story creates as code/doc.

### Testing standards

- **No unit-test framework**; validation = observation in HA Developer Tools + committed artifacts + the sign-off doc. [project-context.md "Testing & Validation"]

### Previous story intelligence

- **Story 4.2** established the matrix procedure, the HA Developer Tools observation flow, the `validation/` artifact convention, and the gateway-log CAN-error watch. 4.3 reuses all of it for node 101 and then aggregates. The 5 node-100 artifacts from 4.2 are a hard dependency for AC5. [4-2-...md]
- **Story 4.1** verified node 101 heartbeats (`R08B0`) and a zero-error bus — the bench prerequisite. [4-1-...md AC3,AC4]
- Older story text referencing payload-byte identity or flat node_id is stale post-ADR-0001 — trust the current header/gateway. [canbus_protocol.h:7-37]

### Git intelligence

- ADR-0001 (commit `0dd821d`) is the controlling design: extended IDs, location-as-address, no node_id. The sign-off doc should record this protocol baseline so a future reader knows exactly what was validated. [git log; canbus_protocol.h:7-37]

### Project Structure Notes

- `validation/` artifacts at repo root; `VALIDATION.md` under `firmware/` (per the epics AC wording: "committed to `firmware/VALIDATION.md`"). Note the asymmetry — artifacts in `validation/`, sign-off doc in `firmware/`. [epics.md#Story-4.3]
- Completing this story makes the optional Epic 4 retrospective available and lets `epic-4` move to `done` in sprint-status. [sprint-status.yaml]

### References

- [Source: epics.md#Story-4.3 — node 101 matrix + PoC sign-off (ACs, FR-9.2, FR-9.4, FR-9.5, FR-9.6, NFR-9)]
- [Source: epics.md:30,42 — FR-9 (10 combinations), NFR-9 (logged/repeatable validation)]
- [Source: architecture.md:219-223 — PoC sign-off criteria], [architecture.md:480 — protocol frozen after sign-off]
- [Source: firmware/gateway.yaml:88-114 — CAT_INPUT handler + `esphome.canbus_button`], [firmware/gateway.yaml:22-24 — logger], [firmware/gateway.yaml:130-135 — heartbeat error logging]
- [Source: firmware/common/canbus_protocol.h:19-26,144-149,158-159,185-202 — ID layout, decoders, payload, `event_type_str`; :39-44 — versioning policy]
- [Source: firmware/common/button.yaml:38-90 — gesture timing]
- [Source: firmware/nodes/node-r8-b0.yaml:15-16,40-41 — node 101 identity room 8/board 0, button GPIOs]
- [Source: firmware/nodes.csv — node 101 = floor 0, room 8, board 0, "Ground floor living room"]
- [Source: firmware/README.md — ESPHome 2026.5.0; OQ-1/OQ-2/OQ-3 hardware values for sign-off]
- [Source: ADR-0001 — Extended IDs with location-as-address]
- [Source: 4-2-button-event-acceptance-matrix-node-100.md — matrix procedure, validation/ convention (dependency for AC5)]
- [Source: 4-1-bench-assembly-and-hardware-commissioning.md — node 101 heartbeat verified, clean-bus baseline, network-log/DEBUG procedure]
- [Source: project-context.md — HA event fields are strings; never hand-edit nodes/]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (Claude Code create-story workflow)

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2026-06-05 — Story 4.3 created (create-story). Node-101 (room 8, board 0) button-event matrix + PoC sign-off. Reconciled to ADR-0001 (identity in extended CAN ID; HA `esphome.canbus_button` 4 string fields; `room` is the node-100/101 differentiator → FR-9.4). Defined the 5-event node-101 matrix, the all-10-artifacts aggregation (AC5, depends on Story 4.2), zero-CAN-error AC, and the `firmware/VALIDATION.md` sign-off contents (ESPHome 2026.5.0, OQ-1/2/3 hardware values, 10-combination table with artifact paths, date, protocol baseline).

## Status

done
