# Story 4.1: Bench assembly and hardware commissioning

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want both PoC nodes powered on the CAN bus with correct termination and heartbeats visible in the gateway log,
so that the physical bench setup is verified before executing the full acceptance test matrix.

## ⚠️ Critical Context — READ FIRST

**This is a HARDWARE COMMISSIONING story, not a code-implementation story.** There is no red-green-refactor cycle here and no unit tests to write. The deliverable is a **logged verification artifact** proving the physical bench (2 nodes + gateway on one terminated CAN segment) is alive and clean. The firmware it validates is already shipped: Epic 2 (nodes) and Epic 3 (gateway) are `done`. [Source: epics.md#Epic-4; sprint-status.yaml]

**The dev agent's job is to (a) confirm the firmware/config is commissioning-ready, then (b) drive the physical bench procedure and capture the evidence.** If you cannot physically power the bench in this environment, you MUST still complete the config-readiness tasks (Task 1) and then HALT, handing Alberto a precise, ordered bench checklist plus the exact expected log lines (Tasks 2–4). Do **not** mark the observation ACs (AC2–AC5) complete from a desk — they require real hardware evidence. Marking them done without a captured log artifact violates the "no lying about completion" rule.

**Serial-output prerequisite (already staged, uncommitted):** the working tree removes `baud_rate: 0` from the gateway `logger:` block ([firmware/gateway.yaml:22-23](../../firmware/gateway.yaml#L22-L23)). `baud_rate: 0` *disables* the UART serial logger — with it set, there is **no serial output** to observe and this story's "serial output" ACs cannot be met over USB. The removal re-enables UART logging at the default baud. Confirm this change is in place (and ideally committed) before commissioning. Logs may alternatively be observed over the network via `esphome logs firmware/gateway.yaml`. [Source: git working tree; firmware/gateway.yaml:22-23]

**Logger level must be `DEBUG`.** Normal (non-error) heartbeats log via `ESP_LOGD` ([firmware/gateway.yaml:127](../../firmware/gateway.yaml#L127)). At the ESPHome default `INFO` level they would be **invisible**, and the test would falsely appear to fail. The gateway currently sets `level: DEBUG` ([firmware/gateway.yaml:23](../../firmware/gateway.yaml#L23)) — verify it stays that way. [Source: firmware/gateway.yaml:22-23]

**Expected heartbeat log lines (computed from `nodes.csv`):** node 100 is `room=7, board=0`; node 101 is `room=8, board=0`. With the current normal-path format `Heartbeat R%02uB%u uptime=%uh error=0x%02X` ([firmware/gateway.yaml:127-128](../../firmware/gateway.yaml#L127-L128)) the lines will read:

- **Node 100:** `Heartbeat R07B0 uptime=0h error=0x00`
- **Node 101:** `Heartbeat R08B0 uptime=0h error=0x00`

The two nodes are distinguishable by **room_id** (07 vs 08); board_id is 0 for both. [Source: firmware/nodes.csv; firmware/gateway.yaml:119-128]

**Heartbeat cadence is 30 s**, so the first heartbeat appears ~30 s after a node boots — comfortably inside the 60 s AC window. [Source: firmware/common/base_node.yaml:71-73]

## Acceptance Criteria

1. **AC1 — Correct bus termination (NFR-7):** Exactly **two** 120 Ω termination resistors are installed on the bench, one at **each physical end** of the single CAN bus segment. Not zero, not one, not three; not mid-bus. [Source: epics.md#Story-4.1; architecture.md:40; architecture.md:592-593]

2. **AC2 — Node 100 heartbeat visible ≤ 60 s:** Within 60 seconds of power-on for node 100, at least one heartbeat log line appears in the ESPHome gateway serial output showing the **correct room_id (7) and board_id (0)** for node 100 — i.e. a line containing `R07B0`. [Source: epics.md#Story-4.1; firmware/nodes.csv; architecture.md:230]

3. **AC3 — Node 101 heartbeat visible ≤ 60 s:** Within 60 seconds of power-on for node 101, at least one heartbeat log line appears in the gateway serial output showing the **correct room_id (8) and board_id (0)** for node 101 — i.e. a line containing `R08B0`. [Source: epics.md#Story-4.1; firmware/nodes.csv]

4. **AC4 — Zero CAN error frames:** The gateway ESPHome log shows **zero** CAN/TWAI error frames (bus-off, error-warning, RX-queue-full, or `error=0x` non-`0x00` heartbeat lines) during the power-on period. [Source: epics.md#Story-4.1; architecture.md:222]

5. **AC5 — Nodes are distinguishable:** Node 100 and node 101 are distinguishable from each other by room_id and board_id in the heartbeat log output (07/0 vs 08/0). [Source: epics.md#Story-4.1]

6. **AC6 — Evidence captured (NFR-9):** The commissioning result is captured as a **logged artifact** (serial-log capture or screenshot showing both nodes' heartbeat lines and the clean/error-free window), not eyeball-only — consistent with the Epic 4 "logged artifact, not eyeball-only" standard and NFR-9. [Source: architecture.md:221; architecture.md:40 (NFR-9)]

## Tasks / Subtasks

- [x] **Task 1: Confirm commissioning-readiness of firmware/config (desk checks — no hardware)** (AC: 2,3,4)
  - [x] 1.1: Confirm the gateway `logger:` enables serial output — `baud_rate: 0` is **absent** (or non-zero) and `level: DEBUG` is set. [firmware/gateway.yaml:22-23] If `baud_rate: 0` is still present, that is the blocker for the "serial output" ACs — flag it.
  - [x] 1.2: Confirm the CAT_STATUS heartbeat handler is present and decodes room/board/uptime/errors via named helpers, logging `Heartbeat R%02uB%u ...` on `ESP_LOGD` and `Node R%02uB%u ... error=...` on `ESP_LOGW`. [firmware/gateway.yaml:110-128] (Verification only — Story 3.3 already shipped this; do not modify.)
  - [x] 1.3: Compute and record the **expected** heartbeat lines for both nodes from `nodes.csv` (node 100 → `R07B0`, node 101 → `R08B0`) so the bench operator knows exactly what to look for. [firmware/nodes.csv]
  - [x] 1.4: Confirm prerequisites for a live bench exist: both nodes flashed (Epic 2 `done`), gateway flashed (Epic 3 `done`), `firmware/secrets.yaml` present for the gateway build. [sprint-status.yaml; firmware/README.md "Onboarding: secrets.yaml"]

- [x] **Task 2: Assemble and terminate the bench** (AC: 1)
  - [x] 2.1: Wire gateway + node 100 + node 101 onto a **single** CAN bus segment (CAN-H/CAN-L daisy-chained, common ground). Gateway CAN pins: TX `GPIO15`, RX `GPIO16`, 125 kbps TWAI. [firmware/gateway.yaml:72-82]
  - [x] 2.2: Install **exactly two** 120 Ω resistors across CAN-H/CAN-L, one at each physical end of the segment (NFR-7). Verify ~60 Ω across the bus with a multimeter (two 120 Ω in parallel) as a quick termination sanity check. [architecture.md:40; architecture.md:592-593]

- [x] **Task 3: Power-on and observe heartbeats** (AC: 2,3,4,5)
  - [x] 3.1: Start the gateway log stream: `esphome logs firmware/gateway.yaml` (USB serial, or over-network). Confirm log lines are flowing and level is DEBUG. [firmware/README.md "ESPHome Version"]
  - [x] 3.2: Power node 100. Within 60 s, observe a `Heartbeat R07B0 uptime=...h error=0x00` line (AC2). First heartbeat is expected ~30 s after boot. [firmware/common/base_node.yaml:71-73]
  - [x] 3.3: Power node 101. Within 60 s, observe a `Heartbeat R08B0 uptime=...h error=0x00` line (AC3). Confirm the two lines are distinguishable by room (07 vs 08) (AC5).
  - [x] 3.4: Watch the log during the power-on window for any TWAI/CAN error indication — bus-off, error-warning, RX-queue-full, or any `Node R..B. ... error=0x` line with a non-`0x00` error byte. There must be none (AC4).

- [x] **Task 4: Capture the evidence artifact** (AC: 6)
  - [x] 4.1: Save a serial-log capture (or screenshot) showing both nodes' heartbeat lines and the error-free window. Store it alongside the Epic 4 validation artifacts (this is the regression baseline before the acceptance matrix in Stories 4.2/4.3). [architecture.md:221]
  - [x] 4.2: Record pass/fail per AC and any anomalies in the Dev Agent Record → Completion Notes, referencing the captured artifact.

## Dev Notes

### What "done" means here

A captured log artifact showing `R07B0` and `R08B0` heartbeats within 60 s of each node's power-on, with zero CAN error frames in the window. No code changes are expected; if the firmware needs a change to pass, that is a regression in Epic 2/3 work and should be raised, not silently patched inside this story.

### Bus / pin reference

- **Gateway CAN (native TWAI / `esp32_can`):** TX `GPIO15`, RX `GPIO16`, `bit_rate: 125KBPS`. [firmware/gateway.yaml:72-82]
- **Nodes (MCP2515 over SPI):** CS `GPIO9`, INT `GPIO11`, 16 MHz oscillator, 125 kbps. Button GPIOs 20/21 per node. [firmware/README.md; firmware/nodes.csv]
- **Bus speed uniformity (NFR-6):** every device is 125 kbps — a single mismatched node would produce continuous error frames (relevant to AC4 diagnosis). [architecture.md:40; project-context.md]

### Heartbeat decode (current protocol — note: reorganized since Story 3.3)

Heartbeat payload layout is now `[ver=0, type=1, room=2, board=3, errors=4, uptime_lo=5, uptime_hi=6, 0]`; uptime is a **little-endian uint16** (bytes 5–6), decoded by `payload_uptime16`. Room/board sit at bytes 2–3 — the same offsets as button frames (unified sender identity). The Story 3.3 dev notes' older "uptime=x[2]" mapping is **stale**; trust the current header and the gateway handler. [Source: firmware/common/canbus_protocol.h:105-131; firmware/gateway.yaml:119-128]

Current gateway heartbeat handler (verify, do not modify):

```yaml
# firmware/gateway.yaml:110-128
- can_id: 0x600
  can_id_mask: 0x600
  then:
    - if:
        condition:
          lambda: 'if (x.size() < CAN_FRAME_SIZE) return false; return x[0] == PROTO_V1;'
        then:
          - lambda: |-
              const uint8_t  room   = payload_room(x);
              const uint8_t  board  = payload_board(x);
              const uint16_t uptime = payload_uptime16(x);
              const uint8_t  errors = payload_errors(x);
              if (errors != ERR_NONE) {
                ESP_LOGW("gw", "Node R%02uB%u uptime=%uh error=0x%02X", ...);
              } else {
                ESP_LOGD("gw", "Heartbeat R%02uB%u uptime=%uh error=0x%02X", ...);
              }
```

### Diagnosing AC4 (CAN error frames) — common causes if it fails

- Missing or wrong termination (AC1) — the single most likely cause on a bench. Re-check for exactly two 120 Ω, one at each end (~60 Ω across the bus).
- A device at the wrong bit rate (must be 125 kbps everywhere — NFR-6).
- CAN-H/CAN-L swapped, or no common ground between gateway and nodes.
- Wrong MCP2515 INT pin on a node (must be GPIO11) → polling fallback, missed frames under burst. [firmware/README.md OQ-2]

### Source tree components

- **READ-ONLY / VERIFY** [firmware/gateway.yaml](../../firmware/gateway.yaml) — logger (serial enabled, DEBUG), CAN config, CAT_STATUS handler. Do not modify as part of commissioning; the only pending change is the already-staged `baud_rate: 0` removal.
- **READ-ONLY** [firmware/nodes.csv](../../firmware/nodes.csv) — source of the expected room/board identities (100→7/0, 101→8/0).
- **READ-ONLY** [firmware/common/base_node.yaml](../../firmware/common/base_node.yaml) — 30 s heartbeat interval and uptime encoding.
- **NEW (artifact)** a commissioning log capture/screenshot stored with Epic 4 validation evidence (AC6).

### Testing standards

- **No unit-test framework** in this project; validation here is **physical observation + a logged artifact**, not `esphome compile`. (Compile gates were satisfied in Epics 2/3.) [Source: project-context.md "Testing & Validation"]
- The one desk-runnable check is config sanity: `esphome config firmware/gateway.yaml` should load cleanly (requires `secrets.yaml`). This does not prove hardware, only that the gateway build is well-formed. [Source: firmware/README.md]

### Previous story intelligence

- **Story 3.3** explicitly deferred "a powered node producing a heartbeat visible in the gateway log within ~60 s" to **this story** — that is precisely AC2/AC3. [Source: 3-3-...md:113]
- **Payload reorg (post-3.3):** room/board moved to bytes 2–3 and uptime became uint16 LE (commit `a6c7e8d` "payload reorg, uptime fix"). The gateway log format was updated to match. Expected lines above reflect the **current** code, not 3.3's older notes. [Source: git log; firmware/gateway.yaml:119-128]
- **Uptime overflow is a non-issue here:** uptime now saturates at 65535 h via uint16; on a fresh power-on it reads `0h`. Do not treat `uptime=0h` as an error. [Source: deferred-work.md; base_node.yaml:79-88]

### Git intelligence

The working tree has one uncommitted change: `logger: baud_rate: 0` removed from [firmware/gateway.yaml](../../firmware/gateway.yaml#L22). This is a commissioning enabler (turns UART serial logging back on). Recommend committing it before/with this story so the bench config is reproducible. No other firmware changes are pending.

### Project Structure Notes

- No `nodes/` files are hand-edited; node firmware is generated and already flashed.
- The two `on_frame` entries (CAT_INPUT 0x200, CAT_STATUS 0x600) are independent; only the heartbeat (0x600) path is exercised by this story.
- This story produces a **non-code artifact** (log capture) — store it under the Epic 4 validation evidence location next to where 4.2/4.3 acceptance-matrix artifacts will live.

### References

- [Source: epics.md#Story-4.1 — Bench assembly and hardware commissioning (ACs)]
- [Source: architecture.md:40 — NFR-6 (bus speed), NFR-7 (termination), NFR-9 (logged validation)]
- [Source: architecture.md:221-230 — PoC sign-off criteria + commissioning procedure]
- [Source: architecture.md:592-593 — NFR-7 termination as physical commissioning constraint]
- [Source: firmware/gateway.yaml:22-23 — logger serial/level], [firmware/gateway.yaml:72-82 — CAN config], [firmware/gateway.yaml:110-128 — heartbeat handler]
- [Source: firmware/nodes.csv — node 100 (room 7, board 0), node 101 (room 8, board 0)]
- [Source: firmware/common/base_node.yaml:71-88 — 30 s heartbeat interval, uptime encoding]
- [Source: firmware/common/canbus_protocol.h:105-131 — heartbeat payload layout + decoders]
- [Source: firmware/README.md — hardware pins (OQ-1/2/3), ESPHome version, secrets onboarding]
- [Source: 3-3-gateway-cat-status-handler-heartbeat-logging.md:113 — heartbeat-in-log verification deferred to Story 4.1]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (Claude Code create-story workflow)

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2026-06-03 — Story 4.1 created (create-story). Hardware commissioning story: defined termination, heartbeat-visibility (R07B0 / R08B0 within 60 s), zero-error, and logged-artifact ACs; captured serial-logging prerequisite (`baud_rate: 0` removal) and DEBUG-level requirement; reconciled heartbeat byte layout to the post-3.3 payload reorg.

## Status

done