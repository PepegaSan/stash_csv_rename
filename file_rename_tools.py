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
import shutil
import unicodedata
from pathlib import Path
from typing import Optional
from urllib.parse import unquote
from urllib.request import Request, urlopen

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
    "new_leaf",
)

# Lowercase alternate headers from other Stash export scripts / versions (used when primary is missing).
CSV_HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "file_path": ("path", "filepath", "full_path", "fullpath"),
    "scene_id": ("sceneid", "stash_scene_id", "stash_id"),
    "new_leaf": ("new_filename", "new_name", "target_leaf"),
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


# Longest match wins (e.g. folder: before path: is not needed — different strings; new: before nl: length 4>3).
_FIELD_FILTER_PREFIXES: tuple[tuple[str, str], ...] = (
    ("folder:", "path"),
    ("name:", "name"),
    ("file:", "name"),
    ("path:", "path"),
    ("new:", "new_leaf"),
    ("nl:", "new_leaf"),
)


def _split_filter_field_term(part: str) -> tuple[str | None, str]:
    """Return (field or None, remainder). field is path | name | new_leaf."""
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


def row_matches_search_filter(
    filter_raw: str,
    *,
    file_path: str = "",
    file_name: str = "",
    new_leaf: str = "",
) -> bool:
    """
    Tab 3 / Tab 4 list filter. Case-insensitive substring match unless a field prefix is used.

    Syntax:
    - Semicolon (;): AND between parts.
    - OR between groups: ``|``, `` OR ``, ``§`` (e.g. Shift+3 DE), or ``>`` (e.g. Shift+. US; ``>`` key DE).
    - Those markers inside ``"quotes"`` stay literal.
    - No prefix: part may match file_path, file_name, or new_leaf (any).
    - ``name:`` or ``file:`` — only the file name (leaf).
    - ``path:`` or ``folder:`` — only the full path.
    - ``new:`` or ``nl:`` — only the new file name column.
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
    nl_l = (new_leaf or "").lower()

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
        if field == "new_leaf":
            return t in nl_l
        return t in fp_l or t in fn_l or t in nl_l

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


def csv_row_from_path(p: Path) -> dict[str, str]:
    p = p.resolve()
    return {
        "scene_id": "",
        "scene_title": "",
        "file_path": str(p),
        "file_directory": str(p.parent),
        "file_name": p.name,
        "new_leaf": "",
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
        rows.append(
            {
                "scene_id": _coalesce_scene_id(norm),
                "scene_title": norm.get("scene_title", ""),
                "file_path": fp,
                "file_directory": norm.get("file_directory", "") or str(p.parent),
                "file_name": norm.get("file_name", "") or p.name,
                "new_leaf": _coalesce_norm_field(norm, "new_leaf"),
            }
        )
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


def apply_file_renames(
    rows: list[dict[str, str]],
    *,
    only_under_folder: Optional[str] = None,
    dry_run: bool = False,
) -> tuple[int, int, list[str]]:
    """
    For each row with non-empty new_leaf different from file_name, rename on disk.
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

    for row in rows:
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

        if root_filter is not None:
            try:
                old_full.relative_to(root_filter)
            except ValueError:
                skipped += 1
                continue

        leaf = old_full.name
        new_leaf = (row.get("new_leaf") or "").strip()
        if not new_leaf:
            skipped += 1
            continue
        if any(sep in new_leaf for sep in "\\/:") or new_leaf in (".", ".."):
            log.append(f"Skip (invalid new file name): {new_leaf!r}")
            skipped += 1
            continue
        if new_leaf == leaf:
            skipped += 1
            continue

        parent = old_full.parent
        final_leaf = unique_leaf_in_dir(parent, new_leaf)
        dest = parent / final_leaf

        if dry_run:
            log.append(f"[dry-run] {old_full} -> {dest}")
            renamed += 1
            continue

        try:
            old_full.rename(dest)
            row["file_path"] = str(dest)
            row["file_directory"] = str(dest.parent)
            row["file_name"] = dest.name
            row["new_leaf"] = ""
            log.append(f"OK: {dest}")
            renamed += 1
        except OSError as e:
            log.append(f"FAIL: {old_full} -> {dest}: {e}")
            skipped += 1

    return renamed, skipped, log


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


def apply_find_replace_to_rows(
    rows: list[dict[str, str]],
    indices: list[int],
    *,
    find: str,
    replace_with: str,
    case_insensitive: bool = False,
) -> tuple[int, int, list[str]]:
    """
    Set ``new_leaf`` after find/replace on the **working** name: if ``new_leaf`` is already set,
    that value is the source (so repeated Apply chains replacements); otherwise ``file_name``.
    If the result equals the original ``file_name``, ``new_leaf`` is cleared (no rename).
    Returns (rows_updated, rows_skipped_invalid, warning_lines).
    """
    warnings: list[str] = []
    updated = 0
    skipped = 0
    for i in indices:
        if i < 0 or i >= len(rows):
            continue
        row = rows[i]
        orig = row.get("file_name") or Path(row["file_path"]).name
        current_leaf = (row.get("new_leaf") or "").strip()
        source = current_leaf if current_leaf else orig
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
) -> tuple[int, int, list[str]]:
    """
    Move files only (no Stash/API update).
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

    for i in indices:
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

        if dry_run:
            log.append(f"[dry-run] move {old_full} -> {dest}")
            moved += 1
            continue
        try:
            shutil.move(str(old_full), str(dest))
            moved += 1
            row["file_path"] = str(dest)
            row["file_directory"] = str(dest.parent)
            row["file_name"] = dest.name
            row["new_leaf"] = ""
            log.append(f"OK: moved {old_full} -> {dest}")
        except OSError as e:
            log.append(f"Move failed: {old_full} -> {dest}: {e}")
            skipped += 1

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
