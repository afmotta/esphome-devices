# API Installation Guide

## ⚠️ IMPORTANT NOTICE

**This guide and the included API installation scripts are NOT FUNCTIONAL** for these dashboards.

After verification, Home Assistant's REST API for dashboards (`/api/lovelace/dashboards`) only supports:
- Creating **storage mode** dashboards (UI-created dashboards)
- The API does **NOT** support loading YAML dashboard configurations

Since these dashboards are designed as YAML configurations, they cannot be installed via the REST API.

**Please use YAML mode installation instead** - see [README.md](README.md) or [QUICK_START.md](QUICK_START.md) for the correct installation method.

---

## Original Documentation (For Reference Only)

The information below was based on an incorrect understanding of Home Assistant's dashboard API capabilities. It is preserved for reference but the scripts will not work as intended.

## Benefits of API Installation (Not Applicable)

✅ **No configuration.yaml edits** - No need to modify Home Assistant config files
✅ **No restart required** - Dashboards appear immediately after installation
✅ **Automated deployment** - Perfect for CI/CD or scripted installations
✅ **Easy updates** - Re-run script to update all dashboards
✅ **Storage mode** - Dashboards stored in HA's internal storage (UI-editable)

## Prerequisites

### 1. Home Assistant Running

Ensure your Home Assistant instance is accessible at a URL:
- Local: `http://homeassistant.local:8123`
- IP: `http://192.168.1.100:8123`
- Remote: `https://your-domain.com`

### 2. Long-Lived Access Token

Create a token in Home Assistant:

1. Click your **profile** (bottom left corner)
2. Scroll down to **"Long-Lived Access Tokens"**
3. Click **"Create Token"**
4. Give it a name (e.g., "Dashboard Installer")
5. Copy the token (it starts with `eyJ0eXAi...`)

⚠️ **Save this token securely** - You won't be able to see it again!

### 3. Install Python Dependencies

**⚠️ REQUIRED for Python script:**

The script needs PyYAML to parse dashboard configuration files.

**Option 1: Install from requirements.txt (Recommended)**
```bash
cd /path/to/esphome-devices/climate/home-assistant/dashboards
pip3 install -r requirements.txt
```

**Option 2: Install directly**
```bash
pip3 install pyyaml
```

**Alternative commands if the above doesn't work:**
```bash
# Try with python3 -m pip
python3 -m pip install pyyaml

# On some systems
pip install pyyaml

# With sudo (if needed)
sudo pip3 install pyyaml
```

**Verify installation:**
```bash
python3 -c "import yaml; print('PyYAML installed successfully')"
```

**For Bash script:**
```bash
# curl is usually pre-installed
curl --version

# PyYAML still required (used internally)
pip3 install pyyaml

# Optional (for pretty output):
sudo apt-get install jq  # Debian/Ubuntu
brew install jq          # macOS
```

---

## Installation Methods

### Method 1: Python Script (Recommended)

**Advantages**: Better error handling, cross-platform, detailed output

**Step 1: Install PyYAML**
```bash
cd /path/to/esphome-devices/climate/home-assistant/dashboards
pip3 install -r requirements.txt
```

**Step 2: Run installation**
```bash
python3 install-dashboards.py \
    --url http://homeassistant.local:8123 \
    --token eyJ0eXAiOiJKV1QiLCJhbGc...YOUR_TOKEN_HERE
```

**Output:**
```
Installing dashboards from: /path/to/dashboards
Home Assistant URL: http://homeassistant.local:8123
------------------------------------------------------------
Creating new dashboard: Climate Control
✓ Climate Control installed successfully
Creating new dashboard: Ground Floor
✓ Ground Floor installed successfully
Creating new dashboard: First Floor
✓ First Floor installed successfully
Creating new dashboard: Second Floor
✓ Second Floor installed successfully
Creating new dashboard: System Monitoring
✓ System Monitoring installed successfully
------------------------------------------------------------

Installation Summary:
Successful: 5
Failed: 0

✓ All dashboards installed successfully!

Access your dashboards at: http://homeassistant.local:8123/lovelace/climate-overview
```

---

### Method 2: Bash Script (Unix/Linux/macOS)

**Advantages**: No Python dependencies (except PyYAML), simple

```bash
cd /path/to/esphome-devices/climate/home-assistant/dashboards

chmod +x install-dashboards.sh

./install-dashboards.sh \
    http://homeassistant.local:8123 \
    eyJ0eXAiOiJKV1QiLCJhbGc...YOUR_TOKEN_HERE
```

