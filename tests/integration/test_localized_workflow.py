import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.core.locale import SUPPORTED_LOCALES

ADR_PY = Path(__file__).resolve().parents[2] / "skills/adr-toolkit/scripts/adr.py"

CASES = {
    "en": ("Separate payment system", "Decision Log"),
    "ko": ("결제 시스템 분리", "결정 기록"),
    "ja": ("決済システムを分離する", "決定記録"),
    "zh": ("拆分支付系统", "决策日志"),
    "fr": ("Séparer le système de paiement", "Journal des décisions"),
    "es": ("Separar el sistema de pagos", "Registro de decisiones"),
    "de": ("Zahlungssystem trennen", "Entscheidungsprotokoll"),
    "pt-BR": ("Separar o sistema de pagamentos", "Registro de decisões"),
}


def _run(repo, *args):
    completed = subprocess.run(
        [sys.executable, str(ADR_PY), *args],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert completed.stderr == ""
    payload = json.loads(completed.stdout)
    assert completed.returncode == 0, payload
    return payload


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_complete_localized_workflow(locale, tmp_path):
    title, index_title = CASES[locale]
    repo = tmp_path / locale
    repo.mkdir()

    initialized = _run(repo, "init", "--locale", locale, "--json")
    assert initialized["ok"] is True

    draft = {
        "title": title,
        "status": "proposed",
        "body": f"# {title}\n\nUnicode body: {title}\n",
    }
    draft_path = repo / "draft.json"
    draft_path.write_text(
        json.dumps(draft, ensure_ascii=False), encoding="utf-8"
    )
    created = _run(
        repo,
        "create",
        "--input",
        str(draft_path),
        "--slug",
        "separate-payment-system",
        "--json",
    )
    created_path = repo / created["created"]
    assert created_path.name == "0002-separate-payment-system.md"
    created_text = created_path.read_text(encoding="utf-8")
    assert f"locale: {locale}" in created_text
    assert title in created_text

    validated = _run(repo, "validate", "--json")
    assert validated["checked"] == 2

    indexed = _run(repo, "index", "--json")
    assert indexed["count"] == 2
    readme = (repo / "docs/decisions/README.md").read_text(encoding="utf-8")
    assert readme.startswith(f"# {index_title}")
