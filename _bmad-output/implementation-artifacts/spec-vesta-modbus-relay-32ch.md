---
title: 'Vesta 32-channel Modbus relay board driver (Waveshare Modbus RTU Relay 32CH)'
type: 'feature'
created: '2026-07-10'
status: 'ready-for-dev'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 'bb7f173f4bc9499ce3722d4f164e2013d5441003'
final_revision: ''
context: ['{project-root}/_bmad-output/planning-artifacts/adrs/0014-standardized-controller-modbus-io-hardware.md']
warnings: []
---

<intent-contract>

## Intent

**Problem:** ADR-0014 standardizes both HVAC and lighting on the **Waveshare Modbus RTU
Relay 32CH** board. `vesta/packages/devices/modbus-io/` today only has an 8-relay aggregator
(`modbus_relay_board.yaml`), built for boards like the (now-orphaned) KC868-A16. Neither HVAC
(P3, replacing two 8-ch boards @0x2/@0x3 with one 32-ch board @0x2) nor lighting (P4,
`relay_0..31` on the gateway's RS485) can be wired until a 32-channel driver exists.

**Approach:** Add a new aggregator package, `modbus_relay_board_32ch.yaml`, that is
structurally identical to the existing 8-ch one — same required/optional vars
(`controller_id`, `controller_name`, `modbus_address`, `modbus_bus_id`, `update_interval`,
`id_offset`), one `modbus_controller`, N `!include modbus_relay_switch.yaml` (the existing,
**unmodified** single-relay driver) at sequential coil addresses — just N=32 instead of 8.
Also settle, in this spec, a design question the driver's *ADR* deliberately left open: does
`id_offset` support **negative** values, needed for lighting's 0-based `relay_0..relay_31`
(vs. the driver's natural 1-based `switch_number`)? Verify with a real `esphome config` run
rather than assuming ESPHome's substitution engine handles `${1 + -1}`; document whichever
answer is true so P4/P5 don't have to re-derive it.

**Hardware facts** (Waveshare wiki 403s automated fetchers — these are pre-verified, don't
re-fetch): coils `0x0000–0x001F` = channels 1–32; FC 0x01 read / 0x05 write single / 0x0F
write multiple; write values `0xFF00`=on, `0x0000`=off, `0x5500`=toggle; `0x00FF` = all-relay
control; device address via holding register `0x4000` (FC 0x06); default comms 9600 8N1,
address 0x01. **No holding/input registers exist on this board — everything is a coil.**

## Boundaries & Constraints

**Always:**
- Follow `modbus_relay_board.yaml`'s exact shape (header comment block, `defaults:`,
  `modbus_controller:`, `packages:` block of sequential includes) — same var names, same
  optionality, same default values (`update_interval: 5s`, `id_offset: 0`) — so the two
  aggregators are drop-in siblings and any code that already knows one knows the other.
- Reuse `modbus_relay_switch.yaml` **unmodified** — it already takes `controller_id`,
  `switch_number`, `register_address` and is generic over channel count; do not fork or edit
  it.
- The connectivity-status `binary_sensor` uses `register_type: coil` (not the 8-ch board's
  `register_type: read`) at address `0x0000` — the 32CH board's protocol only documents
  coil-based function codes (0x01/0x05/0x0F); `coil` is a confirmed-valid
  `MODBUS_REGISTER_TYPE` value for the `modbus_controller` binary_sensor platform (verify
  against the installed ESPHome's `esphome/components/modbus/helpers.py` if you want to
  double check — it merges `coil`/`holding`/`custom` from `MODBUS_WRITE_REGISTER_TYPE` plus
  `discrete_input`/`read`). Do not copy the 8-ch board's `register_type: read` without
  re-verifying it against this specific board — it is unverified for a coil-only device.
- Verify the negative-`id_offset` question with an actual `esphome config` run (a throwaway
  scratch config under the repo's scratchpad or `/tmp`, **not committed**) before deciding
  the package's final documented behavior. Record the outcome in this spec's Design Notes
  and in the package's own header comment, whichever way it goes:
  - If `${N + id_offset}` with `id_offset: -1` compiles and evaluates correctly (i.e.
    `switch_number` for N=1 becomes literal `0`), document 0-based usage as supported.
  - If it errors (e.g. ESPHome's substitution engine chokes on the double sign or on a
    negative result), document that `id_offset` must stay `>= 0` and that a consumer wanting
    0-based ids (lighting, later) must either accept 1-based ids and shift by one at the
    point it maps ids to bindings, or this package needs a follow-up `zero_based: true` var —
    do **not** silently add that follow-up var yourself; just document the limitation.
- Add a paired doc update (extend `vesta/docs/modbus-relay-board.md`, don't fork a new file —
  the interface is identical, just channel count and connectivity-check register type
  differ) and a compile-checked reference example under `vesta/examples/`.
- One commit (AD-9): package + doc + example land together.

**Block If:** none — this is purely additive (new package, new example); nothing existing
changes behavior.

**Never:**
- Do not touch the existing `modbus_relay_board.yaml` (8-ch) or `modbus_relay_switch.yaml` —
  both stay exactly as they are; this is a new sibling, not a replacement.
- Do not touch `devices/climate-control.yaml` or any HVAC room/floor file — wiring the new
  package into HVAC is P3's job, not this one.
- Do not touch `devices/gateway.yaml` or anything under `lighting/` — wiring lighting's
  0-based relay bank is P4/P5's job. This spec only proves whether the arithmetic *can*
  work; it does not build the lighting actuation path.
- Do not invent a `zero_based`/`start_at_zero` var speculatively "for later" — if negative
  offsets don't work, just document the limitation; adding unused API surface for a future
  phase to maybe use is exactly the premature-abstraction this house's style avoids.
- Do not add a version bump or compatibility shim (pre-live, in-place edits only — and this
  is new code anyway, so the question doesn't really arise).

</intent-contract>

## Code Map

- `vesta/packages/devices/modbus-io/modbus_relay_board_32ch.yaml` — **new file**. Model on
  `vesta/packages/devices/modbus-io/modbus_relay_board.yaml` (read it first): same header
  comment shape (Purpose/Required vars/Optional vars/Dependencies/Exposes/Example), same
  `defaults: {update_interval: 5s, id_offset: 0}`, one `modbus_controller:` entry, then a
  `packages:` block with **32** `!include modbus_relay_switch.yaml` entries
  (`relay_1`..`relay_32` as package keys, `register_address: 0x0000` through `0x001F`,
  `switch_number: ${N + id_offset}` for N=1..32), then the connectivity
  `binary_sensor:` (`platform: modbus_controller`, `register_type: coil`, `address: 0x0000`,
  `device_class: connectivity`, `internal: true`, id `${controller_id}_status`).
- `vesta/docs/modbus-relay-board.md` — add a "32-Channel variant" section: same parameter
  table (identical interface), note the file is `modbus_relay_board_32ch.yaml`, note the
  connectivity check differs (`register_type: coil` vs the 8-ch board's `read`), and add it
  to the "Board compatibility" bullet (Waveshare Modbus RTU Relay 32CH named explicitly,
  alongside the existing KC868-A16 8-ch mention).
- `vesta/examples/modbus_relay_board_32ch.yaml` — **new file**, modeled on
  `vesta/examples/two_zone_radiant_fancoil.yaml`'s boilerplate shape (esphome/esp32/wifi/api/
  ota/logger header — read that file first for the exact pattern), wiring a `uart` + `modbus`
  bus and one `modbus_relay_board_32ch` include (`id_offset: 0`) as a minimal, compile-checked
  reference. This is the file `esphome config`/`esphome compile` actually exercises.

## Tasks & Acceptance

**Execution:**
- [ ] Read `modbus_relay_board.yaml` and `modbus_relay_switch.yaml` fully to confirm the
  exact pattern before writing the new file
- [ ] Create `modbus_relay_board_32ch.yaml` per the Code Map -- gives both HVAC (P3) and
  lighting (P4) a 32-channel driver with the same interface as the existing 8-ch one
- [ ] Resolve the negative-`id_offset` question with a throwaway (uncommitted) scratch
  compile, then write the answer into this package's header comment and this spec's Design
  Notes -- P4/P5 need this settled, not re-discovered
- [ ] Extend `vesta/docs/modbus-relay-board.md` with the 32-ch variant section
- [ ] Create `vesta/examples/modbus_relay_board_32ch.yaml` -- gives the new package a
  compile-checked consumer (vesta has no other CI/test harness populated yet — this is the
  actual verification surface per `vesta/docs/testing-strategy.md`)
- [ ] Run `esphome config` and `esphome compile` on the new example

**Acceptance Criteria:**
- Given `modbus_relay_board_32ch.yaml`, when included with `id_offset: 0`, then it exposes
  `switch.relay_1` through `switch.relay_32` and `binary_sensor.<controller_id>_status`
  (internal) — matching the 8-ch board's exposure shape at 4x the channel count.
  end change (`id_offset: 0`, `modbus_address: 0x2`), `esphome config` and `esphome compile`
  both exit 0.
- Given the negative-`id_offset` scratch check, when its result is known, then the package's
  header comment states plainly whether `id_offset: -1` (→ `relay_0..relay_31`) is supported,
  and this spec's Design Notes records the same finding with the evidence (the exact error,
  if any).
- Given `git diff --stat` after this spec, when compared against the file list above, then
  `modbus_relay_board.yaml` and `modbus_relay_switch.yaml` show **zero** changes.

## Design Notes

_Fill in during execution: the negative-`id_offset` finding goes here (which form was
tested, exact command, exact result/error text, and the resulting recommendation for P4/P5)._

The connectivity-status sensor deliberately diverges from the 8-ch board's `register_type:
read` to `coil` — this is a considered correction, not an oversight: the 32CH board's
protocol only exposes coil-based function codes, so `read` (whatever exact Modbus function it
maps to in ESPHome's `ModbusRegisterType::READ`) is unverified against this specific board and
`coil` is the one guaranteed to be answerable by the device per its documented FC support.

`update_interval: 5s` default matches the 8-ch board; ADR-0014's Risks section flags that
lighting's fallback path (P5) may want a shorter interval or `command_throttle` so polling
doesn't queue ahead of a fallback-triggered write — that's P4/P5's tuning concern at the
entry-point level, not this package's default.

## Verification

**Commands:**
- `esphome config vesta/examples/modbus_relay_board_32ch.yaml` -- expected: exits 0
- `esphome compile vesta/examples/modbus_relay_board_32ch.yaml` -- expected: exits 0
- `git diff --stat` -- expected: `modbus_relay_board_32ch.yaml` (new),
  `vesta/docs/modbus-relay-board.md` (modified), `vesta/examples/modbus_relay_board_32ch.yaml`
  (new); `modbus_relay_board.yaml` and `modbus_relay_switch.yaml` unchanged
- `grep -c "!include" vesta/packages/devices/modbus-io/modbus_relay_board_32ch.yaml` --
  expected: 32

**Manual checks (if no CLI):**
- Read the new package top to bottom: confirm all 32 `register_address` values are unique
  and sequential (`0x0000`–`0x001F`), and all 32 `switch_number` expressions correctly add
  `id_offset`.

## Spec Change Log

## Review Triage Log

## Auto Run Result

Status: ready-for-dev — not yet executed.
