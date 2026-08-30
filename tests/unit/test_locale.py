from scripts.core.locale import DEFAULT_LOCALE, load_locale

REQUIRED_KEYS = {
    "decision_log_title", "by_status", "by_tag", "by_affected_path",
    "chronological", "status.proposed", "status.accepted",
    "status.rejected", "status.deprecated", "status.superseded",
}


def test_default_locale_is_english():
    assert DEFAULT_LOCALE == "en"


def test_english_locale_has_all_required_keys():
    strings = load_locale("en")
    assert REQUIRED_KEYS.issubset(strings.keys())


def test_every_shipped_locale_has_all_required_keys():
    for locale in ("en", "fr", "ja", "ko", "zh"):
        strings = load_locale(locale)
        missing = REQUIRED_KEYS - strings.keys()
        assert not missing, f"{locale} is missing keys: {missing}"


def test_french_translates_a_known_string():
    strings = load_locale("fr")
    assert strings["by_status"] == "Par statut"


def test_missing_locale_falls_back_to_english():
    strings = load_locale("xx")
    assert strings["by_status"] == "By status"


def test_missing_key_in_a_present_locale_falls_back_to_english(tmp_path, monkeypatch):
    import scripts.core.locale as locale_module
    partial_dir = tmp_path / "i18n"
    partial_dir.mkdir()
    (partial_dir / "en.json").write_text('{"by_status": "By status"}', encoding="utf-8")
    (partial_dir / "xx.json").write_text('{}', encoding="utf-8")
    monkeypatch.setattr(locale_module, "I18N_DIR", partial_dir)

    strings = locale_module.load_locale("xx")

    assert strings["by_status"] == "By status"
