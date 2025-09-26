"""
Base Scraping Adapter for Project Bot

Defines the interface for provider-specific scraping adapters.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAdapter(ABC):
    """
    Abstract base class for scraping adapters.

    Each provider implements a concrete adapter that normalizes
    scraped data into a unified schema.
    """

    def __init__(self, provider_id: str, config: Dict[str, Any]):
        """
        Initialize the adapter.

        Args:
            provider_id: Provider identifier
            config: Provider-specific configuration
        """
        self.provider_id = provider_id
        self.config = config

    @abstractmethod
    def parse(self, url: str) -> Dict[str, Any]:
        """
        Parse a project URL and return normalized data.

        Args:
            url: Project URL to scrape

        Returns:
            Dictionary with unified project schema

        Raises:
            Exception: If parsing fails
        """
        pass

    def get_provider_name(self) -> str:
        """
        Get human-readable provider name.

        Returns:
            Provider display name
        """
        return self.config.get('name', self.provider_id.title())