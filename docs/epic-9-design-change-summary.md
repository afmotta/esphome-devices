# Epic 9 Design Change Summary

**Date:** November 5, 2025  
**Change Type:** Scope Refinement - Equipment-Aware Control Strategy  
**Status:** Updated Brief, Stories Need Revision

---

## Original Scope (Rejected)

**Simple Approach:** All rooms shut down (PID OFF) when unoccupied

**Problem Identified:**
- Radiant heating/cooling systems have **30-60 minute response time**
- Complete shutdown causes:
  - Long recovery when room becomes occupied (30-60 min to restore comfort)
  - User discomfort: "Room is freezing when I enter"
  - Thermal shock to building structure
  - High energy spike on restart (vs. maintaining reduced setpoint)
- One-size-fits-all approach doesn't account for equipment differences

---

## Updated Scope (Approved)

**Equipment-Aware Approach:** Different strategies based on equipment type

### Fancoil Rooms (Fast Response)
- **Strategy:** Force PID OFF when unoccupied (complete shutdown)
- **Rationale:** 5-10 minute response time, can handle ON/OFF cycling
- **Recovery:** 5-10 minutes to comfort when occupied
- **Energy Savings:** 15-25% (full shutdown)
- **Example Rooms:** Bedrooms with fancoils, bathrooms

### Radiant Rooms (Slow Response)
- **Strategy:** Reduce setpoint when unoccupied (partial reduction)
- **Heating:** 21°C → 18°C (-3°C offset)
- **Cooling:** 25°C → 28°C (+3°C offset)
- **Rationale:** Maintains thermal mass, prevents long recovery times
- **Recovery:** 15-20 minutes to comfort when occupied (vs. 30-60 min if fully shut down)
- **Energy Savings:** 8-12% (setpoint reduction, less than shutdown but maintains comfort)
- **Example Rooms:** Living rooms, large spaces with radiant-only

### Mixed Equipment Rooms (Fancoil + Radiant)
- **Strategy:** Treat as fancoil (fast response dominates)
- **Alternative:** Configurable per room based on user comfort preference

---

## Key Changes to Epic 9 Brief

### Title Updated
- **Before:** "Epic 9 - Occupancy-Based Climate Shutdown"
- **After:** "Epic 9 - Occupancy-Based Climate Optimization"

### Executive Summary
- Added equipment-aware control explanation
- Clarified fancoil vs. radiant strategies
- Updated energy savings expectations (blended 10-20%)

### Problem Statement
- Added "System Equipment Context" section explaining radiant vs. fancoil characteristics
- Updated pain points to include equipment mismatch issues

### Core Concept
- Split into two strategies: Fancoil (OFF) vs. Radiant (setpoint reduction)
- Added coordinator enhancement note (setpoint offset support)

### Key Architecture Decisions
- **NEW Decision #1:** Equipment-aware response strategy (critical design decision)
- Renumbered subsequent decisions
- Updated recovery behavior to explain fancoil vs. radiant differences

### MVP Scope
- Updated occupancy condition component features:
  - Added `equipment_type` var (fancoil/radiant)
  - Added fancoil mode (force OFF) and radiant mode (setpoint offset)
  - Updated diagnostic messages
- Updated single-room validation to test BOTH equipment types
- Updated migration guide to include equipment type selection

### Out of Scope
- **Removed:** "Partial Shutdown" (now IN scope for radiant rooms)
- **Added:** "Per-Room Equipment Detection" (manual configuration required)

### Post-MVP Vision (Epic 10)
- Updated to clarify Epic 9 already implements setpoint reduction
- Epic 10 will add **dynamic** adjustment based on energy state

### New Appendix F
- Equipment types and room classification
- Room-by-room equipment audit template
- Expected savings by equipment type

---

## Impact on Stories 9.1-9.5

### Story 9.1: Occupancy Condition Component
**Changes Required:**
- [ ] Add `equipment_type` var (fancoil/radiant)
- [ ] Add `setpoint_offset_heating` var (default: -3)
- [ ] Add `setpoint_offset_cooling` var (default: +3)
- [ ] Implement two control paths:
  - Fancoil: Set `force_pid_off` flag (coordinator reads this)
  - Radiant: Set `setpoint_offset` value (coordinator applies offset)