**Output:**
```
========================================
Climate Control Dashboard Installer
========================================
Home Assistant: http://homeassistant.local:8123
Dashboard directory: /path/to/dashboards

Testing connection to Home Assistant... ✓

Installing dashboards...
----------------------------------------
Installing: Climate Control... ✓
Installing: Ground Floor... ✓
Installing: First Floor... ✓
Installing: Second Floor... ✓
Installing: System Monitoring... ✓
----------------------------------------

Installation Summary:
  Successful: 5
  Failed: 0

✓ All dashboards installed successfully!

Access your dashboard at:
  http://homeassistant.local:8123/lovelace/climate-overview
```

---

### Method 3: Manual API Calls (Advanced)

For integration into custom deployment scripts or CI/CD pipelines.

**Create Dashboard (POST):**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url_path": "climate-overview",
    "title": "Climate Control",
    "icon": "mdi:home-thermometer",
    "show_in_sidebar": true,
    "require_admin": false
  }' \
  http://homeassistant.local:8123/api/lovelace/dashboards
```

**Set Dashboard Config (POST):**
```bash
# Convert YAML to JSON first
python3 -c "import sys, yaml, json; json.dump(yaml.safe_load(open('climate-overview.yaml')), sys.stdout)" > config.json

curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @config.json \
  http://homeassistant.local:8123/api/lovelace/dashboards/climate-overview/config
```

**Update Existing Dashboard (PUT):**
```bash
curl -X PUT \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url_path": "climate-overview",
    "title": "Climate Control",
    "icon": "mdi:home-thermometer",
    "show_in_sidebar": true,
    "require_admin": false
  }' \
  http://homeassistant.local:8123/api/lovelace/dashboards/climate-overview
```

**Delete Dashboard (DELETE):**
```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://homeassistant.local:8123/api/lovelace/dashboards/climate-overview
```

---

## Room Dashboards

**Note**: Room dashboards (14 total) are **NOT** installed via API because they are designed to be accessed via navigation buttons from floor dashboards, not as standalone dashboard entries.

If you want to install room dashboards as standalone dashboards:

```python
# Example for Soggiorno room
installer.create_dashboard(
    url_path='soggiorno',
    config=installer.load_dashboard_yaml('rooms/ground_floor/soggiorno.yaml'),
    title='Soggiorno',
    icon='mdi:sofa',
    show_in_sidebar=False  # Hidden, but accessible via direct URL
)
```

---

## Updating Dashboards

Simply re-run the installation script. It will detect existing dashboards and update them:

```bash
# Python
python3 install-dashboards.py --url http://homeassistant.local:8123 --token YOUR_TOKEN

# Bash
./install-dashboards.sh http://homeassistant.local:8123 YOUR_TOKEN
```

**Output:**
```
Updating existing dashboard: Climate Control
✓ Climate Control installed successfully
```

---

## Troubleshooting

### Error: "Cannot connect to Home Assistant"

**Cause**: Wrong URL or HA not running

**Fix**:
```bash
# Test connection
curl http://homeassistant.local:8123/api/

# Should return: {"message": "API running."}
```

### Error: "401 Unauthorized"

**Cause**: Invalid or expired token

**Fix**:
1. Create a new long-lived access token in HA
2. Use the new token in the script

### Error: "ModuleNotFoundError: No module named 'yaml'" or "ERROR: PyYAML library not found"

**Cause**: PyYAML library not installed

**Fix (try in this order):**

**1. Install from requirements.txt (Recommended):**
```bash
cd /path/to/esphome-devices/climate/home-assistant/dashboards
pip3 install -r requirements.txt
```

**2. Install directly:**
```bash
pip3 install pyyaml
```

**3. Alternative methods:**
```bash
# Try with python3 -m pip
python3 -m pip install pyyaml

# Try with just pip (some systems)
pip install pyyaml

# With sudo if you get permission errors
sudo pip3 install pyyaml

# On Debian/Ubuntu, install via apt
sudo apt-get install python3-yaml
```

**4. Verify installation:**
```bash
python3 -c "import yaml; print('PyYAML version:', yaml.__version__)"
```

**5. If still failing, check your Python environment:**
```bash
# Check which Python you're using
which python3
python3 --version

# Check where pip installs packages
pip3 show pyyaml

# You might need to use a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install pyyaml
python install-dashboards.py --url ... --token ...
```

### Error: "Failed to parse YAML"

**Cause**: Malformed YAML file

**Fix**:
```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('climate-overview.yaml'))"
```

### Dashboards don't appear in sidebar

**Issue**: Only "Climate Control" should appear in sidebar

**Expected behavior**:
- ✓ "Climate Control" visible in sidebar
- ✗ Other dashboards hidden (access via navigation buttons)

**To verify**:
```bash
# List all dashboards
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://homeassistant.local:8123/api/lovelace/dashboards | jq
```

---

## Security Best Practices

### 1. Protect Your Token

**Never commit tokens to Git:**
```bash
# Use environment variable
export HA_TOKEN="eyJ0eXAiOiJKV1Qi..."

