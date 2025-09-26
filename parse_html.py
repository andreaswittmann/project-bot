import argparse
import datetime as dt
import json
import os
import re
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup, Tag

from state_manager import ProjectStateManager

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

LABELS = [
    "Start", "Von", "Auslastung", "Eingestellt", "Ansprechpartner:",
    "Projekt-ID:", "Branche", "Vertragsart", "Einsatzart",
    "Laufzeit", "Ort", "Sprachen",
]

def fetch_html(url: str) -> str:
    with requests.Session() as s:
        s.headers.update(HEADERS)
        r = s.get(url, timeout=20)
        r.raise_for_status()
        return r.text

def _normalize_ws(txt: str) -> str:
    return re.sub(r"\s+", " ", txt).strip()

def html_to_markdown(tag: Tag) -> str:
    """Recursively convert a tag to a markdown string."""
    if isinstance(tag, str):
        return _normalize_ws(tag)
    
    # Process children first
    content = "".join(html_to_markdown(child) for child in tag.contents)

    # Convert block-level tags to markdown
    if tag.name == "p":
        return f"\n{content.strip()}\n"
    if tag.name == "ul":
        return f"\n{content.strip()}\n"
    if tag.name == "li":
        stripped = content.strip()
        if stripped:
            return f"- {stripped}\n"
        else:
            return ""
    if tag.name == "div":
        # For divs with multiple children, join with spaces to keep inline
        if len(tag.contents) > 1:
            child_contents = []
            for child in tag.contents:
                if isinstance(child, Tag):
                    child_contents.append(html_to_markdown(child))
                elif isinstance(child, str):
                    child_contents.append(_normalize_ws(child))
            return " ".join(child_contents).strip()
        else:
            return content
    
    # Convert inline tags
    if tag.name in ["strong", "b"]:
        return f"**{content.strip()}**"
    if tag.name in ["em", "i"]:
        return f"*{content.strip()}*"
    if tag.name == "br":
        return "\n"
        
    return content

def get_heading_block(soup: BeautifulSoup, heading_text: str) -> Optional[str]:
    """
    Find the section for a heading and convert its content to markdown.
    
    Args:
        soup: BeautifulSoup object containing the parsed HTML
        heading_text: Text to search for in heading tags
        
    Returns:
        Markdown content of the section or None if not found
    """
    hdr = soup.find(lambda tag: tag.name in {"h1", "h2", "h3", "h4"}
                              and tag.get_text(strip=True).lower().startswith(heading_text.lower()))
    if not hdr:
        return None

    content_tags = []
    for sib in hdr.next_siblings:
        if isinstance(sib, Tag):
            if sib.name in {"h1", "h2", "h3", "h4"}:
                break
            content_tags.append(sib)
            
    if not content_tags:
        return None

    # Process each top-level tag under the heading
    markdown_parts = [html_to_markdown(tag) for tag in content_tags]

    # Join with newlines to separate sections/lists
    full_text = "\n".join(markdown_parts).strip()
    return re.sub(r'\n{3,}', '\n\n', full_text) or None

def extract_kv_labels(soup: BeautifulSoup, labels: List[str]) -> Dict[str, str]:
    """
    Robust label-value extraction:
    scan visible text stream and pair each known label with its next value.
    """
    text_stream = list(soup.stripped_strings)
    out: Dict[str, str] = {}

    # build quick lookup allowing labels with and without trailing colon
    canonical = {}
    for lab in labels:
        key = lab.rstrip(":")
        canonical[lab] = key
        canonical[key] = key

    for i, token in enumerate(text_stream):
        token_clean = token.rstrip(":")
        if token in canonical or token_clean in canonical:
            key = canonical.get(token, canonical.get(token_clean, token_clean))
            # prefer the immediate next non-empty token as the value
            if i + 1 < len(text_stream):
                value = text_stream[i+1].strip()
                # Skip obvious "placeholder" words that sometimes appear between label and value
                if value in {"", ":", "•"} and i + 2 < len(text_stream):
                    value = text_stream[i+2].strip()
                # Special handling for Ansprechpartner to include full name
                if key == "Ansprechpartner" and i + 2 < len(text_stream):
                    next_token = text_stream[i+2].strip()
                    if next_token and next_token not in {"", ":", "•"} and next_token not in canonical:
                        value += " " + next_token
                if value:
                    out[key] = value
    return out

def extract_keywords(soup: BeautifulSoup) -> List[str]:
    """
    Find the "Schlagworte" (Keywords) section and extract all associated terms.
    This function searches for a `div` with the class `keywords-container`
    and extracts all keywords from the `span` tags within it. This approach is
    the most reliable as it targets the specific container for the keyword data.
    """
    # Find the container of the keywords by its class name
    container = soup.find('div', class_='keywords-container')
    if not container:
        return []

    # Extract all keyword strings from the `<span>` tags within the container
    keywords = [span.get_text(strip=True) for span in container.find_all("span", class_="keyword")]
    
    # Return the list of non-empty keywords
    return [kw for kw in keywords if kw]

