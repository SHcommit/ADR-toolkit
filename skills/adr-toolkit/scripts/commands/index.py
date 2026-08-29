"""Regenerate the multi-view ADR index (README.md) for a decision directory."""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core import identifiers

SKIP_FILES = {"README.md", "adr-template.md"}


def run(args) -> dict:
    adr_dir = Path(args.dir)
    entries = []

    for entry in sorted(adr_dir.glob("*.md")):
        if entry.name in SKIP_FILES:
            continue
        parsed = identifiers.parse_filename(entry.name)
        if parsed is None:
            continue
        data, _ = fm.parse(entry.read_text(encoding="utf-8"))
        entries.append({
            "id": data.get("id", f"ADR-{parsed[0]:04d}"),
            "filename": entry.name,
            "title": data.get("title", parsed[1]),
            "status": data.get("status", "unknown"),
            "date": data.get("date", ""),
            "tags": data.get("tags", []),
            "affected_paths": data.get("affected_paths", []),
        })

    (adr_dir / "README.md").write_text(_render(entries), encoding="utf-8")

    return {"ok": True, "operation": "index", "count": len(entries), "path": str(adr_dir / "README.md")}


def _render(entries: list) -> str:
    lines = ["# Decision Log", ""]

    lines.append("## By status")
    lines.append("")
    by_status: dict = {}
    for entry in entries:
        by_status.setdefault(entry["status"], []).append(entry)
    for status in sorted(by_status):
        lines.append(f"### {status.capitalize()}")
        for entry in sorted(by_status[status], key=lambda e: e["filename"]):
            lines.append(f"- [{entry['id']} — {entry['title']}]({entry['filename']})")
        lines.append("")

    lines.append("## By tag")
    lines.append("")
    by_tag: dict = {}
    for entry in entries:
        for tag in entry["tags"]:
            by_tag.setdefault(tag, []).append(entry)
    for tag in sorted(by_tag):
        lines.append(f"### {tag}")
        for entry in sorted(by_tag[tag], key=lambda e: e["filename"]):
            lines.append(f"- [{entry['id']} — {entry['title']}]({entry['filename']})")
        lines.append("")

    lines.append("## By affected path")
    lines.append("")
    by_path: dict = {}
    for entry in entries:
        for path in entry["affected_paths"]:
            by_path.setdefault(path, []).append(entry)
    for path in sorted(by_path):
        lines.append(f"### `{path}`")
        for entry in sorted(by_path[path], key=lambda e: e["filename"]):
            lines.append(f"- [{entry['id']} — {entry['title']}]({entry['filename']})")
        lines.append("")

    lines.append("## Chronological (newest first)")
    lines.append("")
    for entry in sorted(entries, key=lambda e: e["date"], reverse=True):
        lines.append(f"- {entry['date']} — [{entry['id']} — {entry['title']}]({entry['filename']})")

    return "\n".join(lines) + "\n"
