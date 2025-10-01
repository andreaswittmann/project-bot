"""
Gulp Scraping Adapter

Adapter for scraping Gulp project pages.
Generated based on HTML pattern analysis.
"""

import re
from typing import Dict, Any
from bs4 import BeautifulSoup
from scraping_adapters.base import BaseAdapter
from playwright.sync_api import sync_playwright


class GulpAdapter(BaseAdapter):
    """
    Scraping adapter for Gulp provider.
    """

    def parse(self, url: str) -> Dict[str, Any]:
        """
        Parse a Gulp project URL.

        Args:
            url: Gulp project URL

        Returns:
            Normalized project schema dictionary
        """
        try:
            # Fetch the page content using headless browser
            html_content = self.fetch_page_content(url)

            if not html_content:
                raise Exception("Failed to fetch page content")

            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract data using identified patterns
            data = {
                "title": self.extract_title(soup),
                "url": url,
                "company": "Gulp/Randstad",
                "reference_id": self.extract_job_id(soup),
                "description": self.extract_description(soup),
                "schlagworte": self.extract_skills(soup),
                "details": {
                    "start": self.extract_start_date(soup),
                    "von": self.extract_start_date(soup),  # Same as start
                    "auslastung": self.extract_duration(soup),
                    "eingestellt": self.extract_published_date(soup),
                    "ansprechpartner": self.extract_contact_person(soup),
                    "branche": self.extract_industry(soup),
                    "vertragsart": "Freelance",
                    "einsatzart": self.extract_location(soup),
                }
            }

            # Remove None values from details
            data["details"] = {k: v for k, v in data["details"].items() if v is not None}

            return data

        except Exception as e:
            self.logger.error(f"Failed to parse Gulp URL {url}: {str(e)}")
            raise

    def fetch_page_content(self, url: str) -> str:
        """
        Fetch page content using headless browser.

        Args:
            url: URL to fetch

        Returns:
            HTML content
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 1024},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    locale='de-DE',  # Set German locale
                    extra_http_headers={
                        'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',  # Prefer German, fallback to English
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                    }
                )

                page = context.new_page()
                page.goto(url, wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(3000)  # Wait for dynamic content

                html_content = page.content()

                context.close()
                browser.close()

                return html_content

        except Exception as e:
            self.logger.error(f"Failed to fetch content from {url}: {str(e)}")
            return None

    def extract_title(self, soup: BeautifulSoup) -> str:
        """Extract project title."""
        selectors = ['h1[data-testid="projectTitle"]', 'h1.gp-title']
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        return ""

    def extract_description(self, soup: BeautifulSoup) -> str:
        """Extract project description."""
        selectors = ['.gp-project-description', '.project-description']
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if len(text) > 100:  # Filter for substantial content
                    return text
        return ""

    def extract_skills(self, soup: BeautifulSoup) -> list:
        """Extract skills/requirements."""
        skills = []
        selectors = ['.tag', '[data-testid="readonlyTagsContainer"] .label']

        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) > 5:  # Filter out short/empty tags
                    skills.append(text)

        return skills

    def extract_contact_person(self, soup: BeautifulSoup) -> str:
        """Extract contact person name."""
        selectors = ['[data-testid="contactPersonFullName"]', '.contact-person-info']
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        return ""

    def extract_start_date(self, soup: BeautifulSoup) -> str:
        """Extract start date."""
        # Look for date patterns in info list items
        elements = soup.select('[data-testid="infoListItem"]')
        for element in elements:
            text = element.get_text().strip()
            # Extract date from patterns like "Start Date  06.10.2025" or "Beginn  06.10.2025"
            match = re.search(r'(\d{1,2}\.\d{1,2}\.\d{4})', text)
            if match:
                return match.group(1)
        return ""

    def extract_duration(self, soup: BeautifulSoup) -> str:
        """Extract project duration."""
        # Look for duration in the same info list items
        elements = soup.select('[data-testid="infoListItem"]')
        for element in elements:
            text = element.get_text().strip()
            # Extract duration from patterns like "31.12.2025"
            match = re.search(r'(\d{1,2}\.\d{1,2}\.\d{4})', text)
            if match and match.group(1) != self.extract_start_date(soup):
                return match.group(1)
        return ""

    def extract_location(self, soup: BeautifulSoup) -> str:
        """Extract location."""
        # Look for location in info list items first (most reliable)
        elements = soup.select('[data-testid="infoListItem"]')
        for element in elements:
            text = element.get_text().strip()
            # Look for "Location" or "Einsatzort" pattern like "Location  55130 Mainz am Rhein" or "Einsatzort  Remote..."
            if text.lower().startswith(('location', 'einsatzort')):
                # Extract everything after the label
                if text.lower().startswith('location'):
                    location = text[8:].strip()  # Remove "Location" prefix
                else:  # einsatzort
                    location = text[10:].strip()  # Remove "Einsatzort" prefix
                if location:
                    return location

        # Try other selectors for location
        selectors = [
            '.fa-map-marker',
            '.location',
            '[data-testid="location"]',
            '.project-location',
            '.einsatzort'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) > 5:
                    return text

        # Fallback: search for location patterns in full text
        text = soup.get_text()
        patterns = [
            r'(?:location|ort|einsatzort):\s*([^\n\r]+)',
            r'(?:Location|Ort|Einsatzort):\s*([^\n\r]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if location and len(location) > 5:
                    return location

        return ""

    def extract_job_id(self, soup: BeautifulSoup) -> str:
        """Extract job ID."""
        selectors = ['#jobId', '[data-testid="jobId"]']
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().strip()
                # Extract ID from patterns like "Job ID C01187473"
                match = re.search(r'(\w+\d+)', text)
                if match:
                    return match.group(1)
        return ""

    def extract_published_date(self, soup: BeautifulSoup) -> str:
        """Extract published date."""
        # Look for published date in small text elements
        elements = soup.select('small')
        for element in elements:
            text = element.get_text().strip()
            if 'Published' in text or 'Veröffentlicht' in text:
                match = re.search(r'(\d{1,2}\.\d{1,2}\.\d{4})', text)
                if match:
                    return match.group(1)
        return ""

    def extract_industry(self, soup: BeautifulSoup) -> str:
        """Extract industry/field."""
        # This might be in the description or meta tags
        # For now, return empty as it may require more complex extraction
        return ""
