# PRD Quality Review — CAN Bus Smart Home PoC (2026-05-29)

## Overall verdict

This is a well-constructed capability spec for a tightly scoped hardware PoC. The protocol is precisely specified, open questions are correctly classified as blocking/non-blocking, assumptions are tagged inline, and the Non-Goals section does real work by explicitly naming deferred scope. Two gaps need resolution before this is fully build-ready: the INT pin assumption (OQ-2) feeds a compile-blocking unknown that should be answered before the PRD is signed off rather than deferred to the developer; and FR-9 acceptance criteria do not cover failure modes or timing tolerances, leaving the PoC/fail boundary under-defined. Neither is fatal at this stage, but both should be addressed before the first firmware compile.

---

## 1. Decision-readiness — adequate

The PRD names a clear decision: validate this hardware/software stack on a 2-node bench before committing to 100+ node hardware procurement. That decision is never buried or softened. Trade-offs are surfaced honestly — WiFi-only gateway acknowledged as a downgrade from Ethernet, no OTA on nodes named explicitly as a constraint, compile-first rule elevated to an NFR with a blocking-defect label.

Open Questions are genuinely open. OQ-4 ("highest-risk software path, has not been tested") is the most honest line in the document and correctly marked blocking. The risk table reinforces this with "High / High" on the `on_frame` + `homeassistant.event` chain.

### Findings

- **medium** Missing decision rationale for 125 kbps bus speed (§ FR-2.3, NFR-6) — 125 kbps is stated as a requirement but the document never explains why (vs. 250/500 kbps, which are more common CAN defaults). For a PoC that's validating hardware choices, the reasoning matters: is it a wiring-length constraint, a component default, or a legacy protocol choice? If someone later uses this PRD to procure additional hardware they could misconfigure it. *Fix:* Add a one-sentence rationale in FR-2.3 or the protocol section (e.g., "chosen for compatibility with long cable runs in the barn conversion").

- **low** FR-9.3 acceptance criterion depends on an open question (OQ-6) but is not marked as tentative — the 60-second window is stated as a hard requirement even though the first-heartbeat timing is unknown. *Fix:* Mark FR-9.3 as "TBD pending OQ-6 resolution" or give a conservative upper bound (e.g., ≤ 60 s from power-on, or ≤ 90 s if first heartbeat fires at t=30 s).

---

## 2. Substance over theater — strong

No persona theater (there are no personas — correct for a single-operator hardware PoC). No vision theater. NFRs are product-specific and non-trivial: NFR-2 (lambda size guard with blocking-defect label), NFR-4 (esp-idf framework mandate with explicit incompatibility reason), NFR-5 (node isolation requirements enumerated), NFR-7 (termination verification as a pre-power-on gate). These are not boilerplate; each one names the exact failure mode it prevents.

The BOM section is unusually thorough for a PRD — that is appropriate here because hardware selection is itself a design decision under validation.

No findings at this level.

---

## 3. Strategic coherence — strong

The thesis is explicit in Goal 5: identify issues before committing to large-scale hardware procurement. Every requirement is traceable to that thesis. The PoC scope (2 nodes, 1 gateway, bench-only, no automations, no OTA, no output commands) is coherent with risk-reduction intent — nothing extra has crept in, nothing necessary has been omitted.

The Deployment Procedure section is an unusual addition for a PRD and works well here: it operationalizes the thesis by sequencing "resolve hardware unknowns first, then compile, then assemble, then validate."

No findings at this level.

---

## 4. Done-ness clarity — adequate

FRs are generally testable and unambiguous. Binary conditions (compile succeeds/fails, event appears in HA Developer Tools, correct field values) dominate. The protocol tables give exact byte offsets, field names, and value enumerations — an engineer cannot misread them.

### Findings

- **high** FR-9 acceptance criteria define the happy path only — no failure threshold is specified (§ FR-9.1–FR-9.4). The PoC passes if every button event reaches HA, but what is the minimum acceptable success rate? For a PoC bench test with 5 event types × 2 nodes = 10 test cases, a single missed frame could be a fluke or a systemic bug. Without a defined acceptance threshold the pass/fail decision is left to judgment at test time. *Fix:* Add FR-9.5: "All 10 event-type/node combinations SHALL be observed in HA within a single uninterrupted test session. A missed event SHALL be retried once; persistent failure is a blocking defect."

- **high** FR-9 does not include a CAN bus health check (§ FR-9, general) — there is no acceptance criterion that verifies the MCP2515 and TWAI controllers report zero error frames during the test. An event could appear in HA via a single successful retry while the bus is in a degraded state. *Fix:* Add FR-9.6: "ESPHome logs on both nodes and the gateway SHALL show zero CAN error-frame or bus-off events during the validation session."

