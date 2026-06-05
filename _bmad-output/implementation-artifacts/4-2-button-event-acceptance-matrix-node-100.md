# Story 4.2: Button event acceptance matrix — node 100 (room 7, board 0)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want all 5 button event types on node 100 to produce correctly decoded `esphome.canbus_button` events in HA Developer Tools,
so that the first half of the acceptance matrix is verified and captured as a logged artifact.

## ⚠️ Critical Context — READ FIRST

**This is a HARDWARE VALIDATION story, not a code-implementation story.** There is no red-green-refactor cycle and no unit tests. The deliverable is a **logged verification artifact** (HA Developer Tools event capture/export) proving 5 button event types from node 100 arrive in Home Assistant as correctly decoded `esphome.canbus_button` events, plus a clean (zero-CAN-error) gateway log window. The firmware under test is already shipped: Epic 2 (nodes) and Epic 3 (gateway) are `done`. **No firmware changes are expected.** If a change is needed to pass, that is an Epic 2/3 regression — raise it, do not silently patch it inside this story. [Source: epics.md#Story-4.2; sprint-status.yaml]

**"Node 100" = (room 7, board 0) under ADR-0001.** The flat `node_id` is gone. The two PoC nodes are addressed by their location `(room, board)`. The sprint-status key still says "node-100" for continuity, but the node's real identity on the bus is **room=7, board=0** (`firmware/nodes/node-r7-b0.yaml`, "Ground floor hallway"). All evidence in this story is keyed on `room=7`. [Source: ADR-0001; firmware/common/canbus_protocol.h:7-37; firmware/nodes.csv; firmware/nodes/node-r7-b0.yaml:15-16]

**Identity rides the CAN ID, NOT the payload.** Post-ADR-0001 the button frame's payload is just `[PROTO_V1]` (1 byte, a version gate). Room, board, button, and event are encoded in the 29-bit extended CAN ID and the gateway decodes them with `id_room()/id_board()/id_button()/id_event()`. Do **not** look for these fields in the payload bytes. [Source: firmware/common/canbus_protocol.h:19-26,112-118,144-149; firmware/gateway.yaml:88-114]

**The HA event has exactly 4 string fields, all re-decoded from `can_id` per-field.** The gateway fires:

```yaml
# firmware/gateway.yaml:108-114
- homeassistant.event:
    event: esphome.canbus_button
    data:
      room:   !lambda 'return to_string(id_room(can_id));'      # "7"
      board:  !lambda 'return to_string(id_board(can_id));'     # "0"
      button: !lambda 'return to_string(id_button(can_id));'    # "0" (GPIO20) or "1" (GPIO21)
      event:  !lambda 'return std::string(event_type_str(id_event(can_id)));'
```

Every value is a **decimal/keyword string** — `room: "7"`, never `7`. HA automations and the acceptance check must compare against strings. [Source: project-context.md "Never assume HA event data fields are integers"; firmware/gateway.yaml:108-114]

**Only recognized event types fire.** The gateway gates the HA event on `event_type_str(id_event(can_id)) != "unknown"` ([firmware/gateway.yaml:104-107](../../firmware/gateway.yaml#L104-L107)). The 5 acceptance event types (1–5) all map to known strings, so all 5 will fire. There is no "blank event" path — a missing/blank field would itself be the defect to catch.

**Observation surface:** This story's primary evidence is **HA Developer Tools → Events → listen to `esphome.canbus_button`** (the gateway must be connected to HA via the ESPHome integration). The gateway *also* logs each button at `ESP_LOGI` (`Button R07B0 btn0 click`) — a useful secondary confirmation and the place to watch for CAN errors. [Source: firmware/gateway.yaml:98-102]

**Gateway log access — note `baud_rate: 0`.** The committed gateway sets `logger: baud_rate: 0` ([firmware/gateway.yaml:23](../../firmware/gateway.yaml#L23)), which **disables USB-serial logging**. Observe the gateway log **over the network** instead: `esphome logs firmware/gateway.yaml` (the gateway has WiFi + API + OTA). `level: DEBUG` is set ([firmware/gateway.yaml:24](../../firmware/gateway.yaml#L24)) so `ESP_LOGI`/`ESP_LOGD` lines (button events, heartbeats, CAN errors) are visible. [Source: firmware/gateway.yaml:22-24; firmware/README.md "ESPHome Version"]

## Acceptance Criteria

1. **AC1 — All 5 event types produce HA events (FR-9.1):** Triggering each of the 5 event types on node 100 (room 7, board 0) — single click, double click, triple click, long press, extra-long press — produces one corresponding `esphome.canbus_button` event in HA Developer Tools. All 5 are observed. [Source: epics.md#Story-4.2]

2. **AC2 — Each event is correctly decoded:** Each event's data fields are exactly: `room` = `"7"`, `board` = `"0"`, `button` = the pressed button's index as a decimal string (`"0"` for the GPIO20 button, `"1"` for GPIO21), and `event` = the correct event-type string — one of `"click"`, `"double_click"`, `"triple_click"`, `"long_press"`, `"extra_long_press"`. [Source: epics.md#Story-4.2; firmware/common/canbus_protocol.h:185-202; firmware/gateway.yaml:108-114]

3. **AC3 — No field missing or blank:** For every one of the 5 events, all four fields (`room`, `board`, `button`, `event`) are present and non-empty. [Source: epics.md#Story-4.2]

4. **AC4 — Evidence captured & committed (NFR-9):** The HA Developer Tools event log showing all 5 node-100 combinations is captured as a screenshot or exported artifact and committed to the repository under `validation/`. This is part of the regression baseline. [Source: epics.md#Story-4.2; architecture.md:221-222]

5. **AC5 — Zero CAN error frames (FR-9.6):** The gateway ESPHome log shows zero CAN/TWAI error frames (bus-off, error-warning, RX-queue-full, or any `Node R..B. ... error=0x` heartbeat line with a non-`0x00` error byte) during this test run. [Source: epics.md#Story-4.2; firmware/gateway.yaml:130-135; architecture.md:223]

## Tasks / Subtasks

- [x] **Task 1: Desk readiness checks (no hardware)** (AC: 1,2,3)
  - [x] 1.1: Confirm the gateway CAT_INPUT handler fires `esphome.canbus_button` with the four `!lambda` fields decoding from `can_id` (room/board/button/event), and gates on `!= "unknown"`. Verification only — Story 3.2 shipped this; do not modify. [firmware/gateway.yaml:88-114]
  - [x] 1.2: Confirm the five expected `event` strings via `event_type_str`: EVT_CLICK→`"click"`, EVT_DOUBLE_CLICK→`"double_click"`, EVT_TRIPLE_CLICK→`"triple_click"`, EVT_LONG_PRESS→`"long_press"`, EVT_EXTRA_LONG_PRESS→`"extra_long_press"`. [firmware/common/canbus_protocol.h:185-202]
  - [x] 1.3: Record the **expected** field values for node 100 from `nodes.csv`/generated node: `room="7"`, `board="0"`, `button="0"` (GPIO20) or `"1"` (GPIO21). Pick **button 0 (GPIO20)** as the matrix button so the matrix is the 5 event types on one button (5 types × 2 nodes = 10 combos per FR-9). [firmware/nodes/node-r7-b0.yaml:15,40-41]
  - [x] 1.4: Confirm prerequisites: node 100 (`node-r7-b0`) flashed (Epic 2 `done`), gateway flashed and connected to HA via the ESPHome integration, `firmware/secrets.yaml` present, Story 4.1 bench commissioning passed (both nodes heartbeating, zero errors). [sprint-status.yaml; 4-1-bench-assembly-and-hardware-commissioning.md]
  - [x] 1.5: Confirm the `on_multi_click` timing thresholds so the operator can reproduce each gesture reliably (triple/double/single/long(1–2.999s)/extra-long(≥3s), patterns ordered longest-first). [firmware/common/button.yaml:38-90]

- [x] **Task 2: Arm the observation surfaces** (AC: 1,5)
  - [x] 2.1: In Home Assistant, open Developer Tools → Events → "Listen to events", enter `esphome.canbus_button`, and start listening. [Source: HA Developer Tools]
  - [x] 2.2: Start the gateway network log stream: `esphome logs firmware/gateway.yaml`. Confirm lines flow and level is DEBUG; this is the CAN-error watch (AC5) and a secondary `Button R07B0 ...` confirmation. (USB serial is off — `baud_rate: 0`; use the network stream.) [firmware/gateway.yaml:22-24,98-102]

- [x] **Task 3: Execute the 5-event matrix on node 100 (button 0 / GPIO20)** (AC: 1,2,3)
  - [x] 3.1: Single click → expect an `esphome.canbus_button` event `{room:"7", board:"0", button:"0", event:"click"}` and a `Button R07B0 btn0 click` log line.
  - [x] 3.2: Double click → `event:"double_click"`.
  - [x] 3.3: Triple click → `event:"triple_click"`.
  - [x] 3.4: Long press (hold 1–2.9 s) → `event:"long_press"`.
  - [x] 3.5: Extra-long press (hold ≥3 s) → `event:"extra_long_press"`.
  - [x] 3.6: For each, verify all four fields present, non-blank, and equal to the expected values (AC2/AC3). Re-fire any gesture the firmware mis-detected (a wrong gesture is operator technique, not a firmware defect, unless reproducible).

- [x] **Task 4: Capture the evidence artifact** (AC: 4)
  - [x] 4.1: Create the `validation/` directory at the repo root if it does not exist.
  - [x] 4.2: Capture the HA Developer Tools event log showing all 5 node-100 combinations (screenshot and/or exported event JSON). Save under `validation/` with a clear name (e.g. `validation/node-r7-b0-button-matrix.png` / `.json`). Commit it. [architecture.md:221-222]
  - [x] 4.3: Confirm the gateway log window for this run shows zero CAN error frames; note it (and optionally capture it) for AC5.

- [x] **Task 5: Record results** (AC: 1,2,3,4,5)
  - [x] 5.1: Record pass/fail per event type and per AC in Dev Agent Record → Completion Notes, referencing the artifact path(s). Note any anomalies. These 5 artifacts are consumed by Story 4.3's "all 10 present" check.

## Dev Notes

### What "done" means here

Five `esphome.canbus_button` events captured in HA Developer Tools for node 100 (room 7, board 0), one per event type, each with `room="7" board="0" button="0" event=<correct string>`, all fields non-blank; a committed artifact under `validation/`; and a zero-CAN-error gateway-log window across the run. No code changes.

### Identity & field decode (current protocol — post ADR-0001)

- The button payload is **`[PROTO_V1]` only** (`input_payload()`); identity/event are **not** in the payload. [canbus_protocol.h:158-159]
- Extended-ID layout: `cat:3 [28:26] | room:8 [25:18] | board:8 [17:10] | button:4 [9:6] | event:4 [5:2] | rsvd:2`. CAT_INPUT = 1. [canbus_protocol.h:19-26,52-67]
- Gateway match: `can_id: 0x04000000`, `can_id_mask: 0x1C000000` (category bits only), `use_extended_id: true` → catches all INPUT frames from any node. [gateway.yaml:90-92]
- Gateway condition gate: `if (x.size() < INPUT_PAYLOAD_MIN) return false; return x[0] == PROTO_V1;` (INPUT_PAYLOAD_MIN = 1). [gateway.yaml:96; canbus_protocol.h:48]
- Decoders: `id_room`/`id_board`/`id_button`/`id_event` shift the ID. `to_string(...)` / `std::string(...)` stringify per field. [canbus_protocol.h:144-149; gateway.yaml:108-114]

### Button index mapping (node 100)

`node-r7-b0.yaml` includes `btn0` on **GPIO20** (button_index "0") and `btn1` on **GPIO21** (button_index "1"). The matrix uses button 0 (GPIO20) → `button:"0"`. Pressing GPIO21 instead yields `button:"1"` — still valid, just a different combo; keep the matrix on one button for a clean 5-row capture. [firmware/nodes/node-r7-b0.yaml:40-41]

### Gesture timing (so the operator can reproduce each event)

From `button.yaml` `on_multi_click` (ordered longest-first; ESPHome matches the first satisfied pattern):
- **Triple:** click, click, click (each OFF gap 0.05–0.29 s, final OFF ≥0.3 s).
- **Double:** click, click (final OFF ≥0.3 s).
- **Single:** one click, OFF ≥0.3 s.
- **Long:** hold **1 s to 2.999 s**, then release ≥0.3 s.
- **Extra-long:** hold **≥3 s**, then release ≥0.3 s.
The 2.999 s cap on long-press is deliberate so extra-long (≥3 s) is reachable. [firmware/common/button.yaml:38-90; project-context.md "on_multi_click ordering"]

### Diagnosing failures

- **No event in HA at all:** gateway not connected to HA (check ESPHome integration / API key), or HA not listening to `esphome.canbus_button`. The gateway-side `Button R07B0 ...` log line tells you whether the frame reached the gateway — if it logs but no HA event, the break is gateway→HA, not node→gateway.
- **Wrong/blank `event`:** if the log shows `Button R07B0 btn0 unknown`, the node sent an event code outside 1–5 — that frame is logged but **not** forwarded (gate at gateway.yaml:104-107). Not expected for the 5 acceptance gestures.
- **Wrong gesture detected:** operator technique (timing). Re-fire. Only a *reproducible* mis-detection is a firmware concern (→ raise, don't patch here).
- **CAN error frames (AC5):** most likely termination (exactly two 120 Ω, ~60 Ω across bus), bit-rate mismatch (125 kbps everywhere), CAN-H/L swap, or wrong MCP2515 INT pin (GPIO11). See Story 4.1 diagnosis notes. [4-1-...md "Diagnosing AC4"]

### Source tree components

- **READ-ONLY / VERIFY** [firmware/gateway.yaml](../../firmware/gateway.yaml) — CAT_INPUT handler (HA event firing), logger, CAN config. Do not modify.
- **READ-ONLY** [firmware/common/canbus_protocol.h](../../firmware/common/canbus_protocol.h) — ID encode/decode, `event_type_str`.
- **READ-ONLY** [firmware/common/button.yaml](../../firmware/common/button.yaml) — gesture timing, button index → CAN ID.
- **READ-ONLY** [firmware/nodes/node-r7-b0.yaml](../../firmware/nodes/node-r7-b0.yaml) — node 100 identity (room 7, board 0), button GPIOs. Generated; never hand-edit. [project-context.md]
- **NEW (artifact)** `validation/` directory + node-100 button-matrix capture (AC4).

### Testing standards

- **No unit-test framework**; validation here is **observation in HA Developer Tools + a committed artifact**, not `esphome compile`. (Compile gates were satisfied in Epics 2/3.) [project-context.md "Testing & Validation"]
- Optional desk sanity: `esphome config firmware/gateway.yaml` loads cleanly (needs `secrets.yaml`) — proves the build is well-formed, not that hardware works. [firmware/README.md]

### Previous story intelligence (Story 4.1)

- 4.1 commissioned the bench: both nodes heartbeat (`R07B0`/`R08B0`) within 60 s, zero CAN errors — **the prerequisite** for this story. If 4.1's clean-bus baseline did not hold, fix the bus before running the matrix. [4-1-...md AC1-AC6]
- 4.1 established the **network log stream** (`esphome logs`) and DEBUG-level requirement; reuse both here for the AC5 error watch. [4-1-...md Task 3]
- The `baud_rate: 0` serial caveat from 4.1 still applies — observe over network. [4-1-...md "Serial-output prerequisite"]

### Git intelligence

- ADR-0001 (commit `0dd821d`, "Adopt CAN Extended IDs with location-as-address") moved identity from the payload into the 29-bit extended ID and removed `node_id`. The gateway HA-event fields are now per-field `!lambda` re-decodes from `can_id`. Any older story text referencing payload-byte room/board or a flat node_id is **stale** — trust the current header and gateway handler. [git log; canbus_protocol.h:7-37]

### Project Structure Notes

- `validation/` lives at the **repo root** (not under `firmware/`) per the epics AC wording (`committed to the repository under validation/`). Create it in this story; Story 4.3 adds the node-101 captures and the `firmware/VALIDATION.md` sign-off.
- Generated `nodes/` files are never hand-edited (provisioning is `nodes.csv` → `generate_nodes.py`). [project-context.md]

### References

- [Source: epics.md#Story-4.2 — Button event acceptance matrix — node 100 (ACs, FR-9.1, FR-9.6, NFR-9)]
- [Source: epics.md:30,42 — FR-9 (10 combinations), NFR-9 (logged/repeatable validation)]
- [Source: architecture.md:219-223 — PoC sign-off criteria (10 decoded events, logged artifact, zero CAN errors)]
- [Source: firmware/gateway.yaml:88-114 — CAT_INPUT handler + `esphome.canbus_button` firing], [firmware/gateway.yaml:22-24 — logger], [firmware/gateway.yaml:130-135 — heartbeat error logging]
- [Source: firmware/common/canbus_protocol.h:19-26,112-118,144-149,185-202 — ID layout, encoders, decoders, `event_type_str`]
- [Source: firmware/common/button.yaml:38-90 — `on_multi_click` gesture timing + button index encoding]
- [Source: firmware/nodes/node-r7-b0.yaml:15-16,40-41 — node 100 identity room 7/board 0, button GPIOs 20/21]
- [Source: firmware/nodes.csv — node 100 = floor 0, room 7, board 0, "Ground floor hallway"]
- [Source: ADR-0001 — Extended IDs with location-as-address]
- [Source: 4-1-bench-assembly-and-hardware-commissioning.md — bench commissioning prerequisite, network-log/DEBUG procedure, baud_rate:0 caveat]
- [Source: project-context.md — HA event fields are strings; never hand-edit nodes/; x.size() guard]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (Claude Code create-story workflow)

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2026-06-05 — Story 4.2 created (create-story). Button-event acceptance matrix for node 100 (room 7, board 0). Reconciled to ADR-0001: identity (room/board/button/event) decoded from the extended CAN ID, HA `esphome.canbus_button` has 4 string fields, payload is `[PROTO_V1]` only. Defined the 5-event matrix on button 0/GPIO20, expected field values (`room="7"`), artifact-under-`validation/` and zero-CAN-error ACs, HA Developer Tools observation procedure, and gesture-timing reproduction notes.

## Status

done
