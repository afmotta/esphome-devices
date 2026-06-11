---
title: 'Ratify ADR-0008 and stand up its post-LIVE evolution artifacts'
type: 'chore'
created: '2026-06-11'
baseline_commit: '115eba9b4659a1d64432aa830a0177b51e5cf307'
status: 'done'
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/planning-artifacts/adrs/0008-post-live-firmware-evolution-no-can-bootloader.md'
  - '{project-root}/_bmad-output/planning-artifacts/adrs/0007-flat-node-id-with-central-meaning-map.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** ADR-0008 captures the post-LIVE firmware/protocol evolution doctrine (controller-absorbs-change, physical-only node/bridge updates, no CAN bootloader) but is still `Proposed`, and two of its open items demand tracked artifacts that do not exist yet — the LIVE-freeze checklist (§5 / open item 5) and the reflash-campaign runbook (open item 2). The doctrine is unratified and its decision-gated deliverables have no home.

**Approach:** Ratify ADR-0008 using the repo's accepted-ADR convention, align the few existing artifacts it explicitly governs (the `canbus_protocol.h` BOOTLOADER reservation comment and the `project-context.md` versioning policy), and create the two tracked artifacts its open items call for. Firmware is validate-only — ADR-0008 produces no wire/protocol change.

## Boundaries & Constraints

**Always:** Use the existing accepted-ADR convention (ADR-0007: `status: 'Accepted'` + `acceptedDate` + a `**Accepted (DATE).**` Status paragraph). Preserve ADR-0008's technical substance and its expiry-date caveat verbatim. Keep every edit minimal and additive. New artifacts must be operator-facing checklists/runbooks that reference ADR-0008, not prose copied from it. The runbook is explicitly a stub pending bench-timing (open item 2). Cross-reference ADR-0008 from every file touched.

**Ask First:** If staying consistent with ADR-0008 would require a *substantive* (non-comment) change to `canbus_protocol.h` or any firmware/YAML; if Alberto wants the checklist/runbook somewhere other than `docs/`; if validation surfaces a real contradiction between the doctrine and shipped firmware.

**Never:** Do not allocate a `CAT_BOOTLOADER` category value or design any reflashing mechanism (§4 forbids it). Do not redesign the protocol, CAN ID layout, or payload semantics; do not bump `PROTO_V1`. Do not fold in the pre-existing project-context ADR-0001 wire-model drift (already tracked in deferred-work — out of scope). Do not resolve open items 1/3/4 (owned by a forthcoming ADR / process). Do not hand-edit generated `nodes/`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Ratification path | ADR-0008 is `Proposed`; no checklist/runbook files exist | ADR-0008 becomes `Accepted` with `acceptedDate`; `docs/live-freeze-checklist.md` + `docs/reflash-campaign-runbook.md` exist and back-reference ADR-0008 | N/A |
| BOOTLOADER already reserved | `canbus_protocol.h` already names BOOTLOADER comment-only, no value allocated | Annotate the comment to cite ADR-0008 §4; leave constants untouched | N/A |
| Firmware-change pressure | Validation suggests honoring the doctrine needs a protocol/YAML edit | Stop, surface the file, renegotiate scope — ADR-0008 is validate-only for firmware | Do not silently broaden the patch |

</frozen-after-approval>

## Code Map

