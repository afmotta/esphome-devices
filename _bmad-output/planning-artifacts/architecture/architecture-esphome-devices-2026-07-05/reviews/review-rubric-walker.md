# Rubric-Walker Review — ARCHITECTURE-SPINE.md (esphome-devices layered restructure)

**Reviewer lens:** GOOD-SPINE RUBRIC (6 points)
**Target:** `_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md`
**Companions read:** `MIGRATION-MAP.md`, `.memlog.md`
**Repo reality checked:** current tree (`canbus/firmware/{registry,tools,tests,gateway,bridge,nodes}`, root `home-assistant/{canbus,dashboards}`, root `locals/`, `remotes/`, `libs/`, empty `scripts/`, no CI workflows under `.github/`), `canbus/docs/merge-into-esphome-devices-proposal.md`, ADR-0009 (Accepted), ADR-0013 (Proposed), `_bmad-output/specs/spec-map-json-contract/SPEC.md`, `canbus/CLAUDE.md`, root `CLAUDE.md`.

**Verdict: PASS-WITH-FIXES.** The spine is genuinely good at this altitude: the ten ADs hit the real seams (merge-history organization, registry ownership, board-vs-system composition, HA import surface, contract freezing, arbitration blindness, generated-artifact territory, pre-live atomicity, convention scoping), and its cross-system contract rule (AD-6) plus the AD-2 carve-out ("infra tooling may read app data only where a frozen contract names the path") is a precise ratification of how `generate_nodes.py` already validates `room_slug` against the climate rooms. The findings below are fixable without rethinking the paradigm.

---

## Rubric point 1 — Fixes the real divergence points for the level below; misses none

**Mostly yes.** The divergence points that would actually bite future CAN-/LIGHT-/HVAC-epic work are each pinned by an AD: where new files land (AD-1), dependency direction (AD-2), who may edit which registry file (AD-3), what happens when one board hosts two systems (AD-4 — this is the sharpest call in the document, and it correctly pre-decides the T-Connect swap shape), what HA imports (AD-5), when a boundary becomes a contract (AD-6), the canonicalization/meaning seam (AD-7), generated-file territory (AD-8), move atomicity (AD-9), and convention scoping (AD-10). The memlog shows each AD traceable to a named divergence observed in the repo, not invented.

**Misses (see Findings F1, F3, F6):**

- The **enumeration in AD-1 is incomplete against its own structural seed** — `libs/` is in the seed tree but not in AD-1's "exactly these" list of homes, and `scripts/` is only in Deferred. AD-1's rule is "every new file lands inside exactly one of these homes"; an enumeration that omits a real directory cannot enforce that. Where does the *next* custom external component (the next `s1_pro`) go — `libs/`, `hvac/`, or `vesta/`? Undecided. (F3)
- The **`node_map.h` C++ compile-time export** (ADR-0009 §7: frozen-additive, "the HVAC controller builds against this repo and includes it like the gateway does") is a named canbus→consumer contract surface that AD-6's instance list omits. If hvac-on-CAN consumer code prefers the header over `map.json`, it crosses a boundary with a freeze but no drift test named. Cheap fix: add it to AD-6's instance list with "test due when a second consumer includes it." (F6)
- Root `docs/` vs per-system docs (`canbus/docs/` exists and stays): AD-1 names `docs/` as a home but gives no rule for which docs are repo-level vs system-level; a new lighting runbook has two plausible homes. Minor; per-system CLAUDE.mds (AD-10) will likely absorb this. (noted, low)

## Rubric point 2 — Every AD's Rule is enforceable and prevents its stated divergence

**Largely yes; two soft spots.**

- **AD-3, AD-8, AD-9** are the strongest: each has a mechanical check already in the repo (push gate, `git diff --exit-code` idempotence, per-slice battery). AD-8's rule even names its own verification.
- **AD-6** is well-formed — "not a contract until spec + drift-breaking test" is a bright line, and the Phase 4 handling of the `components/rooms/**` → `hvac/rooms/**` glob (spec, code, and test in one commit) demonstrates the rule working.
- **AD-2 (dependency direction) has no mechanical teeth** (F5). In a YAML-includes monorepo there is no import linter; nothing but review prevents a `canbus/packages/` file from `!include`-ing `lighting/`. A one-line grep check (forbidden path prefixes per directory) added to the battery would make the rule self-enforcing. Low severity pre-live with one committer, but the project's own retro doctrine ("mechanical gate, not another action item" — Epic 3 retro) argues for tooling here too.
- **AD-5** is enforceable in-repo (path convention) but the *other side* — the HA instance's package includes — lives outside the repo, and the migration map correctly carries manual re-point steps in Phases 2–3. The rule prevents the divergence it names (monolithic `home-assistant/` regrowing) as well as any path convention can.
- **AD-1** would be enforceable if its enumeration were complete (F3).

## Rubric point 3 — Nothing under Deferred lets two units diverge in the meantime

