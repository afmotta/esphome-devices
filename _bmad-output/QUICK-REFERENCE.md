# Quick Reference: BMAD v6 Structure

## Where to Find Things

### Planning Documents

Location: `_bmad-output/planning-artifacts/`

- **PRD**: `prd.md` - Product Requirements Document
- **Product Brief**: `product-brief.md` - High-level product vision
- **Architecture**: `architecture.md` - System architecture
- **Architecture Diagrams**: `architecture-diagram.md` - Visual diagrams
- **Brainstorming**: `brainstorming-session-results.md` - Initial ideation
- **Workflow Status**: `bmm-workflow-status.yaml` - Progress tracking

### Implementation Documents

Location: `_bmad-output/implementation-artifacts/`

- **Epic Briefs**: `epic-N-brief.md` - Epic specifications
- **Completion Reports**: `epic-N-completion-report.md` - What was delivered
- **Testing Checklists**: `epic-N-testing-checklist.md` - QA validation
- **Migration Guides**: `epic-N-migration-guide.md` - How to upgrade
- **Feature Briefs**: `brief-*.md` - Feature-specific planning
- **Feature Brainstorming**: `brainstorming-*.md` - Feature ideation

## Using BMAD Agents

### Analyst Agent

```bash
# From repository root
# Agent will load config and display menu
```

The analyst agent provides:
- [MH] Menu Help
- [CH] Chat with Agent
- [WS] Workflow Status (reads bmm-workflow-status.yaml)
- [BP] Brainstorming Session
- [RS] Research
- [PB] Product Brief
- [DP] Document Project
- [PM] Party Mode
- [DA] Dismiss Agent

### Quick Commands

**Check Workflow Status**:
- Uses: `_bmad-output/planning-artifacts/bmm-workflow-status.yaml`
- Shows: What phase you're in, what's completed, what's next

**View Planning Artifacts**:
```bash
ls _bmad-output/planning-artifacts/
```

**View Implementation Artifacts**:
```bash
ls _bmad-output/implementation-artifacts/
```

**Find Epic Documents**:
```bash
ls _bmad-output/implementation-artifacts/epic-*
```

## Config Variables

These variables are set in `_bmad/bmm/config.yaml`:

- `{project-root}` → Repository root
- `{output_folder}` → `_bmad-output`
- `{planning_artifacts}` → `_bmad-output/planning-artifacts`
- `{implementation_artifacts}` → `_bmad-output/implementation-artifacts`
- `{project_knowledge}` → `docs` (original docs, still valid)

## Workflow Phases (BMad Method - Brownfield)

### ✅ Phase 0: Documentation (Complete)
- [x] Document existing project

### ✅ Phase 1: Analysis (Complete)
- [x] Brainstorming
- [x] Product Brief
- [ ] Research (optional, as needed)

### ✅ Phase 2: Planning (Complete)
- [x] PRD
- [x] UX Design (skipped - no UI)

### ✅ Phase 3: Solutioning (Complete)
- [x] Architecture
- [x] Epics and Stories
- [x] Implementation Readiness

### ✅ Phase 4: Implementation (Complete)
- [x] Epics 1-10, 13-15 (Core climate control, fancoil boost, air quality)
- [x] Epic 18: MEV Modbus Migration
- [x] Epics 19-20: Vesta Climate Framework extraction and migration
- [ ] Epics 11-12 (Deferred - room sensors UDP, autonomous dew point)
- [ ] Epics 16-17 (Backlog - MEV intelligent control, seasonal mode)

### 🔄 Phase 5: Open Source Launch (Next)
- [x] Vesta component extraction (Epics 19-20)
- [x] Entity ID naming convention (brainstorming validated, applied)
- [ ] Community announcement (HA forums, ESPHome Discord)
- [ ] Phase 2: CLI scaffolding tool

## Common Tasks

### Create New Epic Brief

1. Use PM agent or create manually in:
   ```
   _bmad-output/implementation-artifacts/epic-N-brief.md
   ```

2. Update workflow status:
   ```yaml
   # In bmm-workflow-status.yaml
   epic_status: |
     In Progress:
     - Epic N: Description (IN PLANNING)
   ```

### Complete an Epic

1. Create completion report:
   ```
   _bmad-output/implementation-artifacts/epic-N-completion-report.md
   ```

2. Update workflow status with completion date

### Start New Feature Planning

1. Create feature brief:
   ```
   _bmad-output/implementation-artifacts/brief-feature-name.md
   ```

2. Optional: Run brainstorming session:
   ```
   _bmad-output/implementation-artifacts/brainstorming-session-feature-name.md
   ```

## File Naming Conventions

### Planning Artifacts
- `prd.md` - Product Requirements Document
- `product-brief.md` - Product Brief
- `architecture.md` - Architecture Document
- `architecture-diagram.md` - Architecture Diagrams
- `brainstorming-session-results.md` - Main brainstorming
- `bmm-workflow-status.yaml` - Workflow tracking

### Implementation Artifacts
- `epic-N-brief.md` - Epic specification
- `epic-N-completion-report.md` - Epic completion
- `epic-N-testing-checklist.md` - Epic testing
- `epic-N-migration-guide.md` - Epic migration notes
- `brief-feature-name.md` - Feature brief
- `brainstorming-session-feature-name.md` - Feature brainstorming

## Getting Help

1. **README**: Read `_bmad-output/README.md`
2. **Migration Guide**: Read `_bmad-output/MIGRATION-v4-to-v6.md`
3. **BMAD Documentation**: Check `_bmad/` directory
4. **Original Docs**: Reference `docs/` for historical context
5. **Workflow Status**: Check `bmm-workflow-status.yaml` for current state

## Tips

- **Keep originals**: `/docs` still exists for reference
- **Use config variables**: Reference `{planning_artifacts}` not hardcoded paths
- **Update status**: Keep `bmm-workflow-status.yaml` current
- **Follow naming**: Use consistent file naming conventions
- **Separate concerns**: Planning vs Implementation artifacts

---

**Version**: BMAD 6.0.0-alpha.23
**Last Updated**: 2026-03-23
