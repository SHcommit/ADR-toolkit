"""Export ADR relationships as Mermaid and SVG graph artifacts."""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core.adr_directory import iter_adr_files
from scripts.core.relationships import render_mermaid, render_svg, resolve
from scripts.core.repository_paths import PathEscapesRootError, resolve_from_root, resolve_from_root_or_error


def run(args) -> dict:
    root = Path(getattr(args, "root", "."))
    adr_dir, error = resolve_from_root_or_error(root, args.dir, operation="graph")
    if error:
        return error
    entries = []
    warnings = []

    for entry, parsed in iter_adr_files(adr_dir):
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
            "related": data.get("related", []),
            "supersedes": data.get("supersedes", []),
            "superseded_by": data.get("superseded_by"),
        })

    output = getattr(args, "output", None)
    format_ = getattr(args, "format", "both")
    outputs = []
    try:
        if format_ in {"mermaid", "both"}:
            path = _output_path(root, adr_dir, output, format_, "mermaid")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render_mermaid(entries), encoding="utf-8")
            outputs.append(str(path))
        if format_ in {"svg", "both"}:
            path = _output_path(root, adr_dir, output, format_, "svg")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render_svg(entries), encoding="utf-8")
            outputs.append(str(path))
    except PathEscapesRootError as exc:
        return {"ok": False, "operation": "graph", "errors": [{"code": exc.error_code, "detail": str(exc)}]}

    rendered_edges = [edge for edge in resolve(entries) if edge.type in {"related", "supersedes"}]
    return {
        "ok": True,
        "operation": "graph",
        "count": len(rendered_edges),
        "outputs": outputs,
        "warnings": warnings,
    }


def _output_path(root: Path, adr_dir: Path, output: str, requested_format: str, actual_format: str) -> Path:
    suffix = f".{'mmd' if actual_format == 'mermaid' else 'svg'}"
    if not output:
        return adr_dir / f"relationships{suffix}"

    base = resolve_from_root(root, output)
    if requested_format == "both":
        return base.with_suffix(suffix)
    return base
