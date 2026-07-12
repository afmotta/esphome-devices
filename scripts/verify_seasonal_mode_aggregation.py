#!/usr/bin/env python3
"""Verify seasonal-mode heat/cool demand aggregates cover all HVAC PID diagnostics."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOMS_DIR = ROOT / "hvac" / "rooms"
CLIMATE_CONTROL = ROOT / "devices" / "climate-control.yaml"

ROOM_SLUG_RE = re.compile(r'room_slug:\s*["\']?([A-Za-z0-9_]+)["\']?')
ID_REF_RE = re.compile(r'id\(([A-Za-z0-9_]+_pid_is_(?:heating|cooling))\)')

HEAT_ONLY_MARKERS = (
    "vesta/packages/components/heat_only_radiant.yaml",
    "components/heat_only_radiant.yaml",
    "file: ../../../vesta/packages/components/heat_only_radiant.yaml",
)
RADIANT_MARKERS = (
    "vesta/packages/components/radiant.yaml",
    "components/radiant.yaml",
    "file: ../../../vesta/packages/components/radiant.yaml",
)
FANCOIL_MARKERS = (
    "vesta/packages/components/fancoil.yaml",
    "components/fancoil.yaml",
    "file: ../../../vesta/packages/components/fancoil.yaml",
)


def strip_comments(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def room_slug(text: str, path: Path) -> str | None:
    match = ROOM_SLUG_RE.search(text)
    if match:
        return match.group(1)
    if path.name.endswith(".yaml") and not path.name.endswith("-floor.yaml"):
        return path.stem
    return None


def contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def expected_pid_ids() -> tuple[set[str], set[str]]:
    expected_heat: set[str] = set()
    expected_cool: set[str] = set()

    for path in sorted(ROOMS_DIR.glob("**/*.yaml")):
        if path.name.endswith("-floor.yaml"):
            continue
        text = strip_comments(path.read_text())
        slug = room_slug(text, path)
        if not slug:
            continue

        has_heat_only_radiant = contains_any(text, HEAT_ONLY_MARKERS)
        has_radiant = contains_any(text, RADIANT_MARKERS)
        has_fancoil = contains_any(text, FANCOIL_MARKERS)

        if has_heat_only_radiant or has_radiant:
            expected_heat.add(f"{slug}_radiant_pid_is_heating")
        if has_radiant:
            expected_cool.add(f"{slug}_radiant_pid_is_cooling")
        if has_fancoil:
            expected_heat.add(f"{slug}_fancoil_pid_is_heating")
            expected_cool.add(f"{slug}_fancoil_pid_is_cooling")

    return expected_heat, expected_cool


def aggregate_block(text: str, aggregate_id: str) -> str:
    marker = f"id: !extend {aggregate_id}"
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"missing aggregate block {aggregate_id}")
    next_block = text.find("\n  - id: !extend ", start + len(marker))
    if next_block < 0:
        return text[start:]
    return text[start:next_block]


def referenced_ids(aggregate_id: str) -> set[str]:
    text = CLIMATE_CONTROL.read_text()
    block = aggregate_block(text, aggregate_id)
    return set(ID_REF_RE.findall(block))


def report_delta(title: str, values: set[str]) -> None:
    if not values:
        return
    print(title, file=sys.stderr)
    for value in sorted(values):
        print(f"  - {value}", file=sys.stderr)


def main() -> int:
    expected_heat, expected_cool = expected_pid_ids()
    actual_heat = referenced_ids("any_pid_requesting_heat")
    actual_cool = referenced_ids("any_pid_requesting_cool")

    errors = False
    for label, expected, actual in (
        ("heat", expected_heat, actual_heat),
        ("cool", expected_cool, actual_cool),
    ):
        missing = expected - actual
        extra = actual - expected
        if missing or extra:
            errors = True
            print(f"Seasonal {label} aggregate mismatch:", file=sys.stderr)
            report_delta("Missing expected PID diagnostics:", missing)
            report_delta("References without a matching room package:", extra)

    if errors:
        return 1
    print(
        "seasonal mode aggregation: heat/cool PID diagnostics match room packages "
        f"({len(expected_heat)} heat, {len(expected_cool)} cool)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
