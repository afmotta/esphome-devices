---
status: ready-for-dev
epic: 1
story: 2
story_key: 1-2-resolve-hardware-open-questions
---

# Story 1.2: Resolve hardware open questions from board documentation

Status: ready-for-dev

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

- [ ] Task 1: Research CANBed RP2040 board documentation (AC: 1, 2, 3)
  - [ ] Locate the official Longan Labs CANBed RP2040 schematic and pinout diagram
  - [ ] Identify user-facing button GPIO numbers (OQ-1): which RP2040 GPIO pins are connected to physical push-buttons on the board?
  - [ ] Identify MCP2515 INT pin number (OQ-2): which RP2040 GPIO pin is connected to MCP2515 ~INT?
  - [ ] Confirm MCP2515 oscillator frequency (OQ-3): is it 16 MHz as assumed?
  - [ ] Note the source URL or document name for each finding
- [ ] Task 2: Document findings in `firmware/README.md` (AC: 1, 2, 3, 4)
  - [ ] Fill in OQ-1 section: GPIO number(s), status "Confirmed", source reference
  - [ ] Fill in OQ-2 section: INT pin GPIO number, status "Confirmed", source reference
  - [ ] Fill in OQ-3 section: oscillator frequency, status "Confirmed", source reference

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

### Completion Notes List

### File List

### Change Log
