# Troubleshooting Connection Issues

Quick guide for resolving "No route to host" and other connection errors.

## Error: "No route to host" (Errno 65)

This means your computer cannot establish a network connection to Home Assistant.

### Quick Fixes (Try These First)

#### 1. Find Your Home Assistant IP Address

**In Home Assistant:**
1. Go to **Settings → System → Network**
2. Note the IP address (e.g., `192.168.1.100`)

**Alternative - From your router:**
1. Log into your router's admin panel
2. Look for "Connected Devices" or "DHCP Clients"
3. Find "homeassistant" in the list

**Alternative - Use network scan:**
```bash
# On Linux/Mac
arp -a | grep -i homeassistant

# Or use nmap
nmap -sn 192.168.1.0/24 | grep -B 2 homeassistant
```

#### 2. Use IP Address Instead of Hostname

```bash
# Instead of:
python3 install-dashboards.py \
    --url http://homeassistant.local:8123 \
    --token YOUR_TOKEN

# Use:
python3 install-dashboards.py \
    --url http://192.168.1.100:8123 \
    --token YOUR_TOKEN
```

#### 3. Test Connection Manually

```bash
# Test if you can reach Home Assistant
curl http://192.168.1.100:8123/api/

# Should return:
# {"message": "API running."}
```

#### 4. Check Port Number

Home Assistant usually runs on port **8123**. If yours is different:

```bash
# Use your custom port
python3 install-dashboards.py \
    --url http://192.168.1.100:8124 \
    --token YOUR_TOKEN
```

---

## Common Connection Errors

### Error: "Connection refused" (Errno 61)

**Cause**: Home Assistant is not running or not listening on that port.

**Fix:**
1. Check if Home Assistant is running (open in browser)
2. Verify the port number
3. Check if Home Assistant is bound to correct network interface

### Error: "Name or service not known" (Errno -2)

**Cause**: The hostname `homeassistant.local` cannot be resolved.

**Fix:**
1. Use IP address instead of hostname (see above)
2. Or ensure mDNS is working on your network

```bash
# Test mDNS resolution
ping homeassistant.local
```

### Error: "Network is unreachable" (Errno 101)

**Cause**: Your computer cannot reach the network Home Assistant is on.

**Fix:**
1. Ensure you're on the same WiFi/network as Home Assistant
2. Check VPN settings (disable VPN if active)
3. Verify network settings

### Error: "Operation timed out" (Errno 60)

**Cause**: Connection attempt is timing out (firewall or network issue).

**Fix:**
1. Check firewall rules on Home Assistant host
2. Check router/network firewall
3. Try increasing timeout in script
4. Ensure Home Assistant is accessible on your network

---

## Step-by-Step Diagnostic

### Step 1: Verify Home Assistant is Running

Open a web browser and go to:
```
http://homeassistant.local:8123
```

Or with IP:
```
http://192.168.1.100:8123
```

**Expected**: You should see the Home Assistant login page.
**If not**: Home Assistant is not running or not accessible.

### Step 2: Test API Endpoint

```bash
curl http://192.168.1.100:8123/api/
```

**Expected output:**
```json
{"message": "API running."}
```

**If you get an error:**
- Connection refused → Home Assistant not running
- Timeout → Network/firewall issue
- 404 Not Found → Wrong URL

### Step 3: Test with Authentication

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://192.168.1.100:8123/api/config
```

**Expected**: JSON response with Home Assistant configuration.

**If you get:**
- `{"message":"Invalid authentication"}` → Token is wrong
- Connection error → See Step 2
- 401 Unauthorized → Token expired or invalid

### Step 4: Check Python Network Access

```bash
python3 -c "
import urllib.request
try:
    response = urllib.request.urlopen('http://192.168.1.100:8123/api/')
    print('Success:', response.read().decode('utf-8'))
except Exception as e:
    print('Error:', e)
"
```

**Expected**: `Success: {"message": "API running."}`

---

## Network Configuration Issues

### Using Home Assistant on Different Network

If Home Assistant is on a different subnet or network:

1. **Check if you can ping it:**
   ```bash
   ping 192.168.1.100
   ```

2. **Check routing:**
   ```bash
   traceroute 192.168.1.100
   ```

3. **Use VPN or port forwarding if needed**

### Home Assistant in Docker/VM

If HA is in Docker or VM:

1. **Check port mapping:**
   ```bash
   docker ps | grep homeassistant
   # Look for port mapping like 0.0.0.0:8123->8123/tcp
   ```

2. **Use host IP, not container IP:**
   ```bash
   # Use your computer's IP, not 127.0.0.1
   python3 install-dashboards.py \
       --url http://192.168.1.50:8123 \
       --token YOUR_TOKEN
   ```

### Home Assistant OS on Different Machine

If HA is running on a Raspberry Pi or other device:

1. **Find the device IP:**
   - Check your router's DHCP clients
   - Check the device's network settings
   - Use network scanner

2. **Ensure both devices are on same network:**
   - Same WiFi SSID
   - Same subnet (both 192.168.1.x)

---

## Firewall Issues

### macOS Firewall

```bash
# Check if Python is blocked
# System Preferences → Security & Privacy → Firewall → Firewall Options
# Allow Python to accept incoming connections
```

### Linux iptables/firewalld

```bash
# Check if port is open
sudo iptables -L -n | grep 8123

# Or with firewalld
sudo firewall-cmd --list-all
```

### Windows Firewall

1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Find Python and ensure it's allowed

---

## Home Assistant Configuration

### Check Home Assistant Network Binding

In Home Assistant's `configuration.yaml`:

```yaml
http:
  server_host: 0.0.0.0  # Listen on all interfaces
  server_port: 8123
```

Restart Home Assistant after changes.

### Check Home Assistant Logs

In Home Assistant:
1. Go to **Settings → System → Logs**
2. Look for network-related errors
3. Check for port binding issues

---

## Alternative: Use Bash Script

If Python networking isn't working, try the bash script:

```bash
./install-dashboards.sh http://192.168.1.100:8123 YOUR_TOKEN
```

---

## Still Not Working?

### Run Installation from Home Assistant Server

If you can SSH into the Home Assistant host:

```bash
# SSH into Home Assistant
ssh root@homeassistant.local

# Install dashboards locally
cd /config
pip3 install pyyaml

# Run script using localhost
python3 install-dashboards.py \
    --url http://localhost:8123 \
    --token YOUR_TOKEN
```

### Use Home Assistant File Editor

1. Install "File Editor" addon in Home Assistant
2. Copy dashboard YAML files to `/config/www/dashboards/`
3. Use manual API calls from Home Assistant Terminal addon

### Manual Installation via UI

As a last resort, manually copy each dashboard:

1. Go to **Settings → Dashboards → Add Dashboard**
2. Choose "New dashboard from scratch"
3. Open in edit mode → Three dots → Raw configuration editor
4. Copy/paste content from each YAML file
5. Save

---

## Get Help

If none of these work, gather this info for support:

```bash
# System info
python3 --version
uname -a  # or 'ver' on Windows

# Network test
ping 192.168.1.100
curl -v http://192.168.1.100:8123/api/

# Python test
python3 -c "import urllib.request; print(urllib.request.urlopen('http://google.com').status)"

# Home Assistant version
# From HA: Settings → System → About
```

Post this info along with the exact error message to get help.
