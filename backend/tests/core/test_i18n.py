"""Tests for backend i18n helpers."""

import json

import pytest

import core.i18n as core_i18n


@pytest.fixture
def isolated_catalogs(tmp_path, monkeypatch):
    """
    Point :mod:`core.i18n` at an isolated locales directory and clear
    the catalog LRU cache so tests cannot leak data into each other.
    """
    monkeypatch.setattr(core_i18n, "_LOCALES_DIR", tmp_path)
    core_i18n._load_catalog.cache_clear()
    yield tmp_path
    core_i18n._load_catalog.cache_clear()


def _write_catalog(root, locale, payload):
    """Write a catalog JSON file under ``root/locale/email.json``."""
    locale_dir = root / locale
    locale_dir.mkdir(parents=True, exist_ok=True)
    (locale_dir / "email.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


class TestNormalizeLocale:
    """Tests for normalize_locale."""

    def test_returns_default_for_none(self):
        """None input returns the default locale."""
        assert core_i18n.normalize_locale(None) == "us"

    def test_returns_default_for_empty_string(self):
        """Empty string returns the default locale."""
        assert core_i18n.normalize_locale("") == "us"

    def test_returns_default_for_unsupported(self):
        """Unsupported locale codes fall back to default."""
        assert core_i18n.normalize_locale("xx") == "us"

    def test_returns_default_for_whitespace_only(self):
        """Whitespace-only input falls back to default."""
        assert core_i18n.normalize_locale("   ") == "us"

    def test_supported_locale_returned_unchanged(self):
        """A supported locale code is returned as-is."""
        assert core_i18n.normalize_locale("pt") == "pt"

    def test_normalizes_uppercase(self):
        """Locale codes are case-normalized before matching."""
        assert core_i18n.normalize_locale("PT") == "pt"

    def test_normalizes_with_leading_trailing_spaces(self):
        """Whitespace around a valid locale is stripped."""
        assert core_i18n.normalize_locale("  es  ") == "es"

    def test_all_supported_locales_are_accepted(self):
        """Every locale in SUPPORTED_LOCALES passes through."""
        for locale in core_i18n.SUPPORTED_LOCALES:
            assert core_i18n.normalize_locale(locale) == locale


class TestSupportedLocalesSource:
    """SUPPORTED_LOCALES must be derived from the Language enum."""

    def test_matches_language_enum(self):
        """Every Language enum value appears in SUPPORTED_LOCALES."""
        from users.users.schema import Language

        assert core_i18n.SUPPORTED_LOCALES == frozenset(
            language.value for language in Language
        )


class TestHtmlLang:
    """Tests for html_lang."""

    def test_none_returns_en_us(self):
        """None maps to en-US via the default locale."""
        assert core_i18n.html_lang(None) == "en-US"

    def test_us_returns_en_us(self):
        """'us' maps to 'en-US'."""
        assert core_i18n.html_lang("us") == "en-US"

    def test_pt_returns_pt_pt(self):
        """'pt' maps to 'pt-PT'."""
        assert core_i18n.html_lang("pt") == "pt-PT"

    def test_cn_returns_zh_hans(self):
        """'cn' maps to 'zh-Hans'."""
        assert core_i18n.html_lang("cn") == "zh-Hans"

    def test_tw_returns_zh_hant(self):
        """'tw' maps to 'zh-Hant'."""
        assert core_i18n.html_lang("tw") == "zh-Hant"

    def test_de_returns_de_de(self):
        """'de' maps to the region-tagged 'de-DE'."""
        assert core_i18n.html_lang("de") == "de-DE"

    def test_es_returns_es_es(self):
        """'es' maps to the region-tagged 'es-ES'."""
        assert core_i18n.html_lang("es") == "es-ES"

    def test_unsupported_falls_back_to_en_us(self):
        """Unsupported locale normalizes to 'us' → 'en-US'."""
        assert core_i18n.html_lang("xx") == "en-US"

    def test_every_supported_locale_has_region_tag(self):
        """Every supported locale must have an explicit BCP 47 entry."""
        for locale in core_i18n.SUPPORTED_LOCALES:
            assert locale in core_i18n.HTML_LANG_BY_LOCALE


class TestTranslate:
    """Tests for t() translation function."""

    def test_known_key_us_locale(self):
        """A known key returns a non-empty English string."""
        result = core_i18n.t("password_reset.subject", "us")
        assert "Endurain" in result

    def test_fallback_to_us_for_unknown_locale(self):
        """Unknown locale falls back to English translation."""
        result_unknown = core_i18n.t("password_reset.subject", "xx")
        result_us = core_i18n.t("password_reset.subject", "us")
        assert result_unknown == result_us

    def test_missing_key_returns_key_itself(self):
        """Missing keys return the key string as fallback."""
        result = core_i18n.t("nonexistent.key", "us")
        assert result == "nonexistent.key"

    def test_named_placeholder_substitution(self):
        """Named placeholders are replaced with keyword arguments."""
        result = core_i18n.t(
            "password_reset.greeting", "us", name="Alice"
        )
        assert "Alice" in result

    def test_pt_subject_differs_from_us(self, isolated_catalogs):
        """Translated catalog returns a locale-specific subject."""
        _write_catalog(
            isolated_catalogs, "us", {"k.subject": "English subject"}
        )
        _write_catalog(
            isolated_catalogs, "pt", {"k.subject": "Portuguese subject"}
        )
        assert core_i18n.t("k.subject", "pt") == "Portuguese subject"
        assert core_i18n.t("k.subject", "us") == "English subject"

    def test_missing_key_in_locale_falls_back_to_us(self, isolated_catalogs):
        """A key missing from the locale catalog reads from us catalog."""
        _write_catalog(isolated_catalogs, "us", {"only.in.us": "default"})
        _write_catalog(isolated_catalogs, "pt", {"other.key": "x"})
        assert core_i18n.t("only.in.us", "pt") == "default"

    def test_none_locale_returns_english(self):
        """None locale produces the same result as 'us'."""
        assert core_i18n.t("password_reset.subject", None) == (
            core_i18n.t("password_reset.subject", "us")
        )


class TestCommonLabels:
    """Tests for common_labels helper."""

    def test_returns_expected_keys(self):
        """common_labels exposes every shared footer/body label."""
        labels = core_i18n.common_labels("us")
        for key in (
            "best_regards",
            "team",
            "system",
            "visit",
            "source_code",
            "copy_link",
        ):
            assert key in labels and labels[key]

    def test_falls_back_to_us_for_unknown_locale(self):
        """Unknown locale produces the English labels."""
        assert core_i18n.common_labels("xx") == core_i18n.common_labels("us")


class TestLoadCatalogPathSafety:
    """_load_catalog must reject locales not in SUPPORTED_LOCALES."""

    def test_unsupported_locale_uses_default(self, isolated_catalogs):
        """A non-allow-listed locale is silently coerced to default."""
        _write_catalog(isolated_catalogs, "us", {"k": "v"})
        # Even an attempted path-traversal segment is rejected.
        result = core_i18n._load_catalog("../etc")
        assert result == {"k": "v"}
