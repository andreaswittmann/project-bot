"""
Freelance.de Scraping Adapter

Adapter for scraping Freelance.de project pages.
"""

import re
import logging
from typing import Dict, Any
from bs4 import BeautifulSoup
from scraping_adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class FreelanceAdapter(BaseAdapter):
    """
    Scraping adapter for Freelance.de provider.

    Extracts project information from freelance.de project pages
    and normalizes it to the unified schema.
    """

    def parse(self, url: str) -> Dict[str, Any]:
        """
        Parse a Freelance.de project URL.

        Args:
            url: Freelance.de project URL

        Returns:
            Normalized project schema dictionary

        Raises:
            Exception: If parsing fails
        """
        try:
            # Import here to avoid circular imports
            from parse_html import fetch_html

            # Fetch HTML content
            html = fetch_html(url)
            soup = BeautifulSoup(html, "lxml")

            # Extract basic information
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            company = self._extract_company(soup)
            location = self._extract_location(soup)
            project_id = self._extract_project_id(url)
            keywords = self._extract_keywords(soup)
            details = self._extract_details(soup)

            # Build normalized schema
            schema = {
                "title": title,
                "url": url,
                "company": company,
                "location": location,
                "reference_id": project_id,
                "description": description,
                "schlagworte": keywords,
                "details": details
            }

            # Remove None values from details
            schema["details"] = {k: v for k, v in schema["details"].items() if v is not None}

            logger.info("Freelance.de parsing complete", extra={
                'url': url,
                'title': title,
                'project_id': project_id
            })

            return schema

        except Exception as e:
            logger.error("Failed to parse Freelance.de project", extra={
                'url': url,
                'error': str(e)
            })
            raise

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract project title from the page."""
        # Look for title in various possible locations
        title_selectors = [
            'h1.project-title',
            'h1',
            '.project-header h1',
            '.headline h1',
            'title'
        ]

        for selector in title_selectors:
            if selector == 'title':
                # Special case for <title> tag
                title_tag = soup.find('title')
                if title_tag:
                    title_text = title_tag.get_text(strip=True)
                    # Clean up title - often contains site name
                    if ' - freelance.de' in title_text:
                        title_text = title_text.replace(' - freelance.de', '').strip()
                    return title_text
            else:
                title_elem = soup.select_one(selector)
                if title_elem:
                    return title_elem.get_text(strip=True)

        return "N/A"

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract project description."""
        # Look for description in various containers
        desc_selectors = [
            '.project-description',
            '.description',
            '.project-content',
            '.content',
            '.project-text',
            '.text'
        ]

        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                # Get text content and clean it up
                text = desc_elem.get_text(separator='\n', strip=True)
                if text and len(text) > 50:  # Ensure we have substantial content
                    return text

        # Fallback: look for any substantial text content
        # Find the largest text block that might be the description
        text_blocks = []
        for elem in soup.find_all(['div', 'p', 'section']):
            text = elem.get_text(strip=True)
            if len(text) > 100:  # Look for substantial text blocks
                text_blocks.append(text)

        if text_blocks:
            # Return the longest text block
            return max(text_blocks, key=len)

        return "N/A"

    def _extract_company(self, soup: BeautifulSoup) -> str:
        """Extract company/client name."""
        # Look for company information
        company_selectors = [
            '.company',
            '.client',
            '.project-company',
            '.kunde',
            '.client-name'
        ]

        for selector in company_selectors:
            company_elem = soup.select_one(selector)
            if company_elem:
                return company_elem.get_text(strip=True)

        # Look for company in text patterns
        text = soup.get_text()
        patterns = [
            r'(?:von|by|client|kunde):\s*([^\n\r]+)',
            r'(?:company|unternehmen):\s*([^\n\r]+)',
            r'(?:client|auftraggeber):\s*([^\n\r]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "N/A"

    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extract project location."""
        # Look for location information
        location_selectors = [
            '.location',
            '.ort',
            '.place',
            '.project-location'
        ]

        for selector in location_selectors:
            location_elem = soup.select_one(selector)
            if location_elem:
                return location_elem.get_text(strip=True)

        # Look for location in text patterns
        text = soup.get_text()
        patterns = [
            r'(?:ort|location|place):\s*([^\n\r]+)',
            r'(?:einsatzort|deployment):\s*([^\n\r]+)',
            r'(?:standort|site):\s*([^\n\r]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "N/A"

    def _extract_project_id(self, url: str) -> str:
        """Extract project ID from URL."""
        # URL pattern: https://www.freelance.de/projekte/projekt-1229183-SPS-Developer-6-Months-Remote-Start-October
        match = re.search(r'/projekt-(\d+)', url)
        if match:
            return match.group(1)
        return "N/A"

    def _extract_keywords(self, soup: BeautifulSoup) -> list:
        """Extract project keywords/tags."""
        keywords = []

        # Look for keyword containers
        keyword_selectors = [
            '.keywords',
            '.tags',
            '.skills',
            '.schlagworte',
            '.project-tags'
        ]

        for selector in keyword_selectors:
            keyword_container = soup.select_one(selector)
            if keyword_container:
                # Extract individual keywords
                for tag in keyword_container.find_all(['span', 'a', 'li']):
                    text = tag.get_text(strip=True)
                    if text and len(text) > 2:
                        keywords.append(text)

        # Also look for keywords in meta tags
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keyword_text = meta_keywords.get('content')
            if keyword_text:
                # Split by comma and clean up
                for keyword in keyword_text.split(','):
                    keyword = keyword.strip()
                    if keyword:
                        keywords.append(keyword)

        return keywords

    def _extract_details(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract detailed project information."""
        details = {}

        # Common fields to look for
        field_patterns = {
            'start': r'(?:start|beginn|anfang):\s*([^\n\r]+)',
            'duration': r'(?:dauer|laufzeit|duration):\s*([^\n\r]+)',
            'workload': r'(?:auslastung|workload|capacity):\s*([^\n\r]+)',
            'budget': r'(?:budget|honorar|fee):\s*([^\n\r]+)',
            'remote': r'(?:remote|home.?office):\s*([^\n\r]+)',
            'onsite': r'(?:vor.?ort|onsite):\s*([^\n\r]+)',
            'published': r'(?:veröffentlicht|published|eingestellt):\s*([^\n\r]+)',
            'deadline': r'(?:deadline|bewerbungsfrist):\s*([^\n\r]+)',
            'category': r'(?:kategorie|category|bereich):\s*([^\n\r]+)',
            'industry': r'(?:branche|industry):\s*([^\n\r]+)',
            'contract_type': r'(?:vertragsart|contract):\s*([^\n\r]+)',
            'deployment_type': r'(?:einsatzart|deployment):\s*([^\n\r]+)'
        }

        text = soup.get_text()

        for field, pattern in field_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                details[field] = match.group(1).strip()

        return details