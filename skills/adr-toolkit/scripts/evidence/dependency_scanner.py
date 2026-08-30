"""Detect dependency manifest files that hint at technology choices."""
from pathlib import Path

MANIFEST_FILES = {
    "package.json": "npm",
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    "go.mod": "go",
    "Cargo.toml": "cargo",
}


def scan(root: Path) -> list:
    findings = []
    for filename, ecosystem in MANIFEST_FILES.items():
        path = root / filename
        if path.is_file():
            findings.append({"ecosystem": ecosystem, "path": filename})
    return findings