def parse_project(url: str, html: Optional[str] = None) -> Dict:
    """
    Parse a FreelancerMap project page and extract structured data.

    Args:
        url: URL of the project page to parse
        html: Optional pre-fetched HTML content to avoid re-fetching

    Returns:
        Dictionary containing project metadata and content

    Raises:
        requests.RequestException: If HTML fetching fails
    """
    if html is None:
        html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    title = soup.find("h1")
    title_text = title.get_text(strip=True) if title else None

    beschreibung = get_heading_block(soup, "Beschreibung")

    fields = extract_kv_labels(soup, LABELS)

    # Extract company from "Eingestellt von" section
    company_text = None
    
    # First, try to find the div containing "Eingestellt von"
    eingestellt_div = soup.find('div', class_='project-body-info-title', string=re.compile(r"Eingestellt von", re.IGNORECASE))
    if eingestellt_div:
        # The company is in the next sibling div
        parent = eingestellt_div.parent
        if parent:
            # Look for the next div sibling that contains the company name
            for sibling in eingestellt_div.next_siblings:
                if hasattr(sibling, 'get_text'):
                    company_text = sibling.get_text(strip=True)
                    if company_text:  # Only take non-empty text
                        break
    
    # Fallback to JSON-LD if DOM extraction fails
    if not company_text:
        json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                if data.get('@type') == 'Organization':
                    company_text = data.get('name')
                    break
            except (json.JSONDecodeError, TypeError):
                continue

    result = {
        "url": url,
        "titel": title_text,
        "beschreibung": beschreibung,
        "schlagworte": extract_keywords(soup),
        "company": company_text,
        "start": fields.get("Start"),
        "von": fields.get("Von"),
        "auslastung": fields.get("Auslastung"),
        "eingestellt": fields.get("Eingestellt"),
        "ansprechpartner": fields.get("Ansprechpartner"),
        "projekt_id": fields.get("Projekt-ID"),
        "branche": fields.get("Branche"),
        "vertragsart": fields.get("Vertragsart"),
        "einsatzart": fields.get("Einsatzart"),
    }
    return result

def to_markdown(data: Dict) -> str:
    """
    Convert project data dictionary to markdown format.
    
    Args:
        data: Project data dictionary from parse_project()
        
    Returns:
        Formatted markdown string
    """
    title = data.get("titel", "N/A")
    lines = [f"# {title}"]

    lines.append(f"**URL:** [{data.get('url')}]({data.get('url')})")
    lines.append("## Details")
    details = {
        "Start": data.get("start"),
        "Von": data.get("von"),
        "Auslastung": data.get("auslastung"),
        "Eingestellt": data.get("eingestellt"),
        "Ansprechpartner": data.get("ansprechpartner"),
        "Projekt-ID": data.get("projekt_id"),
        "Branche": data.get("branche"),
        "Vertragsart": data.get("vertragsart"),
        "Einsatzart": data.get("einsatzart"),
    }
    for key, value in details.items():
        if value:
            lines.append(f"- **{key}:** {value}")

    lines.append("\n## Schlagworte")
    schlagworte = data.get("schlagworte")
    if schlagworte:
        lines.append(", ".join(schlagworte))
    else:
        lines.append("N/A")

    if data.get("beschreibung"):
        lines.append("\n## Beschreibung")
        # Post-process description to add line breaks and proper formatting
        beschreibung = data.get("beschreibung")
        # Fix bullet points: add space after - if missing (but don't break hyphens in words)
        beschreibung = re.sub(r'(?<!\w)(-)(\w)', r'\1 \2', beschreibung)
        # Remove empty bullet lines
        beschreibung = re.sub(r'^\s*-\s*$', '', beschreibung, flags=re.MULTILINE)
        # Convert • bullets to - bullets on separate lines
        beschreibung = re.sub(r' • ', r'\n- ', beschreibung)
        beschreibung = re.sub(r'^• ', r'- ', beschreibung, flags=re.MULTILINE)
        # Convert - bullets to separate lines
        beschreibung = re.sub(r' - ', r'\n- ', beschreibung)
        beschreibung = re.sub(r'^ - ', r'- ', beschreibung, flags=re.MULTILINE)
        # Split specific labels to new lines
        beschreibung = re.sub(r' (Sprachen: )', r'\n\1', beschreibung)
        # Clean up excessive newlines
        beschreibung = re.sub(r'\n{3,}', '\n\n', beschreibung)
        lines.append(beschreibung.strip())

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Parse a freelancermap.de project page and save it as markdown.")
    parser.add_argument("url", nargs='?', default=None, help="The URL of the project page to parse.")
    parser.add_argument("-o", "--output", help="The output directory for the markdown file.")

    args = parser.parse_args()

    if not args.url:
        parser.print_help()
        return

    data = parse_project(args.url)

    # Generate Markdown
    markdown_content = to_markdown(data)

    # Create filename with validation and fallbacks
    from utils.filename import create_safe_filename
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    original_title = data.get("titel", "project")
    filename = create_safe_filename(original_title, timestamp)

    # Log filename creation for debugging
    print(f"📄 Created filename: {filename} (from title: '{original_title}')")

    # Define output path and save file
    output_dir = args.output or "projects"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    # Write initial markdown content
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    # Initialize project with state management
    state_manager = ProjectStateManager(output_dir)

    # Prepare metadata for frontmatter
    metadata = {
        'title': data.get('titel', 'N/A'),
        'company': data.get('company', 'N/A'),
        'reference_id': data.get('projekt_id', 'N/A'),
        'scraped_date': dt.datetime.now().isoformat(),
        'source_url': data.get('url', args.url),
        'state': 'scraped'
    }

    # Initialize project with frontmatter
    success = state_manager.initialize_project(output_path, metadata)

    if success:
        print(f"Project saved to {output_path} with state management initialized")
    else:
        print(f"Project saved to {output_path} but failed to initialize state management")

if __name__ == "__main__":
    main()