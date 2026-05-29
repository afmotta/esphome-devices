# Reconciliation: canbus-smart-home-reference.md vs. prd.md

**Input:** `canbus-smart-home-reference.md`
**PRD:** `prd-canbus-2026-05-29/prd.md`
**Date:** 2026-05-29

---

## 1. Factual Contradictions

### C1 — Gateway board identity (HIGH SEVERITY)

The input document specifies the gateway board as:

> **Waveshare ESP32-S3-POE-ETH-8DI-8DO**

Key characteristics from the input:
- W5500 Ethernet chip (SPI-based, PoE)
- Native TWAI CAN TX = GPIO2, CAN RX = GPIO3
- PCA9554 I2C I/O expander at 0x20
- 8 optocoupler-isolated digital inputs (GPIO4–11)
- 8 digital outputs via PCA9554
- Buzzer on GPIO46
- WS2812 RGB LED on GPIO38

The PRD specifies the gateway board as:

> **Waveshare ESP32-S3-RS485-CAN**

Key characteristics from the PRD:
- WiFi only (no Ethernet)
- Native TWAI CAN TX = GPIO15, CAN RX = GPIO16
- No PCA9554, no discrete DI/DO, no buzzer, no RGB LED
- Power: 7–36 V DC or USB-C 5 V

The PRD acknowledges this divergence explicitly in a callout note. This is the most critical contradiction: the CAN GPIO pins are completely different (GPIO2/3 vs. GPIO15/16), and the connectivity model changes from PoE Ethernet to WiFi. If the wrong GPIO mapping ends up in `gateway.yaml`, the TWAI controller will not initialize correctly.

**Action required:** Confirm which physical board will be used in the PoC bench. If the RS485-CAN board is the actual bench board, the input document should be updated to reflect it (or a revision note added). The PRD GPIO mapping (GPIO15 TX, GPIO16 RX) should be verified against the RS485-CAN schematic.

---

### C2 — Gateway connectivity: Ethernet vs. WiFi

Directly follows from C1. The input document describes the gateway reaching HA over **PoE Ethernet** (ESPHome native API via the W5500 chip). The PRD describes **WiFi** connectivity. These are mutually exclusive in ESPHome config (`ethernet:` block vs. `wifi:` block). FR-7.1 and NFR-4 in the PRD correctly reflect the WiFi assumption for the RS485-CAN board, but they contradict the input document's architecture section.

---

## 2. Requirements / Constraints in the Input Not Reflected in the PRD

### G1 — CANBed RP2040 board assembly requirement (kit form)

The input notes:

> "The board ships as a kit with unsoldered through-hole components (terminal blocks, DB9 connector, pin headers, 120 Ω termination switch). These must be soldered before use."

The PRD's Deployment Procedure and hardware BOM make no mention of this. For a PoC, skipping this detail could mean someone purchases the boards and tries to use them immediately, only to discover they need soldering time, tools, and a soldering iron. This is a real physical dependency that should appear as a prerequisite in the Deployment Procedure (step 0 or a pre-requisite checklist item).

**Suggested addition:** A note in the Hardware BOM or Deployment Procedure pre-steps: "CANBed RP2040 boards arrive as kits; solder terminal blocks, pin headers, and 120 Ω termination switch before use."

---

### G2 — The "why" of room/board in the payload (ESPHome `on_frame` CAN ID limitation)

The input explains a concrete ESPHome design constraint:

> "ESPHome's `on_frame` CAN trigger provides the data bytes (`x`) but does not cleanly expose the received CAN ID as a lambda variable. When the gateway uses mask-based filtering to match all button events at once, it cannot decode which node sent the message from the CAN ID alone."

This is the technical rationale for why room and board IDs are embedded in the payload (rather than derived from the CAN ID, which would be the natural approach). The PRD documents *what* the payload contains but never states *why* room/board are in the payload. If a developer reads the PRD alone, they might try to extract identity from the CAN ID in a lambda, hit the ESPHome limitation, and waste time debugging it.

**Suggested addition:** A note under the CAN Protocol section or FR-6 explaining that the CAN ID is intentionally not used as the sole identity source because ESPHome `on_frame` lambdas do not expose the received CAN ID cleanly, and that payload bytes 4–5 (room, board) are the canonical source of node identity at the gateway.

---

