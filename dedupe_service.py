"""
Dedupe Service for Project Bot

Handles provider-aware deduplication of project URLs to prevent reprocessing.
"""

import os
import json
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlunparse


class DedupeService:
    """
    Service for deduplicating project URLs across providers.

    Uses provider_id + canonical_url as the dedupe key.
    """

    def __init__(self, state_dir: str = "projects"):
        """
        Initialize the dedupe service.

        Args:
            state_dir: Directory where processed URLs are tracked
        """
        self.state_dir = state_dir
        self.processed_file = os.path.join(state_dir, ".processed_urls.json")
        self._ensure_state_dir()
        self._load_processed()

    def _ensure_state_dir(self) -> None:
        """Ensure the state directory exists."""
        os.makedirs(self.state_dir, exist_ok=True)

    def _load_processed(self) -> None:
        """Load the set of processed URLs from disk."""
        if os.path.exists(self.processed_file):
            try:
                with open(self.processed_file, 'r', encoding='utf-8') as f:
                    self.processed = set(json.load(f))
            except (json.JSONDecodeError, FileNotFoundError):
                self.processed = set()
        else:
            self.processed = set()

    def _save_processed(self) -> None:
        """Save the processed URLs to disk."""
        with open(self.processed_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.processed), f, indent=2)

    def canonicalize_url(self, url: str, provider_id: str) -> str:
        """
        Canonicalize a URL for deduplication.

        Provider-specific rules:
        - Strip tracking parameters
        - Normalize host/path

        Args:
            url: The URL to canonicalize
            provider_id: Provider identifier for custom rules

        Returns:
            Canonicalized URL string
        """
        parsed = urlparse(url)

        # Remove common tracking parameters
        query_params = parse_qs(parsed.query)
        tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                          'fbclid', 'gclid', 'msclkid', 'ref', 'source'}

        # Provider-specific tracking params
        if provider_id == 'freelancermap':
            tracking_params.update({'ref', 'source'})

        # Remove tracking params
        filtered_query = {k: v for k, v in query_params.items() if k not in tracking_params}

        # Reconstruct query string
        query = '&'.join(f"{k}={v[0]}" for k, v in filtered_query.items()) if filtered_query else ''

        # Normalize path (remove trailing slashes, etc.)
        path = parsed.path.rstrip('/')

        # Reconstruct canonical URL
        canonical = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            parsed.params,
            query,
            ''  # Remove fragment
        ))

        return canonical

    def already_processed(self, provider_id: str, canonical_url: str) -> bool:
        """
        Check if a URL has already been processed.

        Args:
            provider_id: Provider identifier
            canonical_url: Canonicalized URL

        Returns:
            True if already processed, False otherwise
        """
        key = f"{provider_id}:{canonical_url}"
        return key in self.processed

    def mark_processed(self, provider_id: str, canonical_url: str) -> None:
        """
        Mark a URL as processed.

        Args:
            provider_id: Provider identifier
            canonical_url: Canonicalized URL
        """
        key = f"{provider_id}:{canonical_url}"
        self.processed.add(key)
        self._save_processed()

    def get_processed_count(self, provider_id: Optional[str] = None) -> int:
        """
        Get the count of processed URLs.

        Args:
            provider_id: Optional provider filter

        Returns:
            Number of processed URLs
        """
        if provider_id:
            return len([k for k in self.processed if k.startswith(f"{provider_id}:")])
        return len(self.processed)