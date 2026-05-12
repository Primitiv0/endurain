"""Tests for backend i18n helpers."""

import core.i18n as core_i18n


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

    def test_unmapped_supported_locale_returns_itself(self):
        """Supported locales without explicit mapping return code."""
        result = core_i18n.html_lang("de")
        assert result == "de"

    def test_unsupported_falls_back_to_en_us(self):
        """Unsupported locale normalizes to 'us' → 'en-US'."""
        assert core_i18n.html_lang("xx") == "en-US"


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

    def test_pt_subject_differs_from_us(self):
        """Portuguese subject differs from the English one."""
        en_subject = core_i18n.t("password_reset.subject", "us")
        pt_subject = core_i18n.t("password_reset.subject", "pt")
        assert en_subject != pt_subject

    def test_none_locale_returns_english(self):
        """None locale produces the same result as 'us'."""
        assert core_i18n.t("password_reset.subject", None) == (
            core_i18n.t("password_reset.subject", "us")
        )
