"""Shared structural validation for AI-harness adapter manifests.

Repo tooling -- not part of the distributable skills/adr-toolkit/ package
(same category as scripts/sync_version.py). Each harness (Claude Code,
Codex, Gemini CLI, Antigravity) defines its own manifest shape with extra
harness-specific keys ($schema, version, ...); this only checks the two
fields every one of them shares. The generic fallback adapter
(adapters/generic/) has no manifest at all and is not covered here.
"""
REQUIRED_FIELDS = {"name": str, "description": str}


def validate_adapter_manifest(manifest: dict) -> list:
    errors = []
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in manifest:
            errors.append(f"missing required field: {field}")
            continue
        value = manifest[field]
        if not isinstance(value, expected_type):
            errors.append(
                f"field {field!r} must be {expected_type.__name__}, got {type(value).__name__}"
            )
        elif not value.strip():
            errors.append(f"field {field!r} must not be empty")
    return errors
