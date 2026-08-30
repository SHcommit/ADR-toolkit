"""Regenerate the multi-view ADR index (README.md) for a decision directory."""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.locale import load_locale

SKIP_FILES = {"README.md", "adr-template.md"}

# Last-resort English headers, used when even the English locale file is
# unavailable — e.g. a copy-based install (permitted by
# adapters/generic/README.md) that omitted scripts/i18n/. Localization is
# cosmetic; a missing translation table must degrade, never crash (§17.1).
FALLBACK_STRINGS = {
    "decision_log_title": "Decision Log",
    "by_status": "By status",
    "by_tag": "By tag",
    "by_affected_path": "By affected path",
    "chronological": "Chronological (newest first)",
}


def run(args) -> dict:
    adr_dir = Path(args.dir)
    locale = getattr(args, "locale", None) or "en"
    strings = load_locale(locale)
    entries = []
    warnings = []

    for entry in sorted(adr_dir.glob("*.md")):
        if entry.name in SKIP_FILES:
            continue
        parsed = identifiers.parse_filename(entry.name)
        if parsed is None:
            continue
        try:
            data, _ = fm.parse(entry.read_text(encoding="utf-8"))
        except fm.FrontmatterError as exc:
            warnings.append({"code": "BAD_FRONTMATTER", "file": entry.name, "detail": str(exc)})
            continue
        entries.append({
            "id": data.get("id", f"ADR-{parsed[0]:04d}"),
            "filename": entry.name,
            "title": data.get("title", parsed[1]),
            "status": data.get("status", "unknown"),
            "date": data.get("date", ""),
            "tags": data.get("tags", []),
            "affected_paths": data.get("affected_paths", []),
        })

    (adr_dir / "README.md").write_text(_render(entries, strings), encoding="utf-8")

    return {
        "ok": True,
        "operation": "index",
        "count": len(entries),
        "path": str(adr_dir / "README.md"),
        "warnings": warnings,
    }


def _s(strings: dict, key: str) -> str:
    """Header lookup that survives a missing/partial English base."""
    return strings.get(key, FALLBACK_STRINGS[key])


def _render(entries: list, strings: dict) -> str:
    lines = [f"# {_s(strings, 'decision_log_title')}", ""]

    lines.append(f"## {_s(strings, 'by_status')}")
    lines.append("")
    by_status: dict = {}
    for entry in entries:
        by_status.setdefault(entry["status"], []).append(entry)
    for status in sorted(by_status):
        label = strings.get(f"status.{status}", status.capitalize())
        lines.append(f"### {label}")
        for entry in sorted(by_status[status], key=lambda e: e["filename"]):
            lines.append(f"- [{entry['id']} — {entry['title']}]({entry['filename']})")
        lines.append("")

    lines.append(f"## {_s(strings, 'by_tag')}")
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

    lines.append(f"## {_s(strings, 'by_affected_path')}")
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

    lines.append(f"## {_s(strings, 'chronological')}")
    lines.append("")
    for entry in sorted(entries, key=lambda e: e["date"], reverse=True):
        lines.append(f"- {entry['date']} — [{entry['id']} — {entry['title']}]({entry['filename']})")

    return "\n".join(lines) + "\n"
