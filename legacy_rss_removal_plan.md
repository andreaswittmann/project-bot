# Legacy RSS Workflow Removal Plan

## Overview
This document outlines the complete removal of the legacy RSS workflow system from the project. The original RSS system (using `rss_helper.py`) has been replaced by the new multi-provider RSS ingestion system in `email_agent.py`, making the legacy code obsolete.

## Current State Analysis

### Legacy RSS System (To Be Removed)
- **Location**: `rss_helper.py`
- **Functions**: `generate_rss_urls()`, `fetch_and_process_rss()`
- **Characteristics**:
  - Single provider (FreelancerMap only)
  - Basic RSS parsing without provider abstraction
  - No deduplication service
  - Manual processed URL tracking via `processed_projects.log`
  - Simple HTML parsing with `parse_html.py`

### New RSS Ingestion System (To Keep)
- **Location**: `email_agent.py` - `run_rss_ingestion()` method
- **Characteristics**:
  - Multi-provider support via scraping adapters
  - Advanced deduplication with `DedupeService`
  - Provider metadata tagging
  - Configurable limits and age filtering
  - Proper state management

## Removal Plan

### Phase 1: Extract Shared Utilities
- **Create new utility module** `utils/filename.py` containing:
  - `sanitize_filename()`
  - `validate_filename()`
  - `create_safe_filename()`
- **Update imports** in `email_agent.py`, `parse_html.py`, and `rss_helper.py` to use the new utility module

### Phase 2: Remove Legacy RSS Functions
- **Delete `rss_helper.py`** entirely (after extracting utilities)
- **Remove imports** from `main.py`: `from rss_helper import generate_rss_urls, fetch_and_process_rss`
- **Remove legacy RSS logic** from `main.py` (lines 539-546) that handles the old workflow
- **Update main.py default behavior** to use RSS ingestion instead of legacy RSS

### Phase 3: Update Scheduler System
- **Remove "main" workflow type** from `scheduler_manager.py`:
  - Remove from `base_commands` dictionary
  - Remove from `_build_workflow_command()` method
  - Update validation logic
- **Disable/delete existing "main" workflow schedules** in `data/schedules.json`
- **Update scheduler documentation** and error messages

### Phase 4: Update Frontend
- **Remove "Full Workflow" option** from `ScheduleForm.vue`:
  - Remove "main" workflow type from dropdown
  - Remove main workflow parameter form section
- **Update ScheduleCard.vue** to handle removed workflow types gracefully
- **Update any workflow type descriptions** in the UI

### Phase 5: Clean Up Configuration
- **Remove global RSS settings** from `config_template.yaml`:
  - Remove `channels.rss.enabled`
  - Remove `channels.rss.default_limit`
  - Remove `channels.rss.max_age_days`
- **Keep provider-specific RSS configs** under `providers.*.channels.rss`
- **Update configuration documentation** and comments

### Phase 6: Update Documentation and References
- **Update README.md** to remove references to `rss_helper.py`
- **Update architecture.md** to remove RSS Helper component references
- **Update docs/concepts/multi-channel-ingestion.md** to reflect current architecture
- **Remove legacy RSS references** from implementation plan documents

### Phase 7: Clean Up Data and Logs
- **Remove processed_projects.log** file (if it exists)
- **Remove from .gitignore** if no longer needed
- **Clean up any remaining schedule data** referencing old workflows

### Phase 8: Testing and Validation
- **Test new RSS ingestion workflows** still function correctly
- **Verify scheduler** works with remaining workflow types
- **Test frontend** schedule creation with new workflow options
- **Validate configuration** loads without deprecated settings

## Impact Assessment

### Files to Modify
- `main.py` - Remove legacy RSS imports and logic
- `scheduler_manager.py` - Remove "main" workflow type
- `frontend/src/components/ScheduleForm.vue` - Remove "Full Workflow" option
- `config_template.yaml` - Remove deprecated RSS settings
- `README.md` - Update component references
- `architecture.md` - Update architecture diagram
- Documentation files - Remove legacy references

### Files to Delete
- `rss_helper.py` (after extracting utilities)

### Files to Create
- `utils/filename.py` - New utility module for filename functions

### Backward Compatibility
- Existing RSS ingestion schedules will need to be recreated as "rss_ingest" type
- Configuration will need to be updated to remove deprecated settings
- No data migration required as legacy system used different storage format

## Success Criteria
- [ ] Legacy RSS functions completely removed from codebase
- [ ] New RSS ingestion system functions without issues
- [ ] Scheduler only shows valid workflow types
- [ ] Frontend schedule creation works with remaining options
- [ ] Configuration validates without deprecated settings
- [ ] All documentation updated to reflect current architecture
- [ ] No broken imports or references to removed code

## Rollback Plan
If issues arise during removal:
1. Restore `rss_helper.py` from git history
2. Revert changes to `main.py` imports
3. Restore "main" workflow type in scheduler
4. Revert frontend changes
5. Restore configuration settings

## Timeline
- **Phase 1-2**: 1-2 hours (utility extraction and core removal)
- **Phase 3-4**: 2-3 hours (scheduler and frontend updates)
- **Phase 5-6**: 1-2 hours (configuration and documentation)
- **Phase 7-8**: 1-2 hours (cleanup and testing)

Total estimated time: 5-9 hours