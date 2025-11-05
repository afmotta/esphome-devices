# Story 9.1: Master REST API Server

**Epic:** 9 - REST API-Based Board Communication  
**Story Type:** New Component Development  
**Estimated Effort:** 3-4 hours  
**Priority:** Critical (Foundation)  
**Date:** November 5, 2025

## Status
Draft

---

## User Story

As a **system owner**,  
I want **the gruppo-miscelazione master board to expose supply temperature and climate mode data via REST API endpoints**,  
So that **slave boards can poll sensor data directly without requiring Home Assistant as an intermediary**.

---

## Story Context

**System Integration:**

- **Creates:** `components/rest_api_master.yaml` - Reusable REST API server component
- **Modifies:** `devices/gruppo-miscelazione.yaml` - Add REST API server package
- **Technology:** ESPHome `web_server` component version 2 (JSON support)
- **Infrastructure:** HTTP server on port 80, mDNS hostname resolution
- **Touch points:**
  - Existing Dallas temperature sensors (supply temps piano terra/primo piano)
  - Existing climate mode text sensor
  - ESPHome native web_server component

**Architecture Pattern:**

- Master board becomes REST API server (gruppo-miscelazione)
- Exposes existing sensor data via HTTP JSON endpoints
- No changes to sensor logic, only adds web server layer
- Enables future slave boards to consume via `http_request` platform

---

## Acceptance Criteria

### Functional Requirements

1. **Web Server Configuration:**
   - ESPHome `web_server` component enabled
   - Port 80 (standard HTTP)
   - Version 2 (JSON API support)
   - mDNS enabled for `gruppo-miscelazione.local` hostname resolution

2. **Supply Temperature Endpoints:**
   - Endpoint: `GET /sensor/supply_temp_piano_terra`
   - Response format: `{"id": "sensor-supply_temp_piano_terra", "value": 42.5, "state": "42.5", "unit": "°C"}`
   - Endpoint: `GET /sensor/supply_temp_primo_piano`
   - Response format: Same JSON structure with primo piano value
   - Values reflect current Dallas sensor readings
   - Returns 404 if sensor not found, valid JSON if sensor unavailable (state: "unavailable")

3. **Climate Mode Endpoint:**
   - Endpoint: `GET /text_sensor/climate_mode`
   - Response format: `{"id": "text_sensor-climate_mode", "value": "heat", "state": "heat"}`
   - Values: "heat", "cool", "off", or current mode string
   - Reflects current climate mode text sensor value

4. **Web Interface (Optional):**
   - Web UI accessible at `http://gruppo-miscelazione.local/`
   - Displays all sensors and text sensors
   - Can be disabled if firmware size is a concern (use `include_internal: false`)

### Integration Requirements

5. **Component Packaging:**
   - Created as reusable component: `components/rest_api_master.yaml`
   - Accepts vars: None required (uses existing sensor IDs by convention)
   - Optional vars: `web_server_port` (default: 80), `web_server_auth` (default: false)
   - Header documentation explains purpose and exposed endpoints

6. **Device Integration:**
   - Package included in `devices/gruppo-miscelazione.yaml`
   - No breaking changes to existing functionality
   - Firmware compiles successfully with web_server enabled
   - Flash size within limits (<90% of available flash)

7. **Network Requirements:**
   - Board must have stable Ethernet or WiFi connection
   - Static IP or mDNS working for `.local` hostname resolution
   - No firewall blocking port 80

### Testing & Validation

8. **Browser Testing:**
   - Open `http://gruppo-miscelazione.local/` in browser
   - Verify web interface loads (if enabled)
   - Manually navigate to `/sensor/supply_temp_piano_terra`
   - Verify valid JSON response with current temperature value
   - Repeat for primo piano and climate_mode endpoints

9. **Command Line Testing (curl):**
   - Execute: `curl http://gruppo-miscelazione.local/sensor/supply_temp_piano_terra`
   - Verify JSON response matches browser
   - Execute: `curl http://gruppo-miscelazione.local/text_sensor/climate_mode`
   - Verify current climate mode returned

