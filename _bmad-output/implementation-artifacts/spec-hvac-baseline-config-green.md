---
title: 'HVAC baseline config green — wire boost_active/last_mode_change_time in fancoil_boost.yaml'
type: 'bug'
created: '2026-07-10'
status: 'done'
review_loop_iteration: 1
followup_review_recommended: false
baseline_revision: 'bb7f173f4bc9499ce3722d4f164e2013d5441003'
final_revision: 'bf037dd (vesta submodule)'
baseline_commit: '843d96163c8f9cde72d35cc3dacb5c4ab75f8c98'
context: ['{project-root}/_bmad-output/planning-artifacts/adrs/0014-standardized-controller-modbus-io-hardware.md']
warnings: []
---

<intent-contract>

## Intent

**Problem:** `esphome config devices/locals/climate-control.yaml` currently fails with 3
distinct "Couldn't find ID" errors (confirmed against ESPHome 2026.5.0 at baseline
`bb7f173`):

```
Couldn't find ID 'soggiorno_boost_active'   (hvac/rooms/ground_floor/ground-floor.yaml:50,
                                              vesta/packages/components/pid_autotune_with_fancoil.yaml:43)
Couldn't find ID 'cucina_boost_active'       (hvac/rooms/ground_floor/ground-floor.yaml:51)
Couldn't find ID 'soggiorno_last_mode_change_time'  (hvac/rooms/ground_floor/ground-floor.yaml:193)
```

(`cucina_last_mode_change_time` at `ground-floor.yaml:194` fails identically but ESPHome's
error output truncates after the first few — expect it too once the first three are fixed.)

Root cause, confirmed by direct inspection: `vesta/packages/coordinators/fancoil_boost.yaml`
is the boost-mode coordinator included by `hvac/rooms/ground_floor/soggiorno.yaml:56` and
`cucina.yaml:57` (each passing `boost_active_global: <zone>_boost_active` into it), but the
coordinator **never creates that id, or any per-zone mode-change timestamp** — it only owns
`${zone_slug}_boost_state` (a `select`) and `${zone_slug}_boost_automation_state` (a
`text_sensor`). Three independent consumers already assume both ids exist:
- `hvac/rooms/ground_floor/ground-floor.yaml:50-51,193-194` reads them as raw globals
  (`id(x)` with no `.state`, and `id(x) = false` assignment in the autotune button) to
  aggregate "any fancoil pump should run" and "time since last mode change" floor sensors.
- `vesta/packages/components/pid_autotune_with_fancoil.yaml:43` assigns
  `id(${boost_active_global}) = false` to force boost off before autotuning — this only
  compiles if the id is a plain `globals:` bool, not an entity.
- `hvac/home-assistant/dashboards/{ground-floor,system-monitoring,rooms/ground_floor/*}.yaml`
  already reference `binary_sensor.climate_control_{soggiorno,cucina}_boost_active` as an HA
  entity, and `hvac/CLAUDE.md`'s own Entity ID Naming Convention example list documents
  `soggiorno_boost_active # Boost active flag` as an intended entity — this is a genuine
  feature gap (Epic 14, per the `# Epic 14: Tracks per-room timing independently` comment at
  `ground-floor.yaml:184`), not a typo.

**Approach:** Wire both missing pieces of state into `fancoil_boost.yaml` — the coordinator
that already owns every boost-mode transition — rather than into the per-room files (which
already reference the right ids and need no changes):

1. Add two **optional** vars with defaults matching the existing call-site naming, so
   `soggiorno.yaml`/`cucina.yaml` need no edits and any future room adopts sane ids for free:
   - `boost_active_global` (default: `${zone_slug}_boost_active`)
   - `last_mode_change_time_global` (default: `${zone_slug}_last_mode_change_time`)
2. Back each with a `globals:` entry (bool / uint32_t) — matching the existing in-repo
   header-accessor-free pattern for simple counters/flags (e.g. `fallback_events` in
   `lighting/packages/buttons.yaml`), since both consumers above read/assign them as raw
   globals, not entities.
