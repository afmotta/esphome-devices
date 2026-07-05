# Story 5.1: Gateway command reliability — send retry/backoff, HA failure notification, and stuck-frame fault surfacing

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->
<!-- SCOPE NOTE: This is a NEW post-PoC story (Epic 5) not present in epics.md. It consolidates
     deferred items #8 and #9 from deferred-work.md. It is drafted ahead but is sequenced AFTER the
     Epic 4 PoC sign-off — do not start it before Epic 4 is done. Registering Epic 5 in the planning
     epics.md is a PM/sprint-planning step still outstanding (see Project Structure Notes). -->

## Story

As the operator of the CAN ↔ Home Assistant gateway,
I want gateway → node commands to retry on transient bus failures, notify Home Assistant when a command ultimately fails, and surface pathological inbound-frame storms as faults,
so that command delivery is reliable on a busy/marginal bus and silent failures or event-bus floods become observable instead of invisible.

## Context & origin

This story consolidates two deferred-work items reviewed and parked on 2026-06-03 because each needs design rather than an ad-hoc patch:

- **#9 — Service `send_data()` error handling** (deferred from review of Story 3.1). The two API services (`canbus_send_output`, `canbus_send_config`) currently call `id(can0).send_data(...)` and only `ESP_LOGW` on a non-OK return — no retry, no recovery, no notification back to HA. [Source: `_bmad-output/implementation-artifacts/deferred-work.md` → "Deferred from: code review of 3-1"; `firmware/gateway.yaml:38-68`]
- **#8 — No rate-limit/dedup on HA event firing** (deferred from review of Story 3.2). Reviewed conclusion: do **not** throttle/dedup `homeassistant.event` (a content-blind throttle drops legitimate rapid distinct button events — buttons are momentary, one frame per gesture). The real risk is a stuck/repeating frame, which is a **fault to surface**, not traffic to mute. [Source: `deferred-work.md` → "Deferred from: code review of 3-2"; memory `feedback_momentary_buttons_no_state`]

## Acceptance Criteria

### AC1 — Non-blocking bounded retry with backoff (both command services)

**Given** the gateway exposes the API services `canbus_send_output` and `canbus_send_config` ([`firmware/gateway.yaml:38-68`])
**When** a service is invoked and `id(can0).send_data(...)` returns a non-`ERROR_OK` `canbus::Error`
**Then** the send is retried up to a bounded maximum (default **3 total attempts**) with a backoff delay between attempts (default **first retry ~50 ms, then ~150 ms**)
**And** the retry is implemented **without blocking the ESPHome main loop** — use an ESPHome `script:` with `parameters:` + `delay:` (or equivalent async/scheduled mechanism), NOT a busy-wait loop with `delay()` inside a single lambda
**And** each attempt logs at its level: `ESP_LOGD` for an attempt, `ESP_LOGW` for a failed attempt that will be retried, and `ESP_LOGE` for final exhaustion
**And** retry counts/delays are defined as named constants or substitutions, not inline magic numbers
**And** `esphome compile firmware/gateway.yaml` completes successfully (NFR-1)

### AC2 — Command idempotency preserved under retry

**Given** retries may resend the same frame
**When** a command is retried
**Then** the resent frame is byte-identical to the original attempt (same CAN ID and 8-byte payload) — output and config writes are idempotent at the node, so a duplicate delivery is safe
**And** the story documents (in a YAML comment near the retry script) that this idempotency assumption is the reason retries are safe, so a future non-idempotent command type is not retried blindly

### AC3 — Home Assistant notification on final failure

**Given** a command has exhausted all retry attempts and still failed
**When** final exhaustion is reached
**Then** the gateway fires a Home Assistant event named `esphome.canbus_command_failed` using the ESPHome **`homeassistant.event:` YAML action** (NOT `api::global_api_server` / the internal single-lambda API — see Dev Notes / decision reference)
**And** the event carries string fields: `service` (which service failed, e.g. `"canbus_send_output"`), `node_id`, and `error` (the final `canbus::Error` as a string/number)
**And** all event field values are strings (per the project rule: HA event data fields are strings) [Source: `_bmad-output/project-context.md`]
**And** the per-field values are produced by per-field `!lambda` (no globals staging) consistent with the gateway's existing event-firing pattern

### AC4 — Stuck / repeating inbound-frame fault surfacing (NOT throttling)

**Given** a malfunctioning node or bus condition can emit the same inbound frame at an abnormally high rate
**When** matching inbound frames (CAT_INPUT and/or CAT_STATUS) arrive faster than a configurable threshold far above human-paced use (default heuristic: **more than ~20 frames/second sustained from the matched category**)
**Then** the gateway emits a **fault log** (`ESP_LOGW`/`ESP_LOGE`) identifying the storm, **without dropping or rate-limiting the legitimate `homeassistant.event` firing** (every legitimate event still fires — this AC adds observability, it does not gate the existing button/heartbeat handlers)
**And** the detection is rate-based over a time window (e.g., a counter reset each window), NOT content dedup — distinct legitimate events (two single-clicks, clicks on different buttons) are never suppressed
**And** the fault is debounced so a single transient burst does not spam the log (e.g., one warning per storm episode, not one per frame over threshold)
**And** the storm threshold and window are named constants, not inline literals

