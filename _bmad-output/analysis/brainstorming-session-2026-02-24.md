---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'Standardizing entity ID naming conventions across the ESPHome codebase'
session_goals: 'Define a single, clear convention for entity ID structure (component ordering: room/location, function type, variant) and apply it uniformly'
selected_approach: 'ai-recommended'
techniques_used: ['Morphological Analysis', 'First Principles Thinking', 'Assumption Reversal']
ideas_generated: [10]
context_file: ''
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Facilitator:** Alberto
**Date:** 2026-02-24

## Session Overview

**Topic:** Standardizing entity ID naming conventions across the ESPHome codebase
**Goals:** Define a single, clear convention for entity ID structure (component ordering: room/location, function type, variant) and apply it uniformly

### Session Setup

_Alberto wants to resolve inconsistent entity ID naming where the room/location component appears in different positions (prefix, middle, suffix) across entities. The goal is to establish one coherent pattern and refactor the codebase to follow it._

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** Entity ID naming standardization with focus on coherent component ordering

**Recommended Techniques:**

- **Morphological Analysis:** Map all naming dimensions (location, component type, variant, mode) and their possible orderings systematically
- **First Principles Thinking:** Strip away inherited assumptions and rebuild the convention from fundamental requirements (readability, sortability, HA integration, ESPHome constraints)
- **Assumption Reversal:** Pressure-test the top candidate conventions by flipping each assumption to catch blind spots

## Technique Execution Results

### Morphological Analysis

**Interactive Focus:** Identifying and mapping all dimensions of entity IDs, exploring all possible orderings, and converging on the optimal structure.

**Key Findings:**

