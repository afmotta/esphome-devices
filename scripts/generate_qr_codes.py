#!/usr/bin/env python3
"""Generate printable QR-code PNGs for each hardware-replacement page on the
Maintenance Guide (docs-site/), so stickers can be produced for physical devices
without hand-copying URLs into a QR generator.

Usage:
    pip install qrcode[pil]
    python3 scripts/generate_qr_codes.py [--out-dir qr-codes] [--base-url URL]
"""

import argparse
from pathlib import Path

import qrcode

SITE_BASE_URL = "https://afmotta.github.io/esphome-devices"

# (output filename stem, page path under docs-site/docs, human label)
HARDWARE_PAGES = [
    ("hardware-which-device", "hardware/", "Which device died? (decision tree)"),
    ("hardware-can-node", "hardware/can-node/", "CAN Node"),
    ("hardware-bridge", "hardware/bridge/", "CAN Bridge"),
    ("hardware-health-monitor", "hardware/health-monitor/", "Health Monitor"),
    ("hardware-controller", "hardware/controller/", "Controller (T-Connect Pro)"),
    ("hardware-relay-board", "hardware/relay-board/", "Relay Board"),
    ("hardware-analog-board", "hardware/analog-board/", "Analog Output Board"),
    ("hardware-mev", "hardware/mev/", "MEV Unit"),
    ("hardware-room-sensor", "hardware/room-sensor/", "Room Sensor Board"),
]

LANGUAGES = [
    ("en", ""),  # default locale serves at the site root, no prefix
    ("it", "it/"),
]


def build_url(base_url: str, lang_prefix: str, page_path: str) -> str:
    return f"{base_url.rstrip('/')}/{lang_prefix}{page_path}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="qr-codes", help="Output directory for PNGs")
    parser.add_argument("--base-url", default=SITE_BASE_URL, help="Site base URL")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated = []
    for stem, page_path, label in HARDWARE_PAGES:
        for lang_code, lang_prefix in LANGUAGES:
            url = build_url(args.base_url, lang_prefix, page_path)
            filename = out_dir / f"{stem}.{lang_code}.png"
            img = qrcode.make(url)
            img.save(filename)
            generated.append((filename, label, lang_code, url))

    print(f"Generated {len(generated)} QR codes in {out_dir}/\n")
    for filename, label, lang_code, url in generated:
        print(f"  [{lang_code}] {label:35s} -> {filename.name}\n        {url}")


if __name__ == "__main__":
    main()
