"""
CSV + on-disk rename helpers for Stash file export and local folder scans.
Paths and CSV use UTF-8 with BOM so Excel and German umlauts (äöüÄÖÜß) round-trip correctly.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import shutil
import subprocess
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Callable, Optional, Sequence

# (row_index, path_before_rename, path_after_rename, new_leaf_value_before_rename)
RenameUndoRecord = tuple[int, str, str, str]

# Progress callback: ``(current, total)`` with ``current`` in ``0 … total`` (``total`` may be 0).
ProgressCallback = Callable[[int, int], None]

# Dry-run can otherwise build hundreds of thousands of log strings (memory + frozen log UI).
_DRY_RUN_LOG_LINE_CAP = 8_000
from urllib.parse import unquote, urlparse
from urllib.request import Request, url2pathname, urlopen

# Unicode lookalikes for ASCII COMMERCIAL AT (Stash/Excel sometimes differ from on-disk NTFS name).
_COMMERCIAL_AT_EQUIV = (
    "\uff20",  # FULLWIDTH COMMERCIAL AT ＠
    "\ufe6b",  # SMALL COMMERCIAL AT ﹫
)

# Columns compatible with export_stash_files.ps1
CSV_COLUMNS = (
    "scene_id",
    "scene_title",
    "file_path",
    "file_directory",
    "file_name",
    "file_extension",
    "new_leaf",
    "scene_date",
    "scene_rating",
    "scene_tags",
    "scene_markers",
)

# Lowercase alternate headers from other Stash export scripts / versions (used when primary is missing).
CSV_HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "file_path": ("path", "filepath", "full_path", "fullpath"),
    "scene_id": ("sceneid", "stash_scene_id", "stash_id"),
    "scene_title": ("scene title", "scenetitle", "stash_title", "title_stash", "title"),
    "new_leaf": ("new_filename", "new_name", "target_leaf"),
    "file_extension": ("ext", "extension", "suffix", "file_ext"),
    "scene_date": ("date", "released", "scene_date_iso", "release_date"),
    "scene_rating": ("rating", "rating100", "stars"),
    "scene_tags": ("tags", "stash_tags", "tag_list"),
    "scene_markers": ("markers", "scene_marker_titles", "marker_titles"),
}

# Stash scene `id` in GraphQL is often a numeric string; accept column "id" only in that shape to avoid wrong columns.
_STASH_NUMERIC_ID_RE = re.compile(r"^\d+$")


def _coalesce_norm_field(norm: dict[str, str], primary: str) -> str:
    """First non-empty value among primary key and its aliases (keys already lowercased)."""
    keys = (primary,) + CSV_HEADER_ALIASES.get(primary, ())
    for k in keys:
        v = (norm.get(k) or "").strip()
        if v:
            return v
    return ""


def _coalesce_scene_id(norm: dict[str, str]) -> str:
    v = _coalesce_norm_field(norm, "scene_id")
    if v:
        return v
    id_v = (norm.get("id") or "").strip()
    if id_v and _STASH_NUMERIC_ID_RE.fullmatch(id_v):
        return id_v
    return ""


def sniff_delimiter(sample: str) -> str:
    return ";" if sample.count(";") >= sample.count(",") else ","


# Longest match wins (e.g. scene_id: before id:).
_FIELD_FILTER_PREFIXES: tuple[tuple[str, str], ...] = (
    ("scene_id:", "scene_id"),
    ("folder:", "path"),
    ("markers:", "scene_markers"),
    ("proposed:", "proposed_leaf"),
    ("name:", "name"),
    ("file:", "name"),
    ("extension:", "file_extension"),
    ("ext:", "file_extension"),
    ("path:", "path"),
    ("new:", "new_leaf"),
    ("nl:", "new_leaf"),
    ("title:", "scene_title"),
    ("tags:", "scene_tags"),
    ("date:", "scene_date"),
    ("id:", "scene_id"),
)


# --- UI list filter (comma terms + column / AND/OR menus) ---------------------------------

_UI_FILTER_FIELDS: frozenset[str] = frozenset(
    {
        "all",
        "path",
        "name",
        "file_extension",
        "new_leaf",
        "scene_title",
        "scene_tags",
        "scene_markers",
        "scene_id",
        "scene_date",
        "proposed",
    }
)
_UI_FILTER_COMBINE: frozenset[str] = frozenset({"and", "or"})

_FIELD_PREFIX_FOR_UI: dict[str, str | None] = {
    "all": None,
    "path": "path:",
    "name": "name:",
    "file_extension": "ext:",
    "new_leaf": "new:",
    "scene_title": "title:",
    "scene_tags": "tags:",
    "scene_markers": "markers:",
    "scene_id": "id:",
    "scene_date": "date:",
    "proposed": "proposed:",
}


def _split_comma_terms_outside_quotes(raw: str) -> list[str]:
    """Split on commas not inside '...' or \"...\"."""
    s = raw.strip()
    if not s:
        return []
    parts: list[str] = []
    buf: list[str] = []
    in_dq = False
    in_sq = False
    for ch in s:
        if ch == '"' and not in_sq:
            in_dq = not in_dq
            buf.append(ch)
        elif ch == "'" and not in_dq:
            in_sq = not in_sq
            buf.append(ch)
        elif ch == "," and not in_dq and not in_sq:
            t = "".join(buf).strip()
            if t:
                parts.append(t)
            buf = []
        else:
            buf.append(ch)
    t = "".join(buf).strip()
    if t:
        parts.append(t)
    return parts


def _filter_input_looks_legacy(raw: str) -> bool:
    """Semicolon / pipe / OR keyword syntax — skip comma rewriting."""
    s = (raw or "").strip()
    if not s:
        return False
    if "|" in s or "§" in s or ";" in s:
        return True
    return bool(re.search(r"(?i)\s+OR\s+", s))


def compose_ui_list_filter(raw: str, field_key: str, combine: str) -> str:
    """
    Build a filter string for ``row_matches_search_filter`` from the main-window boxes:
    comma-separated words, optional column (field) prefix, AND vs OR between words.

    If the user types legacy syntax (; … | … OR …), the text is passed through unchanged.
    """
    fk = field_key if field_key in _UI_FILTER_FIELDS else "all"
    cmb = combine if combine in _UI_FILTER_COMBINE else "and"
    s = (raw or "").strip()
    if not s:
        return ""
    if _filter_input_looks_legacy(s):
        return s
    terms = _split_comma_terms_outside_quotes(s)
    if not terms:
        return ""
    prefix = _FIELD_PREFIX_FOR_UI.get(fk)
    built: list[str] = []
    for term in terms:
        field, _rest = _split_filter_field_term(term)
        if field is not None:
            built.append(term)
        elif prefix:
            built.append(prefix + term)
        else:
            built.append(term)
    sep = ";" if cmb == "and" else "|"
    return sep.join(built)


def _split_filter_field_term(part: str) -> tuple[str | None, str]:
    """Return (field or None, remainder). field keys match row_matches_search_filter columns."""
    p = part.strip()
    if not p:
        return None, ""
    pl = p.lower()
    best_len = -1
    best_field: str | None = None
    best_prefix = ""
    for prefix, field in _FIELD_FILTER_PREFIXES:
        lp = prefix.lower()
        if pl.startswith(lp) and len(lp) > best_len:
            best_len = len(lp)
            best_field = field
            best_prefix = prefix
    if best_field is None:
        return None, p
    return best_field, p[len(best_prefix) :].strip()


def _unquote_search_phrase(s: str) -> str:
    """Strip one pair of ASCII double/single quotes (Google-style exact phrase as substring)."""
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1]
    return s


_QUOTED_SEARCH_SEGMENT = re.compile(r'"[^"]*"|\'[^\']*\'')


def _apply_or_substitutions_unquoted(chunk: str) -> str:
    """
    Turn OR alternatives into ``|`` for splitting:
    - Word `` OR `` (case-insensitive, with spaces)
    - ``§`` — easy on many European keyboards (e.g. Shift+3 DE)
    - ``>`` — easy on US/UK QWERTY (Shift+.) and common on DE layouts (``>`` key); not valid in Windows file names
    - ASCII pipe ``|`` (unchanged; already splits later)
    """
    s = re.sub(r"(?i)\s+OR\s+", "|", chunk)
    s = s.replace("§", "|")
    s = s.replace(">", "|")
    return s