### G3 — `canbus_protocol.h` as single source of truth: drift prevention rationale

The input explicitly describes the purpose of the shared C++ header:

> "Both nodes and gateway include the same header, so the protocol definition cannot drift."

The PRD requires the header in FR-4.1/4.2 and NFR-3, but only frames it as a style/quality rule ("no magic numbers"). The input frames it as a correctness constraint: with 100+ nodes over a multi-year deployment, any drift between node and gateway constants (e.g., a byte index changing in one but not the other) would cause silent misinterpretation of frames. This is a safety argument, not just a code style preference.

**Suggested addition:** NFR-3 should add a sentence: "This constraint prevents silent protocol drift between node and gateway firmware over the life of the deployment."

---

### G4 — Multi-click ordering rationale: shadow prevention

The input explains:

> "Multi-click patterns are ordered longest-first (triple → double → single → long → extra long) so the longest sequence matches before shorter ones."

FR-1.2 in the PRD correctly mandates this ordering but does not explain why. Without the rationale, a developer making adjustments might reorder the patterns and introduce a subtle bug where a triple-click is always captured as three separate single-clicks. For an `on_multi_click` configuration that cannot be changed at runtime, this is a hard-to-diagnose field defect.

**Suggested addition:** FR-1.2 should add a brief inline rationale: "Ordering longest-first prevents shorter patterns from being matched before longer sequences complete."

This is already partially present in the PRD ("to prevent shorter patterns from shadowing longer ones") so this is a minor gap — the language exists but could be slightly clearer about the mechanism.

---

### G5 — HA services exposed by the gateway (canbus_send_output, canbus_send_config)

The input documents two HA services that the gateway exposes:

- `esphome.canbus_gateway_canbus_send_output` (node_id, subtype, param1, param2)
- `esphome.canbus_gateway_canbus_send_config` (node_id, key, value)

The PRD explicitly defers CAT_OUTPUT (gateway → node commands), and these services exist to support that category. The question is whether the *service stubs* should exist in the PoC gateway firmware even if they do nothing in phase 1. The input implies they are already wired up as part of the protocol infrastructure ("the CAN config message infrastructure is wired up in the protocol"). If the PoC gateway.yaml will include these service definitions (even as no-ops), the PRD should at minimum acknowledge them as present scaffolding. If the PoC gateway.yaml will not include them at all, the PRD should say so explicitly.

**Current PRD status:** Non-Goals defers CAT_OUTPUT but does not say whether the service stubs will be present. This creates ambiguity for the developer implementing gateway.yaml.

**Suggested addition:** Clarify in Non-Goals whether the CAT_OUTPUT service stubs (`canbus_send_output`, `canbus_send_config`) will be present as scaffolding in the PoC gateway.yaml or completely absent.

---

### G6 — Node ID reservation convention

The input describes a convention for assigning node IDs:

> "You can reserve ranges by convention (e.g. 0–49 ground floor, 50–99 first floor)."

This is not a hard protocol constraint but is a deployment design decision that affects how the PoC `nodes.csv` is populated and whether the initial assignments will scale cleanly to the 100+ node production system. The PRD (FR-8.3) says the PoC will have 2 nodes with distinct IDs but gives no guidance on which IDs to use or whether to start establishing the floor-based convention now.

**Suggested addition:** FR-8.3 or a note in the Deployment Procedure should indicate whether the PoC nodes should begin from a floor-aligned range (e.g., node_id 0 and 1 for ground floor), so the production convention is established from day one rather than needing a reassignment later.

---

### G7 — Example HA automation (missing from PRD)

The input provides a concrete example HA automation:

```yaml
automation:
  - alias: "Kitchen light toggle"
    trigger:
      - platform: event
        event_type: esphome.canbus_button
        event_data:
          room: "1"
          board: "0"
          button: "0"
          event: "click"
    action:
      - service: light.toggle
        target:
          entity_id: light.kitchen_main
```

The PRD's FR-9 acceptance criteria relies on the tester being able to correctly subscribe to and interpret HA events in Developer Tools. Including a reference automation (even in a commented-out or informational block) in the PRD would help the tester verify that the event schema produced by the gateway is actually usable in a real automation — which is the whole point of the system. This is low-priority but is a qualitative completeness item.

---

## 3. Qualitative Intent / Philosophy Missing from the PRD

