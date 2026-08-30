#!/usr/bin/env python3
"""Sync skills/adr-toolkit/VERSION into every manifest that duplicates it.

Repo tooling — not part of the distributable skills/adr-toolkit/ package.
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = REPO_ROOT / "skills" / "adr-toolkit" / "VERSION"
SKILL_MD_PATH = REPO_ROOT / "skills" / "adr-toolkit" / "SKILL.md"

# (manifest path relative to REPO_ROOT, key path within its JSON)
# Only manifests confirmed to carry their own "version" field are listed —
# a manifest with no such field is never modified to add one.
MANIFEST_SPECS = [
    (REPO_ROOT / ".claude-plugin" / "plugin.json", ["version"]),
    (REPO_ROOT / "adapters" / "gemini-cli" / "gemini-extension.json", ["version"]),
]

VERSION_LINE_RE = re.compile(r"^version:\s*\S+$", re.MULTILINE)


def sync(version_file: Path, manifest_specs: list, check_only: bool) -> list:
    version = version_file.read_text(encoding="utf-8").strip()
    changed = []
    for path, key_path in manifest_specs:
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        target = data
        for key in key_path[:-1]:
            if key not in target:
                target = None
                break
            target = target[key]
        if target is None or key_path[-1] not in target:
            continue
        if target[key_path[-1]] == version:
            continue
        changed.append(path)
        if not check_only:
            target[key_path[-1]] = version
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return changed


def sync_skill_md(version_file: Path, skill_md_path: Path, check_only: bool) -> bool:
    if not skill_md_path.is_file():
        return False
    version = version_file.read_text(encoding="utf-8").strip()
    text = skill_md_path.read_text(encoding="utf-8")
    match = VERSION_LINE_RE.search(text)
    if match is None or match.group() == f"version: {version}":
        return False
    if not check_only:
        new_text = VERSION_LINE_RE.sub(f"version: {version}", text, count=1)
        skill_md_path.write_text(new_text, encoding="utf-8")
    return True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    changed = sync(VERSION_FILE, MANIFEST_SPECS, check_only=args.check)
    if sync_skill_md(VERSION_FILE, SKILL_MD_PATH, check_only=args.check):
        changed.append(SKILL_MD_PATH)

    if args.check and changed:
        for path in changed:
            print(f"drift: {path.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1
    for path in changed:
        print(f"synced: {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
