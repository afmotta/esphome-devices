# Test Implementation Quick Start Guide

**Related Document:** [test-coverage-analysis.md](./test-coverage-analysis.md)

---

## Getting Started (Week 1)

### Step 1: Install Test Dependencies

```bash
# Python testing tools
pip install pytest pytest-cov pytest-asyncio pytest-mock pyyaml

# ESPHome for validation
pip install esphome

# C++ testing tools (for LD2450 component)
sudo apt-get install libgtest-dev libgmock-dev cmake
```

### Step 2: Create Test Directory Structure

```bash
mkdir -p tests/{unit,integration,e2e,fixtures,mocks}
mkdir -p tests/unit/{components,libs,config}
touch tests/conftest.py
touch tests/__init__.py
```

### Step 3: Create First Test (Failover Sensor)

Create `tests/unit/components/test_failover_sensor.py`:

```python
import pytest
from unittest.mock import Mock, MagicMock
import math

class TestFailoverSensor:
    """Test suite for 3-tier sensor failover logic"""

    @pytest.fixture
    def mock_sensors(self):
        """Create mock HA and UDP sensors"""
        ha_sensor = Mock()
        udp_sensor = Mock()
        tier_sensor = Mock()
        return {
            'ha': ha_sensor,
            'udp': udp_sensor,
            'tier': tier_sensor
        }

    def test_tier1_ha_active_when_both_valid(self, mock_sensors):
        """FS-001: When both sensors valid, use HA (Tier 1)"""
        # Arrange
        mock_sensors['ha'].state = 22.5
        mock_sensors['udp'].state = 22.3

        # Act
        result = failover_logic(mock_sensors['ha'], mock_sensors['udp'])

        # Assert
        assert result['value'] == 22.5
        assert result['tier'] == 'HA'

    def test_tier2_udp_active_when_ha_nan(self, mock_sensors):
        """FS-002: When HA unavailable, fallback to UDP (Tier 2)"""
        # Arrange
        mock_sensors['ha'].state = float('nan')
        mock_sensors['udp'].state = 22.3

        # Act
        result = failover_logic(mock_sensors['ha'], mock_sensors['udp'])

        # Assert
        assert result['value'] == 22.3
        assert result['tier'] == 'UDP'

    def test_tier3_emergency_when_both_nan(self, mock_sensors):
        """FS-003: When both unavailable, enter Emergency (Tier 3)"""
        # Arrange
        mock_sensors['ha'].state = float('nan')
        mock_sensors['udp'].state = float('nan')

        # Act
        result = failover_logic(mock_sensors['ha'], mock_sensors['udp'])

        # Assert
        assert math.isnan(result['value'])
        assert result['tier'] == 'Emergency'

    def test_recovery_from_emergency_to_ha(self, mock_sensors):
        """FS-004: Recovery path from Emergency back to HA"""
        # Arrange - start in emergency
        mock_sensors['ha'].state = float('nan')
        mock_sensors['udp'].state = float('nan')
        result1 = failover_logic(mock_sensors['ha'], mock_sensors['udp'])
        assert result1['tier'] == 'Emergency'

        # Act - HA comes back online
        mock_sensors['ha'].state = 21.8
        result2 = failover_logic(mock_sensors['ha'], mock_sensors['udp'])

        # Assert
        assert result2['value'] == 21.8
        assert result2['tier'] == 'HA'


def failover_logic(ha_sensor, udp_sensor):
    """
    Extracted failover logic from YAML lambda for testing.
    This will be imported from the actual implementation.
    """
    # Tier 1: HA sensor (primary)
    if not math.isnan(ha_sensor.state):
        return {'value': ha_sensor.state, 'tier': 'HA'}

    # Tier 2: UDP sensor (fallback)
    if not math.isnan(udp_sensor.state):
        return {'value': udp_sensor.state, 'tier': 'UDP'}

    # Tier 3: Emergency (both unavailable)
    return {'value': float('nan'), 'tier': 'Emergency'}
```

