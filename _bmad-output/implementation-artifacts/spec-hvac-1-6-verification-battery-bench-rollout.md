---
title: 'HVAC-1.6 Verification Battery and Bench Rollout'
type: 'chore'
created: '2026-07-11'
status: 'blocked'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 'ac9049d12554088a240756e0114c84903b9177f2'
context:
  - '{project-root}/hvac/CLAUDE.md'
  - '{project-root}/canbus/CLAUDE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-HVAC-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/HVAC-Epic-1-can-sensor-receiver.md'
warnings: ['oversized']
---

<intent-contract>

## Intent

**Problem:** Epic HVAC-1's release gate (story 1.6) has never run end-to-end: the battery exists but is scattered and partly undocumented (`hvac/CLAUDE.md` has no Test & verify section; `canbus/CLAUDE.md`'s idempotence check omits the generator's `hvac/` outputs; C++ test headers carry stale pre-Phase-6a `firmware/tests/` commands), the committed generated artifacts are mid-flip (`registry/nodes.csv` has node 101 = `sensors=1,soggiorno` since HVAC-1.2 and the two `hvac/` generated artifacts match it, but `registry/map.json`, `canbus/nodes/node101.yaml`, and `canbus/protocol/node_map.h` were never regenerated — so epic AC6 idempotence currently fails and the bench node's firmware config lacks the sensor-kit producer), HVAC-1.4's `vesta` failover e2e residual was never re-run, and no bench procedure exists for the CAN→HA→Emergency proof (epic ACs 7-9 need physical hardware; the system is pre-live).

**Approach:** Reconcile the three stale generated artifacts with one sanctioned `generate_nodes.py` run (completing the already-committed node-101/soggiorno bench flip); run the full verification battery in-repo (generator + native + vesta failover e2e + ESPHome config/compile gates + widened idempotence check) and codify it as one repeatable runner script plus corrected docs; ship a bench-validation checklist covering epic ACs 7-9/10 and the epic completion report recording this run's actual results with bench execution marked pending hardware.

## Boundaries & Constraints

