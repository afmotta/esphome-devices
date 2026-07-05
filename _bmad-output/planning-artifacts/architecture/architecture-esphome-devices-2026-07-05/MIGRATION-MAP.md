# Migration Map — esphome-devices layered restructure

Companion to `ARCHITECTURE-SPINE.md`. Six phases, each one commit, each ending green per AD-9
(full battery below). Order rationale: the registry moves first because every tool anchors on it
and it is the highest-value seam; the HA split precedes the HVAC gathering so `home-assistant/`
empties naturally; the canbus flatten goes last because it is cosmetic and touches the most paths.

## Standing verification battery (AD-9)

Run at the end of every phase (paths shift in Phases 5–6 as noted):

```bash
# Python registry/tooling tests (stdlib-only)
python3 canbus/firmware/tests/test_bindings.py
python3 canbus/firmware/tests/test_generate_exports.py
python3 canbus/firmware/tests/test_push_gate.py

# Native C++ protocol logic
g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_protocol.cpp -o /tmp/proto && /tmp/proto
g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_ha_arbitration.cpp -o /tmp/arb && /tmp/arb
g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_node_health.cpp -o /tmp/health && /tmp/health
g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_bridge_forwarding.cpp -o /tmp/bridge && /tmp/bridge

# ESPHome configs still valid
esphome config locals/climate-control.yaml
esphome compile canbus/firmware/tests/compile_sensor_node.yaml

# Generator idempotence (AD-8) + push gate
python3 canbus/firmware/tools/generate_nodes.py && git diff --exit-code
python3 canbus/firmware/tools/check_registry_pushed.py
```

---

## Phase 0 — Baseline (no changes)

Clean working tree; run the full battery and record it green; confirm push gate green.
This is the reference point every later phase is compared against.

## Phase 1 — Registry elevation *(AD-3)* — size M

- `git mv canbus/firmware/registry registry`
- Update the registry-relative path anchor in every tool (`generate_nodes.py`, `bindings.py`,
  `allocate_node.py`, `commission.py`, `check_registry_pushed.py`) and every Python test — all
  anchor on `Path(__file__)`, so this is one constant per file.
- Add `registry/README.md`: the AD-3 ownership table (nodes.csv+node_id_hwm → canbus;
  bindings.yaml → lighting; map.json → generated, contract owned by hvac; mechanism → canbus).
- Update doc references: `canbus/CLAUDE.md`, root `CLAUDE.md`, protocol reference,
  `live-freeze-checklist.md`, `reflash-campaign-runbook.md`, `spec-map-json-contract`.
- **Verify:** byte-identical regeneration, python tests, live push-gate run.

## Phase 2 — Lighting is born *(AD-1, AD-5)* — size S

- Create `lighting/`; `git mv home-assistant/canbus/ha_hold_automations.yaml lighting/home-assistant/`
- Write `lighting/CLAUDE.md`: owns `registry/bindings.yaml` schema + fallback semantics
  (ADR-0013 lineage), never touches canonicalization/hash (AD-7), epic prefix **LIGHT-**.
- Manual HA step: re-point the package include for hold automations to the new path.
- **Verify:** battery; HA reloads the moved package.

## Phase 3 — HA split completes *(AD-5)* — size S

- `git mv` arbitration automations + generated `ha_manifest_package.yaml` → `canbus/home-assistant/`;
  dashboards → `hvac/home-assistant/dashboards/` (creates `hvac/`).
- Teach `generate_nodes.py` the new manifest output path; regenerate.
- Delete the now-empty top-level `home-assistant/`; port its README content to the system folders.
- Manual HA step: re-point remaining package includes.
- **Verify:** battery; regeneration writes to the new path and is idempotent.

## Phase 4 — HVAC gathering *(AD-1, AD-9)* — size M

- `git mv components/rooms hvac/rooms`; `git mv components/*.yaml hvac/` (mev_modbus, mev_demand,
  room_sensors); remove empty `components/`.
- Update every `!include` path in `devices/climate-control.yaml`, room/floor aggregators, and any
  vesta example that cites `components/`.
- Update the generator's `room_slug` validation glob (`components/rooms/**` → `hvac/rooms/**`) and
  the same path in `spec-map-json-contract` + its test — this is an AD-6 contract edit: spec, code,
  and test move in this one commit.
- `remotes/*.yaml` cite `devices/climate-control.yaml@main` — path unchanged, but the fetched
  package's internal includes must resolve, so this phase is strictly one commit (AD-9).
- Write `hvac/CLAUDE.md` (entity-ID convention, epic prefix **HVAC-**).
- **Verify:** battery + `esphome config locals/climate-control.yaml` and a full
  `esphome compile locals/climate-control.yaml`.

## Phase 5 — Composition layer *(AD-4, AD-6, AD-7)* — size L

- `git mv canbus/firmware/gateway/gateway.yaml devices/gateway.yaml` (+ `secrets.yaml`,
  `secrets.yaml.example`; update `.gitignore` paths). Fix its includes of `protocol/*.h`.
- `git mv canbus/firmware/bridge/bridge.yaml devices/bridge.yaml`; same include fixes.
- Code slice (can trail as its own commits, same phase): extract the gateway monolith into
  `canbus/packages/` (CAN decode, health, arbitration/`ha_ready`, HA event firing) and
  `lighting/packages/` (fallback actuation — lands with ADR-0013 open item 2, when relay outputs
  become real). The seam follows AD-7: hash/gate → canbus package; binding meaning → lighting.
- Write the bindings → arbitration contract spec + drift test (AD-6): the compiled
  `BindingEntry`/`bindings.h` surface.
- **Verify:** battery + `esphome compile` of gateway and bridge from `devices/`.

## Phase 6 — Flatten canbus + context rewrite *(AD-1, AD-10)* — size M

- `git mv canbus/firmware/{protocol,packages,nodes,tools,tests} canbus/` — the `firmware/`
  level is empty ceremony once registry/gateway/bridge are out. Update the generator's output
  path and template, test commands, `compile_sensor_node.yaml` includes, all docs.
- Rewrite root `CLAUDE.md` as the map (four systems + registry + devices + boards); trim
  `canbus/CLAUDE.md` to infra-only; per-system CLAUDE.mds final.
- Update Claude Code memory files that cite old paths.
- **Verify:** full battery at final paths; byte-identical regeneration; live push-gate run.

---

## Risk register

| Risk | Mitigation |
| --- | --- |
| HA imports break at Phases 2–3 | Both phases carry an explicit manual HA re-point step; verify HA reload before closing the phase |
| Production remotes fetch a half-moved tree | AD-9: move + consumers in one commit; both subsystems pre-live, blast radius is a failed compile, not a live outage |
| Stale-path worktrees / `__pycache__` | Clean `.claude/worktrees/` copies and `tools/__pycache__` after Phase 6; they are derived state |
| Doc/runbook path rot | Phases 1 and 6 each include a repo-wide grep for the old path (`firmware/registry`, `canbus/firmware`) as an exit criterion |
| Gateway extraction (Phase 5) changes behavior, not just location | The pure moves commit first and land test-green before any package extraction begins |