### Step 4: Run First Test

```bash
cd /home/user/esphome-devices
pytest tests/unit/components/test_failover_sensor.py -v
```

---

## Priority Test Implementation Order

### Week 1-2: Infrastructure + First Tests
1. ✅ Set up test directory structure
2. ✅ Install dependencies
3. ✅ Write failover sensor tests (FS-001 to FS-007)
4. ⬜ Set up pytest configuration
5. ⬜ Create mock ESPHome sensor objects

### Week 3-4: PID Controller Tests
1. ⬜ Extract PID calculation logic for testing
2. ⬜ Write PID unit tests (PID-001 to PID-006)
3. ⬜ Test heat/cool mode switching
4. ⬜ Test NaN input handling
5. ⬜ Test output saturation

### Week 5-6: Integration Tests
1. ⬜ Test failover → PID interaction
2. ⬜ Test multi-zone coordination
3. ⬜ Set up CI/CD pipeline (GitHub Actions)
4. ⬜ Add coverage reporting

### Week 7-12: Boost Coordinator & MEV
1. ⬜ Boost coordinator unit tests (BC-001 to BC-007)
2. ⬜ MEV control unit tests (MEV-001 to MEV-006)
3. ⬜ Multi-room boost integration tests
4. ⬜ MEV demand aggregation tests

---

## Test Patterns for ESPHome Components

### Pattern 1: Testing YAML Lambda Logic

**Problem:** YAML lambdas are embedded strings, hard to test.

**Solution:** Extract to testable Python functions.

**Example:**

```python
# tests/unit/components/test_boost_coordinator.py

def calculate_boost_trigger(temp_delta, humidity, radiant_output,
                           temp_threshold=3.0, humidity_threshold=65.0,
                           hysteresis=5.0, saturation_threshold=95.0):
    """
    Extracted boost activation logic from fancoil_boost_coordinator.yaml

    Returns True if boost should activate based on:
    - Temperature delta > threshold, OR
    - Humidity > threshold + hysteresis/2, OR
    - Radiant output >= saturation threshold (predictive)
    """
    # Temperature trigger
    if temp_delta > temp_threshold:
        return True, "Temperature"

    # Humidity trigger (with hysteresis)
    if humidity > humidity_threshold + (hysteresis / 2):
        return True, "Humidity"

    # Predictive trigger (radiant saturated)
    if radiant_output >= saturation_threshold:
        return True, "Predictive"

    return False, "Normal"


class TestBoostCoordinator:
    def test_temperature_trigger(self):
        """BC-002: Boost activates when delta exceeds threshold"""
        result, reason = calculate_boost_trigger(
            temp_delta=3.5,  # > 3.0 threshold
            humidity=60.0,
            radiant_output=50.0
        )
        assert result is True
        assert reason == "Temperature"

    def test_humidity_trigger_with_hysteresis(self):
        """BC-003: Boost activates at humidity > threshold + hysteresis/2"""
        result, reason = calculate_boost_trigger(
            temp_delta=2.0,
            humidity=67.6,  # > 65 + 2.5
            radiant_output=50.0
        )
        assert result is True
        assert reason == "Humidity"

    def test_no_trigger_in_normal_conditions(self):
        """BC-001: No boost in normal operating conditions"""
        result, reason = calculate_boost_trigger(
            temp_delta=1.0,
            humidity=60.0,
            radiant_output=50.0
        )
        assert result is False
        assert reason == "Normal"
```

### Pattern 2: Mocking ESPHome Sensor Objects

