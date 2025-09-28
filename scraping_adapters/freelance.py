"""
Freelance.de Scraping Adapter

Adapter for scraping Freelance.de project pages.
"""

import re
import logging
from typing import Dict, Any, Optional
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
            # Fetch HTML content with login (required for full content)
            html = self._fetch_html_with_login(url)
            soup = BeautifulSoup(html, "lxml")

            # Extract basic information using targeted selectors
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
        """Extract project title using targeted selectors."""
        # Priority order similar to solcom
        title_selectors = [
            'meta[property="og:title"]',  # Most reliable
            'h1.project-title',
            'h1',
            '.project-header h1',
            '.headline h1'
        ]

        for selector in title_selectors:
            if selector.startswith('meta'):
                meta_tag = soup.find('meta', {'property': 'og:title'})
                if meta_tag and meta_tag.get('content'):
                    title = meta_tag['content'].strip()
                    # Clean up freelance.de suffix if present
                    title = re.sub(r'\s*-\s*freelance\.de\s*$', '', title, flags=re.IGNORECASE)
                    return title
            else:
                title_elem = soup.select_one(selector)
                if title_elem:
                    return title_elem.get_text(strip=True)

        # Fallback to page title
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            title_text = re.sub(r'\s*-\s*freelance\.de\s*$', '', title_text, flags=re.IGNORECASE)
            return title_text

        return "N/A"

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract project description using targeted selectors."""
        # Look for main project description container
        desc_selectors = [
            '.project-description',
            '.job-description',
            '.projekt-beschreibung',
            '.content-description',
            'div[class*="description"]',
            '.main-content'
        ]

        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                # Get text with line breaks preserved
                description = desc_elem.get_text(separator='\n', strip=True)
                # Clean up excessive whitespace
                description = re.sub(r'\n{3,}', '\n\n', description)
                description = re.sub(r' {2,}', ' ', description)
                if len(description) > 100:  # Ensure substantial content
                    return description

        # Fallback: look for the largest content div
        content_divs = []
        for div in soup.find_all('div'):
            if div.get('class'):
                classes = ' '.join(div.get('class')).lower()
                # Skip navigation, footer, etc.
                if any(skip in classes for skip in ['nav', 'footer', 'sidebar', 'menu', 'header', 'login', 'register']):
                    continue

            text = div.get_text(separator='\n', strip=True)
            if 200 < len(text) < 10000:  # Substantial but not too long
                content_divs.append(text)

        if content_divs:
            # Return the longest content
            content_divs.sort(key=len, reverse=True)
            description = content_divs[0]
            description = re.sub(r'\n{3,}', '\n\n', description)
            description = re.sub(r' {2,}', ' ', description)
            return description[:2500]  # Limit length

        return "N/A"

    def _extract_company(self, soup: BeautifulSoup) -> str:
        """Extract company/client name."""
        company_selectors = [
            '.company-name',
            '.client-name',
            '.kunde',
            '.project-company',
            '.company'
        ]

        for selector in company_selectors:
            company_elem = soup.select_one(selector)
            if company_elem:
                return company_elem.get_text(strip=True)

        # Look for company in structured data or text patterns
        text = soup.get_text()
        patterns = [
            r'(?:Firma|Company|Client|Kunde):\s*([^\n\r]+)',
            r'(?:von|by|für)\s+([^\n\r]+?)(?:\s*(?:sucht|suchen)|\s*$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "N/A"

    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extract project location."""
        location_selectors = [
            '.location',
            '.ort',
            '.place',
            '.project-location',
            '.standort'
        ]

        for selector in location_selectors:
            location_elem = soup.select_one(selector)
            if location_elem:
                return location_elem.get_text(strip=True)

        # Look for location patterns in text
        text = soup.get_text()
        patterns = [
            r'(?:Ort|Location|Standort|Einsatzort):\s*([^\n\r]+)',
            r'(?:in|bei)\s+([^\n\r]+?)(?:\s*(?:gesucht|suchen)|\s*$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "N/A"

    def _extract_project_id(self, url: str) -> str:
        """Extract project ID from URL."""
        match = re.search(r'/projekt-(\d+)', url)
        if match:
            return match.group(1)
        return "N/A"

    def _extract_keywords(self, soup: BeautifulSoup) -> list:
        """Extract project keywords/tags."""
        keywords = []

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
                for tag in keyword_container.find_all(['span', 'a', 'li', 'div']):
                    text = tag.get_text(strip=True)
                    if text and len(text) > 1 and not text.isdigit():
                        keywords.append(text)

        # Also check meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keyword_text = meta_keywords.get('content')
            for keyword in keyword_text.split(','):
                keyword = keyword.strip()
                if keyword and keyword not in keywords:
                    keywords.append(keyword)

        return keywords

    def _extract_details(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract detailed project information."""
        details = {}

        # Look for project details section
        details_container = soup.select_one('.project-details, .projekt-details, .job-details')
        if details_container:
            # Extract from structured list items or divs
            for item in details_container.find_all(['li', 'div']):
                if ':' in item.get_text():
                    key_value = item.get_text(separator=':').split(':', 1)
                    if len(key_value) == 2:
                        key = key_value[0].strip().lower()
                        value = key_value[1].strip()
                        if key and value:
                            details[key] = value

        # Fallback: regex patterns on full text
        text = soup.get_text()
        field_patterns = {
            'start': r'(?:start|beginn|anfang):\s*([^\n\r]+)',
            'duration': r'(?:dauer|laufzeit|duration):\s*([^\n\r]+)',
            'workload': r'(?:auslastung|workload|stunden):\s*([^\n\r]+)',
            'budget': r'(?:budget|honorar|fee):\s*([^\n\r]+)',
            'remote': r'(?:remote|home.?office):\s*([^\n\r]+)',
            'published': r'(?:veröffentlicht|published|eingestellt):\s*([^\n\r]+)',
            'deadline': r'(?:deadline|bewerbungsfrist):\s*([^\n\r]+)',
            'category': r'(?:kategorie|category|bereich):\s*([^\n\r]+)',
            'industry': r'(?:branche|industry):\s*([^\n\r]+)'
        }

        for field, pattern in field_patterns.items():
            if field not in details:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    details[field] = match.group(1).strip()

        return details

    def _fetch_html_with_login(self, url: str) -> str:
        """Fetch HTML content with login (required for full content)."""
        login_config = self._get_login_config()
        if not login_config or not login_config.get('enabled', False):
            logger.warning("Login not configured or disabled, attempting anonymous fetch (may get teaser only)")
            return self._anonymous_fetch(url)

        logger.debug("Login configured, attempting to login and fetch")
        return self._login_and_fetch(url, login_config)

    def _anonymous_fetch(self, url: str) -> str:
        """Fetch HTML anonymously (may return teaser content)."""
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        }
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return response.text

    def _get_login_config(self) -> Optional[Dict[str, Any]]:
        """Get login configuration from config."""
        try:
            import yaml
            with open('config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('providers', {}).get('freelance', {}).get('login')
        except Exception as e:
            logger.warning(f"Failed to load login config: {e}")
            return None

    def _login_and_fetch(self, url: str, login_config: Dict[str, Any]) -> str:
        """Perform login and fetch the target URL."""
        import requests
        from parse_html import HEADERS

        username = login_config.get('username')
        password = login_config.get('password')

        if not username or not password:
            logger.warning("Login credentials not provided, falling back to anonymous fetch")
            return self._anonymous_fetch(url)

        # Expand environment variables if needed
        import os
        username = os.path.expandvars(username)
        password = os.path.expandvars(password)

        session = requests.Session()
        session.headers.update(HEADERS)

        try:
            # Visit login page to get any CSRF tokens
            login_page_url = "https://www.freelance.de/login.php"
            logger.debug(f"Visiting login page: {login_page_url}")
            response = session.get(login_page_url, timeout=20)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Find login form
            login_form = soup.find('form', {'action': lambda x: x and 'login' in x.lower()})
            if not login_form:
                login_form = soup.find('form', {'id': lambda x: x and 'login' in x.lower()})
            if not login_form:
                login_form = soup.find('form')

            if not login_form:
                logger.error("Could not find login form on freelance.de")
                raise Exception("Login form not found")

            action_url = login_form.get('action')
            if action_url and not action_url.startswith('http'):
                action_url = f"https://www.freelance.de{action_url}"

            # Prepare login data
            login_data = {
                'username': username,
                'password': password,
                'login': 'Anmelden'
            }

            # Add hidden fields
            for hidden_input in login_form.find_all('input', {'type': 'hidden'}):
                name = hidden_input.get('name')
                value = hidden_input.get('value')
                if name:
                    login_data[name] = value or ''

            logger.debug(f"Attempting login with email: {username}")
            login_response = session.post(action_url or login_page_url, data=login_data, timeout=20)
            login_response.raise_for_status()

            # Check if login successful
            if 'login.php' in login_response.url.lower():
                logger.error("Login appears to have failed - still on login page")
                raise Exception("Login failed")

            if '/myfreelance/' in login_response.url or 'Mein freelance.de' in login_response.text:
                logger.debug("Login successful")
            else:
                logger.warning("Login may have failed - unexpected redirect")

            # Fetch target URL
            logger.debug("Fetching target URL with authenticated session")
            response = session.get(url, timeout=20)
            response.raise_for_status()

            return response.text

        except Exception as e:
            logger.error(f"Login process failed: {e}")
            logger.debug("Falling back to anonymous fetch")
            return self._anonymous_fetch(url)