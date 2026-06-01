---
status: done
epic: 1
story: 2
story_key: 1-2-resolve-hardware-open-questions
baseline_commit: a092dafc3ac9d4cd60c0d16e0653402210ef7bac
---

# Story 1.2: Resolve hardware open questions from board documentation

Status: review

## Story

As a developer,
I want the hardware pin assignments and oscillator frequency confirmed from official board documentation,
so that firmware can be written with verified values and the risk of silent hardware misconfiguration is eliminated before any compile.

## Acceptance Criteria

1. OQ-1 resolved: the exact GPIO numbers for all user-facing button pins on the CANBed RP2040 are documented in `firmware/README.md` under "Hardware Verification → OQ-1" with the source reference (document name and section or URL)
2. OQ-2 resolved: the MCP2515 INT pin number is confirmed and documented in `firmware/README.md` under "Hardware Verification → OQ-2" with the source reference
3. OQ-3 resolved: the oscillator frequency (expected: 16 MHz) is confirmed and documented in `firmware/README.md` under "Hardware Verification → OQ-3" with the source reference
4. All three resolved values are recorded before any firmware file is compiled

## Tasks / Subtasks

- [x] Task 1: Research CANBed RP2040 board documentation (AC: 1, 2, 3)
  - [x] Locate the official Longan Labs CANBed RP2040 schematic and pinout diagram
  - [x] Identify user-facing button GPIO numbers (OQ-1): which RP2040 GPIO pins are connected to physical push-buttons on the board?
  - [x] Identify MCP2515 INT pin number (OQ-2): which RP2040 GPIO pin is connected to MCP2515 ~INT?
  - [x] Confirm MCP2515 oscillator frequency (OQ-3): is it 16 MHz as assumed?
  - [x] Note the source URL or document name for each finding
- [x] Task 2: Document findings in `firmware/README.md` (AC: 1, 2, 3, 4)
  - [x] Fill in OQ-1 section: GPIO number(s), status "Confirmed", source reference
  - [x] Fill in OQ-2 section: INT pin GPIO number, status "Confirmed", source reference
  - [x] Fill in OQ-3 section: oscillator frequency, status "Confirmed", source reference

### Review Findings

- [ ] [Review][Decision] OQ-1 GPIO count mismatch — README and completion notes both say "8 digital I/O pins on J1" but enumerate exactly 6 (GPIO20–GPIO25). Verify: does the header expose 6 or 8 user-accessible GPIO pins? Correct the count or add the missing 2 GPIOs. (AC1: "exact GPIO numbers for all user-facing button pins") [`firmware/README.md:OQ-1`]
- [ ] [Review][Decision] OQ-1 button polarity undocumented source — "active low, internal pull-up" is stated as fact in OQ-1 Value without a schematic source citation. Confirm whether this was directly read from the schematic (e.g. no external pull-ups present) or is an assumption; update the source line accordingly. [`firmware/README.md:OQ-1`]
- [ ] [Review][Patch] project-context.md hardware verification warnings are stale — two entries still describe GPIO20 (INT) and button GPIOs as unconfirmed open questions; these are now resolved and the entries are misleading to future agents running Stories 1.4 and 2.1. [`_bmad-output/project-context.md`]
- [x] [Review][Patch] Backtick formatting regression in Task 2 — already correct (backticks present) — resolved
- [x] [Review][Defer] SPI pin corrections (SCK=GPIO2, MOSI=GPIO3, MISO=GPIO4) documented in README table but not explicitly assigned to Stories 1.4/2.1 subtasks — deferred, pre-existing
- [x] [Review][Defer] Source URLs point to main branch of CANBED_RP2040_V11_EAGLE repo, not pinned to a commit SHA — reproducibility concern — deferred, pre-existing
- [x] [Review][Defer] `can_clock: "16MHZ"` capitalization not verified against ESPHome case sensitivity — downstream concern for Story 2.1 — deferred, pre-existing
- [x] [Review][Defer] Existing node YAMLs may still contain `can_int_pin: GPIO20` (wrong value) — addressed in Stories 1.4 and 2.1 — deferred, pre-existing

## Dev Notes

### Context: Why This Story Exists

The CANBed RP2040 has a fixed hardware design — incorrect pin assignments cannot be corrected after a node is installed in a wall (no OTA). Three specific hardware questions must be confirmed from documentation before any firmware is written:

- **OQ-1 (Button GPIOs):** Which GPIO pins are user-accessible as push-buttons on the CANBed RP2040? The existing generator script (`firmware/generate_nodes.py`) uses GPIOs 2,3,4,5 as placeholder defaults. These need to be confirmed.
- **OQ-2 (MCP2515 INT pin):** The MCP2515 CAN controller has an interrupt pin (~INT) that signals incoming frames. The existing code assumes GPIO20. **If this is wrong, MCP2515 silently falls back to polling mode, which will miss frames under button burst conditions at 125 kbps.** This is the highest-risk open question.
- **OQ-3 (Oscillator frequency):** The MCP2515 clock rate must be declared in the ESPHome YAML (`clock: 16MHZ`). The existing code assumes 16 MHz. Confirm from the board schematic.

