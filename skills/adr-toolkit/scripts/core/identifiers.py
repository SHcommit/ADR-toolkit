"""ADR ID calculation, filename parsing, and title slugification."""
import re
from pathlib import Path
from typing import Optional

ADR_FILENAME_RE = re.compile(r"^(\d{4})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_filename(filename: str) -> Optional[tuple]:
    match = ADR_FILENAME_RE.match(filename)
    if not match:
        return None
    return int(match.group(1)), match.group(2)


def next_id(adr_dir: Path) -> int:
    existing_ids = []
    for entry in adr_dir.glob("*.md"):
        parsed = parse_filename(entry.name)
        if parsed:
            existing_ids.append(parsed[0])
    return max(existing_ids, default=0) + 1


def format_filename(adr_id: int, slug: str) -> str:
    return f"{adr_id:04d}-{slug}.md"


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return re.sub(r"-+", "-", slug)


def validate_slug(slug: str) -> str:
    if not SLUG_RE.fullmatch(slug):
        raise ValueError("slug must match [a-z0-9]+(?:-[a-z0-9]+)*")
    return slug


def slug_for_title(title: str, explicit_slug: Optional[str] = None) -> str:
    if explicit_slug is not None:
        return validate_slug(explicit_slug)
    return slugify(title) or "decision"


def find_by_number(adr_dir: Path, number: int) -> Optional[Path]:
    for entry in adr_dir.glob(f"{number:04d}-*.md"):
        return entry
    return None
