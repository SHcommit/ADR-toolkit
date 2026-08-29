"""Parse and serialize ADR YAML frontmatter without a YAML library dependency.

Supports exactly the subset ADR Toolkit frontmatter needs: string scalars,
booleans, and flat string lists. Not a general YAML parser.
"""
import re

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


class FrontmatterError(ValueError):
    pass


def parse(text: str) -> tuple:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise FrontmatterError("No YAML frontmatter block found")
    raw_yaml, body = match.group(1), match.group(2)
    return _parse_simple_yaml(raw_yaml), body


def serialize(data: dict, body: str, *, body_is_parsed: bool = False) -> str:
    lines = ["---"]
    for key, value in data.items():
        lines.append(_format_field(key, value))
    lines.append("---")
    separator = "\n" if body_is_parsed else "\n\n"
    return "\n".join(lines) + separator + body


def _parse_simple_yaml(raw: str) -> dict:
    data: dict = {}
    current_list_key = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - "):
            if current_list_key is None:
                raise FrontmatterError(f"List item with no preceding key: {line!r}")
            data[current_list_key].append(line.strip()[2:].strip())
            continue
        if ":" not in line:
            raise FrontmatterError(f"Malformed frontmatter line: {line!r}")
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "" or value == "[]":
            data[key] = []
            current_list_key = key if value == "" else None
        else:
            current_list_key = None
            if value.lower() in ("true", "false"):
                data[key] = value.lower() == "true"
            else:
                data[key] = value.strip('"').strip("'")
    return data


def _format_field(key: str, value) -> str:
    if isinstance(value, list):
        if not value:
            return f"{key}: []"
        item_lines = "\n".join(f"  - {item}" for item in value)
        return f"{key}:\n{item_lines}"
    if isinstance(value, bool):
        return f"{key}: {'true' if value else 'false'}"
    return f"{key}: {value}"