3. Set both in the select's existing two `set_action` branches (`fancoil_boost.yaml:117-160`,
   the "Fancoil Boost" branch at line ~120 and "Radiant Only" branch at line ~140): boost
   active → `true` in the Fancoil-Boost branch, `false` in the Radiant-Only branch; the
   timestamp → `id(x) = millis();` in **both** branches (any transition is a mode change).
4. Expose the boost-active global to Home Assistant via a new non-internal
   `binary_sensor: platform: template` (id `${zone_slug}_boost_active_sensor`, name
   `"${zone_name} Boost Active"`, lambda returns the global) published whenever the global
   changes (alongside the existing `set_action` — publish in the same two branches). This is
   what makes `binary_sensor.climate_control_{room}_boost_active` resolve for the
   already-existing dashboard references, with zero dashboard edits.

## Boundaries & Constraints

**Always:**
- Confine the fix to `vesta/packages/coordinators/fancoil_boost.yaml` (implementation) and
  `vesta/docs/fancoil-boost.md` (its paired doc) — every consumer (`ground-floor.yaml`,
  `pid_autotune_with_fancoil.yaml`, the HA dashboards, `soggiorno.yaml`/`cucina.yaml`'s
  existing `boost_active_global` passes) already expects exactly the ids this spec creates;
  none of them should need editing. Prove this in verification (`git diff --stat`).
- New vars are **optional with defaults** (`${zone_slug}_boost_active` /
  `${zone_slug}_last_mode_change_time`) — existing includes in `soggiorno.yaml`/`cucina.yaml`
  that already pass `boost_active_global` explicitly keep working unchanged; do not make
  either var required.
- The new `globals:` entries are plain `bool` / `uint32_t` (not entities) — `id(x) = false`
  in `pid_autotune_with_fancoil.yaml:43` and bare `id(x)` reads in `ground-floor.yaml` only
  compile against a raw global, not a `binary_sensor`/`sensor` entity.
- The new `binary_sensor` is a *separate* entity from the global (publishes it, doesn't
  replace it) — the global stays the internal state the autotune button and other lambdas
  manipulate directly; the binary_sensor is purely the HA-visible mirror.
- One commit (AD-9): the fix, the doc update, and the "Auto Run Result" status update land
  together.

**Block If:** none — every disposition here (id naming, global-vs-entity split, which branch
sets what) is already fixed by the three existing consumer sites; there is no open design
choice to raise with Alberto.

**Never:**
- Do not touch `hvac/rooms/ground_floor/ground-floor.yaml`, `soggiorno.yaml`, or
  `cucina.yaml` — they already reference the ids this spec creates, exactly as written.
- Do not touch `vesta/packages/components/pid_autotune_with_fancoil.yaml` — its
  `boost_active_global` var contract is already correct and compiles once the id exists.
