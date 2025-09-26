# Implementation Plan: Minimal Email Ingestion, Scraping, and Progressive Integration

This plan delivers a minimal, working Email Agent that replaces RSS ingestion immediately (backend-first, CLI), then progressively adds Dedupe, Scraping Adapters, Markdown rendering, UI integration, multi-provider support, optional RSS channel, Scheduler integration, and Log Viewer verification.

Principles:
- Simplicity is King: pick the simplest compatible approach at every step.
- Backward-compatible: do not break existing flows; extend conservatively.
- Observability-first: structured logs with multiple levels from Milestone 1.

Key Baseline References:
- Entry point currently invokes RSS: [main.py](main.py:501)
- RSS workflow and file persistence: [rss_helper.fetch_and_process_rss()](rss_helper.py:125)
- Parsing and Markdown (FreelancerMap): [parse_html.parse_project()](parse_html.py:140), [parse_html.to_markdown()](parse_html.py:180)
- Central logging: [logging_config.setup_logging()](logging_config.py:1)
- State management and frontmatter: [state_manager.ProjectStateManager](state_manager.py)

---

## Milestone 1 — Minimal Email Agent (Single Provider), Replacing RSS (CLI only)

Goal:
- Implement a minimal Email Agent to immediately replace RSS for a single provider (e.g., freelancermap):
  - Connect IMAP
  - Filter by sender and subject
  - Extract URLs from email body
  - Move processed emails to a processed folder
  - Scrape URLs into Markdown
  - Initialize state and persist into projects/
  - Structured logging with multi-level logs

Scope:
- Single provider (freelancermap).
- No UI integration; CLI only.
- Reuse filename creation and state initialization patterns from RSS flow.

Planned Changes:
- New module: email_agent.py
  - email_agent.run_once(provider_id, config)
  - email_agent.extract_urls_from_email(message, regex_list)
  - email_agent.move_to_processed(message_id, processed_folder)
- Config additions:
  - channels.email: IMAP settings, source_folder, processed_folder
  - providers.freelancermap.channels.email: senders[], subject_patterns[], body_url_patterns[]
- CLI:
  - New flags in [main.py](main.py:406) to run email ingestion instead of RSS:
    - --email-ingest
    - --provider freelancermap

Acceptance Criteria:
- Given an email matching configured sender and subject with a valid project URL:
  - URL extracted
  - Email moved to processed folder
  - Project scraped to projects/
  - Frontmatter initialized via ProjectStateManager
  - INFO/DEBUG logs recorded for each step

Test Plan (manual, CLI):
- Seed mailbox with 1–2 test messages.
- Run:
  - python main.py --email-ingest --provider freelancermap -o projects
- Verify:
  - New Markdown files created in projects/
  - Frontmatter present
  - Logs show structured events
  - Existing evaluation and application generation run without changes

Simplicity Notes:
- Use [parse_html.parse_project()](parse_html.py:140) for this provider (no refactor yet).
- Use simple processed log or in-memory set for minimal dedupe (formal dedupe in Milestone 2).

---

## Milestone 2 — Dedupe Service, Scraping Adapter Abstraction, Markdown Renderer (CLI only)

Goal:
- Introduce provider-aware dedupe, a minimal Scraping Adapter interface, and a Markdown Renderer that adds consistent frontmatter while preserving existing body structure.

Scope:
- CLI-only refactor.
- One working provider adapter (freelancermap) that wraps existing parsing.
- Maintain backward compatibility with current markdown format.

Planned Changes:
- Dedupe Service (dedupe_service.py)
  - dedupe_service.canonicalize_url(url, provider_id)
  - dedupe_service.already_processed(provider_id, canonical_url)
  - dedupe_service.mark_processed(provider_id, canonical_url)
- Scraping Adapters
  - scraping_adapters/base.py: BaseAdapter.parse(url) -> normalized schema dict
  - scraping_adapters/freelancermap.py: implement BaseAdapter using [parse_html.parse_project()](parse_html.py:140), normalize keys to unified schema
- Markdown Renderer (markdown_renderer.py)
  - markdown_renderer.render(schema, provider_meta) -> Markdown
  - Add frontmatter with provider_id, provider_name, collection_channel, collected_at
  - Preserve existing body structure (Details, Schlagworte, Beschreibung sections)
  - No restructuring of description content

Acceptance Criteria:
- CLI pipeline:
  - Skips duplicates via provider-aware dedupe
  - Produces normalized schema via adapter
  - Emits Markdown with consistent frontmatter and unchanged body format

Test Plan:
- Repeat Milestone 1, with a duplicate run or duplicate email.
- Confirm duplicates are skipped and frontmatter includes provider metadata fields.

Simplicity Notes:
- Keep BaseAdapter minimal; reuse [parse_html.py](parse_html.py) until diversity requires deeper specialization.

---

## Milestone 3 — Minimal UI Integration for the Example

Goal:
- Provide a minimal UI path to trigger a single email ingestion run and view a short summary.

