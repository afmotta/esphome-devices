# Lighting Subsystem — AI Assistant Guide

This is the lighting application system (layered-restructure spine,
`_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md`).
It is **pre-live**: no fallback/relay code exists yet — this directory currently
holds only the HA-side reference automations and this charter. The actual
fallback/relay packages land in migration Phase 5, alongside ADR-0013 open
item 2.

## What lighting owns

- **`registry/bindings.yaml` schema** — the binding manifest's shape (fields,
  ops, fan-out) is lighting's to define and change (ADR-0013 lineage). A
  schema change to `bindings.yaml` is a lighting-owned edit.
- **Fallback semantics** — what a binding *means* (which relay(s), which op)
  when Home Assistant is down. This is lighting's domain knowledge; canbus
  never interprets it.
- **HA-side automations under `lighting/home-assistant/`** — hold/hold_release
  dimmer and cover gestures (ADR-0012), and eventually any lighting-specific
  automation that isn't arbitration.

## What lighting never touches (AD-7)

- **Canonicalization or the manifest hash** — `tools/bindings.py`'s
  `canonical_hash` and the compiled `bindings.h` table are canbus-owned. A
  lighting schema change that alters canonical form is still an AD-6 contract
  change: canbus regenerates both sides in the same commit.
- **The `ha_ready` arbitration gate or fallback trigger logic** — that stays
  infra-owned and semantics-blind in canbus; lighting supplies meaning, not
  gate mechanics.

## Files here today

- `lighting/home-assistant/ha_hold_automations.yaml` — hand-maintained HA reference
  automations for hold/hold_release gestures (ADR-0012). Copy or `!include`
  into Home Assistant; replace the EXAMPLE node_id/button/entity_id values
  with real ones.

## Conventions

- Epic prefix: **LIGHT-**. New BMAD artifacts go to the root `_bmad-output/`.
- Entity-ID/automation-naming conventions are lighting's own to set once real
  fallback code lands — not yet decided (see Deferred in the architecture
  spine).
