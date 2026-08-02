"""Message catalogues and lookup.

Every string a person reads lives in ``locales/<language>.json`` under a dotted
key, and is fetched through :func:`t`. English is the master catalogue: it
defines which keys exist, and any key a translation is missing falls back to it
rather than showing a person a raw key.

Catalogues are JSON rather than YAML on purpose — ``.dockerignore`` excludes
``*.yml`` from the build context, so YAML files here would never reach the image.
"""

import json
import logging
from pathlib import Path
from typing import Any, Final

LANGUAGES: Final[tuple[str, ...]] = ('en', 'uk', 'ru', 'he', 'lv')
FALLBACK_LANGUAGE: Final[str] = 'en'

_LOCALES_DIR: Final[Path] = Path(__file__).parent.parent / 'locales'

_log = logging.getLogger(__name__)


def _flatten(data: dict[str, Any], prefix: str = '') -> dict[str, str]:
    """Turn a nested catalogue into dotted keys."""
    flat: dict[str, str] = {}
    for key, value in data.items():
        path = f'{prefix}{key}'
        if isinstance(value, dict):
            flat.update(_flatten(value, f'{path}.'))
        else:
            flat[path] = value
    return flat


def _load(language: str) -> dict[str, str]:
    path = _LOCALES_DIR / f'{language}.json'
    with path.open(encoding='utf-8') as fd:
        return _flatten(json.load(fd))


_CATALOGUES: Final[dict[str, dict[str, str]]] = {
    language: _load(language) for language in LANGUAGES
}


def missing_keys() -> dict[str, list[str]]:
    """Keys each translation lacks compared with English.

    Reported at startup so an untranslated string is noticed then rather than
    when someone happens to trigger it.
    """
    master = set(_CATALOGUES[FALLBACK_LANGUAGE])
    gaps: dict[str, list[str]] = {}
    for language, catalogue in _CATALOGUES.items():
        if language == FALLBACK_LANGUAGE:
            continue
        absent = sorted(master - set(catalogue))
        if absent:
            gaps[language] = absent
    return gaps


def unknown_keys() -> dict[str, list[str]]:
    """Keys a translation has that English does not — usually a typo."""
    master = set(_CATALOGUES[FALLBACK_LANGUAGE])
    extra: dict[str, list[str]] = {}
    for language, catalogue in _CATALOGUES.items():
        if language == FALLBACK_LANGUAGE:
            continue
        surplus = sorted(set(catalogue) - master)
        if surplus:
            extra[language] = surplus
    return extra


def report_catalogue_health() -> None:
    """Log anything wrong with the catalogues, once, at startup."""
    for language, keys in missing_keys().items():
        _log.warning(
            'Locale "%s" is missing %d key(s), English will be used for them: %s',
            language,
            len(keys),
            ', '.join(keys[:10]) + ('…' if len(keys) > 10 else ''),
        )
    for language, keys in unknown_keys().items():
        _log.warning(
            'Locale "%s" defines %d key(s) English does not: %s',
            language,
            len(keys),
            ', '.join(keys[:10]) + ('…' if len(keys) > 10 else ''),
        )


def has_message(key: str | None) -> bool:
    """Whether a key names a real message.

    Worth asking before rendering a key that arrived from the worker: the two
    services are deployed separately, so one can name a message the other has
    never heard of, and showing a person ``postprocess.something`` is worse than
    showing them nothing.
    """
    return bool(key) and key in _CATALOGUES[FALLBACK_LANGUAGE]


def t(key: str, language: str | None = None, **params: Any) -> str:
    """Look up a message, falling back to English and then to the key itself."""
    catalogue = _CATALOGUES.get(language or FALLBACK_LANGUAGE)
    template = (catalogue or {}).get(key)
    if template is None:
        template = _CATALOGUES[FALLBACK_LANGUAGE].get(key)
    if template is None:
        # Showing the key is ugly but traceable; raising would take down a
        # download over a missing string.
        _log.error('No message for key "%s"', key)
        return key

    if not params:
        return template
    try:
        return template.format(**params)
    except (KeyError, IndexError, ValueError):
        _log.exception('Could not fill message "%s" for language "%s"', key, language)
        return template