10. **Error Handling:**
    - Request invalid endpoint (e.g., `/sensor/nonexistent`)
    - Verify 404 response or appropriate error
    - Disconnect Dallas sensor temporarily
    - Verify endpoint returns JSON with state "unavailable" (not crash)

### Quality Requirements

11. **Code Quality:**
    - Component follows ESPHome best practices
    - Header comment documents exposed endpoints and usage
    - Minimal configuration required (convention over configuration)
    - Clear inline comments explaining web_server settings

12. **Documentation:**
    - Update epic brief with actual endpoint URLs
    - Document JSON response format for each endpoint
    - Add curl examples to story completion notes
    - Note firmware size impact (~10-20KB for web_server)

---

## Tasks / Subtasks

- [ ] **Task 1: Create REST API Master Component** (AC: 5, 11)
  - [ ] Create `components/rest_api_master.yaml`
  - [ ] Add `web_server` component configuration (port 80, version 2)
  - [ ] Add header documentation with endpoint list
  - [ ] Add optional vars with defaults (port, auth)
  - [ ] Verify YAML syntax

- [ ] **Task 2: Integrate with gruppo-miscelazione Device** (AC: 6)
  - [ ] Open `devices/gruppo-miscelazione.yaml`
  - [ ] Add package include for `rest_api_master.yaml`
  - [ ] Verify no breaking changes to existing config
  - [ ] Compile firmware and check flash size
  - [ ] Deploy to device

- [ ] **Task 3: Browser Testing** (AC: 8)
  - [ ] Open `http://gruppo-miscelazione.local/` in browser
  - [ ] Verify web interface loads
  - [ ] Navigate to `/sensor/supply_temp_piano_terra`
  - [ ] Verify JSON response with valid temperature
  - [ ] Navigate to `/sensor/supply_temp_primo_piano`
  - [ ] Verify JSON response with valid temperature
  - [ ] Navigate to `/text_sensor/climate_mode`
  - [ ] Verify JSON response with current mode
  - [ ] Screenshot endpoints for documentation

- [ ] **Task 4: curl Command Line Testing** (AC: 9)
  - [ ] Execute `curl http://gruppo-miscelazione.local/sensor/supply_temp_piano_terra`
  - [ ] Verify JSON matches browser output
  - [ ] Execute curl for primo piano endpoint
  - [ ] Execute curl for climate_mode endpoint
  - [ ] Document curl commands in completion notes

- [ ] **Task 5: Error Handling Validation** (AC: 10)
  - [ ] Request invalid endpoint URL
  - [ ] Verify 404 or appropriate error response
  - [ ] Temporarily disconnect Dallas sensor (if safe)
  - [ ] Verify endpoint returns unavailable state (not crash)
  - [ ] Restore sensor connection

- [ ] **Task 6: Documentation Updates** (AC: 12)
  - [ ] Update epic brief with actual endpoint URLs
  - [ ] Document JSON response format examples
  - [ ] Add curl usage examples
  - [ ] Note firmware size impact
  - [ ] Create completion notes with screenshots

---

## Dev Notes

### Relevant Source Tree

**Existing Components:**
- `components/dallas.yaml` - Dallas temperature sensors, provides `supply_temp_piano_terra` and `supply_temp_primo_piano` sensor IDs
- `components/mev.yaml` - MEV component with climate mode coordination
- `boards/a16_ethernet.yaml` - Hardware board with Ethernet connectivity

**Device Configuration:**
- `devices/gruppo-miscelazione.yaml` - Master board device file, includes packages for Dallas sensors, mixing valves, MEV
- `locals/gruppo-miscelazione.yaml` - Local configuration with secrets and specific device settings

**Key Sensor IDs (from architecture):**
- `supply_temp_piano_terra` - Dallas sensor for ground floor supply temperature
- `supply_temp_primo_piano` - Dallas sensor for first floor supply temperature
- `climate_mode` - Text sensor showing current climate mode (heat/cool/off)

