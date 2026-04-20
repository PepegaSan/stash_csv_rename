#!/usr/bin/env python3
"""CustomTkinter: Tab1 Stash CSV, Tab2 disk scan, Tab3 rename, Tab4 move, Tab5 schema rename."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from tkinter import Menu, TclError, filedialog, ttk
from urllib.parse import urljoin

import customtkinter as ctk

from i18n import SUPPORTED_LANGS, Translator

from theme_palette import PALETTE_DARK, PALETTE_LIGHT

from file_rename_tools import (
    append_schema_tags_to_leaf,
    apply_file_renames,
    undo_file_renames,
    disambiguate_new_leaves_among_rows,
    apply_find_replace_to_rows,
    apply_prefix_suffix_to_rows,
    build_leaf_tags_only_mode,
    build_schema_rename_leaf,
    compose_ui_list_filter,
    merge_extra_bracket_tags_into_leaf,
    merge_schema_metadata_into_append_leaf,
    strip_non_auto_bracket_tags_from_leaf,
    ffprobe_paths_parallel,
    ffprobe_video_size,
    filter_stub_for_subfolder_suggest,
    find_ffprobe_executable,
    leaf_extension_from_row,
    move_files_only,
    read_rename_csv,
    rehydrate_leaf_stem_head_from_schema_row,
    row_passes_list_filters,
    rename_folder_dangerous,
    resolve_csv_path_to_existing_file,
    resolve_move_destination_root,
    sanitize_windows_dir_component,
    scan_folder_files,
    probe_stash_csv_export_schema,
    test_stash_graphql_connection,
    truncate_leaf_stem_to_max_chars,
    unique_leaf_in_dir,
    write_rename_csv,
)

def _app_dir() -> Path:
    """Folder next to the app for writable files (settings, presets, CSV output)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _resource_dir() -> Path:
    """Bundled read-only assets (locales, themes, export script) — PyInstaller extract dir or dev tree."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
    return Path(__file__).resolve().parent


_APP_DIR = _app_dir()
_RES_DIR = _resource_dir()

_SETTINGS_PATH = _APP_DIR / "gui_file_tools_settings.json"
_SCHEMA_PRESETS_PATH = _APP_DIR / "schema_rename_presets.json"
_DEFAULT_STASH_PS1 = _RES_DIR / "export_stash_files.ps1"

_FILTER_FIELD_KEYS_TAB34: tuple[str, ...] = (
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
)
_FILTER_FIELD_KEYS_TAB5: tuple[str, ...] = _FILTER_FIELD_KEYS_TAB34 + ("proposed",)

# Tk event.state modifier bits (not in tkinter.constants on some Python 3.12 builds).
_TK_SHIFT_MASK = 0x0001
_TK_CONTROL_MASK = 0x0004
# Large Treeview fills: insert in chunks so the UI stays responsive with thousands of rows.
_TTK_TREE_INSERT_BATCH = 350
# Each successful Tab 3/4/5 disk batch appends one undo entry; oldest batches drop past this cap.
_RENAME_UNDO_MAX_BATCHES = 32

# Deepfake-style chrome (see theme_palette.py).
BTN_RADIUS = 10
FONT_BTN = ("Segoe UI Black", 10)
FONT_APP_TITLE = ("Segoe UI Black", 18)
FONT_BTN_NAV = ("Segoe UI Semibold", 10)
FONT_UI = ("Segoe UI", 14)
FONT_UI_SM = ("Segoe UI", 12)
FONT_SECTION = ("Segoe UI Semibold", 15)
FONT_HINT = ("Segoe UI", 11)

BTN_HEIGHT_COMPACT = 36

def _load_customtkinter_theme() -> None:
    ctk.set_default_color_theme("blue")


# Row / toolbar buttons — same height as Deepfake_smoother browse / actions.
_BTN_H = BTN_HEIGHT_COMPACT

# After last keystroke in list filters, wait before rebuilding large treeviews (smoother typing).
_FILTER_TYPING_DEBOUNCE_MS = 520
# Tab 5: tag slot / title max text — debounced tree refresh (separate from list filters).
_T5_SCHEMA_TYPING_DEBOUNCE_MS = 360

def _btn_w(s: str, *, lo: int = 40, hi: int = 420) -> int:
    return max(lo, min(hi, int(len(s) * 6.8 + 22)))


def _default_file_tools_csv_dir() -> Path:
    d = _APP_DIR / "file_tools_csv"
    d.mkdir(parents=True, exist_ok=True)
    return d


class FileToolsApp(ctk.CTk):
    def __init__(self) -> None:
        _load_customtkinter_theme()
        super().__init__(fg_color=PALETTE_DARK["bg"])
        self._pal: dict[str, str] = dict(PALETTE_DARK)
        self.title("Stashmarker — file list & rename")
        self.geometry("1180x960")
        self.minsize(920, 640)
        self._nav_key = "t1"

        self._rows: list[dict[str, str]] = []
        self._last_shared_csv = ""

        # Tab 1
        self._t1_ps1 = ctk.StringVar(value=str(_DEFAULT_STASH_PS1) if _DEFAULT_STASH_PS1.is_file() else "")
        self._t1_url = ctk.StringVar(value="http://127.0.0.1:9999")
        self._t1_graphql_path = ctk.StringVar(value="")
        self._t1_api = ctk.StringVar(value=os.environ.get("STASH_API_KEY", ""))
        self._t1_out = ctk.StringVar(value=str(_default_file_tools_csv_dir() / "stash_files.csv"))
        self._t1_delim = ctk.StringVar(value=";")
        self._t1_per_page = ctk.StringVar(value="500")
        self._t1_path_prefix = ctk.StringVar(value="")
        self._t1_path_contains = ctk.StringVar(value="")
        self._t1_name_contains = ctk.StringVar(value="")
        self._t1_name_regex = ctk.StringVar(value="")

        # Tab 2
        self._t2_folder = ctk.StringVar(value="")
        self._t2_recursive = ctk.BooleanVar(value=True)
        self._t2_patterns = ctk.StringVar(value="")  # e.g. *.mp4;*.mkv
        self._t2_out = ctk.StringVar(value=str(_default_file_tools_csv_dir() / "disk_scan.csv"))

        # Tab 3
        self._t3_csv = ctk.StringVar(value="")
        self._t3_filter = ctk.StringVar(value="")
        self._t3_filter_exclude = ctk.StringVar(value="")
        self._t3_filter_field = ctk.StringVar(value="all")
        self._t3_filter_combine = ctk.StringVar(value="and")
        self._t3_filter_exclude_field = ctk.StringVar(value="all")
        self._t3_filter_exclude_combine = ctk.StringVar(value="and")
        self._t3_only_under = ctk.StringVar(value="")
        self._t3_prefix = ctk.StringVar(value="")
        self._t3_suffix = ctk.StringVar(value="")
        self._t3_find = ctk.StringVar(value="")
        self._t3_replace = ctk.StringVar(value="")
        self._t3_replace_ci = ctk.BooleanVar(value=False)
        self._t3_dry = ctk.BooleanVar(value=True)
        self._t3_rename_selected_only = ctk.BooleanVar(value=False)
        self._t3_edit_leaf = ctk.StringVar(value="")

        # Folder rename (dangerous)
        self._t3_fold_src = ctk.StringVar(value="")
        self._t3_fold_new = ctk.StringVar(value="")
        self._t3_fold_confirm = ctk.BooleanVar(value=False)
        self._t3_filter_after_id: str | None = None

        # Tab 4
        self._t4_rows: list[dict[str, str]] = []
        self._t4_csv = ctk.StringVar(value=str(_default_file_tools_csv_dir() / "stash_files.csv"))
        self._t4_filter = ctk.StringVar(value="")
        self._t4_filter_exclude = ctk.StringVar(value="")
        self._t4_filter_field = ctk.StringVar(value="all")
        self._t4_filter_combine = ctk.StringVar(value="and")
        self._t4_filter_exclude_field = ctk.StringVar(value="all")
        self._t4_filter_exclude_combine = ctk.StringVar(value="and")
        self._t4_target_folder = ctk.StringVar(value="")
        self._t4_dry = ctk.BooleanVar(value=True)
        self._t4_subfolder = ctk.StringVar(value="")
        self._t4_per_source = ctk.BooleanVar(value=False)
        self._t4_use_selected = ctk.BooleanVar(value=False)
        self._t4_preview_scheduled = False
        self._t4_after_id: str | None = None
        self._t4_filter_ui_after_id: str | None = None
        self._t4_trace_ids: list[tuple[ctk.Variable, str]] = []
        self._t5_trace_ids: list[tuple[ctk.Variable, str]] = []
        self._tree_b1_drag_state: dict[int, dict[str, object]] = {}

        # Tab 5 — schema rename (title + year + tags + ffprobe resolution + rating)
        self._t5_rows: list[dict[str, str]] = []
        self._t5_csv = ctk.StringVar(value=str(_default_file_tools_csv_dir() / "stash_files.csv"))
        self._t5_filter = ctk.StringVar(value="")
        self._t5_filter_exclude = ctk.StringVar(value="")
        self._t5_filter_field = ctk.StringVar(value="all")
        self._t5_filter_combine = ctk.StringVar(value="and")
        self._t5_filter_exclude_field = ctk.StringVar(value="all")
        self._t5_filter_exclude_combine = ctk.StringVar(value="and")
        self._t5_title_max = ctk.StringVar(value="15")
        self._t5_include_year = ctk.BooleanVar(value=True)
        self._t5_include_resolution = ctk.BooleanVar(value=True)
        self._t5_include_rating = ctk.BooleanVar(value=True)
        self._t5_dry = ctk.BooleanVar(value=True)
        self._t5_use_selected = ctk.BooleanVar(value=False)
        self._t5_name_mode = ctk.StringVar(value="full_schema")
        self._t5_preserve_tags_on_shorten = ctk.BooleanVar(value=False)
        self._t5_title_max_entry: ctk.CTkEntry | None = None
        self._t5_full_schema_only_widgets: list[object] = []
        self._t5_tag_en = [ctk.BooleanVar(value=False) for _ in range(5)]
        self._t5_tag_txt = [ctk.StringVar(value="") for _ in range(5)]
        self._t5_preset_name = ctk.StringVar(value="")
        self._t5_preset_pick = ctk.StringVar(value="\u2014")  # same as t5.preset_none in all locales
        self._t5_ffprobe_cache: dict[str, tuple[int | None, int | None]] = {}
        self._t5_probe_busy = False
        self._t5_preset_menu: ctk.CTkOptionMenu | None = None
        self._t5_rebuild_after_id: str | None = None
        self._rename_undo_batches: list[tuple[str, list[tuple[int, str, str, str]]]] = []
        self._header_undo_btn: ctk.CTkButton | None = None
        self._t3_sort_col = "path"
        self._t3_sort_desc = False
        self._t4_sort_col = "path"
        self._t4_sort_desc = False
        self._t5_sort_col = "path"
        self._t5_sort_desc = False

        self._appearance_mode = ctk.StringVar(value="dark")
        self._ui_language = ctk.StringVar(value="en")
        self._settings_dialog: ctk.CTkToplevel | None = None
        self._t5_help_dialog: ctk.CTkToplevel | None = None
        self._work_status = ctk.StringVar(value="")
        self._t1_export_busy = False
        self._t2_scan_busy = False
        self._btn_t1_export: ctk.CTkButton | None = None
        self._btn_t2_scan: ctk.CTkButton | None = None
        self._btn_t5_probe: ctk.CTkButton | None = None
        self._log_collapsed = ctk.BooleanVar(value=False)
        self._log_toggle_btn: ctk.CTkButton | None = None

        self._load_settings()
        self._ensure_bundled_export_ps1_path()
        self._sync_palette_from_appearance()
        self._translator = Translator(_RES_DIR / "locales", self._norm_lang_code(self._ui_language.get()))
        self.title(self._tr("app.window_title"))
        self._build_ui()
        self.configure(fg_color=self._pal["bg"])
        self._apply_user_appearance_setting()
        self._apply_ttk_treeview_style()
        self._install_t4_traces()
        self._install_t5_traces()
        self.after_idle(self._t4_refresh_preview)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    @staticmethod
    def _norm_lang_code(raw: str) -> str:
        c = (raw or "en").strip().lower()
        return c if c in SUPPORTED_LANGS else "en"

    def _tr(self, key: str, **kwargs: object) -> str:
        return self._translator.tr(key, **kwargs)

    def _rebuild_all_tab_variables(self) -> None:
        """New Variable instances after destroying the UI.

        CustomTkinter registers write traces on StringVar/BooleanVar from CTkEntry/CTkCheckBox.
        Reusing the same Python Variable across rebuilds can leave stale Tcl callbacks; a second
        language swap then triggers _textvariable_callback on destroyed entries.
        """
        self._t1_ps1 = ctk.StringVar(value=self._t1_ps1.get())
        self._t1_url = ctk.StringVar(value=self._t1_url.get())
        self._t1_graphql_path = ctk.StringVar(value=self._t1_graphql_path.get())
        self._t1_api = ctk.StringVar(value=self._t1_api.get())
        self._t1_out = ctk.StringVar(value=self._t1_out.get())
        self._t1_per_page = ctk.StringVar(value=self._t1_per_page.get())
        self._t1_path_prefix = ctk.StringVar(value=self._t1_path_prefix.get())
        self._t1_path_contains = ctk.StringVar(value=self._t1_path_contains.get())
        self._t1_name_contains = ctk.StringVar(value=self._t1_name_contains.get())
        self._t1_name_regex = ctk.StringVar(value=self._t1_name_regex.get())

        self._t2_folder = ctk.StringVar(value=self._t2_folder.get())
        self._t2_recursive = ctk.BooleanVar(value=self._t2_recursive.get())
        self._t2_patterns = ctk.StringVar(value=self._t2_patterns.get())
        self._t2_out = ctk.StringVar(value=self._t2_out.get())

        self._t3_csv = ctk.StringVar(value=self._t3_csv.get())
        self._t3_filter = ctk.StringVar(value=self._t3_filter.get())
        self._t3_filter_exclude = ctk.StringVar(value=self._t3_filter_exclude.get())
        self._t3_filter_field = ctk.StringVar(value=self._t3_filter_field.get())
        self._t3_filter_combine = ctk.StringVar(value=self._t3_filter_combine.get())
        self._t3_filter_exclude_field = ctk.StringVar(value=self._t3_filter_exclude_field.get())
        self._t3_filter_exclude_combine = ctk.StringVar(value=self._t3_filter_exclude_combine.get())
        self._t3_only_under = ctk.StringVar(value=self._t3_only_under.get())
        self._t3_prefix = ctk.StringVar(value=self._t3_prefix.get())
        self._t3_suffix = ctk.StringVar(value=self._t3_suffix.get())
        self._t3_find = ctk.StringVar(value=self._t3_find.get())
        self._t3_replace = ctk.StringVar(value=self._t3_replace.get())
        self._t3_replace_ci = ctk.BooleanVar(value=self._t3_replace_ci.get())
        self._t3_dry = ctk.BooleanVar(value=self._t3_dry.get())
        self._t3_rename_selected_only = ctk.BooleanVar(value=self._t3_rename_selected_only.get())
        self._t3_edit_leaf = ctk.StringVar(value=self._t3_edit_leaf.get())
        self._t3_fold_src = ctk.StringVar(value=self._t3_fold_src.get())
        self._t3_fold_new = ctk.StringVar(value=self._t3_fold_new.get())
        self._t3_fold_confirm = ctk.BooleanVar(value=self._t3_fold_confirm.get())

        self._t4_csv = ctk.StringVar(value=self._t4_csv.get())
        self._t4_filter = ctk.StringVar(value=self._t4_filter.get())
        self._t4_filter_exclude = ctk.StringVar(value=self._t4_filter_exclude.get())
        self._t4_filter_field = ctk.StringVar(value=self._t4_filter_field.get())
        self._t4_filter_combine = ctk.StringVar(value=self._t4_filter_combine.get())
        self._t4_filter_exclude_field = ctk.StringVar(value=self._t4_filter_exclude_field.get())
        self._t4_filter_exclude_combine = ctk.StringVar(value=self._t4_filter_exclude_combine.get())
        self._t4_target_folder = ctk.StringVar(value=self._t4_target_folder.get())
        self._t4_subfolder = ctk.StringVar(value=self._t4_subfolder.get())
        self._t4_dry = ctk.BooleanVar(value=self._t4_dry.get())
        self._t4_per_source = ctk.BooleanVar(value=self._t4_per_source.get())
        self._t4_use_selected = ctk.BooleanVar(value=self._t4_use_selected.get())

        self._t5_csv = ctk.StringVar(value=self._t5_csv.get())
        self._t5_filter = ctk.StringVar(value=self._t5_filter.get())
        self._t5_filter_exclude = ctk.StringVar(value=self._t5_filter_exclude.get())
        self._t5_filter_field = ctk.StringVar(value=self._t5_filter_field.get())
        self._t5_filter_combine = ctk.StringVar(value=self._t5_filter_combine.get())
        self._t5_filter_exclude_field = ctk.StringVar(value=self._t5_filter_exclude_field.get())
        self._t5_filter_exclude_combine = ctk.StringVar(value=self._t5_filter_exclude_combine.get())
        self._t5_title_max = ctk.StringVar(value=self._t5_title_max.get())
        self._t5_include_year = ctk.BooleanVar(value=self._t5_include_year.get())
        self._t5_include_resolution = ctk.BooleanVar(value=self._t5_include_resolution.get())
        self._t5_include_rating = ctk.BooleanVar(value=self._t5_include_rating.get())
        self._t5_dry = ctk.BooleanVar(value=self._t5_dry.get())
        self._t5_use_selected = ctk.BooleanVar(value=self._t5_use_selected.get())
        self._t5_name_mode = ctk.StringVar(value=self._t5_name_mode.get())
        self._t5_preserve_tags_on_shorten = ctk.BooleanVar(value=self._t5_preserve_tags_on_shorten.get())
        self._t5_tag_en = [ctk.BooleanVar(value=self._t5_tag_en[i].get()) for i in range(5)]
        self._t5_tag_txt = [ctk.StringVar(value=self._t5_tag_txt[i].get()) for i in range(5)]
        self._t5_preset_name = ctk.StringVar(value=self._t5_preset_name.get())
        self._t5_preset_pick = ctk.StringVar(value=self._t5_preset_pick.get())
        self._log_collapsed = ctk.BooleanVar(value=self._log_collapsed.get())

    def _remove_t4_traces(self) -> None:
        for v, tid in self._t4_trace_ids:
            try:
                v.trace_remove("write", tid)
            except (ValueError, TclError):
                pass
        self._t4_trace_ids.clear()

    def _install_t4_traces(self) -> None:
        self._remove_t4_traces()

        def cb_filter_typing(*_a: object) -> None:
            self._t4_schedule_filter_ui_update()

        def cb_immediate(*_a: object) -> None:
            self._t4_rebuild_tree()
            self._t4_schedule_preview_refresh()

        for v in (
            self._t4_filter,
            self._t4_filter_exclude,
            self._t4_filter_field,
            self._t4_filter_combine,
            self._t4_filter_exclude_field,
            self._t4_filter_exclude_combine,
        ):
            self._t4_trace_ids.append((v, v.trace_add("write", cb_filter_typing)))
        for v in (
            self._t4_target_folder,
            self._t4_subfolder,
            self._t4_per_source,
            self._t4_use_selected,
            self._t4_dry,
        ):
            self._t4_trace_ids.append((v, v.trace_add("write", cb_immediate)))

    def _t5_shorten_scope_effective(self) -> str:
        """``title_only`` = shorten head before trailing ``[…]``; ``full_stem`` = cap whole stem."""
        return "title_only" if self._t5_preserve_tags_on_shorten.get() else "full_stem"

    def _t5_name_mode_effective(self) -> str:
        m = (self._t5_name_mode.get() or "full_schema").strip().lower()
        if m == "tags_overwrite":
            return "tags_replace_except_auto"
        if m in ("tags_append", "tags_replace_except_auto"):
            return m
        return "full_schema"

    def _t5_in_tags_mode(self) -> bool:
        return self._t5_name_mode_effective() in ("tags_append", "tags_replace_except_auto")

    def _t5_tags_replace_except_auto(self) -> bool:
        """Replace non-auto ``[…]`` + slot tags; keep year / resolution / rating literals from the file."""
        return self._t5_name_mode_effective() == "tags_replace_except_auto"

    def _t5_on_name_mode_change(self, *_a: object) -> None:
        self._t5_apply_mode_dependent_ui_state()
        self._t5_on_schema_preview_change()

    def _t5_apply_mode_dependent_ui_state(self) -> None:
        """Reserved for widgets that should depend on name mode (currently none)."""
        for w in self._t5_full_schema_only_widgets:
            try:
                if int(w.winfo_exists()):
                    w.configure(state="normal")
            except TclError:
                pass

    def _cancel_t5_tree_rebuild_after(self) -> None:
        aid = self._t5_rebuild_after_id
        if aid is not None:
            try:
                self.after_cancel(aid)
            except (TclError, ValueError):
                pass
            self._t5_rebuild_after_id = None

    def _t5_schedule_rebuild_tree(self, *, delay_ms: int | None = None) -> None:
        """Debounce full tree rebuild — tag text / title traces fire on every keystroke."""
        self._cancel_t5_tree_rebuild_after()
        ms = _T5_SCHEMA_TYPING_DEBOUNCE_MS if delay_ms is None else delay_ms
        self._t5_rebuild_after_id = self.after(ms, self._t5_run_scheduled_tree_rebuild)

    def _t5_run_scheduled_tree_rebuild(self) -> None:
        self._t5_rebuild_after_id = None
        if not self._t5_try_refresh_tree_leaves_only():
            self._t5_rebuild_tree()

    def _remove_t5_traces(self) -> None:
        self._cancel_t5_tree_rebuild_after()
        for v, tid in self._t5_trace_ids:
            try:
                v.trace_remove("write", tid)
            except (ValueError, TclError):
                pass
        self._t5_trace_ids.clear()

    def _install_t5_traces(self) -> None:
        """Refresh Tab 5 preview when schema options (tags, title length, …) change."""
        self._remove_t5_traces()
        cb_filter = lambda *_: self._t5_schedule_rebuild_tree(delay_ms=_FILTER_TYPING_DEBOUNCE_MS)
        cb_schema_leaf = lambda *_: self._t5_on_schema_preview_change()
        cb_tag_text = lambda *_: self._t5_schedule_rebuild_tree()
        for i in range(5):
            self._t5_trace_ids.append(
                (self._t5_tag_en[i], self._t5_tag_en[i].trace_add("write", cb_schema_leaf)),
            )
            self._t5_trace_ids.append((self._t5_tag_txt[i], self._t5_tag_txt[i].trace_add("write", cb_tag_text)))
        for v in (
            self._t5_filter,
            self._t5_filter_exclude,
            self._t5_filter_field,
            self._t5_filter_combine,
            self._t5_filter_exclude_field,
            self._t5_filter_exclude_combine,
        ):
            self._t5_trace_ids.append((v, v.trace_add("write", cb_filter)))
        self._t5_trace_ids.append((self._t5_title_max, self._t5_title_max.trace_add("write", cb_tag_text)))
        self._t5_trace_ids.append(
            (self._t5_name_mode, self._t5_name_mode.trace_add("write", self._t5_on_name_mode_change)),
        )
        self._t5_trace_ids.append(
            (self._t5_preserve_tags_on_shorten, self._t5_preserve_tags_on_shorten.trace_add("write", cb_schema_leaf)),
        )
        for v in (
            self._t5_include_year,
            self._t5_include_resolution,
            self._t5_include_rating,
        ):
            self._t5_trace_ids.append((v, v.trace_add("write", cb_schema_leaf)))

    def _cancel_t3_filter_rebuild_after(self) -> None:
        aid = self._t3_filter_after_id
        if aid is not None:
            try:
                self.after_cancel(aid)
            except (TclError, ValueError):
                pass
            self._t3_filter_after_id = None

    def _schedule_t3_filter_rebuild(self) -> None:
        """Debounce Tab 3 tree while typing in search / exclude filters."""
        self._cancel_t3_filter_rebuild_after()
        self._t3_filter_after_id = self.after(_FILTER_TYPING_DEBOUNCE_MS, self._t3_run_scheduled_filter_rebuild)

    def _t3_run_scheduled_filter_rebuild(self) -> None:
        self._t3_filter_after_id = None
        self._t3_rebuild_tree()

    def _cancel_t4_filter_ui_after(self) -> None:
        aid = self._t4_filter_ui_after_id
        if aid is not None:
            try:
                self.after_cancel(aid)
            except (TclError, ValueError):
                pass
            self._t4_filter_ui_after_id = None

    def _t4_schedule_filter_ui_update(self) -> None:
        """Debounce Tab 4 tree + move preview while typing filters or paths."""
        self._cancel_t4_filter_ui_after()
        self._t4_filter_ui_after_id = self.after(_FILTER_TYPING_DEBOUNCE_MS, self._t4_run_scheduled_filter_ui_update)

    def _t4_run_scheduled_filter_ui_update(self) -> None:
        self._t4_filter_ui_after_id = None
        self._t4_rebuild_tree()
        self._t4_schedule_preview_refresh()

    def _cancel_t4_preview_after(self) -> None:
        self._t4_preview_scheduled = False
        aid = self._t4_after_id
        if aid is not None:
            try:
                self.after_cancel(aid)
            except (TclError, ValueError):
                pass
            self._t4_after_id = None

    def _rebuild_main_ui(self) -> None:
        self._sync_palette_from_appearance()
        self._cancel_t3_filter_rebuild_after()
        self._cancel_t4_filter_ui_after()
        self._remove_t4_traces()
        self._remove_t5_traces()
        self._cancel_t4_preview_after()
        self._settings_dialog = None
        self._t5_help_dialog = None
        try:
            self.update_idletasks()
        except TclError:
            pass
        for w in list(self.winfo_children()):
            w.destroy()
        try:
            self.update()
        except TclError:
            pass
        self._rebuild_all_tab_variables()
        self._translator.set_lang(self._norm_lang_code(self._ui_language.get()))
        self.title(self._tr("app.window_title"))
        self._build_ui()
        self.configure(fg_color=self._pal["bg"])
        self._apply_user_appearance_setting()
        self._apply_ttk_treeview_style()
        self._install_t4_traces()
        self._install_t5_traces()
        self._t3_rebuild_tree()
        self._t4_rebuild_tree()
        self._t4_refresh_preview()
        self._t5_rebuild_tree()

    def _apply_user_appearance_setting(self) -> None:
        """Apply dark/light/system from saved settings (do not name this _apply_appearance_mode — CTk uses that)."""
        m = (self._appearance_mode.get() or "dark").strip().lower()
        if m not in ("dark", "light", "system"):
            m = "dark"
        ctk.set_appearance_mode(m)

    def _sync_palette_from_appearance(self) -> None:
        """Custom chrome palette: light only when appearance is Light; dark chrome for Dark and System."""
        m = (self._appearance_mode.get() or "dark").strip().lower()
        self._pal = dict(PALETTE_LIGHT if m == "light" else PALETTE_DARK)

    def _entry_kw(self) -> dict:
        p = self._pal
        return dict(
            height=36,
            corner_radius=8,
            border_width=1,
            fg_color=p["panel_elev"],
            border_color=p["border"],
            text_color=p["text"],
            font=FONT_UI,
            placeholder_text_color=p["muted"],
        )

    def _option_kw(self) -> dict:
        p = self._pal
        return dict(
            height=34,
            corner_radius=8,
            fg_color=p["panel_elev"],
            button_color=p["cyan_dim"],
            button_hover_color=p["cyan"],
            font=FONT_UI_SM,
            text_color=p["text"],
            dropdown_fg_color=p["panel"],
            dropdown_hover_color=p["panel_elev"],
            dropdown_text_color=p["text"],
        )

    def _button_kw(self, variant: str = "ghost", *, height: int = 40, font: tuple | None = None, width: int | None = None) -> dict:
        font = font or FONT_BTN
        p = self._pal
        kw: dict = dict(
            corner_radius=BTN_RADIUS,
            font=font,
            height=height,
            border_width=2,
            border_color=p["btn_rim"],
        )
        if width is not None:
            kw["width"] = width
        if variant == "ghost":
            kw.update(
                fg_color=p["panel_elev"],
                hover_color=p["border"],
                text_color=p["text"],
            )
        elif variant == "primary":
            kw.update(
                fg_color=p["cyan_dim"],
                hover_color=p["cyan"],
                text_color=p["text"],
                border_color=p["primary_border"],
            )
        elif variant == "primary_emphasis":
            kw.update(
                fg_color=p["cyan_dim"],
                hover_color=p["cyan"],
                text_color=p["text"],
                border_color=p["primary_border"],
                font=("Segoe UI Black", 11),
            )
        elif variant == "success":
            kw.update(
                fg_color="#1b5e20",
                hover_color="#2e7d32",
                text_color="#f0f0f8",
                border_color="#041208",
            )
        elif variant == "gold":
            kw.update(
                fg_color=p["gold_dim"],
                hover_color=p["gold"],
                text_color=p["text"],
                border_color="#1f1804",
            )
        elif variant == "nav_idle":
            kw.update(
                fg_color=p["panel_elev"],
                hover_color=p["border"],
                text_color=p["muted"],
                font=FONT_BTN_NAV,
            )
        elif variant == "nav_active":
            kw.update(
                fg_color=p["cyan_dim"],
                hover_color=p["cyan"],
                text_color=p["text"],
                border_color=p["cyan"],
                font=("Segoe UI Black", 10),
            )
        elif variant == "danger_soft":
            kw.update(
                fg_color="#8b1e1e",
                hover_color="#5f1212",
                text_color="#f0f0f8",
                border_color="#140404",
            )
        return kw

    def _gear_button_kw(self, *, variant: str = "ghost", height: int = 40) -> dict:
        kw = self._button_kw(variant, height=height)
        kw["width"] = 44
        kw["font"] = ("Segoe UI Semibold", 20)
        return kw

    def _checkbox_kw(self, **extra: object) -> dict:
        p = self._pal
        d: dict = dict(
            checkbox_width=22,
            checkbox_height=22,
            font=FONT_UI_SM,
            text_color=p["text"],
            fg_color=p["cyan_dim"],
            hover_color=p["cyan"],
            border_color=p["border"],
        )
        d.update(extra)
        return d

    def _radio_kw(self) -> dict:
        p = self._pal
        return dict(
            font=FONT_UI_SM,
            text_color=p["text"],
            fg_color=p["cyan_dim"],
            hover_color=p["cyan"],
            border_color=p["border"],
        )

    def _label(self, master: ctk.CTkFrame | ctk.CTkScrollableFrame | ctk.CTkTabview | ctk.CTk | ctk.CTkToplevel, **kwargs) -> ctk.CTkLabel:
        kwargs.setdefault("fg_color", self._pal["panel"])
        kwargs.setdefault("text_color", self._pal["text"])
        return ctk.CTkLabel(master, **kwargs)

    def _nav_button(self, text: str, key: str) -> ctk.CTkButton:
        btn = ctk.CTkButton(
            self.frame_sidebar,
            text=text,
            anchor="w",
            command=lambda k=key: self.select_panel(k),
            **self._button_kw("nav_idle", height=44),
        )
        btn.pack(fill="x", padx=10, pady=5)
        return btn

    def select_panel(self, key: str) -> None:
        self._nav_key = key
        for k, fr in self.panels.items():
            fr.grid_remove()
        self.panels[key].grid(row=0, column=0, sticky="nsew")
        for k, btn in self.nav_buttons.items():
            btn.configure(**self._button_kw("nav_active" if k == key else "nav_idle", height=44))

    def _apply_ttk_treeview_style(self) -> None:
        """ttk.Treeview ignores CTk theme; match light vs dark so lists stay readable."""
        style = ttk.Style()
        try:
            style.theme_use("clam")
            if str(ctk.get_appearance_mode()).lower() == "light":
                style.configure(
                    "Treeview",
                    background="#ffffff",
                    foreground="#1a1a1a",
                    fieldbackground="#ffffff",
                    rowheight=22,
                )
                style.configure("Treeview.Heading", background="#d0d0d0", foreground="#1a1a1a")
                style.configure(
                    "Vertical.TScrollbar",
                    background="#c4c4c4",
                    troughcolor="#e8e8e8",
                    arrowcolor="#1a1a1a",
                )
                style.configure(
                    "Horizontal.TScrollbar",
                    background="#c4c4c4",
                    troughcolor="#e8e8e8",
                    arrowcolor="#1a1a1a",
                )
            else:
                style.configure(
                    "Treeview",
                    background="#2b2b2b",
                    foreground="#dce4ee",
                    fieldbackground="#2b2b2b",
                    rowheight=22,
                )
                style.configure("Treeview.Heading", background="#3d3d3d", foreground="#e8e8e8")
                style.map("Treeview.Heading", background=[("active", "#4a4a4a")])
                style.configure(
                    "Vertical.TScrollbar",
                    background="#3d3d3d",
                    troughcolor="#2b2b2b",
                    arrowcolor="#dce4ee",
                )
                style.configure(
                    "Horizontal.TScrollbar",
                    background="#3d3d3d",
                    troughcolor="#2b2b2b",
                    arrowcolor="#dce4ee",
                )
        except Exception:
            pass

    def _bind_ttk_tree_mousewheel(self, tree: ttk.Treeview) -> None:
        """Wheel over the list scrolls the tree, not the outer CTkScrollableFrame tab body."""

        def on_wheel(event) -> str:
            delta = getattr(event, "delta", 0) or 0
            if sys.platform == "darwin":
                tree.yview_scroll(int(-1 * delta), "units")
            else:
                tree.yview_scroll(int(-1 * (delta / 120)), "units")
            return "break"

        def on_linux_up(_event) -> str:
            tree.yview_scroll(-1, "units")
            return "break"

        def on_linux_down(_event) -> str:
            tree.yview_scroll(1, "units")
            return "break"

        tree.bind("<MouseWheel>", on_wheel)
        tree.bind("<Button-4>", on_linux_up)
        tree.bind("<Button-5>", on_linux_down)

    def _install_tree_drag_range_select(self, tree: ttk.Treeview) -> None:
        """Click-drag to select a contiguous row block; drag past top/bottom edge auto-scrolls the list.

        Ctrl/Shift+click keep the default Treeview extended selection behaviour.
        """
        tid = id(tree)
        edge = 22
        repeat_ms = 55

        def cancel_auto_scroll() -> None:
            st = self._tree_b1_drag_state.get(tid)
            if not st:
                return
            aid = st.pop("auto_scroll_id", None)
            if aid is not None:
                try:
                    self.after_cancel(aid)
                except (TclError, ValueError):
                    pass

        def apply_range(anchor: str, cur: str) -> None:
            if not anchor or not cur:
                return
            children = tree.get_children("")
            try:
                ia = children.index(anchor)
                ib = children.index(cur)
            except ValueError:
                return
            lo, hi = min(ia, ib), max(ia, ib)
            block = children[lo : hi + 1]
            if not block:
                return
            tree.selection_set(block[0])
            for x in block[1:]:
                tree.selection_add(x)

        def auto_tick() -> None:
            st = self._tree_b1_drag_state.get(tid)
            if not st or not st.get("down"):
                cancel_auto_scroll()
                return
            st["auto_scroll_id"] = None
            if not tree.get_children(""):
                cancel_auto_scroll()
                return
            anchor = (st.get("anchor") or "").strip()
            if not anchor:
                return
            state = int(st.get("last_state", 0))
            if (state & _TK_CONTROL_MASK) or (state & _TK_SHIFT_MASK):
                return
            py = tree.winfo_pointery()
            yh = max(tree.winfo_height(), edge * 2 + 4)
            if py < edge:
                tree.yview_scroll(-1, "units")
            elif py > yh - edge:
                tree.yview_scroll(1, "units")
            cur = tree.identify_row(py)
            if not cur:
                cur = tree.identify_row(min(max(edge, py), yh - edge - 1))
            if cur:
                apply_range(anchor, cur)
            if st.get("down") and anchor and (py < edge or py > yh - edge):
                st["auto_scroll_id"] = self.after(repeat_ms, auto_tick)

        def on_press(event: object) -> None:
            cancel_auto_scroll()
            y = getattr(event, "y", 0)
            row_id = tree.identify_row(y)
            self._tree_b1_drag_state[tid] = {
                "anchor": row_id or "",
                "down": True,
                "last_state": int(getattr(event, "state", 0)),
            }

        def on_motion(event: object) -> None:
            st = self._tree_b1_drag_state.get(tid)
            if not st or not st.get("down"):
                return
            state = int(getattr(event, "state", 0))
            st["last_state"] = state
            if (state & _TK_CONTROL_MASK) or (state & _TK_SHIFT_MASK):
                cancel_auto_scroll()
                return
            anchor = (st.get("anchor") or "").strip()
            if not anchor:
                return
            y = getattr(event, "y", 0)
            yh = max(tree.winfo_height(), edge * 2 + 4)
            cur = tree.identify_row(y)
            if not cur:
                if y < edge:
                    tree.yview_scroll(-1, "units")
                    cur = tree.identify_row(edge)
                elif y > yh - edge:
                    tree.yview_scroll(1, "units")
                    cur = tree.identify_row(yh - edge - 1)
            if cur:
                apply_range(anchor, cur)
            if y < edge or y > yh - edge:
                if not st.get("auto_scroll_id"):
                    st["auto_scroll_id"] = self.after(repeat_ms, auto_tick)
            else:
                cancel_auto_scroll()

        def on_release(_event: object) -> None:
            cancel_auto_scroll()
            st = self._tree_b1_drag_state.get(tid)
            if st:
                st["down"] = False

        tree.bind("<ButtonPress-1>", on_press, add="+")
        tree.bind("<B1-Motion>", on_motion, add="+")
        tree.bind("<ButtonRelease-1>", on_release, add="+")

    def _ttk_restore_row_selection(self, tree: ttk.Treeview, indices: list[int]) -> None:
        """Re-apply selection after Treeview rows were deleted/rebuilt (same iids = row indices)."""
        if not indices:
            return
        want = {str(i) for i in indices}
        have = [c for c in tree.get_children() if c in want]
        if not have:
            return
        tree.selection_set(have[0])
        for c in have[1:]:
            tree.selection_add(c)

    def _place_ttk_tree_with_scrollbars(self, tree_frame: ctk.CTkFrame, tree: ttk.Treeview) -> None:
        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        self._bind_ttk_tree_mousewheel(tree)
        self._install_tree_drag_range_select(tree)

    def _log(self, msg: str) -> None:
        self._log_box.configure(state="normal")
        self._log_box.insert("end", msg)
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _log_many_lines(self, lines: list[str]) -> None:
        """Append many log lines in one shot (avoids thousands of Text scroll updates)."""
        if not lines:
            return
        if len(lines) <= 12:
            for ln in lines:
                self._log(ln if ln.endswith("\n") else ln + "\n")
            return
        blob = "".join(ln if ln.endswith("\n") else ln + "\n" for ln in lines)
        self._log_box.configure(state="normal")
        self._log_box.insert("end", blob)
        self._log_box.see("end")
        self._log_box.configure(state="disabled")
        try:
            self.update_idletasks()
        except TclError:
            pass

    def _clear_work_progress(self) -> None:
        self._work_status.set("")

    def _work_progress_rename(self, cur: int, total: int) -> None:
        if total <= 0:
            self._clear_work_progress()
            return
        self._work_status.set(self._tr("common.progress_rename", cur=cur, total=total))

    def _work_progress_move(self, cur: int, total: int) -> None:
        if total <= 0:
            self._clear_work_progress()
            return
        self._work_status.set(self._tr("common.progress_move", cur=cur, total=total))

    def _work_progress_fill(self, cur: int, total: int) -> None:
        if total <= 0:
            self._clear_work_progress()
            return
        self._work_status.set(self._tr("common.progress_fill", cur=cur, total=total))

    def _work_progress_probe(self, cur: int, total: int) -> None:
        if total <= 0:
            self._clear_work_progress()
            return
        self._work_status.set(self._tr("common.progress_probe", cur=cur, total=total))

    def _tk_keepalive(self, step: int) -> None:
        """Pump Tk events during long work so Windows does not show 'Not responding'."""
        if step % 100 == 0:
            try:
                self.update()
            except TclError:
                pass
        elif step % 25 == 0:
            try:
                self.update_idletasks()
            except TclError:
                pass

    def _ttk_tree_replace_rows(
        self,
        tree: ttk.Treeview,
        rows_out: list[tuple[str, tuple[object, ...]]],
        *,
        batch: int = _TTK_TREE_INSERT_BATCH,
    ) -> None:
        ch = tree.get_children()
        if ch:
            tree.delete(*ch)
        n = len(rows_out)
        if n == 0:
            return
        step = 0
        for start in range(0, n, max(1, batch)):
            for iid, vals in rows_out[start : start + batch]:
                tree.insert("", "end", iid=iid, values=vals)
                step += 1
                if step % 400 == 0:
                    try:
                        self.update_idletasks()
                    except TclError:
                        pass
        try:
            self.update_idletasks()
        except TclError:
            pass

    def _app_csv_delim(self) -> str:
        """Semicolon or comma between CSV columns when saving. Opening a file auto-detects ; vs ,."""
        d = self._t1_delim.get().strip()
        return d if d in (";", ",") else ";"

    def _save_log_to_file(self) -> None:
        self._log_box.configure(state="normal")
        text = self._log_box.get("1.0", "end")
        self._log_box.configure(state="disabled")
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")],
            title=self._tr("dlg.save_log"),
        )
        if not path:
            return
        try:
            Path(path).write_text(text, encoding="utf-8")
            self._log(self._tr("log.saved_log_to", path=path))
        except OSError as e:
            self._log(self._tr("log.save_log_failed", e=e))

    def _clear_log(self) -> None:
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    def _sync_log_toggle_btn(self) -> None:
        b = self._log_toggle_btn
        if b is None or not int(b.winfo_exists()):
            return
        b.configure(
            text=self._tr("common.log_expand") if self._log_collapsed.get() else self._tr("common.log_collapse")
        )

    def _apply_log_panel_collapsed(self) -> None:
        if not hasattr(self, "_log_f"):
            return
        self._sync_log_toggle_btn()
        if self._log_collapsed.get():
            try:
                self._log_box.grid_remove()
            except TclError:
                pass
            self._log_f.grid_rowconfigure(1, weight=0, minsize=0)
            self.grid_rowconfigure(3, weight=0, minsize=0)
        else:
            self._log_box.grid(row=1, column=0, sticky="nsew")
            self._log_f.grid_rowconfigure(1, weight=1)
            self.grid_rowconfigure(3, weight=1)

    def _toggle_log_panel(self) -> None:
        self._log_collapsed.set(not self._log_collapsed.get())
        self._apply_log_panel_collapsed()
        self._save_settings()

    def _sync_header_undo_button(self) -> None:
        ok = bool(self._rename_undo_batches)
        b = self._header_undo_btn
        if b is None:
            return
        try:
            if int(b.winfo_exists()) == 0:
                return
        except TclError:
            return
        b.configure(state="normal" if ok else "disabled")

    def _register_rename_undo_stack(self, tab: str, stack: list[tuple[int, str, str, str]]) -> None:
        if not stack:
            self._sync_header_undo_button()
            return
        self._rename_undo_batches.append((tab, list(stack)))
        over = len(self._rename_undo_batches) - _RENAME_UNDO_MAX_BATCHES
        if over > 0:
            del self._rename_undo_batches[:over]
            self._log(self._tr("log.undo_stack_trimmed", n=over, max=_RENAME_UNDO_MAX_BATCHES))
        self._sync_header_undo_button()

    def _undo_last_disk_rename(self) -> None:
        if not self._rename_undo_batches:
            self._log(self._tr("log.undo_rename_nothing"))
            return
        tab, recs = self._rename_undo_batches[-1]
        if tab == "t3":
            rows = self._rows
            dry = self._t3_dry.get()
        elif tab == "t4":
            rows = self._t4_rows
            dry = self._t4_dry.get()
        else:
            rows = self._t5_rows
            dry = self._t5_dry.get()
        n, lines = undo_file_renames(
            recs,
            rows,
            dry_run=dry,
            keep_alive=self._tk_keepalive,
            keep_alive_every=35,
        )
        self._log_many_lines(lines)
        if dry:
            self._log(self._tr("log.undo_rename_done_preview", n=len(recs)))
        else:
            self._log(self._tr("log.undo_rename_done", n=n))
            self._rename_undo_batches.pop()
            if tab == "t3":
                self._t3_rebuild_tree()
            elif tab == "t4":
                self._t4_rebuild_tree()
                self._t4_refresh_preview()
            else:
                self._t5_rebuild_tree()
            self._save_settings()
            self._sync_header_undo_button()
            m = len(self._rename_undo_batches)
            if m:
                self._log(self._tr("log.undo_rename_more_available", m=m))

    def _on_save_gui_settings_click(self) -> None:
        self._save_settings()
        self._log(self._tr("settings.saved_log"))

    def _build_ui(self) -> None:
        self._browse_w = max(88, _btn_w(self._tr("common.browse")))
        p = self._pal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=2)
        self.grid_rowconfigure(3, weight=1)

        self.frame_top = ctk.CTkFrame(self, fg_color=p["panel"], corner_radius=0, height=56)
        self.frame_top.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.frame_top.grid_columnconfigure(1, weight=1)
        self.frame_top.grid_propagate(False)

        self.lbl_app_title = ctk.CTkLabel(
            self.frame_top,
            text=self._tr("app.brand"),
            font=FONT_APP_TITLE,
            text_color=p["text"],
            fg_color="transparent",
        )
        self.lbl_app_title.grid(row=0, column=0, padx=(20, 12), pady=12, sticky="w")

        self._work_status_lbl = ctk.CTkLabel(
            self.frame_top,
            textvariable=self._work_status,
            anchor="w",
            font=FONT_UI,
            text_color=p["muted"],
            fg_color="transparent",
        )
        self._work_status_lbl.grid(row=0, column=1, sticky="ew", padx=8, pady=12)

        self._header_undo_btn = ctk.CTkButton(
            self.frame_top,
            text=self._tr("common.undo_header"),
            command=self._undo_last_disk_rename,
            width=max(118, _btn_w(self._tr("common.undo_header"))),
            state="disabled",
            **self._button_kw("gold", height=40),
        )
        self._header_undo_btn.grid(row=0, column=2, padx=(8, 6), pady=8, sticky="e")

        self.btn_settings = ctk.CTkButton(
            self.frame_top,
            text="\u2699",
            command=self._open_settings_dialog,
            **self._gear_button_kw(variant="primary_emphasis", height=_BTN_H),
        )
        self.btn_settings.grid(row=0, column=3, padx=(8, 20), pady=8, sticky="e")

        self.frame_body = ctk.CTkFrame(self, fg_color=p["bg"])
        self.frame_body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(10, 6))
        self.frame_body.grid_columnconfigure(1, weight=1)
        self.frame_body.grid_rowconfigure(0, weight=1)

        self.frame_sidebar = ctk.CTkFrame(
            self.frame_body,
            width=216,
            fg_color=p["panel"],
            corner_radius=14,
            border_width=1,
            border_color=p["border"],
        )
        self.frame_sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 12), pady=0)
        self.frame_sidebar.grid_propagate(False)

        self.frame_content = ctk.CTkFrame(
            self.frame_body,
            fg_color=p["panel"],
            corner_radius=14,
            border_width=1,
            border_color=p["border"],
        )
        self.frame_content.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.frame_content.grid_rowconfigure(0, weight=1)
        self.frame_content.grid_columnconfigure(0, weight=1)

        def _mk_scroll_panel() -> ctk.CTkScrollableFrame:
            return ctk.CTkScrollableFrame(
                self.frame_content,
                fg_color=p["panel"],
                corner_radius=0,
                scrollbar_fg_color=p["panel_elev"],
                scrollbar_button_color=p["border"],
                scrollbar_button_hover_color=p["cyan_dim"],
            )

        self.panel_t1 = _mk_scroll_panel()
        self.panel_t2 = _mk_scroll_panel()
        self.panel_t3 = _mk_scroll_panel()
        self.panel_t4 = _mk_scroll_panel()
        self.panel_t5 = _mk_scroll_panel()
        self.panels = {
            "t1": self.panel_t1,
            "t2": self.panel_t2,
            "t3": self.panel_t3,
            "t4": self.panel_t4,
            "t5": self.panel_t5,
        }
        for pan in self.panels.values():
            pan.grid_columnconfigure(0, weight=1)

        self.nav_buttons = {}
        for text, key in (
            (self._tr("tab.1"), "t1"),
            (self._tr("tab.2"), "t2"),
            (self._tr("tab.3"), "t3"),
            (self._tr("tab.4"), "t4"),
            (self._tr("tab.5"), "t5"),
        ):
            self.nav_buttons[key] = self._nav_button(text, key)

        self._build_tab1(self.panel_t1)
        self._build_tab2(self.panel_t2)
        self._build_tab3(self.panel_t3)
        self._build_tab4(self.panel_t4)
        self._build_tab5(self.panel_t5)

        for fr in self.panels.values():
            fr.grid(row=0, column=0, sticky="nsew")
            fr.grid_remove()
        self.select_panel(self._nav_key)

        self.frame_bottom = ctk.CTkFrame(
            self,
            fg_color=p["panel"],
            corner_radius=12,
            border_width=1,
            border_color=p["border"],
        )
        self.frame_bottom.grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 6))
        ctk.CTkButton(
            self.frame_bottom,
            text=f"\U0001f4be {self._tr('common.save')}",
            command=self._on_save_gui_settings_click,
            **self._button_kw("success", height=42),
        ).pack(side="left", padx=12, pady=12)

        self._log_f = ctk.CTkFrame(self, fg_color=p["bg"])
        self._log_f.grid(row=3, column=0, sticky="nsew", padx=14, pady=(0, 12))
        self._log_f.grid_rowconfigure(1, weight=1)
        self._log_f.grid_columnconfigure(0, weight=1)
        log_top = ctk.CTkFrame(
            self._log_f, fg_color=p["panel"], corner_radius=8, border_width=1, border_color=p["border"]
        )
        log_top.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self._label(log_top, text=self._tr("common.log"), anchor="w", fg_color="transparent").pack(
            side="left", padx=10, pady=6
        )
        self._log_toggle_btn = ctk.CTkButton(
            log_top,
            text=self._tr("common.log_collapse"),
            width=max(96, _btn_w(self._tr("common.log_collapse"))),
            command=self._toggle_log_panel,
            **self._button_kw("ghost", height=_BTN_H),
        )
        self._log_toggle_btn.pack(side="left", padx=(0, 8), pady=6)
        ctk.CTkButton(
            log_top,
            text=self._tr("common.save_log"),
            width=_btn_w(self._tr("common.save_log")),
            command=self._save_log_to_file,
            **self._button_kw("ghost", height=_BTN_H),
        ).pack(side="right", padx=(8, 10), pady=6)
        ctk.CTkButton(
            log_top,
            text=self._tr("common.clear_log"),
            width=_btn_w(self._tr("common.clear_log")),
            command=self._clear_log,
            **self._button_kw("ghost", height=_BTN_H),
        ).pack(side="right", pady=6)
        self._log_box = ctk.CTkTextbox(
            self._log_f,
            height=200,
            activate_scrollbars=True,
            font=("Consolas", 12),
            fg_color=p["panel_elev"],
            border_color=p["border"],
            text_color=p["text"],
        )
        self._log_box.grid(row=1, column=0, sticky="nsew")
        self._log_box.configure(state="disabled")
        self._apply_log_panel_collapsed()
        self._sync_header_undo_button()

    def _pad(self) -> dict:
        return {"padx": 10, "pady": (4, 6)}

    def _ph_string_entry(
        self,
        master: ctk.CTkFrame,
        var: ctk.StringVar,
        *,
        placeholder: str,
        height: int = 28,
        width: int | None = None,
        after_push: object | None = None,
    ) -> ctk.CTkEntry:
        """
        CTkEntry placeholder + StringVar: CustomTkinter 5.2.x never activates placeholder when
        ``textvariable`` is set (buggy check ``textvariable == ''``). Do not pass textvariable;
        sync via bind + trace instead.
        """
        kw: dict = {
            "placeholder_text": placeholder,
            "placeholder_text_color": self._pal["muted"],
            "height": height,
        }
        if width is not None:
            kw["width"] = width
        ent = ctk.CTkEntry(master, **kw)
        if var.get():
            ent.insert(0, var.get())

        def push(_evt: object | None = None) -> None:
            var.set(ent.get())
            if after_push is not None:
                after_push()

        ent.bind("<KeyRelease>", push)
        ent.bind("<FocusOut>", push)
        ent.bind("<<Paste>>", push)
        ent.bind("<<Cut>>", push)

        def pull(_a: str = "", _b: str = "", _c: str = "") -> None:
            val = var.get()
            if val == ent.get():
                return
            ent.delete(0, "end")
            if val:
                ent.insert(0, val)

        var.trace_add("write", pull)
        return ent

    def _collapsible_section(
        self,
        parent: ctk.CTkFrame,
        *,
        title_key: str,
        start_open: bool,
    ) -> ctk.CTkFrame:
        """Header toggles visibility of the returned frame (pack children into it)."""
        pad = self._pad()
        outer = ctk.CTkFrame(
            parent,
            fg_color=self._pal["panel_elev"],
            corner_radius=12,
            border_width=1,
            border_color=self._pal["border"],
        )
        outer.pack(fill="x", **pad)
        open_flag = [start_open]
        title_base = self._tr(title_key)
        body = ctk.CTkFrame(outer, fg_color="transparent")
        hdr = ctk.CTkButton(
            outer,
            text="",
            anchor="w",
            **self._button_kw("ghost", height=28, font=FONT_UI_SM),
        )

        def toggle() -> None:
            open_flag[0] = not open_flag[0]
            sym = "\u25bc " if open_flag[0] else "\u25b6 "
            hdr.configure(text=f"{sym}{title_base}")
            if open_flag[0]:
                body.pack(fill="x", pady=(0, 2))
            else:
                body.pack_forget()

        hdr.configure(command=toggle)
        sym = "\u25bc " if start_open else "\u25b6 "
        hdr.configure(text=f"{sym}{title_base}")
        hdr.pack(fill="x", pady=(0, 2))
        if start_open:
            body.pack(fill="x", pady=(0, 2))
        return body

    def _build_tab1(self, parent: ctk.CTkFrame) -> None:
        pad = self._pad()
        self._label(
            parent,
            text=self._tr("t1.intro"),
            anchor="w",
            wraplength=860,
            justify="left",
        ).pack(fill="x", **pad)
        self._label(
            parent,
            text=self._tr("t1.hint_scan"),
            anchor="w",
            wraplength=860,
            justify="left",
            text_color=self._pal["muted"],
            font=FONT_HINT,
        ).pack(fill="x", padx=10, pady=(0, 4))
        self._label(
            parent,
            text=self._tr("t1.hint_connection_in_settings"),
            anchor="w",
            wraplength=860,
            justify="left",
            text_color=self._pal["muted"],
            font=FONT_HINT,
        ).pack(fill="x", padx=10, pady=(0, 6))

        csv_row = ctk.CTkFrame(parent, fg_color=self._pal["panel"], height=32)
        csv_row.pack(fill="x", padx=10, pady=(2, 4))
        csv_row.pack_propagate(False)
        self._label(csv_row, text=self._tr("t1.label.save_csv"), width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(csv_row, textvariable=self._t1_out, height=28).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        ctk.CTkButton(
            csv_row,
            text=self._tr("common.browse"),
            width=self._browse_w,
            command=self._browse_t1_out,
            **self._button_kw("ghost", height=_BTN_H),
        ).pack(side="right")

        row_batch = ctk.CTkFrame(parent, fg_color=self._pal["panel"], height=32)
        row_batch.pack(fill="x", padx=10, pady=(0, 4))
        row_batch.pack_propagate(False)
        self._label(row_batch, text=self._tr("t1.batch_size"), width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(row_batch, textvariable=self._t1_per_page, width=80, height=28).pack(side="left")

        filt_body = self._collapsible_section(parent, title_key="t1.filters_title", start_open=False)
        for key, var in (
            ("t1.path_prefix", self._t1_path_prefix),
            ("t1.path_contains", self._t1_path_contains),
            ("t1.name_contains", self._t1_name_contains),
            ("t1.name_regex", self._t1_name_regex),
        ):
            rr = ctk.CTkFrame(filt_body, fg_color=self._pal["panel"], height=30)
            rr.pack(fill="x", pady=(0, 4))
            rr.pack_propagate(False)
            self._label(rr, text=self._tr(key), width=200, anchor="w").pack(side="left")
            ctk.CTkEntry(rr, textvariable=var, height=28).pack(side="left", fill="x", expand=True)

        self._label(
            parent,
            text=self._tr("t1.section_export_actions"),
            anchor="w",
            font=FONT_SECTION,
            fg_color=self._pal["panel"],
        ).pack(fill="x", padx=10, pady=(6, 4))

        bf = ctk.CTkFrame(parent, fg_color=self._pal["panel"], height=34)
        bf.pack(fill="x", padx=10, pady=(0, 6))
        bf.pack_propagate(False)
        self._btn_t1_export = ctk.CTkButton(
            bf,
            text=self._tr("t1.run_export"),
            width=_btn_w(self._tr("t1.run_export")),
            command=self._run_t1_export,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        )
        self._btn_t1_export.pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            bf,
            text=self._tr("t1.open_out_folder"),
            width=_btn_w(self._tr("t1.open_out_folder")),
            command=self._open_t1_out_dir,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            bf,
            text=self._tr("t1.test_connection"),
            width=_btn_w(self._tr("t1.test_connection")),
            command=self._test_stash_connection,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            bf,
            text=self._tr("t1.check_csv_export"),
            width=_btn_w(self._tr("t1.check_csv_export")),
            command=self._probe_stash_csv_export,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left")

        push_hdr = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        push_hdr.pack(fill="x", padx=10, pady=(4, 2))
        self._label(push_hdr, text=self._tr("t1.send_csv_to"), anchor="w", text_color=self._pal["muted"], fg_color=self._pal["panel"]).pack(
            side="left"
        )
        push = ctk.CTkFrame(parent, fg_color=self._pal["panel"], height=34)
        push.pack(fill="x", padx=10, pady=(0, 6))
        push.pack_propagate(False)
        ctk.CTkButton(
            push,
            text=self._tr("t1.tab3_rename"),
            width=_btn_w(self._tr("t1.tab3_rename")),
            command=self._t1_push_to_tab3,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            push,
            text=self._tr("t1.tab4_move"),
            width=_btn_w(self._tr("t1.tab4_move")),
            command=self._t1_push_to_tab4,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            push,
            text=self._tr("t1.tab5_schema"),
            width=_btn_w(self._tr("t1.tab5_schema")),
            command=self._t1_push_to_tab5,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left")

    def _build_tab2(self, parent: ctk.CTkFrame) -> None:
        pad = self._pad()
        self._label(
            parent,
            text=self._tr("t2.intro"),
            anchor="w",
            wraplength=860,
            justify="left",
        ).pack(fill="x", **pad)

        r = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        r.pack(fill="x", **pad)
        self._label(r, text=self._tr("t2.folder_scan"), width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(r, textvariable=self._t2_folder).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            r, text=self._tr("common.browse"), width=self._browse_w, command=self._browse_t2_folder,
            **self._button_kw("ghost", height=_BTN_H),
        ).pack(side="right")

        ctk.CTkCheckBox(
            parent, text=self._tr("t2.recursive"), variable=self._t2_recursive, **self._checkbox_kw()
        ).pack(anchor="w", **pad)

        rr = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        rr.pack(fill="x", **pad)
        self._label(rr, text=self._tr("t2.file_types"), width=160, anchor="w").pack(side="left")
        self._ph_string_entry(
            rr,
            self._t2_patterns,
            placeholder=self._tr("t2.patterns_placeholder"),
        ).pack(side="left", fill="x", expand=True)

        ro = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        ro.pack(fill="x", **pad)
        self._label(ro, text=self._tr("t2.save_list_csv"), width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(ro, textvariable=self._t2_out).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            ro, text=self._tr("common.browse"), width=self._browse_w, command=self._browse_t2_out,
            **self._button_kw("ghost", height=_BTN_H),
        ).pack(side="right")

        bf = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        bf.pack(fill="x", **pad)
        self._btn_t2_scan = ctk.CTkButton(
            bf,
            text=self._tr("t2.run_scan"),
            width=_btn_w(self._tr("t2.run_scan")),
            command=self._run_t2_scan,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        )
        self._btn_t2_scan.pack(side="left", padx=(0, 8))
        self._label(bf, text=self._tr("t1.send_csv_to"), text_color=self._pal["muted"]).pack(side="left", padx=(8, 4))
        ctk.CTkButton(
            bf,
            text=self._tr("t1.tab3_rename"),
            width=_btn_w(self._tr("t1.tab3_rename")),
            command=self._t2_push_to_tab3,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            bf,
            text=self._tr("t1.tab4_move"),
            width=_btn_w(self._tr("t1.tab4_move")),
            command=self._t2_push_to_tab4,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            bf,
            text=self._tr("t1.tab5_schema"),
            width=_btn_w(self._tr("t1.tab5_schema")),
            command=self._t2_push_to_tab5,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left")

    def _pack_list_filter_rows(
        self,
        parent: ctk.CTkFrame,
        *,
        filter_var: ctk.StringVar,
        exclude_var: ctk.StringVar,
        inc_field: ctk.StringVar,
        inc_combine: ctk.StringVar,
        ex_field: ctk.StringVar,
        ex_combine: ctk.StringVar,
        field_keys: tuple[str, ...],
        inc_placeholder: str,
        ex_placeholder: str,
        on_change,
        use_keyrelease: bool = True,
    ) -> None:
        keys = list(field_keys)

        def clamp_field(var: ctk.StringVar) -> None:
            if var.get() not in keys:
                var.set("all")

        def clamp_combine(var: ctk.StringVar) -> None:
            if var.get() not in ("and", "or"):
                var.set("and")

        clamp_field(inc_field)
        clamp_field(ex_field)
        clamp_combine(inc_combine)
        clamp_combine(ex_combine)

        flabels = [self._tr(f"filter.field.{k}") for k in field_keys]
        c_and = self._tr("filter.combine.and")
        c_or = self._tr("filter.combine.or")
        clabels = [c_and, c_or]

        def one_row(text_var: ctk.StringVar, fv: ctk.StringVar, cv: ctk.StringVar, ph: str) -> None:
            row = ctk.CTkFrame(parent, fg_color=self._pal["panel"], height=32)
            row.pack(fill="x", padx=10, pady=(0, 4))
            row.pack_propagate(False)

            def on_field_pick(choice: str) -> None:
                fv.set(keys[flabels.index(choice)])
                on_change()

            def on_combine_pick(choice: str) -> None:
                cv.set("and" if choice == c_and else "or")
                on_change()

            mf = ctk.CTkOptionMenu(
                row,
                values=flabels,
                command=on_field_pick,
                **{**self._option_kw(), "width": 158},
            )
            mf.pack(side="left", padx=(0, 6))
            fk = fv.get()
            mf.set(flabels[keys.index(fk) if fk in keys else 0])

            mc = ctk.CTkOptionMenu(
                row,
                values=clabels,
                command=on_combine_pick,
                **{**self._option_kw(), "width": 72},
            )
            mc.pack(side="left", padx=(0, 8))
            mc.set(c_and if cv.get() == "and" else c_or)

            ent = self._ph_string_entry(
                row,
                text_var,
                placeholder=ph,
                height=28,
                after_push=on_change if use_keyrelease else None,
            )
            ent.pack(side="left", fill="x", expand=True)

        one_row(filter_var, inc_field, inc_combine, inc_placeholder)
        one_row(exclude_var, ex_field, ex_combine, ex_placeholder)

        # Placeholder text in the filter boxes explains usage; no extra hint row needed.

    def _build_tab3(self, parent: ctk.CTkFrame) -> None:
        pad = self._pad()
        self._label(
            parent,
            text=self._tr("t3.steps"),
            anchor="w",
            wraplength=860,
            justify="left",
        ).pack(fill="x", **pad)

        top = ctk.CTkFrame(parent, fg_color=self._pal["panel"], height=32)
        top.pack(fill="x", padx=10, pady=(2, 4))
        top.pack_propagate(False)
        self._label(top, text=self._tr("common.csv_file"), width=100, anchor="w").pack(side="left")
        self._ph_string_entry(
            top,
            self._t3_csv,
            placeholder=self._tr("common.ph.csv_path"),
            height=28,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            top, text=self._tr("common.browse"), width=self._browse_w, command=self._browse_t3_csv,
            **self._button_kw("ghost", height=_BTN_H),
        ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(
            top,
            text=self._tr("common.load"),
            width=_btn_w(self._tr("common.load")),
            command=self._t3_load_csv,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(
            top,
            text=self._tr("t3.save_csv"),
            width=_btn_w(self._tr("t3.save_csv")),
            command=self._t3_save_csv,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="right")

        self._label(
            parent,
            text=self._tr("t3.hint_csv"),
            anchor="w",
            text_color=self._pal["muted"],
            font=FONT_HINT,
        ).pack(fill="x", padx=10, pady=(0, 2))

        self._pack_list_filter_rows(
            parent,
            filter_var=self._t3_filter,
            exclude_var=self._t3_filter_exclude,
            inc_field=self._t3_filter_field,
            inc_combine=self._t3_filter_combine,
            ex_field=self._t3_filter_exclude_field,
            ex_combine=self._t3_filter_exclude_combine,
            field_keys=_FILTER_FIELD_KEYS_TAB34,
            inc_placeholder=self._tr("t3.filter_placeholder"),
            ex_placeholder=self._tr("common.exclude_placeholder"),
            on_change=self._schedule_t3_filter_rebuild,
        )

        batch_body = self._collapsible_section(parent, title_key="t3.section_batch_title", start_open=True)
        edit_row = ctk.CTkFrame(batch_body, fg_color=self._pal["panel"], height=32)
        edit_row.pack(fill="x", padx=10, pady=(4, 4))
        edit_row.pack_propagate(False)
        self._ph_string_entry(
            edit_row,
            self._t3_edit_leaf,
            placeholder=self._tr("t3.ph.new_leaf"),
            height=28,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            edit_row,
            text=self._tr("t3.apply_selected"),
            width=_btn_w(self._tr("t3.apply_selected")),
            command=self._t3_apply_leaf_selection,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="right")

        rule = ctk.CTkFrame(batch_body, fg_color=self._pal["panel"], height=32)
        rule.pack(fill="x", padx=10, pady=(0, 4))
        rule.pack_propagate(False)
        self._ph_string_entry(
            rule,
            self._t3_prefix,
            placeholder=self._tr("t3.ph.prefix"),
            width=140,
            height=28,
        ).pack(side="left", padx=(0, 10))
        self._ph_string_entry(
            rule,
            self._t3_suffix,
            placeholder=self._tr("t3.ph.suffix"),
            width=140,
            height=28,
        ).pack(side="left", padx=(0, 12))
        rule_btns = ctk.CTkFrame(rule, fg_color=self._pal["panel"])
        rule_btns.pack(side="left", padx=(8, 0))
        ctk.CTkButton(
            rule_btns,
            text=self._tr("t3.apply_search"),
            width=_btn_w(self._tr("t3.apply_search")),
            command=self._t3_apply_rule_filtered,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            rule_btns,
            text=self._tr("t3.apply_selected"),
            width=_btn_w(self._tr("t3.apply_selected")),
            command=self._t3_apply_rule_selected,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left")

        fr_row = ctk.CTkFrame(batch_body, fg_color=self._pal["panel"], height=32)
        fr_row.pack(fill="x", padx=10, pady=(0, 4))
        fr_row.pack_propagate(False)
        self._t3_find_entry = self._ph_string_entry(
            fr_row,
            self._t3_find,
            placeholder=self._tr("t3.ph.find"),
            width=150,
            height=28,
        )
        self._t3_find_entry.pack(side="left", padx=(0, 8))
        self._t3_replace_entry = self._ph_string_entry(
            fr_row,
            self._t3_replace,
            placeholder=self._tr("t3.ph.replace"),
            width=150,
            height=28,
        )
        self._t3_replace_entry.pack(side="left", padx=(0, 8))
        ctk.CTkCheckBox(
            fr_row,
            text=self._tr("t3.ignore_case"),
            variable=self._t3_replace_ci,
            **self._checkbox_kw(),
        ).pack(side="left", padx=(0, 8))
        fr_btns = ctk.CTkFrame(fr_row, fg_color=self._pal["panel"])
        fr_btns.pack(side="left", padx=(4, 0))
        ctk.CTkButton(
            fr_btns,
            text=self._tr("t3.fr_search"),
            width=_btn_w(self._tr("t3.fr_search")),
            command=self._t3_apply_find_replace_filtered,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            fr_btns,
            text=self._tr("t3.fr_selected"),
            width=_btn_w(self._tr("t3.fr_selected")),
            command=self._t3_apply_find_replace_selected,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left")

        ou = ctk.CTkFrame(batch_body, fg_color=self._pal["panel"], height=32)
        ou.pack(fill="x", padx=10, pady=(0, 6))
        ou.pack_propagate(False)
        self._ph_string_entry(
            ou,
            self._t3_only_under,
            placeholder=self._tr("t3.ph.only_under"),
            height=28,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            ou,
            text=self._tr("common.browse"),
            width=self._browse_w,
            command=self._browse_t3_only_under,
            **self._button_kw("ghost", height=_BTN_H),
        ).pack(side="right")

        self._label(
            parent,
            text=self._tr("t3.tree_context_hint"),
            anchor="w",
            justify="left",
            wraplength=880,
            text_color=self._pal["muted"],
            font=FONT_HINT,
        ).pack(fill="x", padx=10, pady=(0, 2))

        tree_outer = ctk.CTkFrame(
            parent,
            fg_color=self._pal["panel"],
            corner_radius=6,
            border_width=1,
            border_color=self._pal["border"],
        )
        tree_outer.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        tree_frame = ctk.CTkFrame(tree_outer, fg_color=self._pal["panel"])
        tree_frame.pack(fill="both", expand=True, padx=3, pady=3)
        self._apply_ttk_treeview_style()

        self._tree = ttk.Treeview(
            tree_frame,
            columns=("path", "path_gap", "name", "name_gap", "ext", "ext_gap", "new_leaf"),
            show="headings",
            height=14,
            selectmode="extended",
        )
        self._tree.heading("path", text=self._tr("t3.col.path"), command=lambda: self._toggle_sort_t3("path"))
        self._tree.heading("path_gap", text=self._tr("t3.col.path_gap"))
        self._tree.heading("name", text=self._tr("t3.col.name"), command=lambda: self._toggle_sort_t3("name"))
        self._tree.heading("name_gap", text=self._tr("t3.col.path_gap"))
        self._tree.heading("ext", text=self._tr("t3.col.ext"), command=lambda: self._toggle_sort_t3("ext"))
        self._tree.heading("ext_gap", text=self._tr("t3.col.path_gap"))
        self._tree.heading(
            "new_leaf", text=self._tr("t3.col.new_leaf"), command=lambda: self._toggle_sort_t3("new_leaf")
        )
        self._tree.column("path", width=300, minwidth=80, stretch=False, anchor="w")
        self._tree.column("path_gap", width=16, minwidth=12, stretch=False, anchor="center")
        self._tree.column("name", width=220, minwidth=70, stretch=False, anchor="w")
        self._tree.column("name_gap", width=16, minwidth=12, stretch=False, anchor="center")
        self._tree.column("ext", width=72, minwidth=52, stretch=False, anchor="w")
        self._tree.column("ext_gap", width=16, minwidth=12, stretch=False, anchor="center")
        self._tree.column("new_leaf", width=280, minwidth=80, stretch=False, anchor="w")
        self._place_ttk_tree_with_scrollbars(tree_frame, self._tree)
        self._tree.bind("<<TreeviewSelect>>", self._t3_on_select)
        self._tree.bind("<Double-1>", lambda e: self._t3_focus_edit_leaf())
        self._tree.bind("<Button-3>", self._t3_tree_context_menu)

        runf = ctk.CTkFrame(parent, fg_color=self._pal["panel"], height=40)
        runf.pack(fill="x", padx=10, pady=(0, 6))
        runf.pack_propagate(False)
        ctk.CTkCheckBox(
            runf, text=self._tr("t3.preview_only"), variable=self._t3_dry, **self._checkbox_kw()
        ).pack(side="left", padx=(0, 12))
        ctk.CTkCheckBox(
            runf,
            text=self._tr("t3.rename_selected_only"),
            variable=self._t3_rename_selected_only,
            **self._checkbox_kw(),
        ).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            runf,
            text=self._tr("t3.rename_disk"),
            width=_btn_w(self._tr("t3.rename_disk")),
            command=self._t3_run_renames,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            runf,
            text=self._tr("t3.clear_new_names"),
            width=_btn_w(self._tr("t3.clear_new_names")),
            command=self._t3_clear_filtered_leaves,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left")

        fold_body = self._collapsible_section(parent, title_key="t3.section_folder_title", start_open=False)
        warn_fr = ctk.CTkFrame(fold_body, fg_color=("#8b3a3a", "#5c1f1f"), corner_radius=8)
        warn_fr.pack(fill="x", **pad)
        self._label(
            warn_fr,
            text=self._tr("t3.folder_warn"),
            text_color=("#fff", "#ffcccc"),
            anchor="w",
            justify="left",
            fg_color="transparent",
        ).pack(fill="x", padx=10, pady=8)

        fr = ctk.CTkFrame(warn_fr, fg_color="transparent")
        fr.pack(fill="x", padx=10, pady=(0, 10))
        self._label(fr, text=self._tr("common.folder"), width=80, anchor="w", fg_color="transparent").pack(side="left")
        self._ph_string_entry(
            fr,
            self._t3_fold_src,
            placeholder=self._tr("t3.ph.fold_src"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            fr, text=self._tr("common.browse"), width=self._browse_w, command=self._browse_t3_fold_src,
            **self._button_kw("ghost", height=_BTN_H),
        ).pack(side="right")

        fr2 = ctk.CTkFrame(warn_fr, fg_color="transparent")
        fr2.pack(fill="x", padx=10, pady=(0, 10))
        self._label(fr2, text=self._tr("common.new_name"), width=80, anchor="w", fg_color="transparent").pack(side="left")
        self._ph_string_entry(
            fr2,
            self._t3_fold_new,
            placeholder=self._tr("t3.fold_new_placeholder"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkCheckBox(
            warn_fr,
            text=self._tr("t3.fold_confirm"),
            variable=self._t3_fold_confirm,
            **self._checkbox_kw(text_color=("#fff", "#eee")),
        ).pack(anchor="w", padx=10, pady=(0, 6))

        ctk.CTkButton(
            warn_fr,
            text=self._tr("t3.fold_rename_btn"),
            width=_btn_w(self._tr("t3.fold_rename_btn")),
            command=self._t3_run_folder_rename,
            **self._button_kw("danger_soft", height=_BTN_H),
        ).pack(anchor="w", padx=10, pady=(0, 10))

    def _build_tab4(self, parent: ctk.CTkFrame) -> None:
        pad = self._pad()
        self._label(
            parent,
            text=self._tr("t4.intro_block"),
            anchor="w",
            wraplength=860,
            justify="left",
            text_color=self._pal["muted"],
            font=FONT_HINT,
        ).pack(fill="x", **pad)

        top4 = ctk.CTkFrame(parent, fg_color=self._pal["panel"], height=32)
        top4.pack(fill="x", padx=10, pady=(2, 4))
        top4.pack_propagate(False)
        self._label(top4, text=self._tr("common.csv_file"), width=100, anchor="w").pack(side="left")
        self._ph_string_entry(
            top4,
            self._t4_csv,
            placeholder=self._tr("common.ph.csv_path"),
            height=28,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            top4, text=self._tr("common.browse"), width=self._browse_w, command=self._browse_t4_csv,
            **self._button_kw("ghost", height=_BTN_H),
        ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(
            top4,
            text=self._tr("common.load"),
            width=_btn_w(self._tr("common.load")),
            command=self._t4_load_csv,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(
            top4,
            text=self._tr("t4.export_csv"),
            width=_btn_w(self._tr("t4.export_csv")),
            command=self._t4_export_csv,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="right")

        self._pack_list_filter_rows(
            parent,
            filter_var=self._t4_filter,
            exclude_var=self._t4_filter_exclude,
            inc_field=self._t4_filter_field,
            inc_combine=self._t4_filter_combine,
            ex_field=self._t4_filter_exclude_field,
            ex_combine=self._t4_filter_exclude_combine,
            field_keys=_FILTER_FIELD_KEYS_TAB34,
            inc_placeholder=self._tr("t3.filter_placeholder"),
            ex_placeholder=self._tr("common.exclude_placeholder"),
            on_change=self._t4_schedule_filter_ui_update,
            use_keyrelease=False,
        )

        tree_outer4 = ctk.CTkFrame(
            parent,
            fg_color=self._pal["panel"],
            corner_radius=6,
            border_width=1,
            border_color=self._pal["border"],
        )
        tree_outer4.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        tree_frame = ctk.CTkFrame(tree_outer4, fg_color=self._pal["panel"])
        tree_frame.pack(fill="both", expand=True, padx=3, pady=3)
        self._apply_ttk_treeview_style()
        self._t4_tree = ttk.Treeview(
            tree_frame,
            columns=("path", "path_gap", "name", "name_gap", "scene_id"),
            show="headings",
            height=10,
            selectmode="extended",
        )
        self._t4_tree.heading("path", text=self._tr("t3.col.path"), command=lambda: self._toggle_sort_t4("path"))
        self._t4_tree.heading("path_gap", text=self._tr("t3.col.path_gap"))
        self._t4_tree.heading("name", text=self._tr("t3.col.name"), command=lambda: self._toggle_sort_t4("name"))
        self._t4_tree.heading("name_gap", text=self._tr("t3.col.path_gap"))
        self._t4_tree.heading(
            "scene_id", text=self._tr("t4.col.scene_id"), command=lambda: self._toggle_sort_t4("scene_id")
        )
        self._t4_tree.column("path", width=360, minwidth=80, stretch=False, anchor="w")
        self._t4_tree.column("path_gap", width=16, minwidth=12, stretch=False, anchor="center")
        self._t4_tree.column("name", width=200, minwidth=80, stretch=False, anchor="w")
        self._t4_tree.column("name_gap", width=16, minwidth=12, stretch=False, anchor="center")
        self._t4_tree.column("scene_id", width=120, minwidth=60, stretch=False, anchor="w")
        self._place_ttk_tree_with_scrollbars(tree_frame, self._t4_tree)
        self._t4_tree.bind("<Button-3>", self._t4_tree_context_menu)

        self._t4_stats = self._label(
            parent,
            text=self._tr("t4.stats_empty"),
            anchor="w",
            text_color=self._pal["muted"],
            font=FONT_HINT,
        )
        self._t4_stats.pack(fill="x", padx=10, pady=(0, 4))

        tf = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        tf.pack(fill="x", **pad)
        self._label(tf, text=self._tr("t4.where_move"), width=200, anchor="w").pack(side="left")
        self._ph_string_entry(
            tf,
            self._t4_target_folder,
            placeholder=self._tr("t4.where_placeholder"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            tf,
            text=self._tr("t4.target_from_row"),
            width=_btn_w(self._tr("t4.target_from_row")),
            command=self._t4_set_target_from_selected_row_folder,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            tf,
            text=self._tr("common.browse"),
            width=self._browse_w,
            command=self._browse_t4_target_folder,
            **self._button_kw("ghost", height=_BTN_H),
        ).pack(side="right")

        sf = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        sf.pack(fill="x", **pad)
        self._label(sf, text=self._tr("t4.subfolder_label"), width=200, anchor="w").pack(side="left")
        self._ph_string_entry(
            sf,
            self._t4_subfolder,
            placeholder=self._tr("t4.sub_placeholder"),
        ).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            sf,
            text=self._tr("t4.suggest"),
            width=_btn_w(self._tr("t4.suggest")),
            command=self._t4_suggest_target_from_filtered,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="right", padx=(8, 0))

        path_tips_body = self._collapsible_section(
            parent, title_key="t4.section_path_tips_title", start_open=False
        )
        self._label(
            path_tips_body,
            text=self._tr("t4.move_hint"),
            anchor="w",
            wraplength=860,
            justify="left",
            text_color=self._pal["muted"],
            font=FONT_HINT,
        ).pack(fill="x", **pad)

        mf = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        mf.pack(fill="x", **pad)
        ctk.CTkCheckBox(
            mf,
            text=self._tr("t4.per_source"),
            variable=self._t4_per_source,
            **self._checkbox_kw(),
        ).pack(side="left")

        runf = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        runf.pack(fill="x", **pad)
        ctk.CTkCheckBox(
            runf,
            text=self._tr("t4.preview_only"),
            variable=self._t4_dry,
            **self._checkbox_kw(),
        ).pack(side="left", padx=(0, 12))
        ctk.CTkCheckBox(
            runf,
            text=self._tr("t4.selected_only"),
            variable=self._t4_use_selected,
            **self._checkbox_kw(),
        ).pack(side="left", padx=(0, 12))

        b = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        b.pack(fill="x", **pad)
        ctk.CTkButton(
            b,
            text=self._tr("t4.move_disk"),
            width=_btn_w(self._tr("t4.move_disk")),
            command=self._t4_execute_move,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left")
        self._t4_plan = self._label(
            b,
            text=self._tr("t4.plan_empty"),
            anchor="w",
            text_color=self._pal["muted"],
            font=FONT_HINT,
        )
        self._t4_plan.pack(side="left", padx=(12, 0))

        preview_body = self._collapsible_section(
            parent, title_key="t4.preview_section_title", start_open=True
        )
        pv_btns = ctk.CTkFrame(preview_body, fg_color=self._pal["panel"])
        pv_btns.pack(fill="x", **pad)
        ctk.CTkButton(
            pv_btns,
            text=self._tr("t4.refresh_preview"),
            width=_btn_w(self._tr("t4.refresh_preview")),
            command=self._t4_refresh_preview,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left")
        self._t4_preview = ctk.CTkTextbox(preview_body, height=130, activate_scrollbars=True)
        self._t4_preview.pack(fill="both", expand=False, **pad)
        self._t4_preview.configure(state="disabled")

    def _build_tab5(self, parent: ctk.CTkFrame) -> None:
        pad = self._pad()
        top = ctk.CTkFrame(parent, fg_color=self._pal["panel"], height=32)
        top.pack(fill="x", padx=10, pady=(2, 4))
        top.pack_propagate(False)
        self._label(top, text=self._tr("common.csv_file"), width=100, anchor="w").pack(side="left")
        self._ph_string_entry(
            top,
            self._t5_csv,
            placeholder=self._tr("common.ph.csv_path"),
            height=28,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            top, text=self._tr("common.browse"), width=self._browse_w, command=self._browse_t5_csv,
            **self._button_kw("ghost", height=_BTN_H),
        ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(
            top,
            text=self._tr("common.load"),
            width=_btn_w(self._tr("common.load")),
            command=self._t5_load_csv,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(
            top,
            text=self._tr("t3.save_csv"),
            width=_btn_w(self._tr("t3.save_csv")),
            command=self._t5_save_csv,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="right")

        self._pack_list_filter_rows(
            parent,
            filter_var=self._t5_filter,
            exclude_var=self._t5_filter_exclude,
            inc_field=self._t5_filter_field,
            inc_combine=self._t5_filter_combine,
            ex_field=self._t5_filter_exclude_field,
            ex_combine=self._t5_filter_exclude_combine,
            field_keys=_FILTER_FIELD_KEYS_TAB5,
            inc_placeholder=self._tr("t3.filter_placeholder"),
            ex_placeholder=self._tr("common.exclude_placeholder"),
            on_change=lambda: self._t5_schedule_rebuild_tree(delay_ms=_FILTER_TYPING_DEBOUNCE_MS),
            use_keyrelease=False,
        )

        self._label(
            parent,
            text=self._tr("t5.selection_hint"),
            anchor="w",
            justify="left",
            wraplength=880,
            text_color=self._pal["muted"],
            font=FONT_HINT,
        ).pack(fill="x", padx=10, pady=(0, 4))

        tree_outer5 = ctk.CTkFrame(
            parent,
            fg_color=self._pal["panel"],
            corner_radius=6,
            border_width=1,
            border_color=self._pal["border"],
        )
        tree_outer5.pack(fill="x", expand=False, padx=10, pady=(0, 2))
        tree_frame = ctk.CTkFrame(tree_outer5, fg_color=self._pal["panel"])
        tree_frame.pack(fill="x", expand=False, padx=3, pady=3)
        self._apply_ttk_treeview_style()
        self._t5_tree = ttk.Treeview(
            tree_frame,
            columns=(
                "path",
                "path_gap",
                "file_name",
                "name_gap",
                "proposed",
                "scene_id",
                "scene_tags",
                "scene_markers",
                "scene_date",
            ),
            show="headings",
            height=11,
            selectmode="extended",
        )
        self._t5_tree.heading("path", text=self._tr("t3.col.path"), command=lambda: self._toggle_sort_t5("path"))
        self._t5_tree.heading("path_gap", text=self._tr("t3.col.path_gap"))
        self._t5_tree.heading(
            "file_name", text=self._tr("t3.col.name"), command=lambda: self._toggle_sort_t5("file_name")
        )
        self._t5_tree.heading("name_gap", text=self._tr("t3.col.path_gap"))
        self._t5_tree.heading(
            "proposed", text=self._tr("t5.col.proposed"), command=lambda: self._toggle_sort_t5("proposed")
        )
        self._t5_tree.heading(
            "scene_id", text=self._tr("t5.col.scene_id"), command=lambda: self._toggle_sort_t5("scene_id")
        )
        self._t5_tree.heading(
            "scene_tags", text=self._tr("t5.col.scene_tags"), command=lambda: self._toggle_sort_t5("scene_tags")
        )
        self._t5_tree.heading(
            "scene_markers",
            text=self._tr("t5.col.scene_markers"),
            command=lambda: self._toggle_sort_t5("scene_markers"),
        )
        self._t5_tree.heading(
            "scene_date", text=self._tr("t5.col.scene_date"), command=lambda: self._toggle_sort_t5("scene_date")
        )
        self._t5_tree.column("path", width=160, minwidth=60, stretch=False, anchor="w")
        self._t5_tree.column("path_gap", width=16, minwidth=12, stretch=False, anchor="center")
        self._t5_tree.column("file_name", width=260, minwidth=70, stretch=False, anchor="w")
        self._t5_tree.column("name_gap", width=16, minwidth=12, stretch=False, anchor="center")
        self._t5_tree.column("proposed", width=300, minwidth=100, stretch=False, anchor="w")
        self._t5_tree.column("scene_id", width=100, minwidth=56, stretch=False, anchor="w")
        self._t5_tree.column("scene_tags", width=80, minwidth=44, stretch=False, anchor="w")
        self._t5_tree.column("scene_markers", width=80, minwidth=44, stretch=False, anchor="w")
        self._t5_tree.column("scene_date", width=64, minwidth=44, stretch=False, anchor="w")
        self._place_ttk_tree_with_scrollbars(tree_frame, self._t5_tree)
        # Do not stretch the tree vertically inside the frame (avoids a tall empty band under Tab 5).
        tree_frame.grid_rowconfigure(0, weight=0)
        self._t5_tree.bind("<Button-3>", self._t5_tree_context_menu)

        self._t5_full_schema_only_widgets = []
        self._t5_title_max_entry = None

        t5_help_row = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        t5_help_row.pack(fill="x", padx=10, pady=(0, 2), anchor="w")
        ctk.CTkButton(
            t5_help_row,
            text="\u2139",
            command=self._open_t5_schema_help_dialog,
            **self._button_kw("ghost", height=28, width=36, font=("Segoe UI Semibold", 15)),
        ).pack(side="left", anchor="w")

        title_fr = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        title_fr.pack(fill="x", padx=10, pady=(0, 2))
        title_top = ctk.CTkFrame(title_fr, fg_color=self._pal["panel"])
        title_top.pack(fill="x")
        self._label(title_top, text=self._tr("t5.title_max"), width=160, anchor="w").pack(side="left", padx=(0, 6))
        self._t5_title_max_entry = ctk.CTkEntry(title_top, textvariable=self._t5_title_max, width=56)
        self._t5_title_max_entry.pack(side="left", padx=(0, 12))

        schema_mode_fr = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        schema_mode_fr.pack(fill="x", padx=10, pady=(0, 0))
        schema_mode_row = ctk.CTkFrame(schema_mode_fr, fg_color=self._pal["panel"])
        schema_mode_row.pack(fill="x")
        ctk.CTkRadioButton(
            schema_mode_row,
            text=self._tr("t5.name_mode.full_schema"),
            variable=self._t5_name_mode,
            value="full_schema",
            **self._radio_kw(),
        ).pack(side="left", padx=(0, 14))
        ctk.CTkCheckBox(
            schema_mode_row,
            text=self._tr("t5.preserve_tags_on_shorten"),
            variable=self._t5_preserve_tags_on_shorten,
            **self._checkbox_kw(),
        ).pack(side="left", padx=(0, 8))

        append_fr = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        append_fr.pack(fill="x", padx=10, pady=(0, 2))
        ctk.CTkRadioButton(
            append_fr,
            text=self._tr("t5.name_mode.tags_append"),
            variable=self._t5_name_mode,
            value="tags_append",
            **self._radio_kw(),
        ).pack(side="left", padx=(0, 14))
        ctk.CTkRadioButton(
            append_fr,
            text=self._tr("t5.name_mode.tags_replace_except_auto"),
            variable=self._t5_name_mode,
            value="tags_replace_except_auto",
            **self._radio_kw(),
        ).pack(side="left", anchor="w")

        inc_fr = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        inc_fr.pack(fill="x", padx=10, pady=(0, 2))
        self._label(
            inc_fr,
            text=self._tr("t5.from_csv_label"),
            anchor="w",
            wraplength=880,
        ).pack(fill="x", anchor="w", pady=(0, 2))
        inc_row = ctk.CTkFrame(inc_fr, fg_color=self._pal["panel"])
        inc_row.pack(fill="x")
        ctk.CTkCheckBox(
            inc_row, text=self._tr("t5.include_year"), variable=self._t5_include_year, **self._checkbox_kw()
        ).pack(side="left", padx=(0, 12))
        ctk.CTkCheckBox(
            inc_row,
            text=self._tr("t5.include_resolution"),
            variable=self._t5_include_resolution,
            **self._checkbox_kw(),
        ).pack(side="left", padx=(0, 12))
        ctk.CTkCheckBox(
            inc_row, text=self._tr("t5.include_rating"), variable=self._t5_include_rating, **self._checkbox_kw()
        ).pack(side="left", padx=(0, 12))

        probe_fr = ctk.CTkFrame(parent, fg_color=self._pal["panel"])
        probe_fr.pack(fill="x", padx=10, pady=(0, 2))
        self._btn_t5_probe = ctk.CTkButton(
            probe_fr,
            text=self._tr("t5.refresh_probe"),
            width=_btn_w(self._tr("t5.refresh_probe")),
            command=self._t5_refresh_probe,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        )
        self._btn_t5_probe.pack(side="left", padx=(0, 10))

        for i in range(5):
            tag_row = ctk.CTkFrame(parent, fg_color=self._pal["panel"], height=30)
            tag_row.pack_propagate(False)
            tag_row.pack(fill="x", padx=10, pady=(0, 2))
            ctk.CTkCheckBox(tag_row, text="", variable=self._t5_tag_en[i], **self._checkbox_kw()).pack(
                side="left", padx=(0, 6)
            )
            self._ph_string_entry(
                tag_row,
                self._t5_tag_txt[i],
                placeholder=self._tr("t5.tag_slot_ph", n=i + 1),
            ).pack(side="left", fill="x", expand=True)

        preset_fr = ctk.CTkFrame(parent, fg_color=self._pal["panel"], height=32)
        preset_fr.pack_propagate(False)
        preset_fr.pack(fill="x", **pad)
        self._label(preset_fr, text=self._tr("t5.preset_label"), width=120, anchor="w").pack(side="left")
        none_lbl = self._tr("t5.preset_none")
        self._t5_preset_menu = ctk.CTkOptionMenu(
            preset_fr,
            values=[none_lbl],
            variable=self._t5_preset_pick,
            command=self._t5_on_preset_menu_change,
            **{**self._option_kw(), "width": 200},
        )
        self._t5_preset_menu.pack(side="left", padx=(0, 8))
        self._ph_string_entry(
            preset_fr,
            self._t5_preset_name,
            placeholder=self._tr("t5.preset_name_ph"),
            width=160,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            preset_fr,
            text=self._tr("t5.preset_save"),
            width=_btn_w(self._tr("t5.preset_save")),
            command=self._t5_save_preset_click,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            preset_fr,
            text=self._tr("t5.preset_delete"),
            width=_btn_w(self._tr("t5.preset_delete")),
            command=self._t5_delete_preset_click,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left")

        runf = ctk.CTkFrame(parent, fg_color=self._pal["panel"], height=40)
        runf.pack_propagate(False)
        runf.pack(fill="x", **pad)
        ctk.CTkButton(
            runf,
            text=self._tr("t5.fill_new_leaf"),
            width=_btn_w(self._tr("t5.fill_new_leaf")),
            command=self._t5_fill_new_leaf,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkCheckBox(
            runf, text=self._tr("t3.preview_only"), variable=self._t5_dry, **self._checkbox_kw()
        ).pack(side="left", padx=(0, 12))
        sel_box = ctk.CTkFrame(
            runf,
            fg_color=self._pal["panel_elev"],
            corner_radius=8,
            border_width=2,
            border_color=self._pal["cyan_dim"],
        )
        sel_box.pack(side="left", padx=(4, 14), pady=3)
        ctk.CTkCheckBox(
            sel_box,
            text=self._tr("t5.selected_only"),
            variable=self._t5_use_selected,
            **self._checkbox_kw(),
        ).pack(side="left", padx=10, pady=6)
        ctk.CTkButton(
            runf,
            text=self._tr("t3.rename_disk"),
            width=_btn_w(self._tr("t3.rename_disk")),
            command=self._t5_run_renames,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="left")

        self._t5_apply_mode_dependent_ui_state()
        self._t5_sync_preset_menu_from_disk()

    # --- Tab 5 (schema rename) ---
    def _browse_t5_csv(self) -> None:
        p = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if p:
            self._t5_csv.set(p)
            self._save_settings()

    def _t5_read_presets_json(self) -> dict:
        if not _SCHEMA_PRESETS_PATH.is_file():
            return {"version": 1, "presets": {}, "last": ""}
        try:
            data = json.loads(_SCHEMA_PRESETS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"version": 1, "presets": {}, "last": ""}
        if not isinstance(data, dict):
            return {"version": 1, "presets": {}, "last": ""}
        pr = data.get("presets")
        if not isinstance(pr, dict):
            pr = {}
        last = data.get("last")
        if not isinstance(last, str):
            last = ""
        return {"version": 1, "presets": pr, "last": last}

    def _t5_write_presets_json(self, data: dict) -> None:
        try:
            _SCHEMA_PRESETS_PATH.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as e:
            self._log(self._tr("log.t5_preset_save_fail", e=e))

    def _t5_collect_preset_dict(self) -> dict:
        try:
            tml = int(self._t5_title_max.get().strip() or "15")
        except ValueError:
            tml = 15
        return {
            "title_max_len": tml,
            "include_year": bool(self._t5_include_year.get()),
            "include_resolution": bool(self._t5_include_resolution.get()),
            "include_rating": bool(self._t5_include_rating.get()),
            "tag_enabled": [bool(self._t5_tag_en[i].get()) for i in range(5)],
            "tag_text": [self._t5_tag_txt[i].get() for i in range(5)],
            "name_mode": self._t5_name_mode_effective(),
            "preserve_tags_on_shorten": bool(self._t5_preserve_tags_on_shorten.get()),
        }

    def _t5_apply_preset_dict(self, d: dict) -> None:
        if not isinstance(d, dict):
            return
        tml = d.get("title_max_len", 15)
        try:
            tml = int(tml)
        except (TypeError, ValueError):
            tml = 15
        self._t5_title_max.set(str(max(0, min(200, tml))))
        self._t5_include_year.set(bool(d.get("include_year", True)))
        self._t5_include_resolution.set(bool(d.get("include_resolution", True)))
        self._t5_include_rating.set(bool(d.get("include_rating", True)))
        te = d.get("tag_enabled")
        if isinstance(te, list):
            for i in range(5):
                if i < len(te):
                    self._t5_tag_en[i].set(bool(te[i]))
        tt = d.get("tag_text")
        if isinstance(tt, list):
            for i in range(5):
                if i < len(tt):
                    self._t5_tag_txt[i].set(str(tt[i] or ""))
        nm = d.get("name_mode")
        if isinstance(nm, str):
            nmx = nm.strip().lower()
            if nmx in ("tags_replace_except_auto", "tags_overwrite"):
                self._t5_name_mode.set("tags_replace_except_auto")
            elif nmx in ("tags_append", "tags_append_shorten"):
                self._t5_name_mode.set("tags_append")
            elif nmx == "full_schema":
                self._t5_name_mode.set("full_schema")
            else:
                self._t5_name_mode.set("full_schema")
        else:
            ato = d.get("append_tags_only")
            if isinstance(ato, bool) and ato:
                self._t5_name_mode.set("tags_append")
            elif bool(d.get("tags_shorten_title", False)):
                self._t5_name_mode.set("tags_append")
            else:
                self._t5_name_mode.set("full_schema")
        pv = d.get("preserve_tags_on_shorten")
        if isinstance(pv, bool):
            self._t5_preserve_tags_on_shorten.set(pv)
        else:
            ss = d.get("shorten_scope")
            if isinstance(ss, str) and ss.strip().lower() == "title_only":
                self._t5_preserve_tags_on_shorten.set(True)
            elif isinstance(ss, str) and ss.strip().lower() == "full_stem":
                self._t5_preserve_tags_on_shorten.set(False)
        self._t5_apply_mode_dependent_ui_state()
        self._t5_rebuild_tree()

    def _t5_sync_preset_menu_from_disk(self) -> None:
        data = self._t5_read_presets_json()
        none_lbl = self._tr("t5.preset_none")
        names = sorted(data["presets"].keys(), key=str.lower)
        vals = [none_lbl] + names
        if self._t5_preset_menu is not None:
            self._t5_preset_menu.configure(values=vals)
        last = (data.get("last") or "").strip()
        if last and last in data["presets"]:
            self._t5_preset_pick.set(last)
        else:
            self._t5_preset_pick.set(none_lbl)

    def _t5_on_preset_menu_change(self, choice: str) -> None:
        none_lbl = self._tr("t5.preset_none")
        data = self._t5_read_presets_json()
        if choice == none_lbl:
            data["last"] = ""
            self._t5_write_presets_json(data)
            return
        blob = data["presets"].get(choice)
        if isinstance(blob, dict):
            self._t5_apply_preset_dict(blob)
        data["last"] = choice
        self._t5_write_presets_json(data)

    def _t5_save_preset_click(self) -> None:
        name = self._t5_preset_name.get().strip()
        if not name:
            self._log(self._tr("log.t5_preset_need_name"))
            return
        none_lbl = self._tr("t5.preset_none")
        if name == none_lbl:
            self._log(self._tr("log.t5_preset_bad_name"))
            return
        data = self._t5_read_presets_json()
        data["presets"][name] = self._t5_collect_preset_dict()
        data["last"] = name
        self._t5_write_presets_json(data)
        self._t5_sync_preset_menu_from_disk()
        self._t5_preset_pick.set(name)
        self._log(self._tr("log.t5_preset_saved", name=name))

    def _t5_delete_preset_click(self) -> None:
        choice = self._t5_preset_pick.get().strip()
        none_lbl = self._tr("t5.preset_none")
        if not choice or choice == none_lbl:
            self._log(self._tr("log.t5_preset_none_selected"))
            return
        data = self._t5_read_presets_json()
        if choice in data["presets"]:
            del data["presets"][choice]
        if data.get("last") == choice:
            data["last"] = ""
        self._t5_write_presets_json(data)
        self._t5_sync_preset_menu_from_disk()
        self._log(self._tr("log.t5_preset_deleted", name=choice))

    def _t5_row_visible(self, row: dict[str, str]) -> bool:
        inc = compose_ui_list_filter(
            self._t5_filter.get(),
            self._t5_filter_field.get(),
            self._t5_filter_combine.get(),
        )
        exc = compose_ui_list_filter(
            self._t5_filter_exclude.get(),
            self._t5_filter_exclude_field.get(),
            self._t5_filter_exclude_combine.get(),
        )
        # Building visibility runs for every row — only compute the expensive proposed leaf when
        # the filter actually references the proposed column (``proposed:`` prefix).
        need_prop = "proposed:" in inc.lower() or "proposed:" in exc.lower()
        leaf = ""
        if need_prop:
            leaf, _w = self._t5_compute_leaf_for_row(row)
        return row_passes_list_filters(
            inc,
            exc,
            file_path=row.get("file_path", ""),
            file_name=row.get("file_name", ""),
            file_extension=(row.get("file_extension") or "").strip() or leaf_extension_from_row(row),
            new_leaf=row.get("new_leaf", ""),
            scene_title=row.get("scene_title", ""),
            scene_tags=row.get("scene_tags", ""),
            scene_markers=row.get("scene_markers", ""),
            scene_id=row.get("scene_id", ""),
            scene_date=row.get("scene_date", ""),
            proposed_leaf=leaf if need_prop else "",
        )

    def _t5_visible_indices(self) -> list[int]:
        return [i for i, row in enumerate(self._t5_rows) if self._t5_row_visible(row)]

    def _t5_selected_indices(self) -> list[int]:
        out: list[int] = []
        if not hasattr(self, "_t5_tree"):
            return out
        for iid in self._t5_tree.selection():
            try:
                out.append(int(iid))
            except ValueError:
                continue
        return out

    def _t5_cache_key_for_row(self, row: dict[str, str]) -> str:
        fp = (row.get("file_path") or "").strip()
        hit = resolve_csv_path_to_existing_file(fp)
        return str(hit) if hit else ""

    def _t5_dims_for_row(self, row: dict[str, str]) -> tuple[int | None, int | None]:
        key = self._t5_cache_key_for_row(row)
        if not key:
            return None, None
        w, h = self._t5_ffprobe_cache.get(key, (None, None))
        return w, h

    def _t5_schema_options_kwargs(self) -> dict:
        try:
            tml = int(self._t5_title_max.get().strip() or "15")
        except ValueError:
            tml = 15
        return {
            "title_max_len": tml,
            "tag_enabled": [self._t5_tag_en[i].get() for i in range(5)],
            "tag_text": [self._t5_tag_txt[i].get() for i in range(5)],
            "include_year": self._t5_include_year.get(),
            "include_resolution": self._t5_include_resolution.get(),
            "include_rating": self._t5_include_rating.get(),
            "resolution_mode": "heightp",
        }

    @staticmethod
    def _sort_key_text(v: object) -> str:
        return str(v or "").strip().casefold()

    @staticmethod
    def _sort_key_int_or_text(v: object) -> tuple[int, object]:
        s = str(v or "").strip()
        if s.isdigit():
            return (0, int(s))
        return (1, s.casefold())

    def _t3_sort_key(self, row: dict[str, str], col: str):
        if col == "path":
            return self._sort_key_text(row.get("file_path", ""))
        if col == "name":
            return self._sort_key_text(row.get("file_name", ""))
        if col == "ext":
            return self._sort_key_text(leaf_extension_from_row(row))
        if col == "new_leaf":
            return self._sort_key_text(row.get("new_leaf", ""))
        return self._sort_key_text(row.get("file_path", ""))

    def _t4_sort_key(self, row: dict[str, str], col: str):
        if col == "path":
            return self._sort_key_text(row.get("file_path", ""))
        if col == "name":
            return self._sort_key_text(row.get("file_name", ""))
        if col == "scene_id":
            return self._sort_key_int_or_text(row.get("scene_id", ""))
        return self._sort_key_text(row.get("file_path", ""))

    def _t5_sort_key_for_row(
        self, row: dict[str, str], col: str, *, proposed_leaf: str | None = None
    ) -> object:
        if col == "path":
            return self._sort_key_text(row.get("file_path", ""))
        if col == "file_name":
            return self._sort_key_text(row.get("file_name", ""))
        if col == "scene_id":
            return self._sort_key_int_or_text(row.get("scene_id", ""))
        if col == "scene_tags":
            return self._sort_key_text(row.get("scene_tags", ""))
        if col == "scene_markers":
            return self._sort_key_text(row.get("scene_markers", ""))
        if col == "scene_date":
            return self._sort_key_text(row.get("scene_date", ""))
        if col == "proposed":
            if proposed_leaf is not None:
                return self._sort_key_text(proposed_leaf)
            leaf, _w = self._t5_compute_leaf_for_row(row)
            return self._sort_key_text(leaf)
        return self._sort_key_text(row.get("file_path", ""))

    def _toggle_sort_t3(self, col: str) -> None:
        if self._t3_sort_col == col:
            self._t3_sort_desc = not self._t3_sort_desc
        else:
            self._t3_sort_col = col
            self._t3_sort_desc = False
        self._t3_rebuild_tree()

    def _toggle_sort_t4(self, col: str) -> None:
        if self._t4_sort_col == col:
            self._t4_sort_desc = not self._t4_sort_desc
        else:
            self._t4_sort_col = col
            self._t4_sort_desc = False
        self._t4_rebuild_tree()
        self._t4_schedule_preview_refresh()

    def _toggle_sort_t5(self, col: str) -> None:
        if self._t5_sort_col == col:
            self._t5_sort_desc = not self._t5_sort_desc
        else:
            self._t5_sort_col = col
            self._t5_sort_desc = False
        self._t5_rebuild_tree()

    def _t5_prior_leaf_for_merge(self, row: dict[str, str]) -> str:
        """
        Source leaf for ``merge_extra_bracket_tags_into_leaf``. Prefer ``new_leaf`` after Fill.
        In **Add tags** / **Overwrite tags** mode, derive from ``file_name`` + slots + CSV metadata
        (same pipeline as the proposed name). With full schema and **protect tags** on, use
        ``file_name`` so existing ``[…]`` are visible to merge even when no slot changed the name yet.
        """
        nl = (row.get("new_leaf") or "").strip()
        if nl:
            return nl
        fn = (row.get("file_name") or "").strip()
        if not fn:
            return ""
        if self._t5_in_tags_mode():
            opts = self._t5_schema_options_kwargs()
            w, h = self._t5_dims_for_row(row)
            base_in = fn
            if self._t5_tags_replace_except_auto():
                base_in = strip_non_auto_bracket_tags_from_leaf(fn)
            work = append_schema_tags_to_leaf(
                base_in,
                tag_enabled=opts["tag_enabled"],
                tag_text=opts["tag_text"],
                replace_existing_slot_tags=self._t5_tags_replace_except_auto(),
            )
            work2, _mw = merge_schema_metadata_into_append_leaf(
                work,
                row,
                include_year=bool(opts["include_year"]),
                include_resolution=bool(opts["include_resolution"]),
                include_rating=bool(opts["include_rating"]),
                resolution_mode=str(opts["resolution_mode"] or "heightp"),
                video_width=w,
                video_height=h,
                overwrite_auto_tags=False,
                preserve_auto_tokens_from_leaf=self._t5_tags_replace_except_auto(),
            )
            # Tags modes: always shorten only the head before trailing ``[…]`` — never cap the
            # whole stem (that would chop appended tags when “Protect tags” is off).
            built, _w = build_leaf_tags_only_mode(
                row,
                title_max_len=opts["title_max_len"],
                tag_enabled=opts["tag_enabled"],
                tag_text=opts["tag_text"],
                leaf_after_append_and_metadata=work2,
            )
            return built.strip() if built.strip() else ""
        # Full schema: use the real file name so ``merge_extra_bracket_tags_into_leaf`` can
        # see existing ``[…]`` tags. (Previously we only used a preview when slots changed
        # the name — then “protect tags” had nothing to merge unless “append only” was on.)
        if self._t5_preserve_tags_on_shorten.get():
            return fn
        appended = append_schema_tags_to_leaf(
            fn,
            tag_enabled=[self._t5_tag_en[k].get() for k in range(5)],
            tag_text=[self._t5_tag_txt[k].get() for k in range(5)],
        )
        return appended if appended.strip() != fn.strip() else ""

    def _t5_compute_leaf_for_row(self, row: dict[str, str]) -> tuple[str, str]:
        opts = self._t5_schema_options_kwargs()
        scope = self._t5_shorten_scope_effective()
        if self._t5_in_tags_mode():
            base_leaf = (row.get("new_leaf") or "").strip() or (row.get("file_name") or "").strip()
            if not base_leaf:
                return "", ""
            w, h = self._t5_dims_for_row(row)
            base_in = base_leaf
            if self._t5_tags_replace_except_auto():
                base_in = strip_non_auto_bracket_tags_from_leaf(base_leaf)
            work = append_schema_tags_to_leaf(
                base_in,
                tag_enabled=opts["tag_enabled"],
                tag_text=opts["tag_text"],
                replace_existing_slot_tags=self._t5_tags_replace_except_auto(),
            )
            work2, meta_warn = merge_schema_metadata_into_append_leaf(
                work,
                row,
                include_year=bool(opts["include_year"]),
                include_resolution=bool(opts["include_resolution"]),
                include_rating=bool(opts["include_rating"]),
                resolution_mode=str(opts["resolution_mode"] or "heightp"),
                video_width=w,
                video_height=h,
                overwrite_auto_tags=False,
                preserve_auto_tokens_from_leaf=self._t5_tags_replace_except_auto(),
            )
            warn = meta_warn or ""
            # Tags modes: always shorten only the title head (see prior_leaf_for_merge).
            leaf, tw = build_leaf_tags_only_mode(
                row,
                title_max_len=opts["title_max_len"],
                tag_enabled=opts["tag_enabled"],
                tag_text=opts["tag_text"],
                leaf_after_append_and_metadata=work2,
            )
            if tw and not warn:
                warn = tw
            return leaf, warn
        w, h = self._t5_dims_for_row(row)
        leaf, warn = build_schema_rename_leaf(
            row,
            video_width=w,
            video_height=h,
            **opts,
        )
        if leaf:
            prior = self._t5_prior_leaf_for_merge(row)
            if prior:
                # Merge keeps ``[…]`` from ``prior`` that are still missing on ``schema_leaf``.
                # Inners already present on ``leaf`` (including from checked slots / resolution /
                # rating) are skipped, so duplicates are not added.
                leaf = merge_extra_bracket_tags_into_leaf(prior, leaf)
            if scope == "full_stem":
                leaf2, tw = truncate_leaf_stem_to_max_chars(leaf, opts["title_max_len"])
                leaf = leaf2
                if tw and not warn:
                    warn = tw
        return leaf, warn

    def _t5_build_visible_tree_rows(self) -> list[tuple[str, tuple[object, ...]]]:
        visible = [i for i, row in enumerate(self._t5_rows) if self._t5_row_visible(row)]
        col = self._t5_sort_col
        # One ``_t5_compute_leaf_for_row`` per visible row (sorting by "proposed" used to call it
        # O(n log n) times via key comparisons).
        decorated: list[tuple[object, int, str]] = []
        for i in visible:
            row = self._t5_rows[i]
            leaf, _w = self._t5_compute_leaf_for_row(row)
            sk = self._t5_sort_key_for_row(row, col, proposed_leaf=leaf)
            decorated.append((sk, i, leaf))
        decorated.sort(key=lambda t: t[0], reverse=self._t5_sort_desc)
        rows_out: list[tuple[str, tuple[object, ...]]] = []
        for _sk, i, leaf in decorated:
            row = self._t5_rows[i]
            rows_out.append(
                (
                    str(i),
                    (
                        row.get("file_path", ""),
                        "",
                        row.get("file_name", ""),
                        "",
                        leaf or "—",
                        row.get("scene_id", ""),
                        row.get("scene_tags", ""),
                        row.get("scene_markers", ""),
                        row.get("scene_date", ""),
                    ),
                )
            )
        return rows_out

    def _t5_try_refresh_tree_leaves_only(self) -> bool:
        """
        If the tree already lists the same row iids in the same order, only refresh cell
        values (avoids delete+reinsert — that was especially slow when toggling tag slots).
        """
        if not hasattr(self, "_t5_tree"):
            return True
        rows_out = self._t5_build_visible_tree_rows()
        want_ids = [iid for iid, _ in rows_out]
        have_ids = list(self._t5_tree.get_children())
        if want_ids != have_ids:
            return False
        prev = self._t5_selected_indices()
        for step, (iid, vals) in enumerate(rows_out):
            self._t5_tree.item(iid, values=vals)
            if step > 0 and step % 400 == 0:
                try:
                    self.update_idletasks()
                except TclError:
                    pass
        self._ttk_restore_row_selection(self._t5_tree, prev)
        try:
            self.update_idletasks()
        except TclError:
            pass
        return True

    def _t5_on_schema_preview_change(self, *_args: object) -> None:
        """Schema options that only change the proposed leaf column — prefer in-place tree update."""
        self._cancel_t5_tree_rebuild_after()
        if not self._t5_try_refresh_tree_leaves_only():
            self._t5_rebuild_tree()

    def _t5_rebuild_tree(self) -> None:
        if not hasattr(self, "_t5_tree"):
            return
        self._cancel_t5_tree_rebuild_after()
        prev = self._t5_selected_indices()
        rows_out = self._t5_build_visible_tree_rows()
        self._ttk_tree_replace_rows(self._t5_tree, rows_out)
        self._ttk_restore_row_selection(self._t5_tree, prev)

    def _t5_load_csv(self) -> None:
        path = self._t5_csv.get().strip()
        if not path or not Path(path).is_file():
            self._log(self._tr("log.t5_need_csv"))
            return
        try:
            self._t5_rows, sniffed = read_rename_csv(Path(path))
        except OSError as e:
            self._log(self._tr("log.csv_read_fail", e=e))
            return
        self._t5_ffprobe_cache.clear()
        self._log(self._tr("log.t5_loaded", n=len(self._t5_rows), path=path, sniff=sniffed))
        self.after(1, self._t5_finish_csv_load)

    def _t5_finish_csv_load(self) -> None:
        if not hasattr(self, "_t5_tree"):
            return
        self._t5_rebuild_tree()
        self._save_settings()

    def _t5_save_csv(self) -> None:
        path = self._t5_csv.get().strip()
        if not path:
            path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
            if not path:
                return
            self._t5_csv.set(path)
        try:
            write_rename_csv(Path(path), self._t5_rows, self._app_csv_delim())
            self._log(self._tr("log.t5_saved", n=len(self._t5_rows), path=path))
        except OSError as e:
            self._log(self._tr("log.save_failed", e=e))
        self._save_settings()

    def _t5_refresh_probe(self) -> None:
        if self._t5_probe_busy:
            self._log(self._tr("log.busy_probe"))
            return
        exe = find_ffprobe_executable()
        if not exe:
            self._log(self._tr("log.t5_no_ffprobe"))
            return
        vis = self._t5_visible_indices()
        keys_order: list[str] = []
        seen_k: set[str] = set()
        idx_by_key: dict[str, int] = {}
        for i in vis:
            row = self._t5_rows[i]
            key = self._t5_cache_key_for_row(row)
            if not key or key in seen_k:
                continue
            seen_k.add(key)
            keys_order.append(key)
            idx_by_key[key] = i
        if not keys_order:
            self._log(self._tr("log.t5_probed", ok=0, total=len(vis)))
            self._t5_rebuild_tree()
            return

        total_k = len(keys_order)
        self._t5_probe_busy = True
        if self._btn_t5_probe is not None:
            self._btn_t5_probe.configure(state="disabled")
        self._work_status.set(self._tr("common.work_background"))
        self._work_progress_probe(0, total_k)

        def prog(cur: int, tot: int) -> None:
            self.after(0, lambda c=cur, t=tot: self._work_progress_probe(c, t))

        def worker() -> None:
            res, fails = ffprobe_paths_parallel(keys_order, ffprobe_exe=exe, progress=prog)
            ik = dict(idx_by_key)
            self.after(
                0,
                lambda res=res, fails=fails, ik=ik: self._finish_t5_probe_batch(res, fails, ik),
            )

        threading.Thread(target=worker, daemon=True).start()

    def _finish_t5_probe_batch(
        self,
        res: dict[str, tuple[int, int]],
        fails: list[tuple[str, str]],
        idx_by_key: dict[str, int],
    ) -> None:
        self._t5_probe_busy = False
        try:
            if self._btn_t5_probe is not None:
                self._btn_t5_probe.configure(state="normal")
        except TclError:
            pass
        self._clear_work_progress()
        for p, wh in res.items():
            self._t5_ffprobe_cache[p] = wh
        for p, err in fails:
            i = idx_by_key.get(p, -1)
            fp = self._t5_rows[i].get("file_path", "") if 0 <= i < len(self._t5_rows) else p
            self._log(self._tr("log.t5_probe_row_fail", path=fp or p, err=err[:120]))
        n_paths = len(res) + len(fails)
        self._log(self._tr("log.t5_probed", ok=len(res), total=n_paths))
        self._t5_rebuild_tree()

    def _t5_fill_new_leaf(self, *, silent: bool = False) -> None:
        idxs = self._t5_selected_indices() if self._t5_use_selected.get() else self._t5_visible_indices()
        n = 0
        total = len(idxs)
        try:
            if total > 0:
                self._work_progress_fill(0, total)
            for step, i in enumerate(idxs):
                if i < 0 or i >= len(self._t5_rows):
                    continue
                row = self._t5_rows[i]
                leaf, _w = self._t5_compute_leaf_for_row(row)
                if leaf:
                    self._t5_rows[i]["new_leaf"] = leaf
                    n += 1
                done = step + 1
                if total > 0 and (done == 1 or done % 40 == 0 or done == total):
                    self._work_progress_fill(done, total)
                    self._tk_keepalive(step)
            if not silent:
                self._log(self._tr("log.t5_fill_done", n=n))
            self._t5_rebuild_tree()
        finally:
            self._clear_work_progress()

    def _t5_run_renames(self) -> None:
        try:
            self.update_idletasks()
        except TclError:
            pass
        if self._t5_use_selected.get():
            sel = self._t5_selected_indices()
            if not sel:
                self._log(self._tr("log.t5_rename_need_selection"))
                return
            rename_indices = sel
        else:
            rename_indices = None
        # new_leaf is only updated on Fill; re-fill from current schema so tag/title changes apply.
        self._t5_fill_new_leaf(silent=True)
        dry = self._t5_dry.get()
        undo_rec: list[tuple[int, str, str, str]] = []
        try:
            renamed, skipped, log_lines = apply_file_renames(
                self._t5_rows,
                dry_run=dry,
                only_indices=rename_indices,
                keep_alive=self._tk_keepalive,
                keep_alive_every=35,
                progress=self._work_progress_rename,
                undo_stack=undo_rec,
            )
            self._log_many_lines(log_lines)
            self._log(self._tr("log.t5_rename_summary", renamed=renamed, skipped=skipped, dry=dry))
            self._t5_rebuild_tree()
            self._save_settings()
            if not dry and renamed > 0 and undo_rec:
                self._register_rename_undo_stack("t5", undo_rec)
        finally:
            self._clear_work_progress()

    # --- Tab 1 ---
    def _t1_reset_graphql_path(self) -> None:
        self._t1_graphql_path.set("")

    def _browse_t1_ps1(self) -> None:
        p = filedialog.askopenfilename(
            filetypes=[("PowerShell", "*.ps1"), ("All", "*.*")],
            title=self._tr("dlg.choose_ps1"),
        )
        if p:
            self._t1_ps1.set(p)

    def _browse_t1_out(self) -> None:
        p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if p:
            self._t1_out.set(p)
            self._save_settings()

    def _browse_t1_ps1_to_var(self, var: ctk.StringVar) -> None:
        p = filedialog.askopenfilename(
            filetypes=[("PowerShell", "*.ps1"), ("All", "*.*")],
            title=self._tr("dlg.choose_ps1"),
        )
        if p:
            var.set(p)

    def _open_t1_out_dir(self) -> None:
        d = Path(self._t1_out.get().strip() or ".")
        folder = d.parent if d.suffix else d
        folder = folder.resolve()
        if folder.is_dir():
            subprocess.Popen(f'explorer "{folder}"', shell=True)
        else:
            self._log(self._tr("log.folder_not_found", folder=folder))

    def _run_t1_export(self) -> None:
        ps1 = self._t1_ps1.get().strip()
        if not ps1 or not Path(ps1).is_file():
            self._log(self._tr("log.t1_need_ps1"))
            return
        out = self._t1_out.get().strip()
        if not out:
            out = str(_default_file_tools_csv_dir() / "stash_files.csv")
            self._t1_out.set(out)
        try:
            per_page = int(self._t1_per_page.get().strip())
        except ValueError:
            self._log(self._tr("log.batch_size_int"))
            return
        delim = self._app_csv_delim()
        url = self._t1_url.get().strip() or "http://127.0.0.1:9999"

        args: list[str] = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(Path(ps1).resolve()),
            "-StashUrl",
            url,
            "-GraphqlPath",
            (self._t1_graphql_path.get().strip() or "/graphql"),
            "-OutFile",
            out,
            "-PerPage",
            str(per_page),
            "-Delimiter",
            delim,
        ]
        ak = self._t1_api.get().strip()
        if ak:
            args.extend(["-ApiKey", ak])

        def add_opt(flag: str, val: str) -> None:
            v = val.strip()
            if v:
                args.extend([flag, v])

        add_opt("-PathPrefix", self._t1_path_prefix.get())
        add_opt("-PathContains", self._t1_path_contains.get())
        add_opt("-FileNameContains", self._t1_name_contains.get())
        add_opt("-FileNameRegex", self._t1_name_regex.get())

        if self._t1_export_busy:
            self._log(self._tr("log.busy_export"))
            return
        self._t1_export_busy = True
        if self._btn_t1_export is not None:
            self._btn_t1_export.configure(state="disabled")
        self._work_status.set(self._tr("common.work_background"))
        self._log(self._tr("log.t1_export_header"))
        cwd = str(Path(ps1).parent)

        def worker() -> None:
            try:
                r = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=cwd,
                )
            except OSError as e:
                self.after(0, lambda e=e: self._finish_t1_export(None, e, out))
            else:
                self.after(0, lambda r=r, o=out: self._finish_t1_export(r, None, o))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_t1_export(
        self,
        r: subprocess.CompletedProcess[str] | None,
        err: OSError | None,
        out: str,
    ) -> None:
        self._t1_export_busy = False
        try:
            if self._btn_t1_export is not None:
                self._btn_t1_export.configure(state="normal")
        except TclError:
            pass
        self._clear_work_progress()
        if err is not None:
            self._log(self._tr("log.powershell_fail", e=err))
            return
        if r is None:
            return
        if r.stdout:
            self._log(r.stdout)
        if r.stderr:
            self._log(r.stderr)
        self._log(self._tr("log.exit_code", code=r.returncode))
        if r.returncode == 0:
            self._last_shared_csv = str(Path(out).resolve())
            self._t3_csv.set(self._last_shared_csv)
            self._t4_csv.set(self._last_shared_csv)
            self._t5_csv.set(self._last_shared_csv)
            self._log(self._tr("log.tip_tab3_csv", path=self._last_shared_csv))
            self._log(self._tr("log.tip_shared_csv_tabs", path=self._last_shared_csv))
            self._save_settings()

    # --- Tab 2 ---
    def _browse_t2_folder(self) -> None:
        p = filedialog.askdirectory(title=self._tr("dlg.folder_scan"))
        if p:
            self._t2_folder.set(p)

    def _browse_t2_out(self) -> None:
        p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if p:
            self._t2_out.set(p)

    def _parse_patterns(self) -> list[str]:
        raw = self._t2_patterns.get().strip()
        if not raw:
            return []
        parts: list[str] = []
        for chunk in raw.replace(",", ";").split(";"):
            c = chunk.strip()
            if c:
                parts.append(c)
        return parts

    def _run_t2_scan(self) -> None:
        if self._t2_scan_busy:
            self._log(self._tr("log.busy_scan"))
            return
        folder = self._t2_folder.get().strip()
        if not folder:
            self._log(self._tr("log.t2_pick_folder"))
            return
        root = Path(folder)
        if not root.is_dir():
            self._log(self._tr("log.not_directory", root=root))
            return
        out = self._t2_out.get().strip()
        if not out:
            out = str(_default_file_tools_csv_dir() / "disk_scan.csv")
            self._t2_out.set(out)
        patterns = self._parse_patterns()
        self._log(
            self._tr("log.t2_scanning", root=root, sub=self._t2_recursive.get()),
        )
        out_path = Path(out)
        delim = self._app_csv_delim()
        recursive = self._t2_recursive.get()
        pat_list = patterns or None
        self._t2_scan_busy = True
        if self._btn_t2_scan is not None:
            self._btn_t2_scan.configure(state="disabled")
        self._work_status.set(self._tr("common.work_background"))

        def worker() -> None:
            try:
                rows = scan_folder_files(root, recursive=recursive, patterns=pat_list)
                write_rename_csv(out_path, rows, delim)
            except OSError as e:
                self.after(0, lambda e=e, op=out_path: self._finish_t2_scan(None, e, op))
            else:
                self.after(0, lambda rows=rows, op=out_path: self._finish_t2_scan(rows, None, op))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_t2_scan(
        self,
        rows: list[dict[str, str]] | None,
        err: OSError | None,
        out_path: Path,
    ) -> None:
        self._t2_scan_busy = False
        try:
            if self._btn_t2_scan is not None:
                self._btn_t2_scan.configure(state="normal")
        except TclError:
            pass
        self._clear_work_progress()
        if err is not None:
            self._log(self._tr("log.save_failed", e=err))
            return
        if rows is None:
            return
        out_s = str(out_path)
        self._log(self._tr("log.wrote_items", n=len(rows), out=out_s))
        self._last_shared_csv = str(out_path.resolve())
        self._t3_csv.set(self._last_shared_csv)
        self._log(self._tr("log.tip_t3_set", path=self._last_shared_csv))
        self._save_settings()

    def _push_csv_path_to_tab3(self, out: str, err_msg: str) -> None:
        out = out.strip()
        if out and Path(out).is_file():
            self._t3_csv.set(str(Path(out).resolve()))
            self._t3_load_csv()
        else:
            self._log(err_msg)

    def _t1_push_to_tab3(self) -> None:
        self._push_csv_path_to_tab3(self._t1_out.get(), self._tr("log.t1_push_fail"))

    def _t2_push_to_tab3(self) -> None:
        self._push_csv_path_to_tab3(self._t2_out.get(), self._tr("log.t2_push_fail"))

    def _push_csv_path_to_tab4(self, out: str, err_msg: str) -> None:
        out = out.strip()
        if out and Path(out).is_file():
            self._t4_csv.set(str(Path(out).resolve()))
            self._t4_load_csv()
        else:
            self._log(err_msg)

    def _t1_push_to_tab4(self) -> None:
        self._push_csv_path_to_tab4(self._t1_out.get(), self._tr("log.t1_push_fail"))

    def _t2_push_to_tab4(self) -> None:
        self._push_csv_path_to_tab4(self._t2_out.get(), self._tr("log.t2_push_fail"))

    def _t2_push_to_tab5(self) -> None:
        self._push_csv_path_to_tab5(self._t2_out.get(), self._tr("log.t2_push_fail"))

    def _push_csv_path_to_tab5(self, out: str, err_msg: str) -> None:
        out = out.strip()
        if out and Path(out).is_file():
            self._t5_csv.set(str(Path(out).resolve()))
            self._t5_load_csv()
        else:
            self._log(err_msg)

    def _t1_push_to_tab5(self) -> None:
        self._push_csv_path_to_tab5(self._t1_out.get(), self._tr("log.t1_push_fail"))

    # --- Tab 3 ---
    def _browse_t3_csv(self) -> None:
        p = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if p:
            self._t3_csv.set(p)

    def _browse_t3_only_under(self) -> None:
        p = filedialog.askdirectory(title=self._tr("dlg.restrict_rename"))
        if p:
            self._t3_only_under.set(p)

    def _browse_t3_fold_src(self) -> None:
        p = filedialog.askdirectory(title=self._tr("dlg.folder_danger"))
        if p:
            self._t3_fold_src.set(p)

    def _browse_t4_target_folder(self) -> None:
        p = filedialog.askdirectory(title=self._tr("dlg.move_target"))
        if p:
            self._t4_target_folder.set(p)

    def _t4_set_target_from_selected_row_folder(self) -> None:
        """Fill move-target field with the parent directory of a selected list row (first selected)."""
        indices = self._t4_selected_indices()
        if not indices:
            self._log(self._tr("log.t4_target_folder_select_row"))
            return
        row = self._t4_rows[indices[0]]
        fp = (row.get("file_path") or "").strip()
        if not fp:
            self._log(self._tr("log.t4_target_folder_no_path"))
            return
        resolved = resolve_csv_path_to_existing_file(fp)
        path_obj = resolved if resolved is not None else Path(fp)
        parent = path_obj.parent
        self._t4_target_folder.set(str(parent))
        if len(indices) > 1:
            self._log(self._tr("log.t4_target_folder_multi", n=len(indices), path=parent))
        else:
            self._log(self._tr("log.t4_target_folder_set", path=parent))
        self._t4_schedule_preview_refresh()

    def _browse_t4_csv(self) -> None:
        p = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if p:
            self._t4_csv.set(p)

    def _t4_row_visible(self, row: dict[str, str]) -> bool:
        inc = compose_ui_list_filter(
            self._t4_filter.get(),
            self._t4_filter_field.get(),
            self._t4_filter_combine.get(),
        )
        exc = compose_ui_list_filter(
            self._t4_filter_exclude.get(),
            self._t4_filter_exclude_field.get(),
            self._t4_filter_exclude_combine.get(),
        )
        return row_passes_list_filters(
            inc,
            exc,
            file_path=row.get("file_path", ""),
            file_name=row.get("file_name", ""),
            file_extension=leaf_extension_from_row(row),
            new_leaf=row.get("new_leaf", ""),
            scene_title=row.get("scene_title", ""),
            scene_tags=row.get("scene_tags", ""),
            scene_markers=row.get("scene_markers", ""),
            scene_id=row.get("scene_id", ""),
            scene_date=row.get("scene_date", ""),
            proposed_leaf="",
        )

    def _t4_rebuild_tree(self) -> None:
        if not hasattr(self, "_t4_tree"):
            return
        prev = self._t4_selected_indices()
        visible = [i for i, row in enumerate(self._t4_rows) if self._t4_row_visible(row)]
        visible.sort(
            key=lambda idx: self._t4_sort_key(self._t4_rows[idx], self._t4_sort_col),
            reverse=self._t4_sort_desc,
        )
        rows_out: list[tuple[str, tuple[object, ...]]] = []
        for i in visible:
            row = self._t4_rows[i]
            rows_out.append(
                (
                    str(i),
                    (row.get("file_path", ""), "", row.get("file_name", ""), "", row.get("scene_id", "")),
                ),
            )
        self._ttk_tree_replace_rows(self._t4_tree, rows_out)
        self._ttk_restore_row_selection(self._t4_tree, prev)

    def _t4_selected_indices(self) -> list[int]:
        out: list[int] = []
        if not hasattr(self, "_t4_tree"):
            return out
        for iid in self._t4_tree.selection():
            try:
                out.append(int(iid))
            except ValueError:
                continue
        return out

    def _t4_filtered_indices(self) -> list[int]:
        indices: list[int] = []
        if not hasattr(self, "_t4_tree"):
            return indices
        for item in self._t4_tree.get_children():
            try:
                indices.append(int(item))
            except ValueError:
                continue
        return indices

    def _t4_is_per_source_mode(self) -> bool:
        return self._t4_per_source.get()

    def _t4_suggest_target_from_filtered(self) -> None:
        indices = self._t4_filtered_indices()
        if not indices:
            self._log(self._tr("log.t4_suggest_no_match"))
            return
        parents: list[Path] = []
        for i in indices:
            row = self._t4_rows[i]
            fp = (row.get("file_path") or "").strip()
            if not fp:
                continue
            resolved = resolve_csv_path_to_existing_file(fp)
            if resolved is not None:
                parents.append(resolved.parent)
            else:
                parents.append(Path(fp).parent)
        if not parents:
            self._log(self._tr("log.t4_suggest_no_paths"))
            return

        eff = compose_ui_list_filter(
            self._t4_filter.get(),
            self._t4_filter_field.get(),
            self._t4_filter_combine.get(),
        )
        sub = sanitize_windows_dir_component(filter_stub_for_subfolder_suggest(eff)) or "moved"
        parent_strs = sorted({str(p) for p in parents})
        base = Path(parent_strs[0])
        if len(parent_strs) > 1:
            try:
                base = Path(os.path.commonpath(parent_strs))
            except ValueError:
                base = Path(parent_strs[0])
                self._log(self._tr("log.t4_mixed_drives"))

        if self._t4_is_per_source_mode():
            self._t4_target_folder.set(str(base.anchor or base))
            self._t4_subfolder.set(sub)
            self._log(self._tr("log.t4_suggest_per_source", sub=sub))
        else:
            self._t4_target_folder.set(str(base))
            self._t4_subfolder.set(sub)
            self._log(self._tr("log.t4_suggest_target", base=base, sub=sub))
        self._t4_refresh_preview()

    def _t4_schedule_preview_refresh(self) -> None:
        if not hasattr(self, "_t4_preview"):
            return
        try:
            if int(self._t4_preview.winfo_exists()) == 0:
                return
        except TclError:
            return
        if self._t4_preview_scheduled:
            return
        self._t4_preview_scheduled = True
        self._t4_after_id = self.after(200, self._t4_preview_refresh_tick)

    def _t4_preview_refresh_tick(self) -> None:
        self._t4_preview_scheduled = False
        self._t4_after_id = None
        if not hasattr(self, "_t4_preview"):
            return
        try:
            if int(self._t4_preview.winfo_exists()) == 0:
                return
        except TclError:
            return
        self._t4_refresh_preview()

    def _t4_load_csv(self) -> None:
        self._cancel_t4_filter_ui_after()
        path = self._t4_csv.get().strip()
        if not path or not Path(path).is_file():
            self._log(self._tr("log.t4_need_csv"))
            return
        try:
            self._t4_rows, sniffed = read_rename_csv(Path(path))
        except OSError as e:
            self._log(self._tr("log.t4_read_fail", e=e))
            return
        self._log(
            self._tr(
                "log.t4_loaded",
                n=len(self._t4_rows),
                path=path,
                sniff=sniffed,
            )
        )
        self.after(1, self._t4_finish_csv_load)

    def _t4_finish_csv_load(self) -> None:
        if not hasattr(self, "_t4_tree"):
            return
        self._t4_rebuild_tree()
        self._t4_refresh_preview()
        self._save_settings()

    def _t4_export_csv(self) -> None:
        if not self._t4_rows:
            self._log(self._tr("log.t4_export_empty"))
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title=self._tr("dlg.export_t4"),
        )
        if not path:
            return
        try:
            write_rename_csv(Path(path), self._t4_rows, self._app_csv_delim())
            self._log(self._tr("log.t4_exported", n=len(self._t4_rows), path=path))
        except OSError as e:
            self._log(self._tr("log.t4_export_fail", e=e))
        self._save_settings()

    def _t4_refresh_preview(self) -> None:
        if not hasattr(self, "_t4_preview"):
            return
        try:
            if int(self._t4_preview.winfo_exists()) == 0:
                return
        except TclError:
            return
        n = len(self._t4_rows)
        filtered = self._t4_filtered_indices()
        sel = self._t4_selected_indices()
        self._t4_stats.configure(
            text=self._tr("log.t4_stats", n=n, f=len(filtered), s=len(sel)),
        )
        ft = self._t4_target_folder.get().strip()
        sub = self._t4_subfolder.get()
        lines: list[str] = []
        if self._t4_is_per_source_mode():
            sub_ok = sanitize_windows_dir_component(sub)
            if not sub_ok:
                lines.append(self._tr("log.t4_preview_nextto"))
            else:
                lines.append(self._tr("log.t4_preview_mode_line", sub=sub_ok))
                lines.append("")
                cap = 200
                for i in filtered[:cap]:
                    row = self._t4_rows[i]
                    fp = (row.get("file_path") or "").strip()
                    if not fp:
                        lines.append(self._tr("log.t4_empty_path_csv"))
                        lines.append("")
                        continue
                    resolved = resolve_csv_path_to_existing_file(fp)
                    src = resolved if resolved else Path(fp)
                    old_show = str(src) if resolved else self._tr("log.t4_name_only", fp=fp)
                    leaf_name = (row.get("file_name") or "").strip() or src.name
                    target_dir = src.parent / sub_ok
                    try:
                        leaf = unique_leaf_in_dir(target_dir, leaf_name)
                        dest = target_dir / leaf
                    except OSError as e:
                        lines.append(f"{old_show}")
                        lines.append(self._tr("log.t4_preview_arrow_err", e=e))
                    else:
                        lines.append(f"{old_show}")
                        lines.append(f"  -> {dest}")
                    lines.append("")
                if len(filtered) > cap:
                    lines.append(self._tr("log.t4_more_items", n=len(filtered) - cap))
        else:
            if not ft:
                lines.append(self._tr("log.t4_preview_set_move"))
                root_p = None
            else:
                root_p, err = resolve_move_destination_root(ft, sub)
                if err or root_p is None:
                    lines.append(err or self._tr("log.t4_invalid_target"))
                else:
                    lines.append(self._tr("log.t4_dest_root", root=root_p))
                    lines.append("")
                    cap = 200
                    for i in filtered[:cap]:
                        row = self._t4_rows[i]
                        fp = (row.get("file_path") or "").strip()
                        name = (row.get("file_name") or "").strip() or (Path(fp).name if fp else "")
                        if not fp:
                            lines.append(self._tr("log.t4_empty_path_csv"))
                            lines.append("")
                            continue
                        resolved = resolve_csv_path_to_existing_file(fp)
                        old_show = str(resolved) if resolved else self._tr("log.t4_name_only", fp=fp)
                        leaf_name = name or Path(fp).name
                        try:
                            leaf = unique_leaf_in_dir(root_p, leaf_name)
                            dest = root_p / leaf
                        except OSError as e:
                            lines.append(f"{old_show}")
                            lines.append(self._tr("log.t4_preview_arrow_err", e=e))
                        else:
                            lines.append(f"{old_show}")
                            lines.append(f"  -> {dest}")
                        lines.append("")
                    if len(filtered) > cap:
                        lines.append(self._tr("log.t4_more_items", n=len(filtered) - cap))

        text = "\n".join(lines).strip() + "\n"
        self._t4_preview.configure(state="normal")
        self._t4_preview.delete("1.0", "end")
        self._t4_preview.insert("1.0", text)
        self._t4_preview.configure(state="disabled")
        if hasattr(self, "_t4_plan"):
            source_mode = (
                self._tr("plan.source.selected")
                if self._t4_use_selected.get()
                else self._tr("plan.source.all_search")
            )
            run_mode = self._tr("plan.run.preview") if self._t4_dry.get() else self._tr("plan.run.real")
            place_mode = (
                self._tr("plan.place.next") if self._t4_is_per_source_mode() else self._tr("plan.place.one")
            )
            self._t4_plan.configure(
                text=self._tr(
                    "log.t4_plan",
                    run=run_mode,
                    source=source_mode,
                    place=place_mode,
                )
            )

    def _t3_load_csv(self) -> None:
        self._cancel_t3_filter_rebuild_after()
        path = self._t3_csv.get().strip()
        if not path or not Path(path).is_file():
            self._log(self._tr("log.t3_need_csv"))
            return
        try:
            self._rows, sniffed = read_rename_csv(Path(path))
        except OSError as e:
            self._log(self._tr("log.csv_read_fail", e=e))
            return
        self._log(
            self._tr("log.t3_loaded", n=len(self._rows), path=path, sniff=sniffed),
        )
        self.after(1, self._t3_finish_csv_load)

    def _t3_finish_csv_load(self) -> None:
        if not hasattr(self, "_tree"):
            return
        self._t3_rebuild_tree()
        self._t4_schedule_preview_refresh()
        self._save_settings()

    def _t3_save_csv(self) -> None:
        path = self._t3_csv.get().strip()
        if not path:
            path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
            if not path:
                return
            self._t3_csv.set(path)
        try:
            write_rename_csv(Path(path), self._rows, self._app_csv_delim())
            self._log(self._tr("log.t3_saved", n=len(self._rows), path=path))
        except OSError as e:
            self._log(self._tr("log.save_failed", e=e))

    def _t3_row_visible(self, row: dict[str, str]) -> bool:
        inc = compose_ui_list_filter(
            self._t3_filter.get(),
            self._t3_filter_field.get(),
            self._t3_filter_combine.get(),
        )
        exc = compose_ui_list_filter(
            self._t3_filter_exclude.get(),
            self._t3_filter_exclude_field.get(),
            self._t3_filter_exclude_combine.get(),
        )
        return row_passes_list_filters(
            inc,
            exc,
            file_path=row.get("file_path", ""),
            file_name=row.get("file_name", ""),
            file_extension=leaf_extension_from_row(row),
            new_leaf=row.get("new_leaf", ""),
            scene_title=row.get("scene_title", ""),
            scene_tags=row.get("scene_tags", ""),
            scene_markers=row.get("scene_markers", ""),
            scene_id=row.get("scene_id", ""),
            scene_date=row.get("scene_date", ""),
            proposed_leaf="",
        )

    def _t3_rebuild_tree(self) -> None:
        prev = self._t3_selected_indices()
        visible = [i for i, row in enumerate(self._rows) if self._t3_row_visible(row)]
        visible.sort(
            key=lambda idx: self._t3_sort_key(self._rows[idx], self._t3_sort_col),
            reverse=self._t3_sort_desc,
        )
        rows_out: list[tuple[str, tuple[object, ...]]] = []
        for i in visible:
            row = self._rows[i]
            rows_out.append(
                (
                    str(i),
                    (
                        row.get("file_path", ""),
                        "",
                        row.get("file_name", ""),
                        "",
                        leaf_extension_from_row(row),
                        "",
                        row.get("new_leaf", ""),
                    ),
                )
            )
        self._ttk_tree_replace_rows(self._tree, rows_out)
        self._ttk_restore_row_selection(self._tree, prev)

    def _t3_selected_indices(self) -> list[int]:
        out: list[int] = []
        for iid in self._tree.selection():
            try:
                out.append(int(iid))
            except ValueError:
                continue
        return out

    def _t3_restore_selection(self, indices: list[int]) -> None:
        self._ttk_restore_row_selection(self._tree, indices)

    def _t3_on_select(self, _evt=None) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        focus = self._tree.focus()
        iid = focus if focus and focus in sel else sel[-1]
        try:
            i = int(iid)
            self._t3_edit_leaf.set(self._rows[i].get("new_leaf", ""))
        except (ValueError, IndexError):
            pass

    def _t3_focus_edit_leaf(self) -> None:
        self._t3_on_select()

    def _t3_selected_file_path(self) -> str:
        sel = self._tree.selection()
        if not sel:
            return ""
        try:
            i = int(sel[0])
            return (self._rows[i].get("file_path") or "").strip()
        except (ValueError, IndexError):
            return ""

    def _t3_selected_folder_path(self) -> str:
        """Directory containing the file (CSV file_directory, else parent of file_path)."""
        sel = self._tree.selection()
        if not sel:
            return ""
        try:
            i = int(sel[0])
            row = self._rows[i]
        except (ValueError, IndexError):
            return ""
        fp = (row.get("file_path") or "").strip()
        if not fp:
            return ""
        d = (row.get("file_directory") or "").strip()
        if d:
            return d
        try:
            return str(Path(fp).expanduser().resolve(strict=False).parent)
        except OSError:
            return str(Path(fp).parent)

    def _t3_copy_selected_path(self) -> None:
        folder = self._t3_selected_folder_path()
        if not folder:
            self._log(self._tr("log.select_item_path"))
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(folder)
            self.update()
        except TclError:
            self._log(self._tr("log.clipboard_fail"))
            return
        self._log(self._tr("log.copied_path"))

    def _t3_selected_primary_leaf(self) -> str:
        """Displayed / CSV file name for the first selected Tab 3 row (leaf only, no path)."""
        idxs = self._t3_selected_indices()
        if not idxs:
            return ""
        i = idxs[0]
        if i < 0 or i >= len(self._rows):
            return ""
        row = self._rows[i]
        fn = (row.get("file_name") or "").strip()
        if fn:
            return fn
        fp = (row.get("file_path") or "").strip()
        return Path(fp).name if fp else ""

    def _t3_ph_entry_assign(self, ent: ctk.CTkEntry | None, var: ctk.StringVar, text: str, *, strip: bool) -> None:
        """Write text into a placeholder-style CTkEntry and its StringVar (Find / Replace fields)."""
        s = text.strip() if strip else text
        var.set(s)
        if ent is None:
            return
        try:
            if not int(ent.winfo_exists()):
                return
            ent.delete(0, "end")
            if s:
                ent.insert(0, s)
        except TclError:
            pass

    def _t3_copy_selected_file_name(self) -> None:
        name = self._t3_selected_primary_leaf()
        if not name:
            self._log(self._tr("log.select_item"))
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(name)
            self.update()
        except TclError:
            self._log(self._tr("log.clipboard_fail"))
            return
        self._log(self._tr("log.copied_file_name"))

    def _t3_copy_selected_file_stem(self) -> None:
        leaf = self._t3_selected_primary_leaf()
        if not leaf:
            self._log(self._tr("log.select_item"))
            return
        stem = Path(leaf).stem
        if not stem:
            self._log(self._tr("log.empty_stem"))
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(stem)
            self.update()
        except TclError:
            self._log(self._tr("log.clipboard_fail"))
            return
        self._log(self._tr("log.copied_file_stem"))

    def _t3_copy_selected_extension(self) -> None:
        name = self._t3_selected_primary_leaf()
        if not name:
            self._log(self._tr("log.select_item"))
            return
        ext = Path(name).suffix
        if not ext:
            self._log(self._tr("log.no_extension"))
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(ext)
            self.update()
        except TclError:
            self._log(self._tr("log.clipboard_fail"))
            return
        self._log(self._tr("log.copied_extension"))

    def _t3_put_selected_name_in_find(self) -> None:
        leaf = self._t3_selected_primary_leaf()
        if not leaf:
            self._log(self._tr("log.select_item"))
            return
        stem = Path(leaf).stem
        if not stem:
            self._log(self._tr("log.empty_stem"))
            return
        self._t3_ph_entry_assign(getattr(self, "_t3_find_entry", None), self._t3_find, stem, strip=False)
        self._save_settings()

    def _t3_put_selected_name_in_replace(self) -> None:
        leaf = self._t3_selected_primary_leaf()
        if not leaf:
            self._log(self._tr("log.select_item"))
            return
        stem = Path(leaf).stem
        if not stem:
            self._log(self._tr("log.empty_stem"))
            return
        self._t3_ph_entry_assign(getattr(self, "_t3_replace_entry", None), self._t3_replace, stem, strip=False)
        self._save_settings()

    def _open_path_in_file_manager(self, fp: str) -> None:
        """Open folder or reveal file in Explorer / Finder / xdg-open (same rules as Tab 3)."""
        p = Path((fp or "").strip()).expanduser()
        try:
            rp = p.resolve(strict=False)
        except OSError:
            rp = p
        if sys.platform == "win32":
            if rp.is_file():
                ep = os.path.normpath(str(rp))
                if '"' in ep:
                    self._log(self._tr("log.path_semicolon"))
                    if rp.parent.is_dir():
                        subprocess.Popen(f'explorer "{rp.parent}"', shell=True)
                    return
                subprocess.run(f'explorer /select,"{ep}"', shell=True, check=False)
            elif rp.is_dir():
                os.startfile(str(rp))  # type: ignore[attr-defined]
            elif rp.parent.is_dir():
                subprocess.Popen(f'explorer "{os.path.normpath(str(rp.parent))}"', shell=True)
            else:
                self._log(self._tr("log.path_not_found", fp=fp))
        elif sys.platform == "darwin":
            if rp.is_file():
                subprocess.run(["open", "-R", str(rp)], check=False)
            elif rp.is_dir():
                subprocess.run(["open", str(rp)], check=False)
            elif rp.parent.is_dir():
                subprocess.run(["open", str(rp.parent)], check=False)
            else:
                self._log(self._tr("log.path_not_found", fp=fp))
        else:
            if rp.is_dir():
                subprocess.run(["xdg-open", str(rp)], check=False)
            elif rp.parent.is_dir():
                subprocess.run(["xdg-open", str(rp.parent)], check=False)
            else:
                self._log(self._tr("log.path_not_found", fp=fp))

    def _t3_open_selected_path(self) -> None:
        fp = self._t3_selected_file_path()
        if not fp:
            self._log(self._tr("log.select_item"))
            return
        self._open_path_in_file_manager(fp)

    def _t4_selected_file_path(self) -> str:
        sel = self._t4_tree.selection()
        if not sel:
            return ""
        try:
            i = int(sel[0])
            return (self._t4_rows[i].get("file_path") or "").strip()
        except (ValueError, IndexError):
            return ""

    def _t4_open_selected_in_explorer(self) -> None:
        fp = self._t4_selected_file_path()
        if not fp:
            self._log(self._tr("log.select_item"))
            return
        self._open_path_in_file_manager(fp)

    def _t4_copy_selected_folder_path(self) -> None:
        fp = self._t4_selected_file_path()
        if not fp:
            self._log(self._tr("log.select_item_path"))
            return
        try:
            folder = str(Path(fp).expanduser().resolve(strict=False).parent)
        except OSError:
            folder = str(Path(fp).parent)
        if not folder:
            self._log(self._tr("log.select_item_path"))
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(folder)
            self.update()
        except TclError:
            self._log(self._tr("log.clipboard_fail"))
            return
        self._log(self._tr("log.copied_path"))

    def _t4_tree_context_menu(self, event) -> None:
        row_id = self._t4_tree.identify_row(event.y)
        if row_id:
            self._t4_tree.selection_set(row_id)
            self._t4_tree.focus(row_id)
        menu = Menu(self, tearoff=0)
        menu.add_command(label=self._tr("ctx.copy_folder_path"), command=self._t4_copy_selected_folder_path)
        menu.add_command(label=self._tr("ctx.open_in_explorer"), command=self._t4_open_selected_in_explorer)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _t5_selected_file_path(self) -> str:
        sel = self._t5_tree.selection()
        if not sel:
            return ""
        try:
            i = int(sel[0])
            return (self._t5_rows[i].get("file_path") or "").strip()
        except (ValueError, IndexError):
            return ""

    def _t5_open_selected_in_explorer(self) -> None:
        fp = self._t5_selected_file_path()
        if not fp:
            self._log(self._tr("log.select_item"))
            return
        self._open_path_in_file_manager(fp)

    def _t5_copy_selected_folder_path(self) -> None:
        fp = self._t5_selected_file_path()
        if not fp:
            self._log(self._tr("log.select_item_path"))
            return
        try:
            folder = str(Path(fp).expanduser().resolve(strict=False).parent)
        except OSError:
            folder = str(Path(fp).parent)
        if not folder:
            self._log(self._tr("log.select_item_path"))
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(folder)
            self.update()
        except TclError:
            self._log(self._tr("log.clipboard_fail"))
            return
        self._log(self._tr("log.copied_path"))

    def _t5_tree_context_menu(self, event) -> None:
        row_id = self._t5_tree.identify_row(event.y)
        if row_id:
            self._t5_tree.selection_set(row_id)
            self._t5_tree.focus(row_id)
        menu = Menu(self, tearoff=0)
        menu.add_command(label=self._tr("ctx.copy_folder_path"), command=self._t5_copy_selected_folder_path)
        menu.add_command(label=self._tr("ctx.open_in_explorer"), command=self._t5_open_selected_in_explorer)
        menu.add_command(label=self._tr("ctx.open_in_stash"), command=self._t5_open_selected_in_stash)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _t5_stash_scene_url(self, scene_id: str) -> str:
        """Stash web UI scene page (same host as Tab 1 «Stash URL»)."""
        sid = (scene_id or "").strip()
        if not sid:
            return ""
        base = (self._t1_url.get() or "").strip().rstrip("/") or "http://127.0.0.1:9999"
        return urljoin(base + "/", f"scenes/{sid}")

    def _t5_open_selected_in_stash(self) -> None:
        idxs = self._t5_selected_indices()
        if not idxs:
            self._log(self._tr("log.select_item"))
            return
        sid = ""
        for i in idxs:
            if 0 <= i < len(self._t5_rows):
                cand = (self._t5_rows[i].get("scene_id") or "").strip()
                if cand:
                    sid = cand
                    break
        if not sid:
            self._log(self._tr("log.t5_stash_need_scene_id"))
            return
        url = self._t5_stash_scene_url(sid)
        try:
            ok = webbrowser.open(url)
        except Exception as e:
            self._log(self._tr("log.t5_open_stash_fail", e=e))
            return
        if not ok:
            self._log(self._tr("log.t5_open_stash_fail_browser"))
            return
        self._log(self._tr("log.t5_open_stash", url=url))

    def _t3_tree_context_menu(self, event) -> None:
        row_id = self._tree.identify_row(event.y)
        if row_id:
            self._tree.selection_set(row_id)
            self._tree.focus(row_id)
        menu = Menu(self, tearoff=0)
        menu.add_command(label=self._tr("ctx.copy_folder_path"), command=self._t3_copy_selected_path)
        menu.add_command(label=self._tr("ctx.copy_file_name"), command=self._t3_copy_selected_file_name)
        menu.add_command(label=self._tr("ctx.copy_file_stem"), command=self._t3_copy_selected_file_stem)
        menu.add_command(label=self._tr("ctx.copy_extension"), command=self._t3_copy_selected_extension)
        menu.add_separator()
        menu.add_command(label=self._tr("ctx.t3_name_to_find"), command=self._t3_put_selected_name_in_find)
        menu.add_command(label=self._tr("ctx.t3_name_to_replace"), command=self._t3_put_selected_name_in_replace)
        menu.add_separator()
        menu.add_command(label=self._tr("ctx.open_in_explorer"), command=self._t3_open_selected_path)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _t3_note_rename_scope_after_batch(self, *, selected_scope: bool) -> None:
        """Align «Rename on disk: selected rows only» with the last batch action (search vs selection)."""
        self._t3_rename_selected_only.set(selected_scope)

    def _t3_disambiguate_new_leaves(self) -> None:
        n_ext, n_dis = disambiguate_new_leaves_among_rows(self._rows)
        if n_ext:
            self._log(self._tr("log.t3_ext_inherited", n=n_ext))
        if n_dis:
            self._log(self._tr("log.t3_disambiguate", n=n_dis))

    def _t3_apply_leaf_selection(self) -> None:
        sel_idx = self._t3_selected_indices()
        if not sel_idx:
            self._log(self._tr("log.select_item"))
            return
        val = self._t3_edit_leaf.get().strip()
        for i in sel_idx:
            if 0 <= i < len(self._rows):
                self._rows[i]["new_leaf"] = val
        self._t3_disambiguate_new_leaves()
        self._t3_note_rename_scope_after_batch(selected_scope=True)
        self._t3_rebuild_tree()
        self._t3_restore_selection(sel_idx)
        self._save_settings()

    def _t3_apply_rule_filtered(self) -> None:
        prefix = self._t3_prefix.get()
        suffix = self._t3_suffix.get()
        if "\\" in prefix or "/" in prefix or "\\" in suffix or "/" in suffix:
            self._log(self._tr("log.prefix_sep"))
            return
        indices: list[int] = []
        for item in self._tree.get_children():
            try:
                indices.append(int(item))
            except ValueError:
                continue
        apply_prefix_suffix_to_rows(self._rows, indices, prefix=prefix, suffix_before_ext=suffix)
        self._log(self._tr("log.applied_prefix_search", n=len(indices)))
        self._t3_disambiguate_new_leaves()
        self._t3_note_rename_scope_after_batch(selected_scope=False)
        self._t3_rebuild_tree()
        self._save_settings()

    def _t3_apply_rule_selected(self) -> None:
        prefix = self._t3_prefix.get()
        suffix = self._t3_suffix.get()
        if "\\" in prefix or "/" in prefix or "\\" in suffix or "/" in suffix:
            self._log(self._tr("log.prefix_sep"))
            return
        indices = self._t3_selected_indices()
        if not indices:
            self._log(self._tr("log.select_multi"))
            return
        apply_prefix_suffix_to_rows(self._rows, indices, prefix=prefix, suffix_before_ext=suffix)
        self._log(self._tr("log.applied_prefix_sel", n=len(indices)))
        self._t3_disambiguate_new_leaves()
        self._t3_note_rename_scope_after_batch(selected_scope=True)
        self._t3_rebuild_tree()
        self._t3_restore_selection(indices)
        self._save_settings()

    def _ctk_ph_entry_value(self, ent: ctk.CTkEntry | None, var: ctk.StringVar, *, strip: bool = True) -> str:
        """
        Reliable text from a CTkEntry used with ``placeholder_text`` but **without** ``textvariable``.

        ``CTkEntry.get()`` returns ``\"\"`` while the grey placeholder is active, even though the
        underlying ``tkinter.Entry`` still holds the placeholder string — so we read the inner
        entry and treat a value equal to ``placeholder_text`` as empty.
        """
        def _finish(s: str) -> str:
            return s.strip() if strip else s

        if ent is None:
            return _finish(var.get() or "")
        try:
            if not int(ent.winfo_exists()):
                return _finish(var.get() or "")
        except (TclError, ValueError):
            return _finish(var.get() or "")
        inner = getattr(ent, "_entry", None)
        if inner is None:
            return _finish(ent.get() or var.get() or "")
        try:
            raw = inner.get()
        except TclError:
            return _finish(var.get() or "")
        ph = ent.cget("placeholder_text")
        if ph is not None and raw == ph:
            return ""
        return _finish(raw)

    def _t3_sync_find_replace_entries(self) -> None:
        """Flush pending UI events, then copy Find/Replace widget text into StringVars."""
        try:
            self.update_idletasks()
        except TclError:
            pass
        self._t3_find.set(self._ctk_ph_entry_value(getattr(self, "_t3_find_entry", None), self._t3_find, strip=False))
        self._t3_replace.set(
            self._ctk_ph_entry_value(getattr(self, "_t3_replace_entry", None), self._t3_replace, strip=False)
        )

    def _t3_apply_find_replace_filtered(self) -> None:
        self._t3_sync_find_replace_entries()
        find = self._t3_find.get()
        if not find.strip():
            self._log(self._tr("log.fr_find_empty"))
            return
        replace_with = self._t3_replace.get()
        if "\\" in replace_with or "/" in replace_with or ":" in replace_with:
            self._log(self._tr("log.fr_replace_invalid"))
            return
        indices: list[int] = []
        for item in self._tree.get_children():
            try:
                indices.append(int(item))
            except ValueError:
                continue
        if not indices:
            self._log(self._tr("log.no_items_list"))
            return
        ci = self._t3_replace_ci.get()
        updated, skipped, warns = apply_find_replace_to_rows(
            self._rows,
            indices,
            find=find,
            replace_with=replace_with,
            case_insensitive=ci,
        )
        for w in warns:
            self._log(w + "\n")
        skip_part = self._tr("log.skip_invalid_suffix", n=skipped) if skipped else ""
        self._log(
            self._tr("log.fr_applied_search", u=updated, skip=skip_part),
        )
        if updated == 0 and skipped == 0 and indices:
            self._log(self._tr("log.fr_zero_hits"))
        self._t3_disambiguate_new_leaves()
        self._t3_note_rename_scope_after_batch(selected_scope=False)
        self._t3_rebuild_tree()
        self._save_settings()

    def _t3_apply_find_replace_selected(self) -> None:
        self._t3_sync_find_replace_entries()
        find = self._t3_find.get()
        if not find.strip():
            self._log(self._tr("log.fr_find_empty"))
            return
        replace_with = self._t3_replace.get()
        if "\\" in replace_with or "/" in replace_with or ":" in replace_with:
            self._log(self._tr("log.fr_replace_invalid"))
            return
        indices = self._t3_selected_indices()
        if not indices:
            self._log(self._tr("log.select_multi"))
            return
        ci = self._t3_replace_ci.get()
        updated, skipped, warns = apply_find_replace_to_rows(
            self._rows,
            indices,
            find=find,
            replace_with=replace_with,
            case_insensitive=ci,
        )
        for w in warns:
            self._log(w + "\n")
        skip_part = self._tr("log.skip_invalid_suffix", n=skipped) if skipped else ""
        self._log(
            self._tr("log.fr_applied_sel", u=updated, skip=skip_part),
        )
        if updated == 0 and skipped == 0 and indices:
            self._log(self._tr("log.fr_zero_hits"))
        self._t3_disambiguate_new_leaves()
        self._t3_note_rename_scope_after_batch(selected_scope=True)
        self._t3_rebuild_tree()
        self._t3_restore_selection(indices)
        self._save_settings()

    def _t3_clear_filtered_leaves(self) -> None:
        for item in self._tree.get_children():
            try:
                i = int(item)
                self._rows[i]["new_leaf"] = ""
            except (ValueError, IndexError):
                continue
        self._t3_rebuild_tree()
        self._log(self._tr("log.cleared_new_names"))

    def _t3_run_renames(self) -> None:
        if not self._rows:
            self._log(self._tr("log.load_csv_first"))
            return
        try:
            self.update_idletasks()
        except TclError:
            pass
        only = self._t3_only_under.get().strip() or None
        dry = self._t3_dry.get()
        only_idx: list[int] | None = None
        if self._t3_rename_selected_only.get():
            only_idx = self._t3_selected_indices()
            if not only_idx:
                self._log(self._tr("log.t3_rename_need_selection"))
                return
        undo_rec: list[tuple[int, str, str, str]] = []
        try:
            renamed, skipped, lines = apply_file_renames(
                self._rows,
                only_under_folder=only,
                only_indices=only_idx,
                dry_run=dry,
                keep_alive=self._tk_keepalive,
                keep_alive_every=35,
                progress=self._work_progress_rename,
                undo_stack=undo_rec,
            )
            self._log_many_lines(lines)
            self._log(
                self._tr(
                    "log.t3_rename_done",
                    preview=self._tr("log.preview_prefix") if dry else "",
                    renamed=renamed,
                    skipped=skipped,
                ),
            )
            self._t3_rebuild_tree()
            self._save_settings()
            if not dry and renamed > 0 and undo_rec:
                self._register_rename_undo_stack("t3", undo_rec)
        finally:
            self._clear_work_progress()

    def _t3_run_folder_rename(self) -> None:
        if not self._t3_fold_confirm.get():
            self._log(self._tr("log.fold_confirm_first"))
            return
        src = self._t3_fold_src.get().strip()
        new_name = self._t3_fold_new.get().strip()
        if not src or not new_name:
            self._log(self._tr("log.fold_need_values"))
            return
        old_p = Path(src)
        ok, msg = rename_folder_dangerous(old_p, new_name)
        self._log(self._tr("log.fold_result", msg=msg))
        if ok:
            self._t3_fold_confirm.set(False)
        self._save_settings()

    def _t4_run_move_only_indices(self, indices: list[int], mode_label: str) -> None:
        try:
            self.update_idletasks()
        except TclError:
            pass
        if not self._t4_rows:
            self._log(self._tr("log.t4_load_first"))
            return
        if not indices:
            self._log(self._tr("log.t4_no_items_mode", mode=mode_label))
            return
        target = self._t4_target_folder.get().strip()
        per_source = self._t4_is_per_source_mode()
        if not per_source:
            if not target:
                self._log(self._tr("log.t4_need_dest"))
                return
            if not Path(target).is_absolute():
                self._log(self._tr("log.t4_dest_absolute", target=target))
                return
        dry = self._t4_dry.get()
        self._log(self._tr("log.t4_move_only_header", mode=mode_label))
        undo_rec: list[tuple[int, str, str, str]] = []
        try:
            moved, skipped, lines = move_files_only(
                self._t4_rows,
                indices,
                target_folder=target,
                subfolder=self._t4_subfolder.get(),
                dry_run=dry,
                per_source_subfolder=per_source,
                keep_alive=self._tk_keepalive,
                keep_alive_every=35,
                progress=self._work_progress_move,
                undo_stack=undo_rec,
            )
            self._log_many_lines(lines)
            self._log(
                self._tr(
                    "log.t4_move_only_done",
                    preview=self._tr("log.preview_prefix") if dry else "",
                    moved=moved,
                    skipped=skipped,
                ),
            )
            self._t4_rebuild_tree()
            self._t4_refresh_preview()
            self._save_settings()
            if not dry and moved > 0 and undo_rec:
                self._register_rename_undo_stack("t4", undo_rec)
        finally:
            self._clear_work_progress()

    def _t4_execute_move(self) -> None:
        use_selected = self._t4_use_selected.get()
        indices = self._t4_selected_indices() if use_selected else self._t4_filtered_indices()
        label = self._tr("mode.selected_items") if use_selected else self._tr("mode.search_matches")
        self._t4_run_move_only_indices(indices, label)

    def _test_stash_connection(self) -> None:
        stash_url = self._t1_url.get().strip() or "http://127.0.0.1:9999"
        api_key = self._t1_api.get().strip()
        gql = self._t1_graphql_path.get().strip() or "/graphql"
        self._log(self._tr("log.test_stash", url=stash_url, gql=gql))
        ok, msg = test_stash_graphql_connection(stash_url, api_key, graphql_path=gql)
        self._log(self._tr("log.ok_prefix" if ok else "log.fail_prefix") + msg + "\n")

    def _probe_stash_csv_export(self) -> None:
        stash_url = self._t1_url.get().strip() or "http://127.0.0.1:9999"
        api_key = self._t1_api.get().strip()
        gql = self._t1_graphql_path.get().strip() or "/graphql"
        self._log(self._tr("log.probe_csv_export", url=stash_url, gql=gql))
        csv_ok, csv_detail = probe_stash_csv_export_schema(stash_url, api_key, graphql_path=gql)
        self._log(
            self._tr(
                "log.export_line_ok" if csv_ok else "log.export_line_fail",
                detail=csv_detail,
            )
            + "\n"
        )

    def _open_t5_schema_help_dialog(self) -> None:
        if self._t5_help_dialog is not None:
            try:
                if self._t5_help_dialog.winfo_exists():
                    self._t5_help_dialog.focus()
                    return
            except TclError:
                pass
            self._t5_help_dialog = None

        top = ctk.CTkToplevel(self, fg_color=self._pal["bg"])
        self._t5_help_dialog = top
        top.title(self._tr("t5.help.window_title"))
        top.geometry("560x640")
        top.minsize(440, 420)
        top.transient(self)
        top.grab_set()

        pad = {"padx": 14, "pady": (8, 6)}
        outer = ctk.CTkScrollableFrame(
            top,
            fg_color=self._pal["panel"],
            scrollbar_fg_color=self._pal["panel_elev"],
            scrollbar_button_color=self._pal["border"],
            scrollbar_button_hover_color=self._pal["cyan_dim"],
        )
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        self._label(
            outer,
            text=self._tr("t5.help.intro"),
            anchor="w",
            justify="left",
            wraplength=480,
            font=FONT_UI_SM,
            fg_color=self._pal["panel"],
        ).pack(fill="x", **pad)

        def section(title_key: str, body_key: str) -> None:
            self._label(outer, text=self._tr(title_key), anchor="w", font=FONT_SECTION, fg_color=self._pal["panel"]).pack(
                fill="x", **pad
            )
            self._label(
                outer,
                text=self._tr(body_key),
                anchor="w",
                justify="left",
                wraplength=480,
                text_color=self._pal["muted"],
                font=FONT_HINT,
                fg_color=self._pal["panel"],
            ).pack(fill="x", padx=14, pady=(0, 10))

        section("t5.help.heading_modes", "t5.name_mode_hint")
        section("t5.help.heading_protect", "t5.preserve_tags_hint")
        section("t5.help.heading_tags", "t5.tag_structure_hint")
        section("t5.help.heading_metadata", "t5.help.body_metadata")

        btns = ctk.CTkFrame(top, fg_color=self._pal["bg"])
        btns.pack(fill="x", padx=14, pady=(0, 12))

        def on_close() -> None:
            try:
                top.grab_release()
            except TclError:
                pass
            top.destroy()
            self._t5_help_dialog = None

        ok_t = self._tr("common.ok")
        ctk.CTkButton(
            btns,
            text=ok_t,
            width=_btn_w(ok_t, lo=52),
            command=on_close,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="right")
        top.protocol("WM_DELETE_WINDOW", on_close)

    def _open_settings_dialog(self) -> None:
        if self._settings_dialog is not None:
            try:
                if self._settings_dialog.winfo_exists():
                    self._settings_dialog.focus()
                    return
            except TclError:
                pass
            self._settings_dialog = None

        top = ctk.CTkToplevel(self, fg_color=self._pal["bg"])
        self._settings_dialog = top
        top.title(self._tr("settings.title"))
        top.geometry("520x640")
        top.minsize(440, 520)
        top.transient(self)
        top.grab_set()

        pad = {"padx": 14, "pady": (8, 6)}
        outer = ctk.CTkScrollableFrame(
            top,
            fg_color=self._pal["panel"],
            scrollbar_fg_color=self._pal["panel_elev"],
            scrollbar_button_color=self._pal["border"],
            scrollbar_button_hover_color=self._pal["cyan_dim"],
        )
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        self._label(
            outer,
            text=self._tr("settings.intro"),
            anchor="w",
            font=FONT_SECTION,
        ).pack(fill="x", **pad)

        appearance = ctk.StringVar(value=self._appearance_mode.get())
        delim = ctk.StringVar(value=self._t1_delim.get())
        ps1 = ctk.StringVar(value=self._t1_ps1.get())
        url = ctk.StringVar(value=self._t1_url.get())
        api = ctk.StringVar(value=self._t1_api.get())
        gql = ctk.StringVar(value=self._t1_graphql_path.get())
        lang_choice = ctk.StringVar(value=self._norm_lang_code(self._ui_language.get()))

        self._label(outer, text=self._tr("settings.language"), anchor="w", font=FONT_SECTION).pack(
            fill="x", **pad
        )
        ctk.CTkSegmentedButton(
            outer,
            values=["en", "de", "es", "fr"],
            variable=lang_choice,
            font=FONT_UI_SM,
            fg_color=self._pal["panel_elev"],
            selected_color=self._pal["cyan_dim"],
            selected_hover_color=self._pal["cyan"],
            unselected_color=self._pal["panel_elev"],
            unselected_hover_color=self._pal["border"],
            text_color=self._pal["text"],
        ).pack(anchor="w", padx=14, pady=(0, 4))
        self._label(
            outer,
            text=self._tr("settings.language_hint"),
            anchor="w",
            wraplength=400,
            justify="left",
            text_color=self._pal["muted"],
            font=FONT_HINT,
        ).pack(fill="x", padx=14, pady=(0, 8))

        self._label(outer, text=self._tr("settings.appearance"), anchor="w", font=FONT_SECTION).pack(
            fill="x", **pad
        )
        ctk.CTkSegmentedButton(
            outer,
            values=["dark", "light", "system"],
            variable=appearance,
            font=FONT_UI_SM,
            fg_color=self._pal["panel_elev"],
            selected_color=self._pal["cyan_dim"],
            selected_hover_color=self._pal["cyan"],
            unselected_color=self._pal["panel_elev"],
            unselected_hover_color=self._pal["border"],
            text_color=self._pal["text"],
        ).pack(anchor="w", padx=14, pady=(0, 4))

        self._label(
            outer,
            text=self._tr("settings.column_sep"),
            anchor="w",
        ).pack(fill="x", **pad)
        ctk.CTkSegmentedButton(
            outer,
            values=[";", ","],
            variable=delim,
            font=FONT_UI_SM,
            fg_color=self._pal["panel_elev"],
            selected_color=self._pal["cyan_dim"],
            selected_hover_color=self._pal["cyan"],
            unselected_color=self._pal["panel_elev"],
            unselected_hover_color=self._pal["border"],
            text_color=self._pal["text"],
        ).pack(anchor="w", padx=14, pady=(0, 8))
        self._label(
            outer,
            text=self._tr("settings.csv_detect"),
            anchor="w",
            text_color=self._pal["muted"],
            font=FONT_HINT,
        ).pack(fill="x", padx=14, pady=(0, 8))

        self._label(outer, text=self._tr("settings.stash_group"), anchor="w", font=FONT_SECTION).pack(
            fill="x", **pad
        )
        self._label(
            outer,
            text=self._tr("settings.stash_hint"),
            anchor="w",
            wraplength=400,
            justify="left",
            text_color=self._pal["muted"],
            font=FONT_HINT,
        ).pack(fill="x", **pad)

        self._label(
            outer,
            text=self._tr("settings.export_script_hint"),
            anchor="w",
            wraplength=400,
            justify="left",
            text_color=self._pal["muted"],
            font=FONT_HINT,
        ).pack(fill="x", padx=14, pady=(0, 4))

        ps1_row = ctk.CTkFrame(outer, fg_color=self._pal["panel"])
        ps1_row.pack(fill="x", **pad)
        self._label(ps1_row, text=self._tr("t1.export_script"), width=200, anchor="w").pack(side="left")
        ctk.CTkEntry(ps1_row, textvariable=ps1).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            ps1_row,
            text=self._tr("common.browse"),
            width=self._browse_w,
            command=lambda: self._browse_t1_ps1_to_var(ps1),
            **self._button_kw("ghost", height=_BTN_H),
        ).pack(side="right")

        for key, var, secret in (
            ("common.stash_url", url, False),
            ("common.api_key", api, True),
            ("settings.graphql_path_label", gql, False),
        ):
            row_f = ctk.CTkFrame(outer, fg_color=self._pal["panel"])
            row_f.pack(fill="x", **pad)
            self._label(row_f, text=self._tr(key), width=200, anchor="w").pack(side="left")
            ctk.CTkEntry(row_f, textvariable=var, show="*" if secret else None).pack(
                side="left", fill="x", expand=True, padx=(0, 8)
            )

        gql_btns = ctk.CTkFrame(outer, fg_color=self._pal["panel"])
        gql_btns.pack(fill="x", padx=14, pady=(4, 8))
        gql_clear = self._tr("settings.graphql_clear")
        ctk.CTkButton(
            gql_btns,
            text=gql_clear,
            width=_btn_w(gql_clear),
            command=lambda: gql.set(""),
            **self._button_kw("ghost", height=_BTN_H),
        ).pack(side="left")

        btns = ctk.CTkFrame(top, fg_color=self._pal["bg"])
        btns.pack(fill="x", padx=14, pady=(0, 12))

        def on_ok() -> None:
            old_lang = self._norm_lang_code(self._ui_language.get())
            old_appearance = (self._appearance_mode.get() or "dark").strip().lower()
            m = (appearance.get() or "dark").strip().lower()
            if m not in ("dark", "light", "system"):
                m = "dark"
            self._appearance_mode.set(m)
            self._apply_user_appearance_setting()
            self._apply_ttk_treeview_style()

            d = delim.get().strip()
            self._t1_delim.set(d if d in (";", ",") else ";")

            self._t1_ps1.set(ps1.get())
            self._ensure_bundled_export_ps1_path()
            self._t1_url.set(url.get())
            self._t1_api.set(api.get())
            self._t1_graphql_path.set(gql.get())

            new_lang = self._norm_lang_code(lang_choice.get())
            self._ui_language.set(new_lang)

            top.grab_release()
            top.destroy()
            self._settings_dialog = None
            self._save_settings()
            self._log(self._tr("settings.saved_log"))
            if new_lang != old_lang or m != old_appearance:
                self._rebuild_main_ui()

        def on_cancel() -> None:
            top.grab_release()
            top.destroy()
            self._settings_dialog = None

        cancel_t = self._tr("common.cancel")
        ok_t = self._tr("common.ok")
        ctk.CTkButton(
            btns,
            text=cancel_t,
            width=_btn_w(cancel_t),
            command=on_cancel,
            **self._button_kw("ghost", height=_BTN_H),
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            btns,
            text=ok_t,
            width=_btn_w(ok_t, lo=52),
            command=on_ok,
            **self._button_kw("primary_emphasis", height=_BTN_H),
        ).pack(side="right")

        top.protocol("WM_DELETE_WINDOW", on_cancel)

    # --- settings ---
    def _gather_settings(self) -> dict:
        return {
            "appearance_mode": self._appearance_mode.get(),
            "t1_ps1": self._t1_ps1.get(),
            "t1_url": self._t1_url.get(),
            "t1_graphql_path": self._t1_graphql_path.get(),
            "t1_api": self._t1_api.get(),
            "t1_out": self._t1_out.get(),
            "t1_delim": self._t1_delim.get(),
            "t1_per_page": self._t1_per_page.get(),
            "t1_path_prefix": self._t1_path_prefix.get(),
            "t1_path_contains": self._t1_path_contains.get(),
            "t1_name_contains": self._t1_name_contains.get(),
            "t1_name_regex": self._t1_name_regex.get(),
            "t2_folder": self._t2_folder.get(),
            "t2_recursive": self._t2_recursive.get(),
            "t2_patterns": self._t2_patterns.get(),
            "t2_out": self._t2_out.get(),
            "t3_csv": self._t3_csv.get(),
            "t3_filter": self._t3_filter.get(),
            "t3_filter_exclude": self._t3_filter_exclude.get(),
            "t3_filter_field": self._t3_filter_field.get(),
            "t3_filter_combine": self._t3_filter_combine.get(),
            "t3_filter_exclude_field": self._t3_filter_exclude_field.get(),
            "t3_filter_exclude_combine": self._t3_filter_exclude_combine.get(),
            "t3_only_under": self._t3_only_under.get(),
            "t3_find": self._t3_find.get(),
            "t3_replace": self._t3_replace.get(),
            "t3_replace_ci": self._t3_replace_ci.get(),
            "t3_dry": self._t3_dry.get(),
            "t3_rename_selected_only": self._t3_rename_selected_only.get(),
            "t4_csv": self._t4_csv.get(),
            "t4_filter": self._t4_filter.get(),
            "t4_filter_exclude": self._t4_filter_exclude.get(),
            "t4_filter_field": self._t4_filter_field.get(),
            "t4_filter_combine": self._t4_filter_combine.get(),
            "t4_filter_exclude_field": self._t4_filter_exclude_field.get(),
            "t4_filter_exclude_combine": self._t4_filter_exclude_combine.get(),
            "t4_target_folder": self._t4_target_folder.get(),
            "t4_subfolder": self._t4_subfolder.get(),
            "t4_per_source": self._t4_per_source.get(),
            "t4_dry": self._t4_dry.get(),
            "t4_use_selected": self._t4_use_selected.get(),
            "ui_language": self._ui_language.get(),
            "t5_csv": self._t5_csv.get(),
            "t5_filter": self._t5_filter.get(),
            "t5_filter_exclude": self._t5_filter_exclude.get(),
            "t5_filter_field": self._t5_filter_field.get(),
            "t5_filter_combine": self._t5_filter_combine.get(),
            "t5_filter_exclude_field": self._t5_filter_exclude_field.get(),
            "t5_filter_exclude_combine": self._t5_filter_exclude_combine.get(),
            "t5_title_max": self._t5_title_max.get(),
            "t5_include_year": self._t5_include_year.get(),
            "t5_include_resolution": self._t5_include_resolution.get(),
            "t5_include_rating": self._t5_include_rating.get(),
            "t5_dry": self._t5_dry.get(),
            "t5_use_selected": self._t5_use_selected.get(),
            "t5_name_mode": self._t5_name_mode.get(),
            "t5_append_tags_only": self._t5_in_tags_mode(),
            "t5_preserve_tags_on_shorten": self._t5_preserve_tags_on_shorten.get(),
            "t5_tag_en": [self._t5_tag_en[i].get() for i in range(5)],
            "t5_tag_txt": [self._t5_tag_txt[i].get() for i in range(5)],
            "t5_preset_name": self._t5_preset_name.get(),
            "log_panel_collapsed": self._log_collapsed.get(),
        }

    def _ensure_bundled_export_ps1_path(self) -> None:
        """Frozen EXE ships ``export_stash_files.ps1`` under ``_MEIPASS``; settings may still hold an old dev path."""
        bundle = _resource_dir() / "export_stash_files.ps1"
        if not bundle.is_file():
            return
        cur = self._t1_ps1.get().strip()
        if cur and Path(cur).is_file():
            return
        try:
            self._t1_ps1.set(str(bundle.resolve()))
        except OSError:
            self._t1_ps1.set(str(bundle))

    def _load_settings(self) -> None:
        if not _SETTINGS_PATH.is_file():
            return
        try:
            data = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(data, dict):
            return

        def g(k: str, var: ctk.StringVar | ctk.BooleanVar) -> None:
            if k not in data:
                return
            v = data[k]
            if type(var).__name__ == "BooleanVar":
                var.set(bool(v))
            else:
                var.set(str(v) if v is not None else "")
        g("appearance_mode", self._appearance_mode)
        g("t1_ps1", self._t1_ps1)
        g("t1_url", self._t1_url)
        g("t1_graphql_path", self._t1_graphql_path)
        g("t1_api", self._t1_api)
        g("t1_out", self._t1_out)
        g("t1_delim", self._t1_delim)
        g("t1_per_page", self._t1_per_page)
        g("t1_path_prefix", self._t1_path_prefix)
        g("t1_path_contains", self._t1_path_contains)
        g("t1_name_contains", self._t1_name_contains)
        g("t1_name_regex", self._t1_name_regex)
        g("t2_folder", self._t2_folder)
        g("t2_recursive", self._t2_recursive)
        g("t2_patterns", self._t2_patterns)
        g("t2_out", self._t2_out)
        g("t3_csv", self._t3_csv)
        g("t3_filter", self._t3_filter)
        g("t3_filter_exclude", self._t3_filter_exclude)
        g("t3_filter_field", self._t3_filter_field)
        g("t3_filter_combine", self._t3_filter_combine)
        g("t3_filter_exclude_field", self._t3_filter_exclude_field)
        g("t3_filter_exclude_combine", self._t3_filter_exclude_combine)
        g("t3_only_under", self._t3_only_under)
        g("t3_find", self._t3_find)
        g("t3_replace", self._t3_replace)
        g("t3_replace_ci", self._t3_replace_ci)
        g("t3_dry", self._t3_dry)
        g("t3_rename_selected_only", self._t3_rename_selected_only)
        g("t4_csv", self._t4_csv)
        g("t4_filter", self._t4_filter)
        g("t4_filter_exclude", self._t4_filter_exclude)
        g("t4_filter_field", self._t4_filter_field)
        g("t4_filter_combine", self._t4_filter_combine)
        g("t4_filter_exclude_field", self._t4_filter_exclude_field)
        g("t4_filter_exclude_combine", self._t4_filter_exclude_combine)
        g("t4_target_folder", self._t4_target_folder)
        g("t4_subfolder", self._t4_subfolder)
        g("t4_per_source", self._t4_per_source)
        g("t4_dry", self._t4_dry)
        g("t4_use_selected", self._t4_use_selected)
        g("t5_csv", self._t5_csv)
        g("t5_filter", self._t5_filter)
        g("t5_filter_exclude", self._t5_filter_exclude)
        g("t5_filter_field", self._t5_filter_field)
        g("t5_filter_combine", self._t5_filter_combine)
        g("t5_filter_exclude_field", self._t5_filter_exclude_field)
        g("t5_filter_exclude_combine", self._t5_filter_exclude_combine)
        g("t5_title_max", self._t5_title_max)
        g("t5_include_year", self._t5_include_year)
        g("t5_include_resolution", self._t5_include_resolution)
        g("t5_include_rating", self._t5_include_rating)
        g("t5_dry", self._t5_dry)
        g("t5_use_selected", self._t5_use_selected)
        if "t5_name_mode" in data:
            g("t5_name_mode", self._t5_name_mode)
            if (self._t5_name_mode.get() or "").strip().lower() == "tags_overwrite":
                self._t5_name_mode.set("tags_replace_except_auto")
        elif "t5_append_tags_only" in data:
            if bool(data.get("t5_append_tags_only")):
                self._t5_name_mode.set("tags_append")
            else:
                self._t5_name_mode.set("full_schema")
        elif "t5_tags_only_mode" in data or "t5_tags_shorten_title" in data:
            self._t5_name_mode.set("tags_append" if bool(data.get("t5_tags_only_mode", False)) else "full_schema")
        if "t5_preserve_tags_on_shorten" in data:
            g("t5_preserve_tags_on_shorten", self._t5_preserve_tags_on_shorten)
        elif "t5_shorten_scope" in data:
            ss = data.get("t5_shorten_scope")
            if isinstance(ss, str) and ss.strip().lower() == "title_only":
                self._t5_preserve_tags_on_shorten.set(True)
            elif isinstance(ss, str) and ss.strip().lower() == "full_stem":
                self._t5_preserve_tags_on_shorten.set(False)
        g("t5_preset_name", self._t5_preset_name)
        g("log_panel_collapsed", self._log_collapsed)
        g("ui_language", self._ui_language)
        te = data.get("t5_tag_en")
        if isinstance(te, list):
            for i, v in enumerate(te[:5]):
                self._t5_tag_en[i].set(bool(v))
        tt = data.get("t5_tag_txt")
        if isinstance(tt, list):
            for i, v in enumerate(tt[:5]):
                self._t5_tag_txt[i].set(str(v) if v is not None else "")

        k34 = frozenset(_FILTER_FIELD_KEYS_TAB34)
        k5 = frozenset(_FILTER_FIELD_KEYS_TAB5)

        def _clamp_ff(var: ctk.StringVar, allowed: frozenset[str]) -> None:
            if var.get() not in allowed:
                var.set("all")

        def _clamp_cmb(var: ctk.StringVar) -> None:
            if var.get() not in ("and", "or"):
                var.set("and")

        for v in (
            self._t3_filter_field,
            self._t3_filter_exclude_field,
            self._t4_filter_field,
            self._t4_filter_exclude_field,
        ):
            _clamp_ff(v, k34)
        for v in (self._t5_filter_field, self._t5_filter_exclude_field):
            _clamp_ff(v, k5)
        for v in (
            self._t3_filter_combine,
            self._t3_filter_exclude_combine,
            self._t4_filter_combine,
            self._t4_filter_exclude_combine,
            self._t5_filter_combine,
            self._t5_filter_exclude_combine,
        ):
            _clamp_cmb(v)

        am = (self._appearance_mode.get() or "dark").strip().lower()
        if am not in ("dark", "light", "system"):
            am = "dark"
        self._appearance_mode.set(am)
        dd = self._t1_delim.get().strip()
        if dd not in (";", ","):
            self._t1_delim.set(";")
        ul = self._norm_lang_code(self._ui_language.get())
        self._ui_language.set(ul)
        self._apply_user_appearance_setting()
        if hasattr(self, "_translator"):
            self._translator.set_lang(ul)
        self._apply_ttk_treeview_style()

    def _save_settings(self) -> None:
        try:
            _SETTINGS_PATH.write_text(
                json.dumps(self._gather_settings(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _on_close(self) -> None:
        self._save_settings()
        self.destroy()


def main() -> None:
    app = FileToolsApp()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)