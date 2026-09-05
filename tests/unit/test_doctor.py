import json
from argparse import Namespace

from scripts.commands import doctor


def _args(tmp_path, adr_dir="docs/decisions"):
    return Namespace(root=str(tmp_path), dir=adr_dir)


def test_doctor_reports_healthy_repository(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (tmp_path / ".adr-toolkit.json").write_text(
        json.dumps({"schema_version": 1, "locale": "ko", "adr_dir": "docs/decisions"}),
        encoding="utf-8",
    )
    (adr_dir / "0001-test.md").write_text(
        "---\n"
        "id: ADR-0001\n"
        "title: Test decision\n"
        "status: accepted\n"
        "date: 2026-01-01\n"
        "---\n"
        "Body\n",
        encoding="utf-8",
    )

    result = doctor.run(_args(tmp_path))

    assert result == {
        "ok": True,
        "operation": "doctor",
        "checked": {
            "config": True,
            "frontmatter_files": 1,
            "lock": True,
        },
        "diagnostics": [],
    }


def test_doctor_reports_invalid_config_with_repair_guidance(tmp_path):
    (tmp_path / ".adr-toolkit.json").write_text(
        json.dumps({"schema_version": 2, "locale": "ko"}),
        encoding="utf-8",
    )

    result = doctor.run(_args(tmp_path))

    assert result["ok"] is False
    assert result["diagnostics"][0]["code"] == "CONFIG_ERROR"
    assert result["diagnostics"][0]["repair"] == (
        "Edit .adr-toolkit.json so schema_version is 1, locale is supported, "
        "and adr_dir is a relative path inside the repository."
    )


def test_doctor_reports_bad_frontmatter_without_stopping_other_checks(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-bad.md").write_text("not frontmatter\n", encoding="utf-8")
    (tmp_path / ".adr").mkdir()
    (tmp_path / ".adr" / "lock").write_text("stale\n", encoding="utf-8")

    result = doctor.run(_args(tmp_path))

    assert result["ok"] is False
    assert result["checked"]["frontmatter_files"] == 1
    assert [item["code"] for item in result["diagnostics"]] == [
        "BAD_FRONTMATTER",
        "STALE_LOCK",
    ]
    assert result["diagnostics"][0]["file"] == "0001-bad.md"
    assert result["diagnostics"][1]["path"] == str(tmp_path / ".adr" / "lock")
    assert result["diagnostics"][1]["repair"] == (
        "If no adr command is running, remove .adr/lock and rerun the command."
    )