- [ ] Update diagnostic text sensor messages:
  - "Unoccupied (Fancoil OFF)" vs "Unoccupied (Radiant Reduced)"
- [ ] Update acceptance criteria to test both equipment types

### Story 9.2: Occupancy Stub Component
**Changes Required:**
- [ ] Add `equipment_type` var (for consistency, though stub never activates)
- [ ] Update documentation

### Story 9.3: Single-Room Validation
**Changes Required:**
- [ ] Test TWO rooms instead of one:
  - Test Room 1: Fancoil-equipped room (test OFF strategy)
  - Test Room 2: Radiant-only room (test setpoint reduction strategy)
- [ ] Add comfort validation for radiant room:
  - Measure recovery time (target: 15-20 min vs. 30-60 min baseline)
  - User feedback: "Room comfortable when entering?" 
- [ ] Update acceptance criteria with equipment-specific tests

### Story 9.4: Multi-Room Rollout
**Changes Required:**
- [ ] Add equipment audit phase:
  - Document which rooms have fancoils, radiant, or mixed
  - Determine occupancy strategy per room
- [ ] Update room configurations with `equipment_type` var
- [ ] Separate energy savings tracking:
  - Fancoil rooms: expect 15-25% savings
  - Radiant rooms: expect 8-12% savings
  - System-wide: blended 10-20% average
- [ ] Update migration guide with equipment type selection process

### Story 9.5: Completion Documentation
**Changes Required:**
- [ ] Update completion report with equipment-aware results
- [ ] Document per-equipment-type energy savings
- [ ] Update migration guide with equipment classification
- [ ] Add lessons learned about equipment-specific optimization
- [ ] Update energy dashboard to show fancoil vs. radiant performance

---

## Coordinator Enhancement Required

### Current Coordinator (Epic 8)
- Reads `${zone_slug}_${condition}_state` and `${zone_slug}_${condition}_priority`
- Forces PID OFF when any condition Active/Recovering

### Updated Coordinator (Epic 9)
**Option 1: Extend Globals Pattern**
- Add new global: `${zone_slug}_${condition}_setpoint_offset` (float, default: 0.0)
- Coordinator reads setpoint offset alongside state/priority
- When condition Active:
  - If setpoint_offset == 0.0: Force PID OFF (fancoil behavior)
  - If setpoint_offset != 0.0: Apply offset to PID setpoint (radiant behavior)

**Option 2: Equipment-Aware State**
- Keep current globals
- Add `${zone_slug}_equipment_type` global (string: "fancoil" or "radiant")
- Coordinator reads equipment type and applies appropriate control

**Recommendation:** Option 1 (setpoint offset) is more flexible and extensible for Epic 10

