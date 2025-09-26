"""
Solcom Scraping Adapter

Adapter for scraping Solcom project pages.
Wraps the existing parse_html.parse_project() function.
"""

import re
from typing import Dict, Any
from scraping_adapters.base import BaseAdapter
from parse_html import parse_project


class SolcomAdapter(BaseAdapter):
    """
    Scraping adapter for Solcom provider.

    Uses the existing parse_html.parse_project() and normalizes
    the output to the unified schema.
    """

    def parse(self, url: str) -> Dict[str, Any]:
        """
        Parse a Solcom project URL.

        Args:
            url: Solcom project URL

        Returns:
            Dict with 'schema' key containing normalized project schema and 'html' key with raw HTML

        Raises:
            Exception: If parsing fails
        """
        import logging
        logger = logging.getLogger(__name__)

        # Fetch HTML once to avoid double fetching
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            }
            import requests
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            html = response.text
            logger.debug(f"Fetched HTML for {url}, length: {len(html)}")
        except Exception as e:
            logger.error(f"Failed to fetch HTML for {url}: {e}")
            raise

        # First try the existing parsing logic with pre-fetched HTML
        raw_data = parse_project(url, html=html)
        logger.debug(f"Solcom raw data from parse_project: title='{raw_data.get('titel')}', description_length={len(raw_data.get('beschreibung') or '')}")

        # Check if we got meaningful data or fallback data
        if raw_data.get("titel") in ["Weitere Projekte", None] or not raw_data.get("beschreibung"):
            logger.warning(f"parse_project returned poor data for solcom URL: {url}, implementing custom parsing")

            # Custom parsing for solcom.de using pre-fetched HTML
            normalized = self._parse_solcom_custom(url, html)
        else:
            # Use the standard normalization
            normalized = {
                "title": raw_data.get("titel"),
                "url": raw_data.get("url"),
                "company": raw_data.get("company"),
                "reference_id": raw_data.get("projekt_id"),
                "description": raw_data.get("beschreibung"),
                "schlagworte": raw_data.get("schlagworte", []),
                "details": {
                    "start": raw_data.get("start"),
                    "von": raw_data.get("von"),
                    "auslastung": raw_data.get("auslastung"),
                    "eingestellt": raw_data.get("eingestellt"),
                    "ansprechpartner": raw_data.get("ansprechpartner"),
                    "branche": raw_data.get("branche"),
                    "vertragsart": raw_data.get("vertragsart"),
                    "einsatzart": raw_data.get("einsatzart"),
                }
            }

        # Remove None values from details
        normalized["details"] = {k: v for k, v in normalized["details"].items() if v is not None}

        return {"schema": normalized, "html": html}

    def _parse_solcom_custom(self, url: str, html: str) -> Dict[str, Any]:
        """
        Custom parsing logic for solcom.de project pages.

        Args:
            url: Solcom project URL
            html: Pre-fetched HTML content

        Returns:
            Normalized project schema dictionary
        """
        from bs4 import BeautifulSoup
        import logging

        logger = logging.getLogger(__name__)

        try:
            soup = BeautifulSoup(html, "lxml")

            # Extract title from URL or page title
            # URL format: .../projektangebote/[slug]-[id]
            url_parts = url.split('/')
            project_slug = url_parts[-1].split('?')[0]  # Remove query params
            project_id = project_slug.split('-')[-1] if '-' in project_slug else None

            # Try to get title from page
            title_tag = soup.find('title')
            page_title = title_tag.get_text(strip=True) if title_tag else ""

            # Extract meaningful title from URL slug
            if project_slug and project_id:
                # Remove the ID from the end and clean up
                title_from_url = project_slug.replace(f'-{project_id}', '').replace('-', ' ').title()
            else:
                title_from_url = "Solcom Project"

            # Try to find project title in various places
            project_title = None

            # For Solcom: Priority order
            # 1. Meta og:title (most reliable)
            meta_title = soup.find('meta', {'property': 'og:title'})
            if meta_title and meta_title.get('content'):
                project_title = meta_title['content'].strip()

            # 2. H2 tags (solcom puts actual title in h2, h1 is generic)
            if not project_title:
                h2_tags = soup.find_all('h2')
                for h2 in h2_tags:
                    text = h2.get_text(strip=True)
                    if text and len(text) > 10 and not any(word in text.lower() for word in ['weitere', 'projekte', 'solcom', 'portal', 'angebote', 'projekt', 'details']):
                        project_title = text
                        break

            # 3. Page title (remove solcom suffix)
            if not project_title and page_title:
                # Remove " – Freiberufler Projekt SOLCOM" suffix
                clean_title = re.sub(r'\s*–\s*Freiberufler Projekt SOLCOM\s*$', '', page_title, flags=re.IGNORECASE)
                if clean_title != page_title:  # Only use if suffix was removed
                    project_title = clean_title.strip()

            # 4. Extract from URL as last resort
            if not project_title and title_from_url:
                project_title = title_from_url

            # Clean up the title
            if project_title:
                # Remove extra whitespace and clean up
                project_title = re.sub(r'\s+', ' ', project_title).strip()
                # Remove common prefixes/suffixes
                project_title = re.sub(r'^(Projekt|Ausschreibung|Job):\s*', '', project_title, flags=re.IGNORECASE)

            final_title = project_title or "Solcom Project"

            # Extract description - target the specific project description div
            description = ""
            projekt_desc_div = soup.find('div', class_='projekt-desc')
            if projekt_desc_div:
                # Preserve line breaks by using get_text with separator
                description = projekt_desc_div.get_text(separator='\n', strip=True)
                # Clean up excessive whitespace but keep intentional line breaks
                description = re.sub(r'\n{3,}', '\n\n', description)  # Max 2 consecutive newlines
                description = re.sub(r' {2,}', ' ', description)  # Single spaces
            else:
                # Fallback: look for the neos-nodetypes-text div within projekt-body
                projekt_body = soup.find('div', class_='projekt-body')
                if projekt_body:
                    text_div = projekt_body.find('div', class_=re.compile(r'neos-nodetypes-text'))
                    if text_div:
                        description = text_div.get_text(separator='\n', strip=True)
                        description = re.sub(r'\n{3,}', '\n\n', description)
                        description = re.sub(r' {2,}', ' ', description)

            # Extract company (Solcom GmbH)
            company = "Solcom GmbH"

            # Extract reference_id (Projekt-Nr.)
            reference_id = None
            project_header = soup.find('div', class_='project-header')
            if project_header:
                # Find all divs in project-header and check for Projekt-Nr.
                for div in project_header.find_all('div'):
                    div_text = div.get_text(strip=True)
                    if 'Projekt-Nr.' in div_text:
                        # Extract the number from the <b> tag
                        b_tag = div.find('b')
                        if b_tag:
                            reference_id = b_tag.get_text(strip=True)
                            break

            # Extract project details from project-infos section
            project_details = {}
            project_infos = soup.find('div', class_='project-infos')
            if project_infos:
                for li in project_infos.find_all('li'):
                    label_span = li.find('span', class_='icon-label')
                    value_span = li.find('span', class_='icon-value')
                    if label_span and value_span:
                        label = label_span.get_text(strip=True).rstrip(':')
                        value = value_span.get_text(strip=True)
                        if label and value:
                            project_details[label.lower()] = value

            # Extract keywords/tags if available
            keywords = []
            keyword_tags = soup.find_all(['span', 'div'], class_=re.compile(r'(tag|keyword|skill)'))
            for tag in keyword_tags:
                text = tag.get_text(strip=True)
                if text and len(text) > 1:
                    keywords.append(text)

            # Basic project data
            project_data = {
                "title": final_title,
                "url": url,
                "company": company,
                "reference_id": reference_id or project_id,  # Use extracted reference_id, fallback to URL-based
                "description": description or f"Project details available at {url}",
                "schlagworte": keywords,
                "details": {
                    "dauer": project_details.get("dauer"),
                    "einsatzort": project_details.get("einsatzort"),
                    "starttermin": project_details.get("starttermin"),
                    "stellentyp": project_details.get("stellentyp"),
                    "branche": project_details.get("branche") or "Unbekannt",
                    "vertragsart": "Unbekannt",
                    "einsatzart": "Unbekannt",
                }
            }

            logger.debug(f"Custom solcom parsing result: title='{final_title}', company='{company}', keywords={keywords}")
            return project_data

        except Exception as e:
            logger.error(f"Custom solcom parsing failed for {url}: {e}")
            # Fallback to basic data
            return {
                "title": "Solcom Project",
                "url": url,
                "company": "Solcom GmbH",
                "reference_id": None,
                "description": f"Project details available at {url}",
                "schlagworte": [],
                "details": {}
            }