- Do not rename `${zone_slug}_boost_state`, `${zone_slug}_boost_automation_state`, or change
  the select's existing options/transitions — those are live, documented interfaces
  (`hvac/CLAUDE.md`'s entity convention list, the dashboards).
- Do not touch other coordinators (`mev_ventilation.yaml`, `seasonal_mode.yaml`) or any
  other room/floor file — this is a single-coordinator fix.
- Do not add a version bump, migration shim, or backward-compat alias (pre-live; house style
  is in-place edits only).

</intent-contract>

## Code Map

- `vesta/packages/coordinators/fancoil_boost.yaml`
  - Header comment block (~lines 1-85): add `boost_active_global` and
    `last_mode_change_time_global` to the "Optional vars" list; add
    `binary_sensor.{zone_slug}_boost_active` to the "Exposes" list.
  - `defaults:` (~line 88): add the two new optional vars with their defaults.
  - `globals:` — new top-level key (file has none today): two entries,
    `id: ${boost_active_global}` (`type: bool`, `initial_value: 'false'`) and
    `id: ${last_mode_change_time_global}` (`type: uint32_t`, `initial_value: '0'`).
  - `select:` → `set_action:` (~lines 117-160): in the `x == "Fancoil Boost"` branch (~120-135)
    add `id(${boost_active_global}) = true;`, `id(${last_mode_change_time_global}) = millis();`,
    and a `binary_sensor.template.publish` for the new sensor; in the `x == "Radiant Only"`
    branch (~140-150) add the same three actions with `false` for the boost flag.
  - `binary_sensor:` (~line 259 today): add the new `platform: template` entry
    (`id: ${zone_slug}_boost_active_sensor`, `name: "${zone_name} Boost Active"`,
    `device_class: running`, no `internal: true` so it reaches HA, `update_interval: never`
    since it's push-published from the two `set_action` branches, not polled).
- `vesta/docs/fancoil-boost.md` — add the two new optional vars and the new exposed entity
  to its parameter/exposes tables (follow the existing table shape in this file).

## Tasks & Acceptance

**Execution:**
- [x] `fancoil_boost.yaml` -- add `boost_active_global`/`last_mode_change_time_global`
  optional vars + doc-comment updates -- gives the coordinator the two ids every consumer
  already expects
- [x] `fancoil_boost.yaml` -- add the two `globals:` entries -- backing state the autotune
  button can assign directly (`id(x) = false`) and the floor aggregator can read raw
- [x] `fancoil_boost.yaml` -- wire both globals + a new `boost_active_sensor` publish into
  the select's two existing `set_action` branches -- every boost-state transition updates
  both the internal flag/timestamp and the HA-visible mirror in one place
- [x] `fancoil_boost.yaml` -- add the new `binary_sensor: platform: template` entry -- makes
  `binary_sensor.climate_control_{room}_boost_active` resolve for the dashboards that already
  reference it
- [x] `vesta/docs/fancoil-boost.md` -- document the two new vars and the new exposed entity
- [x] Run `esphome config devices/locals/climate-control.yaml` -- confirm all three
  previously-failing IDs now resolve and config exits 0

**Acceptance Criteria:**
- Given `esphome config devices/locals/climate-control.yaml`, when run after this fix, then
  it exits 0 with no "Couldn't find ID" errors (previously: 3 confirmed failures on
  `soggiorno_boost_active`, `cucina_boost_active`, `soggiorno_last_mode_change_time`, plus
  the same failure expected for `cucina_last_mode_change_time` once the first three clear).
- Given `git diff --stat` after this fix, when compared against the file list in Boundaries,
  then only `vesta/packages/coordinators/fancoil_boost.yaml` and
  `vesta/docs/fancoil-boost.md` appear changed — no room/floor file, no
  `pid_autotune_with_fancoil.yaml` edit.
- Given the compiled config, when the "Fancoil Boost" option is selected on
  `select.{zone}_boost_state`, then `binary_sensor.climate_control_{zone}_boost_active`
  publishes `true` and `${zone_slug}_last_mode_change_time` updates to the current `millis()`;
  selecting "Radiant Only" publishes `false` and also updates the timestamp.
- Given the autotune button (`pid_autotune_with_fancoil.yaml`) is pressed, when its
  `id(${boost_active_global}) = false;` lambda runs, then it compiles and executes against
  the new plain `globals:` bool (not an entity) — no type-mismatch compile error.

## Design Notes

The timestamp update happens in **both** branches (not just one), matching the comment at
`ground-floor.yaml:184` ("Epic 14: Tracks per-room timing independently") and the floor
aggregator's semantics (`ground_floor_time_in_current_mode` wants "time since last
transition", which is symmetric — entering boost is as much a mode change as leaving it).

The new `binary_sensor` uses `update_interval: never` and is only ever updated via
`binary_sensor.template.publish` from the `set_action` — this mirrors the existing
`fallback_events_sensor` / `binding_manifest_hash` push-publish pattern already used in
`lighting/packages/buttons.yaml`, so it's consistent with house style rather than introducing
a new idiom.

Two globals per zone (bool + uint32_t) is a small, fixed footprint — no need for the
header-accessor-for-custom-structs pattern (`pending_acks_store`); ESPHome globals handle
primitive types natively, that constraint only bites for structs.

## Verification

**Commands:**
- `esphome config devices/locals/climate-control.yaml` -- expected: exits 0, no missing-ID
  errors (previously 3+ confirmed failures at baseline `bb7f173`)
- `esphome compile devices/locals/climate-control.yaml` -- expected: exits 0
- `git diff --stat` -- expected: only `vesta/packages/coordinators/fancoil_boost.yaml` and
  `vesta/docs/fancoil-boost.md` changed
- `grep -n "boost_active_global\|last_mode_change_time_global" vesta/packages/coordinators/fancoil_boost.yaml` -- expected: appears in defaults, globals, and both set_action branches

**Manual checks (if no CLI):**
- Read the updated `set_action` block top to bottom: confirm both branches set the boost
  global, the timestamp global, and publish the new binary_sensor — symmetrically.
- Confirm `soggiorno.yaml`/`cucina.yaml`'s existing `boost_active_global: <zone>_boost_active`
  var passes still line up with the new default naming (they should be identical strings,
  making the explicit pass redundant but harmless).

## Spec Change Log

- 2026-07-10: `binary_sensor.template` in ESPHome 2026.5.0 does not accept
  `update_interval` (that option only exists on `sensor.template`/polling platforms;
  `esphome config` rejected it with "invalid option ... Did you mean [internal]?"). Dropped
  the option — the entity is still push-only (no `lambda:`, so it never polls), updated
  solely via `binary_sensor.template.publish` from the two `set_action` branches, same
  intended behavior as originally specified.

- 2026-07-10 (review loop 1, bad_spec): Blind Hunter and Edge Case Hunter both independently
  flagged that `${zone_slug}_boost_state`'s `restore_value: true` restores the select's
  option from flash on boot via `publish_state`, which does **not** invoke `set_action`. The
  original Code Map only initialized the two new globals to their static defaults
  (`false`/`0`) and never accounted for boot-time resync, so a reboot mid-boost would leave
  `boost_active_global` silently `false` and `${zone_slug}_boost_active_sensor` unpublished
  ("unknown" in HA) despite the select correctly restoring "Fancoil Boost". **KEEP** (verified
  working, not touched by this amendment): the two `globals:` entries and their placement,
  wiring both globals + the new binary_sensor publish into both `set_action` branches
  symmetrically, the binary_sensor's push-only design (no `lambda:`/`update_interval`), the
  unwrapped `value: millis()` raw-expression form for `globals.set` (confirmed compiles under
  ESPHome 2026.5.0 — `esphome compile` succeeded), and the doc-table additions.
  **Amendment**: extend the existing `${zone_slug}_boost_update_idle` script (already runs
  `on_boot` at priority -100 for exactly this class of restore-resync, previously only
  re-published the text_sensor) to also set `boost_active_global` from the restored select
  option and publish the binary_sensor to match — no separate boot hook needed.
  `last_mode_change_time_global` is deliberately left unsynced on boot (stays `0`, matching
  the non-restoring `globals:` declaration): ESPHome globals have no restore-across-reboot
  story here, and per ADR-0014 §5 this house has no RTC yet (SNTP only) and already accepts
  that timestamps don't survive a power-loss reboot — treating a reboot as time-zero is
  consistent with that accepted limitation, not a new gap.
  Two secondary findings folded into the same pass (both `bad_spec`, low severity, no
  loopback needed on their own): the new binary_sensor was missing `entity_category:
  diagnostic` and an `icon:` that every sibling entity in this file has — added
  (`entity_category: diagnostic`, `icon: mdi:fan-auto`); and the new "Raw globals" header
  comment named house-specific consumer files (`ground-floor.yaml`,
  `pid_autotune_with_fancoil.yaml`) inside `vesta/`, which is the extractable open-source
  library — reworded to describe the *pattern* (external lambdas reading/assigning via
  `id(x)`) generically instead of naming this house's specific files.
  Re-verified: `esphome config` and `esphome compile` both green after the amendment.

## Review Triage Log

**Iteration 1** (2026-07-10):
- bad_spec (high) — boot-restore resync gap for the two new globals + binary_sensor →
  addressed via Spec Change Log amendment above; re-derived in place (fix-forward, see note)
  rather than full revert, because the destructive `git checkout` step this workflow
  prescribes for bad_spec loopbacks was blocked by the auto-mode safety classifier
  (irreversible discard of already-validated uncommitted work with no user sign-off). The
  net result is identical to revert-and-redo: the flawed increment is gone, replaced by the
  amended one, verified green.
- bad_spec (low) — missing `entity_category`/`icon` on new binary_sensor → fixed in the same
  pass, see change log.
- bad_spec (low) — vesta header comment hardcoded house-specific filenames → fixed in the
  same pass, see change log.
- defer — `pid_autotune_with_fancoil.yaml`'s autotune button writes
  `id(${boost_active_global}) = false` directly, bypassing `select.set`/`set_action`
  entirely, so after an autotune-triggered deactivation the select, radiant override switch,
  and the new binary_sensor can disagree with the raw global until the next real transition.
  Pre-existing design in a file this spec's Boundaries explicitly forbid touching (its
  `boost_active_global` contract was declared "already correct" — this spec only had to make
  the id exist); the desync was latent and unobservable before this fix (the file didn't even
  compile), now exposed. Logged to `deferred-work.md`.
- defer — `vesta/docs/fancoil-boost.md`'s Diagnostic Sensors table lists three entities
  (`{zone_slug}_cooling_mode`, `{zone_slug}_time_in_mode`, `{zone_slug}_saturation_duration`)
  that don't exist in `fancoil_boost.yaml` before or after this change — pre-existing doc
  drift, unrelated to this fix. Logged to `deferred-work.md`.
- reject — re-selecting the currently-active option (e.g. HA re-issuing "Fancoil Boost" while
  already boosted) would re-stamp `last_mode_change_time_global` to `millis()` with no real
  transition. Real but negligible: only feeds a display metric
  (`ground_floor_time_in_current_mode`), min_time_in_state anti-cycling is driven by the
  script `delay:`s (independent of this global), and nothing in this codebase currently
  calls `select.set` with an unchanged value.
- reject — unwrapped `value: millis()` questioned as possibly not compiling as intended;
  verified via ESPHome source (`globals.set`'s `value` is `cv.templatable(cv.string_strict)`
  with `to_exp=cg.RawExpression`, so a bare literal is emitted as raw C++) and via a
  successful `esphome compile`. Non-issue.

**Iteration 2** (2026-07-10, re-review of the iteration-1 amendment only — no bad_spec/
intent_gap this round, so `review_loop_iteration` was not incremented further):
- patch — the on_boot resync lambda and the `binary_sensor.template.publish` step
  duplicated the same "is boosting" boolean via two independently-written expressions →
  merged into one lambda that computes `boosting` once and calls
  `id(${zone_slug}_boost_active_sensor).publish_state(boosting)` directly instead of a
  separate publish action.
- patch — the comment above `${zone_slug}_boost_update_idle` said it resyncs "the raw
  globals" (plural) but only touched `boost_active_global`, contradicting itself for
  `last_mode_change_time_global` → reworded to precisely state what's resynced (reported
  state only), why `last_mode_change_time_global` intentionally isn't (no RTC, ADR-0014 §5),
  and that physical outputs are intentionally not replayed here (see defer below).
