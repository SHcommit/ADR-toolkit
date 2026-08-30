from types import SimpleNamespace

from scripts.commands import create


def test_gather_draft_interactively_builds_valid_minimal_body():
    answers = iter([
        "Use Kafka for domain events",
        "Order processing and downstream work are tightly coupled",
        "synchronous HTTP, RabbitMQ, Kafka",
        "Kafka",
        "it isolates failures and allows reprocessing",
        "failures in one consumer don't block others",
        "operational complexity increases",
        "no direct SDK calls appear outside the events module",
        "message volume exceeds what a single queue can handle",
    ])
    draft = create.gather_draft_interactively(input_fn=lambda _prompt: next(answers))

    assert draft["title"] == "Use Kafka for domain events"
    assert draft["status"] == "proposed"
    assert "## Context and Problem Statement" in draft["body"]
    assert "Kafka" in draft["body"]


def test_create_run_supports_interactive_mode_end_to_end(tmp_path, monkeypatch):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)

    answers = iter([
        "Use Kafka for domain events", "Problem text", "HTTP, Kafka", "Kafka",
        "reason", "good thing", "bad thing", "verification note", "revisit condition",
    ])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    result = create.run(SimpleNamespace(interactive=True, input=None, dir=str(adr_dir), dry_run=False))

    assert result["ok"] is True
    assert result["id"] == "ADR-0001"


def test_create_run_without_input_or_interactive_is_an_error(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)

    result = create.run(SimpleNamespace(interactive=False, input=None, dir=str(adr_dir), dry_run=False))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "MISSING_INPUT_OR_INTERACTIVE"
