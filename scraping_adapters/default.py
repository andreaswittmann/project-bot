"""
Default Scraping Adapter for Project Bot

Fallback adapter when no provider-specific adapter is available.
"""

import logging
from typing import Dict, Any
from scraping_adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class DefaultAdapter(BaseAdapter):
    """
    Default scraping adapter that provides basic fallback functionality.

    This adapter attempts to extract minimal information from URLs
    when no provider-specific adapter is available.
    """

    def parse(self, url: str) -> Dict[str, Any]:
        """
        Parse a project URL with minimal fallback logic.

        Args:
            url: Project URL to scrape

        Returns:
            Dictionary with basic project schema

        Raises:
            Exception: If parsing fails
        """
        logger.warning(f"Using default adapter for URL: {url} - no provider-specific adapter available")

        # Basic schema with minimal information
        schema = {
            'title': f'Project from {self.provider_id}',
            'description': f'Project scraped via default adapter from {url}',
            'company': 'Unknown',
            'location': 'Unknown',
            'details': f'Source URL: {url}',
            'schlagworte': [],
            'beschreibung': f'This project was found at {url} but no specific adapter was available for provider {self.provider_id}.'
        }

        logger.info("Default adapter parsing complete", extra={
            'url': url,
            'title': schema['title']
        })

        return schema

    def get_provider_name(self) -> str:
        """
        Get human-readable provider name.

        Returns:
            Provider display name with fallback indicator
        """
        base_name = super().get_provider_name()
        return f"{base_name} (Default Adapter)"