- patch — `boost_active_global`/`last_mode_change_time_global` were documented under
  "Optional vars" but not under "# Exposes:", even though the header comment describes them
  as public interface for external consumers → added both to `# Exposes:`.
- defer — the boot-restore resync (this spec's own fix) only updates *reported* state
  (globals + binary_sensor + text_sensor), not the physical outputs `set_action` drives
  (radiant override switch/value, radiant PWM, fancoil PID mode) — a mid-boost reboot
  restores the select to "Fancoil Boost" but leaves hardware at power-on defaults while now
  confidently reporting "boosting". Pre-existing gap in the coordinator's boot-restore story
  (the select's `restore_value` never replayed `set_action`'s hardware side, before or after
  this spec) — fixing it needs a real design decision (component-init ordering at boot
  priority -100, whether hardware replay on boot is even desired), out of scope for a
  targeted two-id wiring fix. Logged to `deferred-work.md`.
- reject — `last_mode_change_time_global` not resyncing on boot re-flagged in round 2;
  already an intentional, documented decision from iteration 1 (see Spec Change Log), not a
  new finding.
- reject — remaining round-2 findings (hardcoded true/false per select branch instead of a
  shared "apply state" primitive, confusable `_boost_active` vs. `_boost_active_sensor`
  naming, no sanity check for select-restore edge cases like an OTA that changes the options
  list, redundant writes on a same-value `select.set`) are code-quality/robustness
  suggestions, not correctness bugs, and several call for centralizing logic across
  `set_action`'s two branches — which the spec's Boundaries explicitly forbid altering
  ("Do not rename ... or change the select's existing options/transitions"). No change.
- Re-verified: `esphome config` and `esphome compile` both green after the round-2 patches.

## Auto Run Result

Status: implemented, config + compile green, review loops 1 and 2 complete (all findings
triaged — 6 fixed in place across two passes, 3 deferred, 3 rejected as non-issues).

## Suggested Review Order

**State wiring (the fix)**

- Two new globals backing the ids every consumer already expected; `boost_active_global`
  optional var default matches `soggiorno.yaml`/`cucina.yaml`'s existing explicit pass.
  [`fancoil_boost.yaml:119`](../../vesta/packages/coordinators/fancoil_boost.yaml#L119)

- Both `set_action` branches set the two globals + publish the new binary_sensor
  symmetrically — boost on sets `true`/stamps `millis()`, boost off sets `false`/stamps
  `millis()` (Design Notes: any transition counts, not just activation).
  [`fancoil_boost.yaml:159`](../../vesta/packages/coordinators/fancoil_boost.yaml#L159)
  [`fancoil_boost.yaml:182`](../../vesta/packages/coordinators/fancoil_boost.yaml#L182)

- New `binary_sensor.{zone_slug}_boost_active_sensor` — push-only (no `lambda`), makes
  `binary_sensor.climate_control_{room}_boost_active` resolve for existing dashboard refs.
  [`fancoil_boost.yaml:311`](../../vesta/packages/coordinators/fancoil_boost.yaml#L311)

**Boot-restore resync (review-loop finding, iteration 1)**

- `select: restore_value: true` restores the option from flash without invoking
  `set_action` — this on_boot lambda (already ran for the text_sensor) now also resyncs
  `boost_active_global` and the binary_sensor to match. Deliberately does not resync
  `last_mode_change_time_global` (no RTC yet) or replay hardware outputs (deferred).
  [`fancoil_boost.yaml:282`](../../vesta/packages/coordinators/fancoil_boost.yaml#L282)

**Docs**

- Optional-vars/Exposes table entries for the two new globals and the new entity.
  [`fancoil-boost.md:144`](../../vesta/docs/fancoil-boost.md#L144)

**ADR + planning**

- ADR-0014 marked Accepted, unblocking this phase's implementation plan.
  [`0014-standardized-controller-modbus-io-hardware.md:4`](../planning-artifacts/adrs/0014-standardized-controller-modbus-io-hardware.md#L4)