### What to Research

**Primary source:** Longan Labs CANBed RP2040 official product page and schematic.
- Product page: search for "Longan Labs CANBed RP2040"
- GitHub: Longan Labs maintains a GitHub org (longan-labs) with board schematics
- Wiki: wiki.longan-labs.cc

**What the existing code assumes (to confirm or correct):**
```yaml
# From generate_nodes.py template (current assumptions):
can_cs_pin: "GPIO9"      # SPI CS for MCP2515
can_clk_pin: "GPIO18"    # SPI SCK
can_mosi_pin: "GPIO19"   # SPI MOSI
can_miso_pin: "GPIO16"   # SPI MISO (also used as CAN MISO — shared SPI bus)
can_int_pin: "GPIO20"    # MCP2515 ~INT ← OQ-2: confirm this
can_clock: "16MHZ"       # MCP2515 oscillator ← OQ-3: confirm this
# Button GPIOs used in nodes.csv example: 2, 3, 4, 5 ← OQ-1: confirm these
```

**What to look for in the schematic:**
- MCP2515 ~INT pin → which RP2040 GPIO
- Crystal/oscillator connected to MCP2515 → value in MHz
- User-facing tactile switches → which RP2040 GPIOs, pull-up or pull-down, active high or active low

### Where to Record Results

File: `firmware/README.md` (created in Story 1.1). Update each OQ section:

```markdown
### OQ-1: Button GPIO numbers (CANBed RP2040)

**Status:** Confirmed  
**Value:** GPIO <X>, GPIO <Y> (active low, internal pull-up required)
**Source:** <URL or document name, section>

### OQ-2: MCP2515 INT pin (CANBed RP2040)

**Status:** Confirmed  
**Value:** GPIO <N>  
**Source:** <URL or document name, section>

### OQ-3: Oscillator frequency (MCP2515 on CANBed RP2040)

**Status:** Confirmed  
**Value:** <X> MHz  
**Source:** <URL or document name, section>
```

### If Documentation is Unavailable or Ambiguous

If the Longan Labs schematic cannot be located or is ambiguous:
1. Mark the OQ status as "Assumed" (not "Confirmed") with a note explaining what was searched
2. Use the existing code's assumed values as the working assumption
3. Document the risk: an incorrect INT pin means MCP2515 polling mode (missed frames under burst conditions)
4. The story is still complete — resolution with a documented assumption is acceptable when documentation is inaccessible

### Downstream Impact of These Values

The confirmed values from this story will be used in:
- **Story 1.4:** `firmware/nodes.csv` gpio_list for nodes 100 and 101 (OQ-1)
- **Story 2.1:** `firmware/common/base_node.yaml` SPI and MCP2515 configuration (OQ-2, OQ-3)
- **Story 1.4:** `firmware/generate_nodes.py` template for `can_int_pin` and `can_clock` defaults (OQ-2, OQ-3)

### Testing / Validation

This story produces documentation only (README.md updates). There is no compilable artifact. Completion is verified by:
1. `firmware/README.md` OQ-1, OQ-2, OQ-3 sections are filled in with status "Confirmed" or "Assumed"
2. Each section cites a source reference
3. The values are internally consistent (e.g., INT pin is a valid RP2040 GPIO number)

### References

- [Source: architecture.md#Technical Constraints & Dependencies] — OQ-1/OQ-2/OQ-3 description, and the consequence of wrong INT pin
- [Source: epics.md#Story 1.2] — Acceptance criteria
- [Source: architecture.md#Gap Analysis Results] — "Hardware open questions blocking compile"

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Fetched official docs page: https://docs.longan-labs.cc/1030018/
- Fetched V1.1 Eagle schematic: https://raw.githubusercontent.com/Longan-Labs/CANBED_RP2040_V11_EAGLE/main/CANBed2040_V1.1.sch
- Confirmed all three OQ values directly from schematic net connections and part values.

### Completion Notes List

- ✅ OQ-1 (Button GPIOs): Confirmed GPIO20–GPIO27 are the 8 digital I/O pins on the 9×2 header (J1), no external pull-ups. GPIO2/3/4 are SPI SCK/MOSI/MISO (used by MCP2515) — generate_nodes.py defaults are wrong and need correction in Story 1.4.
- ✅ OQ-2 (INT pin): Confirmed GPIO11. The existing template assumption of GPIO20 is wrong. Critical finding: incorrect INT pin would cause polling fallback and missed CAN frames at burst load.
- ✅ OQ-3 (Oscillator): Confirmed 16 MHz. Existing assumption is correct.
- ℹ️ Bonus finding: SPI pins GPIO2/3/4 also differ from generate_nodes.py template (GPIO18/19/16). Full correction table added to firmware/README.md for Stories 1.4 and 2.1.

### File List

- firmware/README.md

### Change Log

- 2026-06-01: Resolved OQ-1 (Button GPIOs: GPIO20–25), OQ-2 (INT: GPIO11), OQ-3 (Oscillator: 16 MHz) from CANBed RP2040 V1.1 Eagle schematic. Documented in firmware/README.md with source references and correction warnings for Stories 1.4 and 2.1.
