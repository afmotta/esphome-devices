---
title: 'Lighting gateway swap — T-Connect Pro + Waveshare Relay 32CH, exposed to HA (ADR-0013 item 3)'
type: 'feature'
created: '2026-07-10'
status: 'ready-for-dev'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 'bb7f173f4bc9499ce3722d4f164e2013d5441003'
final_revision: ''
context: ['{project-root}/_bmad-output/planning-artifacts/adrs/0014-standardized-controller-modbus-io-hardware.md', '{project-root}/_bmad-output/implementation-artifacts/spec-vesta-modbus-relay-32ch.md', '{project-root}/_bmad-output/implementation-artifacts/spec-hvac-controller-swap-t-connect-pro.md']
warnings: []
---

<intent-contract>

## Intent

**Problem:** `devices/gateway.yaml` today is a hand-rolled Waveshare ESP32-S3-RS485-CAN
config (its own `esp32`/`wifi`/`api.encryption`/`ota` blocks, no shared board file) with
**no relay hardware at all** — ADR-0013's fallback is log-only because there is nothing to
switch. Per ADR-0014 the gateway moves onto the same `boards/t-connect-pro.yaml` board file
P3 creates for HVAC (Ethernet instead of WiFi), and gains a Waveshare Modbus RTU Relay 32CH
bank on its RS485 bus, mirroring the address HVAC's own relay bank uses (`0x2`) so a spare
board swaps into either system unmodified.

**Approach:** Swap the board layer only — drop gateway.yaml's hand-rolled esp32/network/api/
ota blocks in favor of composing `t-connect-pro.yaml` (Ethernet), retarget the CAN pins to
the new board's transceiver (IO6/IO7), and add the relay bank as a **live-path-only** slice:
relays become real `switch` entities HA can drive directly (closing ADR-0013 open item 3),
but the fallback path (the two log-only branches in `lighting/packages/buttons.yaml`) is
**not** wired up here — that is P5's job, in its own commit, because a relay-id→switch
lookup store with no caller yet would be exactly the "half-finished implementation" this
house's style avoids. This spec's slice is complete and independently valuable on its own:
lights become HA-switchable through the gateway even before the fallback exists.

**Depends on:** P2 (the 32-ch vesta package must exist) and P3 (the shared board file must
exist — read that spec's Code Map for the exact `boards/t-connect-pro.yaml` shape you're
composing here; do not re-derive or duplicate it).

## Boundaries & Constraints

