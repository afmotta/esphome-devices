#!/usr/bin/env bash
# =============================================================================
# verification-battery.sh — the repeatable cross-system verification battery
# (HVAC-Epic-1 story 1.6 release gate; useful for any change touching canbus/,
# lighting/, climate/, shared packages, or the generated registry artifacts).
#
# Usage (from anywhere — the script locates the repo root):
#   bash scripts/verification-battery.sh                 # full battery
#   bash scripts/verification-battery.sh --native-only   # esphome-free subset
#
# --native-only runs only the python + native C++ tests and the generator
# idempotence check, loudly skipping every step that needs the `esphome` CLI:
# the ESPHome config/compile gates and the Climate package failover e2e (whose fixture
# compiles a host-platform harness). Use it when ESPHome is not installed.
# ESPHome pin for full runs: esphome==2026.7.0 (climate/tests/pyproject.toml's
# deliberate pin, >= the repo entry points' 2026.7.0 floor). The Climate package e2e
# step additionally needs pytest, pytest-asyncio, and aioesphomeapi.
#
# NOTE — the "generator idempotence" step regenerates every generated artifact
# and then asserts `git diff --exit-code canbus climate registry`, so the TRACKED
# FILES UNDER canbus/, climate/, AND registry/ MUST BE CLEAN before running
# (commit or stash first). The step pre-checks this and fails with a clear
# message instead of burying uncommitted work under regenerated output.
#
# Behavior: fail-fast — the first failing step prints its log tail and aborts
# the run (later steps show as "skip (aborted)" in the summary); exit code is
# 0 only when every non-skipped step passed. Full per-step logs are kept in a
# temp directory whose path is printed at the end.
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

usage() {
  sed -n '2,29p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

NATIVE_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --native-only) NATIVE_ONLY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "error: unknown argument '$arg' (try --help)" >&2; exit 2 ;;
  esac
done

# Pre-flight: in full mode the esphome CLI must exist; fail early and clearly.
if [ "$NATIVE_ONLY" -eq 0 ] && ! command -v esphome >/dev/null 2>&1; then
  echo "error: 'esphome' CLI not found on PATH." >&2
  echo "  install it (pip install \"esphome==2026.7.0\") or re-run with --native-only" >&2
  exit 2
fi

LOG_DIR="$(mktemp -d "${TMPDIR:-/tmp}/verification-battery.XXXXXX")"
BIN_DIR="$LOG_DIR/bin"
mkdir -p "$BIN_DIR"

STEP_NAMES=()
STEP_RESULTS=()
FAILED=0

# run_step <name> <command...> — run one battery step, capture its output,
# print PASS/FAIL. After the first failure, later steps are recorded as
# skipped (fail-fast) but the summary still lists every step.
run_step() {
  local name="$1"; shift
  STEP_NAMES+=("$name")
  if [ "$FAILED" -ne 0 ]; then
    STEP_RESULTS+=("skip (aborted)")
    return 0
  fi
  local log="$LOG_DIR/$(printf '%02d' "${#STEP_NAMES[@]}").log"
  printf '%-66s ' "$name"
  local start=$SECONDS
  if "$@" >"$log" 2>&1; then
    STEP_RESULTS+=("PASS")
    printf 'PASS (%3ds)\n' "$((SECONDS - start))"
  else
    STEP_RESULTS+=("FAIL")
    FAILED=1
    printf 'FAIL (%3ds)\n' "$((SECONDS - start))"
    echo "――― last 50 lines of $log ―――"
    tail -n 50 "$log"
    echo "―――――――――――――――――――――――――――――"
  fi
}

# skip_step <name> <reason> — record a deliberately skipped step, loudly.
skip_step() {
  STEP_NAMES+=("$1")
  STEP_RESULTS+=("skip ($2)")
  printf '%-66s SKIP: %s\n' "$1" "$2"
}

# cxx_run <bin-name> <g++ args...> — compile a native test and run it.
cxx_run() {
  local bin="$BIN_DIR/$1"; shift
  g++ -std=c++17 -Wall -Wextra "$@" -o "$bin"
  "$bin"
}

# Generator idempotence (epic HVAC-1 AC6): an unchanged registry regenerates
# byte-for-byte across canbus/, climate/ (routing artifacts), and registry/.
idempotence_check() {
  if ! git diff --quiet -- canbus climate registry; then
    echo "PRECONDITION FAILED: tracked files under canbus/, climate/, or registry/"
    echo "have uncommitted modifications. This step regenerates all generated"
    echo "artifacts and asserts a byte-identical tree — commit or stash first."
    git --no-pager diff --stat -- canbus climate registry
    return 1
  fi
  python3 canbus/tools/generate_nodes.py
  git diff --exit-code canbus climate registry
}

# Top-level logger configuration in deployable packages should be variable-driven with an
# INFO default. Tests, examples, and bench docs may intentionally use DEBUG, but production
# device/board/node packages should not hardcode it.
logger_level_check() {
  local offenders
  offenders="$(
    git grep -n -E '^  level: DEBUG$' -- boards canbus/packages devices 2>/dev/null || true
  )"
  if [ -n "$offenders" ]; then
    echo "Hardcoded top-level logger DEBUG found in deployable configs/packages:"
    echo "$offenders"
    echo "Use a logger_level substitution with INFO default, then override only in local/test wrappers."
    return 1
  fi
}

