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
    draft = create.gather_draft_interactively("en", input_fn=lambda _prompt: next(answers))

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

    result = create.run(SimpleNamespace(
        interactive=True, input=None, dir=str(adr_dir), root=str(tmp_path),
        locale=None, slug=None, dry_run=False,
    ))

    assert result["ok"] is True
    assert result["id"] == "ADR-0001"


def test_create_run_without_input_or_interactive_is_an_error(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)

    result = create.run(SimpleNamespace(
        interactive=False, input=None, dir=str(adr_dir), root=str(tmp_path),
        locale=None, slug=None, dry_run=False,
    ))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "MISSING_INPUT_OR_INTERACTIVE"


def test_gather_draft_interactively_localizes_korean_structure():
    answers = iter([
        "결제 시스템 분리", "장애 격리가 필요하다", "유지, 분리", "분리",
        "장애를 격리한다", "독립 배포", "운영 복잡성", "CI 경계 검사",
        "운영 비용이 편익을 초과할 때",
    ])

    draft = create.gather_draft_interactively(
        "ko", input_fn=lambda _prompt: next(answers)
    )

    assert "## 맥락 및 문제 설명" in draft["body"]
    assert "장애 격리가 필요하다" in draft["body"]
    assert draft["locale"] == "ko"
