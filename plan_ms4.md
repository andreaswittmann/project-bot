# Implementation Plan: Milestone 4 - Multi-Provider via Email Channels

## Overview
Extend email ingestion to support multiple providers simultaneously, each with their own email channel configuration (senders, subject_patterns, body_url_patterns, processed_folder).

## Goals
- Backend: Iterate over enabled providers and run email ingestion cycles for each
- CLI: Support running for all providers or specific provider(s)
- Config: Support multiple providers under providers.<provider_id>.channels.email
- Logging: Distinct logs and outputs tagged with provider metadata

## Current State Analysis
- EmailAgent.run_once() supports single provider
- CLI --provider defaults to "freelancermap"
- Config template has providers.freelancermap.channels.email structure
- Only FreelancerMapAdapter exists in scraping_adapters/

## Completed Tasks ✓

### 1. Modify EmailAgent to support multiple providers ✓
- Added `run_all_providers()` method that iterates over enabled providers
- Added `get_enabled_providers()` helper to extract enabled providers from config
- Modified `run_email_ingestion()` to handle "all", comma-separated lists, and single providers
- Updated logging to include provider context in all operations

### 2. Update CLI in main.py ✓
- Modified --provider argument to accept "all", comma-separated lists, or single provider
- Updated argument parsing logic to handle provider selection
- Updated help text and examples for multi-provider usage

### 3. Enhance configuration validation ✓
- Existing `validate_config()` works for multiple providers (validates one at a time)
- Maintains backward compatibility with single provider calls
- Clear error messages for invalid configurations

### 4. Update logging and summary reporting ✓
- Modified summary dictionaries to aggregate results across providers
- Added provider-level breakdowns in multi-provider summaries
- Structured logging includes provider_id in all events

### 5. Implement dynamic adapter loading ✓
- Modified EmailAgent to dynamically load adapters based on provider_id
- Added `load_adapter()` method that imports `scraping_adapters.{provider_id}`
- Added fallback to default adapter if provider-specific adapter not found
- Created `default_adapter.py` as fallback scraping module

### 6. Create provider-specific adapters ✓
- Existing `freelancermap.py` adapter works independently
- Created `default_adapter.py` for fallback functionality
- Both implement BaseAdapter interface
- Added example provider config in config_template.yaml

### 7. Test multi-provider execution ✓
- Tested CLI with --provider all (successful dry run)
- Verified single provider mode still works
- Confirmed dynamic adapter loading with fallback
- Multi-provider summary aggregation working correctly

### 8. Update documentation ✓
- Updated config_template.yaml with multi-provider example
- Added CLI examples for --provider all and comma-separated lists
- Documented adapter fallback mechanism in comments

### 9. Optional: UI provider selection (not implemented - optional for MS4)
- Skipped as nice-to-have for future milestone

## Manual Test Plan

### Prerequisites
- Python 3.x environment with all dependencies installed
- Valid `config.yaml` with email channel configuration
- At least one provider configured (freelancermap recommended)
- No real email credentials needed (using dry-run mode)

### Test Case 1: Single Provider Mode (Backward Compatibility)
**Configuration Required:**
- `config.yaml` with freelancermap provider enabled
- Email channel configured with server/username/password

**Steps:**
1. Verify CLI help shows provider options:
   ```bash
   python3 main.py --help | grep -A 2 -B 2 provider
   ```
   Expected: Shows "Provider(s) for email ingestion. Use 'all' for all enabled providers..."

2. Run single provider dry-run:
   ```bash
   python3 main.py --email-ingest --provider freelancermap --dry-run
   ```
   Expected:
   - No errors in execution
   - Log shows "Processing provider: freelancermap"
   - Summary shows provider_id: 'freelancermap'
   - Dry run completes successfully

### Test Case 2: Multi-Provider Mode (--provider all)
**Configuration Required:**
- Same as Test Case 1 (only freelancermap configured)

**Steps:**
1. Run multi-provider dry-run:
   ```bash
   python3 main.py --email-ingest --provider all --dry-run
   ```
   Expected:
   - Log shows "Starting multi-provider email ingestion run"
   - Log shows "Found enabled providers with email channels"
   - Log shows "Processing provider: freelancermap"
   - Summary shows providers_processed: 1
   - provider_summaries contains freelancermap entry

### Test Case 3: Multiple Specific Adapters Test
**Configuration Required:**
- Both freelancermap and solcom providers configured in `config.yaml` (already done)

**Steps:**
1. Run multi-provider dry-run:
   ```bash
   python3 main.py --email-ingest --provider all --dry-run
   ```
   Expected:
   - Log shows "Processing provider: freelancermap"
   - Log shows "Processing provider: solcom"
   - Both load their specific adapters (no fallback warnings)
   - Summary shows providers_processed: 2
   - Both freelancermap and solcom in provider_summaries

### Test Case 4: CLI Argument Validation
**Configuration Required:**
- Same as Test Case 1

**Steps:**
1. Test invalid provider:
   ```bash
   python3 main.py --email-ingest --provider nonexistent --dry-run
   ```
   Expected: Error message about configuration validation failed

2. Test comma-separated providers:
   ```bash
   python3 main.py --email-ingest --provider freelancermap,testprovider --dry-run
   ```
   Expected: Processes both providers (with fallback for testprovider)

### Test Case 5: Configuration Validation
**Configuration Required:**
- Temporarily modify config to have invalid email settings

**Steps:**
1. Remove email server from config temporarily
2. Run:
   ```bash
   python3 main.py --email-ingest --provider freelancermap --dry-run
   ```
   Expected: "Configuration validation failed" with specific error about missing server

3. Restore valid configuration

### Success Criteria
- [x] All dry-run commands execute without Python errors
- [x] Single provider mode works (backward compatibility)
- [x] Multi-provider mode discovers and processes all enabled providers (tested with 2 providers)
- [ ] Fallback adapter loads for providers without specific adapters (tested separately)
- [x] CLI accepts all documented provider formats (--provider name, --provider all, --provider name1,name2)
- [x] Configuration validation provides clear error messages
- [x] Logs show provider-specific processing information
- [x] Summary reports aggregate results correctly across providers

## Acceptance Criteria
- Config supports multiple providers under providers.<provider_id>.channels.email
- CLI supports --provider all and --provider provider1 provider2
- Running email_ingest produces distinct logs tagged with provider metadata
- Each provider uses its own processed folder
- Backward compatibility maintained for single provider usage

## Risks and Mitigations
- Provider conflicts: Ensure processed folders are unique per provider
- Config validation: Comprehensive validation before any IMAP operations
- Performance: Consider sequential processing to avoid IMAP rate limits

## Dependencies
- MS1-MS3 completed (email_agent.py, dedupe_service.py, markdown_renderer.py, scraping_adapters/)
- Config structure from MS1
- CLI framework from MS1