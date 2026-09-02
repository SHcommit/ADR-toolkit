#!/usr/bin/env python3
"""Sync skills/adr-toolkit/VERSION and SKILL.md's description into every
manifest that duplicates them.

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
    (REPO_ROOT / "adapters" / "antigravity" / "plugin.json", ["version"]),
]

# SKILL.md's frontmatter `description:` is the single canonical source; every
# manifest below duplicates it for its own harness's format and is synced
# from it the same way MANIFEST_SPECS entries are synced from VERSION.
DESCRIPTION_MANIFEST_SPECS = [
    (REPO_ROOT / ".claude-plugin" / "plugin.json", ["description"]),
    (REPO_ROOT / "adapters" / "codex" / ".codex-plugin" / "plugin.json", ["description"]),
    (REPO_ROOT / "adapters" / "gemini-cli" / "gemini-extension.json", ["description"]),
    (REPO_ROOT / "adapters" / "antigravity" / "plugin.json", ["description"]),
]

VERSION_LINE_RE = re.compile(r"^version:\s*\S+$", re.MULTILINE)
VERSION_FORMAT_RE = re.compile(r"\d+\.\d+\.\d+(-[\w.]+)?")
DESCRIPTION_LINE_RE = re.compile(r"^description:[ \t]*(.+)$", re.MULTILINE)


def read_version(version_file: Path) -> str:
    """Read VERSION and reject anything that isn't a plausible semver string.

    Without this, an empty or corrupted VERSION propagates silently into every
    manifest and then --check passes forever, because everything agrees on the
    same garbage.
    """
    version = version_file.read_text(encoding="utf-8").strip()
    if not VERSION_FORMAT_RE.fullmatch(version):
        raise SystemExit(f"invalid VERSION: {version!r}")
    return version


def replace_version_line(text: str, version: str) -> str:
    """Rewrite SKILL.md's frontmatter `version:` line to `version`.

    The replacement is a callable, not a template string, so re.sub never
    interprets backslash escapes (\\g<0>, \\1, ...) that a corrupted version
    might contain. read_version() should already have rejected such a value;
    this keeps the substitution literal regardless of how it is reached.
    """
    return VERSION_LINE_RE.sub(lambda _: f"version: {version}", text, count=1)


def read_description(skill_md_path: Path) -> str:
    """Read the canonical `description:` value from SKILL.md's frontmatter."""
    text = skill_md_path.read_text(encoding="utf-8")
    match = DESCRIPTION_LINE_RE.search(text)
    if match is None:
        raise SystemExit(f"no description: line found in {skill_md_path}")
    return match.group(1).strip()


def sync(version_file: Path, manifest_specs: list, check_only: bool) -> list:
    return _sync_value(read_version(version_file), manifest_specs, check_only)


def sync_descriptions(skill_md_path: Path, manifest_specs: list, check_only: bool) -> list:
    return _sync_value(read_description(skill_md_path), manifest_specs, check_only)


def _sync_value(value: str, manifest_specs: list, check_only: bool) -> list:
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
        if target[key_path[-1]] == value:
            continue
        changed.append(path)
        if not check_only:
            target[key_path[-1]] = value
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
    return changed


def sync_skill_md(version_file: Path, skill_md_path: Path, check_only: bool) -> bool:
    if not skill_md_path.is_file():
        return False
    version = read_version(version_file)
    text = skill_md_path.read_text(encoding="utf-8")
    match = VERSION_LINE_RE.search(text)
    if match is None or match.group() == f"version: {version}":
        return False
    if not check_only:
        new_text = replace_version_line(text, version)
        skill_md_path.write_text(new_text, encoding="utf-8")
    return True


def require_known_paths() -> None:
    """Fail loudly if a manifest this repo is supposed to track has vanished.

    sync()/sync_skill_md() stay tolerant of missing paths so tests can pass
    partial fixture sets, but the CLI runs against the hardcoded
    MANIFEST_SPECS/SKILL_MD_PATH — a renamed or deleted manifest there must
    not silently drop out of the drift check and leave CI green forever.
    """
    all_specs = MANIFEST_SPECS + DESCRIPTION_MANIFEST_SPECS
    tracked_paths = {p for p, _ in all_specs}
    missing = [p for p in tracked_paths if not p.is_file()]
    if not VERSION_FILE.is_file():
        missing.append(VERSION_FILE)
    if not SKILL_MD_PATH.is_file():
        missing.append(SKILL_MD_PATH)
    if missing:
        names = ", ".join(_display_path(p) for p in sorted(missing, key=str))
        raise SystemExit(f"missing tracked file(s): {names}")

    keyless = []
    for path, key_path in all_specs:
        target = json.loads(path.read_text(encoding="utf-8"))
        for key in key_path:
            if not isinstance(target, dict) or key not in target:
                keyless.append((path, key_path[-1]))
                break
            target = target[key]
    if keyless:
        names = ", ".join(f"{_display_path(p)} ({key})" for p, key in keyless)
        raise SystemExit(f"tracked manifest(s) lost a tracked key: {names}")

    untracked = discover_untracked_manifests()
    if untracked:
        names = ", ".join(_display_path(p) for p in sorted(untracked, key=str))
        raise SystemExit(f"untracked plugin/extension manifest(s) found: {names}")


def discover_untracked_manifests() -> list:
    """Discover any untracked plugin or extension manifest files in the repo.

    Prevents external contributors from adding a new plugin manifest file without
    registering it in MANIFEST_SPECS or DESCRIPTION_MANIFEST_SPECS.
    """
    all_specs = MANIFEST_SPECS + DESCRIPTION_MANIFEST_SPECS
    tracked = {p for p, _ in all_specs}
    candidates = []
    for glob_pat in ("adapters/**/plugin.json", "adapters/**/*.json", ".claude-plugin/*.json"):
        for path in REPO_ROOT.glob(glob_pat):
            if path.name in ("plugin.json", "gemini-extension.json", "antigravity-plugin.json") and path.is_file():
                if path not in tracked:
                    candidates.append(path)
    return candidates


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    require_known_paths()
    changed = sync(VERSION_FILE, MANIFEST_SPECS, check_only=args.check)
    changed += sync_descriptions(SKILL_MD_PATH, DESCRIPTION_MANIFEST_SPECS, check_only=args.check)
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