echo "verification battery — repo: $REPO_ROOT"
[ "$NATIVE_ONLY" -eq 1 ] && echo "mode: --native-only (esphome-dependent steps are SKIPPED)"
echo

# ── Python tests (stdlib-only) ──────────────────────────────────────────────
run_step "hygiene: no tracked secrets or build artifacts" python3 scripts/check_repo_hygiene.py
run_step "hygiene: deployable logger levels are configurable" logger_level_check
run_step "climate: seasonal mode PID aggregation is complete" python3 scripts/verify_seasonal_mode_aggregation.py
run_step "python: canbus/tests/test_bindings.py"          python3 canbus/tests/test_bindings.py
run_step "python: canbus/tests/test_generate_exports.py"  python3 canbus/tests/test_generate_exports.py
run_step "python: canbus/tests/test_push_gate.py"         python3 canbus/tests/test_push_gate.py

# ── Native C++ tests (no ESPHome deps) ──────────────────────────────────────
run_step "native: canbus test_protocol.cpp"          cxx_run proto     canbus/tests/test_protocol.cpp
run_step "native: canbus test_ha_arbitration.cpp"    cxx_run arb       canbus/tests/test_ha_arbitration.cpp
run_step "native: canbus test_node_health.cpp"       cxx_run health    canbus/tests/test_node_health.cpp
run_step "native: canbus test_bridge_forwarding.cpp" cxx_run bridge    canbus/tests/test_bridge_forwarding.cpp
run_step "native: canbus test_bindings_contract.cpp" cxx_run bcontract canbus/tests/test_bindings_contract.cpp
run_step "native: lighting test_binding_actuation.cpp" \
  cxx_run act -Icanbus/protocol -Ilighting/protocol lighting/tests/test_binding_actuation.cpp
run_step "native: climate test_can_sensor_receiver.cpp" \
  cxx_run climate_can_sensor_receiver -Icanbus/protocol -Iclimate/protocol climate/tests/test_can_sensor_receiver.cpp

# ── Generator idempotence (needs clean canbus/climate/registry paths) ──────────
run_step "generator idempotence: regenerate + git diff --exit-code" idempotence_check

# ── ESPHome gates + Climate package e2e (skipped under --native-only) ───────
if [ "$NATIVE_ONLY" -eq 1 ]; then
  skip_step "esphome config climate/tests/compile_can_sensor_receiver.yaml" "--native-only"
  skip_step "esphome compile canbus/tests/compile_sensor_node.yaml"      "--native-only"
  skip_step "esphome config devices/locals/climate-control.yaml"         "--native-only"
  skip_step "esphome compile devices/locals/climate-control.yaml"        "--native-only"
  skip_step "pytest climate/tests/e2e/test_failover_sensor.py"              "--native-only"
else
  run_step "esphome config climate/tests/compile_can_sensor_receiver.yaml" \
    esphome config climate/tests/compile_can_sensor_receiver.yaml
  run_step "esphome compile canbus/tests/compile_sensor_node.yaml" \
    esphome compile canbus/tests/compile_sensor_node.yaml
  run_step "esphome config devices/locals/climate-control.yaml" \
    esphome config devices/locals/climate-control.yaml
  run_step "esphome compile devices/locals/climate-control.yaml" \
    esphome compile devices/locals/climate-control.yaml
  run_step "pytest climate/tests/e2e/test_failover_sensor.py" \
    python3 -m pytest climate/tests/e2e/test_failover_sensor.py
fi

# ── Summary ─────────────────────────────────────────────────────────────────
echo
echo "── Summary ──────────────────────────────────────────────────────────"
for i in "${!STEP_NAMES[@]}"; do
  printf '  %-64s %s\n' "${STEP_NAMES[$i]}" "${STEP_RESULTS[$i]}"
done
echo "─────────────────────────────────────────────────────────────────────"
echo "logs: $LOG_DIR"

if [ "$FAILED" -ne 0 ]; then
  echo "RESULT: FAIL"
  exit 1
fi
echo "RESULT: PASS"