### ESPHome web_server Component Reference

**Basic Configuration:**
```yaml
web_server:
  port: 80
  version: 2  # Enables JSON API
  # Optional:
  # auth:
  #   username: admin
  #   password: !secret web_server_password
  # include_internal: false  # Hide internal sensors from web UI
```

**Endpoint URL Pattern:**
- Sensors: `/sensor/{sensor_id}`
- Text Sensors: `/text_sensor/{text_sensor_id}`
- Binary Sensors: `/binary_sensor/{binary_sensor_id}`

**JSON Response Format:**
```json
{
  "id": "sensor-supply_temp_piano_terra",
  "value": 42.5,
  "state": "42.5",
  "unit": "°C"
}
```

**mDNS Hostname:**
- Configured in `esphome` section as `name: gruppo-miscelazione`
- Accessible as `http://gruppo-miscelazione.local/`

### Epic 9 Architecture Context

**Current State (Epic 5):**
- Room sensors sourced from Home Assistant via `homeassistant` platform
- Supply temps shared via HA (gruppo-miscelazione → HA → distribuzione boards)
- Single point of failure when HA restarts

**Epic 9 Goal:**
- Direct ESPHome-to-ESPHome communication via REST API
- Eliminate HA as sensor data intermediary
- Maintain HA for monitoring and overrides only

**Story 9.1 Deliverable:**
- Master board exposes REST endpoints
- No consumer changes yet (Story 9.2 will create slave clients)
- Validates REST API works before slave integration

### Firmware Size Considerations

**web_server Component Impact:**
- Adds ~10-20KB to firmware size
- Includes HTTP server, JSON serialization, web UI assets
- Monitor flash usage during compilation
- If >90% flash used, disable web UI with `include_internal: false`

**Mitigation if Flash Constrained:**
- Disable web UI (keep JSON API only)
- Reduce log levels
- Remove unnecessary components

### Testing Standards

**Manual Testing Required:**
- Web browser testing (visual inspection)
- curl command line testing (automation ready)
- Error handling verification (robustness)

**Success Criteria:**
- All endpoints return valid JSON
- Temperature values match ESPHome logs
- Climate mode matches current system state
- No firmware crashes or restarts

**Test Environment:**
- Physical gruppo-miscelazione board (A16 Ethernet)
- Stable network connection (Ethernet preferred)
- Dallas sensors operational
- Climate system in known state (heat/cool/off)

### Known Dependencies

**Requires:**
- Epic 5 completed (HA sensor baseline)
- gruppo-miscelazione board operational
- Dallas sensors functional
- Ethernet/WiFi connected
- mDNS working on local network

**Blocks:**
- Story 9.2 (Slave REST Client) - Needs master endpoints available
- Story 9.3 (Failover Logic) - Needs REST API baseline
- Story 9.4 (Reliability Testing) - Needs full REST implementation

### Security Considerations

**MVP Approach:**
- No authentication (local network only)
- No SSL/TLS (plaintext HTTP)
- Trust-based security model

**Future Enhancements (Out of Scope):**
- Basic auth with username/password
- API keys for service-to-service auth
- SSL/TLS with self-signed certificates

**Acceptable Risk:**
- Local network is trusted
- No exposure to internet
- Physical security sufficient for now

---

## Change Log

| Date       | Version | Description            | Author     |
| ---------- | ------- | ---------------------- | ---------- |
| 2025-11-05 | 1.0     | Initial story creation | Sarah (PO) |

---

## Dev Agent Record

### Agent Model Used
*To be populated during implementation*

### Debug Log References
*To be populated during implementation*

### Completion Notes List
*To be populated during implementation*

### File List
*To be populated during implementation*

---

## QA Results

*To be populated after QA review*

---

**Story Status:** Draft - Ready for Development  
**Next Story:** 9.2 - Slave REST Client (depends on 9.1 completion)
