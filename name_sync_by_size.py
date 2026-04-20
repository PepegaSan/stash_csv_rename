#!/usr/bin/env python3
"""
Rename files under TARGET_DIR so their leaf names match the counterpart under SOURCE_DIR.

Matching is by exact file size (bytes) and file extension (case-insensitive suffix). Optionally
the SHA-256 hash of the first 1 MiB is included in the key to reduce false positives when many
files share the same size and extension.

Only renames are performed (no copy, move, or delete). Targets without a unique source partner
are left unchanged. Optionally targets whose basename already has Tab-5-style trailing `` [tag]``
groups can be excluded from renaming while keeping the same size/extension (and optional hash)
matching logic.
"""

from __future__ import annotations

import hashlib
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from file_rename_tools import leaf_has_trailing_bracket_tag_suffix

# --- Defaults when run as a script (edit freely) ---------------------------------
SOURCE_DIR = Path(r"E:\backup\media")  # Renamed files (reference names)
TARGET_DIR = Path(r"C:\Videos")  # Old names; files here get renamed in place
DRY_RUN = True  # If True, only print what would happen — no os.rename
# If True, matching key is (size, ext, sha256_first_1MiB); safer when sizes collide.
REQUIRE_PARTIAL_HASH = False
PARTIAL_HASH_BYTES = 1024 * 1024
# Max paths logged per ambiguous key group (avoid huge logs for degenerate trees).
_AMBIGUOUS_PATHS_LOG_CAP = 500


@dataclass(frozen=True)
class NameSyncResult:
    """Counters after a sync run."""

    renamed: int = 0
    skipped_ambiguous: int = 0
    skipped_no_partner: int = 0
    skipped_already_named: int = 0
    skipped_destination_exists: int = 0
    skipped_keep_bracket_tags: int = 0


def _normalize_extension(path: Path) -> str:
    """Lowercase suffix including leading dot, e.g. ``.MP4`` -> ``.mp4``."""
    return path.suffix.lower()