- `_bmad-output/planning-artifacts/adrs/0008-post-live-firmware-evolution-no-can-bootloader.md` -- target ADR to ratify (frontmatter + Status prose + open items 2 & 5 pointers).
- `_bmad-output/planning-artifacts/adrs/0007-flat-node-id-with-central-meaning-map.md` -- accepted-ADR convention exemplar to mirror.
- `firmware/protocol/canbus_protocol.h` -- categories block has the "Values 5-14 reserved … BOOTLOADER" comment to annotate with ADR-0008 §4; versioning comment is validate-only.
- `_bmad-output/project-context.md` -- Versioning policy bullet (line 133) to extend with a post-LIVE doctrine note citing ADR-0008.
- `firmware/bridge/bridge.yaml` -- validation anchor: confirms radios-off (no `wifi:`/`api:`/`ota:`), supports §1/§2; leave unchanged.
- `docs/live-freeze-checklist.md` -- NEW tracked LIVE-freeze checklist (ADR §5 / open item 5).
- `docs/reflash-campaign-runbook.md` -- NEW stub reflash-campaign runbook (open item 2).
- `_bmad-output/implementation-artifacts/deferred-work.md` -- log remaining open items 1/3/4 as deferred.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/planning-artifacts/adrs/0008-post-live-firmware-evolution-no-can-bootloader.md` -- flip frontmatter `Proposed`→`Accepted`, add `acceptedDate: '2026-06-11'`, rewrite the Status paragraph to the `**Accepted (2026-06-11).**` form (preserving the expiry-date caveat and substance), and update open items 2 & 5 to point at the new tracked files -- ratifies the doctrine using the repo convention.
- [x] `firmware/protocol/canbus_protocol.h` -- extend the "Values 5-14 are reserved … BOOTLOADER" comment to cite ADR-0008 §4 (comment-level reservation, no value allocated); change no constant -- records that BOOTLOADER non-allocation is now a ratified decision, not an oversight.
- [x] `_bmad-output/project-context.md` -- after the Versioning policy bullet (line 133), add one bullet stating the post-LIVE doctrine (controller absorbs change; node/bridge updates are physical USB-reflash or board-swap; no CAN bootloader) citing ADR-0008 -- gives agents the post-LIVE rule, not only the pre-LIVE one.
- [x] `docs/live-freeze-checklist.md` -- NEW operator checklist from ADR §5 (sensor-kit soak on production-form node, `ha_ready` tuned with real timeouts/manifest hash, ≥1 bridge soak-tested in line, reflash runbook written + bench-timed, per-release firmware artifacts archived with pinned ESPHome version) with an Alberto sign-off line -- realizes open item 5 as a tracked artifact.
- [x] `docs/reflash-campaign-runbook.md` -- NEW stub runbook: in-place USB reflash (primary) and board-swap (secondary) paths from §2, identity-preservation notes (`node_id` is a flash-time substitution; swap = fresh id + press-to-identify + re-point central map), per-board/fleet time fields marked TBD-by-bench, clearly labeled a stub pending bench-timing -- realizes open item 2.
- [x] `_bmad-output/implementation-artifacts/deferred-work.md` -- append open items 1 (USB-reachability mechanical spec → forthcoming physical/electrical ADR), 3 (firmware artifact archival location/metadata), 4 (spare-stock policy) as deferred with owners -- keeps the unaddressed doctrine items tracked.
- [x] `firmware/bridge/bridge.yaml` -- inspect only; confirm radios-off (no `wifi:`/`api:`/`ota:`) still holds; leave unchanged -- disconfirms the no-firmware-change hypothesis.

**Acceptance Criteria:**
- Given ADR-0008 is the post-LIVE evolution decision record, when its frontmatter and Status section are reviewed, then it is `Accepted` with `acceptedDate: '2026-06-11'`, reads as ratified doctrine (expiry caveat preserved), and open items 2 & 5 reference the new files.
- Given open items 2 and 5 demanded tracked artifacts, when `docs/` is listed, then `live-freeze-checklist.md` and `reflash-campaign-runbook.md` exist, back-reference ADR-0008, and the runbook is explicitly a bench-timing stub.
- Given ADR-0008 §4 forbids a CAN bootloader, when `canbus_protocol.h` is reviewed, then BOOTLOADER remains a comment-level reservation citing ADR-0008 with no category value allocated and no constant changed.
- Given ADR-0008 results in no wire change, when `git diff -- firmware/` is reviewed, then only a comment changed — no protocol constant or YAML behavior.
- Given the doctrine has unaddressed open items, when deferred-work.md is read, then items 1/3/4 are logged with owners.

## Spec Change Log

## Design Notes

Mirrors the [spec-adr-0004-approve-and-align-artifacts.md](spec-adr-0004-approve-and-align-artifacts.md) pattern: ratification + minimal doc alignment, since ADR-0008 is doctrine and §4 forbids new firmware. New artifacts live in `docs/` (operator-facing root, beside `canbus-smart-home-reference.md`); the runbook stays a stub because bench-timing (open item 2) cannot be done from the repo and feeds the LIVE checklist later.

## Verification

**Commands:**
- `grep -nE "status: 'Accepted'|acceptedDate" _bmad-output/planning-artifacts/adrs/0008-post-live-firmware-evolution-no-can-bootloader.md` -- expected: both acceptance markers present.
- `ls docs/live-freeze-checklist.md docs/reflash-campaign-runbook.md` -- expected: both files exist.
- `grep -ln "ADR-0008" docs/live-freeze-checklist.md docs/reflash-campaign-runbook.md firmware/protocol/canbus_protocol.h _bmad-output/project-context.md` -- expected: each touched file cites ADR-0008.
- `git diff -- firmware/` -- expected: only the BOOTLOADER comment in `canbus_protocol.h` changed; no constant or YAML behavior change.

**Manual checks (if no CLI):**
- Confirm `firmware/bridge/bridge.yaml` still has no `wifi:`/`api:`/`ota:` sections (validates ADR §1/§2 radios-off) and is otherwise unchanged.

## Suggested Review Order

**The decision (start here)**

- ADR-0008 ratified — Status declares Accepted and why the bootloader option is let to expire.
  [`0008-no-can-bootloader.md:27`](../planning-artifacts/adrs/0008-post-live-firmware-evolution-no-can-bootloader.md#L27)

- Open items re-pointed: item 2 → runbook, item 5 → checklist; 1/3/4 deferred.
  [`0008-no-can-bootloader.md:198`](../planning-artifacts/adrs/0008-post-live-firmware-evolution-no-can-bootloader.md#L198)

**Doctrine propagated to guidance + code**

- Post-LIVE rule for all agents: controller absorbs change; node/bridge updates are physical-only.
  [`project-context.md:134`](../project-context.md#L134)

- BOOTLOADER stays a comment-level name reservation — ADR-0008 §4, no category value allocated.
  [`canbus_protocol.h:62`](../../firmware/protocol/canbus_protocol.h#L62)

**New operator artifacts**

- LIVE-freeze gate extracted from §5 into a tracked, sign-off checklist.
  [`live-freeze-checklist.md:18`](../../docs/live-freeze-checklist.md#L18)

- Reflash-campaign runbook (stub): controller-first guard, Paths A/B, TBD-by-bench timings.
  [`reflash-campaign-runbook.md:8`](../../docs/reflash-campaign-runbook.md#L8)

- Board-swap path: regenerate + retire the old registry row before reassigning location.
  [`reflash-campaign-runbook.md:47`](../../docs/reflash-campaign-runbook.md#L47)

**Tracking**

- ADR-0008 open items 1/3/4 logged with owners.
  [`deferred-work.md:1`](deferred-work.md#L1)