Scope:
- Backend endpoint to trigger one run:
  - POST /api/v1/workflows/email_ingest/run
- Frontend:
  - Add a simple button on the dashboard to trigger the run and show a success/failure toast or modal.

Acceptance Criteria:
- Clicking “Run Email Ingest” triggers backend action and returns a summary:
  - URLs found, skipped (dedupe), saved
- No provider filtering UI yet.

---

## Milestone 4 — Multi-Provider via Email Channels

Goal:
- Extend email ingestion to multiple providers, each with their own:
  - senders
  - subject_patterns
  - body_url_patterns
  - processed folder

Scope:
- Backend: Iterate over enabled providers and run cycles for each.
- UI: optional provider selection in action modal (nice to have).

Acceptance Criteria:
- Config supports multiple providers under providers.<provider_id>.channels.email
- Running email_ingest for provider A or ALL produces distinct logs and outputs tagged with provider metadata.

---

## Milestone 5 — Optional: RSS Channel (Unavailable for Testing)

Goal:
- Restore RSS channel behind the new orchestrator.

Constraints:
- RSS is switched off by provider, so no end-to-end testing.
- Keep implementation as close to original as possible.

Acceptance Criteria:
- Orchestrator supports channels.email and channels.rss.
- RSS code aligns with original logic in [rss_helper.fetch_and_process_rss()](rss_helper.py:125) and compiles; add unit/mocks where feasible.

---

## Milestone 6 — Full UI Integration

Goal:
- Integrate all implemented features into the UI:
  - Provider column and filter
  - Channel-triggering actions (Email; optionally RSS)
  - Dashboard stats by provider/channel

Scope:
- Extend existing store and views:
  - [frontend/src/stores/projects.js](frontend/src/stores/projects.js)

Acceptance Criteria:
- UI displays provider per project.
- Provider filter available (multi-select).
- Optional quick filters saved and restored.

---

## Milestone 7 — Scheduler Integration

Goal:
- Modify Scheduler to support schedules per provider and per channel.
- providers.<provider_id>.enabled defaults to true (per concept document).

Acceptance Criteria:
- New schedules can be created per provider for the email channel.
- Manual CLI/UI overrides allow ad-hoc runs.

---

## Milestone 8 — Logfile Manager Verification

Goal:
- Ensure all structured logs are available through the Log Viewer.

Acceptance Criteria:
- Log Viewer displays recent runs with these fields:
  - provider_id, channel, mailbox/folder, message_id, urls_found, urls_skipped_dedupe, projects_saved

---

## Structured Logging (from Milestone 1)

Levels:
- DEBUG: detailed steps
- INFO: milestones and counts
- WARNING: recoverable issues
- ERROR: failures
- CRITICAL: fatal errors

Context Fields:
- ingest_start/end:
  - provider_id, channel, mailbox, folder, config_version
- email_message_processed:
  - message_id, urls_extracted, moved_to_processed
- dedupe_summary:
  - total_before, total_after, duplicates
- scrape_summary:
  - fields_expected, fields_found, coverage_pct
- persist_summary:
  - filename, frontmatter_provider_ok

Formatting:
- Structured JSON-like logs via [logging_config.setup_logging()](logging_config.py:1)

Files:
- Write to logs/ with rotation and naming compatible with the Log Viewer.

---

## Compatibility and Simplicity Guardrails

- Keep existing CLI options; add new flags conservatively.
- Centralize new logic to preserve fallback to existing behavior.
- Keep adapter and dedupe abstractions minimal.
- Reuse [parse_html.py](parse_html.py) wherever possible.
- Config changes must be additive and backward-compatible.
- Document minimal config changes in [config_template.yaml](config_template.yaml:1) without breaking existing setups.

---

## Risks and Mitigations

- IMAP Variations:
  - Start with standard IMAP; log envelopes and MIME at DEBUG; skip complex bodies initially.
- URL Extraction Variance:
  - Maintain provider-specific regex lists; basic tests and sample emails.
- Dedupe Correctness:
  - Use provider_id + canonical_url key; extend canonicalization only if necessary.
- Adapter Drift:
  - Keep adapter thin; log extraction coverage and warnings.

---

## Optional Features (No Implementation Plan Yet)

- API Polling Channel
- Sitemap/Catalog Crawler Channel
- Manual/CSV Import Channel
- Webhook Receiver Channel
- Advanced provider heuristics/ML-based extraction
- Alerting/notifications beyond logs
- Persistent job queue and distributed workers
- Advanced retry orchestration with persisted backoff
- Advanced analytics dashboards

---

## Appendix: Example CLI Flows

Minimal Email Ingest (single provider):
```
python main.py --email-ingest --provider freelancermap -o projects
```

All Providers (future milestone):
```
python main.py --email-ingest --provider all -o projects
```

With evaluation and application generation (as today):
```
python main.py --email-ingest --provider freelancermap --config config.yaml --cv-file data/cv.md
