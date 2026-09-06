from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[2]


def load_yaml(relative_path: str) -> object:
    with (ROOT / relative_path).open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def test_dependabot_updates_merge_through_develop() -> None:
    config = load_yaml(".github/dependabot.yml")

    assert isinstance(config, dict)
    updates = config["updates"]
    assert all(update["target-branch"] == "develop" for update in updates)


def test_cli_paths_receive_the_cli_area_label() -> None:
    config = load_yaml(".github/labeler.yml")

    assert isinstance(config, dict)
    cli_rules = config["area:cli"]
    patterns = cli_rules[0]["changed-files"][0]["any-glob-to-any-file"]
    assert "skills/adr-toolkit/scripts/adr.py" in patterns
    assert "skills/adr-toolkit/scripts/commands/**" in patterns


def test_ci_does_not_pipe_remote_installers_to_a_shell() -> None:
    workflow = (ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "install.sh | bash" not in workflow


def test_dependency_audit_installs_dev_requirements_from_pyproject() -> None:
    workflow = (ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "scripts/export_dev_requirements.py" in workflow


def test_dev_requirement_export_reads_the_requested_extra(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project.optional-dependencies]\n'
        'dev = ["pytest==9.1.1", "ruff==0.16.6"]\n'
        'docs = ["mkdocs==1.6.1"]\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/export_dev_requirements.py"),
            "--pyproject",
            str(pyproject),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "pytest==9.1.1\nruff==0.16.6\n"


def test_release_uses_pinned_dependencies_and_action_commits() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    assert 'pip install -e ".[dev]"' in workflow
    assert "pip install pytest build" not in workflow
    for line in workflow.splitlines():
        if "uses:" in line:
            ref = line.split("uses:", 1)[1].strip().split("#", 1)[0].strip()
            revision = ref.rsplit("@", 1)[1]
            assert len(revision) == 40
            assert all(character in "0123456789abcdef" for character in revision)


def test_pr_title_is_not_interpolated_into_a_shell_script() -> None:
    workflow = (ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")

    assert 'PR_TITLE: ${{ github.event.pull_request.title }}' in workflow
    assert 'TITLE="${{ github.event.pull_request.title }}"' not in workflow


def test_labeler_write_permissions_are_scoped_per_job() -> None:
    workflow = load_yaml(".github/workflows/labeler.yml")

    assert isinstance(workflow, dict)
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["label-pr"]["permissions"] == {
        "contents": "read",
        "pull-requests": "write",
    }
    assert workflow["jobs"]["triage-issue"]["permissions"] == {
        "issues": "write"
    }
