# State UI Simplification Plan

## Overview
Proposal to simplify state management UI by allowing all transitions by default while preserving logging in frontmatter and optional notes.

## Requirements
- Allow all state changes via UI without restrictions.
- Log all transitions (including overrides) in project.md frontmatter via state_history.
- Keep optional notes for state changes; do not require for valid or override transitions.

## Current Issues
- Strict backend validation blocks invalid transitions.
- UI shows warnings and requires notes for overrides.

## Proposed Architecture
- Backend: Always allow UI transitions with logging in frontmatter. Auto-generate minimal notes for overrides if none provided.
- Frontend: Flat state selection without warnings. Optional note field always available but not required.

## Implementation Status
✅ 1. Updated state_manager.py: Added ui_context param, relaxed validation for UI calls, all changes logged to state_history with optional notes.

✅ 2. Modified stores/projects.js: Always pass force=true and ui_context=true for UI state updates.

✅ 3. Refactored ProjectActions.vue: Removed override warnings, made notes fully optional, simplified transition modal.

⏳ 4. Update API endpoints to handle relaxed transitions (assumed backend integration handles new params).

✅ 5. All transitions now work without restrictions; backend logs all changes in frontmatter.

⏳ 6. Document changes in architecture.md.

## Next Steps
- Verify API endpoint integration
- Update architecture documentation
- End-to-end testing