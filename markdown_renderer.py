"""
Markdown Renderer for Project Bot

Renders normalized project schema to markdown format with consistent frontmatter.
Preserves existing body structure for backward compatibility.
"""

import datetime
from typing import Dict, Any


class MarkdownRenderer:
    """
    Renders project data to markdown format.

    Adds provider metadata to frontmatter while preserving
    the existing body structure.
    """

    def render(self, schema: Dict[str, Any], provider_meta: Dict[str, Any]) -> str:
        """
        Render project schema to markdown string.

        Args:
            schema: Normalized project schema from adapter
            provider_meta: Provider metadata dict

        Returns:
            Complete markdown string with frontmatter
        """
        lines = []

        # Build frontmatter
        frontmatter = self._build_frontmatter(schema, provider_meta)
        lines.extend(["---", frontmatter, "---", ""])

        # Title
        title = schema.get("title", "N/A")
        lines.append(f"# {title}")

        # URL
        url = schema.get("url", "")
        if url:
            lines.append(f"**URL:** [{url}]({url})")

        # Details section
        details = schema.get("details", {})
        if details:
            lines.append("## Details")
            for key, value in details.items():
                if value:
                    # Capitalize first letter of key for display
                    display_key = key.replace("_", " ").title()
                    lines.append(f"- **{display_key}:** {value}")

        # Schlagworte section
        schlagworte = schema.get("schlagworte", [])
        lines.append("\n## Schlagworte")
        if schlagworte:
            lines.append(", ".join(schlagworte))
        else:
            lines.append("N/A")

        # Beschreibung section
        description = schema.get("description", "")
        if description:
            lines.append("\n## Beschreibung")
            lines.append(description.strip())

        return "\n".join(lines)

    def _build_frontmatter(self, schema: Dict[str, Any], provider_meta: Dict[str, Any]) -> str:
        """
        Build YAML frontmatter from schema and provider metadata.

        Args:
            schema: Project schema
            provider_meta: Provider metadata

        Returns:
            YAML frontmatter string
        """
        frontmatter = {}

        # Provider metadata
        frontmatter["provider_id"] = provider_meta.get("provider_id")
        frontmatter["provider_name"] = provider_meta.get("provider_name")
        frontmatter["collection_channel"] = provider_meta.get("collection_channel")
        frontmatter["collected_at"] = provider_meta.get("collected_at")

        # Project metadata
        frontmatter["title"] = schema.get("title", "N/A")
        frontmatter["company"] = schema.get("company", "N/A")
        frontmatter["reference_id"] = schema.get("reference_id", "N/A")
        frontmatter["source_url"] = schema.get("url", "")
        frontmatter["state"] = "scraped"

        # Convert to YAML format
        yaml_lines = []
        for key, value in frontmatter.items():
            if isinstance(value, str):
                # Escape quotes if needed
                yaml_lines.append(f'{key}: "{value}"')
            else:
                yaml_lines.append(f"{key}: {value}")

        return "\n".join(yaml_lines)