**Almost clean.** Walking the table:

- *Contract tests in push gate* — safe **only if** the battery actually runs between migration slices; see F4.
- *Master-controller swap* — safe; AD-4 is explicitly designed so the swap is a new entry point. Correct.
- *hvac-on-CAN consumer placement* — safe; the contract is frozen and AD-1/AD-2 already bound where the code could land (an application concern, so `hvac/`).
- *Gateway extraction granularity* — safe; AD-7 fixes the seam (hash/gate vs meaning), so however Phase 5 slices the YAML, the two systems can't claim the same responsibility.
- *boards/ unification* — safe; ratifies the merge proposal's "don't force it."
- *Vesta extraction* — safe; AD-2 isolates it.
- *scripts/, secrets layout* — "no divergence risk" is asserted, and `scripts/` is currently **empty** (verified), so it holds today. But note the interaction: Phase 5 moves the gateway's `secrets.yaml` into `devices/`, while `locals/secrets.yaml` and `remotes/secrets.yaml` also exist and the spine's own seed puts `locals/`/`remotes/` under `devices/` — three secrets files converging on one directory with ESPHome's resolve-next-to-config semantics. The deferral is fine; the migration map should note the collision so Phase 5 doesn't discover it mid-commit. (part of F1/F8)

## Rubric point 4 — Named tech verified-current / consistent with repo reality

**Verified, all consistent; no new tech bound (as claimed).**

- ESPHome 2026.3.0+ — matches root `CLAUDE.md`.
- Python 3.x stdlib-only registry tooling — matches `canbus/firmware/tools/` (no third-party imports; ADR-0009 §4 mandates stdlib-only).
- C++17 — matches every native test command in the battery and `canbus/CLAUDE.md`.
- HA 2024.x+ — matches root `CLAUDE.md`.
- CAN 125 kbps, 29-bit extended IDs — verified present in ADR-0001's context ("communicating over CAN bus at 125 kbps"; extended-ID addressing is ADR-0001's subject). Citation holds.
- Modbus RTU 9600 8N1 — matches root `CLAUDE.md` and the hvac boards.

Nit: frontmatter `binds: []` is empty while every AD says "Binds: all/…" — either populate it or drop it; an empty binds list on a build-substrate spine reads as unfinished. `status: draft` is honest but should flip on ratification. (F7)

## Rubric point 5 — Ratifies rather than contradicts the brownfield and standing decisions

**Strong, with one structural gap.**

