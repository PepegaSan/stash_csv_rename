"""Tab 7 file sync: incremental update or full mirror from a source tree into a target tree."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


def _resolved(p: Path) -> Path:
    try:
        return p.expanduser().resolve(strict=False)
    except OSError:
        return p.expanduser()


def path_is_under(maybe_child: Path, root: Path) -> bool:
    """True if ``maybe_child`` is ``root`` or inside ``root``."""
    c = _resolved(maybe_child)
    r = _resolved(root)
    try:
        c.relative_to(r)
        return True
    except ValueError:
        return False


def roots_overlap_unsafe(source_root: Path, target_root: Path) -> bool:
    """True if one root lies inside the other (or they are equal) — sync would be unsafe."""
    s = _resolved(source_root)
    t = _resolved(target_root)
    if s == t:
        return True
    return path_is_under(s, t) or path_is_under(t, s)


def _is_regular_file(path: Path) -> bool:
    try:
        return path.is_file()
    except OSError:
        return False


def _unique_flat_destination(target_root: Path, source_basename: str) -> Path:
    """``target_root / name`` with numeric suffix if that path already exists."""
    p = target_root / source_basename
    if not p.exists():
        return p
    stem = Path(source_basename).stem
    suf = Path(source_basename).suffix
    n = 1
    while True:
        cand = target_root / f"{stem}_t7sync{n}{suf}"
        if not cand.exists():
            return cand
        n += 1


@dataclass(frozen=True)
class MirrorCopyRow:
    """One row for UI / logs."""

    source: str
    dest: str
    status: str


def _iter_files_under(root: Path) -> Iterable[Path]:
    root = _resolved(root)
    if not root.is_dir():
        return
    for dirpath, _dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        base = Path(dirpath)
        for name in filenames:
            p = base / name
            if _is_regular_file(p):
                yield p


def _rel_key(path: Path, root: Path) -> str | None:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return os.path.normcase(rel.as_posix())


def _file_map(root: Path) -> dict[str, Path]:
    root = _resolved(root)
    m: dict[str, Path] = {}
    for p in _iter_files_under(root):
        k = _rel_key(p, root)
        if k:
            m[k] = p
    return m


def _stats_differ(source_file: Path, target_file: Path) -> bool:
    try:
        sa, sb = source_file.stat(), target_file.stat()
        if sa.st_size != sb.st_size:
            return True
        return int(sa.st_mtime) != int(sb.st_mtime)
    except OSError:
        return True


def _try_copy_to(src: Path, dst: Path) -> bool:
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except OSError:
        return False


def run_mirror_copy(
    source_root: Path,
    target_root: Path,
    *,
    dry_run: bool,
    mode: str = "update",
) -> tuple[list[MirrorCopyRow], list[str]]:
    """
    ``mode="update"``: copy missing files and refresh files that differ (size / mtime);
    nothing is deleted on the target.

    ``mode="mirror"``: make the target file tree match the source — remove target-only
    files, copy missing files, and overwrite differing files. Deletions are not undoable.

    Raises ``ValueError`` with ``"overlap"`` or ``"not_dir"`` when the run must not proceed.

    Returns ``(rows, undo_paths)`` — ``undo_paths`` lists only **newly created** files
    from this run (safe to delete on undo), not overwrites or mirror deletions.
    """
    rows: list[MirrorCopyRow] = []
    undo: list[str] = []

    m = (mode or "update").strip().lower()
    if m not in ("update", "mirror"):
        m = "update"

    if roots_overlap_unsafe(source_root, target_root):
        raise ValueError("overlap")

    src = _resolved(source_root)
    tgt = _resolved(target_root)
    if not src.is_dir() or not tgt.is_dir():
        raise ValueError("not_dir")

    src_map = _file_map(src)
    tgt_work: dict[str, Path] = _file_map(tgt)

    if m == "mirror":
        for rel, tp in sorted(tgt_work.items(), key=lambda x: x[0], reverse=True):
            if rel in src_map:
                continue
            if dry_run:
                rows.append(MirrorCopyRow("", str(tp), "dry_delete"))
            else:
                try:
                    tp.unlink()
                    rows.append(MirrorCopyRow("", str(tp), "deleted"))
                except OSError:
                    rows.append(MirrorCopyRow("", str(tp), "error_delete"))
            del tgt_work[rel]

    for rel, sp in sorted(src_map.items(), key=lambda x: x[0]):
        tp = tgt_work.get(rel)
        if tp is None:
            try:
                ideal = tgt / sp.relative_to(src)
            except ValueError:
                continue
            conflict = ideal.exists() and not _is_regular_file(ideal)
            if dry_run:
                if conflict:
                    flat = _unique_flat_destination(tgt, sp.name)
                    rows.append(MirrorCopyRow(str(sp), str(flat), "dry_fallback"))
                else:
                    rows.append(MirrorCopyRow(str(sp), str(ideal), "dry_mirror"))
                continue

            dest: Path | None = None
            status = "error"
            if not conflict:
                was_new = not _is_regular_file(ideal)
                if _try_copy_to(sp, ideal):
                    dest = ideal
                    status = "copied"
                    if was_new:
                        undo.append(str(dest))
            if dest is None:
                flat = _unique_flat_destination(tgt, sp.name)
                was_new = not _is_regular_file(flat)
                if _try_copy_to(sp, flat):
                    dest = flat
                    status = "copied_fallback"
                    if was_new:
                        undo.append(str(dest))
                else:
                    rows.append(MirrorCopyRow(str(sp), str(ideal if not conflict else flat), "error"))
                    continue
            rows.append(MirrorCopyRow(str(sp), str(dest), status))
        else:
            if not _stats_differ(sp, tp):
                continue
            if dry_run:
                rows.append(MirrorCopyRow(str(sp), str(tp), "dry_update"))
            else:
                if _try_copy_to(sp, tp):
                    rows.append(MirrorCopyRow(str(sp), str(tp), "copied_update"))
                else:
                    rows.append(MirrorCopyRow(str(sp), str(tp), "error_update"))

    return rows, undo


def delete_copied_files(paths: list[str]) -> tuple[int, list[tuple[str, str]]]:
    """Delete files created by a sync run; returns ``(deleted_count, [(path, err), ...])``."""
    fails: list[tuple[str, str]] = []
    n = 0
    for p in reversed(paths):
        fp = Path(p)
        try:
            if fp.is_file():
                fp.unlink()
                n += 1
        except OSError as e:
            fails.append((p, str(e)))
    return n, fails
