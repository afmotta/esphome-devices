# canbus/archive — retired firmware, kept on disk deliberately

Nothing here is built, generated, flashed, or covered by the verification battery.
These files are parked because the hardware still exists and the design work behind
them is worth not re-deriving.

| File | Retired | Why | Revival |
| --- | --- | --- | --- |
| `bridge-t2can.yaml` | 2026-08-04, ADR-0017 §7 | Segment bridges moved to the fleet node board (CANBed RP2040 + a second MCP2515). Exactly one T-2CAN is owned — a second bridge profile is not worth the code for a single board. | Add a `bridge-t2can` entry to `PROFILES` in `canbus/tools/generate_nodes.py` pointing at a package built from this file, and give it a registry row. The `PROFILES` table was shaped to absorb this without a schema change. |

Archived files are frozen at their retirement state. If a revival happens, expect to
re-check them against the current ESPHome version first — they were last valid against
the version pinned at the date in the table above.
