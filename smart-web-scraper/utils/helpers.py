"""Small standalone helpers that don't fit anywhere else."""
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return all([parsed.scheme in ("http", "https"), parsed.netloc])
    except (ValueError, AttributeError):
        return False


def clean_text(value: str) -> str:
    """Collapses whitespace/newlines from scraped HTML text nodes."""
    if not value:
        return ""
    return " ".join(value.split()).strip()
