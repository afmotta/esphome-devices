---
title: 'Migration Phase 5b-2 — Gateway package extraction'
type: 'refactor'
created: '2026-07-07'
status: 'done'
review_loop_iteration: 0
baseline_commit: '0e7e97594cc442a39671fb3d06017465a83cb4e3'
context: ['{project-root}/_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md', '{project-root}/_bmad-output/specs/spec-bindings-arbitration-contract/SPEC.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `devices/gateway.yaml` is a 409-line monolith mixing two systems' behavior (AD-7 as amended 2026-07-06): canbus-owned transport health (heartbeat decode, aliveness sweep, discovery) and lighting-owned button handling (CAT_INPUT decode → HA events, the `ha_ready` gate instance). The physical device split is deferred to ADR-0013's hardware decision, but the *package seam* must exist first — and it's identical under any topology.

**Approach:** Extract by ownership into `canbus/packages/health.yaml` and `lighting/packages/buttons.yaml`; `devices/gateway.yaml` becomes a thin composer (identity, board, network, api encryption/OTA, header includes, substitution overrides, package composition). Behavior-neutral by construction and by proof: the ESPHome-validated config dump before and after must be semantically identical.

## Boundaries & Constraints

**Always:**
- Zero behavior change. The proof is `esphome config devices/gateway.yaml` captured at baseline and after extraction: any diff must be ordering/cosmetic only, itemized in this spec on completion. Plus a full `esphome compile` SUCCESS.
- Device identity untouched: `esphome: name: canbus-gateway`, friendly name, api encryption, OTA password stay in the entry point exactly as-is (renaming the device forces HA re-adoption — out of scope).
- Package composition order is canbus before lighting (lighting's `!extend can0` must see the bus canbus's package defines) — the entry point must state this constraint in a comment.
- Seam per AD-7 amendment: health.yaml gets the CAT_STATUS `on_frame` handler, the 5s aliveness sweep, health globals (`health_edges`, `lost_node_idx`), health entities (`nodes_online/total/missing`, `node_map_version`), the node_lost/recovered/error/unknown HA events, and the `node_lost_timeout_ms` substitution default. buttons.yaml gets the CAT_INPUT handler, `homeassistant.event: esphome.canbus_button`, both api services + `on_client_disconnected`, arbitration globals (`last_ha_hb_ms`, `ha_hb_seen`, `ha_hash_ok`, `ha_hash_evaluated`, `next_event_id`, `fallback_events`), the 250ms ACK sweep, `ha_ready_sensor`, `binding_manifest_hash`, and the `ha_heartbeat_ttl_ms`/`ack_timeout_ms` substitution defaults.
- ESPHome merge mechanics are verified empirically, not assumed: if a block doesn't merge cleanly from a package (`esphome: on_boot:` is the known suspect; `api:` deep-merge the second), fall back to keeping that specific block in the entry point with a comment naming which system owns it — and record the fallback in this spec.
- Header `includes:` stay in the entry point (include paths resolve relative to the main config; keeping them there keeps packages location-independent).
- Full battery + `esphome compile devices/gateway.yaml` + `esphome compile devices/bridge.yaml` green.

**Ask First:**
- If the `!extend can0` direction fails outright (lighting package cannot extend the canbus package's bus), HALT and present alternatives rather than improvising a hybrid — the seam choice was architectural, its mechanical realization shouldn't silently mutate it.

**Never:**
- No relay outputs, no actuation, no `fallback_events` semantic changes — ADR-0013's slice, not this one.
- Do not touch protocol headers, the generator, the registry, `bridge.yaml`, or node packages (`canbus/firmware/packages/*` stays untouched; the new top-level `canbus/packages/` is gateway-side only until Phase 6 merges them).
- Do not modify the frozen bindings contract or its drift test.

</frozen-after-approval>

## Code Map

- `devices/gateway.yaml` -- shrinks to composer: substitutions (overrides), esphome identity + includes, esp32, logger, wifi, api encryption/OTA, `packages:` block. The `canbus:` bus definition MOVES OUT (see health.yaml) with `tx_pin`/`rx_pin`/`bit_rate` parameterized; entry point supplies pin substitutions
- `canbus/packages/health.yaml` -- new: the bus definition (`id: can0`, pins/bitrate from substitutions with defaults) + CAT_STATUS handler + aliveness sweep + health globals/entities/events + `node_lost_timeout_ms` default. Bus lives here so lighting's `!extend` direction works (packages merge in order; main-config-defined ids may not be extendable from packages)
- `lighting/packages/buttons.yaml` -- new: `canbus: - id: !extend can0` adding the CAT_INPUT handler; api services + on_client_disconnected; arbitration globals, ACK sweep, ha_ready sensor, manifest-hash diagnostic; `ha_heartbeat_ttl_ms`/`ack_timeout_ms` defaults
- `lighting/CLAUDE.md` -- "Files here today" section gains `packages/buttons.yaml`
- `canbus/CLAUDE.md` + `canbus/firmware/README.md` -- note the gateway-side package home (`canbus/packages/`, distinct from node-side `canbus/firmware/packages/` until Phase 6)
- on_boot publishes: `binding_manifest_hash` → buttons.yaml; `node_map_version` + `nodes_total` → health.yaml (the known merge-mechanics suspect; fallback per Always)

## Tasks & Acceptance

**Execution:**
- [x] Captured baseline config dump (scratchpad, not committed)
- [x] Authored `canbus/packages/health.yaml` (bus + health seam per Code Map)
- [x] Authored `lighting/packages/buttons.yaml` (buttons + gate instance per Code Map). One human-approved semantic exception (see Spec Change Log): the `fallback_events_sensor` 5s re-publish moved out of the health sweep into a lighting-owned 5s interval, removing the monolith's baked-in canbus→lighting reference (AD-2).
- [x] Rewrote `devices/gateway.yaml` as composer; package-order constraint documented in-file
- [x] Verified config-dump equivalence via a YAML-level semantic comparator (itemization below)
- [x] `esphome compile devices/gateway.yaml` SUCCESS; `devices/bridge.yaml` SUCCESS with a byte-identical config hash to Phase 5a (0xecd286a0) proving it untouched
- [x] Updated `lighting/CLAUDE.md` (also refreshed its stale pre-amendment AD-7 wording), `canbus/CLAUDE.md`, `canbus/firmware/README.md`
- [x] Full standing battery green, byte-identical regeneration included

**Config-dump semantic diff, itemized (baseline vs extracted):**
- IDENTICAL: `api` (all services, encryption, on_client_disconnected merged perfectly), `binary_sensor`, `esp32`, `logger`, `ota`, `sensor`, `wifi`; `canbus` bus config identical with pins resolving to the same values through the new substitutions
- REORDERED ONLY: `globals` (8/8), `text_sensor` (3/3), `canbus.on_frame` (2/2 — STATUS now before INPUT; handlers match disjoint category masks, order semantically irrelevant)
- INTENTIONAL (3): (1) two new substitutions `can_tx_pin`/`can_rx_pin` parameterizing previously hardcoded pins, same values; (2) `on_boot` split from one automation with 3 publishes into two automations totaling the same 3 publishes at the same priority 600 (independent publishes, order irrelevant); (3) the approved `fallback_events_sensor` publish relocation — health's 5s sweep lost one line, a new lighting 5s interval carries it, same cadence and value

**Acceptance Criteria:**
- Given the extracted packages, when `esphome config devices/gateway.yaml` is diffed against the pre-extraction baseline, then differences are ordering/cosmetic only (itemized), with every substitution value, global, entity, service, automation, and on_frame handler semantically present and unchanged.
- Given `esphome compile devices/gateway.yaml`, when run, then SUCCESS.
- Given the standing battery, when run, then all green, byte-identical regeneration included.
- Given the composed config, when packages are listed in the entry point, then canbus/health precedes lighting/buttons and a comment states why.

## Spec Change Log

- **2026-07-07, pre-implementation renegotiation (human-approved):** a full cross-seam scan found exactly one coupling conflicting with the frozen "cosmetic-only diff" rule — the health sweep published lighting's `fallback_events_sensor` (`gateway.yaml:260` in the monolith), a canbus→lighting reference AD-2 forbids. Alberto chose moving the publish into a lighting-owned 5s interval (same cadence/value/reconnect behavior) over preserving a byte-identical dump with the violation carried forward. The frozen Always stands for everything else; this one itemized, behavior-equivalent exception is authorized.

## Design Notes

The bus definition living in `canbus/packages/health.yaml` (parameterized pins) rather than the entry point is the one deviation from "hardware stays in the entry point" — chosen because ESPHome's `!extend` reliably extends ids defined in *earlier-merged* packages, while extending a *main-config* id from a package is the shakier direction. The entry point still owns the actual pin values via substitutions. If ADR-0013's split later gives lighting its own device, its entry point composes buttons.yaml plus a bus-bearing package (or health.yaml moves — decided then).

## Verification

**Commands:**
- `esphome config devices/gateway.yaml` -- baseline before, semantic-equal after
- `esphome compile devices/gateway.yaml` -- expected: SUCCESS
- `esphome compile devices/bridge.yaml` -- expected: SUCCESS (untouched, regression check)
- Full standing battery (python, native C++ incl. `test_bindings_contract`, sensor-node compile, regeneration idempotence, push gate) -- expected: green

**Note (review):** both review subagents failed immediately on a monthly spend limit, so the review ran inline against the verification points their prompts specified (same fallback as Phase 5b-1, user-acknowledged). Executed checks beyond the pre-existing dump comparison: (1) package-order reversal test — a scratch entry point with the packages swapped still produced one `can0` with both handlers, proving ESPHome 2026.5.0 resolves `!extend` order-tolerantly; the three files' "order MATTERS" comments were softened to convention-with-rationale accordingly. (2) Substitution-precedence test — changing an entry-point value produced a dump where the package default appeared zero times, proving main-config override. (3) Globals split verified disjoint (2 health + 6 buttons = the original 8; entity duplication already excluded by dump equivalence). (4) Docs-claims greps match file contents. (5) The relocated fallback-publish assessed for timing: the counter and the health aggregates now publish from independent 5s intervals rather than one lambda, so their updates can skew by up to one scheduler pass — no consumer couples them (independent diagnostic entities), no observable behavior change for HA.

## Suggested Review Order

**The seam**

- Entry point: now a ~70-line composer — identity, board, network, api encryption, includes, substitutions, package composition.
  [`devices/gateway.yaml:1`](../../devices/gateway.yaml#L1)
- canbus's half: bus definition + heartbeat/health/discovery. Note the bus-in-package rationale in the header.
  [`canbus/packages/health.yaml:1`](../../canbus/packages/health.yaml#L1)
- lighting's half: button decode → HA events + the ha_ready gate instance; the `!extend can0` at the bottom.
  [`lighting/packages/buttons.yaml:1`](../../lighting/packages/buttons.yaml#L1)

**The one semantic change (human-approved)**

- The relocated fallback-aggregate publish, with its rationale comment.
  [`buttons.yaml:167`](../../lighting/packages/buttons.yaml#L167)

**Doc updates**

- lighting's charter — also refreshed its stale pre-amendment AD-7 wording.
  [`lighting/CLAUDE.md:10`](../../lighting/CLAUDE.md#L10)
- [`canbus/CLAUDE.md:35`](../../canbus/CLAUDE.md#L35)
- [`canbus/firmware/README.md:184`](../../canbus/firmware/README.md#L184)
