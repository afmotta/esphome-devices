---
title: 'Accept ADR-0010 (security posture) — close the OTA hole, register the standing constraints'
type: 'chore'
created: '2026-06-16'
baseline_commit: '6977c727f1f1f1fa7b20924100bb0b2de301029f'
status: 'done'
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/planning-artifacts/adrs/0010-security-posture-accepted-risk-record.md'
  - '{project-root}/_bmad-output/planning-artifacts/adrs/0007-flat-node-id-with-central-meaning-map.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** ADR-0010 records the threat model (physical envelope + LAN as trust boundary, no bus cryptography, four consequence-limiting invariants) but is still `Proposed`. Writing it surfaced one concrete defect — the gateway's OTA is unauthenticated (`ota: platform: esphome`), the most privileged device pushable by anyone on the LAN — plus one standing constraint (no security-critical actuation on this bus) to register where future features are intaked.

**Approach:** Accept ADR-0010 via the repo's accepted-ADR convention, make the one mandated code change (wire the already-provisioned `ota_password` secret into the gateway), register the actuation constraint in `project-context.md`, and defer open items 2/3/4 to their named owners. No bus-protocol or wire change — the ADR explicitly forgoes bus cryptography.

## Boundaries & Constraints

**Always:** Use the existing accepted-ADR convention (ADR-0007: `status: 'Accepted'` + `acceptedDate` + an `**Accepted (DATE).**` Status paragraph). Preserve ADR-0010's substance verbatim — especially the named revisit triggers (exterior need; RP2350-class platform change; nodes gaining RX behavior) and the §2 envelope rule. Keep every edit minimal and additive. The OTA password is the **only** firmware change. Cite ADR-0010 in every file touched (gateway.yaml and secrets example via inline comment).

**Ask First:** If closing the OTA hole would require editing the real gitignored `secrets.yaml` (it must not — `ota_password` is already present there; this spec only wires the reference and updates the `.example`). If Alberto wants the standing constraint registered somewhere other than `project-context.md`. If any device other than the gateway is found to carry OTA today and would need the same wiring now.

**Never:** Do not add per-frame MACs, frame signing, encryption, or any node key material (ADR §3 explicitly forgoes bus crypto). Do not build the isolated/filtering security segment (ADR rejects building the exception before an exterior device exists). Do not give nodes any `CAT_OUTPUT`/RX-driven behavior (breaks invariant §4.1). Do not resolve open items 2/3/4 (owned by the physical-topology ADR, external HVAC firmware, and the monitoring ADR). Do not generate, rotate, commit, or print the real OTA secret. Do not hand-edit generated `firmware/nodes/`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Wire the OTA password | `ota:` block is `- platform: esphome` only; real `secrets.yaml` already defines `ota_password` | block gains `password: !secret ota_password`; `esphome config` validates and the secret resolves | N/A |
| Secret resolution | `esphome config firmware/gateway/gateway.yaml` run after the edit | passes; no "secret not defined" error (secret pre-exists) | If it ever errored, the secret is missing — STOP, do not invent one |
| Scope boundary | firmware grepped for `ota:` | only the gateway carries OTA + password; bridge stays radios-off, nodes have no network | N/A |

</frozen-after-approval>

## Code Map