- **ADR-0013**: AD-7 restates its seam faithfully (canbus owns canonicalization/hash/`ha_ready`/gate; lighting owns meaning; `BindingEntry`/`bindings.h` is the surface), and Phase 5 sequences the fallback-actuation package with ADR-0013 open item 2. Ratified.
- **spec-map-json-contract**: AD-3 names map.json's consumer contract as hvac-owned and frozen; Phase 4 treats the `components/rooms/**` path constraint as an AD-6 contract edit (spec + code + test, one commit). This even resolves the spec's own open question direction (the validation path is contract-named, so it moves with the contract). Ratified.
- **Merge proposal**: the one deliberate reversal — the proposal's Phase 4 "one `home-assistant/` directory answers what HA imports" becomes AD-5's per-system split — is documented as Alberto's amendment in the memlog and AD-5's Prevents line names the old shape as the divergence. A supersession done properly. The proposal's "don't force boards/ unification" advice is ratified verbatim in Deferred.
- **ADR-0009 — the gap (F2):** AD-1 declares `canbus/_bmad-output/` **frozen in place**, yet the spine changes facts that Accepted, load-bearing ADR-0009 states: §1 names `firmware/registry/` in the (canbus) tree as "the single authoritative home"; its frontmatter and §7 cite `firmware/registry/*`, `firmware/gateway/gateway.yaml` — paths Phases 1 and 5 relocate. Migration Phase 1 updates the spec, CLAUDE.mds, and runbooks but **not the ADR**, and the freeze rule forbids updating it — so after Phase 1 the standing decision record contradicts the repo with no recorded supersession. Note the freeze is already softer in practice: ADR-0009 was annotated on 2026-07-05 to close open item 5. The spine needs one sentence deciding where supersession notes live (annotate the historical ADR despite the freeze, or record supersessions in a root `_bmad-output/` ADR/log and point AD-1's freeze at *content*, not *pointers*).

## Rubric point 6 — Every owned dimension decided, deferred, or open; operational envelope especially

**Better than most spines — the Structural Seed's "Deployment envelope" paragraph exists and is accurate** (nodes USB-flashed and frozen; OTA via `locals/`/`remotes/`; GitHub `@main` fetch is why AD-9 atomicity exists; HA imports only `<system>/home-assistant/`; both subsystems pre-live; no staging; battery + push gate = release gate). Environments: decided (there is deliberately no staging). Operations: runbooks are path-updated in Phases 1 and 6; drift visibility is ADR-0009 §6's standing mechanism. Security: silent, but ADR-0010 (accepted-risk record) stands uncontradicted and secrets layout is explicitly deferred — acceptable at this altitude.

**Two dimension-level findings:**

- **F1 (the big one): the spine and its own migration map diverge on `locals/`/`remotes/`.** AD-4's rule and the seed bind entry points "plus their `locals/` and `remotes/` variants" into `devices/`, and the deployment envelope says "locally from `devices/locals/`, in production via `devices/remotes/`" — but **no migration phase moves them**. `locals/` and `remotes/` sit at repo root today (verified), the standing battery cites `esphome config locals/climate-control.yaml` through Phase 6 with no noted shift, and Phase 6 claims "final paths." So the plan, executed fully, ends with the spine's own rule violated — the exact rule-vs-repo drift a spine exists to prevent. The move also needs its own manual step (the HA ESPHome-addon dashboard points at local file paths, same class as Phases 2–3's re-point) and a secrets-resolution note (F8). Fix: either add the move to a phase (with AD-9 atomicity and the manual step), or amend AD-4/seed/envelope to keep `locals/`/`remotes/` at root — one of the two documents must yield.
- **F4: steady-state verification cadence is decided only for migration slices.** The Consistency Conventions row scopes the battery "per slice (AD-9)"; there is **no CI** (verified: `.github/` holds only agents/chatmodes), so AD-6's drift tests bite only when a human runs them, and the deferral of push-gate wiring means nothing mechanical runs them either. The envelope's "battery + push gate are the release gate" sentence partially covers this, but it should be stated as a standing rule for *feature work* (every HVAC-/LIGHT-/CAN-epic change runs the battery, or CI is explicitly deferred as a decision), not left implied. The project's own memory ("story-close drift recurred 3 epics; the fix is a tooling gate, not discipline") says exactly why.

---

## Findings summary

| # | Severity | Finding | Fix |
|---|----------|---------|-----|
| F1 | **High** | Spine binds `locals/`/`remotes/` into `devices/` (AD-4, seed, deployment envelope) but the migration map never moves them and its battery cites root `locals/` through "final paths" — the spine's own rule ends up violated by its own plan | Add the move to a phase (with manual HA-addon re-point + AD-9 atomicity) **or** amend AD-4/seed/envelope to keep them at root |
| F2 | **Medium** | AD-1 freezes `canbus/_bmad-output/` while the spine supersedes facts Accepted ADR-0009 states (`firmware/registry/` as authoritative home; gateway path); no rule says where supersession/amendment notes live | One sentence in AD-1 or AD-10: supersessions of frozen-tree ADRs are recorded via annotation (the existing 2026-07-05 precedent) or a root-`_bmad-output/` ADR; add ADR-0009 annotation to Phase 1's doc-update list |
| F3 | **Medium** | AD-1's "exactly these homes" enumeration omits `libs/` (present in its own structural seed) and leaves `scripts/` only in Deferred — the anti-ambient-root rule can't be enforced from an incomplete list; a new external component has no decided home | Add `libs/` to AD-1's enumeration (or fold it into `hvac/`/system ownership and say so) |
| F4 | **Medium** | Standing verification is bound only "per slice (AD-9)"; no CI exists and push-gate wiring is deferred, so AD-6 drift tests run only on human initiative during ordinary feature work | State the battery as the standing per-change gate for all epic work, or add "CI" as an explicit Deferred row with a trigger |
| F5 | Low | AD-2 dependency direction has no mechanical check (no include-path linter); review-only enforcement contradicts the project's own mechanical-gate doctrine | Add a grep-based forbidden-include check to the battery (one-liner) |
| F6 | Low | AD-6's instance list omits `node_map.h` (ADR-0009 §7 frozen-additive C++ export), the other canbus→consumer contract surface | Add as a fourth instance, test due when a second firmware consumer includes it |
| F7 | Low | Frontmatter `binds: []` empty while ADs declare binds; `status: draft` | Populate or drop `binds`; flip status on ratification |
| F8 | Low | Phase 5 moves gateway `secrets.yaml` into `devices/` where `locals/secrets.yaml`/`remotes/secrets.yaml` may also converge (per F1's resolution), with ESPHome's next-to-config secret resolution | Note the collision in the migration map's Phase 5 / risk register |

**Not findings (verified clean):** Stack table fully consistent with repo reality; AD-2's contract-named-path carve-out precisely matches the shipped `room_slug` validation; AD-5's reversal of the merge proposal's monolithic-HA-dir advice is a documented, deliberate supersession; all Deferred rows except the F1/F4-adjacent ones are genuinely divergence-safe; the migration map's phase ordering rationale (registry first, cosmetic flatten last) is sound and each phase carries AD-9-compliant verification.

**Verdict: pass-with-fixes** — fix F1 before ratification (it is a self-contradiction, not a judgment call); F2–F4 are one-sentence edits to the spine or one-line additions to the migration map.
