"""ADR ID calculation, filename parsing, and title slugification."""
import re
from pathlib import Path
from typing import Optional

ADR_FILENAME_RE = re.compile(r"^(\d{4})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")


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