- `_bmad-output/planning-artifacts/adrs/0010-security-posture-accepted-risk-record.md` -- target ADR to accept (frontmatter + Status prose + open-items 1 & 5 status).
- `_bmad-output/planning-artifacts/adrs/0007-flat-node-id-with-central-meaning-map.md` -- accepted-ADR convention exemplar to mirror.
- `firmware/gateway/gateway.yaml` -- the `ota:` list (lines 123-124) is `- platform: esphome` with no password; the one mandated code change (§5).
- `firmware/gateway/secrets.yaml.example` -- 4-line committed template; needs an `ota_password` entry mirroring the `api_encryption_key` comment style.
- `firmware/gateway/secrets.yaml` -- gitignored real secrets; already defines `ota_password` (verified key present). Inspect-only — never edit, commit, or print.
- `firmware/bridge/bridge.yaml` -- validation anchor: confirms radios-off (no `ota:`); leave unchanged.
- `_bmad-output/project-context.md` -- Critical Don't-Miss Rules section: add the standing no-security-critical-actuation constraint (open item 5).
- `_bmad-output/implementation-artifacts/deferred-work.md` -- log open items 2/3/4 as deferred.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/planning-artifacts/adrs/0010-security-posture-accepted-risk-record.md` -- flip frontmatter `Proposed`→`Accepted`, add `acceptedDate: '2026-06-16'`, rewrite the Status paragraph to the `**Accepted (2026-06-16).**` form (preserve the substance: posture-is-a-decision, the one defect found, the envelope rule), and mark open item 1 (OTA) closed/implemented + open item 5 (constraint) registered -- accepts the posture via repo convention.
- [x] `firmware/gateway/gateway.yaml` -- add `password: !secret ota_password` under the `ota: - platform: esphome` list item, with a short inline comment citing ADR-0010 §5 -- closes the unauthenticated-OTA hole (the one mandated code change).
- [x] `firmware/gateway/secrets.yaml.example` -- add an `ota_password` placeholder line with a generation hint and an ADR-0010 §5 comment -- documents the now-required secret (the real `secrets.yaml` already carries it).
- [x] `_bmad-output/project-context.md` -- in "Critical Don't-Miss Rules", add a bullet registering the standing constraint: this bus must never carry security-critical actuation (door locks, alarm arming) without revisiting ADR-0010 -- gives agents the constraint at activation (open item 5).
- [x] `_bmad-output/implementation-artifacts/deferred-work.md` -- append a "Deferred from: ADR-0010 acceptance + implementation (2026-06-16)" section logging open items 2 (envelope audit → physical-topology ADR queue #2 + commissioning runbook), 3 (HVAC sensor sanity bounds → external HVAC firmware), 4 (security signals in monitoring ADR queue #5); note items 1 & 5 resolved here -- keeps unaddressed items tracked.

**Acceptance Criteria:**
- Given ADR-0010 is the security-posture record, when its frontmatter and Status are reviewed, then it is `Accepted` with `acceptedDate: '2026-06-16'`, reads as ratified (substance + the three named revisit triggers preserved), and open item 1 is marked closed.
- Given the OTA hole was the one mandated code change, when `gateway.yaml`'s `ota:` block is reviewed and `esphome config` is run, then `password: !secret ota_password` is present, the secret resolves (no "secret not defined"), and no other firmware behavior changed.
- Given the gateway is the only OTA-capable device today, when firmware is grepped for `ota:`, then only the gateway carries an OTA password — bridge stays radios-off, nodes unchanged.
- Given the standing actuation constraint, when `project-context.md` Critical Don't-Miss Rules are read, then it is present and cites ADR-0010.
- Given ADR-0010 has open items beyond this pass, when `deferred-work.md` is read, then items 2/3/4 are logged with owners and items 1/5 are recorded as resolved here.

## Spec Change Log

## Design Notes

Mirrors the [spec-adr-0008-ratify-and-evolution-artifacts.md](spec-adr-0008-ratify-and-evolution-artifacts.md) pattern: ADR acceptance + minimal doc/config alignment, deferring open items to their owners. Key finding that makes the code change a one-liner: the real (gitignored) `secrets.yaml` **already defines `ota_password`** — provisioned but never referenced — so the hole closes additively, no secret-generation step, no compile break. The §2 envelope rule and §3 no-bus-crypto stance produce no code now (constraints for the physical-topology and platform-generation revisit triggers). The §6 detection primitive `esphome.canbus_node_unknown` already ships in `gateway.yaml`; promoting it to a security signal is the monitoring ADR's job (deferred).

## Verification

**Commands:**
- `grep -nE "status: 'Accepted'|acceptedDate" _bmad-output/planning-artifacts/adrs/0010-security-posture-accepted-risk-record.md` -- expected: both acceptance markers present.
- `esphome config firmware/gateway/gateway.yaml >/dev/null && echo CONFIG_OK` -- expected: `CONFIG_OK` (YAML valid, `!secret ota_password` resolves, `ota` schema accepts `password`).
- `grep -rn "ota:" firmware --include="*.yaml" | grep -vE '\.esphome|build|storage'` -- expected: only `gateway.yaml` (with the new password line) and the `bridge.yaml` radios-off comment.
- `grep -ln "ADR-0010" firmware/gateway/gateway.yaml firmware/gateway/secrets.yaml.example _bmad-output/project-context.md _bmad-output/implementation-artifacts/deferred-work.md` -- expected: each touched guidance/config file cites ADR-0010.

**Manual checks (if no CLI):**
- If `esphome` is unavailable: confirm `password: !secret ota_password` sits under the `ota:` list item in `gateway.yaml`, and `ota_password:` exists in the gitignored `firmware/gateway/secrets.yaml` (inspect keys only — do not print values).

## Suggested Review Order

**The decision (start here)**

- Posture ratified: Status names the one defect found (OTA) and the three named revisit triggers.
  [`0010-security-posture.md:28`](../planning-artifacts/adrs/0010-security-posture-accepted-risk-record.md#L28)

- Open items 1 (OTA) & 5 (constraint) marked done; 2/3/4 deferred to their owners.
  [`0010-security-posture.md:193`](../planning-artifacts/adrs/0010-security-posture-accepted-risk-record.md#L193)

**The one mandated code change (§5)**

- OTA now authenticated — the only bus-external defect, closed; `esphome config` validates it.
  [`gateway.yaml:127`](../../firmware/gateway/gateway.yaml#L127)

- New required secret documented with an openssl generation hint.
  [`secrets.yaml.example:6`](../../firmware/gateway/secrets.yaml.example#L6)

**Guidance + tracking propagation**

- Standing rule for all future agents: no security-critical actuation on this bus.
  [`project-context.md:154`](../project-context.md#L154)

- Remaining open items logged to their named owners.
  [`deferred-work.md:10`](deferred-work.md#L10)