def _normalize_or_separators_outside_quotes(raw: str) -> str:
    """Apply OR substitutions only outside '...' and \"...\" (literal § or OR inside quotes stays)."""
    out: list[str] = []
    pos = 0
    for m in _QUOTED_SEARCH_SEGMENT.finditer(raw):
        out.append(_apply_or_substitutions_unquoted(raw[pos : m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(_apply_or_substitutions_unquoted(raw[pos:]))
    return "".join(out)


def _split_or_groups(raw: str) -> list[str]:
    """Split OR-groups on ``|``, `` OR ``, ``§``, or ``>``."""
    merged = _normalize_or_separators_outside_quotes(raw.strip())
    return [g.strip() for g in merged.split("|") if g.strip()]


def _effective_scene_title_for_search(file_name: str, scene_title: str) -> str:
    """If the CSV scene_title cell is empty (common for disk-only rows), use the file stem like Tab 5."""
    st = (scene_title or "").strip()
    if st:
        return st
    return Path(file_name or "").stem


def row_matches_search_filter(
    filter_raw: str,
    *,
    file_path: str = "",
    file_name: str = "",
    file_extension: str = "",
    new_leaf: str = "",
    scene_title: str = "",
    scene_tags: str = "",
    scene_markers: str = "",
    scene_id: str = "",
    scene_date: str = "",
    proposed_leaf: str = "",
) -> bool:
    """
    Tab 3 / Tab 4 / Tab 5 list filter. Case-insensitive substring match unless a field prefix is used.

    Syntax:
    - Semicolon (;): AND between parts.
    - OR between groups: ``|``, `` OR ``, ``§`` (e.g. Shift+3 DE), or ``>`` (e.g. Shift+. US; ``>`` key DE).
    - Those markers inside ``"quotes"`` stay literal.
    - No prefix: part may match file_path, file_name, extension, new_leaf, scene_title, tags, markers, scene_id, scene_date (any).
    - ``name:`` or ``file:`` — only the file name (leaf).
    - ``ext:`` or ``extension:`` — only the file extension cell (e.g. ``.mp4``), from the current file name.
    - ``path:`` or ``folder:`` — only the full path.
    - ``new:`` or ``nl:`` — only the new file name column (often empty until you fill it).
    - ``title:`` — scene title from CSV if present, else the file name stem (extension stripped).
    - ``tags:`` — Stash tag names cell (``scene_tags``).
    - ``markers:`` — scene marker titles cell (``scene_markers``).
    - ``id:`` / ``scene_id:`` — scene id cell.
    - ``date:`` — scene date / release cell.
    - ``proposed:`` — proposed new file name (Tab 5 only; pass computed leaf).
    - Quotes ``"like this"`` strip to search that exact substring (spaces kept); works with or without a prefix.

    Examples:
    - ``name:vacation`` — filename must contain vacation, path is ignored for this part.
    - ``name:"my clip"`` — filename must contain my clip.
    - ``path:D:\\Work;name:1080`` — path contains D:\\Work and name contains 1080.
    """
    raw = (filter_raw or "").strip()
    if not raw:
        return True
    fp_l = (file_path or "").lower()
    fn_l = (file_name or "").lower()
    fe_l = (file_extension or "").lower()
    if not fe_l and fn_l:
        fe_l = Path(file_name).suffix.lower()
    nl_l = (new_leaf or "").lower()
    st_l = _effective_scene_title_for_search(file_name, scene_title).lower()
    tg_l = (scene_tags or "").lower()
    mk_l = (scene_markers or "").lower()
    sid_l = (scene_id or "").lower()
    sdt_l = (scene_date or "").lower()
    prop_l = (proposed_leaf or "").lower()

    def term_matches(part: str) -> bool:
        field, text = _split_filter_field_term(part)
        text = _unquote_search_phrase(text)
        t = text.lower().strip()
        if not t:
            return field is None
        if field == "path":
            return t in fp_l
        if field == "name":
            return t in fn_l
        if field == "file_extension":
            return t in fe_l
        if field == "new_leaf":
            return t in nl_l
        if field == "scene_title":
            return t in st_l
        if field == "scene_tags":
            return t in tg_l
        if field == "scene_markers":
            return t in mk_l
        if field == "scene_id":
            return t in sid_l
        if field == "scene_date":
            return t in sdt_l
        if field == "proposed_leaf":
            return t in prop_l
        # Unqualified: match path, file name, extension, new_leaf, scene_title, tags, markers, id, date (not proposed).
        return (
            t in fp_l
            or t in fn_l
            or t in fe_l
            or t in nl_l
            or t in st_l
            or t in tg_l
            or t in mk_l
            or t in sid_l
            or t in sdt_l
        )

    or_groups = _split_or_groups(raw)
    if not or_groups:
        return True
    for group in or_groups:
        parts = [p.strip() for p in group.split(";") if p.strip()]
        if not parts:
            continue
        if all(term_matches(p) for p in parts):
            return True
    return False


def row_passes_list_filters(
    include_raw: str,
    exclude_raw: str,
    *,
    file_path: str = "",
    file_name: str = "",
    file_extension: str = "",
    new_leaf: str = "",
    scene_title: str = "",
    scene_tags: str = "",
    scene_markers: str = "",
    scene_id: str = "",
    scene_date: str = "",
    proposed_leaf: str = "",
) -> bool:
    """
    List visibility: row matches the include filter and does **not** match the exclude filter.
    Empty exclude string disables exclusion. Same field syntax as ``row_matches_search_filter``.
    """
    kw: dict[str, str] = {
        "file_path": file_path,
        "file_name": file_name,
        "file_extension": file_extension,
        "new_leaf": new_leaf,
        "scene_title": scene_title,
        "scene_tags": scene_tags,
        "scene_markers": scene_markers,
        "scene_id": scene_id,
        "scene_date": scene_date,
        "proposed_leaf": proposed_leaf,
    }
    if not row_matches_search_filter(include_raw, **kw):
        return False
    if not (exclude_raw or "").strip():
        return True
    return not row_matches_search_filter(exclude_raw, **kw)


def filter_stub_for_subfolder_suggest(filter_raw: str) -> str:
    """First AND-term of the first OR-group — used when deriving a subfolder label from the search box."""
    raw = (filter_raw or "").strip()
    if not raw:
        return "moved"
    groups = _split_or_groups(raw)
    first_group = groups[0] if groups else ""
    first_term = first_group.split(";", 1)[0].strip()
    _field, text = _split_filter_field_term(first_term)
    text = _unquote_search_phrase(text).strip()
    return text if text else "moved"


def normalize_commercial_at(s: str) -> str:
    """Map fullwidth/small @ to ASCII U+0040 (same glyph, different code point)."""
    t = s
    for u in _COMMERCIAL_AT_EQUIV:
        t = t.replace(u, "@")
    return t


def normalize_stash_path_for_windows(s: str) -> str:
    """Match export_stash_files.ps1 Normalize-StashFilePathForWindows."""
    s = s.strip().strip('"').strip("'")
    if len(s) >= 3 and s[1] == ":" and s[0].isalpha() and s[2] not in "\\/":
        s = s[:2] + "\\" + s[2:]
    return s.replace("/", "\\")


def _mojibake_path_variants(s: str) -> list[str]:
    """UTF-8 bytes misread as cp1252/latin1, then reinterpreted as UTF-8 (same idea as export PS1)."""
    out: list[str] = []
    for enc in ("cp1252", "iso8859-1"):
        try:
            b = s.encode(enc)
            fixed = b.decode("utf-8")
            if fixed != s:
                out.append(fixed)
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    return out


def _mojibake_expand_closure(s: str, *, max_rounds: int = 6) -> set[str]:
    """Repeat mojibake repair (some paths need more than one round-trip)."""
    bag: set[str] = {s.strip()}
    if not s.strip():
        return bag
    for _ in range(max_rounds):
        added = False
        for item in list(bag):
            for v in _mojibake_path_variants(item):
                if v not in bag:
                    bag.add(v)
                    added = True
        if not added:
            break
    return bag


def _filename_identity_variants(leaf: str) -> frozenset[str]:
    """
    All strings we treat as the same file name: URL-decoding, NFC/NFD, repeated mojibake repair,
    and on Windows casefold (NTFS case-insensitive).
    """
    s = (leaf or "").strip()
    if not s:
        return frozenset()
    seeds: set[str] = {s}
    try:
        u = unquote(s)
        seeds.add(u)
    except Exception:
        pass
    bag: set[str] = set()
    for seed in seeds:
        bag.update(_mojibake_expand_closure(seed))
        bag.add(seed)
    out: set[str] = set()
    for x in bag:
        out.add(x)
        out.add(unicodedata.normalize("NFC", x))
        out.add(unicodedata.normalize("NFD", x))
    if os.name == "nt":
        for x in list(out):
            out.add(x.casefold())
    for x in list(out):
        na = normalize_commercial_at(x)
        if na != x:
            out.add(na)
            out.add(unicodedata.normalize("NFC", na))
            if os.name == "nt":
                out.add(na.casefold())
    return frozenset(out)


def _win_extended_long_path(path_str: str) -> Optional[str]:
    """Prefix \\\\?\\ or \\\\?\\UNC\\ so Windows accepts long / tricky paths."""
    if os.name != "nt":
        return None
    s = path_str.strip()
    if s.startswith("\\\\?\\"):
        return s
    if s.startswith("\\\\"):
        body = s[2:].lstrip("\\")
        if not body:
            return None
        return "\\\\?\\UNC\\" + body
    if len(s) >= 2 and s[1] == ":":
        norm = os.path.normpath(s)
        return "\\\\?\\" + norm
    return None


def _win32_file_attributes(path: str) -> Optional[int]:
    """Return GetFileAttributesW value, or None if path is not found / error."""
    if os.name != "nt" or not path:
        return None
    try:
        import ctypes
        from ctypes import wintypes

        INVALID = 0xFFFFFFFF
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetFileAttributesW.restype = wintypes.DWORD
        attr = kernel32.GetFileAttributesW(path)
        if attr == INVALID:
            return None
        return int(attr)
    except OSError:
        return None


def _win32_is_plain_file(path: str) -> bool:
    """True if path exists and is not a directory (covers cases where Path.is_file misbehaves)."""
    attr = _win32_file_attributes(path)
    if attr is None:
        return False
    return (attr & 16) == 0  # FILE_ATTRIBUTE_DIRECTORY


def _path_existing_equivalent(p: Path) -> Optional[Path]:
    """
    Return a Path that definitely exists as a regular file, or None.
    Tries the same string as p, @-lookalike normalization (＠ -> @), extended-length paths,
    and GetFileAttributesW — and returns the path string that actually worked (critical when
    CSV has U+FF20 but NTFS has ASCII @).
    """
    try:
        if p.is_file():
            return p
    except OSError:
        pass
    candidates: list[str] = []
    try:
        candidates.append(os.path.normpath(str(p)))
    except OSError:
        candidates.append(str(p))
    try:
        r = os.path.normpath(str(p.resolve(strict=False)))
        if r not in candidates:
            candidates.append(r)
    except OSError:
        pass
    for cand in candidates:
        na = normalize_commercial_at(cand)
        for s in {cand, na}:
            if not s:
                continue
            try:
                if os.path.isfile(s):
                    return Path(s)
            except (OSError, ValueError):
                pass
            if os.name == "nt" and _win32_is_plain_file(s):
                return Path(s)
            if os.name == "nt":
                ext = _win_extended_long_path(s)
                if ext:
                    try:
                        if os.path.isfile(ext):
                            return Path(ext)
                    except (OSError, ValueError):
                        pass
                    if _win32_is_plain_file(ext):
                        return Path(ext)
                    try:
                        if Path(ext).is_file():
                            return Path(ext)
                    except OSError:
                        pass
    return None


def _collect_path_string_candidates(raw: str) -> list[str]:
    bag: set[str] = set()
    out: list[str] = []

    def add(x: str) -> None:
        x = x.strip()
        if not x or x in bag:
            return
        bag.add(x)
        out.append(x)

    add(raw)
    qu = unquote(raw)
    if qu != raw:
        add(qu)
    if os.name == "nt":
        add(normalize_stash_path_for_windows(raw))
        add(normalize_stash_path_for_windows(qu))
    # ASCII @ vs fullwidth ＠ (and similar) anywhere in the path
    for s in list(out):
        n = normalize_commercial_at(s)
        if n != s:
            add(n)
        if os.name == "nt":
            add(normalize_stash_path_for_windows(n))

    first = list(out)
    for item in first:
        for v in _mojibake_path_variants(item):
            add(v)
            nv = normalize_commercial_at(v)
            if nv != v:
                add(nv)

    return out


def _resolve_by_parent_variant_match(logical: Path) -> Optional[Path]:
    """
    If the literal path misses, list the parent directory and match basename using
    mojibake/NFC/case variants (CSV ``â€"`` vs on-disk en-dash ``–``, etc.).
    """
    target_leaf = logical.name
    if not target_leaf:
        return None
    want = _filename_identity_variants(target_leaf)

    parent = logical.parent
    parents_to_try: list[Path] = []
    try:
        if parent.is_dir():
            parents_to_try.append(parent)
    except OSError:
        pass
    try:
        r = parent.resolve(strict=False)
        if r.is_dir():
            if r not in parents_to_try:
                parents_to_try.append(r)
    except OSError:
        pass

    for par in parents_to_try:
        try:
            children = list(par.iterdir())
        except OSError:
            if os.name == "nt":
                ext = _win_extended_long_path(str(par))
                if ext:
                    try:
                        children = list(Path(ext).iterdir())
                    except OSError:
                        continue
                else:
                    continue
            else:
                continue
        for child in children:
            real = _path_existing_equivalent(child)
            if real is None:
                continue
            if _filename_identity_variants(real.name) & want:
                try:
                    return real.resolve(strict=False)
                except OSError:
                    return real
    return None


def resolve_csv_path_to_existing_file(fp: str) -> Optional[Path]:
    """
    Map CSV file_path to a path that exists as a regular file: URL-decoding, Windows slashes,
    mojibake variants, NFC basename match in parent directory.
    """
    raw = fp.strip()
    if not raw:
        return None
    for cand in _collect_path_string_candidates(raw):
        p = Path(cand)
        try:
            resolved = p.resolve(strict=False)
        except OSError:
            resolved = p
        found = _path_existing_equivalent(resolved)
        if found is not None:
            return found
        hit = _resolve_by_parent_variant_match(p)
        if hit is not None:
            found2 = _path_existing_equivalent(hit)
            if found2 is not None:
                return found2
    return None


def leaf_extension_from_row(row: dict[str, str]) -> str:
    """Return ``Path.suffix`` for the current file (from ``file_name``, else ``file_path``)."""
    fn = (row.get("file_name") or "").strip()
    if fn:
        return Path(fn).suffix
    fp = (row.get("file_path") or "").strip()
    return Path(fp).suffix if fp else ""


def csv_row_from_path(p: Path) -> dict[str, str]:
    p = p.resolve()
    name = p.name
    return {
        "scene_id": "",
        "scene_title": "",
        "file_path": str(p),
        "file_directory": str(p.parent),
        "file_name": name,
        "file_extension": Path(name).suffix,
        "new_leaf": "",
        "scene_date": "",
        "scene_rating": "",
        "scene_tags": "",
        "scene_markers": "",
    }


def scan_folder_files(
    root: Path,
    *,
    recursive: bool = True,
    patterns: Optional[list[str]] = None,
) -> list[dict[str, str]]:
    """
    List files under root. If patterns is non-empty, each pattern is a fnmatch against the file name
    (e.g. *.mp4). If empty, include all files.
    """
    root = root.resolve()
    if not root.is_dir():
        return []

    rows: list[dict[str, str]] = []
    seen: set[str] = set()

    def ok_name(name: str) -> bool:
        if not patterns:
            return True
        import fnmatch

        n = name.lower()
        for pat in patterns:
            pat = pat.strip()
            if not pat:
                continue
            if fnmatch.fnmatch(n, pat.lower()):
                return True
        return False

    if recursive:
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            if not ok_name(p.name):
                continue
            key = str(p.resolve())
            if key in seen:
                continue
            seen.add(key)
            rows.append(csv_row_from_path(p))
    else:
        for p in sorted(root.iterdir()):
            if not p.is_file():
                continue
            if not ok_name(p.name):
                continue
            key = str(p.resolve())
            if key in seen:
                continue
            seen.add(key)
            rows.append(csv_row_from_path(p))

    return rows


def write_rename_csv(path: Path, rows: list[dict[str, str]], delimiter: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(CSV_COLUMNS), delimiter=delimiter, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            row = {k: (r.get(k) or "") for k in CSV_COLUMNS}
            row["file_extension"] = leaf_extension_from_row(r)
            w.writerow(row)


def read_rename_csv(path: Path, delimiter: Optional[str] = None) -> tuple[list[dict[str, str]], str]:
    raw = path.read_text(encoding="utf-8-sig")
    if delimiter is None:
        delimiter = sniff_delimiter(raw[:4096])
    f = io.StringIO(raw, newline=None)
    reader = csv.DictReader(f, delimiter=delimiter)
    rows: list[dict[str, str]] = []
    for row in reader:
        norm = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        fp = _coalesce_norm_field(norm, "file_path")
        if not fp:
            continue
        p = Path(fp)
        built = {
            "scene_id": _coalesce_scene_id(norm),
            "scene_title": _coalesce_norm_field(norm, "scene_title"),
            "file_path": fp,
            "file_directory": norm.get("file_directory", "") or str(p.parent),
            "file_name": norm.get("file_name", "") or p.name,
            "new_leaf": _coalesce_norm_field(norm, "new_leaf"),
            "scene_date": _coalesce_norm_field(norm, "scene_date"),
            "scene_rating": _coalesce_norm_field(norm, "scene_rating"),
            "scene_tags": _coalesce_norm_field(norm, "scene_tags"),
            "scene_markers": _coalesce_norm_field(norm, "scene_markers"),
        }
        built["file_extension"] = leaf_extension_from_row(built)
        rows.append(built)
    return rows, delimiter


def unique_leaf_in_dir(directory: Path, desired_leaf: str) -> str:
    directory = directory.resolve()
    p = Path(desired_leaf)
    base = p.stem
    ext = p.suffix
    candidate = desired_leaf
    n = 0
    while (directory / candidate).exists():
        n += 1
        candidate = f"{base}_{n}{ext}"
    return candidate


def inherit_missing_extension(new_leaf: str, source_leaf: str) -> str:
    """
    If ``new_leaf`` has no ``Path.suffix``, append the suffix from ``source_leaf`` (the file on disk).

    So ``VIDEO`` + ``clip.mp4`` -> ``VIDEO.mp4``. If the source has no extension, ``new_leaf`` is unchanged.
    """
    nl = new_leaf.strip()
    if not nl or nl in (".", ".."):
        return nl
    if Path(nl).suffix:
        return nl
    ext = Path((source_leaf or "").strip()).suffix
    if not ext:
        return nl
    return nl + ext


def merge_new_leaf_missing_extensions(rows: list[dict[str, str]]) -> int:
    """
    For every row with a non-empty ``new_leaf`` that lacks a file extension, append the extension
    from the row's current file name (or path). Returns how many cells were updated.
    """
    changed = 0
    for i, row in enumerate(rows):
        nl = (row.get("new_leaf") or "").strip()
        if not nl:
            continue
        fp = (row.get("file_path") or "").strip()
        cur = (row.get("file_name") or "").strip() or (Path(fp).name if fp else "")
        if not cur:
            continue
        merged = inherit_missing_extension(nl, cur)
        if merged != nl:
            rows[i]["new_leaf"] = merged
            changed += 1
    return changed


def disambiguate_new_leaves_among_rows(rows: list[dict[str, str]]) -> tuple[int, int]:
    """
    First appends a missing file extension from each row's current file name (see
    :func:`merge_new_leaf_missing_extensions`). Then, after batch rules, many rows can share the
    same ``new_leaf`` in one folder: adjust ``new_leaf`` in place so proposed names are unique
    **per parent folder** among rows that actually rename, and do not collide with other paths
    already in that folder (case-insensitive).

    Returns ``(n_extension_merged, n_collision_resolved)``.
    """
    ext_merged = merge_new_leaf_missing_extensions(rows)
    by_parent: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for i, row in enumerate(rows):
        leaf = (row.get("new_leaf") or "").strip()
        if not leaf:
            continue
        fp = (row.get("file_path") or "").strip()
        if not fp:
            continue
        cur = (row.get("file_name") or "").strip() or Path(fp).name
        if leaf == cur:
            continue
        try:
            parent_s = str(Path(fp).expanduser().resolve(strict=False).parent)
        except OSError:
            parent_s = str(Path(fp).parent)
        by_parent[parent_s].append((i, leaf, cur))

    changed = 0
    for parent_s, items in by_parent.items():
        items.sort(key=lambda t: t[0])
        parent = Path(parent_s)
        occ: set[str] = set()
        if parent.is_dir():
            try:
                occ = {p.name.casefold() for p in parent.iterdir()}
            except OSError:
                occ = set()

        for i, desired, cur_name in items:
            cur_cf = cur_name.casefold()
            occ.discard(cur_cf)

            p_des = Path(desired)
            base = p_des.stem
            ext = p_des.suffix
            cand = desired
            n = 0
            cand_cf = cand.casefold()
            while cand_cf in occ:
                n += 1
                cand = f"{base}_{n}{ext}"
                cand_cf = cand.casefold()

            if cand != desired:
                rows[i]["new_leaf"] = cand
                changed += 1
            occ.add(cand_cf)

    return ext_merged, changed


def apply_file_renames(
    rows: list[dict[str, str]],
    *,
    only_under_folder: Optional[str] = None,
    only_indices: Optional[Sequence[int]] = None,
    dry_run: bool = False,
    keep_alive: Optional[Callable[[int], None]] = None,
    keep_alive_every: int = 40,
    progress: Optional[ProgressCallback] = None,
    undo_stack: Optional[list[RenameUndoRecord]] = None,
) -> tuple[int, int, list[str]]:
    """
    For each row with non-empty new_leaf different from file_name, rename on disk.
    If ``new_leaf`` has no extension, the current file's extension is appended first (same rule as
    :func:`inherit_missing_extension`).
    If ``only_indices`` is set, only those row indices are considered (e.g. Tab 5 selection).
    Optional ``keep_alive(step)`` is called from the GUI main thread every ``keep_alive_every``
    processed rows so the window stays responsive during long batches.
    Optional ``progress(current, total)`` reports how many row indices have been processed
    (``total`` = number of indices in this run).
    If ``undo_stack`` is given and ``dry_run`` is false, each successful rename appends
    ``(row_index, old_path, new_path, new_leaf_before)`` for :func:`undo_file_renames`.
    Returns (renamed_count, skipped_count, log_lines).
    """
    log: list[str] = []
    renamed = 0
    skipped = 0

    root_filter: Optional[Path] = None
    if only_under_folder and only_under_folder.strip():
        root_filter = Path(only_under_folder.strip()).resolve()
        if not root_filter.is_dir():
            log.append(f"Only-under folder does not exist: {root_filter}")
            return 0, 0, log

    if only_indices is not None:
        allowed: set[int] = set()
        for raw_i in only_indices:
            try:
                ii = int(raw_i)
            except (TypeError, ValueError):
                continue
            if 0 <= ii < len(rows):
                allowed.add(ii)
        if not allowed:
            log.append("Rename: no valid indices (empty selection or out of range).\n")
            return 0, 0, log
        row_indices = sorted(allowed)
    else:
        row_indices = list(range(len(rows)))

    total = len(row_indices)
    if progress is not None and total > 0:
        progress(0, total)

    for step, i in enumerate(row_indices):
        if keep_alive is not None and step > 0 and step % max(1, keep_alive_every) == 0:
            keep_alive(step)
        try:
            row = rows[i]
            raw_fp = row["file_path"].strip()
            if not raw_fp:
                skipped += 1
                continue

            resolved = resolve_csv_path_to_existing_file(raw_fp)
            if resolved is None:
                log.append(f"Skip (not a file): {raw_fp!r}")
                skipped += 1
                continue

            old_full = resolved
            row["file_path"] = str(old_full)
            row["file_directory"] = str(old_full.parent)
            row["file_name"] = old_full.name
            row["file_extension"] = old_full.suffix

            if root_filter is not None:
                try:
                    old_full.relative_to(root_filter)
                except ValueError:
                    skipped += 1
                    continue

            leaf = old_full.name
            new_leaf_raw = (row.get("new_leaf") or "").strip()
            if not new_leaf_raw:
                skipped += 1
                continue
            if any(sep in new_leaf_raw for sep in "\\/:") or new_leaf_raw in (".", ".."):
                log.append(f"Skip (invalid new file name): {new_leaf_raw!r}")
                skipped += 1
                continue
            new_leaf = inherit_missing_extension(new_leaf_raw, leaf)
            if new_leaf != new_leaf_raw:
                row["new_leaf"] = new_leaf
            if new_leaf == leaf:
                skipped += 1
                continue

            parent = old_full.parent
            final_leaf = unique_leaf_in_dir(parent, new_leaf)
            dest = parent / final_leaf

            if dry_run:
                if renamed < _DRY_RUN_LOG_LINE_CAP:
                    log.append(f"[dry-run] {old_full} -> {dest}")
                elif renamed == _DRY_RUN_LOG_LINE_CAP:
                    log.append(
                        "[dry-run] ... (further per-file preview lines omitted in log; "
                        "rename counts in the summary are still complete.)"
                    )
                renamed += 1
                continue

            try:
                old_full.rename(dest)
                row["file_path"] = str(dest)
                row["file_directory"] = str(dest.parent)
                row["file_name"] = dest.name
                row["file_extension"] = dest.suffix
                row["new_leaf"] = ""
                if undo_stack is not None:
                    undo_stack.append((i, str(old_full), str(dest), new_leaf_raw))
                log.append(f"OK: {dest}")
                renamed += 1
            except OSError as e:
                log.append(f"FAIL: {old_full} -> {dest}: {e}")
                skipped += 1
        finally:
            done = step + 1
            if progress is not None and total > 0:
                if done == total or done % max(1, keep_alive_every) == 0:
                    progress(done, total)

    return renamed, skipped, log


def undo_file_renames(
    records: Sequence[RenameUndoRecord],
    rows: list[dict[str, str]],
    *,
    dry_run: bool = False,
    keep_alive: Optional[Callable[[int], None]] = None,
    keep_alive_every: int = 40,
) -> tuple[int, list[str]]:
    """
    Reverse a single ``apply_file_renames`` or ``move_files_only`` batch. ``records`` must be in
    the same forward order as that run; this function processes **last operation first**.
    Each record: ``(row_index, path_before, path_after, new_leaf_before)``.
    Uses ``shutil.move`` so cross-volume moves can be undone where the OS allows.
    Returns (undone_count, log_lines).
    """
    log: list[str] = []
    undone = 0
    rev = list(records)[::-1]
    total = len(rev)
    for step, (i, old_p_s, new_p_s, prev_leaf) in enumerate(rev):
        if keep_alive is not None and step > 0 and step % max(1, keep_alive_every) == 0:
            keep_alive(step)
        if i < 0 or i >= len(rows):
            log.append(f"[undo] skip: row index out of range: {i}\n")
            continue
        old_p = Path(old_p_s)
        new_p = Path(new_p_s)
        if dry_run:
            log.append(f"[undo dry-run] {new_p} -> {old_p}\n")
            continue
        if not new_p.is_file():
            log.append(f"[undo] skip (not a file): {new_p}\n")
            continue
        if old_p.exists():
            log.append(f"[undo] skip (target exists): {old_p}\n")
            continue
        try:
            shutil.move(str(new_p), str(old_p))
        except OSError as e:
            log.append(f"[undo] FAIL {new_p} -> {old_p}: {e}\n")
            continue
        row = rows[i]
        row["file_path"] = str(old_p)
        row["file_directory"] = str(old_p.parent)
        row["file_name"] = old_p.name
        row["file_extension"] = old_p.suffix
        row["new_leaf"] = prev_leaf
        log.append(f"[undo] OK: {new_p} -> {old_p}\n")
        undone += 1
    return undone, log


def apply_prefix_suffix_to_rows(
    rows: list[dict[str, str]],
    indices: list[int],
    *,
    prefix: str,
    suffix_before_ext: str,
) -> None:
    for i in indices:
        if i < 0 or i >= len(rows):
            continue
        row = rows[i]
        name = row.get("file_name") or Path(row["file_path"]).name
        p = Path(name)
        base = p.stem
        ext = p.suffix
        row["new_leaf"] = prefix + base + suffix_before_ext + ext


def replace_in_basename(
    name: str,
    find: str,
    replace_with: str,
    *,
    case_insensitive: bool = False,
) -> str:
    """Replace every occurrence of ``find`` in ``name`` (literal text, not regex)."""
    if not find:
        return name
    if case_insensitive:
        return re.sub(re.escape(find), replace_with, name, flags=re.IGNORECASE)
    return name.replace(find, replace_with)


def _find_replace_source_leaf(
    orig: str,
    current_leaf: str,
    find: str,
    replace_with: str,
    *,
    case_insensitive: bool,
) -> str:
    """
    Full file name string that find/replace runs on.

    Prefer **new_leaf** when the find text matches there (repeat Apply chains edits).
    If **new_leaf** is set but does not contain a match, fall back to **file_name** so text
    the user sees in the current-name column still matches.
    """
    cur = (current_leaf or "").strip()
    if not cur:
        return orig
    if not find:
        return cur
    if replace_in_basename(cur, find, replace_with, case_insensitive=case_insensitive) != cur:
        return cur
    if replace_in_basename(orig, find, replace_with, case_insensitive=case_insensitive) != orig:
        return orig
    return cur


def apply_find_replace_to_rows(
    rows: list[dict[str, str]],
    indices: list[int],
    *,
    find: str,
    replace_with: str,
    case_insensitive: bool = False,
) -> tuple[int, int, list[str]]:
    """
    Set ``new_leaf`` after find/replace. The source string is chosen by
    ``_find_replace_source_leaf`` (prefers ``new_leaf`` when the find text matches there,
    otherwise ``file_name`` when that matches).

    If the result equals the original ``file_name``, ``new_leaf`` is cleared (no rename).
    Returns (rows_updated, rows_skipped_invalid, warning_lines).
    """
    find = find or ""
    if not find.strip():
        return 0, 0, []
    warnings: list[str] = []
    updated = 0
    skipped = 0
    for i in indices:
        if i < 0 or i >= len(rows):
            continue
        row = rows[i]
        orig = row.get("file_name") or Path(row["file_path"]).name
        current_leaf = (row.get("new_leaf") or "").strip()
        source = _find_replace_source_leaf(
            orig,
            current_leaf,
            find,
            replace_with,
            case_insensitive=case_insensitive,
        )
        new = replace_in_basename(source, find, replace_with, case_insensitive=case_insensitive)

        if new == orig:
            row["new_leaf"] = ""
            continue
        if new == source:
            continue
        if any(sep in new for sep in "\\/:") or new in (".", ".."):
            warnings.append(f"Skip (invalid new name after replace): {new!r}")
            skipped += 1
            continue
        row["new_leaf"] = new
        updated += 1
    return updated, skipped, warnings


def rename_folder_dangerous(old: Path, new_basename: str) -> tuple[bool, str]:
    """
    Rename directory old to old.parent / new_basename. Destructive; breaks absolute paths elsewhere.
    """
    old = old.resolve()
    if not old.is_dir():
        return False, "Source is not a directory."
    name = new_basename.strip()
    if not name or name in (".", ".."):
        return False, "Invalid new folder name."
    if re.search(r'[\\/:*?"<>|]', name):
        return False, "New name must not contain \\ / : * ? \" < > |"
    dest = old.parent / name
    if dest.exists():
        return False, f"Target already exists: {dest}"
    try:
        old.rename(dest)
        return True, str(dest)
    except OSError as e:
        return False, str(e)


def sanitize_windows_dir_component(name: str) -> str:
    """
    Single folder name under a base path: strip separators / reserved characters.
    Returns "" if nothing usable remains.
    """
    s = (name or "").strip()
    if not s:
        return ""
    for ch in "\\/:*?\"<>|":
        s = s.replace(ch, "_")
    s = s.rstrip(" .")
    if not s or s in (".", ".."):
        return ""
    return s


def _stash_graphql_json(
    stash_url: str,
    api_key: str,
    graphql_path: str,
    payload: dict,
    *,
    timeout_sec: int = 30,
) -> tuple[Optional[dict], str]:
    """
    POST JSON to Stash GraphQL. Returns (parsed_body, error_message).
    On transport/HTTP/JSON errors: (None, msg). GraphQL-level errors: (parsed, msg) with msg non-empty.
    """
    gp = (graphql_path or "/graphql").strip()
    if not gp.startswith("/"):
        gp = "/" + gp
    url = stash_url.strip().rstrip("/") + gp
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if api_key.strip():
        headers["ApiKey"] = api_key.strip()
    req = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=timeout_sec) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            status = getattr(resp, "status", 200)
    except OSError as e:
        return None, f"HTTP request failed: {e}"
    if status < 200 or status >= 300:
        return None, f"HTTP {status}: {body[:500]}"
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return None, f"Invalid JSON response: {body[:500]}"
    errs = parsed.get("errors") if isinstance(parsed, dict) else None
    if errs:
        msg = "; ".join(str(e.get("message", e)) for e in errs if isinstance(e, dict))
        if not msg:
            msg = str(errs)
        return parsed, msg
    return parsed, ""


def resolve_move_destination_root(base_folder: str, subfolder: str) -> tuple[Optional[Path], Optional[str]]:
    """
    Combine absolute base folder with optional subfolder segment.
    Returns (Path, None) or (None, error_message).
    """
    base = Path(base_folder.strip())
    if not base_folder.strip():
        return None, "Target folder is empty."
    if not base.is_absolute():
        return None, f"Target folder must be an absolute path: {base_folder!r}"
    sub = sanitize_windows_dir_component(subfolder)
    if (subfolder or "").strip() and not sub:
        return None, f"Invalid subfolder name after sanitizing: {subfolder!r}"
    final = base / sub if sub else base
    return final, None


def move_files_only(
    rows: list[dict[str, str]],
    indices: list[int],
    *,
    target_folder: str,
    subfolder: str = "",
    dry_run: bool = False,
    per_source_subfolder: bool = False,
    keep_alive: Optional[Callable[[int], None]] = None,
    keep_alive_every: int = 40,
    progress: Optional[ProgressCallback] = None,
    undo_stack: Optional[list[RenameUndoRecord]] = None,
) -> tuple[int, int, list[str]]:
    """
    Move files only (no Stash/API update).
    Optional ``keep_alive(step)`` is called every ``keep_alive_every`` processed files (GUI thread).
    Optional ``progress(current, total)`` uses ``total = len(indices)``.
    If ``undo_stack`` is given and ``dry_run`` is false, each successful move appends
    ``(row_index, old_path, new_path, new_leaf_before)`` for :func:`undo_file_renames`.
    Returns (moved_count, skipped_count, log_lines).
    """
    log: list[str] = []
    moved = 0
    skipped = 0

    sub = sanitize_windows_dir_component(subfolder)
    if per_source_subfolder:
        if not sub:
            return 0, len(indices), ["Per-source mode needs a valid subfolder name."]
        target: Optional[Path] = None
    else:
        target, terr = resolve_move_destination_root(target_folder, subfolder)
        if terr or target is None:
            return 0, len(indices), [terr or "Invalid target folder."]
        try:
            target.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return 0, len(indices), [f"Cannot create target folder {target}: {e}"]

    total = len(indices)
    if progress is not None and total > 0:
        progress(0, total)

    for step, i in enumerate(indices):
        if keep_alive is not None and step > 0 and step % max(1, keep_alive_every) == 0:
            keep_alive(step)
        try:
            if i < 0 or i >= len(rows):
                skipped += 1
                continue
            row = rows[i]
            raw_fp = (row.get("file_path") or "").strip()
            if not raw_fp:
                log.append("Skip: empty file_path.")
                skipped += 1
                continue
            resolved = resolve_csv_path_to_existing_file(raw_fp)
            if resolved is None:
                log.append(f"Skip (not a file): {raw_fp!r}")
                skipped += 1
                continue

            old_full = resolved
            if per_source_subfolder:
                target_dir = old_full.parent / sub
                try:
                    target_dir.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    log.append(f"Cannot create per-source target folder {target_dir}: {e}")
                    skipped += 1
                    continue
            else:
                target_dir = target
                if target_dir is None:
                    log.append("Internal error: target folder not resolved.")
                    skipped += 1
                    continue
            dest_leaf = unique_leaf_in_dir(target_dir, old_full.name)
            dest = target_dir / dest_leaf
            prev_new_leaf = (row.get("new_leaf") or "").strip()

            if dry_run:
                if moved < _DRY_RUN_LOG_LINE_CAP:
                    log.append(f"[dry-run] move {old_full} -> {dest}")
                elif moved == _DRY_RUN_LOG_LINE_CAP:
                    log.append(
                        "[dry-run] ... (further per-file preview lines omitted in log; "
                        "move counts in the summary are still complete.)"
                    )
                moved += 1
                continue
            try:
                shutil.move(str(old_full), str(dest))
                moved += 1
                row["file_path"] = str(dest)
                row["file_directory"] = str(dest.parent)
                row["file_name"] = dest.name
                row["file_extension"] = dest.suffix
                row["new_leaf"] = ""
                if undo_stack is not None:
                    undo_stack.append((i, str(old_full), str(dest), prev_new_leaf))
                log.append(f"OK: moved {old_full} -> {dest}")
            except OSError as e:
                log.append(f"Move failed: {old_full} -> {dest}: {e}")
                skipped += 1
        finally:
            done = step + 1
            if progress is not None and total > 0:
                if done == total or done % max(1, keep_alive_every) == 0:
                    progress(done, total)

    return moved, skipped, log


def test_stash_graphql_connection(
    stash_url: str,
    api_key: str,
    graphql_path: str = "/graphql",
    *,
    timeout_sec: int = 30,
) -> tuple[bool, str]:
    """Minimal GraphQL ping to validate endpoint/auth reachability."""
    gp = (graphql_path or "/graphql").strip()
    if not gp.startswith("/"):
        gp = "/" + gp
    url = stash_url.strip().rstrip("/") + gp
    payload = {"query": "query Ping { __typename }", "variables": {}}
    parsed, err = _stash_graphql_json(stash_url, api_key, graphql_path, payload, timeout_sec=timeout_sec)
    if parsed is None:
        return False, err or "Connection failed"
    if err:
        return False, err
    return True, f"GraphQL endpoint reachable: {url}"


def probe_stash_csv_export_schema(
    stash_url: str,
    api_key: str,
    graphql_path: str = "/graphql",
    *,
    timeout_sec: int = 30,
) -> tuple[bool, str]:
    """
    Same findScenes query shape as export_stash_files.ps1 (one page). If this succeeds, CSV export
    from Stash should still work after a Stash update (for the user's "is my export broken?" check).
    """
    q = """
query ProbeCsvExport($filter: FindFilterType) {
  findScenes(filter: $filter) {
    count
    scenes {
      id
      title
      files {
        path
      }
    }
  }
}
""".strip()
    payload = {
        "query": q,
        "variables": {"filter": {"per_page": 1, "page": 1}},
    }
    parsed, err = _stash_graphql_json(
        stash_url, api_key, graphql_path, payload, timeout_sec=timeout_sec
    )
    if parsed is None:
        return False, err or "Request failed"
    if err:
        return False, err
    data = parsed.get("data") if isinstance(parsed, dict) else None
    if not isinstance(data, dict):
        return False, "Unexpected response (no data object)."
    fs = data.get("findScenes")
    if not isinstance(fs, dict):
        return False, "findScenes missing — export would fail."
    if "scenes" not in fs:
        return False, "findScenes.scenes missing — export would fail."
    cnt = fs.get("count")
    cnt_s = str(cnt) if cnt is not None else "?"
    return (
        True,
        f"same fields as CSV export (id, title, files.path). Scene count from Stash: ~{cnt_s}.",
    )


def find_ffprobe_executable() -> Optional[str]:
    return shutil.which("ffprobe")


def _media_path_for_ffprobe_argv(path_str: str) -> str:
    """
    Normalize paths for ffprobe subprocess argv.

    - ``file:///…`` URLs → local path when possible.
    - Windows ``\\\\?\\`` extended paths → conventional ``C:\\…`` / ``\\\\server\\…`` when the
      file is still visible there (many ffmpeg/ffprobe builds mishandle extended prefixes).
    """
    s = (path_str or "").strip()
    if not s:
        return s
    low = s.lower()
    if low.startswith("file:"):
        try:
            tail = url2pathname(urlparse(s).path or "")
            tail = tail.strip()
            if tail and os.path.isfile(tail):
                s = tail
        except (ValueError, OSError, TypeError):
            pass
    if os.name != "nt":
        return s
    t = s.strip()
    if not t.startswith("\\\\?\\"):
        return t
    upper = t.upper()
    if upper.startswith("\\\\?\\UNC\\"):
        rest = t[8:]
        conv = "\\\\" + rest.lstrip("\\")
        try:
            if os.path.isfile(conv):
                return conv
        except (OSError, ValueError):
            pass
        return t
    if len(t) >= 7 and t[5] == ":":
        conv = t[4:]
        try:
            if os.path.isfile(conv):
                return conv
        except (OSError, ValueError):
            pass
    return t


def ffprobe_video_size(
    path_str: str,
    *,
    ffprobe_exe: Optional[str] = None,
) -> tuple[Optional[int], Optional[int], str]:
    """
    First video stream width/height via ffprobe JSON. Returns (w, h, err).
    err empty on success.
    """
    exe = ffprobe_exe or find_ffprobe_executable()
    if not exe:
        return None, None, "ffprobe not found in PATH (install FFmpeg and add to PATH)"
    raw = (path_str or "").strip()
    if not raw:
        return None, None, "empty path"
    media = _media_path_for_ffprobe_argv(raw)
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    try:
        proc = subprocess.run(
            [
                exe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "json",
                media,
            ],
            capture_output=True,
            text=True,
            timeout=120,
            creationflags=creationflags,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, None, str(e)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        return None, None, err or f"ffprobe exit {proc.returncode}"
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return None, None, "invalid ffprobe JSON"
    streams = data.get("streams")
    if not isinstance(streams, list) or not streams:
        return None, None, "no video stream"
    st0 = streams[0]
    if not isinstance(st0, dict):
        return None, None, "bad stream entry"
    try:
        wi = int(st0.get("width") or 0)
        hi = int(st0.get("height") or 0)
    except (TypeError, ValueError):
        return None, None, "non-numeric size"
    if wi <= 0 or hi <= 0:
        return None, None, "invalid dimensions"
    return wi, hi, ""


def ffprobe_paths_parallel(
    paths: Sequence[str],
    *,
    ffprobe_exe: str,
    max_workers: int = 8,
    progress: Optional[ProgressCallback] = None,
) -> tuple[dict[str, tuple[int, int]], list[tuple[str, str]]]:
    """
    Run ffprobe for distinct non-empty paths in parallel.

    ``progress(done, total)`` may be called from worker threads (use ``widget.after`` to touch Tk).
    Returns ``(path -> (width, height), [(path, err), ...])`` for failures.
    """
    uniq: list[str] = []
    seen: set[str] = set()
    for raw in paths:
        p = (raw or "").strip()
        if not p or p in seen:
            continue
        seen.add(p)
        uniq.append(p)
    total = len(uniq)
    if total == 0:
        return {}, []
    results: dict[str, tuple[int, int]] = {}
    fails: list[tuple[str, str]] = []
    cpus = os.cpu_count() or 4
    mw = max(1, min(total, max_workers, max(2, min(8, cpus + 2))))
    lock = threading.Lock()
    done = 0

    def handle_one(p: str, w: Optional[int], h: Optional[int], err: str) -> None:
        nonlocal done
        with lock:
            err_s = err if isinstance(err, str) else (str(err) if err is not None else "")
            if w is not None and h is not None and w > 0 and h > 0:
                results[p] = (int(w), int(h))
            else:
                fails.append((p, err_s or "ffprobe failed"))
            done += 1
            d, t = done, total
            if progress and (d == 1 or d % 8 == 0 or d == t):
                progress(d, t)

    fut_to_path: dict = {}
    with ThreadPoolExecutor(max_workers=mw) as ex:
        for p in uniq:
            fut = ex.submit(ffprobe_video_size, p, ffprobe_exe=ffprobe_exe)
            fut_to_path[fut] = p
        for fut in as_completed(fut_to_path):
            p = fut_to_path[fut]
            try:
                w, h, err = fut.result()
            except Exception as e:
                handle_one(p, None, None, str(e))
            else:
                handle_one(p, w, h, err)
    return results, fails


def format_resolution_tag(width: int, height: int, mode: str) -> str:
    """mode: heightp (default) or wxh."""
    m = (mode or "heightp").strip().lower()
    if m == "wxh":
        return f"{width}x{height}"
    tier = {
        4320: "4320p",
        2160: "2160p",
        1440: "1440p",
        1080: "1080p",
        720: "720p",
        576: "576p",
        480: "480p",
        360: "360p",
    }
    return tier.get(height, f"{width}x{height}")


def extract_year_from_scene_date(s: str) -> str:
    t = (s or "").strip()
    if len(t) >= 4 and t[:4].isdigit():
        y = int(t[:4])
        if 1900 <= y <= 2100:
            return t[:4]
    m = re.search(r"(19|20)\d{2}", t)
    if m:
        y = int(m.group(0))
        if 1900 <= y <= 2100:
            return str(y)
    return ""


def _file_timestamp_for_schema_year(path: Path) -> float:
    """
    Best-effort "when did this file appear" for year extraction (local time when converted).
    Windows: creation time (``st_ctime``). macOS (and some BSD): ``st_birthtime`` if set.
    Otherwise: last modification time (``st_mtime``). On Linux, true creation time is often unavailable.
    """
    st = path.stat()
    if os.name == "nt":
        return st.st_ctime
    birth = getattr(st, "st_birthtime", None)
    if birth is not None and birth > 0:
        return birth
    return st.st_mtime


def extract_year_from_file_for_schema(path: Path) -> str:
    """YYYY from file timestamps (see ``_file_timestamp_for_schema_year``)."""
    try:
        if not path.is_file():
            return ""
        y = datetime.fromtimestamp(_file_timestamp_for_schema_year(path)).year
        if 1900 <= y <= 2100:
            return str(y)
    except OSError:
        pass
    return ""


def year_for_schema_rename_bracket(row: dict[str, str]) -> str:
    """Prefer ``scene_date`` from CSV/Stash; if empty or unusable, use on-disk file (creation where OS exposes it)."""
    y = extract_year_from_scene_date(row.get("scene_date") or "")
    if y:
        return y
    resolved = resolve_csv_path_to_existing_file((row.get("file_path") or "").strip())
    if resolved is None:
        return ""
    return extract_year_from_file_for_schema(resolved)


def format_rating_token_for_schema(raw: str) -> str:
    """
    Stash GraphQL often uses rating100 (0–100). Maps to 1–5 for compact [n] tags.
    Non-numeric values are sanitized and truncated (custom stars text).
    """
    s = (raw or "").strip()
    if not s:
        return ""
    try:
        v = int(float(s.replace(",", ".")))
    except ValueError:
        inner = sanitize_windows_dir_component(s)
        return inner[:20] if inner else ""
    if v <= 0:
        return ""
    stars = max(1, min(5, (v + 10) // 20))
    return str(stars)


def primary_label_for_schema_row(row: dict[str, str]) -> str:
    """
    Short name source for Tab 5 proposed file name: scene_title only, then file stem.
    Stash tags/markers stay in CSV for search/columns — they are not used as the title prefix.
    """
    st = (row.get("scene_title") or "").strip()
    if st:
        return st
    return Path(row.get("file_name") or "").stem


def title_head_before_trailing_bracket_tags(label: str) -> str:
    """
    Text used for ``title_max_len`` in ``build_schema_rename_leaf``: trailing `` [a] [b]``
    groups are **not** part of the title — they are treated like filename tags (same rule as
    ``split_stem_trailing_bracket_groups`` on the stem) so truncation does not cut inside them.
    """
    t = (label or "").strip()
    if not t:
        return ""
    head, _tail = split_stem_trailing_bracket_groups(t)
    h = head.strip()
    return h if h else t


def sanitize_schema_label(s: str, *, max_len: int = 80) -> str:
    t = (s or "").strip()
    if not t:
        return ""
    for ch in "\\/:*?\"<>|":
        t = t.replace(ch, "_")
    t = t.rstrip(" .")
    if not t:
        return ""
    return t[:max_len]


def schema_unlimited_title_head_from_row(row: dict[str, str]) -> str:
    """
    Sanitized title used when ``title_max_len`` <= 0 in ``build_schema_rename_leaf`` — same
    source as the unlimited (non-truncated) head: ``scene_title`` / file stem, max 400 chars.
    """
    title_src = primary_label_for_schema_row(row)
    t = sanitize_schema_label(title_src, max_len=400)
    return t if t else "video"


def build_schema_rename_leaf(
    row: dict[str, str],
    *,
    title_max_len: int = 15,
    tag_enabled: Optional[list[bool]] = None,
    tag_text: Optional[list[str]] = None,
    include_year: bool = True,
    include_resolution: bool = True,
    include_rating: bool = True,
    resolution_mode: str = "heightp",
    video_width: Optional[int] = None,
    video_height: Optional[int] = None,
) -> tuple[str, str]:
    """
    Build a file name like: ShortTitle (2020) - [HDR] [1080p] [4].ext
    Year in parentheses: Stash ``scene_date`` when present, else the video file's year from
    creation time (Windows) / birth time (macOS) / else last modification.
    ``title_max_len`` 0 or negative: use the full sanitized title (still capped in ``sanitize_schema_label``).
    Positive values 1–200 truncate the title stem.
    Returns (leaf, warning). leaf empty if result would be invalid.
    """
    warn = ""
    try:
        tml = int(title_max_len)
    except (TypeError, ValueError):
        tml = 15

    te = list(tag_enabled or [])
    tt = list(tag_text or [])
    while len(te) < 5:
        te.append(False)
    while len(tt) < 5:
        tt.append("")
    te = te[:5]
    tt = tt[:5]

    base_title = schema_unlimited_title_head_from_row(row)
    # 0 (or negative): keep full sanitized title; 1–200: truncate only the head before any
    # trailing ``[…]`` blocks (those are tags on the file name, not part of the title string).
    if tml <= 0:
        title_short = base_title
    else:
        tml = max(1, min(200, tml))
        head_for_len = title_head_before_trailing_bracket_tags(base_title)
        title_short = head_for_len[:tml]

    year_part = ""
    if include_year:
        y = year_for_schema_rename_bracket(row)
        if y:
            year_part = f" ({y})"

    brackets: list[str] = []
    for i in range(5):
        if te[i] and (tt[i] or "").strip():
            inner = sanitize_schema_label(tt[i].strip(), max_len=40)
            if inner:
                brackets.append(f"[{inner}]")

    if include_resolution:
        if video_width and video_height:
            brackets.append(
                f"[{format_resolution_tag(video_width, video_height, resolution_mode)}]"
            )
        else:
            if not warn:
                warn = "resolution enabled but dimensions missing (click ffprobe start)"

    if include_rating:
        rt = format_rating_token_for_schema(row.get("scene_rating") or "")
        if rt:
            brackets.append(f"[{rt}]")

    tail = ""
    if brackets:
        tail = " - " + " ".join(brackets)

    ext = Path(row.get("file_name") or "").suffix

    leaf = f"{title_short}{year_part}{tail}{ext}"
    if any(c in leaf for c in '\\/:*?"<>|'):
        return "", "result contains illegal filename characters"
    if not leaf.strip():
        return "", "empty file name"
    return leaf, warn


def _remove_bracket_tokens_with_inners_casefold(stem: str, inners_cf: set[str]) -> str:
    """Remove `` [inner]`` / ``[inner]`` groups whose ``inner.casefold()`` is in ``inners_cf``."""
    if not stem or not inners_cf:
        return stem
    parts: list[str] = []
    pos = 0
    for m in re.finditer(r"\s*\[([^\]]+)\]", stem):
        parts.append(stem[pos : m.start()])
        inner_cf = m.group(1).strip().casefold()
        if inner_cf not in inners_cf:
            parts.append(m.group(0))
        pos = m.end()
    parts.append(stem[pos:])
    joined = "".join(parts)
    joined = re.sub(r" {2,}", " ", joined).rstrip()
    return joined


def append_schema_tags_to_leaf(
    base_leaf: str,
    *,
    tag_enabled: Optional[list[bool]] = None,
    tag_text: Optional[list[str]] = None,
    replace_existing_slot_tags: bool = False,
) -> str:
    """
    Append currently enabled custom ``[tag]`` slots to an existing file leaf without rebuilding title/year.
    Existing bracket tokens are kept and duplicates are avoided (case-insensitive).

    If ``replace_existing_slot_tags`` is True, any existing ``[inner]`` matching a **checked**
    slot's text (after sanitise) is removed first so the slot can be re-applied (overwrite-tags mode).
    """
    leaf = (base_leaf or "").strip()
    if not leaf:
        return ""
    if any(sep in leaf for sep in "\\/:") or leaf in (".", ".."):
        return ""

    te = list(tag_enabled or [])
    tt = list(tag_text or [])
    while len(te) < 5:
        te.append(False)
    while len(tt) < 5:
        tt.append("")
    te = te[:5]
    tt = tt[:5]

    if replace_existing_slot_tags:
        targets_cf: set[str] = set()
        for i in range(5):
            if te[i] and (tt[i] or "").strip():
                inn = sanitize_schema_label((tt[i] or "").strip(), max_len=40)
                if inn:
                    targets_cf.add(inn.casefold())
        if targets_cf:
            ext = Path(leaf).suffix
            stem = leaf[: -len(ext)] if ext else leaf
            stem = _remove_bracket_tokens_with_inners_casefold(stem, targets_cf)
            stem = stem.rstrip() or "video"
            leaf = f"{stem}{ext}"

    existing: set[str] = set()
    for m in re.finditer(r"\[([^\]]+)\]", leaf):
        raw = (m.group(1) or "").strip()
        if not raw:
            continue
        sx = sanitize_schema_label(raw, max_len=40)
        if sx:
            existing.add(sx.casefold())

    add: list[str] = []
    for i in range(5):
        if not te[i]:
            continue
        inner = sanitize_schema_label((tt[i] or "").strip(), max_len=40)
        if not inner:
            continue
        key = inner.casefold()
        if key in existing:
            continue
        existing.add(key)
        add.append(f"[{inner}]")

    if not add:
        return leaf

    ext = Path(leaf).suffix
    stem = leaf[: -len(ext)] if ext else leaf
    stem = stem.rstrip() or "video"
    return f"{stem} {' '.join(add)}{ext}"


def bracket_inner_tokens_from_leaf_stem(leaf: str) -> list[str]:
    """Ordered ``[inner]`` contents from the file stem (extension ignored)."""
    leaf = (leaf or "").strip()
    if not leaf:
        return []
    ext = Path(leaf).suffix
    stem = leaf[: -len(ext)] if ext else leaf
    return [m.group(1).strip() for m in re.finditer(r"\[([^\]]+)\]", stem) if m.group(1).strip()]


def merge_extra_bracket_tags_into_leaf(prior_leaf: str, schema_leaf: str) -> str:
    """
    When ``schema_leaf`` is rebuilt from title/year/slots (e.g. shorter title), keep any
    ``[...]`` tokens that were present in ``prior_leaf`` but are missing from ``schema_leaf``.
    Used after e.g. tags-only fill appended custom slots, then the user switches back to
    full schema with a smaller title max length.
    """
    prior_leaf = (prior_leaf or "").strip()
    schema_leaf = (schema_leaf or "").strip()
    if not prior_leaf or not schema_leaf:
        return schema_leaf or prior_leaf
    old_tokens = bracket_inner_tokens_from_leaf_stem(prior_leaf)
    if not old_tokens:
        return schema_leaf
    fresh_cf = {t.casefold() for t in bracket_inner_tokens_from_leaf_stem(schema_leaf)}
    extras: list[str] = []
    for t in old_tokens:
        cf = t.casefold()
        if cf in fresh_cf:
            continue
        fresh_cf.add(cf)
        inn = sanitize_schema_label(t, max_len=40)
        if inn:
            extras.append(f"[{inn}]")
    if not extras:
        return schema_leaf
    ext = Path(schema_leaf).suffix
    stem = schema_leaf[: -len(ext)] if ext else schema_leaf
    stem = stem.rstrip() or "video"
    return f"{stem} {' '.join(extras)}{ext}"


def split_stem_trailing_bracket_groups(stem: str) -> tuple[str, str]:
    """
    Split ``stem`` into (head, trailing_groups) where ``trailing_groups`` collects a suffix made of
    `` [tag]`` tokens and optional Windows-style **copy markers** ``]_1``, ``]_2``, … between tags.

    Parsed **from the right**: e.g. ``10001_ - [Cat] [720p]_1 [Dog] [Park]`` yields head
    ``10001_ -`` and tail `` [Cat] [720p]_1 [Dog] [Park]``. A single regex on ``(brackets)+(_\\d+)?$``
    is wrong once ``_1`` is followed by more `` […]`` tokens (append-tags / fill order).

    If nothing matches, returns ``(stem, "")``.
    """
    stem = (stem or "").rstrip()
    if not stem:
        return "", ""
    chunks_rev: list[str] = []
    s = stem
    _re_bracket_end = re.compile(r"(\s*\[[^\]]+\])\s*$")
    _re_copy_after_bracket = re.compile(r"](_\d+)\s*$")
    while True:
        s = s.rstrip()
        if not s:
            break
        m_copy = _re_copy_after_bracket.search(s)
        m_br = _re_bracket_end.search(s)
        take_copy = bool(m_copy) and (not m_br or m_copy.start() > m_br.start())
        if take_copy:
            chunks_rev.append(m_copy.group(1))
            s = s[: m_copy.start() + 1].rstrip()
            continue
        if m_br:
            chunks_rev.append(m_br.group(1))
            s = s[: m_br.start()].rstrip()
            continue
        break
    if not chunks_rev:
        return stem, ""
    tail = "".join(reversed(chunks_rev))
    return s.rstrip(), tail


def rehydrate_leaf_stem_head_from_schema_row(row: dict[str, str], leaf: str) -> tuple[str, str]:
    """
    Replace the stem head (text before trailing `` […] `` groups) with the full schema title
    from the CSV row — same unlimited head as ``build_schema_rename_leaf`` with
    ``title_max_len`` <= 0. Preserves extension and trailing bracket groups on ``leaf``.

    Used for append-tags-only when title max is unlimited so the preview does not stay stuck
    on an older shortened ``new_leaf`` / file stem.
    """
    warn = ""
    leaf = (leaf or "").strip()
    if not leaf:
        return "", ""
    if any(c in leaf for c in '\\/:*?"<>|'):
        return "", "result contains illegal filename characters"
    ext = Path(leaf).suffix
    stem = leaf[: -len(ext)] if ext else leaf
    _head, tail = split_stem_trailing_bracket_groups(stem)
    title_short = schema_unlimited_title_head_from_row(row)
    new_stem = f"{title_short}{tail}".rstrip()
    out = f"{new_stem}{ext}"
    if any(c in out for c in '\\/:*?"<>|'):
        return "", "result contains illegal filename characters"
    if not out.strip():
        return "", "empty file name"
    return out, warn


_YEAR_PARENS_END_RE = re.compile(r"\s*\((19|20)\d{2}\)\s*$")


def _strip_trailing_year_parens(head: str) -> str:
    h = (head or "").rstrip()
    while True:
        m = _YEAR_PARENS_END_RE.search(h)
        if not m:
            return h
        h = h[: m.start()].rstrip()


def _head_ends_with_year_parens(head: str) -> bool:
    return bool(_YEAR_PARENS_END_RE.search((head or "").rstrip()))


def _bracket_inners_ordered_from_suffix(s: str) -> list[str]:
    s = (s or "").strip()
    if not s:
        return []
    return [m.group(1).strip() for m in re.finditer(r"\[([^\]]+)\]", s) if m.group(1).strip()]


def _looks_like_schema_resolution_inner(inner: str) -> bool:
    t = (inner or "").strip()
    if re.fullmatch(r"\d+p", t, flags=re.IGNORECASE):
        return True
    return bool(re.fullmatch(r"\d+\s*x\s*\d+", t, flags=re.IGNORECASE))


def _looks_like_compact_schema_rating_inner(inner: str) -> bool:
    """Single-digit 1–5 (star buckets from numeric Stash rating)."""
    t = (inner or "").strip()
    if len(t) != 1 or not t.isdigit():
        return False
    v = int(t)
    return 1 <= v <= 5


def _stem_contains_resolution_like_bracket(stem: str) -> bool:
    """True if ``stem`` already has any ``[…]`` token that looks like a resolution label."""
    for m in re.finditer(r"\[([^\]]+)\]", stem or ""):
        if _looks_like_schema_resolution_inner(m.group(1)):
            return True
    return False


def _stem_contains_compact_rating_like_bracket(stem: str) -> bool:
    """True if ``stem`` already has a compact ``[1]``–``[5]`` style rating token."""
    for m in re.finditer(r"\[([^\]]+)\]", stem or ""):
        if _looks_like_compact_schema_rating_inner(m.group(1)):
            return True
    return False


def _restore_bracket_copy_suffixes(out_stem: str, prior_tail_groups: str) -> str:
    """
    Re-insert ``]_N`` copy markers that followed a ``[inner]`` in the original trailing tail.

    ``merge_schema_metadata_into_append_leaf`` rebuilds the suffix from bracket inners only, so
    ``[720p]_1 [Dog]`` would otherwise become ``[720p] [Dog]`` and move the copy marker incorrectly.
    """
    if not out_stem or not prior_tail_groups or "]_" not in prior_tail_groups:
        return out_stem
    out = out_stem
    for m in re.finditer(r"\[([^\]]+)\](_\d+)", prior_tail_groups):
        inner_s = sanitize_schema_label(m.group(1).strip(), max_len=40)
        sfx = m.group(2)
        if not inner_s:
            continue
        plain = f"[{inner_s}]"
        combined = f"[{inner_s}]{sfx}"
        if combined in out:
            continue
        if plain in out:
            out = out.replace(plain, combined, 1)
    return out


def strip_non_auto_bracket_tags_from_leaf(leaf: str) -> str:
    """
    Keep only resolution- and compact-rating-like ``[…]`` tokens in the trailing bracket suffix;
    drop custom and slot-style brackets so the leaf can be rebuilt from checked slots.

    Year ``(YYYY)`` on the head is left unchanged.
    """
    leaf = (leaf or "").strip()
    if not leaf or any(c in leaf for c in '\\/:*?"<>|'):
        return leaf
    ext = Path(leaf).suffix
    stem = leaf[: -len(ext)] if ext else leaf
    head, tail_groups = split_stem_trailing_bracket_groups(stem)
    head = (head or "").rstrip()
    head = re.sub(r"\s+-\s*$", "", head).rstrip()
    inners = _bracket_inners_ordered_from_suffix(tail_groups)
    kept: list[str] = []
    for x in inners:
        if _looks_like_schema_resolution_inner(x) or _looks_like_compact_schema_rating_inner(x):
            sx = sanitize_schema_label(x.strip(), max_len=40)
            if sx:
                kept.append(sx)
    if kept:
        out_stem = f"{head} - {' '.join(f'[{x}]' for x in kept)}".rstrip()
    else:
        out_stem = head
    return f"{out_stem}{ext}"


def merge_schema_metadata_into_append_leaf(
    base_leaf: str,
    row: dict[str, str],
    *,
    include_year: bool,
    include_resolution: bool,
    include_rating: bool,
    resolution_mode: str,
    video_width: Optional[int],
    video_height: Optional[int],
    overwrite_auto_tags: bool = False,
    preserve_auto_tokens_from_leaf: bool = False,
) -> tuple[str, str]:
    """
    After custom ``[slot]`` tags were appended, add year / resolution / rating from the CSV row
    in the same style as ``build_schema_rename_leaf`` (``(YYYY)`` before the `` - […]`` block).

    * Unchecked **include_year / include_resolution / include_rating**: existing matching tokens
      are removed from the leaf (so you can drop those special tags again).
    * ``preserve_auto_tokens_from_leaf`` True: never replace an existing year suffix or existing
      resolution/rating-like ``[…]`` text with CSV/ffprobe values — only add when missing and
      the corresponding include flag is on.
    * ``overwrite_auto_tags`` True (optional): replace auto tokens from CSV/ffprobe even when
      already present (ignored when ``preserve_auto_tokens_from_leaf`` is True).
    """
    warn = ""
    leaf = (base_leaf or "").strip()
    if not leaf:
        return "", ""
    if any(c in leaf for c in '\\/:*?"<>|'):
        return "", "result contains illegal filename characters"

    ext = Path(leaf).suffix
    stem = leaf[: -len(ext)] if ext else leaf
    stem_in = stem
    head, tail_groups = split_stem_trailing_bracket_groups(stem)
    head = (head or "").rstrip()
    # ``split_stem…`` leaves a literal `` - `` before the bracket suffix on disk; drop it here
    # so year ``(YYYY)`` sits at the head end and we do not emit `` - - […]`` when rebuilding.
    head = re.sub(r"\s+-\s*$", "", head).rstrip()
    inners = _bracket_inners_ordered_from_suffix(tail_groups)

    y = year_for_schema_rename_bracket(row) if include_year else ""

    if not include_year:
        head = _strip_trailing_year_parens(head)
    elif include_year and y:
        year_part = f" ({y})"
        if preserve_auto_tokens_from_leaf:
            if not _head_ends_with_year_parens(head):
                head = (head + year_part).rstrip()
        elif overwrite_auto_tags:
            head = _strip_trailing_year_parens(head)
            head = (head + year_part).rstrip()
        elif not _head_ends_with_year_parens(head):
            head = (head + year_part).rstrip()
    elif overwrite_auto_tags and not preserve_auto_tokens_from_leaf:
        head = _strip_trailing_year_parens(head)

    res_inner = ""
    if include_resolution and video_width and video_height:
        res_inner = format_resolution_tag(video_width, video_height, resolution_mode)
    elif include_resolution:
        if not warn:
            warn = "resolution enabled but dimensions missing (click ffprobe start)"

    rat_inner = ""
    if include_rating:
        rt = format_rating_token_for_schema(row.get("scene_rating") or "")
        if rt:
            rat_inner = str(rt).strip()

    new_inners: list[str] = []
    for inner in inners:
        if not include_resolution and _looks_like_schema_resolution_inner(inner):
            continue
        if not include_rating and _looks_like_compact_schema_rating_inner(inner):
            continue
        if preserve_auto_tokens_from_leaf:
            new_inners.append(inner)
            continue
        if overwrite_auto_tags:
            if include_resolution and video_width and video_height and res_inner:
                if _looks_like_schema_resolution_inner(inner) or inner.casefold() == res_inner.casefold():
                    continue
            if include_rating and rat_inner:
                if inner.casefold() == rat_inner.casefold():
                    continue
                if rat_inner.isdigit() and len(rat_inner) == 1 and _looks_like_compact_schema_rating_inner(inner):
                    continue
        new_inners.append(inner)

    cfset = {x.casefold() for x in new_inners}
    has_res_anywhere = _stem_contains_resolution_like_bracket(stem_in)
    has_rat_anywhere = _stem_contains_compact_rating_like_bracket(stem_in)

    if include_resolution and video_width and video_height and res_inner:
        if preserve_auto_tokens_from_leaf:
            if not any(_looks_like_schema_resolution_inner(x) for x in new_inners) and not has_res_anywhere:
                new_inners.append(res_inner)
                cfset.add(res_inner.casefold())
        elif overwrite_auto_tags:
            new_inners.append(res_inner)
            cfset.add(res_inner.casefold())
        elif (
            not any(_looks_like_schema_resolution_inner(x) for x in new_inners)
            and not has_res_anywhere
            and res_inner.casefold() not in cfset
        ):
            new_inners.append(res_inner)
            cfset.add(res_inner.casefold())

    if include_rating and rat_inner:
        if preserve_auto_tokens_from_leaf:
            if (
                rat_inner.casefold() not in cfset
                and not any(_looks_like_compact_schema_rating_inner(x) for x in new_inners)
                and not has_rat_anywhere
            ):
                new_inners.append(rat_inner)
                cfset.add(rat_inner.casefold())
        elif overwrite_auto_tags:
            if rat_inner.casefold() not in cfset:
                new_inners.append(rat_inner)
                cfset.add(rat_inner.casefold())
        elif rat_inner.casefold() not in cfset and not has_rat_anywhere:
            new_inners.append(rat_inner)
            cfset.add(rat_inner.casefold())

    sanitized: list[str] = []
    for x in new_inners:
        sx = sanitize_schema_label(x.strip(), max_len=40)
        if sx:
            sanitized.append(sx)
    if sanitized:
        out_stem = f"{head} - {' '.join(f'[{x}]' for x in sanitized)}".rstrip()
    else:
        out_stem = head
    if tail_groups:
        out_stem = _restore_bracket_copy_suffixes(out_stem, tail_groups)
    out = f"{out_stem}{ext}"
    if any(c in out for c in '\\/:*?"<>|'):
        return "", "result contains illegal filename characters"
    if not out.strip():
        return "", "empty file name"
    return out, warn


def build_leaf_tags_only_mode(
    row: dict[str, str],
    *,
    title_max_len: object = 15,
    tag_enabled: Optional[list[bool]] = None,
    tag_text: Optional[list[str]] = None,
    leaf_after_append_and_metadata: Optional[str] = None,
) -> tuple[str, str]:
    """
    "Only add tags" behaviour: append checked ``[slot]`` tokens to the current leaf, then shorten
    only the leading stem (before trailing `` [...] `` groups) using ``title_max_len`` — same
    rules as ``build_schema_rename_leaf`` (0 = unlimited: full schema title from the row, not
    the previous shortened stem; 1–200 = truncate that head).

    If ``leaf_after_append_and_metadata`` is set, the slot-append + CSV metadata merge was done
    elsewhere; only shortening / rehydration runs here.
    """
    warn = ""
    if leaf_after_append_and_metadata is not None:
        work = (leaf_after_append_and_metadata or "").strip()
        if not work:
            return "", ""
        if any(c in work for c in '\\/:*?"<>|'):
            return "", "result contains illegal filename characters"
    else:
        base_leaf = ((row.get("new_leaf") or "").strip() or (row.get("file_name") or "").strip())
        if not base_leaf:
            return "", ""
        if any(c in base_leaf for c in '\\/:*?"<>|'):
            return "", "result contains illegal filename characters"

        work = append_schema_tags_to_leaf(
            base_leaf,
            tag_enabled=tag_enabled,
            tag_text=tag_text,
        )
        if not work.strip():
            return "", ""

    try:
        tml = int(title_max_len)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        tml = 15

    if tml <= 0:
        return rehydrate_leaf_stem_head_from_schema_row(row, work)

    ext = Path(work).suffix
    stem = work[: -len(ext)] if ext else work
    head, tail = split_stem_trailing_bracket_groups(stem)

    raw_head = head.strip()
    if not raw_head:
        raw_head = primary_label_for_schema_row(row).strip()
    if not raw_head:
        raw_head = Path(row.get("file_name") or "").stem or "video"

    title = sanitize_schema_label(raw_head, max_len=400)
    if not title:
        title = "video"

    cap = max(1, min(200, tml))
    title_short = title[:cap]

    new_stem = f"{title_short}{tail}".rstrip()
    leaf = f"{new_stem}{ext}"
    if any(c in leaf for c in '\\/:*?"<>|'):
        return "", "result contains illegal filename characters"
    if not leaf.strip():
        return "", "empty file name"
    return leaf, warn


def truncate_leaf_stem_to_max_chars(leaf: str, title_max_len: object) -> tuple[str, str]:
    """
    Cap the full stem (everything before the extension) to ``title_max_len`` characters.
    ``title_max_len`` ≤ 0 leaves the leaf unchanged. Uses the same 1–200 cap as schema title trim.
    """
    leaf = (leaf or "").strip()
    if not leaf:
        return "", ""
    try:
        tml = int(title_max_len)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        tml = 15
    if tml <= 0:
        return leaf, ""
    ext = Path(leaf).suffix
    stem = leaf[: -len(ext)] if ext else leaf
    cap = max(1, min(200, tml))
    if len(stem) <= cap:
        return leaf, ""
    stem = stem[:cap].rstrip()
    if not stem:
        stem = "video"
    out = f"{stem}{ext}"
    if any(c in out for c in '\\/:*?"<>|'):
        return "", "result contains illegal filename characters"
    if not out.strip():
        return "", "empty file name"
    return out, ""