```python
# tests/mocks/mock_sensors.py

class MockSensor:
    """Mock ESPHome sensor object"""
    def __init__(self, initial_state=None):
        self.state = initial_state or 0.0
        self._observers = []

    def publish_state(self, value):
        self.state = value
        for callback in self._observers:
            callback(value)

    def add_observer(self, callback):
        self._observers.append(callback)


class MockTextSensor:
    """Mock ESPHome text sensor"""
    def __init__(self, initial_state=""):
        self.state = initial_state

    def publish_state(self, value):
        self.state = str(value)


# Usage in tests
def test_with_mock_sensors():
    temp_sensor = MockSensor(initial_state=22.5)
    tier_sensor = MockTextSensor()

    # Simulate sensor update
    temp_sensor.publish_state(23.0)
    assert temp_sensor.state == 23.0
```

### Pattern 3: Parameterized Multi-Zone Tests

```python
# Test all 13 zones with same logic
@pytest.mark.parametrize("zone,expected_relay", [
    ("soggiorno", "relay_1"),
    ("cucina", "relay_2"),
    ("bagno", "relay_3"),
    ("anticamera", "relay_4"),
    ("locale_tecnico", "relay_5"),
    ("bagno_grande", "relay_9"),
    ("bagno_ospiti", "relay_10"),
    ("bagno_padronale", "relay_11"),
    ("camera_nord", "relay_12"),
    ("camera_sud", "relay_13"),
    ("camera_ospiti", "relay_14"),
    ("camera_padronale", "relay_15"),
    ("lavanderia", "relay_16"),
])
def test_zone_relay_mapping(zone, expected_relay):
    """Verify each zone maps to correct relay"""
    config = load_zone_config(zone)
    assert config['radiant_relay'] == expected_relay
```

---

## Testing C++ Components (LD2450)

### Create C++ Test File

Create `tests/unit/libs/test_ld2450.cpp`:

```cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "libs/s1_pro/s1_pro.h"

using namespace esphome::s1_pro;

class LD2450Test : public ::testing::Test {
protected:
    LD2450 sensor;

    void SetUp() override {
        // Initialize test sensor
    }
};

TEST_F(LD2450Test, ExclusionZoneDetection) {
    // Test point-in-polygon algorithm
    // Set up exclusion zone with 4 points
    // Verify points inside zone are filtered
    // Verify points outside zone are tracked
}

TEST_F(LD2450Test, StationaryDetection) {
    // Test stationary target detection
    // Target with speed < threshold for time > threshold
    // Should mark target as stationary
}

TEST_F(LD2450Test, DropoutHoldPreventsFlapping) {
    // Test dropout hold timing
    // Target disappears then reappears within hold time
    // Should maintain tracking state
}
```

### Compile and Run C++ Tests

```bash
cd tests/unit/libs
g++ -std=c++17 -I../../.. -lgtest -lgtest_main test_ld2450.cpp -o test_ld2450
./test_ld2450
```

---

## CI/CD Integration

### Create `.github/workflows/test.yml`

```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop, 'claude/**' ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov pytest-asyncio pytest-mock
          pip install esphome pyyaml

      - name: Run unit tests
        run: |
          pytest tests/unit -v --cov=components --cov=libs --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  compile-check:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install ESPHome
        run: pip install esphome

      - name: Compile climate-control
        run: esphome compile devices/climate-control.yaml

      - name: Compile room sensor
        run: esphome compile devices/room-sensor-soggiorno.yaml
```

---

## Quick Wins (Immediate Value)

### 1. YAML Syntax Validation Test

```python
# tests/unit/config/test_yaml_syntax.py
import yaml
import pytest
from pathlib import Path

def test_all_yaml_files_valid_syntax():
    """Verify all YAML files have valid syntax"""
    base_dir = Path(__file__).parent.parent.parent.parent
    yaml_files = list(base_dir.glob('**/*.yaml'))

    for yaml_file in yaml_files:
        if '.git' in str(yaml_file):
            continue

        with open(yaml_file, 'r') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"YAML syntax error in {yaml_file}: {e}")
```

### 2. Entity ID Uniqueness Test

