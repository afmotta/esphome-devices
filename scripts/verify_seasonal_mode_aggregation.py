#!/usr/bin/env python3
"""Verify seasonal-mode heat/cool demand aggregates cover all Climate PID diagnostics.

Also verifies that each floor's radiant pump-demand sum covers every radiant zone
twice over: through the PID's `_radiant_pid_is_active` and through the radiant
override's `_radiant_override_active` (a valve held open by boost or by hand has
no PID action behind it; review R-05).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOMS_DIR = ROOT / "climate" / "rooms"
CLIMATE_CONTROL = ROOT / "devices" / "climate-control.yaml"

ROOM_SLUG_RE = re.compile(r'room_slug:\s*["\']?([A-Za-z0-9_]+)["\']?')
ID_REF_RE = re.compile(r'id\(([A-Za-z0-9_]+_pid_is_(?:heating|cooling))\)')

HEAT_ONLY_MARKERS = (
    "climate/packages/components/heat_only_radiant.yaml",
    "components/heat_only_radiant.yaml",
    "file: ../../packages/components/heat_only_radiant.yaml",
)
RADIANT_MARKERS = (
    "climate/packages/components/radiant.yaml",
    "components/radiant.yaml",
    "file: ../../packages/components/radiant.yaml",
)
FANCOIL_MARKERS = (
    "climate/packages/components/fancoil.yaml",
    "components/fancoil.yaml",
    "file: ../../packages/components/fancoil.yaml",
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

    for _, slug, text in iter_rooms():
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


DEMAND_BLOCK_RE = re.compile(r"^\s+id:\s*\w*any_zone_open\b.*?(?=\n  - |\Z)", re.S | re.M)
BARE_DEMAND_REF_RE = re.compile(
    r"id\(\w+_radiant_(?:pid_is_active|override_active)\)(?!\.state)"
)


def strip_comments_keep_cpp(text: str) -> str:
    """Drop YAML comment lines and C++ // comments, keeping lambda code.

    strip_comments cuts at any `#`, which would truncate lambda bodies.
    """
    lines = (re.sub(r"\s//.*$", "", line) for line in text.splitlines())
    return "\n".join(line for line in lines if not line.lstrip().startswith(("#", "//")))


def iter_rooms(floor_dir: Path | None = None):
    """Yield (path, slug, comment-stripped text) for every room file."""
    root = floor_dir or ROOMS_DIR
    for path in sorted(root.glob("**/*.yaml")):
        if path.name.endswith("-floor.yaml"):
            continue
        text = strip_comments(path.read_text())
        slug = room_slug(text, path)
        if slug:
            yield path, slug, text


def radiant_pump_demand_errors() -> list[str]:
    """Each radiant room must appear, with both inputs, in its floor's demand sum."""
    errors: list[str] = []
    for floor_dir in sorted(p for p in ROOMS_DIR.iterdir() if p.is_dir()):
        floor_files = sorted(floor_dir.glob("*-floor.yaml"))
        if not floor_files:
            continue
        floor_text = "\n".join(strip_comments_keep_cpp(f.read_text()) for f in floor_files)
        radiant_rooms = [
            slug
            for _, slug, text in iter_rooms(floor_dir)
            if contains_any(text, HEAT_ONLY_MARKERS) or contains_any(text, RADIANT_MARKERS)
        ]
        if not radiant_rooms:
            continue
        # The radiant sum is picked by its id; a floor with a single sum (no
        # fancoil sum) uses that one.
        blocks = [m.group(0) for m in DEMAND_BLOCK_RE.finditer(floor_text)]
        radiant_blocks = [b for b in blocks if "radiant" in b.split(None, 2)[1]]
        demand = "\n".join(radiant_blocks or (blocks if len(blocks) == 1 else []))
        if not demand:
            errors.append(f"{floor_dir.name}: missing *_any_zone_open radiant demand sum")
            continue
        # `.state` is mandatory: id(binary_sensor) alone is the sensor's
        # POINTER, which is always true in an `||` chain.
        for bare in BARE_DEMAND_REF_RE.findall(demand):
            errors.append(f"{floor_dir.name}: pump demand reads {bare} without .state")
        for slug in radiant_rooms:
            for suffix in ("radiant_pid_is_active", "radiant_override_active"):
                if f"id({slug}_{suffix}).state" not in demand:
                    errors.append(f"{floor_dir.name}: pump demand is missing {slug}_{suffix}.state")
    return errors


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

    pump_errors = radiant_pump_demand_errors()
    for error in pump_errors:
        errors = True
        print(f"Radiant pump demand mismatch: {error}", file=sys.stderr)

    if errors:
        return 1
    print(
        "seasonal mode aggregation: heat/cool PID diagnostics match room packages "
        f"({len(expected_heat)} heat, {len(expected_cool)} cool)"
    )
    print("radiant pump demand: every radiant zone feeds its floor sum via PID and override")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
