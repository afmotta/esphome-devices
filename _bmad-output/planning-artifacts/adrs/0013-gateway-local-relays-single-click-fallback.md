---
adr: 0013
title: 'Gateway-local relays and single-click fallback bindings: progressive relay ids, no Modbus addressing in the registry, one binding file'
status: 'Proposed'
date: '2026-06-16'
deciders: ['Alberto']
author: 'Winston (System Architect)'
dependsOn:
  - 'ADR-0003: Centralized single-controller with on-board fallback (partially superseded here: relay transport + binding-model scope)'
  - 'ADR-0009: Central map & binding manifest (resolves its open item 1 — binding action vocabulary)'
  - 'ADR-0012: Hold/release gestures are HA-only continuous control (consistent with single-click fallback)'
supersedes:
  - 'ADR-0003 §Decision: relays as Modbus/RS485 modules backed by ESPHome switch entities'
  - 'ADR-0003 §Decision: binding model with mode (ha_with_local_fallback / local_authoritative / ha_only) and per-event fallback'
relatedDocuments:
  - _bmad-output/planning-artifacts/adrs/0003-centralized-single-controller-with-onboard-fallback.md
  - _bmad-output/planning-artifacts/adrs/0009-central-map-binding-manifest-system-of-record.md
  - _bmad-output/planning-artifacts/adrs/0012-hold-release-button-gestures-continuous-control.md
  - firmware/registry/bindings.yaml
  - firmware/tools/bindings.py
  - firmware/tools/generate_nodes.py
  - firmware/protocol/bindings.h
  - firmware/gateway/gateway.yaml
---

# ADR-0013: Gateway-local relays, single-click fallback

## Status

**Proposed.** Resolves ADR-0009 open item 1 (binding action vocabulary) and **partially
supersedes ADR-0003**: the relay *transport* (Modbus/RS485 relay modules) and the *binding
model* (per-event bindings with a three-way `mode`). ADR-0003's load-bearing core is
untouched — one centralized controller, `ha_ready`/ACK arbitration, HA-drives-when-up /
board-drives-when-down, and the manifest-hash agreement that gates fallback authority. What
changes is only how the fallback expresses itself: **fewer relays to address, fewer gestures
to handle, one file to keep.**

## Context

ADR-0003 specified a capable fallback: relays as Modbus/RS485 modules (remoteable), exposed
as ESPHome `switch` entities, with bindings carrying a `mode`
(`ha_with_local_fallback` / `local_authoritative` / `ha_only`) and acting on the full event
vocabulary. ADR-0009 then made bindings real as data (`registry/bindings.yaml` + a canonical
hash) but deliberately deferred the *action side* — relay naming and Modbus addressing — to
this decision (its open item 1), pending board selection (ADR-0003 open item 7).

Two observations collapse that deferred scope:

1. **The fallback's only job is keeping basic switching alive when HA is down.** Everything
   rich is already HA-only by prior decision: ADR-0012 puts *all* continuous control
   (hold-to-dim, hold-to-move) and the long-press derivation in HA, and ADR-0003 itself makes
   Zigbee/Thread fixtures HA-only. By the same logic, multi-gesture / multi-mode fallback is
   machinery for a job the fallback doesn't have. The single click — "toggle this light" — is
   the whole of what must survive an HA outage.

2. **Modbus addressing is a maintenance surface the house doesn't need.** Authoring and
   keeping `(slave address, coil)` tuples in git, validated and hash-stamped, is real
   overhead. If relays live on the controller board itself, addressed by position, the entire
   addressing concern disappears — `relay_5` is just the 5th output.

These together mean the binding manifest needs to express only: *which button, when single-
clicked, toggles which relay(s)* — no event, no mode, no address. That is small enough to be
one file with nothing beside it.

## Decision

The stance in one line: **fallback is single-click only and drives gateway-local relays by
progressive id; the binding manifest is one file keyed `(node_id, button) → relay id(s) +
op`, with no event, no mode, and no addresses anywhere in git.**

### 1. Relays are gateway-local outputs, addressed by progressive id

Relays are physical outputs **on the controller/gateway board** (ADR-0003 §71: the single
controller subsumes the PoC gateway role). They are referenced by a **progressive id** —
`relay_0, relay_1, …` — and the gateway resolves id → physical output **by position**. No
Modbus addresses, coils, or slave ids live in `registry/`. The relay outputs themselves are
defined in the gateway's own ESPHome config (hardware), not in the registry.

