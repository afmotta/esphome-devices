#!/bin/bash
# Install Climate Control Dashboards via Home Assistant API
#
# Usage:
#   ./install-dashboards.sh http://homeassistant.local:8123 YOUR_LONG_LIVED_TOKEN
#
# Requirements:
# - curl
# - jq (optional, for pretty output)

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <HA_URL> <ACCESS_TOKEN>"
    echo ""
    echo "Example:"
    echo "  $0 http://homeassistant.local:8123 eyJ0eXAiOiJKV1QiLCJhbGc..."
    echo ""
    echo "To create a long-lived access token:"
    echo "  1. Open Home Assistant"
    echo "  2. Click your profile (bottom left)"
    echo "  3. Scroll to 'Long-Lived Access Tokens'"
    echo "  4. Click 'Create Token'"
    exit 1
fi

HA_URL="${1%/}"  # Remove trailing slash
TOKEN="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to convert YAML to JSON (basic conversion)
yaml_to_json() {
    python3 -c "import sys, yaml, json; json.dump(yaml.safe_load(sys.stdin), sys.stdout)" < "$1"
}

# Function to create or update dashboard
install_dashboard() {
    local url_path="$1"
    local title="$2"
    local icon="$3"
    local show_in_sidebar="$4"
    local yaml_file="$5"

    echo -n "Installing: $title... "

    # Check if Python3 and PyYAML are available
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗${NC}"
        echo "  Error: python3 not found. Please install Python 3."
        return 1
    fi

    # Convert YAML to JSON
    if ! config_json=$(yaml_to_json "$yaml_file" 2>/dev/null); then
        echo -e "${RED}✗${NC}"
        echo "  Error: Failed to parse YAML. Install PyYAML: pip3 install pyyaml"
        return 1
    fi

    # Create dashboard metadata
    dashboard_meta=$(cat <<EOF
{
    "url_path": "$url_path",
    "title": "$title",
    "icon": "$icon",
    "show_in_sidebar": $show_in_sidebar,
    "require_admin": false
}
EOF
)

    # Try to get existing dashboard
    if curl -s -f -X GET \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        "$HA_URL/api/lovelace/dashboards/$url_path" &>/dev/null; then

        # Dashboard exists, update it
        curl -s -X PUT \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$dashboard_meta" \
            "$HA_URL/api/lovelace/dashboards/$url_path" > /dev/null

        # Update config
        curl -s -X POST \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$config_json" \
            "$HA_URL/api/lovelace/dashboards/$url_path/config" > /dev/null

    else
        # Dashboard doesn't exist, create it
        curl -s -X POST \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$dashboard_meta" \
            "$HA_URL/api/lovelace/dashboards" > /dev/null

        # Set config
        curl -s -X POST \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$config_json" \
            "$HA_URL/api/lovelace/dashboards/$url_path/config" > /dev/null
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# Main installation
echo "========================================"
echo "Climate Control Dashboard Installer"
echo "========================================"
echo "Home Assistant: $HA_URL"
echo "Dashboard directory: $SCRIPT_DIR"
echo ""

# Test connection
echo -n "Testing connection to Home Assistant... "
if curl -s -f -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$HA_URL/api/" > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Error: Cannot connect to Home Assistant or invalid token"
    exit 1
fi

echo ""
echo "Installing dashboards..."
echo "----------------------------------------"

# Install main dashboards
SUCCESS=0
FAILED=0

if install_dashboard "climate-overview" "Climate Control" "mdi:home-thermometer" "true" "$SCRIPT_DIR/climate-overview.yaml"; then
    ((SUCCESS++))
else
    ((FAILED++))
fi

if install_dashboard "ground-floor" "Ground Floor" "mdi:home-floor-0" "false" "$SCRIPT_DIR/ground-floor.yaml"; then
    ((SUCCESS++))
else
    ((FAILED++))
fi

if install_dashboard "first-floor" "First Floor" "mdi:home-floor-1" "false" "$SCRIPT_DIR/first-floor.yaml"; then
    ((SUCCESS++))
else
    ((FAILED++))
fi

if install_dashboard "second-floor" "Second Floor" "mdi:home-floor-2" "false" "$SCRIPT_DIR/second-floor.yaml"; then
    ((SUCCESS++))
else
    ((FAILED++))
fi

if install_dashboard "system-monitoring" "System Monitoring" "mdi:monitor-dashboard" "false" "$SCRIPT_DIR/system-monitoring.yaml"; then
    ((SUCCESS++))
else
    ((FAILED++))
fi

echo "----------------------------------------"
echo ""
echo "Installation Summary:"
echo "  Successful: $SUCCESS"
echo "  Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All dashboards installed successfully!${NC}"
    echo ""
    echo "Access your dashboard at:"
    echo "  $HA_URL/lovelace/climate-overview"
    echo ""
    echo "Note: Room dashboards are not installed via API as they"
    echo "      are accessed via navigation buttons from floor dashboards."
    exit 0
else
    echo -e "${RED}Some dashboards failed to install.${NC}"
    exit 1
fi
