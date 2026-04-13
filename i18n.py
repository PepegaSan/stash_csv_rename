"""JSON locale files: merge target language over English (fallback)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SUPPORTED_LANGS = frozenset({"en", "de", "es", "fr"})


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def merge_flat(base: dict[str, str], overlay: dict[str, Any]) -> dict[str, str]:
    out = dict(base)
    for k, v in overlay.items():
        if isinstance(v, str):
            out[str(k)] = v
    return out


class Translator:
    """Flat string keys; English is always loaded as fallback for missing keys."""

    def __init__(self, locales_dir: Path, lang: str) -> None:
        self._dir = Path(locales_dir)
        self._en: dict[str, str] = {}
        self._cur: dict[str, str] = {}
        self.set_lang(lang)

    def set_lang(self, lang: str) -> None:
        code = (lang or "en").strip().lower()
        if code not in SUPPORTED_LANGS:
            code = "en"
        self.lang = code
        self._en = {k: str(v) for k, v in _load_json(self._dir / "en.json").items() if isinstance(v, str)}
        if code == "en":
            self._cur = dict(self._en)
        else:
            loc = {k: str(v) for k, v in _load_json(self._dir / f"{code}.json").items() if isinstance(v, str)}
            self._cur = merge_flat(self._en, loc)

    def tr(self, key: str, **kwargs: Any) -> str:
        s = self._cur.get(key) or self._en.get(key) or key
        if kwargs:
            try:
                return s.format(**kwargs)
            except (KeyError, ValueError):
                return s
        return s
