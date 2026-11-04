#!/bin/bash
# fresh placement + import of the last Freerouting session + pours
set -e
cd "$(dirname "$0")"
python3 gen_pcb.py 2>&1 | grep -v swig
python3 route_import.py "${1:-bridgecan.ses}" 2>&1 | grep -v swig
python3 drc.py 2>&1 | grep -v swig
