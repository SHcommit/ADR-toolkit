import json

import pytest

from scripts.core.config import ConfigError, load_repository_config, resolve_locale


def test_missing_config_is_empty(tmp_path):
    assert load_repository_config(tmp_path) == {}


def test_loads_versioned_repository_locale(tmp_path):
    (tmp_path / ".adr-toolkit.json").write_text(
        json.dumps({"schema_version": 1, "locale": "ko"}), encoding="utf-8"
    )

    assert load_repository_config(tmp_path)["locale"] == "ko"


@pytest.mark.parametrize(
    "payload",
    [
        {"schema_version": 2, "locale": "ko"},
        {"schema_version": 1, "locale": "xx"},
        {"schema_version": 1, "locale": "ko", "extra": True},
    ],
)
def test_invalid_config_fails_visibly(tmp_path, payload):
    (tmp_path / ".adr-toolkit.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    with pytest.raises(ConfigError):
        load_repository_config(tmp_path)


def test_locale_precedence_is_cli_then_draft_then_repo_then_english(tmp_path):
    config_path = tmp_path / ".adr-toolkit.json"
    config_path.write_text(
        json.dumps({"schema_version": 1, "locale": "ko"}), encoding="utf-8"
    )

    assert resolve_locale(cli_locale="ja", draft_locale="fr", root=tmp_path) == "ja"
    assert resolve_locale(cli_locale=None, draft_locale="fr", root=tmp_path) == "fr"
    assert resolve_locale(cli_locale=None, draft_locale=None, root=tmp_path) == "ko"

    config_path.unlink()
    assert resolve_locale(cli_locale=None, draft_locale=None, root=tmp_path) == "en"