def _partial_file_hash(path: Path, max_bytes: int) -> Optional[str]:
    """SHA-256 of up to ``max_bytes`` bytes from the start of the file."""
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while max_bytes > 0:
                chunk = handle.read(min(65536, max_bytes))
                if not chunk:
                    break
                digest.update(chunk)
                max_bytes -= len(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _comparison_key(path: Path, *, use_partial_hash: bool, hash_bytes: int) -> Optional[tuple]:
    """
    Build a comparison key for ``path``.

    Returns ``None`` if the file cannot be read. Key is either ``(size, ext)`` or
    ``(size, ext, partial_hash_hex)``.
    """
    try:
        size = path.stat().st_size
    except OSError:
        return None
    ext = _normalize_extension(path)
    if not use_partial_hash:
        return (size, ext)
    ph = _partial_file_hash(path, hash_bytes)
    if ph is None:
        return None
    return (size, ext, ph)


def _iter_files(root: Path) -> list[Path]:
    """All regular files under ``root`` (recursive). Skips unreadable paths."""
    root = root.resolve()
    if not root.is_dir():
        return []
    out: list[Path] = []
    try:
        for candidate in root.rglob("*"):
            try:
                if candidate.is_file():
                    out.append(candidate)
            except OSError:
                continue
    except OSError:
        return []
    return out


def _index_by_key(
    files: list[Path],
    *,
    use_partial_hash: bool,
    hash_bytes: int,
) -> tuple[dict[tuple, list[Path]], list[str]]:
    """
    Group files by comparison key.

    Returns ``(index, warnings)`` where ``warnings`` lists keys that appear more than once
    (ambiguous on that side).
    """
    index: dict[tuple, list[Path]] = defaultdict(list)
    bad_read: list[Path] = []
    for path in files:
        key = _comparison_key(path, use_partial_hash=use_partial_hash, hash_bytes=hash_bytes)
        if key is None:
            bad_read.append(path)
            continue
        index[key].append(path)
    warns: list[str] = []
    for path in bad_read:
        warns.append(f"[skip unreadable] {path}")
    for key, paths in index.items():
        if len(paths) > 1:
            warns.append(f"[ambiguous group] {len(paths)} file(s) share the same match key {key!r}")
            cap = _AMBIGUOUS_PATHS_LOG_CAP
            for p in paths[:cap]:
                warns.append(f"  {p}")
            if len(paths) > cap:
                warns.append(f"  ... and {len(paths) - cap} more path(s) omitted (log cap)")
    return index, warns


def _format_match_key_for_ui(key: tuple) -> str:
    """Human-readable comparison key for grouping rows in the UI (not filenames)."""
    if not key:
        return ""
    size = key[0]
    ext = key[1] if len(key) > 1 else "?"
    if len(key) <= 2:
        return f"{size} B · {ext}"
    hx = key[2]
    if isinstance(hx, str) and len(hx) > 12:
        hx = hx[:12] + "…"
    return f"{size} B · {ext} · {hx}"


def _collect_index_duplicate_rows(
    index: dict[tuple, list[Path]],
    side: str,
    out: list[dict[str, str]],
    group_counter: list[int],
) -> None:
    """Append one row per file that shares a match key with at least one other file on the same side."""
    for key, paths in index.items():
        if len(paths) <= 1:
            continue
        gid = str(group_counter[0])
        group_counter[0] += 1
        key_repr = _format_match_key_for_ui(key)
        for p in paths:
            out.append(
                {
                    "group": gid,
                    "key": key_repr,
                    "side": side,
                    "path": str(p),
                    "reason": "group",
                }
            )


def sync_target_names_from_source(
    source_dir: Path,
    target_dir: Path,
    *,
    dry_run: bool = True,
    use_partial_hash: bool = False,
    hash_bytes: int = PARTIAL_HASH_BYTES,
    keep_target_if_bracket_tags: bool = False,
    log_line: Optional[Callable[[str], None]] = None,
    undo_stack: Optional[list[tuple[int, str, str, str]]] = None,
) -> tuple[NameSyncResult, list[str], list[dict[str, str]]]:
    """
    For each file under ``target_dir``, if there is exactly one file under ``source_dir`` with the
    same comparison key, rename the target file so its basename matches the source file's basename
    (same parent folder on the target side).

    If ``undo_stack`` is set and ``dry_run`` is false, each successful rename appends
    ``(0, old_path, new_path, new_leaf)`` in forward order for last-to-first undo (callers may pass
    these records to ``undo_file_renames`` with a one-element dummy ``rows`` list and index ``0``).

    If ``keep_target_if_bracket_tags`` is true, a target file whose basename already has trailing
    `` […]`` tag groups (Tab 5 schema style) is left unchanged even when the source suggests a
    different name; matching logic is unchanged.

    Returns ``(result, log_lines, duplicate_rows)``. ``duplicate_rows`` lists ambiguous same-side
    matches and multi-source collisions (for UI): each item has ``side`` (``source`` / ``target``),
    ``path``, ``reason`` (``group`` | ``multi_source``), ``group`` (same number = same collision
    cluster), and ``key`` (size / extension / optional hash summary — same value = same match key).
    """
    lines: list[str] = []

    def log(msg: str) -> None:
        lines.append(msg)
        if log_line is not None:
            log_line(msg)

    src_root = source_dir.expanduser()
    tgt_root = target_dir.expanduser()
    if not src_root.is_dir() or not tgt_root.is_dir():
        log(f"ERROR: SOURCE_DIR and TARGET_DIR must be existing directories.\n  source={src_root}\n  target={tgt_root}")
        return NameSyncResult(), lines, []

    log(f"Scanning source: {src_root.resolve()}")
    source_files = _iter_files(src_root)
    log(f"Scanning target: {tgt_root.resolve()}")
    target_files = _iter_files(tgt_root)

    src_index, src_warns = _index_by_key(source_files, use_partial_hash=use_partial_hash, hash_bytes=hash_bytes)
    tgt_index, tgt_warns = _index_by_key(target_files, use_partial_hash=use_partial_hash, hash_bytes=hash_bytes)
    for w in src_warns + tgt_warns:
        log(w)

    dup_rows: list[dict[str, str]] = []
    _grp_seq = [1]
    _collect_index_duplicate_rows(src_index, "source", dup_rows, _grp_seq)
    _collect_index_duplicate_rows(tgt_index, "target", dup_rows, _grp_seq)

    renamed = 0
    skipped_ambiguous = 0
    skipped_no_partner = 0
    skipped_already_named = 0
    skipped_destination_exists = 0
    skipped_keep_bracket_tags = 0

    for key, t_list in tgt_index.items():
        if len(t_list) != 1:
            skipped_ambiguous += len(t_list)
            for p in t_list:
                log(f"[skip ambiguous: multiple targets same key] {p}")
            continue

        tgt = t_list[0]
        s_list = src_index.get(key, [])
        if len(s_list) == 0:
            skipped_no_partner += 1
            continue
        if len(s_list) != 1:
            skipped_ambiguous += 1
            log(f"[skip ambiguous: multiple sources same key] target file: {tgt}")
            for sp in s_list:
                log(f"  matching source candidate: {sp}")
            gid = str(_grp_seq[0])
            _grp_seq[0] += 1
            key_repr = _format_match_key_for_ui(key)
            dup_rows.append(
                {"group": gid, "key": key_repr, "side": "target", "path": str(tgt), "reason": "multi_source"}
            )
            for sp in s_list:
                dup_rows.append(
                    {"group": gid, "key": key_repr, "side": "source", "path": str(sp), "reason": "multi_source"}
                )
            continue

        src = s_list[0]
        new_name = src.name
        if keep_target_if_bracket_tags and leaf_has_trailing_bracket_tag_suffix(tgt.name):
            if tgt.name == new_name:
                skipped_already_named += 1
            else:
                skipped_keep_bracket_tags += 1
                log(f"[skip keep bracket tags] {tgt}")
            continue
        if tgt.name == new_name:
            skipped_already_named += 1
            continue

        dest = tgt.with_name(new_name)
        if dest.exists() and dest.resolve() != tgt.resolve():
            skipped_destination_exists += 1
            log(f"[skip destination exists] {tgt} -> {dest}")
            continue

        if dry_run:
            log(f"[dry-run] RENAME: {tgt}  ->  {dest}")
            renamed += 1
        else:
            try:
                os.rename(tgt, dest)
                log(f"OK: {tgt}  ->  {dest}")
                renamed += 1
                if undo_stack is not None:
                    undo_stack.append((0, str(tgt), str(dest), new_name))
            except OSError as exc:
                skipped_ambiguous += 1
                log(f"[skip rename error] {tgt} -> {dest}: {exc}")

    result = NameSyncResult(
        renamed=renamed,
        skipped_ambiguous=skipped_ambiguous,
        skipped_no_partner=skipped_no_partner,
        skipped_already_named=skipped_already_named,
        skipped_destination_exists=skipped_destination_exists,
        skipped_keep_bracket_tags=skipped_keep_bracket_tags,
    )
    log(
        f"Summary: {result.renamed} file(s) successfully renamed"
        f"{' (dry-run)' if dry_run else ''}, "
        f"{result.skipped_ambiguous} skipped (ambiguous match and/or rename errors), "
        f"{result.skipped_no_partner} ignored (no partner in source), "
        f"{result.skipped_destination_exists} skipped (target name already exists), "
        f"{result.skipped_keep_bracket_tags} skipped (keep Tab-5-style [tag] suffix on target), "
        f"{result.skipped_already_named} already had matching name. "
        "Search this log for “[skip ambiguous”, “[ambiguous group]”, “[skip rename error]”, "
        "“[skip keep bracket tags]”, “[skip destination exists]”.\n"
    )
    return result, lines, dup_rows


def main() -> None:
    """CLI entry: uses module-level SOURCE_DIR / TARGET_DIR / DRY_RUN / REQUIRE_PARTIAL_HASH."""
    res, lines, _dup_rows = sync_target_names_from_source(
        SOURCE_DIR,
        TARGET_DIR,
        dry_run=DRY_RUN,
        use_partial_hash=REQUIRE_PARTIAL_HASH,
        hash_bytes=PARTIAL_HASH_BYTES,
        keep_target_if_bracket_tags=False,
    )
    for ln in lines:
        print(ln, end="" if ln.endswith("\n") else "\n")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
