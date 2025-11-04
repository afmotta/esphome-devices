# Epic 8: User Stories Index

**Epic:** 8 - Unified State Machine Architecture  
**Date:** October 31, 2025  
**Total Stories:** 5  
**Estimated Total Effort:** 18-22 hours

---

## Story Overview

### Foundation Stories (Critical Path)

**Story 8.1: Emergency Condition Component** ✅  
- **File:** `8.1-emergency-condition-component.md`
- **Effort:** 4 hours
- **Summary:** Refactor Epic 5 emergency detection into interface-compliant condition component
- **Deliverable:** `components/room_emergency_condition.yaml`
- **Status:** Created

**Story 8.2: Window Condition Component**  
- **Effort:** 4-6 hours
- **Summary:** Refactor Epic 7 window detection into interface-compliant condition component with mode-awareness
- **Deliverable:** `components/room_window_condition.yaml`
- **Status:** To be created

**Story 8.3: Coordinator Component**  
- **Effort:** 6-8 hours
- **Summary:** Create stateless coordinator that reads condition states and controls PID via priority hierarchy
- **Deliverable:** `components/room_control_coordinator.yaml`
- **Status:** To be created

### Migration Stories

**Story 8.4: Test Room Migration**  
- **Effort:** 3-4 hours
- **Summary:** Migrate single test room (Soggiorno) from Epic 5/7 to Epic 8 architecture, validate 48-72h
- **Deliverable:** Updated `components/rooms/first_floor/soggiorno.yaml`, validation report
- **Status:** To be created

**Story 8.5: Production Rollout**  
- **Effort:** 1-2 hours
- **Summary:** Migrate remaining 5+ rooms using phased rollout strategy, deprecate old components
- **Deliverable:** All rooms on Epic 8, completion report
- **Status:** To be created

---

## Story Dependencies

```
8.1 (Emergency) ──┐
                  ├──> 8.3 (Coordinator) ──> 8.4 (Test Room) ──> 8.5 (Rollout)
8.2 (Window) ─────┘
```

**Critical Path:** 8.1 → 8.3 → 8.4 → 8.5  
**Parallel Work:** 8.1 and 8.2 can be developed simultaneously

---

## Acceptance Criteria Summary

### Story 8.1: Emergency Condition ✅
- [x] Exposes `${zone_slug}_emergency_state` (0/1/2) and `${zone_slug}_emergency_priority` (1)
- [x] Implements 3-state machine (Normal → Active → Recovering)
- [x] Monitors HA temperature sensor with 180s/60s timeouts
- [x] No PID control logic
- [x] Interface spec compliant

### Story 8.2: Window Condition
- [ ] Exposes `${zone_slug}_window_state` (0/1/2) and `${zone_slug}_window_priority` (2)
- [ ] Implements mode-aware triggering (only in configured modes)
- [ ] Monitors HA window binary_sensor with 180s/60s timeouts
- [ ] No PID control logic
- [ ] Interface spec compliant

### Story 8.3: Coordinator
- [ ] Reads all condition states every 5s
- [ ] Applies priority hierarchy (emergency=1 > window=2)
- [ ] Forces PID OFF when any condition Active/Recovering
- [ ] Exposes diagnostic text_sensor showing active condition
- [ ] HA-driven resume strategy (MVP)

### Story 8.4: Test Room Migration
- [ ] Soggiorno migrated to Epic 8 architecture
- [ ] All 3 components deployed and operational
- [ ] Manual testing: emergency trigger/clear (3+ cycles)
- [ ] Manual testing: window trigger/clear (3+ cycles)
- [ ] Manual testing: priority hierarchy (simultaneous triggers)
- [ ] 48-72h soak test passed
- [ ] Rollback procedure validated

### Story 8.5: Production Rollout
- [ ] Remaining 5+ rooms migrated (1 room/day cadence)
- [ ] Old Epic 5/7 components deprecated
- [ ] Documentation updated
- [ ] Completion report created
- [ ] 40% code reduction achieved

---

## Risk Summary

| Story | Primary Risk | Mitigation |
|-------|--------------|------------|
| 8.1 | State machine bug causes stuck Active | Extensive testing, logging, quick rollback |
| 8.2 | Mode-awareness error causes false triggers | Test all mode combinations, log checks |
| 8.3 | Priority resolution error | Unit test priority algorithm, log decisions |
| 8.4 | Migration breaks Soggiorno climate control | Validation criteria, immediate rollback plan |
| 8.5 | Cascade failure affects multiple rooms | Staggered rollout (1/day), stop-on-error |

---

## Success Metrics

**Code Quality:**
- 40% reduction in PID control logic duplication
- Single source of truth for coordination (coordinator only)
- Interface contract enables future extensibility

**Production Reliability:**
- Zero downtime during migration
- No climate control quality regression
- All rooms operational within 3-week timeline

**Architecture:**
- Extensible foundation for Epic 9+ (occupancy, maintenance conditions)
- Clear separation of concerns (detection vs. control)
- Improved observability (coordinator status sensor)

---

## Timeline

**Week 1:**
- Day 1-2: Stories 8.1 + 8.2 (parallel development)
- Day 3: Story 8.3 (coordinator)
- Day 4-7: Story 8.4 (test room + validation)

**Week 2:**
- Day 8-14: Story 8.5 (phased rollout, 1 room/day)

**Week 3:**
- Day 15-21: Documentation, deprecation, completion report

---

## References

- **Interface Spec:** `docs/epic-8-condition-interface-spec.md`
- **Coordinator Design:** `docs/epic-8-coordinator-design.md`
- **Migration Strategy:** `docs/epic-8-migration-strategy.md`
- **Project Brief:** `docs/epic-8-brief.md`
- **Brainstorming Session:** `docs/epic-8-brainstorming-session.md`

---

**Status:** Story 8.1 complete ✅, remaining stories ready for creation  
**Next Action:** Create Story 8.2 (Window Condition Component)

---

*Epic 8 stories index - Unified State Machine Architecture*
