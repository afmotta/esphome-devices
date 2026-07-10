---
title: 'HVAC baseline config green — wire boost_active/last_mode_change_time in fancoil_boost.yaml'
type: 'bug'
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
- [ ] `fancoil_boost.yaml` -- add `boost_active_global`/`last_mode_change_time_global`
  optional vars + doc-comment updates -- gives the coordinator the two ids every consumer
  already expects
- [ ] `fancoil_boost.yaml` -- add the two `globals:` entries -- backing state the autotune
  button can assign directly (`id(x) = false`) and the floor aggregator can read raw
- [ ] `fancoil_boost.yaml` -- wire both globals + a new `boost_active_sensor` publish into
  the select's two existing `set_action` branches -- every boost-state transition updates
  both the internal flag/timestamp and the HA-visible mirror in one place
- [ ] `fancoil_boost.yaml` -- add the new `binary_sensor: platform: template` entry -- makes
  `binary_sensor.climate_control_{room}_boost_active` resolve for the dashboards that already
  reference it
- [ ] `vesta/docs/fancoil-boost.md` -- document the two new vars and the new exposed entity
- [ ] Run `esphome config devices/locals/climate-control.yaml` -- confirm all three
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

## Review Triage Log

## Auto Run Result

Status: ready-for-dev — not yet executed.
