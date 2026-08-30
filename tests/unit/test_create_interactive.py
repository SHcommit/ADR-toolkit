from types import SimpleNamespace

import pytest

from scripts.commands import create


INTERACTIVE_LOCALE_CASES = {
    "en": ("Title of the decision?", "Context and Problem Statement"),
    "ko": ("결정의 제목은 무엇인가요?", "맥락 및 문제 설명"),
    "ja": ("決定のタイトルは何ですか？", "コンテキストと問題"),
    "zh": ("决策标题是什么？", "背景与问题陈述"),
    "fr": ("Quel est le titre de la décision ?", "Contexte et problème"),
    "es": ("¿Cuál es el título de la decisión?", "Contexto y problema"),
    "de": ("Wie lautet der Titel der Entscheidung?", "Kontext und Problemstellung"),
    "pt-BR": ("Qual é o título da decisão?", "Contexto e problema"),
}


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


def test_gather_draft_interactively_keeps_english_default_for_existing_callers():
    answers = iter([
        "Use Postgres", "Persistence is required", "SQLite, Postgres",
        "Postgres", "it scales", "durability", "operations", "integration test",
        "requirements change",
    ])

    draft = create.gather_draft_interactively(
        input_fn=lambda _prompt: next(answers)
    )

    assert draft["locale"] == "en"
    assert "## Context and Problem Statement" in draft["body"]


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


@pytest.mark.parametrize("locale", INTERACTIVE_LOCALE_CASES)
def test_interactive_create_prompts_and_renders_every_supported_locale(locale, capsys):
    expected_prompt, expected_heading = INTERACTIVE_LOCALE_CASES[locale]
    answers = iter([
        "Decision title", "Problem", "Option A, Option B", "Option A",
        "Rationale", "Benefit", "Cost", "CI evidence", "Trigger",
    ])

    draft = create.gather_draft_interactively(
        locale, input_fn=lambda _prompt: next(answers)
    )

    assert expected_prompt in capsys.readouterr().err
    assert f"## {expected_heading}" in draft["body"]
    assert draft["locale"] == locale
