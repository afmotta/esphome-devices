---
title: 'Vesta 32-channel Modbus relay board driver (Waveshare Modbus RTU Relay 32CH)'
type: 'feature'
created: '2026-07-10'
status: 'done'
review_loop_iteration: 1
followup_review_recommended: false
baseline_revision: 'bb7f173f4bc9499ce3722d4f164e2013d5441003'
final_revision: ''
baseline_commit: 'e81671fa427caeb82f802c2d7cc8475163b2d93b'
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
address 0x01. **No holding/input registers exist on this board, and no coil outside the
32 relay channels is documented as a status/heartbeat bit — every documented coil address is
one of the 32 relay channels themselves.** There is no register on this board that represents
"is the board alive" independent of "what state is some relay in." (Revised in review-loop 1 —
see Spec Change Log: this rules out a `binary_sensor` connectivity check the way the 8-ch
board has one.)

## Boundaries & Constraints

**Always:**
- Follow `modbus_relay_board.yaml`'s exact shape (header comment block, `defaults:`,
  `modbus_controller:`, `packages:` block of sequential includes) — same var names, same
  optionality, same default values (`update_interval: 5s`, `id_offset: 0`) — so the two
  aggregators are drop-in siblings and any code that already knows one knows the other.
- Reuse `modbus_relay_switch.yaml` **unmodified** — it already takes `controller_id`,
  `switch_number`, `register_address` and is generic over channel count; do not fork or edit
  it.