- **[Morphological #1] Three-Dimension Model:** Zone entity IDs are composed of Scope + Component + (optional) Mode. Board-level hardware entities (relay_1, dac_output_1) are excluded from the convention.
- **[Morphological #2] Room-First Mental Model:** Alberto's natural mental model is room-first ("what's happening in soggiorno?"), not system-first. Convention should mirror cognition.
- **[Morphological #3] Four-Segment Pattern with Trailing Qualifiers:** Initial exploration revealed a possible 4th dimension for diagnostic aspects (output, setpoint, kp, status) that reads general → specific.
- **[Morphological #4] PID as Mode, Not Aspect:** PID belongs in the Mode dimension alongside heat/cool/boost. It describes how the component operates — "radiant under PID control" — not a view into it.
- **[Morphological #5] Three Dimensions Are Sufficient:** One PID per radiant that switches mode internally eliminates the need for sub-modes. Core entities need max 3 segments.
- **[Morphological #6] Four Dimensions Confirmed — Aspect for Diagnostics:** The 4th segment (aspect) is real but only applies to diagnostic/parameter entities (output, setpoint, kp, ki, kd, status) that describe properties of a core entity.

### First Principles Thinking

**Interactive Focus:** Stress-testing the convention against real-world constraints and requirements.

**Key Findings:**

- **[First Principles #1] Alphabetical Sort Alignment:** `scope_component_mode_aspect` naturally clusters entities by room in HA alphabetical listings, aligning sort order with the user's room-first mental model. No artificial prefixes needed.
- **[First Principles #2] Zero Architecture Impact:** The pattern works with existing `${slug}` substitution and `!include` vars as-is. Adoption requires renaming, not restructuring.
- **[First Principles #3] Low Migration Cost:** No downstream HA automation breakage. The refactoring scope is contained entirely within the ESPHome codebase.
- **[First Principles #4] No Collision Risk:** Unique room names + single instances per component type per scope guarantee uniqueness without needing additional disambiguation.

### Assumption Reversal

**Interactive Focus:** Deliberately trying to break the convention by flipping every core assumption.

**Key Findings:**

- **[Assumption Reversal #1] Room-First Survives System-Wide Debugging:** System-wide failures are diagnosed at higher-level components (pumps, mixing valves, master registers), not by scanning room entities. Room-first naming is validated.
- **[Assumption Reversal #2] Single-Token Mode — Watch Point:** The convention assumes each dimension is one underscore-delimited token. Holds today, but multi-word modes would create ambiguity. Conscious constraint to keep in mind.
- **[Assumption Reversal #3] No Aspect-Mode Nesting:** Single PID per radiant with internal mode switching means aspects never need their own mode qualifier. 4 segments is the true maximum.
- **[Assumption Reversal #4] Clean Scope Boundary:** Every entity is either room-scoped or floor-scoped, never both. The physical architecture enforces this.
- **[Assumption Reversal #5] Convention Scoped to Entity IDs Only:** File names, variable names, and package structure are separate concerns with their own conventions.

### Creative Facilitation Narrative

_This session followed a tight analytical arc: Morphological Analysis mapped the full design space and identified the 4-dimension model, First Principles validated it against every real-world constraint, and Assumption Reversal tried to destroy it from five angles. The convention survived intact with only one minor watch point (single-token modes). The key breakthrough was Alberto's insight that PID is a mode of operation ("radiant under PID control"), not a separate component or aspect — this simplified the model and eliminated dimensional nesting._

## Idea Organization and Prioritization

### The Final Convention

**Pattern:** `{scope}_{component}[_{mode}][_{aspect}]`

| Position | Dimension | Required | Examples |
|----------|-----------|----------|---------|
| 1st | Scope | Yes | `soggiorno`, `cucina`, `camera_nord`, `ground_floor` |
| 2nd | Component | Yes | `radiant`, `fancoil`, `mev`, `pump`, `mixing` |
| 3rd | Mode | Optional | `heat`, `cool`, `pid`, `boost` |
| 4th | Aspect | Optional | `output`, `setpoint`, `kp`, `ki`, `kd`, `status` |

**Rules:**

1. Room names are atomic tokens (e.g., `camera_nord` is one slug, not two dimensions)
2. Floor scope is only used when no room applies (entity is floor-scoped)
3. Board-level hardware entities (`relay_1`, `dac_output_1`) are excluded — they keep their own convention
4. Each dimension is always a single underscore-delimited token
5. Convention applies to entity IDs only — file names and variable names are separate concerns

**Example Entity IDs:**

```
soggiorno_radiant
soggiorno_radiant_heat
soggiorno_radiant_cool
soggiorno_radiant_pid
soggiorno_radiant_pid_output
soggiorno_radiant_pid_setpoint
soggiorno_radiant_pid_kp
soggiorno_fancoil
soggiorno_fancoil_boost
soggiorno_fancoil_boost_status
cucina_radiant
cucina_radiant_pid
camera_nord_radiant
camera_nord_radiant_pid
ground_floor_mev
ground_floor_mev_status
first_floor_pump
```

### Watch Points

- **Multi-word modes:** If a future mode requires two words, choose a single compound token (e.g., `autoheat`) or revisit the convention

### Validation Summary

| Criterion | Result |
|-----------|--------|
| Matches mental model (room-first) | Passed |
| Alphabetical sort alignment in HA | Passed |
| Compatible with existing package architecture | Passed |
| No HA automation breakage | Passed |
| No collision risk | Passed |
| Survives system-wide debugging scenarios | Passed |
| Max 4 segments (no nesting explosion) | Passed |
| Clean room/floor scope boundary | Passed |

## Action Plan

1. **Audit** the current codebase to identify all entities that don't follow `scope_component_mode_aspect`
2. **Rename** entity IDs in component YAML packages to match the convention
3. **Document** the convention in CLAUDE.md under Key Conventions > Entity Naming
4. **Validate** compilation after renaming (`esphome compile`)

## Session Summary and Insights

**Key Achievements:**

- Established a clear, validated 4-dimension entity ID convention
- Confirmed the convention is adoption-ready with zero architecture impact
- Pressure-tested from 5 adversarial angles with no breakage
- Produced a concrete action plan for implementation

**Breakthrough Moment:** Recognizing that PID is a mode of operation, not a component or aspect — this was the insight that collapsed the model from a potentially complex hierarchy into a clean 4-segment flat structure.

**Session Reflections:** The structured approach (map → validate → attack) was well-suited to this type of standardization problem. The convention emerged not from opinion but from systematic analysis of dimensions, first-principles validation against constraints, and adversarial stress-testing.
