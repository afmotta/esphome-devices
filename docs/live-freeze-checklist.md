# LIVE-Freeze Checklist

> **Status:** Draft gate — not yet satisfied. Owner sign-off: _pending_.
> **Source:** ADR-0008 §5 (open item 5). This file *is* the tracked artifact that
> ADR-0008 says must replace "freeze is a date" with "freeze is a checklist."

## Why this gate exists

Declaring the project **LIVE** is Alberto's explicit call (see `project-context.md`
versioning policy). After LIVE, ADR-0008 makes node/bridge firmware changes deliberately
expensive: there is no CAN bootloader and no OTA on nodes/bridges, so a fielded change is a
**physical reflash campaign** (see `docs/reflash-campaign-runbook.md`). Because the cost of
being wrong rises sharply at LIVE, the frozen surface must have *soaked end-to-end* first.

Do **not** declare LIVE on the PoC surface alone. Every item below must be checked and
signed off.

## Freeze checklist

- [ ] **Sensor kit deployed and reporting** — the ADR-0006 `CAT_SENSOR` kit is running on
      **at least one production-form node** and reporting measurements end-to-end (node →
      bus → gateway → Home Assistant), not just on the bench.
- [ ] **`ha_ready` arbitration tuned with real values** — ADR-0003 arbitration is configured
      with **real timeout values** (not placeholders) and a **real manifest hash**, verified
      against live Home Assistant latency. Record the chosen values:
  - `ack_timeout_ms`: _________
  - manifest hash source / value: _________
- [ ] **At least one bridge soak-tested in line** — an ADR-0005 segment bridge has passed its
      soak test on real hardware (its open item 5): burst-rate frame integrity, and
      watchdog/brownout/never-babble behavior observed under induced faults.
- [ ] **Reflash-campaign runbook written and bench-timed** — `docs/reflash-campaign-runbook.md`
      is complete (no stub sections) and its per-board / fleet timings have been **measured on
      the bench**, validating the ADR-0008 §2 cost estimate before we rely on it.
- [ ] **Per-release firmware artifacts archived** — compiled UF2/bin images for every fielded
      board are archived per release **alongside the pinned ESPHome version**, so a campaign
      years later does not depend on rebuilding a bit-rotted toolchain. Record where they live
      and what metadata ties them to registry state (ADR-0008 open item 3): _________
- [ ] **USB service-access verified at install** — every fielded node and bridge was mounted
      with its USB port reachable without rewiring (ADR-0008 §3), confirmed during
      commissioning.

## Sign-off

LIVE is declared only when every box above is checked.

- Declared LIVE by: _________________________  (Alberto)
- Date: _________________________
- Commit / release tag at freeze: _________________________

_Once signed, a post-LIVE breaking payload change requires a `PROTO_V1` bump; fielded nodes
need a physical reflash campaign (`docs/reflash-campaign-runbook.md`) only if they must adopt
the change — otherwise the controller keeps decoding their existing payload version
(ADR-0008 §1)._