**Always:**
- Compose `boards/t-connect-pro.yaml` with `enable_ethernet: true` — same board file P3
  builds for HVAC, not a fork. If P3 landed with `framework: arduino` instead of the
  preferred `esp-idf` (recorded in that spec's Design Notes), this spec inherits whatever
  the board file actually contains; do not re-litigate that choice here.
- Preserve every substitution/behavior that is genuinely gateway-specific and not part of
  the board file: `ha_heartbeat_ttl_ms`, `ack_timeout_ms`, `node_lost_timeout_ms` (canbus/
  lighting package tuning knobs, unrelated to hardware), the explicit `logger: level: DEBUG`
  override, and the `esphome.includes:` list (the five protocol headers) — these stay in
  `devices/gateway.yaml` itself, they don't move into the board file.
- Retarget `can_tx_pin`/`can_rx_pin` from `GPIO15`/`GPIO16` to **`GPIO6`/`GPIO7`** (the
  T-Connect Pro's onboard CAN transceiver pins, per ADR-0014) — this is a substitution
  override already wired through `canbus/packages/health.yaml`'s `can_tx_pin`/`can_rx_pin`
  vars; no change needed inside `health.yaml` itself.
- Secrets: the board file expects `${encryption_key}` and `${ota_password}` substitutions
  (matching `boards/waveshare-s3.yaml`'s existing pattern). Gateway has no locals/remotes
  wrapper and reads secrets directly — add
  `substitutions: {encryption_key: !secret api_encryption_key, ota_password: !secret
  ota_password}` to `devices/gateway.yaml` so the board's substitution names resolve. This
  keeps consuming the **same actual secret** (`api_encryption_key`) gateway already reads
  today — do not rename the secret itself or touch `devices/secrets.yaml.example`; the
  broader secrets-naming inconsistency across the repo (climate-control's locals/remotes
  wrapper references a differently-named `encryption_key` secret) is out of scope here —
  it's a separate, already-identified cross-cutting cleanup for the docs-sweep phase.
- Add `defaults: {device_name: canbus-gateway, friendly_name: "CAN Bus Gateway"}` so the
  board file's `esphome: {name: ${device_name}, friendly_name: ${friendly_name}}` resolves —
  matching the exact pattern `devices/climate-control.yaml` already uses (read it for the
  shape). Gateway's own `esphome:` block then keeps only `includes:` (the board file already
  sets `comment`/`min_version`; gateway's `comment` in its current header — "WaveShare
  ESP32-S3-RS485-CAN" via the board's `comment:` field — updates automatically since it's
  now the board file's job, not gateway's).
- Add `modbus: {id: rs485_bus, uart_id: modbus_uart}` to `devices/gateway.yaml` — the board
  file only defines the physical `modbus_uart` UART (AD-4: hardware-level truth lives in the
  board; the bus binding is entry-point composition), exactly mirroring how
  `devices/climate-control.yaml` already owns its own `modbus:` block.
- Include the 32-ch relay package with `modbus_address: 0x2` (mirrors HVAC's relay bank
  address per ADR-0014 §4 — this is deliberate, not a coincidence to "fix") and whichever
  `id_offset` P2's spec determined actually works for 0-based numbering:
  - If P2 confirmed negative `id_offset` works: use `id_offset: -1` → `relay_0..relay_31`
    (ADR-0013's progressive-id convention, 0-based).
  - If P2 found negative offsets don't work: use `id_offset: 0` → `relay_1..relay_32`, and
    note in this spec's Design Notes that lighting's relay ids are 1-based, not 0-based as
    ADR-0013's example bindings show — P5 (and any future binding authoring) must account
    for the one-off shift, it does not block this spec.
- Relay switches must be **non-internal** (the vesta package's default) so they reach Home
  Assistant automatically over the API — this alone is ADR-0013 open item 3 (live-path relay
  entities), closed by this spec.
- One commit (AD-9): board swap + relay bank land together, gateway compiles green with the
  existing canbus/lighting behavior untouched.

**Block If:** none — every disposition here is fixed by ADR-0014 and by P2/P3's already-made
choices; there is no new design decision for Alberto to weigh in on.

**Never:**
- Do not touch `lighting/packages/buttons.yaml`, `canbus/packages/health.yaml`, or any
  `canbus/protocol/*.h` header — the button-decode/gate/health logic is completely unchanged
  by this spec; only the board and the addition of relay hardware change.
- Do not build the relay-id→switch-pointer store, any header-accessor pattern, or wire
  either of `buttons.yaml`'s two fallback branches — that is P5's complete, self-contained
  slice. Landing half of it here (a store nothing calls) would violate AD-9.
- Do not touch `registry/bindings.yaml`, `canbus/tools/bindings.py`, or any generated
  artifact (`canbus/protocol/bindings.h`, `canbus/protocol/node_map.h`,
  `canbus/home-assistant/ha_manifest_package.yaml`) — none of those change until P5 (the
  `MAX_RELAY_ID` bound) or bindings authoring (explicitly out of this whole epic's scope).
- Do not touch `devices/climate-control.yaml`, `boards/waveshare-s3*.yaml`, or anything
  under `hvac/` — this is the lighting/canbus device only.
- Do not add a `devices/locals/gateway.yaml` / `devices/remotes/gateway.yaml` deploy wrapper
  "while we're in here" — the gateway's direct-secrets-read deployment model is a
  pre-existing, deliberate difference from climate-control (no wrapper exists today); adding
  one is a separate concern nobody asked for in this spec.
- Do not add a version bump or compatibility shim (pre-live, in-place edits only).

</intent-contract>

## Code Map

- `devices/gateway.yaml`:
  - Header comment (~lines 1-19): update "Hardware: Waveshare ESP32-S3-RS485-CAN" →
    "Hardware: LilyGO T-Connect Pro"; update the "physical split into separate devices is
    deferred to ADR-0013's relay-hardware decision" sentence — ADR-0014 already resolved
    this (no further split; the gateway keeps composing canbus + lighting packages per AD-4,
    now alongside relay hardware).
  - `substitutions:` (~lines 21-29): keep `ha_heartbeat_ttl_ms`/`ack_timeout_ms`/
    `node_lost_timeout_ms` as-is; change `can_tx_pin: GPIO15` → `GPIO6`, `can_rx_pin:
    GPIO16` → `GPIO7`; add `encryption_key: !secret api_encryption_key`,
    `ota_password: !secret ota_password`.
  - Add `defaults: {device_name: canbus-gateway, friendly_name: "CAN Bus Gateway"}`.
  - `packages:` (~lines 31-34): add `base: !include {file: ../boards/t-connect-pro.yaml,
    vars: {enable_ethernet: true}}` (first — it defines `can0`'s host board and
    `modbus_uart`); keep `health`/`buttons` includes as-is; add a third entry for the relay
    bank, `relays: !include {file: ../vesta/packages/devices/modbus-io/modbus_relay_board_32ch.yaml,
    vars: {controller_id: relay_board_1, controller_name: "Relay Board 1", modbus_address:
    0x2, modbus_bus_id: rs485_bus, update_interval: 2s, id_offset: <per P2's finding>}}`.
  - `esphome:` (~lines 36-44): remove `name`/`friendly_name` (now via `defaults:` +
    board substitution); keep `includes:` (the five protocol headers) unchanged.
  - Remove the hand-rolled `esp32:` block (~lines 46-50) — now the board file's job.
  - Keep `logger: {level: DEBUG}` (~lines 52-54) exactly as-is (explicit override).
  - Remove the hand-rolled `wifi:` block (~lines 56-59) — the board's ethernet variant
    replaces it (`enable_ethernet: true`).
  - Remove the hand-rolled `api: {encryption: {key: !secret api_encryption_key}}` block
    (~lines 61-66) — now the board file's `${encryption_key}` substitution, fed by the new
    top-level substitution above. `buttons.yaml`'s `api.services`/`on_client_disconnected`
    additions still merge in exactly as they do today (unaffected by this change).
  - Remove the hand-rolled `ota:` block (~lines 68-72) — now the board file's
    `${ota_password}` substitution.
  - Add `modbus: {id: rs485_bus, uart_id: modbus_uart}`.

## Tasks & Acceptance

**Execution:**
- [ ] Read `boards/t-connect-pro.yaml` (from P3) and
  `vesta/packages/devices/modbus-io/modbus_relay_board_32ch.yaml` (from P2, including its
  Design Notes for the `id_offset` finding) before editing anything
- [ ] Rewrite `devices/gateway.yaml` per the Code Map: board composition, CAN pin retarget,
  secrets substitutions, relay bank package, `modbus:` bus binding, header comment fixes
- [ ] Run `esphome compile devices/gateway.yaml`
- [ ] Run the full canbus verification battery (python + native C++ tests) to confirm
  nothing in the unchanged `health.yaml`/`buttons.yaml` behavior regressed

**Acceptance Criteria:**
- Given `esphome compile devices/gateway.yaml`, when run after this swap, then it exits 0.
- Given the compiled gateway config, when its entity list is inspected, then
  `switch.relay_0` through `switch.relay_31` (or `relay_1..relay_32`, per P2's `id_offset`
  finding) are present, non-internal, and reachable over the Home Assistant API — this is
  ADR-0013 open item 3, closed.
- Given the same compiled config, when the CAN bus definition is inspected, then
  `can_tx_pin`/`can_rx_pin` resolve to `GPIO6`/`GPIO7`, and every other canbus/lighting
  substitution (`ha_heartbeat_ttl_ms`, `ack_timeout_ms`, `node_lost_timeout_ms`) is unchanged
  from before this spec.
- Given `git diff --stat` after this spec, when compared against the file list above, then
  **only `devices/gateway.yaml`** shows changes — no file under `lighting/packages/`,
  `canbus/packages/`, `canbus/protocol/`, or `registry/` is touched.
- Given the standing verification battery (`python3 canbus/tests/test_bindings.py`,
  `test_generate_exports.py`, `test_push_gate.py`, and the five native C++ tests), when run
  after this spec, then all pass exactly as before — this spec changes hardware composition,
  not any tested logic.

## Design Notes

_Fill in: which `id_offset` was used (from P2's finding) and the resulting relay-id range
(`relay_0..31` or `relay_1..32`)._

The relay bank's `update_interval: 2s` is a starting point, not a tuned value — ADR-0014's
Risks section flags that polling 32 coils could queue ahead of a fallback-triggered write
once P5 wires actuation; revisit then if latency is a problem (the `modbus_controller`
component's `command_throttle` option is the likely lever, not a faster/slower poll alone).

This spec deliberately does not exercise the fallback path at all — with `registry/
bindings.yaml` still empty, there is nothing for P5's eventual `binding_find()` calls to
match anyway. The relay bank being live-path-only (HA-switchable, fallback untouched) is a
genuinely shippable, independently useful state, not a partial one.

## Verification

**Commands:**
- `esphome compile devices/gateway.yaml` -- expected: exits 0
- `python3 canbus/tests/test_bindings.py && python3 canbus/tests/test_generate_exports.py && python3 canbus/tests/test_push_gate.py` -- expected: all pass
- `g++ -std=c++17 -Wall -Wextra canbus/tests/test_protocol.cpp -o /tmp/proto && /tmp/proto` -- expected: passes (repeat for `test_ha_arbitration.cpp`, `test_node_health.cpp`, `test_bridge_forwarding.cpp`, `test_bindings_contract.cpp`)
- `git diff --stat` -- expected: only `devices/gateway.yaml` changed

**Manual checks (if no CLI):**
- Read the rewritten `devices/gateway.yaml` top to bottom: confirm nothing from
  `lighting/packages/buttons.yaml`'s api services, globals, or `on_frame` handler was
  touched — this spec only changes what physical hardware backs the entry point.

## Spec Change Log

## Review Triage Log

## Auto Run Result

Status: ready-for-dev — not yet executed.
