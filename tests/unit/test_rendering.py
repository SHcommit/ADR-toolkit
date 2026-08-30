from scripts.core.rendering import (
    interactive_prompts,
    render_initial_adr,
    render_minimal,
    render_template,
)


def test_korean_minimal_uses_korean_structure_and_preserves_answers():
    body = render_minimal(
        "ko",
        {
            "title": "결제 시스템 분리",
            "problem": "장애 격리가 필요하다.",
            "options": ["유지", "분리"],
            "decision": "분리",
            "rationale": "격리할 수 있다",
            "good": "독립 배포",
            "bad": "운영 복잡성",
            "confirmation": "CI에서 경계를 검사한다.",
            "revisit": "운영 비용이 편익을 초과할 때",
        },
    )

    assert "## 맥락 및 문제 설명" in body
    assert "장애 격리가 필요하다." in body
    assert "## 재검토 조건" in body


def test_japanese_full_template_has_full_sections():
    template = render_template("ja", full=True)

    assert "## 決定要因" in template
    assert "## 選択肢の長所と短所" in template


def test_korean_prompts_are_localized_in_stable_order():
    prompts = interactive_prompts("ko")

    assert prompts[0] == "결정의 제목은 무엇인가요?"
    assert prompts[-1] == "어떤 조건에서 이 결정을 재검토해야 하나요?"


def test_initial_adr_uses_locale_boilerplate_and_path():
    title, body = render_initial_adr("fr", "docs/decisions/")

    assert title == "Consigner les décisions d’architecture"
    assert "`docs/decisions/`" in body
    assert "## Contexte et problème" in body