- **Do not add a connectivity-status `binary_sensor` to this package.** (Revised in
  review-loop 1 — see Spec Change Log.) The 8-ch board's status sensor works because its
  `register_type: read` polls an independent register outside the relay coil range. This
  board has no such register — every documented coil is one of the 32 relay channels. Polling
  any of them for "connectivity" would alias the sensor to that relay's actual on/off state
  (e.g. address `0x0000` == `relay_1`'s own coil), so a user switching relay 1 off would make
  the board falsely report as disconnected. Ship the 32 relay switches and skip the
  connectivity sensor entirely rather than ship one that lies. Communication failures already
  surface per-switch: ESPHome's `modbus_controller` marks a switch unavailable on read
  timeout, so there is no loss of failure visibility, just no single aggregate "board status"
  entity. Document this omission and its reasoning in both the package header comment and
  `vesta/docs/modbus-relay-board.md` (don't leave it silently absent) so nobody re-adds a
  colliding sensor later without knowing why it was left out.
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
  comment shape (Purpose/Required vars/Optional vars/Dependencies/Exposes/Example — but the
  header's own worked example must not include a connectivity sensor either), same
  `defaults: {update_interval: 5s, id_offset: 0}`, one `modbus_controller:` entry, then a
  `packages:` block with **32** `!include modbus_relay_switch.yaml` entries
  (`relay_1`..`relay_32` as package keys, `register_address: 0x0000` through `0x001F`,
  `switch_number: ${N + id_offset}` for N=1..32). **No `binary_sensor:` block** (revised in
  review-loop 1 — see Boundaries & Constraints and Spec Change Log for why). Add a one-line
  comment near the top explaining the omission so it reads as a decision, not a gap: this
  board has no coil outside the 32 relay channels to poll for connectivity without aliasing a
  relay's own state.
- `vesta/docs/modbus-relay-board.md` — add a "32-Channel variant" section: same parameter
  table as the 8-ch board (keep `controller_name` in the table for interface parity/drop-in
  symmetry with the 8-ch board, but note next to it that this variant currently accepts and
  ignores it — there's no status sensor to name, since this board has no independent status
  register), note the file is `modbus_relay_board_32ch.yaml`, explicitly call out **no
  connectivity sensor** and why (no independent status register on this board — polling any
  documented coil would alias a relay's state), and add it to the "Board compatibility" bullet
  (Waveshare Modbus RTU Relay 32CH named explicitly, alongside the existing KC868-A16 8-ch
  mention). The "Exposed Entities" table for this variant lists only the 32 switches — no
  `binary_sensor.*_status` row — and must show both the positive and negative `id_offset`
  forms (`switch.relay_{1+offset}`..`switch.relay_{32+offset}`, and — when `id_offset: -1` —
  `switch.relay_0`..`switch.relay_31`) so the table doesn't contradict the negative-offset
  prose next to it (a real inconsistency from review-loop 1: the first pass documented
  negative offsets in prose but left the table showing only the positive form).
- `vesta/examples/modbus_relay_board_32ch.yaml` — **new file**, modeled on
  `vesta/examples/two_zone_radiant_fancoil.yaml`'s boilerplate shape (esphome/esp32/wifi/api/
  ota/logger header — read that file first for the exact pattern), wiring a `uart` + `modbus`
  bus and one `modbus_relay_board_32ch` include (`id_offset: 0`) as a minimal, compile-checked
  reference. This is the file `esphome config`/`esphome compile` actually exercises.

## Tasks & Acceptance

**Execution:**
- [x] Read `modbus_relay_board.yaml` and `modbus_relay_switch.yaml` fully to confirm the
  exact pattern before writing the new file
- [x] Create `modbus_relay_board_32ch.yaml` per the Code Map -- gives both HVAC (P3) and
  lighting (P4) a 32-channel driver with the same interface as the existing 8-ch one, **minus
  the connectivity binary_sensor** (see Boundaries & Constraints — no independent status
  register exists on this board)
- [x] Resolve the negative-`id_offset` question with a throwaway (uncommitted) scratch
  compile, then write the answer into this package's header comment and this spec's Design
  Notes -- P4/P5 need this settled, not re-discovered (resolved in review-loop 0, finding kept
  and re-verified unchanged against the re-derived file)
- [x] Extend `vesta/docs/modbus-relay-board.md` with the 32-ch variant section, including the
  Exposed Entities table showing both positive- and negative-offset forms, and the explicit
  "no connectivity sensor" note
- [x] Create `vesta/examples/modbus_relay_board_32ch.yaml` -- gives the new package a
  compile-checked consumer (vesta has no other CI/test harness populated yet — this is the
  actual verification surface per `vesta/docs/testing-strategy.md`)
- [x] Run `esphome config` and `esphome compile` on the new example

**Acceptance Criteria:**
- Given `modbus_relay_board_32ch.yaml`, when included with `id_offset: 0`, then it exposes
  `switch.relay_1` through `switch.relay_32` and **no other entities** — matching the 8-ch
  board's switch exposure shape at 4x the channel count, minus the connectivity sensor this
  board cannot honestly provide. **Met**: package includes `modbus_relay_switch.yaml` 32
  times at coils `0x0000`–`0x001F`; `grep -c binary_sensor` returns 0.
- Given the compile-checked example change (`id_offset: 0`, `modbus_address: 0x2`), when
  run, then `esphome config` and `esphome compile` both exit 0. **Met**: both re-verified
  against the re-derived `vesta/examples/modbus_relay_board_32ch.yaml` (ESPHome 2026.5.0,
  `esp32dev`/esp-idf) — config validated, compile succeeded (`SUCCESS`).
- Given the negative-`id_offset` scratch check, when its result is known, then the package's
  header comment states plainly whether `id_offset: -1` (→ `relay_0..relay_31`) is supported,
  and this spec's Design Notes records the same finding with the evidence (the exact error,
  if any). **Met**: see Design Notes (finding preserved from review-loop 0, KEEP-listed in
  the Spec Change Log).
- Given `git diff --stat` after this spec, when compared against the file list above, then
  `modbus_relay_board.yaml` and `modbus_relay_switch.yaml` show **zero** changes. **Met**:
  verified via `git diff --stat` on both sibling files (empty output).
- Given the package file, when grepped for `binary_sensor`, then there are **zero** matches —
  confirms the review-loop-1 fix actually landed (no aliased connectivity sensor). **Met**.

## Design Notes

**Negative `id_offset` finding:** Two forms were tested with a throwaway scratch config
(uncommitted, deleted after the check).

1. `id_offset` passed as a top-level `substitutions:` string (`id_offset: "-1"`), consumed via
   `${1 + id_offset}` inside a package `vars:` block → **fails**:
   `TypeError Error evaluating jinja expression '${1 + id_offset}': unsupported operand
   type(s) for +: 'int' and 'EStr'`. Substitution values are always strings (`EStr`), and
   ESPHome's jinja arithmetic refuses to add an `int` and a string.
2. `id_offset` passed as a numeric `vars:` value one level up (i.e. `vars: { id_offset: -1 }`
   on the package `!include`, exactly how `modbus_relay_board.yaml`/`_32ch.yaml` already
   receive all their other vars — no `substitutions:` involved) → **succeeds**: `esphome
   config` resolved `switch_number: ${1 + id_offset}` to literal `0`, producing
   `switch.relay_0` as expected for a 0-based scheme.

**Recommendation for P4/P5:** negative `id_offset` (e.g. `-1` for `relay_0..relay_31`) is
supported — but only when passed as a numeric `vars` value on the `!include`, not as a quoted
string or through a `substitutions:` block. Both the 8-ch and 32-ch packages already receive
`id_offset` this way (`vars: { id_offset: <int> }`), so P4/P5's gateway wiring should follow
the same convention and does not need a `zero_based`/`start_at_zero` var. Documented in the
package's header comment and in `vesta/docs/modbus-relay-board.md`.

**`grep -c "!include"` count is 33, not the spec's stated 32:** the package's header comment
includes a usage example containing one `!include` line (mirroring the 8-ch board's own
header, which likewise has 9 for its 8 real includes). This is the established convention,
not a deviation — the spec's expected count of 32 didn't account for the header comment.

**Connectivity sensor removed (review-loop 1):** the first pass added a `binary_sensor` at
`register_type: coil, address: 0x0000` to mirror the 8-ch board's status sensor. Both review
subagents (Blind Hunter, Edge Case Hunter) independently flagged that this address is
identical to `relay_1`'s own coil — so the "connectivity" sensor was actually just relay_1's
on/off state relayed under a `device_class: connectivity` label. Root cause: this board has no
holding/input registers and no documented coil outside the 32 relay channels, so there is no
register that represents "board alive" independent of "some relay's current state." The 8-ch
board avoids this because its status check uses `register_type: read` — a different register
space (holding/input) that doesn't collide with any relay's coil. Since the 32CH board has no
equivalent independent register, the correct fix is to ship the 32 switches only and document
the omission, not to fake a connectivity indicator against a register that means something
else. See Spec Change Log for the full triage record.

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
  expected: 33 (32 real includes + 1 in the header comment's worked example, matching the
  8-ch board's own convention of N+1)
- `grep -c "binary_sensor" vesta/packages/devices/modbus-io/modbus_relay_board_32ch.yaml` --
  expected: 0 (confirms the review-loop-1 fix: no aliased connectivity sensor)

**Manual checks (if no CLI):**
- Read the new package top to bottom: confirm all 32 `register_address` values are unique
  and sequential (`0x0000`–`0x001F`), and all 32 `switch_number` expressions correctly add
  `id_offset`.

## Spec Change Log

### review-loop 1 (2026-07-10)

**Triggering finding (bad_spec, high severity):** both Blind Hunter and Edge Case Hunter
independently flagged that the connectivity `binary_sensor` (`register_type: coil, address:
0x0000`) polled the exact same register as `relay_1`'s own coil, so it silently mirrored
relay_1's on/off state instead of representing board connectivity — a user switching relay 1
off would make the board falsely report as disconnected. Root cause was in the spec's original
`intent-contract` (Boundaries & Constraints), which explicitly mandated `register_type: coil`
at `address: 0x0000` for the status sensor without checking that address against the relay
coil range.

**What was amended:** Intent (hardware facts), Boundaries & Constraints, Code Map, Tasks &
Acceptance, Design Notes, and Verification all updated to drop the connectivity `binary_sensor`
requirement entirely — this board has no register that represents "alive" independent of "some
relay's state," so shipping no connectivity sensor (with the reasoning documented) is more
honest than shipping one that lies.

**Known-bad state avoided:** do not reintroduce a `binary_sensor` on this package unless a
genuinely independent status register is confirmed for this specific board (not assumed from
the relay coil range or the "all-relay control" address `0x00FF`, which also isn't independent
of relay state).

**KEEP instructions (positive preservation — carry these into re-derivation unchanged):**
- The 32-relay `!include` block shape (32x `modbus_relay_switch.yaml`, coils `0x0000`–`0x001F`,
  `switch_number: ${N + id_offset}`) was correct and un-flagged by either reviewer — keep as-is.
- The negative-`id_offset` finding (Design Notes: numeric `vars` value works, string
  substitution doesn't) was correct and un-flagged — keep the finding and its wording.
- The `grep -c "!include"` count of 33 (32 + 1 header-comment example) is correct and matches
  the 8-ch board's own convention — keep, don't "fix" it down to 32.
- The example config's boilerplate shape (esp32dev, generic UART pins, modeled on
  `two_zone_radiant_fancoil.yaml`) is correct per this spec's explicit scope boundary (real
  ADR-0014 hardware wiring is P3/P4's job, not this one) — keep as-is despite Blind Hunter's
  note about it; that finding was rejected as out-of-scope-by-design, not a real gap.

## Review Triage Log

**review-loop 1:**
- bad_spec (high) — connectivity `binary_sensor` aliases `relay_1`'s coil → spec amended,
  sensor removed. Loopback triggered.
- patch — doc wording "verified against this specific board" overclaimed hardware
  verification for the register-type choice → moot, the sensor (and that doc claim) no longer
  exist after the fix.
- patch — "Exposed Entities" doc table didn't show the negative-offset form the adjacent prose
  described → folded into the amended Code Map instruction for the re-derived docs section.
- defer — no lower-bound guard on `id_offset` for values `< -1` (would yield invalid entity
  ids like `relay_-1`) → real but out of this spec's explicit scope (spec forbids adding
  speculative validation vars); appended to `deferred-work.md` for P4/P5 or a future hardening
  pass to pick up.
- reject — cross-board stagger-by-32-vs-8 collision risk (pre-existing pattern, not introduced
  by this change), generic example pins not matching ADR-0014 hardware (explicitly out of
  scope per this spec's Boundaries), missing test/CI artifact (out of scope per
  `vesta/docs/testing-strategy.md`'s stated layer-1/2-only coverage for modbus-io packages),
  `update_interval: 5s` tuning (already addressed in original Design Notes as P4/P5's concern),
  controller_name collision risk (subsumed by the primary fix), firmware-revision caveat
  (subsumed by the primary fix — no register is claimed "verified" anymore).

**review-loop 1, second pass (post-fix re-review):** neither reviewer re-flagged the removed
connectivity sensor — the primary fix held. Remaining findings were all documentation
completeness/hardening, no new bad_spec/intent_gap, so no further loopback:
- patch — `controller_name` documented "Required" while unused (both reviewers, independently)
  → reclassified Optional in package header comment and docs table.
- patch — `update_interval: 5s`'s untested-at-scale caveat lived only in this spec's Design
  Notes, never reached user-facing docs → added to the package header comment and docs
  Board Parameters table.
- patch — Exposed Entities table's two rows (positive/negative offset) could misread as 64
  simultaneous switches → added a framing sentence.
- patch — "Board compatibility" bullet read confusingly (led with "8-relay" then extended to a
  32-relay board) → reworded into two clearly separated statements.
- patch — stagger-by-8 guidance didn't note the 32ch board needs stagger-by-32 → added an
  explicit note (this reverses the loop-1 "reject" on the same underlying topic — the specific,
  actionable form of it, a one-line doc note, is now in scope even though the general
  cross-board-collision-validation ask remains rejected as pre-existing/out-of-scope).
- defer — `id_offset` has no type check (non-integer values silently break) → appended to
  `deferred-work.md`, same root cause and scope rationale as the loop-1 bounds-guard deferral.
- defer — negative-`id_offset` behavior has no persisted regression check (only `id_offset: 0`
  is compile-checked in the committed example) → appended to `deferred-work.md`.
- reject — no automated uniqueness/sequence check across the 32 hand-written includes
  (pre-existing pattern shared with the 8-ch board), cross-board `modbus_address` collision
  risk (pre-existing gap in both boards' docs, not introduced here), unattributed "0x00FF"
  hardware fact (sourced from the ADR's own pre-verified, unfetchable vendor reference — same
  standard applied throughout this spec's hardware facts), dead-parameter-tracking concern
  (resolved by the `controller_name` patch above).

All patches applied directly; `esphome config`/`esphome compile` re-verified green after each
patch round. No further review loop needed.

## Auto Run Result

Status: in-review — review-loop 1 complete (one bad_spec loopback + one post-fix patch round),
both review passes clean of new bad_spec/intent_gap findings. Ready to present.

## Suggested Review Order

**Package structure (the new driver)**

- Entry point: 32-channel aggregator, same shape as the 8-ch sibling minus the sensor block.
  [`modbus_relay_board_32ch.yaml:71`](../../vesta/packages/devices/modbus-io/modbus_relay_board_32ch.yaml#L71)

- First and last of the 32 sequential relay includes — confirms the coil/id_offset arithmetic.
  [`modbus_relay_board_32ch.yaml:82`](../../vesta/packages/devices/modbus-io/modbus_relay_board_32ch.yaml#L82)
  [`modbus_relay_board_32ch.yaml:268`](../../vesta/packages/devices/modbus-io/modbus_relay_board_32ch.yaml#L268)

**Connectivity-sensor removal (the review-loop-1 fix)**

- Why there's no `binary_sensor` here: this board has no register independent of relay state.
  [`modbus_relay_board_32ch.yaml:8`](../../vesta/packages/devices/modbus-io/modbus_relay_board_32ch.yaml#L8)

- Same reasoning surfaced in user-facing docs, plus the negative-offset caveat this fix compounds with.
  [`modbus-relay-board.md:129`](../../vesta/docs/modbus-relay-board.md#L129)

**id_offset semantics (negative-offset support + its limits)**

- `controller_name` downgraded to Optional and `id_offset` caveats (bounds/type/staleness) documented.
  [`modbus_relay_board_32ch.yaml:23`](../../vesta/packages/devices/modbus-io/modbus_relay_board_32ch.yaml#L23)

- Doc-side parameter table mirrors the header comment's caveats for a reader who skips the code.
  [`modbus-relay-board.md:111`](../../vesta/docs/modbus-relay-board.md#L111)

- Stagger-by-32 (not 8) note — the one concrete finding reclassified from reject to patch in the second review pass.
  [`modbus-relay-board.md:147`](../../vesta/docs/modbus-relay-board.md#L147)

**Compile-checked reference (peripheral)**

- Minimal wiring exercised by `esphome config`/`esphome compile`; only `id_offset: 0` is covered here.
  [`examples/modbus_relay_board_32ch.yaml:60`](../../vesta/examples/modbus_relay_board_32ch.yaml#L60)