- **medium** FR-3.2 requires error flags to "reflect CAN TX failure and bus-off conditions" but does not specify how the node detects these conditions or what ESPHome API surfaces them (§ FR-3.2). This is under-specified for implementation. *Fix:* Reference the specific ESPHome MCP2515 callback or error register the lambda SHALL inspect, or mark as "implementation-defined, verify in testing."

- **medium** FR-6.4 (staging values into ESPHome globals before HA event blocks) is stated as a requirement but the mechanism is not validated anywhere in FR-9 (§ FR-6.4). If the globals approach doesn't work as expected in ESPHome, there is no acceptance criterion that would catch it independently of the end-to-end event test. *Fix:* Add a compile-time note that this pattern should be validated in OQ-4's minimal test YAML before integration.

---

## 5. Scope honesty — strong

Non-Goals section is explicit and does real work: CAT_OUTPUT, health dashboard, multi-gateway, physical installation, OTA, and production automations are all named. This is not a generic "out of scope" list — each item is something that could reasonably be assumed in scope given the broader project.

Assumptions are tagged inline and carry meaningful content (not just "TBD"). The OQ table distinguishes blocking from non-blocking with specific FR citations — a model practice.

### Findings

- **low** The note about the gateway board differing from "prior design notes" (§ Gateway section) references an external document ("ESP32-S3-POE-ETH-8DI-8DO referenced in prior design notes") that is not linked or identified. If there is a prior design document with conflicting specs, a reader who finds it could be confused. *Fix:* Either name and link the prior document, or replace "prior design notes" with "earlier architecture exploration" if the document is informal/internal only.

---

## 6. Downstream usability — adequate

For a solo hardware PoC with no UX, no separate architecture document, and no story backlog yet, downstream traceability requirements are light. The FR numbering is contiguous and unique (FR-1 through FR-9, with sub-items). The OQ table uses a stable ID scheme.

### Findings

- **medium** There is no Glossary (§ general). Domain nouns are used consistently within this document, but terms like "node," "gateway," "room," "board," "node_id," and "room ID" have specific technical meanings that differ from their everyday use. If this PRD feeds story creation or architecture docs, the absence of a glossary will cause drift. For a PoC-only document this is acceptable, but worth noting. *Fix:* Add a one-table glossary if/when this PRD is promoted to a production-phase spec; defer for now since Non-Goals explicitly excludes production-phase scope.

- **low** `[ASSUMPTION]` tags appear inline throughout the document but are not collected into an Assumptions Index at the end. Inline tags are present and navigable, but an index would allow quick review before sign-off. *Fix:* Add an Assumptions Index section listing all six inline assumptions (INT pin GPIO20, SPI 16 MHz oscillator, 2 buttons per node, WiFi credentials provided at build time, HA on same network, first heartbeat at t=0) with their FR dependencies.

---

## 7. Shape fit — strong

This PRD is written as a capability/technical spec, which is exactly the right shape for a single-operator hardware PoC. No personas, no user journeys, no conversion metrics — appropriate omissions, not oversights. The BOM, protocol tables, pin mappings, and deployment procedure are all load-bearing content that belongs in this document for this product type.

The rubric criterion "hobby / solo → rigor light, substance bar still applies" fits. The document meets the substance bar: protocol is fully specified, requirements are testable, risks are named with mitigations. Rigor is calibrated appropriately — not under-specified, not bureaucratically over-specified.

No findings at this level.

---

## Mechanical notes

- **ID continuity:** FR-1 through FR-9 contiguous. OQ-1 through OQ-6 contiguous. No gaps or duplicates found.
- **Glossary drift:** Minor — "room ID" (protocol section) vs. "room" (FR-6.1 event field) vs. `room` (YAML field name). These refer to the same value but are named differently depending on context. Low risk for this document; would matter for downstream story creation.
- **Assumptions Index:** Six inline `[ASSUMPTION]` tags present; no index section. See Downstream usability finding above.
- **Cross-references:** FR-9 references FR-9.1 through FR-9.4 in the Deployment Procedure without issue. OQ table cites FR numbers correctly (OQ-1 → FR-1, FR-8; OQ-2 → FR-2; OQ-4 → FR-5, FR-6). OQ-5 cites FR-9 — correct.
- **Required sections:** Overview, Goals, Non-Goals, BOM, Architecture, Protocol, FRs, NFRs, Open Questions, Deployment Procedure, Risks — all present and appropriate for the stakes and product type.
