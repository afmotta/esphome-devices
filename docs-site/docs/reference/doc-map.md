# Document Map

This site isn't the only documentation in the project's code repository. If you (or
someone helping you) ever open the repository directly instead of browsing this site,
it helps to know which files are the current authority for what, and which ones are
old and should be ignored. This page is that map.

## The three layers of documentation

There are three different kinds of documents in the repository, written for three
different purposes:

1. **This site (`docs-site/`) — the practical, day-to-day guide.**
   Written for whoever is actually doing the work: a technician, a family member, or
   the owner years from now trying to remember how something works. If you want to
   know *how to do something* — replace a board, add a room, diagnose a problem — start
   here.

2. **`CLAUDE.md` files (one at the repository root, and one inside each subsystem
   folder: `canbus/CLAUDE.md`, `lighting/CLAUDE.md`, `climate/CLAUDE.md`) — deeper
   technical/architectural references.**
   These were written primarily to brief an AI coding assistant working on the code,
   but they double as the most detailed technical reference in the repository: entity
   naming conventions, full Modbus register maps, PID tuning ranges, file layout
   rules. If this site references a specific value or convention and you want the full
   underlying detail, the relevant `CLAUDE.md` is usually where it lives. The root
   file is a map of the whole repository; each subsystem's own file is the actual
   rulebook for that subsystem.

3. **ADRs (Architecture Decision Records), under
   `_bmad-output/planning-artifacts/adrs/` and
   `canbus/_bmad-output/planning-artifacts/adrs/`) — the record of *why*.**
   Each ADR documents one significant decision (e.g. "which controller hardware to
   standardize on"), the alternatives that were considered, and the trade-offs
   accepted. Read an ADR when you want to understand *why* something was built the way
   it was, not just what it currently does. This site and the `CLAUDE.md` files
   describe the current state; ADRs explain the reasoning behind it and are not kept
   in sync with later changes the way the other two are — a decision can be amended by
   a *later* ADR without the original file being rewritten.

If these three ever seem to disagree, treat it in this order: this site and the
relevant `CLAUDE.md` describe the *current* system; an ADR explains *why* it got that
way and may describe an earlier or since-amended version of the decision.

## Historical documents — ignore these for current procedures

The repository's `docs/` folder (not this site's `docs-site/`) contains some
documents that describe an earlier, retired generation of hardware (Kincony KC868-A6 /
A16 boards, a master/slave controller topology, and Modbus-based room sensors). That
generation was fully replaced by the current LilyGO T-Connect Pro hardware and
single-master design. These files are kept only as historical record — **do not follow
them for current work**:

| File | What it covers | Superseded by |
|---|---|---|
| `docs/deployment-guide.md` | Deploying the old A6/A16 master/slave topology | `docs/climate-deployment-runbook.md` |
| `docs/sensor-technology-selection.md` | The original (later reversed) decision to use Modbus room sensors | Room sensing over CAN bus / Home Assistant, `climate/room_sensors.yaml` |
| `docs/0-10v-adapter-setup-guide.md` | Setting up a generic AliExpress 0–10V Modbus adapter | The Waveshare Modbus RTU Analog Output 8CH (B) board — see [Hardware & Address Table](hardware-table.md) |
| `docs/modbus-register-map.md` | The full register map for the old KC868-A6-based master/slave system | The current, much smaller Modbus footprint described in [Hardware & Address Table](hardware-table.md) |

Most of these files carry their own "historical document" notice at the top if you do
open them directly — that notice is accurate and you should believe it. The other
files under `docs/` (deployment runbook, weather-compensation notes, wiring guides,
window-sensor mapping, and so on) are current and not part of this list.

## A minor footnote: orphaned board files

The repository's `boards/` folder holds hardware definitions for every board the
project has ever used. A handful of them are leftovers from the retired hardware
generation above and are no longer referenced by anything: files named `a6*.yaml`,
`a16*.yaml`, `base.yaml`, and `wifi.yaml`, plus a set of unused Waveshare-S3 variants
(`waveshare-s3.yaml`, `waveshare-s3-ethernet.yaml`, `waveshare-s3-wifi.yaml` — as
opposed to `waveshare-s3-rs485-can.yaml`, which **is** the one actually used, by the
CAN bus health monitor). If you're browsing that folder and wonder why a file exists
that nothing seems to use, this is why — it's not a mistake you need to fix, just old
code that was never deleted.

## Related

- [Confidence Ledger](confidence-ledger.md) — tracks which claims across this whole
  site are still unverified, separately from which *documents* are current or
  historical (this page's concern).
- [Hardware & Address Table](hardware-table.md) — the current hardware reference this
  page's "historical documents" section points away from.
- [Glossary](glossary.md) — if a term in one of these documents (Italian or
  technical) is unfamiliar.