### Q1 — "Dumb nodes, smart gateway" as an explicit design principle

The input's architecture section opens with a named design principle:

> **Design principle: dumb nodes, smart gateway**
> - Nodes are frozen firmware. They detect button clicks locally and send self-describing CAN frames. They do not know what any button "does."
> - The gateway is updatable. It bridges CAN bus to Home Assistant via the ESPHome API.
> - Home Assistant owns all logic.

The PRD's architecture section describes *how* this works but never names or frames it as a deliberate design philosophy. For a PoC PRD that is also meant to communicate intent to future collaborators or serve as a reference, this principle is important context: it explains why nodes are intentionally kept simple (not a limitation, but a choice), why HA automations are the locus of all behavior, and why gateway firmware can be changed without touching nodes.

**Suggested addition:** A brief "Design Principles" subsection under System Architecture naming "Dumb nodes, smart gateway" explicitly, with a one-sentence explanation of each of the three sub-principles.

---

### Q2 — The operational constraint driving the design ("walled in, hard to reach")

The input explains *why* the dumb-node philosophy exists:

> "The button boards are walled in and hard to reach after installation. The RP2040 boards have no WiFi, so no OTA updates."

This constraint is mentioned in the PoC Overview ("RP2040 nodes...no OTA") and in Non-Goals ("OTA update capability on nodes") but the *reason* — that nodes are physically inaccessible once installed — is never stated in the PRD. This matters because it frames why every design decision that reduces future need to touch node firmware is a quality attribute, not just a preference. A reader who doesn't know the nodes are walled-in might question why the protocol is over-engineered with room/board in the payload rather than just using the CAN ID.

**Suggested addition:** One sentence in the Overview or System Architecture: "Nodes are permanently installed behind walls after commissioning and cannot be reflashed; the dumb-node architecture is a physical necessity, not just a preference."

---

### Q3 — "Not yet compiled/tested" as an explicit risk acknowledgment

The input is candid:

> "Not yet compiled/tested. The YAML and C++ have been designed but not compiled against ESPHome. The `on_frame` + `can_id_mask` + `homeassistant.event` chain in the gateway is the most likely area for issues."

The PRD captures this in Risks (the `on_frame` + `homeassistant.event` chain is "High" likelihood/impact) and in Open Questions (OQ-4). However, the PRD does not explicitly state that *nothing* in the existing YAML/C++ codebase has been compiled yet. If a developer starts the PoC believing some baseline is already validated, they may waste time before realizing they are starting from a fully unvalidated design.

**Suggested addition:** A sentence in the Overview or a pre-condition note: "As of PoC kickoff, no ESPHome firmware from this project has been compiled or flashed. The entire YAML and C++ design is untested."

---

## Summary of Gaps by Priority

| Priority | ID | Type | Short Description |
|----------|-----|------|-------------------|
| Critical | C1 | Contradiction | Gateway board identity differs: input=POE-ETH-8DI-8DO (GPIO2/3), PRD=RS485-CAN (GPIO15/16) |
| Critical | C2 | Contradiction | Gateway connectivity: input=PoE Ethernet, PRD=WiFi |
| High | G2 | Missing rationale | ESPHome `on_frame` CAN ID limitation not documented; developers may try to use CAN ID in lambdas |
| High | Q2 | Missing philosophy | Reason nodes are dumb (physically inaccessible after installation) not stated in PRD |
| High | Q3 | Missing context | No explicit statement that the entire codebase is uncompiled/untested as of PoC start |
| Medium | G1 | Missing requirement | CANBed RP2040 boards require soldering before use; not mentioned in Deployment Procedure |
| Medium | G5 | Ambiguous scope | Whether CAT_OUTPUT service stubs will be present in PoC gateway.yaml is unresolved |
| Medium | Q1 | Missing philosophy | "Dumb nodes, smart gateway" design principle not named or framed in PRD |
| Low | G3 | Missing rationale | NFR-3 protocol header rule lacks the drift-prevention safety argument |
| Low | G4 | Missing rationale | FR-1.2 multi-click ordering mandate lacks a clear inline explanation of shadow mechanism |
| Low | G6 | Missing convention | Node ID floor-range reservation convention not carried into PoC FR-8.3 |
| Low | G7 | Missing aid | Example HA automation not included in PRD (useful for validating event schema end-to-end) |
