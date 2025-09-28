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
        """Extract project description using multiple targeted strategies."""

        # Strategy 1: Look for the main project description area
        main_content = self._extract_main_project_content(soup)
        if main_content and len(main_content) > 200:
            return main_content[:2500]  # Limit length

        # Strategy 2: Look for structured content sections
        structured_content = self._extract_structured_content(soup)
        if structured_content and len(structured_content) > 200:
            return structured_content[:2500]

        # Strategy 3: Find content by analyzing the page structure
        structural_content = self._extract_by_structure(soup)
        if structural_content and len(structural_content) > 200:
            return structural_content[:2500]

        # Strategy 4: Final fallback - find any substantial content
        fallback_content = self._get_fallback_description(soup)
        return fallback_content[:2500] if fallback_content != "N/A" else "N/A"

    def _extract_main_project_content(self, soup: BeautifulSoup) -> str:
        """Extract content from the main project description area."""
        # Strategy: Look for the actual job description text patterns
        full_text = soup.get_text(separator='\n')

        # Look for the specific pattern that indicates the start of the actual job description
        # This is typically something like "Für einen unserer" or "Für ein langfristiges"
        start_patterns = [
            r'für einen unserer.*?suchen wir',
            r'für ein.*?suchen wir',
            r'für.*?suchen wir.*?der die',
            r'für.*?suchen wir.*?die die'
        ]

        description_text = ""
        for pattern in start_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
            if match:
                # Get text starting from the match
                start_pos = match.start()
                description_text = full_text[start_pos:start_pos + 2000]  # Get next 2000 chars
                break

        if description_text:
            # Get more content after the start pattern
            start_pos = match.start()

            # Look for the end of the job description (before footer/sidebar content)
            full_text_lower = full_text.lower()
            end_patterns = [
                'kostenlos registrieren',
                'ähnliche projekte',
                'sie suchen freelancer',
                'kategorien und skills',
                '© 2007 - 2025 freelance.de gmbh'
            ]

            end_pos = len(full_text)
            for pattern in end_patterns:
                pattern_pos = full_text_lower.find(pattern, start_pos)
                if pattern_pos > start_pos:
                    end_pos = min(end_pos, pattern_pos)
                    break

            # Extract the job description content
            description_text = full_text[start_pos:end_pos]

            # Clean up the extracted content
            cleaned = self._clean_extracted_content(description_text)

            # Look for structured sections within this content
            structured = self._extract_structured_sections(cleaned)
            if structured and len(structured) > len(cleaned) * 0.8:  # Structured content is substantial
                return structured

            return cleaned[:2000]  # Limit length

        return ""

    def _extract_structured_content(self, soup: BeautifulSoup) -> str:
        """Extract content from structured sections like Aufgaben, Anforderungen."""
        sections = []

        # Look for section headers
        section_headers = ['aufgaben', 'anforderungen', 'profil', 'erfahrungen', 'qualifikationen']

        for header_text in section_headers:
            # Find headers
            headers = soup.find_all(lambda tag: tag.name in ['h2', 'h3', 'h4', 'strong', 'b', 'div']
                                   and header_text in tag.get_text().lower())

            for header in headers:
                content = self._get_content_after_header(header)
                if content:
                    sections.append(f"**{header_text.title()}:**\n{content}")

        return '\n\n'.join(sections) if sections else ""

    def _extract_by_structure(self, soup: BeautifulSoup) -> str:
        """Extract content by analyzing HTML structure."""
        # Look for the main content area - often the largest content div
        content_divs = []

        for div in soup.find_all('div'):
            # Skip navigation, footer, etc.
            div_class = div.get('class', [])
            if div_class:
                class_str = ' '.join(div_class).lower()
                if any(skip in class_str for skip in ['nav', 'footer', 'sidebar', 'menu', 'header']):
                    continue

            text = div.get_text(separator='\n', strip=True)
            if len(text) > 300:  # Substantial content
                cleaned = self._clean_extracted_content(text)
                if cleaned and len(cleaned) > 200:
                    content_divs.append(cleaned)

        # Return the best content div
        if content_divs:
            # Sort by quality score
            content_divs.sort(key=self._calculate_content_quality, reverse=True)
            return content_divs[0]

        return ""

    def _extract_meaningful_content(self, text: str) -> str:
        """Extract only the meaningful job-related content from text."""
        if not text:
            return ""

        lines = text.split('\n')
        meaningful_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip obvious noise
            noise_indicators = [
                'kostenlos registrieren', 'jetzt registrieren', 'einloggen',
                'expert-mitglieder', 'firmenname.*sichtbar',
                'seit wann aktiv', 'projektansichten', 'bewerbungen',
                'ähnliche projekte', 'sie suchen freelancer',
                'kategorien und skills', 'schreiben sie ihr projekt',
                'erhalten sie noch heute', 'jetzt projekt erstellen'
            ]

            skip_line = False
            for indicator in noise_indicators:
                if indicator.lower() in line.lower():
                    skip_line = True
                    break

            if skip_line:
                continue

            # Skip very short lines that are likely metadata
            if len(line) < 20 and not any(char.isdigit() for char in line):
                continue

            # Skip lines that are just dates, locations, or IDs
            if re.match(r'^[\d\.\s\-/]+$', line):  # Just numbers and punctuation
                continue

            meaningful_lines.append(line)

        # Join and clean up
        result = '\n'.join(meaningful_lines)
        result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)  # Multiple newlines to double
        return result.strip()

    def _get_content_after_header(self, header_elem) -> str:
        """Get content that appears after a specific header."""
        content_parts = []

        # Look at the next few siblings
        for sibling in header_elem.next_siblings:
            if sibling.name in ['h1', 'h2', 'h3', 'h4']:  # Stop at next header
                break

            if sibling.name in ['p', 'div', 'ul', 'li']:
                text = sibling.get_text(separator='\n', strip=True)
                if len(text) > 20:
                    cleaned = self._extract_meaningful_content(text)
                    if cleaned:
                        content_parts.append(cleaned)

            # Limit to reasonable amount of content
            if len(content_parts) >= 3:
                break

        return '\n\n'.join(content_parts) if content_parts else ""

    def _calculate_content_quality(self, text: str) -> int:
        """Calculate a quality score for content (higher is better)."""
        score = 0

        # Positive indicators
        job_keywords = [
            'aufgaben', 'anforderungen', 'entwicklung', 'erfahrung',
            'kenntnisse', 'koordination', 'steuerung', 'mehrjährige',
            'abgeschlossene', 'zertifizierung', 'start', 'dauer'
        ]

        for keyword in job_keywords:
            if keyword in text.lower():
                score += 10

        # Length bonus
        score += min(len(text) // 50, 20)  # Up to 20 points for length

        # Avoid noise penalty
        noise_indicators = ['registrieren', 'kostenlos', 'expert', 'ähnliche']
        for indicator in noise_indicators:
            if indicator in text.lower():
                score -= 15

        return max(score, 0)

    def _get_fallback_description(self, soup: BeautifulSoup) -> str:
        """Final fallback for description extraction."""
        # Look for any text that contains job-related keywords
        all_text = soup.get_text(separator='\n')

        # Find the section with the most job-related content
        paragraphs = [p.strip() for p in all_text.split('\n\n') if p.strip()]

        best_paragraph = ""
        best_score = 0

        for para in paragraphs:
            if len(para) > 100:
                score = self._calculate_content_quality(para)
                if score > best_score:
                    best_score = score
                    best_paragraph = para

        return best_paragraph if best_score > 10 else "N/A"

    def _clean_extracted_content(self, text: str) -> str:
        """Clean extracted content by removing noise and formatting."""
        if not text:
            return ""

        # Remove specific noise patterns
        noise_patterns = [
            r'Firmenname\s+für EXPERT-Mitglieder sichtbar',
            r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}',
            r'Jetzt registrieren\s*Einloggen',
            r'kostenlos registrieren',
            r'Als registriertes Mitglied.*kann.*bewerben',
            r'Ähnliche Projekte.*',
            r'Sie suchen Freelancer\?.*',
            r'Kategorien und Skills.*',
            r'Projekt Insights.*',
            r'für einen unserer.*kann.*bewerben',
            r'95% Remote: Solution.*',
            r'Java Entwickler.*',
            r'DevOps Public.*',
            r'Informations- und Kommunikationstechnologie.*',
            r'Systementwickler und -analytiker.*',
            r'Softwareentwicklung.*',
            r'Bauwesen und Bergbau.*',
            r'Leiter Kindertagesstätte.*',
        ]

        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        # Clean up formatting
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single
        text = text.strip()

        return text

    def _extract_structured_sections(self, text: str) -> str:
        """Extract structured sections like Aufgaben, Anforderungen from text."""
        sections = []

        # Look for common section headers
        section_patterns = [
            (r'Aufgaben\s*(?:\n|\r|\r\n)(.*?)(?=\n\s*(?:Anforderungen|Profil|Erfahrungen|Start|Dauer)|$)',
             'Aufgaben'),
            (r'Anforderungen\s*(?:\n|\r|\r\n)(.*?)(?=\n\s*(?:Profil|Erfahrungen|Start|Dauer|Aufgaben)|$)',
             'Anforderungen'),
            (r'Profil\s*(?:\n|\r|\r\n)(.*?)(?=\n\s*(?:Erfahrungen|Start|Dauer|Aufgaben|Anforderungen)|$)',
             'Profil'),
            (r'Erfahrungen?\s*(?:\n|\r|\r\n)(.*?)(?=\n\s*(?:Start|Dauer|Aufgaben|Anforderungen|Profil)|$)',
             'Erfahrungen')
        ]

        for pattern, section_name in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if len(content) > 20:  # Substantial content
                    sections.append(f"**{section_name}:**\n{content}")

        # Also look for project details
        details_match = re.search(r'Start:\s*(.*?)\n.*?Dauer:\s*(.*?)\n.*?Workload:\s*(.*?)(?:\n|$)', text, re.IGNORECASE)
        if details_match:
            start, dauer, workload = details_match.groups()
            sections.append(f"**Projekt Details:**\n- Start: {start.strip()}\n- Dauer: {dauer.strip()}\n- Workload: {workload.strip()}")

        return '\n\n'.join(sections) if sections else text

    def _clean_description_text(self, text: str) -> str:
        """Clean up extracted description text."""
        if not text:
            return ""

        # Remove common noise patterns
        noise_patterns = [
            r'Firmenname\s*für EXPERT-Mitglieder sichtbar',
            r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}',
            r'Jetzt registrieren\s*Einloggen',
            r'kostenlos registrieren',
            r'Als registriertes Mitglied.*kann.*bewerben',
            r'Ähnliche Projekte.*',
            r'Sie suchen Freelancer\?.*',
            r'Kategorien und Skills.*',
            r'Projekt Insights.*',
        ]

        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        # Clean up whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single
        text = text.strip()

        return text

    def _is_likely_job_content(self, text: str) -> bool:
        """Check if text is likely to be actual job description content."""
        # Positive indicators
        job_keywords = [
            'aufgaben', 'anforderungen', 'profil', 'erfahrung',
            'entwicklung', 'koordination', 'steuerung', 'planung',
            'mehrjährige erfahrung', 'abgeschlossene', 'kenntnisse',
            'start:', 'dauer:', 'workload:', 'remote'
        ]

        # Check for job-related keywords
        has_job_keywords = any(keyword in text.lower() for keyword in job_keywords)

        # Check for substantial content (not just dates/locations)
        has_substance = len(text) > 100

        # Avoid obvious noise
        noise_indicators = [
            'registrieren', 'einloggen', 'expert-mitglieder',
            'kostenlos', 'ähnliche projekte', 'sie suchen'
        ]
        no_noise = not any(indicator in text.lower() for indicator in noise_indicators)

        return has_job_keywords and has_substance and no_noise

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