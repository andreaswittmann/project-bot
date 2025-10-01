# Plan for New Email Adapter Implementation

## Overview
This plan outlines the step-by-step approach to implement a new email adapter for the "gulp" provider. The process involves filtering emails to extract project URLs, saving HTML content for pattern analysis, and then developing the scraping adapter.

## Current Status
- Configuration has been edited to include the new "gulp" provider with email settings
- gulp_mail.txt is currently empty and will be populated with sample email content to derive body_url_patterns
- Email agent framework is in place for URL extraction
- Base adapter structure exists for scraping implementation

## Todo List

### Phase 1: Email Filtering and URL Extraction
1. **Prepare Sample Email Content**
   - Populate gulp_mail.txt with sample email content from gulp provider
   - Analyze email structure to identify URL patterns in the body

2. **Validate Configuration**
   - Verify the "gulp" provider configuration in config.yaml is correct
   - Derive and configure body_url_patterns based on gulp_mail.txt content
   - Ensure body_url_patterns are properly defined and regex-validated
   - Test email filtering logic with sample emails (if available)

2. **Implement Email Processing Script**
   - Create a script to run email ingestion for "gulp" provider only
   - Modify email processing to save HTML content instead of immediately scraping
   - Add HTML saving functionality to email_agent.py or create a separate utility

3. **Extract URLs from Emails**
   - Run email processing to filter emails matching gulp sender/subject patterns
   - Extract URLs using configured body_url_patterns
   - Log extracted URLs for verification

### Phase 2: HTML Content Collection
4. **Save HTML Files**
   - For each extracted URL, fetch and save the complete HTML content
   - Store HTML files in a dedicated directory (e.g., `html_content/gulp/`)
   - Include metadata (URL, extraction date, email source) with each HTML file

5. **Collect Representative Sample**
   - Aim to collect 10-20 HTML files representing different project types
   - Ensure variety in project categories, companies, and content structures
   - Validate HTML files are complete and properly saved

### Phase 3: Pattern Analysis
6. **Analyze HTML Structure**
   - Examine saved HTML files to identify common patterns
   - Document CSS selectors for key elements that must be extracted:
     - Titel (Project title)
     - Projektbeschreibung (Project description)
     - Skills (Required skills)
     - Ihr Ansprechpartner (Contact person)
     - Startdatum (Start date)
     - Dauer (Duration)
     - Einsatzort (Location/deployment site)
     - Job ID (Job identifier)
     - Veröffentlicht am (Published date)
   - Note any variations or edge cases in the HTML structure
   - Ensure all required fields are reliably extractable from the HTML

7. **Identify Data Extraction Rules**
   - Define XPath or CSS selector patterns for each data field
   - Handle cases where data might be missing or formatted differently
   - Document any JavaScript-rendered content that needs special handling

### Phase 4: Adapter Development
8. **Create Scraping Adapter**
   - Implement `scraping_adapters/gulp.py` extending BaseAdapter
   - Implement parse() method using identified patterns
   - Normalize extracted data to unified schema format

9. **Test Adapter Implementation**
   - Test parsing with saved HTML files
   - Verify data extraction accuracy
   - Handle edge cases and error conditions

10. **Integration Testing**
    - Integrate adapter with email processing pipeline
    - Run full email ingestion workflow for gulp provider
    - Validate end-to-end functionality from email to markdown file

## Success Criteria
- Successfully extract URLs from gulp emails using configured patterns
- Save complete HTML content for pattern analysis
- Identify reliable CSS selectors/XPath patterns for all required fields
- Implement working scraping adapter that normalizes data correctly
- Full integration with existing email processing workflow

## Dependencies
- Access to gulp email account for testing
- Sample emails containing project URLs
- Working email IMAP connection
- Existing email agent and scraping framework

## Risk Mitigation
- Start with small sample of emails to validate patterns
- Have fallback to manual HTML inspection if automated saving fails
- Document all assumptions about HTML structure for future maintenance
- Plan for HTML structure changes by gulp website updates

## Next Steps
After plan approval, switch to Code mode to implement the email filtering and HTML saving functionality.