```python
# tests/unit/config/test_entity_uniqueness.py
def test_no_duplicate_entity_ids():
    """Verify no duplicate entity IDs across all configs"""
    entity_ids = []
    # Parse all YAML configs
    # Extract all entity IDs
    # Check for duplicates
    assert len(entity_ids) == len(set(entity_ids)), "Duplicate entity IDs found"
```

### 3. Relay Assignment Validation

```python
# tests/unit/config/test_relay_assignments.py
def test_no_relay_conflicts():
    """Verify no relay is assigned to multiple zones"""
    relay_assignments = {}
    # Parse all room configs
    # Check relay_1 through relay_24
    # Ensure no conflicts
    for relay, zones in relay_assignments.items():
        assert len(zones) == 1, f"Relay {relay} assigned to multiple zones: {zones}"
```

---

## Measuring Success

### Coverage Report

```bash
# Run tests with coverage
pytest tests/ --cov=components --cov=libs --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Test Metrics Dashboard

Track these metrics over time:
- **Line coverage**: Target 75% overall, 90% for safety-critical
- **Test execution time**: Keep under 10 minutes
- **Test failures**: Should be zero on main branch
- **Flaky tests**: Track and fix tests that fail intermittently

### Example Coverage Goals

```
components/failover_sensor.yaml        90%  ████████████████████░
components/pid.yaml                    80%  ████████████████░░░░
components/fancoil_boost_coordinator   85%  █████████████████░░░
components/mev.yaml                    80%  ████████████████░░░░
libs/s1_pro/s1_pro.h                   70%  ██████████████░░░░░░
Overall                                75%  ███████████████░░░░░
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Testing ESPHome-Specific APIs
**Problem:** ESPHome components use platform-specific APIs (e.g., `id()`, `ESP_LOGI`)

**Solution:** Mock these in `conftest.py`:
```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def mock_esphome_globals(monkeypatch):
    """Mock ESPHome global functions"""
    monkeypatch.setattr('id', MagicMock())
    monkeypatch.setattr('ESP_LOGI', MagicMock())
    monkeypatch.setattr('ESP_LOGE', MagicMock())
```

### Pitfall 2: Time-Dependent Tests
**Problem:** Boost coordinator has 10-minute minimum time-in-state

**Solution:** Mock time functions:
```python
from unittest.mock import patch
import time

def test_minimum_time_in_state():
    with patch('time.time') as mock_time:
        mock_time.return_value = 1000
        # Trigger boost
        # Advance time by 9 minutes
        mock_time.return_value = 1000 + (9 * 60)
        # Verify boost still active
        # Advance time by 11 minutes
        mock_time.return_value = 1000 + (11 * 60)
        # Verify boost can deactivate now
```

### Pitfall 3: Floating Point Comparisons
**Problem:** Temperature comparisons may fail due to floating point precision

**Solution:** Use `pytest.approx()`:
```python
def test_temperature_calculation():
    result = calculate_temp_delta(setpoint=22.0, current=19.5)
    assert result == pytest.approx(2.5, abs=0.01)
```

---

## Resources

### Documentation
- [pytest documentation](https://docs.pytest.org/)
- [ESPHome testing guide](https://esphome.io/guides/contributing.html#testing)
- [Google Test documentation](https://google.github.io/googletest/)

### Example Projects
- ESPHome core tests: https://github.com/esphome/esphome/tree/dev/tests
- pytest examples: https://github.com/pytest-dev/pytest/tree/main/testing

### Getting Help
- ESPHome Discord: https://discord.gg/KhAMKrd
- pytest Gitter: https://gitter.im/pytest-dev/pytest

---

## Next Steps

1. **Read** [test-coverage-analysis.md](./test-coverage-analysis.md) for full context
2. **Follow** Week 1-2 steps above to set up infrastructure
3. **Implement** failover sensor tests (highest priority)
4. **Run** tests locally and verify they pass
5. **Set up** CI/CD pipeline to run tests automatically
6. **Iterate** on test coverage following the implementation roadmap

**Questions?** Open an issue or check the BMAD framework documentation in `.bmad-core/`.