python3 install-dashboards.py \
    --url http://homeassistant.local:8123 \
    --token "$HA_TOKEN"
```

**Or use a token file:**
```bash
echo "eyJ0eXAiOiJKV1Qi..." > .ha_token
chmod 600 .ha_token

# Add to .gitignore
echo ".ha_token" >> .gitignore

# Use in script
python3 install-dashboards.py \
    --url http://homeassistant.local:8123 \
    --token "$(cat .ha_token)"
```

### 2. Token Rotation

Rotate tokens periodically:
1. Create new token in HA
2. Update scripts/env vars
3. Delete old token in HA

### 3. Network Security

**For remote installations:**
- Use HTTPS URLs only
- Consider VPN/tunnel for sensitive networks
- Restrict token to specific IP ranges (if HA supports)

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Dashboards

on:
  push:
    branches: [main]
    paths:
      - 'climate/home-assistant/dashboards/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install dependencies
        run: pip3 install pyyaml

      - name: Install dashboards
        env:
          HA_URL: ${{ secrets.HA_URL }}
          HA_TOKEN: ${{ secrets.HA_TOKEN }}
        run: |
          python3 climate/home-assistant/dashboards/install-dashboards.py \
            --url "$HA_URL" \
            --token "$HA_TOKEN"
```

### Docker Example

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY climate/home-assistant/dashboards/ ./dashboards/

ENV HA_URL=""
ENV HA_TOKEN=""

CMD python3 dashboards/install-dashboards.py \
    --url "$HA_URL" \
    --token "$HA_TOKEN"
```

---

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/lovelace/dashboards` | List all dashboards |
| GET | `/api/lovelace/dashboards/{id}` | Get dashboard metadata |
| GET | `/api/lovelace/dashboards/{id}/config` | Get dashboard config |
| POST | `/api/lovelace/dashboards` | Create dashboard |
| POST | `/api/lovelace/dashboards/{id}/config` | Set dashboard config |
| PUT | `/api/lovelace/dashboards/{id}` | Update dashboard metadata |
| DELETE | `/api/lovelace/dashboards/{id}` | Delete dashboard |

### Dashboard Metadata Schema

```json
{
  "url_path": "string",        // URL path (e.g., "climate-overview")
  "title": "string",            // Display title
  "icon": "string",             // MDI icon (e.g., "mdi:home")
  "show_in_sidebar": boolean,   // Show in sidebar?
  "require_admin": boolean      // Require admin access?
}
```

### Dashboard Config Schema

Follows standard Lovelace dashboard YAML structure converted to JSON.

See: https://www.home-assistant.io/lovelace/

---

## Comparison: API vs YAML Mode

| Feature | API Installation | YAML Mode |
|---------|-----------------|-----------|
| Installation | Run script once | Edit config.yaml + restart |
| Updates | Re-run script | Edit YAML + restart |
| Storage | HA internal (.storage) | YAML files |
| UI Editable | ✅ Yes | ❌ No (YAML only) |
| Version Control | Files + manual sync | ✅ Native |
| Automation | ✅ Easy (scripts) | Manual |
| Restart Required | ❌ No | ✅ Yes |
| Debugging | API errors | YAML syntax errors |

### When to Use Each

**API Installation** (Recommended for most users):
- Quick setup without config file changes
- Want UI editing capability
- Automated deployments
- Less technical users

**YAML Mode**:
- Want version-controlled dashboards
- Need exact control over config files
- Prefer infrastructure-as-code approach
- Advanced users

---

## FAQ

**Q: Can I switch from YAML mode to API mode later?**

A: Yes, but you'll need to remove the dashboard entries from `configuration.yaml` and restart HA first.

**Q: Will API-installed dashboards persist across HA restarts?**

A: Yes, they're stored in `.storage/lovelace.*` files.

**Q: Can I edit API-installed dashboards in the UI?**

A: Yes! That's one of the main benefits of storage mode.

**Q: What happens if I run the script twice?**

A: It detects existing dashboards and updates them (no duplicates).

**Q: How do I uninstall dashboards?**

A: Use the HA UI or delete via API:
```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://homeassistant.local:8123/api/lovelace/dashboards/climate-overview
```

**Q: Can I install just one dashboard?**

A: Yes, modify the script or use manual API calls.

---

## Support

For issues with:
- **Scripts**: Check this document's troubleshooting section
- **Home Assistant API**: See [HA Developer Docs](https://developers.home-assistant.io/docs/api/rest)
- **Dashboards**: See main README.md

---

**Last Updated**: January 25, 2026
**Version**: 1.0