The registry model is deliberately **transport-agnostic**: because `relay_N` is opaque, a
later move to Modbus relay banks (ADR-0003's original remoteable design) needs *no registry
change* — only a `relay_N → coil` map in the gateway config. This ADR fixes the *meaning*
(progressive id) and the *current realization* (local outputs); it does not weld the registry
to either transport.

### 2. Fallback acts on the single click only

When HA is down, the gateway acts on the **single click** and nothing else.
Double/triple/hold are HA-only and simply do nothing during an outage — consistent with
ADR-0012 (continuous control is HA-side) and ADR-0003 (HA-only fixtures degrade to no
response). Because there is exactly one fallback gesture, it is **implicit**: a binding
carries no `event` field. This also forbids, by construction, authoring a fallback binding on
a gesture that can never fire — the same "no silently-dead binding" principle the validator
already applies to out-of-range buttons.

ADR-0003's three-way `mode` is dropped: every binding is "toggle locally on single-click when
HA isn't ready." A relay-backed light degrades to on/off; everything else degrades to HA-only
by absence.

### 3. One file: `(node_id, button) → relay id(s) + op`

`registry/bindings.yaml` is the single source — no separate actuator/relay-map file, because
a relay has no metadata to store beyond its id (no address, no per-relay config). Schema
(strict scalars-only subset, unchanged reader):

```yaml
schema_version: 1
bindings:
  - node_id: 100
    button: 0
    relay: 0          # gateway relay_0
    op: toggle
  - node_id: 100
    button: 1
    relay: "3,4,5"    # one click → relays 3,4,5 (fan-out)
    op: toggle
```

- **Key:** `(node_id, button)`, unique. No `event`.
- **`relay`:** a single progressive id, or a **comma-list scalar** for fan-out (one click →
  several relays). The list stays in *one scalar*, so the strict no-nesting reader is
  unchanged; it is normalized (sorted, de-duplicated) before validation and hashing.
- **`op`:** `on | off | toggle`, one op applied to every listed relay. **Mixed per-relay ops
  are not expressible** — that would need nested structure (the deferred PyYAML decision,
  ADR-0009 open item 1). For an all-on/all-off group prefer explicit `on`/`off` over `toggle`
  (which desyncs from mixed start states).

The compiled fallback artifact mirrors this: `BindingEntry { node_id, button, relay_count,
relays, op }` and `binding_find(node_id, button)`. The manifest hash and `ha_ready`
agreement (ADR-0003/0009) are unchanged in mechanism — only the data shape shrank.

### 4. The live path is unchanged and uses the same relays

HA, when up, drives the same gateway relays it always would — as ESPHome `switch` entities
over the Native API. The progressive-id manifest governs only the **fallback** path; the live
path targets HA entities as before (ADR-0003). One set of physical relays, two drivers (HA
online, gateway offline), one gate — exactly ADR-0003's stance, with a simpler fallback.

## Consequences

### Positive

- **No addressing surface.** No Modbus tuples to author, validate, or hash; `relay_N` is the
  whole identity. The registry stays the minimum that expresses house behavior.
- **One file, one concern.** Button → relay, nothing beside it; reviewed by git diff like the
  rest of the registry. No second actuator-map artifact.
- **Smallest fallback that does the job.** HA-down still toggles lights; the rich
  interactions that were always HA-dependent (dimming, covers, scenes) are unaffected because
  they never relied on fallback.
- **Transport-agnostic by id.** A future return to remoteable Modbus relays is a gateway-
  config change, not a registry/schema change — the opaque id absorbs it.

### Negative / costs

- **Fallback is genuinely minimal:** single-click toggle only. No dimming, covers, scenes, or
  `local_authoritative` behavior when HA is down — those stop until HA returns. Accepted: the
  fallback is a safety floor, not a feature.
- **Relays must be on (or wired to) the gateway board.** Dropping Modbus relay modules gives
  up ADR-0003's remoteable relay placement; the board must provide enough outputs for every
  fallback-critical load, and home-run wiring reaches them. Revisitable via §1's transport-
  agnostic id if topology later demands remote banks.
- **A stale gateway comment.** `gateway.yaml` still says "relay control is Modbus/API …
  input-only"; it must be corrected when relay outputs are actually added (open item).
- **Re-narrows a capability ADR-0003 deliberately left broad.** The multi-mode/event binding
  model is gone; if a future need for `local_authoritative` or non-single fallback appears, it
  is a new decision, not a config toggle.

## Alternatives considered

- **Keep ADR-0003 as written (Modbus relay banks + multi-mode/event bindings).** Rejected:
  more addressing and binding machinery than a house needs pre-LIVE, for fallback behavior
  (rich gestures, multiple modes) that the rest of the architecture already routes through HA.
- **Progressive ids over Modbus relays (keep Modbus, hide it behind ids).** Not rejected so
  much as **deferred** — the chosen model is transport-agnostic (§1), so this is the natural
  later step if remote relay placement is needed. Chosen now: local outputs, no Modbus at all.
- **Two files (relay catalog + bindings), HA-entity naming in the registry.** Rejected: with
  no per-relay metadata and relays defined in the gateway config, a catalog is an empty
  ceremony; the id is sufficient.
- **Keep the `event` field, constrain it to `single`.** Rejected: verbose with no gain, and
  it permits authoring double/triple/hold fallback bindings that silently never fire — the
  exact failure the validator otherwise prevents.

## Open items

1. **Relay count / board (ADR-0003 open item 7).** How many relay outputs the gateway board
   provides, and whether to add a max-relay-id validation bound once that count is fixed.
   Until then the validator checks only `relay >= 0`.
2. **Wire the gateway fallback to drive outputs.** The compiled `BINDINGS[]` table is still
   log-only; making it actuate gateway relay outputs (and defining those outputs in
   `gateway.yaml`) is the implementation slice. Fix the stale "input-only/Modbus" comment then.
3. **Live-path relay entities.** Confirm the gateway exposes `relay_N` outputs to HA as switch
   entities so the live path drives the same relays the fallback does.
4. **HA package interplay (ADR-0009 open item 3).** The generated HA side currently echoes the
   manifest hash; if HA automations for the single-click bindings are ever generated, they
   target the same relay entities as §3.

## Notes

This is the simplification ADR-0003 explicitly left room for (its topology was "parked for a
future ADR"; its open item 7 gated the relay specifics). It follows the same trajectory as
ADR-0012: push capability into HA, keep the device/firmware surface minimal, and let the
fallback be the smallest thing that keeps the lights working. The registry model decided here
(progressive ids, single-click, one file) is the durable part; the gateway-local realization
is the current answer to ADR-0003 §7, changeable without touching the registry.
