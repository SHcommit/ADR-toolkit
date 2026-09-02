import json
import os

import pytest

from scripts.core.config import (
    ConfigError,
    load_repository_config,
    resolve_adr_dir,
    resolve_locale,
)


def test_missing_config_is_empty(tmp_path):
    assert load_repository_config(tmp_path) == {}


def test_loads_versioned_repository_locale_and_adr_dir(tmp_path):
    (tmp_path / ".adr-toolkit.json").write_text(
        json.dumps({"schema_version": 1, "locale": "ko", "adr_dir": "architecture/decisions"}),
        encoding="utf-8",
    )

    config = load_repository_config(tmp_path)
    assert config["locale"] == "ko"
    assert config["adr_dir"] == "architecture/decisions"


@pytest.mark.parametrize(
    "payload",
    [
        {"schema_version": 2, "locale": "ko"},
        {"schema_version": 1, "locale": "xx"},
        {"schema_version": 1, "locale": "ko", "extra": True},
        {"schema_version": 1, "adr_dir": ""},
        {"schema_version": 1, "adr_dir": "/absolute/path"},
        {"schema_version": 1, "adr_dir": "../escaped"},
    ],
)
def test_invalid_config_fails_visibly(tmp_path, payload):
    (tmp_path / ".adr-toolkit.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    with pytest.raises(ConfigError):
        load_repository_config(tmp_path)


def test_locale_precedence_is_cli_then_draft_then_env_then_repo_then_english(tmp_path, monkeypatch):
    config_path = tmp_path / ".adr-toolkit.json"
    config_path.write_text(
        json.dumps({"schema_version": 1, "locale": "ko"}), encoding="utf-8"
    )

    assert resolve_locale(cli_locale="ja", draft_locale="fr", root=tmp_path) == "ja"
    assert resolve_locale(cli_locale=None, draft_locale="fr", root=tmp_path) == "fr"

    monkeypatch.setenv("ADR_LOCALE", "es")
    assert resolve_locale(cli_locale=None, draft_locale=None, root=tmp_path) == "es"

    monkeypatch.delenv("ADR_LOCALE", raising=False)
    assert resolve_locale(cli_locale=None, draft_locale=None, root=tmp_path) == "ko"

    config_path.unlink()
    assert resolve_locale(cli_locale=None, draft_locale=None, root=tmp_path) == "en"


def test_resolve_adr_dir_precedence(tmp_path, monkeypatch):
    config_path = tmp_path / ".adr-toolkit.json"
    config_path.write_text(
        json.dumps({"schema_version": 1, "adr_dir": "config/adr"}), encoding="utf-8"
    )

    # CLI explicit override
    assert resolve_adr_dir(cli_dir="custom/decisions", root=tmp_path) == tmp_path / "custom/decisions"

    # Environment variable override
    monkeypatch.setenv("ADR_DIR", "env/decisions")
    assert resolve_adr_dir(cli_dir="docs/decisions", root=tmp_path) == tmp_path / "env/decisions"

    # Config file value
    monkeypatch.delenv("ADR_DIR", raising=False)
    assert resolve_adr_dir(cli_dir="docs/decisions", root=tmp_path) == tmp_path / "config/adr"

    # Default fallback
    config_path.unlink()
    assert resolve_adr_dir(cli_dir=None, root=tmp_path) == tmp_path / "docs/decisions"