### AC5 — No regression to existing PoC behavior

**Given** Epics 1–4 define the working PoC baseline
**When** this story's changes are added
**Then** the existing CAT_INPUT button-event firing ([`firmware/gateway.yaml:84-108`]) and CAT_STATUS heartbeat logging ([`firmware/gateway.yaml:110-129`]) continue to behave exactly as before for normal, human-paced traffic — no dropped events, no added latency on the happy path
**And** every `on_frame` receive lambda still begins with the `if (x.size() < CAN_FRAME_SIZE) return ...;` guard (NFR-2)
**And** all protocol constants/decoders still come from `canbus_protocol.h` — no magic numbers introduced in YAML (NFR-3)
**And** `esphome compile firmware/gateway.yaml` completes successfully

## Tasks / Subtasks

- [ ] **Task 1 — Research ESPHome `esp32_can` send semantics (AC1, AC2)**
  - [ ] Confirm `id(can0).send_data(can_id, use_ext, data)` return type and the `canbus::Error` enum values reachable on the ESP32 TWAI path (e.g. `ERROR_OK`, `ERROR_ALLTXBUSY`, `ERROR_FAILTX`, `ERROR_FAIL`) against the pinned ESPHome 2026.5.0 source.
  - [ ] Determine whether `send_data` is a synchronous enqueue (TX queue) and which error codes are transient (worth retrying) vs. terminal (e.g. bus-off / init failure — retry won't help).
  - [ ] Decide retry policy: which `canbus::Error` values trigger retry, which fail fast to AC3 notification.
- [ ] **Task 2 — Parameterized retry script (AC1, AC2)**
  - [ ] Add an ESPHome `script:` (with `parameters:` for node_id/payload fields and an attempt counter) that performs one `send_data` attempt and, on a transient failure, schedules itself again after the backoff `delay:` until the attempt cap is hit.
  - [ ] Refactor `canbus_send_output` and `canbus_send_config` service `then:` blocks to invoke the retry script instead of a single inline `send_data` lambda. Preserve the exact frame bytes each builds today ([`firmware/gateway.yaml:46-48`, `62-65`]).
  - [ ] Add the idempotency-rationale comment (AC2).
  - [ ] Define `MAX_SEND_ATTEMPTS` and backoff delays as constants/substitutions.
- [ ] **Task 3 — HA failure notification (AC3)**
  - [ ] On final exhaustion in the retry script, fire `homeassistant.event: esphome.canbus_command_failed` with per-field `!lambda` string values (`service`, `node_id`, `error`).
  - [ ] Verify the `homeassistant.event` YAML action path (not internal API) per the firing-approach decision.
- [ ] **Task 4 — Stuck-frame fault surfacing (AC4)**
  - [ ] Add a windowed rate counter (ESPHome `globals` + an `interval:` to reset/evaluate, or a timestamp-delta check inside the existing `on_frame` handlers) that counts matched inbound frames per window.
  - [ ] On threshold breach, emit a debounced fault log; do NOT alter the existing event-firing/logging flow.
  - [ ] Define `FRAME_STORM_THRESHOLD` and window as constants.
- [ ] **Task 5 — Verify & document (AC5)**
  - [ ] `esphome compile firmware/gateway.yaml` → SUCCESS on 2026.5.0.
  - [ ] Confirm happy-path button + heartbeat behavior unchanged (re-read the two existing handlers; no behavioral diff on normal traffic).
  - [ ] Update `firmware/README.md` (or gateway header comment) with the retry policy, the `canbus_command_failed` event contract, and the storm-detection thresholds so HA automations can consume them.
  - [ ] Move deferred items #8 and #9 to a "Closed" section in `deferred-work.md` referencing this story.

## Dev Notes

### Current state of the files this story touches (READ THESE FIRST)

- **`firmware/gateway.yaml`** — the only firmware file this story modifies.
  - **API services** ([`:38-68`]): `canbus_send_output` (params `node_id, subtype, param1, param2`) and `canbus_send_config` (params `node_id, key, value`). Both build an 8-byte frame and call `auto err = id(can0).send_data(can_id(CAT_OUTPUT, (uint16_t) node_id), false, {...});` then `if (err != canbus::ERROR_OK) ESP_LOGW(...)`. **This story replaces the inline single-attempt send with a retry script but must preserve the exact frame each currently builds.**
  - **CAN bus / `on_frame`** ([`:73-129`]): `esp32_can` platform, `id: can0`, two `on_frame` filters — CAT_INPUT (`0x200`/mask `0x600`) fires `esphome.canbus_button`; CAT_STATUS (`0x600`/mask `0x600`) logs heartbeat. **AC4 adds observability around these handlers but must not change their existing happy-path behavior (AC5).**
- **Do NOT modify** `firmware/common/*` or `firmware/nodes/*` for this story — it is gateway-only. Nodes are frozen firmware; command reliability is a gateway concern.

### Critical guardrails

- **Non-blocking only.** ESPHome lambdas run on the main loop. A retry loop that calls `delay()` inside a single lambda will stall CAN RX and the API. Use a `script:` + `delay:` (cooperative) so the loop keeps running between attempts. This is the single most important design constraint of the story.
- **HA events via the YAML action, not the internal API.** Fire `esphome.canbus_command_failed` with `homeassistant.event:` guarded/parameterized by per-field `!lambda`. Do NOT "fix" toward `api::global_api_server->send_homeassistant_action` — that contradicts the deliberate project decision. [Source: memory `project_gateway_ha_event_firing_approach`; the same per-field `!lambda` pattern is already used by the CAT_INPUT handler at `firmware/gateway.yaml:102-108`]
- **Momentary buttons → never dedup/throttle events.** AC4 surfaces a storm; it must not drop a single legitimate event. Buttons emit one frame per gesture; rapid distinct events are valid. [Source: memory `feedback_momentary_buttons_no_state`]
- **HA event data fields are strings.** Use `to_string(...)`/`std::string(...)`. [Source: `_bmad-output/project-context.md`]
- **No magic numbers in YAML lambdas.** Protocol values come from `canbus_protocol.h`; new tuning values (attempt cap, backoff, storm threshold/window) are named constants or substitutions. (NFR-3)
- **Lambda size guard stays.** Every `on_frame` lambda keeps `if (x.size() < CAN_FRAME_SIZE) return ...;` first. (NFR-2)

### Reusable protocol facts

- Error-flag constants already exist for fault semantics if useful: `ERR_NONE`, `ERR_CAN_TX_FAIL`, `ERR_CAN_BUS_OFF` [Source: `firmware/common/canbus_protocol.h`]. These are the *node*-side heartbeat error bits; the gateway-side command-failure path is new and uses the `esphome.canbus_command_failed` event rather than these flags.
- Command frames are built with `can_id(CAT_OUTPUT, node_id)` + `PROTO_V1` + the message-type/param bytes already present in the two services. Gateway→node frames carry params (not room/board) — the CAN ID addresses the node. [Source: `firmware/common/canbus_protocol.h` payload doc block]

### Testing standards

- **No unit-test framework.** The "test" is `esphome compile firmware/gateway.yaml` → SUCCESS on the pinned **ESPHome 2026.5.0**, plus bench observation. [Source: `_bmad-output/project-context.md` → Testing & Validation]
- Behavioral verification is bench-level (requires a node that can NACK / a saturated bus to exercise retry, and a frame-storm injection to exercise AC4). Because Epic 4 owns the bench, full behavioral sign-off of this story depends on bench availability; compile + code review gate the implementation.

### Project Structure Notes

- **Output location:** `_bmad-output/implementation-artifacts/5-1-gateway-command-reliability.md` (matches the `{epic}-{story}-{slug}.md` convention of all prior stories).
- **Epic 5 is not yet in `epics.md`.** epics.md defines Epics 1–4 only; all four are PoC scope and FR-mapped (FR-1…FR-9). This story introduces no new FRs — it is **post-PoC NFR hardening** (reliability/observability) and currently has no FR home. Registering an "Epic 5: Post-PoC — Command Reliability & Fault Surfacing" in `epics.md` and the FR/NFR map is a PM/sprint-planning action that has NOT been done here (avoided unilateral edits to the planning epic breakdown). **Recommendation:** run `bmad-correct-course` or `bmad-sprint-planning` to formalize Epic 5 before scheduling this story.
- **Sequencing:** this story is queued AFTER Epic 4 PoC sign-off. It is `ready-for-dev` (the file exists with full context) but should not be picked up ahead of Epic 4. `sprint-status.yaml` lists `epic-5: backlog` to reflect that it is not the active epic.
- **Stale planning note (not this story's job, but flagged):** epics.md FR-6.4 and Story 3.2 still describe the single-lambda `api::global_api_server` event-firing approach, which Alberto overrode to the `homeassistant.event:` YAML action. This story follows the *actual* decision (memory `project_gateway_ha_event_firing_approach`); the planning docs remain to be reconciled separately.

### References

- [Source: `_bmad-output/implementation-artifacts/deferred-work.md` — "Deferred from: code review of 3-1" (#9) and "Deferred from: code review of 3-2" (#8), and the 2026-06-03 review dispositions]
- [Source: `firmware/gateway.yaml:38-68` — the two API services and their current single-attempt send]
- [Source: `firmware/gateway.yaml:73-129` — `esp32_can` config and the two `on_frame` handlers]
- [Source: `firmware/common/canbus_protocol.h` — `can_id()`, `CAT_OUTPUT`, `PROTO_V1`, `ERR_*`, payload layout doc block]
- [Source: `_bmad-output/project-context.md` — HA event strings rule, no-magic-numbers rule, testing-by-compile rule]
- [Source: memory `project_gateway_ha_event_firing_approach` — fire HA events via `homeassistant.event:` YAML action, not the internal API]
- [Source: memory `feedback_momentary_buttons_no_state` — never dedup/throttle button events; buttons emit one frame per gesture]

## Dev Agent Record

### Agent Model Used

(to be filled by dev-story)

### Debug Log References

### Completion Notes List

### File List