### Coordinator Modification Impact
- **Previously claimed:** "Zero coordinator modifications required"
- **Now requires:** Coordinator enhancement to support setpoint offsets
- **Mitigation:** Still follows Epic 8 interface contract (extends, doesn't break)
- **Benefit:** Enables equipment-aware control without per-room coordinator logic

---

## Testing Strategy Updates

### Story 9.3 Testing
**Before:** 1 test room (Soggiorno), 7 days validation  
**After:** 2 test rooms (1 fancoil + 1 radiant), 7 days validation each

**Test Room 1 (Fancoil):**
- Example: Camera Matrimoniale (bedroom with fancoil)
- Validation: PID forces OFF when unoccupied
- Recovery time: 5-10 minutes to comfort
- Energy savings: 15-25%

**Test Room 2 (Radiant):**
- Example: Soggiorno (living room with radiant-only)
- Validation: Setpoint reduced when unoccupied (21°C → 18°C)
- Recovery time: 15-20 minutes to comfort (vs. 30-60 min baseline)
- Energy savings: 8-12%
- **Critical:** User feedback on comfort ("Room too cold when entering?")

---

## Risk Assessment Updates

### New Risks Added

**Risk: Radiant Room Comfort Complaints**
- **Likelihood:** Medium (depends on setpoint offset tuning)
- **Impact:** High (user trust, adoption)
- **Mitigation:**
  - Conservative setpoint offset (start with -3°C, adjust per room)
  - Test room validation before rollout
  - User feedback collection during Story 9.3
  - Option to configure per room (-2°C, -3°C, -4°C)
- **Fallback:** Switch problematic radiant rooms to fancoil strategy (force OFF)

**Risk: Setpoint Offset Insufficient Savings**
- **Likelihood:** Low-Medium (radiant rooms may save <10%)
- **Impact:** Medium (reduces overall system savings)
- **Mitigation:**
  - Prioritize fancoil rooms for occupancy detection first (higher ROI)
  - Consider larger setpoint offsets for radiant rooms (-4°C vs. -3°C)
  - Epic 10 can add dynamic adjustment based on energy state
- **Acceptance:** 8-12% radiant savings still valuable, combined with fancoil savings achieves 10-20% target

### Risks Removed/Mitigated

**Risk: Long Recovery Times (Previously High)**
- **Status:** Mitigated by equipment-aware control
- **Before:** All rooms force OFF → 30-60 min recovery for radiant
- **After:** Radiant rooms use setpoint reduction → 15-20 min recovery

---

## Implementation Complexity Assessment

### Complexity Increase
- **Story 9.1:** +1 story point (equipment-aware logic, two control paths)
- **Story 9.3:** +1 story point (test two rooms instead of one)
- **Story 9.4:** +0.5 story points (equipment audit, per-room classification)
- **Story 9.5:** +0 story points (documentation update, same effort)

**Total:** 9 story points → 11.5 story points (+28% increase)

**Still Better Than Pre-Epic 8:** 11.5 points (Epic 9 with equipment-aware) vs. 15-20 points (pre-Epic 8 equivalent)

### Benefit Increase
- **User Comfort:** Significantly improved (no 30-60 min recovery times)
- **Energy Savings:** Maintained (10-20% system-wide target still achievable)
- **Adoption Risk:** Reduced (user complaints about cold rooms prevented)
- **System Quality:** Increased (equipment-appropriate control)

**Recommendation:** Accept 28% complexity increase for significantly better user experience and reduced adoption risk

---

## Next Steps

### Immediate Actions
1. **[ ] Finalize equipment-aware design:** Review and approve updated Epic 9 brief
2. **[ ] Audit room equipment:** Document fancoil vs. radiant per room (15+ rooms)
3. **[ ] Update Stories 9.1-9.5:** Revise acceptance criteria, test plans, configurations
4. **[ ] Select test rooms:** 
   - Test Room 1 (Fancoil): Camera Matrimoniale or similar
   - Test Room 2 (Radiant): Soggiorno or similar
5. **[ ] Coordinator enhancement design:** Define setpoint offset globals and coordinator logic

### Implementation Sequence
1. Update Story 9.1 (component) with equipment-aware vars
2. Update Story 9.3 (validation) with two-room test plan
3. Validate both strategies in parallel (fancoil + radiant)
4. Proceed to Story 9.4 (rollout) only if both strategies successful
5. Story 9.5 (documentation) includes equipment-specific results

---

## Conclusion

**Design Change Rationale:** Equipment-aware control is **essential for user comfort** and system adoption. Radiant systems cannot handle aggressive ON/OFF cycling without causing significant user discomfort (30-60 min recovery times). The updated approach balances energy savings with comfort by using equipment-appropriate strategies.

**Impact:** +28% implementation complexity, but significantly improved user experience and reduced adoption risk. Still 40-50% faster than pre-Epic 8 equivalent.

**Recommendation:** **Approve updated Epic 9 scope** with equipment-aware control. The additional complexity is justified by the comfort improvement and is still leveraging Epic 8's extensible architecture effectively.

---

**Change Approved By:** [Pending Review]  
**Date:** 2025-11-05  
**Next Review:** After Story 9.3 validation (test both equipment strategies)
