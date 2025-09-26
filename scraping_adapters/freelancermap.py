"""
FreelancerMap Scraping Adapter

Adapter for scraping FreelancerMap project pages.
Wraps the existing parse_html.parse_project() function.
"""

from typing import Dict, Any
from scraping_adapters.base import BaseAdapter
from parse_html import parse_project


class FreelancerMapAdapter(BaseAdapter):
    """
    Scraping adapter for FreelancerMap provider.

    Uses the existing parse_html.parse_project() and normalizes
    the output to the unified schema.
    """

    def parse(self, url: str) -> Dict[str, Any]:
        """
        Parse a FreelancerMap project URL.

        Args:
            url: FreelancerMap project URL

        Returns:
            Normalized project schema dictionary

        Raises:
            Exception: If parsing fails
        """
        # Use existing parsing logic
        raw_data = parse_project(url)

        # Normalize to unified schema
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

        return normalized