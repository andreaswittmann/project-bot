# Implementation Plan: Milestone 5 - RSS Channel Restoration

## Overview
Restore RSS channel integration behind the new orchestrator, now that RSS feed is available at www.freelancermap.de/feeds/projekte/de.xml?p=kbZGfgs2Gz6KrSGjCgRb. Integrate RSS with the new architecture (scraping adapters, dedupe service, markdown renderer) while maintaining compatibility with original logic.

## Goals
- Enable RSS ingestion as an alternative channel to email
- Integrate RSS with new components: scraping adapters, dedupe service, markdown renderer
- Support end-to-end testing with the provided RSS feed
- Maintain backward compatibility with existing RSS workflow patterns

## Detailed Tasks

### 1. Configuration Updates
- [ ] Add RSS channel configuration schema to config_template.yaml
- [ ] Document providers.<provider_id>.channels.rss: feed_urls[], limit, max_age_days
- [ ] Ensure RSS config is additive and backward-compatible

### 2. Extend EmailAgent for RSS Support
- [ ] Add RSS ingestion methods to EmailAgent class:
  - `fetch_rss_feed(feed_url, limit)` - Fetch and parse RSS feed
  - `process_rss_entries(entries, provider_config, output_dir)` - Process RSS entries
  - `run_rss_ingestion(provider_id, output_dir, dry_run)` - Main RSS runner
- [ ] Integrate RSS with existing services:
  - Use DedupeService for provider-aware dedupe
  - Use scraping adapters for project parsing
  - Use MarkdownRenderer for consistent output
  - Apply structured logging with RSS-specific context

### 3. CLI Integration
- [ ] Add --rss-ingest flag to main.py argument parser
- [ ] Update CLI logic to handle RSS ingestion alongside email
- [ ] Ensure RSS and email can coexist or be run separately

### 4. RSS-Specific Features
- [ ] Implement RSS URL extraction from feed entries
- [ ] Add RSS metadata to frontmatter: collection_channel='rss', provider_id, collected_at
- [ ] Handle RSS feed parsing errors gracefully
- [ ] Support multiple RSS feeds per provider

### 5. Testing and Validation
- [ ] Create test configuration with provided RSS feed URL
- [ ] Test end-to-end RSS ingestion: python main.py --rss-ingest --provider freelancermap -o projects
- [ ] Verify dedupe works across RSS runs
- [ ] Compare output with original RSS workflow for consistency
- [ ] Validate structured logs include RSS context fields

### 6. Documentation and Compatibility
- [ ] Update README with RSS ingestion examples
- [ ] Document RSS vs Email channel differences
- [ ] Ensure RSS maintains original filename creation patterns
- [ ] Add RSS to logging context fields documentation

## Acceptance Criteria
- RSS ingestion successfully fetches from provided URL
- Projects are created with correct provider metadata and collection_channel='rss'
- Dedupe service prevents duplicate processing
- Structured logs include RSS-specific events
- CLI supports both --email-ingest and --rss-ingest
- End-to-end testing passes with real RSS feed

## Dependencies
- Milestone 2 (Dedupe Service, Scraping Adapters, Markdown Renderer) must be complete
- RSS feed must remain accessible at provided URL
- Existing scraping adapters must support RSS-sourced URLs

## Risks and Mitigations
- RSS feed format changes: Monitor feed structure, add error handling
- Network issues: Add retry logic and timeout handling
- Feedparser library compatibility: Ensure feedparser is available and up-to-date
- Performance: Limit RSS entries processed per run to prevent overload

## Success Metrics
- RSS ingestion completes without errors
- Projects saved match expected count from RSS feed
- No duplicate projects created on re-run
- Logs provide clear visibility into RSS processing steps
- RSS and email channels can be used interchangeably