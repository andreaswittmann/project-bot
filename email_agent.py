#!/usr/bin/env python3
"""
Email Agent for Project Ingestion

This module provides functionality to poll an IMAP mailbox for project emails,
extract URLs, and process them into project markdown files.
"""

import imaplib
import email
import re
import logging
from typing import List, Dict, Any
from datetime import datetime
import os

from bs4 import BeautifulSoup
from parse_html import parse_project, to_markdown
from state_manager import ProjectStateManager
from rss_helper import create_safe_filename
from dedupe_service import DedupeService
from scraping_adapters.freelancermap import FreelancerMapAdapter
from markdown_renderer import MarkdownRenderer

logger = logging.getLogger(__name__)

class EmailAgent:
    """
    Email Agent for polling IMAP and processing project emails.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Email Agent with configuration.

        Args:
            config: Configuration dictionary containing email settings
        """
        self.config = config
        self.email_config = config.get('channels', {}).get('email', {})
        self.logger = logger

    def validate_config(self, provider_id: str) -> bool:
        """
        Validate the configuration for the given provider.

        Args:
            provider_id: Provider identifier

        Returns:
            True if config is valid, False otherwise
        """
        self.logger.debug("Validating config", extra={'provider_id': provider_id, 'email_config_keys': list(self.email_config.keys())})
        errors = []

        # Check email config
        required_email = ['server', 'username', 'password']
        for field in required_email:
            if not self.email_config.get(field):
                errors.append(f"Missing channels.email.{field}")

        # Check provider config
        provider_config = self.config.get('providers', {}).get(provider_id, {}).get('channels', {}).get('email', {})
        self.logger.debug("Provider config", extra={'provider_config_keys': list(provider_config.keys())})
        if not provider_config:
            errors.append(f"No email config found for provider {provider_id}")
            for error in errors:
                self.logger.error(f"Config validation error: {error}")
            return False

        required_provider = ['senders', 'subject_patterns', 'body_url_patterns']
        for field in required_provider:
            if not provider_config.get(field):
                errors.append(f"Missing or empty providers.{provider_id}.channels.email.{field}")

        # Validate regex patterns
        for pattern in provider_config.get('subject_patterns', []):
            try:
                re.compile(pattern)
            except re.error as e:
                errors.append(f"Invalid subject pattern '{pattern}': {e}")

        for pattern in provider_config.get('body_url_patterns', []):
            try:
                re.compile(pattern)
            except re.error as e:
                errors.append(f"Invalid body URL pattern '{pattern}': {e}")

        if errors:
            for error in errors:
                self.logger.error(f"Config validation error: {error}")
            return False

        self.logger.info("Configuration validation passed")
        return True

    def connect_imap(self) -> imaplib.IMAP4_SSL:
        """
        Connect to IMAP server.

        Returns:
            IMAP4_SSL connection object

        Raises:
            Exception: If connection fails
        """
        try:
            server = self.email_config.get('server')
            port = self.email_config.get('port', 993)
            username = self.email_config.get('username')
            password = os.path.expandvars(self.email_config.get('password', ''))

            if not all([server, username, password]):
                raise ValueError("IMAP server, username, and password are required")

            mail = imaplib.IMAP4_SSL(server, port)
            mail.login(username, password)
            self.logger.info("Connected to IMAP server", extra={
                'server': server,
                'username': username
            })
            return mail
        except Exception as e:
            self.logger.error("Failed to connect to IMAP", extra={
                'error': str(e),
                'server': self.email_config.get('server')
            })
            raise

    def extract_urls_from_email(self, message: email.message.EmailMessage, url_patterns: List[str]) -> List[str]:
        """
        Extract URLs from email message body using regex patterns.
        Handles both text/plain and text/html parts.

        Args:
            message: Email message object
            url_patterns: List of regex patterns for URL extraction

        Returns:
            List of extracted URLs
        """
        urls = []
        bodies = []

        # Get message bodies (both text and html)
        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    bodies.append(('text', body))
                elif content_type == "text/html":
                    html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    bodies.append(('html', html))
                    # Also extract URLs from HTML links
                    soup = BeautifulSoup(html, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.startswith('http'):
                            urls.append(href)
        else:
            content_type = message.get_content_type()
            body = message.get_payload(decode=True).decode('utf-8', errors='ignore')
            if content_type == "text/html":
                bodies.append(('html', body))
                # Extract from HTML
                soup = BeautifulSoup(body, 'html.parser')
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('http'):
                        urls.append(href)
            else:
                bodies.append(('text', body))

        # Log body samples
        for content_type, body in bodies:
            self.logger.debug(f"Processing email {content_type} body: {body[:500]}{'...' if len(body) > 500 else ''}", extra={
                'body_length': len(body)
            })

        # Apply regex patterns to text bodies
        for content_type, body in bodies:
            if content_type == 'text':
                for pattern in url_patterns:
                    try:
                        # Use finditer to get full matches, not just groups
                        matches = [match.group(0) for match in re.finditer(pattern, body, re.IGNORECASE)]
                        urls.extend(matches)
                        self.logger.debug(f"Applied pattern to text: {pattern} -> {len(matches)} matches", extra={
                            'matches': matches[:3]  # Show first 3 matches
                        })
                    except re.error as e:
                        self.logger.warning("Invalid regex pattern", extra={
                            'pattern': pattern,
                            'error': str(e)
                        })

        # Clean and deduplicate URLs
        cleaned_urls = [url.strip() for url in urls]
        unique_urls = list(set(cleaned_urls))
        self.logger.info("URLs extracted from email", extra={
            'total_urls': len(unique_urls),
            'urls': unique_urls[:5]  # Log first 5 for debugging
        })

        return unique_urls

    def move_to_processed(self, mail: imaplib.IMAP4_SSL, message_id: str, processed_folder: str) -> bool:
        """
        Move email to processed folder.

        Args:
            mail: IMAP connection
            message_id: Message ID to move
            processed_folder: Target folder name

        Returns:
            True if successful, False otherwise
        """
        try:
            # Copy to processed folder
            mail.copy(message_id, processed_folder)
            # Mark as deleted in current folder
            mail.store(message_id, '+FLAGS', '\\Deleted')
            # Expunge to permanently remove
            mail.expunge()
            self.logger.info("Email moved to processed folder", extra={
                'message_id': message_id,
                'processed_folder': processed_folder
            })
            return True
        except Exception as e:
            self.logger.error("Failed to move email", extra={
                'message_id': message_id,
                'processed_folder': processed_folder,
                'error': str(e)
            })
            return False

    def process_email(self, mail: imaplib.IMAP4_SSL, message_id: str, provider_config: Dict[str, Any], output_dir: str) -> Dict[str, int]:
        """
        Process a single email: extract URLs, scrape projects, save to files.

        Args:
            mail: IMAP connection
            message_id: Message ID
            provider_config: Provider-specific email config
            output_dir: Directory to save project files

        Returns:
            Dict with processing results: projects_saved, urls_skipped_dedupe
        """
        projects_saved = 0
        urls_skipped_dedupe = 0

        try:
            # Fetch the email
            status, msg_data = mail.fetch(message_id, '(RFC822)')
            if status != 'OK':
                self.logger.error("Failed to fetch email", extra={
                    'message_id': message_id,
                    'status': status
                })
                return 0

            email_body = msg_data[0][1]
            message = email.message_from_bytes(email_body)

            # Log email metadata
            email_date = message.get('Date', 'No Date')
            sender = message.get('From', '')
            subject = message.get('Subject', '')
            self.logger.debug("Email metadata", extra={
                'message_id': message_id,
                'email_date': email_date,
                'sender': sender,
                'subject': subject
            })

            self.logger.debug(f"Processing email: {sender} - {subject}", extra={
                'message_id': message_id
            })

            senders = provider_config.get('senders', [])
            subject_patterns = provider_config.get('subject_patterns', [])

            sender_match = any(s in sender for s in senders)
            subject_match = any(re.search(pattern, subject, re.IGNORECASE) for pattern in subject_patterns)

            if not (sender_match and subject_match):
                self.logger.debug(f"Email filtered out: {sender} - {subject} (sender_match: {sender_match}, subject_match: {subject_match})", extra={
                    'message_id': message_id,
                    'senders_config': senders,
                    'subject_patterns_config': subject_patterns
                })
                return 0

            self.logger.info("Processing matching email", extra={
                'message_id': message_id,
                'sender': sender,
                'subject': subject
            })

            # Extract URLs
            url_patterns = provider_config.get('body_url_patterns', [])
            urls = self.extract_urls_from_email(message, url_patterns)

            if not urls:
                self.logger.info("No URLs found in email", extra={
                    'message_id': message_id
                })
                return 0

            # Initialize services
            dedupe_service = DedupeService(output_dir)
            adapter = FreelancerMapAdapter(provider_config['provider_id'], provider_config)
            renderer = MarkdownRenderer()

            # Process each URL
            for url in urls:
                try:
                    self.logger.debug(f"Starting to scrape project URL: {url}", extra={
                        'message_id': message_id
                    })

                    # Canonicalize URL for dedupe
                    canonical_url = dedupe_service.canonicalize_url(url, provider_config['provider_id'])

                    # Check if already processed
                    if dedupe_service.already_processed(provider_config['provider_id'], canonical_url):
                        urls_skipped_dedupe += 1
                        self.logger.info("URL already processed, skipping", extra={
                            'url': url,
                            'canonical_url': canonical_url,
                            'message_id': message_id
                        })
                        continue

                    # Parse project via adapter
                    self.logger.debug("Calling adapter.parse", extra={'url': url})
                    schema = adapter.parse(url)
                    self.logger.debug("adapter.parse completed", extra={'url': url, 'title': schema.get('title', 'N/A')})

                    # Build provider metadata
                    provider_meta = {
                        'provider_id': provider_config['provider_id'],
                        'provider_name': adapter.get_provider_name(),
                        'collection_channel': 'email',
                        'collected_at': datetime.now().isoformat()
                    }

                    # Render markdown
                    markdown_content = renderer.render(schema, provider_meta)

                    # Create filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    original_title = schema.get('title', 'project')
                    filename = create_safe_filename(original_title, timestamp)

                    # Save file
                    os.makedirs(output_dir, exist_ok=True)
                    filepath = os.path.join(output_dir, filename)

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)

                    # Mark as processed
                    dedupe_service.mark_processed(provider_config['provider_id'], canonical_url)

                    # Initialize state (will merge with existing frontmatter)
                    state_manager = ProjectStateManager(output_dir)
                    metadata = {
                        'scraped_date': datetime.now().isoformat(),
                        'source_url': url
                    }

                    success = state_manager.initialize_project(filepath, metadata)

                    if success:
                        projects_saved += 1
                        self.logger.info("Project saved", extra={
                            'filepath': filepath,
                            'url': url,
                            'canonical_url': canonical_url,
                            'message_id': message_id
                        })
                    else:
                        self.logger.warning("Failed to initialize project state", extra={
                            'filepath': filepath
                        })

                except Exception as e:
                    import traceback
                    self.logger.error("Failed to process project URL", extra={
                        'url': url,
                        'message_id': message_id,
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    })

            # Move email to processed folder (if enabled)
            move_processed = provider_config.get('move_processed', True)
            if move_processed:
                processed_folder = provider_config.get('processed_folder', 'Processed')
                moved = self.move_to_processed(mail, message_id, processed_folder)
            else:
                self.logger.debug("Skipping email move (move_processed=false)")
                moved = False

            self.logger.info("Email processing complete", extra={
                'message_id': message_id,
                'projects_saved': projects_saved,
                'urls_skipped_dedupe': urls_skipped_dedupe,
                'moved_to_processed': moved if move_processed else 'disabled'
            })

        except Exception as e:
            self.logger.error("Failed to process email", extra={
                'message_id': message_id,
                'error': str(e)
            })

        return {
            'projects_saved': projects_saved,
            'urls_skipped_dedupe': urls_skipped_dedupe
        }

    def run_once(self, provider_id: str, output_dir: str = 'projects', dry_run: bool = False) -> Dict[str, Any]:
        """
        Run one ingestion cycle for the specified provider.

        Args:
            provider_id: Provider identifier (e.g., 'freelancermap')
            output_dir: Directory to save project files
            dry_run: If True, validate config and simulate operations without side effects

        Returns:
            Summary dictionary with processing results
        """
        self.logger.info("Starting email ingestion run", extra={
            'provider_id': provider_id,
            'output_dir': output_dir,
            'dry_run': dry_run
        })

        summary = {
            'provider_id': provider_id,
            'dry_run': dry_run,
            'emails_processed': 0,
            'emails_matched': 0,
            'urls_found': 0,
            'urls_skipped_dedupe': 0,
            'projects_saved': 0,
            'errors': 0
        }

        try:
            # Validate config first
            self.logger.debug("Calling validate_config", extra={'provider_id': provider_id})
            is_valid = self.validate_config(provider_id)
            self.logger.debug("validate_config result", extra={'is_valid': is_valid})
            if not is_valid:
                self.logger.info("Configuration validation failed, aborting run", extra={'provider_id': provider_id})
                summary['errors'] += 1
                return summary

            # Get provider config
            provider_config = self.config.get('providers', {}).get(provider_id, {}).get('channels', {}).get('email', {})
            provider_config['provider_id'] = provider_id

            if dry_run:
                # Simulate operations
                self.logger.info("DRY RUN: Would connect to IMAP", extra={
                    'server': self.email_config.get('server'),
                    'source_folder': provider_config.get('source_folder', 'INBOX')
                })
                self.logger.info("DRY RUN: Would process emails", extra={
                    'estimated_emails': 'unknown (would search ALL)',
                    'filters': {
                        'senders': provider_config.get('senders', []),
                        'subject_patterns': provider_config.get('subject_patterns', []),
                        'body_url_patterns': provider_config.get('body_url_patterns', [])
                    }
                })
                self.logger.info("DRY RUN: Would save projects to", extra={
                    'output_dir': output_dir
                })
                summary['emails_processed'] = 0  # Unknown in dry run
                summary['emails_matched'] = 0
                summary['urls_found'] = 0
                summary['urls_skipped_dedupe'] = 0
                summary['projects_saved'] = 0
                self.logger.info("Email ingestion dry run complete", extra=summary)
                return summary

            # Actual run
            # Connect to IMAP
            mail = self.connect_imap()

            # Select source folder
            source_folder = provider_config.get('source_folder', 'INBOX')
            mail.select(source_folder)

            self.logger.debug("Selected source folder", extra={
                'source_folder': source_folder
            })

            # Search for emails within the configured time frame
            max_age_days = provider_config.get('max_age_days', 7)  # Default to 7 days
            import datetime
            now = datetime.datetime.now()
            since_datetime = now - datetime.timedelta(days=max_age_days)
            since_date = since_datetime.strftime('%d-%b-%Y')
            search_criteria = f'SINCE {since_date}'
            self.logger.info(f"Email search parameters: max_age_days={max_age_days}, current_datetime={now.isoformat()}, since_datetime={since_datetime.isoformat()}, since_date_formatted={since_date}, search_criteria={search_criteria}, timezone_info={str(now.tzinfo)}")
            status, messages = mail.search(None, search_criteria)
            if status != 'OK':
                self.logger.error("Failed to search emails", extra={
                    'status': status
                })
                return summary

            message_ids = messages[0].split()
            self.logger.info(f"Emails found by search: total_emails_found={len(message_ids)}, search_criteria={search_criteria}, message_ids_sample={[mid.decode() if isinstance(mid, bytes) else mid for mid in message_ids[:5]]}")

            # Limit the number of emails to process
            max_emails = provider_config.get('max_emails', 50)  # Default to 50 emails
            if len(message_ids) > max_emails:
                message_ids = message_ids[-max_emails:]  # Take the most recent ones
                self.logger.info("Limited email processing to most recent", extra={
                    'original_count': len(messages[0].split()),
                    'limited_to': max_emails
                })

            self.logger.info("Found emails in folder", extra={
                'source_folder': source_folder,
                'email_count': len(message_ids),
                'max_age_days': max_age_days
            })

            # Process each email
            for message_id in message_ids:
                summary['emails_processed'] += 1
                try:
                    result = self.process_email(mail, message_id, provider_config, output_dir)
                    projects_saved = result['projects_saved']
                    urls_skipped = result['urls_skipped_dedupe']
                    if projects_saved > 0 or urls_skipped > 0:
                        summary['emails_matched'] += 1
                    summary['projects_saved'] += projects_saved
                    summary['urls_skipped_dedupe'] += urls_skipped
                except Exception as e:
                    summary['errors'] += 1
                    self.logger.error("Error processing email", extra={
                        'message_id': message_id.decode(),
                        'error': str(e)
                    })

            # Logout
            mail.logout()

            self.logger.info("Email ingestion run complete", extra=summary)

        except Exception as e:
            summary['errors'] += 1
            self.logger.error("Email ingestion run failed", extra={
                'error': str(e),
                'summary': summary
            })

        return summary

def run_email_ingestion(provider_id: str, config: Dict[str, Any], output_dir: str = 'projects', dry_run: bool = False) -> Dict[str, Any]:
    """
    Convenience function to run email ingestion.

    Args:
        provider_id: Provider identifier
        config: Full configuration dictionary
        output_dir: Output directory for project files
        dry_run: If True, validate config and simulate without side effects

    Returns:
        Summary of the ingestion run
    """
    agent = EmailAgent(config)
    return agent.run_once(provider_id, output_dir, dry_run)