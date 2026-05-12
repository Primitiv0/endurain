"""Backend localization helpers for transactional emails."""

import functools
import json
import pathlib
from typing import Final

DEFAULT_LOCALE: Final[str] = "us"

SUPPORTED_LOCALES: Final[frozenset[str]] = frozenset(
    {
        "ca",
        "cn",
        "tw",
        "de",
        "fr",
        "gl",
        "it",
        "nl",
        "pt",
        "sl",
        "sv",
        "es",
        "us",
    }
)

HTML_LANG_BY_LOCALE: Final[dict[str, str]] = {
    "us": "en-US",
    "pt": "pt-PT",
    "cn": "zh-Hans",
    "tw": "zh-Hant",
    "ca": "ca",
    "de": "de",
    "fr": "fr",
    "gl": "gl",
    "it": "it",
    "nl": "nl",
    "sl": "sl",
    "sv": "sv",
    "es": "es",
}

_LOCALES_DIR = pathlib.Path(__file__).parent / "i18n_locales"


def normalize_locale(locale: str | None) -> str:
    """
    Return a supported backend locale, falling back to English.

    Args:
        locale: Raw locale string from user preference or
            None.

    Returns:
        A locale code guaranteed to be in SUPPORTED_LOCALES.
    """
    if not locale:
        return DEFAULT_LOCALE
    normalized = locale.strip().lower()
    if normalized in SUPPORTED_LOCALES:
        return normalized
    return DEFAULT_LOCALE


def html_lang(locale: str | None) -> str:
    """
    Return the BCP 47 HTML lang value for a backend locale.

    Args:
        locale: Raw locale string or None.

    Returns:
        A BCP 47 language tag string (e.g. ``"en-US"``).
    """
    normalized = normalize_locale(locale)
    return HTML_LANG_BY_LOCALE.get(normalized, normalized)


@functools.lru_cache(maxsize=32)
def _load_catalog(locale: str) -> dict[str, str]:
    """
    Load and cache a translation catalog JSON file.

    Args:
        locale: A normalized locale code.

    Returns:
        A dict mapping translation keys to localized strings.
        Falls back to the ``us`` catalog if the locale file
        does not exist.
    """
    catalog_path = _LOCALES_DIR / locale / "email.json"
    if not catalog_path.exists():
        catalog_path = _LOCALES_DIR / DEFAULT_LOCALE / "email.json"
    with catalog_path.open(encoding="utf-8") as fh:
        return json.load(fh)


def t(key: str, locale: str | None, **kwargs: str) -> str:
    """
    Translate a key for the given locale.

    Named placeholders in the catalog value (``{name}``) are
    replaced with the keyword arguments supplied.

    Args:
        key: Dot-separated translation key.
        locale: Raw locale string or None; normalized
            internally.
        **kwargs: Named placeholder values for string
            formatting.

    Returns:
        The translated, formatted string. Returns ``key``
        itself if the key is missing from the catalog.
    """
    normalized = normalize_locale(locale)
    catalog = _load_catalog(normalized)
    if key not in catalog:
        # Fall back to default locale catalog
        catalog = _load_catalog(DEFAULT_LOCALE)
    value = catalog.get(key, key)
    if kwargs:
        value = value.format(**kwargs)
    return value