**Always:** Change generated files only by running `python3 canbus/tools/generate_nodes.py`; keep `registry/nodes.csv`, `registry/bindings.yaml`, and `registry/node_id_hwm` byte-identical (the bench flip is already committed; hvac never writes the registry, ADR-0009). The battery must include the epic's exact command set: generator tests (`python3 canbus/tests/test_generate_exports.py`), native receiver tests (`g++ -std=c++17 -Wall -Wextra -Icanbus/protocol -Ihvac/protocol hvac/tests/test_can_sensor_receiver.cpp`), `esphome compile canbus/tests/compile_sensor_node.yaml`, `esphome config devices/locals/climate-control.yaml`, `esphome compile devices/locals/climate-control.yaml`, and regeneration idempotence widened to `python3 canbus/tools/generate_nodes.py && git diff --exit-code canbus hvac registry` — plus the rest of the documented canbus/lighting battery (3 python + 5 canbus C++ + 1 lighting C++ tests), the hvac receiver compile fixture (`esphome config hvac/tests/compile_can_sensor_receiver.yaml`), and `python3 -m pytest vesta/tests/e2e/test_failover_sensor.py` (closes HVAC-1.4's recorded residual). Use `esphome==2026.5.3` (vesta's deliberate pin, ≥ repo floor 2026.5.0) and record the version wherever results are recorded. Runner script is bash, no new dependencies, fail-fast with a per-step PASS/FAIL summary, offers a documented flag to run only the esphome-free subset, and documents that the idempotence step needs clean `canbus`/`hvac`/`registry` paths. Bench checklist and completion report go in `_bmad-output/implementation-artifacts/` with `epic-HVAC-1-` naming; record only actually-executed results.

**Block If:** Rerunning the generator diffs any file beyond `registry/map.json`, `canbus/nodes/node101.yaml`, `canbus/protocol/node_map.h` (unknown drift beyond the documented mid-flip state). Any battery step fails such that the fix requires changing runtime behavior of the receiver, failover, MEV, protocol headers, or `generate_nodes.py` logic (verification story; product-behavior fixes need a decision). ESPHome cannot be installed or cannot run the compile gates in this environment.

**Never:** Do not hand-edit any generated file (`canbus/nodes/**`, `registry/map.json`, `canbus/protocol/node_map.h`, `canbus/protocol/bindings.h`, `canbus/home-assistant/ha_manifest_package.yaml`, `hvac/packages/generated/**`, `hvac/protocol/generated_can_sensor_routes.h`). Do not modify anything under `vesta/` or bump the vesta submodule gitlink (read-only pinned dependency; initialize it for builds only). Do not add registry rows or new CAN nodes. Do not install git hooks or CI (runner script + docs only — hook/CI wiring is a separately-tracked decision in deferred-work). Do not mark `hvac-epic-1` done in sprint-status and do not fabricate bench results — epic ACs 7-9 execute on hardware later, guided by the checklist.

</intent-contract>

## Code Map

- `registry/map.json`, `canbus/nodes/node101.yaml`, `canbus/protocol/node_map.h` -- the three stale generated artifacts; reconciled by one generator run (map.json flips node 101 to `sensors:1`/`soggiorno` + new `map_version`; node101.yaml gains the `sensor_kit.yaml` include; node_map.h restamps `NODE_MAP_VERSION`).
- `canbus/tools/generate_nodes.py` -- read-only; sole sanctioned writer of generated artifacts.
- `scripts/verification-battery.sh` -- new runner codifying the battery (root `scripts/` is currently empty).
- `hvac/CLAUDE.md` -- add a Test & verify section (receiver native test with both `-I` flags, receiver fixture config, climate config/compile, battery script pointer).
- `canbus/CLAUDE.md` -- widen the documented idempotence check from `git diff --exit-code canbus registry` to include `hvac`; point at the runner.
- `canbus/tests/*.cpp` (5 files), `lighting/tests/test_binding_actuation.cpp` -- fix stale `firmware/tests/`-era build-command comments if present (audit each; lighting's may already be correct).
- `hvac/tests/test_can_sensor_receiver.cpp`, `hvac/tests/compile_can_sensor_receiver.yaml`, `canbus/tests/compile_sensor_node.yaml` -- existing battery members, run not rewritten.
- `_bmad-output/implementation-artifacts/epic-HVAC-1-testing-checklist.md` -- new bench-validation checklist (epic ACs 7-9 procedures + AC10 findings section).
- `_bmad-output/implementation-artifacts/epic-HVAC-1-completion-report.md` -- new completion report (per-story delivered files, this run's command results, bench pending).
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- mark story done; epic stays in-progress with a comment.

## Tasks & Acceptance

**Execution:**
- [x] `registry/map.json` + `canbus/nodes/node101.yaml` + `canbus/protocol/node_map.h` -- run `python3 canbus/tools/generate_nodes.py`; verify the diff is exactly these three files (nodes.csv untouched, hvac artifacts byte-identical) -- completes the bench flip so node 101 produces CAT_SENSOR and AC6 idempotence can hold. *(Done: commit dcc8db3; AC6 idempotence now passes.)*
- [x] `scripts/verification-battery.sh` -- create the fail-fast runner with the full step list from Always, per-step PASS/FAIL summary, and the esphome-free subset flag -- makes the battery repeatable (the story's core promise). *(Done: commit ac2c4ad; `--native-only` run green.)*
- [x] `canbus/tests/*.cpp`, `lighting/tests/test_binding_actuation.cpp` -- audit and correct stale build-command header comments to the current documented commands -- stops the battery's own docs from misleading. *(Done: 5 canbus headers corrected; lighting's was already correct.)*
- [x] `hvac/CLAUDE.md` -- add Test & verify section -- hvac's test commands currently live only in a fixture header and an old spec.
- [x] `canbus/CLAUDE.md` -- correct the idempotence line to `git diff --exit-code canbus hvac registry` and reference the runner -- the generator has written `hvac/` outputs since HVAC-1.1/1.4.
- [x] `_bmad-output/implementation-artifacts/epic-HVAC-1-testing-checklist.md` -- write bench procedures for epic AC7 (flash-prep: `esphome compile canbus/nodes/node101.yaml`, `python3 canbus/tools/check_registry_pushed.py` gate, flash, observe `soggiorno_*_can` → abstracted `CAN` tier in HA), AC8 (stop frames >90 s → `HA` tier), AC9 (CAN+HA off → `Emergency`/NaN + existing shutdown), each with expected observations, plus an AC10 findings-recording section -- the hardware session's script.
- [x] `_bmad-output/implementation-artifacts/epic-HVAC-1-completion-report.md` -- record delivered files per story (1.1-1.6), each battery command with this run's actual result and esphome version, bench-validation section = pending hardware (pointer to checklist), deferred/tuning list -- epic DoD artifact. *(Done: results table records the environment-permitted subset green and the compile gates as environment-blocked.)*
- [ ] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- mark `hvac-1-6-verification-battery-bench-rollout: done` only after the battery passes; add a comment on `hvac-epic-1` that the manual done-flip awaits the bench session -- keeps tracking honest. *(Battery did NOT fully pass in this environment (compile gates egress-blocked) → story set to `in-progress`, epic comment added; the `done` flip belongs to the local green run.)*

**Acceptance Criteria:**
- Given the reconciled tree, when `python3 canbus/tools/generate_nodes.py` runs again, then `git diff --exit-code canbus hvac registry` exits 0 and `registry/map.json` shows node 101 with `sensors: 1`, `room_slug: "soggiorno"`, unchanged `schema_version`.
- Given reconciled `canbus/nodes/node101.yaml`, when inspected, then it includes `../packages/sensor_kit.yaml`, and `esphome compile canbus/nodes/node101.yaml` succeeds (bench node flash-ready).
- Given a clean tree with `esphome==2026.5.3`, when `scripts/verification-battery.sh` runs, then every step passes with a green summary (epic ACs 1-6 all satisfied by the covered commands).
- Given the existing test files, when coverage is inspected, then generator tests already cover room_slug validation/routing artifact/idempotence (epic AC1) and native receiver tests already cover valid/malformed/wrong-proto/non-sensor/non-OK/unknown-route/90 s-stale (epic AC2) — asserted green, not rewritten.
- Given `python3 -m pytest vesta/tests/e2e/test_failover_sensor.py` with pytest installed, when run, then it passes (HVAC-1.4 residual closed).
- Given the checklist, when read, then each of epic ACs 7-9 maps to a numbered procedure with expected observations, the pre-flash push gate is included, and a findings section satisfies AC10's recording path.
- Given the completion report, when read, then every recorded result corresponds to a command actually executed in this run, and bench execution is explicitly pending.

## Spec Change Log

## Review Triage Log

## Design Notes

The mid-flip state is deliberate history, not corruption: HVAC-1.2 committed the nodes.csv flip, HVAC-1.4 regenerated but committed only the two hvac artifacts (its boundaries barred the rest). Reconciliation is therefore a generator run whose expected diff is known in advance — anything else is drift and blocks. `registry/nodes.csv` itself must not change: the "bench rollout registry flip" of the epic is already in the history, and this story only brings the generated outputs into agreement with it. Epic status stays `in-progress` by design: the epic's DoD requires bench-proven CAN→HA→Emergency transitions, which need the physical node and a live HA — this story delivers the gate, the flash-ready node config, and the session script, not the session itself.

## Verification

**Commands:**
- `bash scripts/verification-battery.sh` -- expected: all steps PASS, exit 0.
- `python3 canbus/tools/generate_nodes.py && git diff --exit-code canbus hvac registry` -- expected: exit 0 (byte-identical regeneration).
- `esphome compile canbus/nodes/node101.yaml` -- expected: compiles (bench node flash-ready; RP2040 toolchain).
- `python3 -m pytest vesta/tests/e2e/test_failover_sensor.py` -- expected: passes under esphome 2026.5.3.
- `git diff --check` -- expected: no whitespace errors.

## Auto Run Result

**Status:** blocked

**Blocking condition:** Spec Block If triggered — ESPHome cannot run the compile gates in this environment. The session's egress policy (Claude Code remote network policy) denies GitHub release-asset downloads and the PlatformIO registry with 403 (the agent proxy's documentation classifies 403 as organization policy: "do not retry or route around it"). Every `esphome compile` requires PlatformIO platform packages from exactly those hosts, so epic AC3 (`esphome compile canbus/tests/compile_sensor_node.yaml` — RP2040 toolchain asset), epic AC5 (`esphome compile devices/locals/climate-control.yaml` — `pioarduino/platform-espressif32` release zip), the node101 bench compile, and the vesta failover e2e (host build needs `platformio/native` from `api.registry.platformio.org`) could not execute. This also leaves the spec AC "every `scripts/verification-battery.sh` step passes" unsatisfiable here (step-03 implementation-verification failure).

**What ran green in this environment (esphome==2026.5.3, Python 3.11, g++ 13):** all 3 canbus python suites (generator suite: 29 tests — epic AC1), all 5 canbus native C++ tests, the lighting native test, the hvac receiver native test (9 cases — epic AC2), the widened regeneration-idempotence gate (epic AC6, passing for the first time thanks to the reconciliation commit), `esphome config hvac/tests/compile_can_sensor_receiver.yaml`, `esphome config devices/locals/climate-control.yaml` ("Configuration is valid!", epic AC4), `esphome config canbus/nodes/node101.yaml`, `bash scripts/verification-battery.sh --native-only` (RESULT: PASS), and `git diff --check`.

**Delivered (3 commits on `claude/hvac-1-6-story-t1qko7`):**
- `dcc8db3` — reconciliation: `registry/map.json` (node 101 → `sensors:1`/`soggiorno`, new `map_version`), `canbus/nodes/node101.yaml` (+`sensor_kit` include — the bench node now produces CAT_SENSOR), `canbus/protocol/node_map.h` (restamp). Exactly the three expected files; `registry/nodes.csv` untouched.
- `ac2c4ad` — `scripts/verification-battery.sh` (fail-fast runner, `--native-only`, idempotence pre-check), stale build-command comments fixed in 5 canbus test headers (lighting's already correct), `hvac/CLAUDE.md` Test & verify section, `canbus/CLAUDE.md` idempotence line widened to `canbus hvac registry` + runner pointer, `epic-HVAC-1-testing-checklist.md` (bench session script: prerequisites, `check_registry_pushed.py` gate, runbook Path A flash prep, AC7/AC8/AC9 numbered proofs with expected observations and exact entity ids, AC10 findings table), `epic-HVAC-1-completion-report.md`.
- Final commit — completion report updated with this run's actual per-command results and the "Environment limits of this run" section, sprint-status (`hvac-1-6…: in-progress` with rationale comments), this spec's task checkboxes and Auto Run Result.

**Not delivered / pending:** sprint-status `done` flip for this story (its own task text forbids it until the battery passes); the three `esphome compile` gates + vesta e2e execution; the bench session (epic ACs 7-10, hardware — by design).

**Unblock path (any network-unrestricted machine, from repo root):** `pip install "esphome==2026.5.3" pytest pytest-asyncio aioesphomeapi`, then `bash scripts/verification-battery.sh` (expected: RESULT: PASS, 16/16) and `esphome compile canbus/nodes/node101.yaml`. On green: flip `hvac-1-6-verification-battery-bench-rollout` to `done`, update completion-report rows 13/15/16/17/18, set this spec's `status` to `done`, then run the bench session per `epic-HVAC-1-testing-checklist.md`. Alternatively, rerun this story in a remote session whose environment network policy permits `github.com` release assets and `*.registry.platformio.org`.

**Environment notes:** `devices/locals/secrets.yaml` (gitignored) was created with clearly-labeled dummy values so the locals config gate could resolve `!secret` references — never flash with it. The vesta submodule was initialized read-only at its pinned commit `a890105` for the gates; no vesta changes, no gitlink bump. Implementation ran partly under a subagent that was terminated by an account spend limit mid-run; all of its work was verified from the tree and logs (battery summary, per-step logs) before being recorded here — every result above corresponds to an actually-executed command.

**Review status:** the step-04 adversarial review pass did not run (HALT during step-03 verification). `followup_review_recommended` stays false only in the sense that no review occurred; treat the diff as unreviewed when resuming.
