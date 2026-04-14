#!/usr/bin/env python3
"""CustomTkinter: Tab1 Stash CSV, Tab2 disk scan, Tab3 rename, Tab4 move, Tab5 schema rename."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from tkinter import Menu, TclError, filedialog, simpledialog, ttk

import customtkinter as ctk

from i18n import SUPPORTED_LANGS, Translator

from file_rename_tools import (
    append_schema_tags_to_leaf,
    apply_file_renames,
    apply_find_replace_to_rows,
    apply_prefix_suffix_to_rows,
    build_schema_rename_leaf,
    ffprobe_video_size,
    filter_stub_for_subfolder_suggest,
    find_ffprobe_executable,
    move_files_only,
    read_rename_csv,
    row_passes_list_filters,
    rename_folder_dangerous,
    resolve_csv_path_to_existing_file,
    resolve_move_destination_root,
    sanitize_windows_dir_component,
    scan_folder_files,
    probe_stash_csv_export_schema,
    test_stash_graphql_connection,
    unique_leaf_in_dir,
    write_rename_csv,
)

_SETTINGS_PATH = Path(__file__).resolve().parent / "gui_file_tools_settings.json"
_SCHEMA_PRESETS_PATH = Path(__file__).resolve().parent / "schema_rename_presets.json"
_DEFAULT_STASH_PS1 = Path(__file__).resolve().parent / "export_stash_files.ps1"
_ROOT = Path(__file__).resolve().parent

# Tk event.state modifier bits (not in tkinter.constants on some Python 3.12 builds).
_TK_SHIFT_MASK = 0x0001
_TK_CONTROL_MASK = 0x0004

# Secondary / hint labels: (light appearance, dark appearance). CTk scroll areas use gray in light mode — avoid
# theme grays like gray25/gray70 here or text disappears on the frame background.
_LABEL_HINT = ("#1a1a1a", "#d0d0d0")
# Scroll areas + labels: CTk "transparent" often paints wrong on scroll canvas in light mode (dark slabs).
_UI_SURFACE = ("gray95", "gray17")


def _label(master, **kwargs):
    """CTkLabel with same surface as scroll content (not transparent — avoids dark blocks in light mode)."""
    kwargs.setdefault("fg_color", _UI_SURFACE)
    return ctk.CTkLabel(master, **kwargs)


# Compact buttons: width from label length (CTk default width is oversized for short text).
_BTN_H = 28

def _btn_w(s: str, *, lo: int = 40, hi: int = 420) -> int:
    return max(lo, min(hi, int(len(s) * 6.8 + 22)))


def _default_file_tools_csv_dir() -> Path:
    d = _ROOT / "file_tools_csv"
    d.mkdir(parents=True, exist_ok=True)
    return d


class FileToolsApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__(fg_color=_UI_SURFACE)
        self.title("Stashmarker — file list & rename")
        self.geometry("960x900")
        self.minsize(640, 520)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

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
        self._t3_only_under = ctk.StringVar(value="")
        self._t3_prefix = ctk.StringVar(value="")
        self._t3_suffix = ctk.StringVar(value="")
        self._t3_find = ctk.StringVar(value="")
        self._t3_replace = ctk.StringVar(value="")
        self._t3_replace_ci = ctk.BooleanVar(value=False)
        self._t3_dry = ctk.BooleanVar(value=True)
        self._t3_edit_leaf = ctk.StringVar(value="")

        # Folder rename (dangerous)
        self._t3_fold_src = ctk.StringVar(value="")
        self._t3_fold_new = ctk.StringVar(value="")
        self._t3_fold_confirm = ctk.BooleanVar(value=False)

        # Tab 4
        self._t4_rows: list[dict[str, str]] = []
        self._t4_csv = ctk.StringVar(value=str(_default_file_tools_csv_dir() / "stash_files.csv"))
        self._t4_filter = ctk.StringVar(value="")
        self._t4_filter_exclude = ctk.StringVar(value="")
        self._t4_target_folder = ctk.StringVar(value="")
        self._t4_dry = ctk.BooleanVar(value=True)
        self._t4_subfolder = ctk.StringVar(value="")
        self._t4_per_source = ctk.BooleanVar(value=False)
        self._t4_use_selected = ctk.BooleanVar(value=False)
        self._t4_preview_scheduled = False
        self._t4_after_id: str | None = None
        self._t4_trace_ids: list[tuple[ctk.Variable, str]] = []
        self._t5_trace_ids: list[tuple[ctk.Variable, str]] = []
        self._tree_b1_drag_state: dict[int, dict[str, object]] = {}

        # Tab 5 — schema rename (title + year + tags + ffprobe resolution + rating)
        self._t5_rows: list[dict[str, str]] = []
        self._t5_csv = ctk.StringVar(value=str(_default_file_tools_csv_dir() / "stash_files.csv"))
        self._t5_filter = ctk.StringVar(value="")
        self._t5_filter_exclude = ctk.StringVar(value="")
        self._t5_title_max = ctk.StringVar(value="15")
        self._t5_include_year = ctk.BooleanVar(value=True)
        self._t5_include_resolution = ctk.BooleanVar(value=True)
        self._t5_include_rating = ctk.BooleanVar(value=True)
        self._t5_resolution_mode = ctk.StringVar(value="heightp")
        self._t5_dry = ctk.BooleanVar(value=True)
        self._t5_use_selected = ctk.BooleanVar(value=False)
        self._t5_tags_only_mode = ctk.BooleanVar(value=False)
        self._t5_tag_en = [ctk.BooleanVar(value=False) for _ in range(5)]
        self._t5_tag_txt = [ctk.StringVar(value="") for _ in range(5)]
        self._t5_preset_name = ctk.StringVar(value="")
        self._t5_preset_pick = ctk.StringVar(value="\u2014")  # same as t5.preset_none in all locales
        self._t5_ffprobe_cache: dict[str, tuple[int | None, int | None]] = {}
        self._t5_preset_menu: ctk.CTkOptionMenu | None = None
        self._t3_sort_col = "path"
        self._t3_sort_desc = False
        self._t4_sort_col = "path"
        self._t4_sort_desc = False
        self._t5_sort_col = "path"
        self._t5_sort_desc = False

        self._appearance_mode = ctk.StringVar(value="dark")
        self._ui_language = ctk.StringVar(value="en")
        self._settings_dialog: ctk.CTkToplevel | None = None

        self._load_settings()
        self._translator = Translator(_ROOT / "locales", self._norm_lang_code(self._ui_language.get()))
        self.title(self._tr("app.window_title"))
        self._build_ui()
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
        self._t3_only_under = ctk.StringVar(value=self._t3_only_under.get())
        self._t3_prefix = ctk.StringVar(value=self._t3_prefix.get())
        self._t3_suffix = ctk.StringVar(value=self._t3_suffix.get())
        self._t3_find = ctk.StringVar(value=self._t3_find.get())
        self._t3_replace = ctk.StringVar(value=self._t3_replace.get())
        self._t3_replace_ci = ctk.BooleanVar(value=self._t3_replace_ci.get())
        self._t3_dry = ctk.BooleanVar(value=self._t3_dry.get())
        self._t3_edit_leaf = ctk.StringVar(value=self._t3_edit_leaf.get())
        self._t3_fold_src = ctk.StringVar(value=self._t3_fold_src.get())
        self._t3_fold_new = ctk.StringVar(value=self._t3_fold_new.get())
        self._t3_fold_confirm = ctk.BooleanVar(value=self._t3_fold_confirm.get())

        self._t4_csv = ctk.StringVar(value=self._t4_csv.get())
        self._t4_filter = ctk.StringVar(value=self._t4_filter.get())
        self._t4_filter_exclude = ctk.StringVar(value=self._t4_filter_exclude.get())
        self._t4_target_folder = ctk.StringVar(value=self._t4_target_folder.get())
        self._t4_subfolder = ctk.StringVar(value=self._t4_subfolder.get())
        self._t4_dry = ctk.BooleanVar(value=self._t4_dry.get())
        self._t4_per_source = ctk.BooleanVar(value=self._t4_per_source.get())
        self._t4_use_selected = ctk.BooleanVar(value=self._t4_use_selected.get())

        self._t5_csv = ctk.StringVar(value=self._t5_csv.get())
        self._t5_filter = ctk.StringVar(value=self._t5_filter.get())
        self._t5_filter_exclude = ctk.StringVar(value=self._t5_filter_exclude.get())
        self._t5_title_max = ctk.StringVar(value=self._t5_title_max.get())
        self._t5_include_year = ctk.BooleanVar(value=self._t5_include_year.get())
        self._t5_include_resolution = ctk.BooleanVar(value=self._t5_include_resolution.get())
        self._t5_include_rating = ctk.BooleanVar(value=self._t5_include_rating.get())
        self._t5_resolution_mode = ctk.StringVar(value=self._t5_resolution_mode.get())
        self._t5_dry = ctk.BooleanVar(value=self._t5_dry.get())
        self._t5_use_selected = ctk.BooleanVar(value=self._t5_use_selected.get())
        self._t5_tags_only_mode = ctk.BooleanVar(value=self._t5_tags_only_mode.get())
        self._t5_tag_en = [ctk.BooleanVar(value=self._t5_tag_en[i].get()) for i in range(5)]
        self._t5_tag_txt = [ctk.StringVar(value=self._t5_tag_txt[i].get()) for i in range(5)]
        self._t5_preset_name = ctk.StringVar(value=self._t5_preset_name.get())
        self._t5_preset_pick = ctk.StringVar(value=self._t5_preset_pick.get())

    def _remove_t4_traces(self) -> None:
        for v, tid in self._t4_trace_ids:
            try:
                v.trace_remove("write", tid)
            except (ValueError, TclError):
                pass
        self._t4_trace_ids.clear()

    def _install_t4_traces(self) -> None:
        self._remove_t4_traces()
        cb = lambda *_: self._t4_schedule_preview_refresh()
        for v in (
            self._t4_filter,
            self._t4_filter_exclude,
            self._t4_target_folder,
            self._t4_subfolder,
            self._t4_per_source,
            self._t4_use_selected,
            self._t4_dry,
        ):
            self._t4_trace_ids.append((v, v.trace_add("write", cb)))

    def _remove_t5_traces(self) -> None:
        for v, tid in self._t5_trace_ids:
            try:
                v.trace_remove("write", tid)
            except (ValueError, TclError):
                pass
        self._t5_trace_ids.clear()

    def _install_t5_traces(self) -> None:
        """Refresh Tab 5 preview when schema options (tags, title length, …) change."""
        self._remove_t5_traces()
        cb = lambda *_: self._t5_rebuild_tree()
        for i in range(5):
            self._t5_trace_ids.append((self._t5_tag_en[i], self._t5_tag_en[i].trace_add("write", cb)))
            self._t5_trace_ids.append((self._t5_tag_txt[i], self._t5_tag_txt[i].trace_add("write", cb)))
        for v in (
            self._t5_title_max,
            self._t5_include_year,
            self._t5_include_resolution,
            self._t5_include_rating,
            self._t5_resolution_mode,
        ):
            self._t5_trace_ids.append((v, v.trace_add("write", cb)))

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
        self._remove_t4_traces()
        self._remove_t5_traces()
        self._cancel_t4_preview_after()
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
                style.configure("Treeview.Heading", background="#1f538d", foreground="#dce4ee")
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
        """Click-drag to select a contiguous row block (Ctrl/Shift+click still use default extended mode)."""
        tid = id(tree)

        def on_press(event: object) -> None:
            y = getattr(event, "y", 0)
            row_id = tree.identify_row(y)
            self._tree_b1_drag_state[tid] = {"anchor": row_id or "", "down": True}

        def on_motion(event: object) -> None:
            st = self._tree_b1_drag_state.get(tid)
            if not st or not st.get("down"):
                return
            state = int(getattr(event, "state", 0))
            if (state & _TK_CONTROL_MASK) or (state & _TK_SHIFT_MASK):
                return
            anchor = (st.get("anchor") or "").strip()
            if not anchor:
                return
            y = getattr(event, "y", 0)
            cur = tree.identify_row(y)
            if not cur:
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

        def on_release(_event: object) -> None:
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

    def _build_ui(self) -> None:
        self._browse_w = max(88, _btn_w(self._tr("common.browse")))
        head = ctk.CTkFrame(self, fg_color=_UI_SURFACE)
        head.pack(fill="x", padx=10, pady=(10, 0))
        _label(head, text=self._tr("app.brand"), font=ctk.CTkFont(size=17, weight="bold")).pack(side="left")
        ctk.CTkButton(
            head,
            text="\u2699",
            width=36,
            height=32,
            font=ctk.CTkFont(size=18),
            command=self._open_settings_dialog,
            fg_color=("gray78", "gray28"),
            hover_color=("gray68", "gray38"),
        ).pack(side="right")

        tabs = ctk.CTkTabview(self, fg_color=_UI_SURFACE)
        tabs.pack(fill="both", expand=True, padx=10, pady=(6, 4))
        tab1, tab2, tab3, tab4, tab5 = (
            self._tr("tab.1"),
            self._tr("tab.2"),
            self._tr("tab.3"),
            self._tr("tab.4"),
            self._tr("tab.5"),
        )
        tabs.add(tab1)
        tabs.add(tab2)
        tabs.add(tab3)
        tabs.add(tab4)
        tabs.add(tab5)

        def _scroll_wrap(tab_label: str) -> ctk.CTkScrollableFrame:
            inner = ctk.CTkScrollableFrame(tabs.tab(tab_label), fg_color=_UI_SURFACE)
            inner.pack(fill="both", expand=True)
            return inner

        self._build_tab1(_scroll_wrap(tab1))
        self._build_tab2(_scroll_wrap(tab2))
        self._build_tab3(_scroll_wrap(tab3))
        self._build_tab4(_scroll_wrap(tab4))
        self._build_tab5(_scroll_wrap(tab5))

        log_f = ctk.CTkFrame(self, fg_color=_UI_SURFACE)
        log_f.pack(fill="both", expand=False, padx=10, pady=(4, 10))
        log_top = ctk.CTkFrame(log_f, fg_color=_UI_SURFACE)
        log_top.pack(fill="x")
        _label(log_top, text=self._tr("common.log"), anchor="w").pack(side="left")
        ctk.CTkButton(
            log_top,
            text=self._tr("common.save_log"),
            width=_btn_w(self._tr("common.save_log")),
            height=_BTN_H,
            command=self._save_log_to_file,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            log_top,
            text=self._tr("common.clear_log"),
            width=_btn_w(self._tr("common.clear_log")),
            height=_BTN_H,
            command=self._clear_log,
        ).pack(side="right")
        self._log_box = ctk.CTkTextbox(log_f, height=200, activate_scrollbars=True)
        self._log_box.pack(fill="both", expand=True)
        self._log_box.configure(state="disabled")

    def _pad(self) -> dict:
        return {"padx": 10, "pady": (4, 6)}

    def _collapsible_section(
        self,
        parent: ctk.CTkFrame,
        *,
        title_key: str,
        start_open: bool,
    ) -> ctk.CTkFrame:
        """Header toggles visibility of the returned frame (pack children into it)."""
        pad = self._pad()
        outer = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        outer.pack(fill="x", **pad)
        open_flag = [start_open]
        title_base = self._tr(title_key)
        body = ctk.CTkFrame(outer, fg_color=_UI_SURFACE)
        hdr = ctk.CTkButton(
            outer,
            text="",
            anchor="w",
            height=26,
            corner_radius=6,
            fg_color=("gray82", "gray28"),
            hover_color=("gray72", "gray38"),
            font=ctk.CTkFont(size=12),
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
        _label(
            parent,
            text=self._tr("t1.intro"),
            anchor="w",
            wraplength=860,
            justify="left",
        ).pack(fill="x", **pad)
        _label(
            parent,
            text=self._tr("t1.hint_scan"),
            anchor="w",
            wraplength=860,
            justify="left",
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", padx=10, pady=(0, 6))

        r = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        r.pack(fill="x", **pad)
        _label(r, text=self._tr("t1.export_script"), width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(r, textvariable=self._t1_ps1).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            r, text=self._tr("common.browse"), width=self._browse_w, height=_BTN_H, command=self._browse_t1_ps1
        ).pack(side="right")

        for key, var, secret, csv_browse in (
            ("common.stash_url", self._t1_url, False, False),
            ("common.api_key", self._t1_api, True, False),
            ("t1.label.save_csv", self._t1_out, False, True),
        ):
            rr = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
            rr.pack(fill="x", **pad)
            _label(rr, text=self._tr(key), width=160, anchor="w").pack(side="left")
            ctk.CTkEntry(rr, textvariable=var, show="*" if secret else None).pack(
                side="left", fill="x", expand=True, padx=(0, 8)
            )
            if csv_browse:
                ctk.CTkButton(
                    rr, text=self._tr("common.browse"), width=self._browse_w, height=_BTN_H, command=self._browse_t1_out
                ).pack(side="right")

        gql_row = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        gql_row.pack(fill="x", **pad)
        _label(gql_row, text=self._tr("t1.graphql_path"), width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(
            gql_row,
            textvariable=self._t1_graphql_path,
            placeholder_text=self._tr("t1.graphql_placeholder"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            gql_row,
            text=self._tr("common.default"),
            width=_btn_w(self._tr("common.default")),
            height=_BTN_H,
            command=self._t1_reset_graphql_path,
        ).pack(side="right")

        _label(
            parent,
            text=self._tr("t1.hint_settings"),
            anchor="w",
            wraplength=860,
            justify="left",
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", padx=10, pady=(0, 6))

        row2 = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        row2.pack(fill="x", **pad)
        _label(row2, text=self._tr("t1.batch_size"), width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(row2, textvariable=self._t1_per_page, width=80).pack(side="left")

        _label(parent, text=self._tr("t1.filters_title"), anchor="w").pack(fill="x", **pad)
        for key, var in (
            ("t1.path_prefix", self._t1_path_prefix),
            ("t1.path_contains", self._t1_path_contains),
            ("t1.name_contains", self._t1_name_contains),
            ("t1.name_regex", self._t1_name_regex),
        ):
            rr = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
            rr.pack(fill="x", **pad)
            _label(rr, text=self._tr(key), width=200, anchor="w").pack(side="left")
            ctk.CTkEntry(rr, textvariable=var).pack(side="left", fill="x", expand=True)

        bf = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        bf.pack(fill="x", **pad)
        ctk.CTkButton(
            bf,
            text=self._tr("t1.run_export"),
            width=_btn_w(self._tr("t1.run_export")),
            height=30,
            command=self._run_t1_export,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            bf,
            text=self._tr("t1.test_connection"),
            width=_btn_w(self._tr("t1.test_connection")),
            height=_BTN_H,
            command=self._test_stash_connection,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            bf,
            text=self._tr("t1.check_csv_export"),
            width=_btn_w(self._tr("t1.check_csv_export")),
            height=_BTN_H,
            command=self._probe_stash_csv_export,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            bf,
            text=self._tr("t1.open_out_folder"),
            width=_btn_w(self._tr("t1.open_out_folder")),
            height=_BTN_H,
            command=self._open_t1_out_dir,
        ).pack(side="left", padx=(0, 8))
        _label(bf, text=self._tr("t1.send_csv_to"), text_color=_LABEL_HINT).pack(side="left", padx=(12, 4))
        ctk.CTkButton(
            bf,
            text=self._tr("t1.tab3_rename"),
            width=_btn_w(self._tr("t1.tab3_rename")),
            height=_BTN_H,
            command=self._t1_push_to_tab3,
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            bf,
            text=self._tr("t1.tab4_move"),
            width=_btn_w(self._tr("t1.tab4_move")),
            height=_BTN_H,
            command=self._t1_push_to_tab4,
        ).pack(side="left")

    def _build_tab2(self, parent: ctk.CTkFrame) -> None:
        pad = self._pad()
        _label(
            parent,
            text=self._tr("t2.intro"),
            anchor="w",
            wraplength=860,
            justify="left",
        ).pack(fill="x", **pad)

        r = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        r.pack(fill="x", **pad)
        _label(r, text=self._tr("t2.folder_scan"), width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(r, textvariable=self._t2_folder).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            r, text=self._tr("common.browse"), width=self._browse_w, height=_BTN_H, command=self._browse_t2_folder
        ).pack(side="right")

        ctk.CTkCheckBox(parent, text=self._tr("t2.recursive"), variable=self._t2_recursive).pack(anchor="w", **pad)

        rr = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        rr.pack(fill="x", **pad)
        _label(rr, text=self._tr("t2.file_types"), width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(
            rr, textvariable=self._t2_patterns, placeholder_text=self._tr("t2.patterns_placeholder")
        ).pack(side="left", fill="x", expand=True)

        ro = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        ro.pack(fill="x", **pad)
        _label(ro, text=self._tr("t2.save_list_csv"), width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(ro, textvariable=self._t2_out).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            ro, text=self._tr("common.browse"), width=self._browse_w, height=_BTN_H, command=self._browse_t2_out
        ).pack(side="right")

        bf = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        bf.pack(fill="x", **pad)
        ctk.CTkButton(
            bf,
            text=self._tr("t2.run_scan"),
            width=_btn_w(self._tr("t2.run_scan")),
            height=30,
            command=self._run_t2_scan,
        ).pack(side="left", padx=(0, 8))
        _label(bf, text=self._tr("t1.send_csv_to"), text_color=_LABEL_HINT).pack(side="left", padx=(8, 4))
        ctk.CTkButton(
            bf,
            text=self._tr("t1.tab3_rename"),
            width=_btn_w(self._tr("t1.tab3_rename")),
            height=_BTN_H,
            command=self._t2_push_to_tab3,
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            bf,
            text=self._tr("t1.tab4_move"),
            width=_btn_w(self._tr("t1.tab4_move")),
            height=_BTN_H,
            command=self._t2_push_to_tab4,
        ).pack(side="left")

    def _build_tab3(self, parent: ctk.CTkFrame) -> None:
        pad = self._pad()
        _label(
            parent,
            text=self._tr("t3.steps"),
            anchor="w",
            wraplength=860,
            justify="left",
        ).pack(fill="x", **pad)

        top = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        top.pack(fill="x", **pad)
        _label(top, text=self._tr("common.csv_file"), width=100, anchor="w").pack(side="left")
        ctk.CTkEntry(top, textvariable=self._t3_csv).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            top, text=self._tr("common.browse"), width=self._browse_w, height=_BTN_H, command=self._browse_t3_csv
        ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(
            top, text=self._tr("common.load"), width=_btn_w(self._tr("common.load")), height=_BTN_H, command=self._t3_load_csv
        ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(
            top,
            text=self._tr("t3.save_csv"),
            width=_btn_w(self._tr("t3.save_csv")),
            height=_BTN_H,
            command=self._t3_save_csv,
        ).pack(side="right")

        _label(
            parent,
            text=self._tr("t3.hint_csv"),
            anchor="w",
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", padx=10, pady=(0, 2))

        sf = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        sf.pack(fill="x", **pad)
        _label(sf, text=self._tr("t3.search_label"), width=160, anchor="w").pack(side="left")
        ent = ctk.CTkEntry(
            sf,
            textvariable=self._t3_filter,
            placeholder_text=self._tr("t3.filter_placeholder"),
        )
        ent.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ent.bind("<KeyRelease>", lambda e: self._t3_rebuild_tree())

        ex3 = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        ex3.pack(fill="x", **pad)
        _label(ex3, text=self._tr("common.exclude_filter"), width=160, anchor="w").pack(side="left")
        ent_ex3 = ctk.CTkEntry(
            ex3,
            textvariable=self._t3_filter_exclude,
            placeholder_text=self._tr("common.exclude_placeholder"),
        )
        ent_ex3.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ent_ex3.bind("<KeyRelease>", lambda e: self._t3_rebuild_tree())

        _label(
            parent,
            text=self._tr("common.search_syntax_hint"),
            anchor="w",
            justify="left",
            wraplength=880,
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=11),
        ).pack(fill="x", padx=10, pady=(0, 2))
        _label(
            parent,
            text=self._tr("common.exclude_syntax_hint"),
            anchor="w",
            justify="left",
            wraplength=880,
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=11),
        ).pack(fill="x", padx=10, pady=(0, 4))

        tree_frame = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        tree_frame.pack(fill="both", expand=True, **pad)
        self._apply_ttk_treeview_style()

        self._tree = ttk.Treeview(
            tree_frame,
            columns=("path", "name", "new_leaf"),
            show="headings",
            height=14,
            selectmode="extended",
        )
        self._tree.heading("path", text=self._tr("t3.col.path"), command=lambda: self._toggle_sort_t3("path"))
        self._tree.heading("name", text=self._tr("t3.col.name"), command=lambda: self._toggle_sort_t3("name"))
        self._tree.heading(
            "new_leaf", text=self._tr("t3.col.new_leaf"), command=lambda: self._toggle_sort_t3("new_leaf")
        )
        self._tree.column("path", width=420, minwidth=80, stretch=False)
        self._tree.column("name", width=160, minwidth=60, stretch=False)
        self._tree.column("new_leaf", width=220, minwidth=60, stretch=False)
        self._place_ttk_tree_with_scrollbars(tree_frame, self._tree)
        self._tree.bind("<<TreeviewSelect>>", self._t3_on_select)
        self._tree.bind("<Double-1>", lambda e: self._t3_focus_edit_leaf())
        self._tree.bind("<Button-3>", self._t3_tree_context_menu)

        t3_path_btns = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        t3_path_btns.pack(fill="x", padx=10, pady=(0, 4))
        _label(t3_path_btns, text=self._tr("t3.selected"), width=90, anchor="w").pack(side="left")
        ctk.CTkButton(
            t3_path_btns,
            text=self._tr("t3.copy_folder"),
            width=_btn_w(self._tr("t3.copy_folder")),
            height=_BTN_H,
            command=self._t3_copy_selected_path,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            t3_path_btns,
            text=self._tr("t3.open_explorer"),
            width=_btn_w(self._tr("t3.open_explorer")),
            height=_BTN_H,
            command=self._t3_open_selected_path,
        ).pack(side="left")

        edit_row = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        edit_row.pack(fill="x", **pad)
        _label(edit_row, text=self._tr("t3.new_name_selected"), width=200, anchor="w").pack(side="left")
        ctk.CTkEntry(edit_row, textvariable=self._t3_edit_leaf).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            edit_row,
            text=self._tr("t3.apply_selected"),
            width=_btn_w(self._tr("t3.apply_selected")),
            height=_BTN_H,
            command=self._t3_apply_leaf_selection,
        ).pack(side="right")

        batch_body = self._collapsible_section(parent, title_key="t3.section_batch_title", start_open=False)
        rule = ctk.CTkFrame(batch_body, fg_color=_UI_SURFACE)
        rule.pack(fill="x", **pad)
        _label(rule, text=self._tr("common.prefix"), width=80, anchor="w").pack(side="left")
        ctk.CTkEntry(rule, textvariable=self._t3_prefix, width=120).pack(side="left", padx=(0, 12))
        _label(rule, text=self._tr("t3.suffix_before_ext"), width=120, anchor="w").pack(side="left")
        ctk.CTkEntry(rule, textvariable=self._t3_suffix, width=120).pack(side="left", padx=(0, 12))
        rule_btns = ctk.CTkFrame(rule, fg_color=_UI_SURFACE)
        rule_btns.pack(side="left", padx=(8, 0))
        ctk.CTkButton(
            rule_btns,
            text=self._tr("t3.apply_search"),
            width=_btn_w(self._tr("t3.apply_search")),
            height=_BTN_H,
            command=self._t3_apply_rule_filtered,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            rule_btns,
            text=self._tr("t3.apply_selected"),
            width=_btn_w(self._tr("t3.apply_selected")),
            height=_BTN_H,
            command=self._t3_apply_rule_selected,
        ).pack(side="left")

        fr_row = ctk.CTkFrame(batch_body, fg_color=_UI_SURFACE)
        fr_row.pack(fill="x", **pad)
        _label(fr_row, text=self._tr("common.find"), width=80, anchor="w").pack(side="left")
        ctk.CTkEntry(fr_row, textvariable=self._t3_find, width=140).pack(side="left", padx=(0, 8))
        _label(fr_row, text=self._tr("common.replace_with"), width=100, anchor="w").pack(side="left")
        ctk.CTkEntry(fr_row, textvariable=self._t3_replace, width=140).pack(side="left", padx=(0, 8))
        ctk.CTkCheckBox(
            fr_row,
            text=self._tr("t3.ignore_case"),
            variable=self._t3_replace_ci,
        ).pack(side="left", padx=(0, 8))
        fr_btns = ctk.CTkFrame(fr_row, fg_color=_UI_SURFACE)
        fr_btns.pack(side="left", padx=(4, 0))
        ctk.CTkButton(
            fr_btns,
            text=self._tr("t3.fr_search"),
            width=_btn_w(self._tr("t3.fr_search")),
            height=_BTN_H,
            command=self._t3_apply_find_replace_filtered,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            fr_btns,
            text=self._tr("t3.fr_selected"),
            width=_btn_w(self._tr("t3.fr_selected")),
            height=_BTN_H,
            command=self._t3_apply_find_replace_selected,
        ).pack(side="left")

        fr_hint = ctk.CTkFrame(batch_body, fg_color=_UI_SURFACE)
        fr_hint.pack(fill="x", padx=(0, 0), pady=(0, 4))
        _label(
            fr_hint,
            text=self._tr("t3.fr_hint"),
            anchor="w",
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=(80, 0))

        ou = ctk.CTkFrame(batch_body, fg_color=_UI_SURFACE)
        ou.pack(fill="x", **pad)
        _label(ou, text=self._tr("t3.limit_folder"), width=180, anchor="w").pack(side="left")
        ctk.CTkEntry(ou, textvariable=self._t3_only_under).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            ou, text=self._tr("common.browse"), width=self._browse_w, height=_BTN_H, command=self._browse_t3_only_under
        ).pack(side="right")

        runf = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        runf.pack(fill="x", **pad)
        ctk.CTkCheckBox(runf, text=self._tr("t3.preview_only"), variable=self._t3_dry).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            runf,
            text=self._tr("t3.rename_disk"),
            width=_btn_w(self._tr("t3.rename_disk")),
            height=30,
            fg_color="#1f538d",
            command=self._t3_run_renames,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            runf,
            text=self._tr("t3.clear_new_names"),
            width=_btn_w(self._tr("t3.clear_new_names")),
            height=_BTN_H,
            command=self._t3_clear_filtered_leaves,
        ).pack(side="left")

        fold_body = self._collapsible_section(parent, title_key="t3.section_folder_title", start_open=False)
        warn_fr = ctk.CTkFrame(fold_body, fg_color=("#8b3a3a", "#5c1f1f"), corner_radius=8)
        warn_fr.pack(fill="x", **pad)
        _label(
            warn_fr,
            text=self._tr("t3.folder_warn"),
            text_color=("#fff", "#ffcccc"),
            anchor="w",
            justify="left",
            fg_color="transparent",
        ).pack(fill="x", padx=10, pady=8)

        fr = ctk.CTkFrame(warn_fr, fg_color="transparent")
        fr.pack(fill="x", padx=10, pady=(0, 10))
        _label(fr, text=self._tr("common.folder"), width=80, anchor="w", fg_color="transparent").pack(side="left")
        ctk.CTkEntry(fr, textvariable=self._t3_fold_src).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            fr, text=self._tr("common.browse"), width=self._browse_w, height=_BTN_H, command=self._browse_t3_fold_src
        ).pack(side="right")

        fr2 = ctk.CTkFrame(warn_fr, fg_color="transparent")
        fr2.pack(fill="x", padx=10, pady=(0, 10))
        _label(fr2, text=self._tr("common.new_name"), width=80, anchor="w", fg_color="transparent").pack(side="left")
        ctk.CTkEntry(
            fr2, textvariable=self._t3_fold_new, placeholder_text=self._tr("t3.fold_new_placeholder")
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkCheckBox(
            warn_fr,
            text=self._tr("t3.fold_confirm"),
            variable=self._t3_fold_confirm,
            text_color=("#fff", "#eee"),
        ).pack(anchor="w", padx=10, pady=(0, 6))

        ctk.CTkButton(
            warn_fr,
            text=self._tr("t3.fold_rename_btn"),
            width=_btn_w(self._tr("t3.fold_rename_btn")),
            height=_BTN_H,
            fg_color="#8b0000",
            hover_color="#a52a2a",
            command=self._t3_run_folder_rename,
        ).pack(anchor="w", padx=10, pady=(0, 10))

    def _build_tab4(self, parent: ctk.CTkFrame) -> None:
        pad = self._pad()
        _label(
            parent,
            text=self._tr("t4.intro_block"),
            anchor="w",
            wraplength=860,
            justify="left",
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", **pad)

        csv_row = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        csv_row.pack(fill="x", **pad)
        _label(csv_row, text=self._tr("common.csv_file"), width=100, anchor="w").pack(side="left")
        ctk.CTkEntry(csv_row, textvariable=self._t4_csv).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            csv_row, text=self._tr("common.browse"), width=self._browse_w, height=_BTN_H, command=self._browse_t4_csv
        ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(
            csv_row,
            text=self._tr("common.load"),
            width=_btn_w(self._tr("common.load")),
            height=_BTN_H,
            command=self._t4_load_csv,
        ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(
            csv_row,
            text=self._tr("t4.export_csv"),
            width=_btn_w(self._tr("t4.export_csv")),
            height=_BTN_H,
            command=self._t4_export_csv,
        ).pack(side="right")

        filt_row = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        filt_row.pack(fill="x", **pad)
        _label(filt_row, text=self._tr("common.search"), width=120, anchor="w").pack(side="left")
        ent4 = ctk.CTkEntry(
            filt_row,
            textvariable=self._t4_filter,
            placeholder_text=self._tr("t3.filter_placeholder"),
        )
        ent4.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ent4.bind("<KeyRelease>", lambda e: (self._t4_rebuild_tree(), self._t4_schedule_preview_refresh()))

        ex4 = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        ex4.pack(fill="x", **pad)
        _label(ex4, text=self._tr("common.exclude_filter"), width=120, anchor="w").pack(side="left")
        ent_ex4 = ctk.CTkEntry(
            ex4,
            textvariable=self._t4_filter_exclude,
            placeholder_text=self._tr("common.exclude_placeholder"),
        )
        ent_ex4.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ent_ex4.bind(
            "<KeyRelease>",
            lambda e: (self._t4_rebuild_tree(), self._t4_schedule_preview_refresh()),
        )

        _label(
            parent,
            text=self._tr("common.search_syntax_hint"),
            anchor="w",
            justify="left",
            wraplength=880,
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=11),
        ).pack(fill="x", padx=10, pady=(0, 2))
        _label(
            parent,
            text=self._tr("common.exclude_syntax_hint"),
            anchor="w",
            justify="left",
            wraplength=880,
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=11),
        ).pack(fill="x", padx=10, pady=(0, 4))

        tree_frame = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        tree_frame.pack(fill="both", expand=True, **pad)
        self._apply_ttk_treeview_style()
        self._t4_tree = ttk.Treeview(
            tree_frame,
            columns=("path", "name", "scene_id"),
            show="headings",
            height=10,
            selectmode="extended",
        )
        self._t4_tree.heading("path", text=self._tr("t3.col.path"), command=lambda: self._toggle_sort_t4("path"))
        self._t4_tree.heading("name", text=self._tr("t3.col.name"), command=lambda: self._toggle_sort_t4("name"))
        self._t4_tree.heading(
            "scene_id", text=self._tr("t4.col.scene_id"), command=lambda: self._toggle_sort_t4("scene_id")
        )
        self._t4_tree.column("path", width=420, minwidth=80, stretch=False)
        self._t4_tree.column("name", width=180, minwidth=80, stretch=False)
        self._t4_tree.column("scene_id", width=120, minwidth=60, stretch=False)
        self._place_ttk_tree_with_scrollbars(tree_frame, self._t4_tree)
        self._t4_tree.bind("<Button-3>", self._t4_tree_context_menu)

        t4_path_btns = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        t4_path_btns.pack(fill="x", padx=10, pady=(0, 4))
        _label(t4_path_btns, text=self._tr("t3.selected"), width=90, anchor="w").pack(side="left")
        ctk.CTkButton(
            t4_path_btns,
            text=self._tr("t3.open_explorer"),
            width=_btn_w(self._tr("t3.open_explorer")),
            height=_BTN_H,
            command=self._t4_open_selected_in_explorer,
        ).pack(side="left")

        self._t4_stats = _label(
            parent,
            text=self._tr("t4.stats_empty"),
            anchor="w",
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=12),
        )
        self._t4_stats.pack(fill="x", padx=10, pady=(0, 4))

        tf = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        tf.pack(fill="x", **pad)
        _label(tf, text=self._tr("t4.where_move"), width=200, anchor="w").pack(side="left")
        ctk.CTkEntry(
            tf,
            textvariable=self._t4_target_folder,
            placeholder_text=self._tr("t4.where_placeholder"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            tf,
            text=self._tr("t4.target_from_row"),
            width=_btn_w(self._tr("t4.target_from_row")),
            height=_BTN_H,
            command=self._t4_set_target_from_selected_row_folder,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            tf,
            text=self._tr("common.browse"),
            width=self._browse_w,
            height=_BTN_H,
            command=self._browse_t4_target_folder,
        ).pack(side="right")

        sf = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        sf.pack(fill="x", **pad)
        _label(sf, text=self._tr("t4.subfolder_label"), width=200, anchor="w").pack(side="left")
        ctk.CTkEntry(
            sf,
            textvariable=self._t4_subfolder,
            placeholder_text=self._tr("t4.sub_placeholder"),
        ).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            sf,
            text=self._tr("t4.suggest"),
            width=_btn_w(self._tr("t4.suggest")),
            height=_BTN_H,
            command=self._t4_suggest_target_from_filtered,
        ).pack(side="right", padx=(8, 0))

        path_tips_body = self._collapsible_section(
            parent, title_key="t4.section_path_tips_title", start_open=False
        )
        _label(
            path_tips_body,
            text=self._tr("t4.move_hint"),
            anchor="w",
            wraplength=860,
            justify="left",
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", **pad)

        mf = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        mf.pack(fill="x", **pad)
        ctk.CTkCheckBox(
            mf,
            text=self._tr("t4.per_source"),
            variable=self._t4_per_source,
        ).pack(side="left")

        runf = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        runf.pack(fill="x", **pad)
        ctk.CTkCheckBox(
            runf,
            text=self._tr("t4.preview_only"),
            variable=self._t4_dry,
        ).pack(side="left", padx=(0, 12))
        ctk.CTkCheckBox(
            runf,
            text=self._tr("t4.selected_only"),
            variable=self._t4_use_selected,
        ).pack(side="left", padx=(0, 12))

        b = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        b.pack(fill="x", **pad)
        ctk.CTkButton(
            b,
            text=self._tr("t4.move_disk"),
            width=_btn_w(self._tr("t4.move_disk")),
            height=30,
            fg_color="#1f538d",
            command=self._t4_execute_move,
        ).pack(side="left")
        self._t4_plan = _label(
            b,
            text=self._tr("t4.plan_empty"),
            anchor="w",
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=12),
        )
        self._t4_plan.pack(side="left", padx=(12, 0))

        preview_body = self._collapsible_section(
            parent, title_key="t4.preview_section_title", start_open=True
        )
        pv_btns = ctk.CTkFrame(preview_body, fg_color=_UI_SURFACE)
        pv_btns.pack(fill="x", **pad)
        ctk.CTkButton(
            pv_btns,
            text=self._tr("t4.refresh_preview"),
            width=_btn_w(self._tr("t4.refresh_preview")),
            height=_BTN_H,
            command=self._t4_refresh_preview,
        ).pack(side="left")
        self._t4_preview = ctk.CTkTextbox(preview_body, height=130, activate_scrollbars=True)
        self._t4_preview.pack(fill="both", expand=False, **pad)
        self._t4_preview.configure(state="disabled")

    def _build_tab5(self, parent: ctk.CTkFrame) -> None:
        pad = self._pad()
        _label(
            parent,
            text=self._tr("t5.intro"),
            anchor="w",
            wraplength=860,
            justify="left",
        ).pack(fill="x", **pad)
        fp_exe = find_ffprobe_executable() or ""
        _label(
            parent,
            text=self._tr("t5.hint_ffprobe", exe=fp_exe or "—"),
            anchor="w",
            wraplength=860,
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", padx=10, pady=(0, 2))
        _label(
            parent,
            text=self._tr("t5.hint_csv_meta"),
            anchor="w",
            wraplength=860,
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", padx=10, pady=(0, 6))

        top = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        top.pack(fill="x", **pad)
        _label(top, text=self._tr("common.csv_file"), width=100, anchor="w").pack(side="left")
        ctk.CTkEntry(top, textvariable=self._t5_csv).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            top, text=self._tr("common.browse"), width=self._browse_w, height=_BTN_H, command=self._browse_t5_csv
        ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(
            top,
            text=self._tr("common.load"),
            width=_btn_w(self._tr("common.load")),
            height=_BTN_H,
            command=self._t5_load_csv,
        ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(
            top,
            text=self._tr("t3.save_csv"),
            width=_btn_w(self._tr("t3.save_csv")),
            height=_BTN_H,
            command=self._t5_save_csv,
        ).pack(side="right")

        sf = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        sf.pack(fill="x", **pad)
        _label(sf, text=self._tr("t3.search_label"), width=160, anchor="w").pack(side="left")
        ent5 = ctk.CTkEntry(
            sf,
            textvariable=self._t5_filter,
            placeholder_text=self._tr("t3.filter_placeholder"),
        )
        ent5.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ent5.bind("<KeyRelease>", lambda e: self._t5_rebuild_tree())

        ex5 = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        ex5.pack(fill="x", **pad)
        _label(ex5, text=self._tr("common.exclude_filter"), width=160, anchor="w").pack(side="left")
        ent_ex5 = ctk.CTkEntry(
            ex5,
            textvariable=self._t5_filter_exclude,
            placeholder_text=self._tr("common.exclude_placeholder"),
        )
        ent_ex5.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ent_ex5.bind("<KeyRelease>", lambda e: self._t5_rebuild_tree())

        _label(
            parent,
            text=self._tr("common.search_syntax_hint"),
            anchor="w",
            justify="left",
            wraplength=880,
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=11),
        ).pack(fill="x", padx=10, pady=(0, 2))
        _label(
            parent,
            text=self._tr("common.exclude_syntax_hint"),
            anchor="w",
            justify="left",
            wraplength=880,
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=11),
        ).pack(fill="x", padx=10, pady=(0, 2))
        _label(
            parent,
            text=self._tr("t5.selection_hint"),
            anchor="w",
            justify="left",
            wraplength=880,
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=11),
        ).pack(fill="x", padx=10, pady=(0, 4))

        tree_frame = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        tree_frame.pack(fill="both", expand=True, **pad)
        self._apply_ttk_treeview_style()
        self._t5_tree = ttk.Treeview(
            tree_frame,
            columns=(
                "path",
                "file_name",
                "scene_title",
                "scene_tags",
                "scene_markers",
                "scene_date",
                "proposed",
            ),
            show="headings",
            height=11,
            selectmode="extended",
        )
        self._t5_tree.heading("path", text=self._tr("t3.col.path"), command=lambda: self._toggle_sort_t5("path"))
        self._t5_tree.heading(
            "file_name", text=self._tr("t3.col.name"), command=lambda: self._toggle_sort_t5("file_name")
        )
        self._t5_tree.heading(
            "scene_title", text=self._tr("t5.col.scene_title"), command=lambda: self._toggle_sort_t5("scene_title")
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
        self._t5_tree.heading(
            "proposed", text=self._tr("t5.col.proposed"), command=lambda: self._toggle_sort_t5("proposed")
        )
        self._t5_tree.column("path", width=200, minwidth=60, stretch=False)
        self._t5_tree.column("file_name", width=100, minwidth=50, stretch=False)
        self._t5_tree.column("scene_title", width=120, minwidth=50, stretch=False)
        self._t5_tree.column("scene_tags", width=110, minwidth=50, stretch=False)
        self._t5_tree.column("scene_markers", width=110, minwidth=50, stretch=False)
        self._t5_tree.column("scene_date", width=72, minwidth=50, stretch=False)
        self._t5_tree.column("proposed", width=200, minwidth=80, stretch=False)
        self._place_ttk_tree_with_scrollbars(tree_frame, self._t5_tree)
        self._t5_tree.bind("<Button-3>", self._t5_tree_context_menu)

        t5_path_btns = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        t5_path_btns.pack(fill="x", padx=10, pady=(0, 4))
        _label(t5_path_btns, text=self._tr("t3.selected"), width=90, anchor="w").pack(side="left")
        ctk.CTkButton(
            t5_path_btns,
            text=self._tr("t3.open_explorer"),
            width=_btn_w(self._tr("t3.open_explorer")),
            height=_BTN_H,
            command=self._t5_open_selected_in_explorer,
        ).pack(side="left")

        opt = ctk.CTkFrame(parent, fg_color=_UI_SURFACE, height=32)
        opt.pack_propagate(False)
        opt.pack(fill="x", padx=10, pady=(2, 0))
        _label(opt, text=self._tr("t5.title_max"), width=200, anchor="w").pack(side="left")
        ctk.CTkEntry(opt, textvariable=self._t5_title_max, width=56).pack(side="left", padx=(0, 12))
        ctk.CTkCheckBox(opt, text=self._tr("t5.include_year"), variable=self._t5_include_year).pack(
            side="left", padx=(0, 10)
        )
        ctk.CTkCheckBox(
            opt, text=self._tr("t5.include_resolution"), variable=self._t5_include_resolution
        ).pack(side="left", padx=(0, 10))
        ctk.CTkCheckBox(opt, text=self._tr("t5.include_rating"), variable=self._t5_include_rating).pack(
            side="left", padx=(0, 10)
        )

        rr = ctk.CTkFrame(parent, fg_color=_UI_SURFACE, height=32)
        rr.pack_propagate(False)
        rr.pack(fill="x", padx=10, pady=(0, 2))
        _label(rr, text=self._tr("t5.resolution_mode"), width=200, anchor="w").pack(side="left")
        ctk.CTkRadioButton(
            rr,
            text=self._tr("t5.res_heightp"),
            variable=self._t5_resolution_mode,
            value="heightp",
        ).pack(side="left", padx=(0, 12))
        ctk.CTkRadioButton(
            rr,
            text=self._tr("t5.res_wxh"),
            variable=self._t5_resolution_mode,
            value="wxh",
        ).pack(side="left")
        rr_spacer = ctk.CTkFrame(rr, fg_color=_UI_SURFACE)
        rr_spacer.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            rr,
            text=self._tr("t5.refresh_probe"),
            width=_btn_w(self._tr("t5.refresh_probe")),
            height=_BTN_H,
            command=self._t5_refresh_probe,
        ).pack(side="right", padx=(8, 0))

        _label(
            parent,
            text=self._tr("t5.tag_structure_hint"),
            anchor="w",
            justify="left",
            wraplength=880,
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=11),
        ).pack(fill="x", padx=10, pady=(0, 2))
        ctk.CTkCheckBox(
            parent,
            text=self._tr("t5.tags_only_mode"),
            variable=self._t5_tags_only_mode,
            fg_color=_UI_SURFACE,
        ).pack(fill="x", padx=10, pady=(0, 2))

        for i in range(5):
            tag_row = ctk.CTkFrame(parent, fg_color=_UI_SURFACE, height=30)
            tag_row.pack_propagate(False)
            tag_row.pack(fill="x", padx=10, pady=(0, 2))
            _label(tag_row, text=self._tr("t5.tag_slot", n=i + 1), width=88, anchor="w").pack(side="left")
            ctk.CTkCheckBox(tag_row, text="", variable=self._t5_tag_en[i]).pack(side="left", padx=(0, 6))
            ctk.CTkEntry(
                tag_row,
                textvariable=self._t5_tag_txt[i],
                placeholder_text=self._tr("t5.tag_placeholder"),
            ).pack(side="left", fill="x", expand=True)

        preset_fr = ctk.CTkFrame(parent, fg_color=_UI_SURFACE, height=32)
        preset_fr.pack_propagate(False)
        preset_fr.pack(fill="x", **pad)
        _label(preset_fr, text=self._tr("t5.preset_label"), width=120, anchor="w").pack(side="left")
        none_lbl = self._tr("t5.preset_none")
        self._t5_preset_menu = ctk.CTkOptionMenu(
            preset_fr,
            values=[none_lbl],
            variable=self._t5_preset_pick,
            command=self._t5_on_preset_menu_change,
            width=200,
        )
        self._t5_preset_menu.pack(side="left", padx=(0, 8))
        ctk.CTkEntry(
            preset_fr,
            textvariable=self._t5_preset_name,
            placeholder_text=self._tr("t5.preset_name_ph"),
            width=160,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            preset_fr,
            text=self._tr("t5.preset_save"),
            width=_btn_w(self._tr("t5.preset_save")),
            height=_BTN_H,
            command=self._t5_save_preset_click,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            preset_fr,
            text=self._tr("t5.preset_delete"),
            width=_btn_w(self._tr("t5.preset_delete")),
            height=_BTN_H,
            command=self._t5_delete_preset_click,
        ).pack(side="left")

        runf = ctk.CTkFrame(parent, fg_color=_UI_SURFACE, height=34)
        runf.pack_propagate(False)
        runf.pack(fill="x", **pad)
        ctk.CTkButton(
            runf,
            text=self._tr("t5.fill_new_leaf"),
            width=_btn_w(self._tr("t5.fill_new_leaf")),
            height=_BTN_H,
            command=self._t5_fill_new_leaf,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkCheckBox(runf, text=self._tr("t3.preview_only"), variable=self._t5_dry).pack(
            side="left", padx=(0, 12)
        )
        ctk.CTkCheckBox(runf, text=self._tr("t5.selected_only"), variable=self._t5_use_selected).pack(
            side="left", padx=(0, 12)
        )
        ctk.CTkButton(
            runf,
            text=self._tr("t3.rename_disk"),
            width=_btn_w(self._tr("t3.rename_disk")),
            height=30,
            fg_color="#1f538d",
            command=self._t5_run_renames,
        ).pack(side="left")

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
            "resolution_mode": (self._t5_resolution_mode.get() or "heightp").strip(),
            "tag_enabled": [bool(self._t5_tag_en[i].get()) for i in range(5)],
            "tag_text": [self._t5_tag_txt[i].get() for i in range(5)],
        }

    def _t5_apply_preset_dict(self, d: dict) -> None:
        if not isinstance(d, dict):
            return
        tml = d.get("title_max_len", 15)
        try:
            tml = int(tml)
        except (TypeError, ValueError):
            tml = 15
        self._t5_title_max.set(str(max(1, min(200, tml))))
        self._t5_include_year.set(bool(d.get("include_year", True)))
        self._t5_include_resolution.set(bool(d.get("include_resolution", True)))
        self._t5_include_rating.set(bool(d.get("include_rating", True)))
        rm = str(d.get("resolution_mode") or "heightp").strip().lower()
        self._t5_resolution_mode.set(rm if rm in ("heightp", "wxh") else "heightp")
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
        return row_passes_list_filters(
            self._t5_filter.get(),
            self._t5_filter_exclude.get(),
            file_path=row.get("file_path", ""),
            file_name=row.get("file_name", ""),
            new_leaf=row.get("new_leaf", ""),
            scene_title=row.get("scene_title", ""),
            scene_tags=row.get("scene_tags", ""),
            scene_markers=row.get("scene_markers", ""),
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
            "resolution_mode": self._t5_resolution_mode.get(),
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

    def _t5_sort_key(self, row: dict[str, str], col: str):
        if col == "path":
            return self._sort_key_text(row.get("file_path", ""))
        if col == "file_name":
            return self._sort_key_text(row.get("file_name", ""))
        if col == "scene_title":
            return self._sort_key_text(row.get("scene_title", ""))
        if col == "scene_tags":
            return self._sort_key_text(row.get("scene_tags", ""))
        if col == "scene_markers":
            return self._sort_key_text(row.get("scene_markers", ""))
        if col == "scene_date":
            return self._sort_key_text(row.get("scene_date", ""))
        if col == "proposed":
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

    def _t5_compute_leaf_for_row(self, row: dict[str, str]) -> tuple[str, str]:
        w, h = self._t5_dims_for_row(row)
        leaf, warn = build_schema_rename_leaf(
            row,
            video_width=w,
            video_height=h,
            **self._t5_schema_options_kwargs(),
        )
        return leaf, warn

    def _t5_rebuild_tree(self) -> None:
        if not hasattr(self, "_t5_tree"):
            return
        prev = self._t5_selected_indices()
        for item in self._t5_tree.get_children():
            self._t5_tree.delete(item)
        visible = [i for i, row in enumerate(self._t5_rows) if self._t5_row_visible(row)]
        visible.sort(
            key=lambda idx: self._t5_sort_key(self._t5_rows[idx], self._t5_sort_col),
            reverse=self._t5_sort_desc,
        )
        for i in visible:
            row = self._t5_rows[i]
            leaf, _w = self._t5_compute_leaf_for_row(row)
            self._t5_tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    row.get("file_path", ""),
                    row.get("file_name", ""),
                    row.get("scene_title", ""),
                    row.get("scene_tags", ""),
                    row.get("scene_markers", ""),
                    row.get("scene_date", ""),
                    leaf or "—",
                ),
            )
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
        exe = find_ffprobe_executable()
        if not exe:
            self._log(self._tr("log.t5_no_ffprobe"))
            return
        vis = self._t5_visible_indices()
        ok = 0
        for i in vis:
            row = self._t5_rows[i]
            key = self._t5_cache_key_for_row(row)
            if not key:
                continue
            w, h, err = ffprobe_video_size(key, ffprobe_exe=exe)
            if w and h:
                self._t5_ffprobe_cache[key] = (w, h)
                ok += 1
            elif err:
                fp = row.get("file_path", "")
                self._log(self._tr("log.t5_probe_row_fail", path=fp, err=err[:120]))
        self._log(self._tr("log.t5_probed", ok=ok, total=len(vis)))
        self._t5_rebuild_tree()

    def _t5_fill_new_leaf(self, *, silent: bool = False) -> None:
        idxs = self._t5_selected_indices() if self._t5_use_selected.get() else self._t5_visible_indices()
        n = 0
        tags_only = bool(self._t5_tags_only_mode.get())
        for i in idxs:
            if i < 0 or i >= len(self._t5_rows):
                continue
            row = self._t5_rows[i]
            if tags_only:
                base_leaf = (row.get("new_leaf") or "").strip() or (row.get("file_name") or "").strip()
                leaf = append_schema_tags_to_leaf(
                    base_leaf,
                    tag_enabled=[self._t5_tag_en[k].get() for k in range(5)],
                    tag_text=[self._t5_tag_txt[k].get() for k in range(5)],
                )
            else:
                leaf, _w = self._t5_compute_leaf_for_row(row)
            if leaf:
                self._t5_rows[i]["new_leaf"] = leaf
                n += 1
        if not silent:
            self._log(self._tr("log.t5_fill_done", n=n))
        self._t5_rebuild_tree()

    def _t5_run_renames(self) -> None:
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
        renamed, skipped, log_lines = apply_file_renames(
            self._t5_rows, dry_run=dry, only_indices=rename_indices
        )
        for line in log_lines:
            self._log(line)
        self._log(self._tr("log.t5_rename_summary", renamed=renamed, skipped=skipped, dry=dry))
        self._t5_rebuild_tree()
        self._save_settings()

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

        self._log(self._tr("log.t1_export_header"))
        try:
            r = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(Path(ps1).parent),
            )
        except OSError as e:
            self._log(self._tr("log.powershell_fail", e=e))
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
        rows = scan_folder_files(root, recursive=self._t2_recursive.get(), patterns=patterns or None)
        write_rename_csv(Path(out), rows, self._app_csv_delim())
        self._log(self._tr("log.wrote_items", n=len(rows), out=out))
        self._last_shared_csv = str(Path(out).resolve())
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
        return row_passes_list_filters(
            self._t4_filter.get(),
            self._t4_filter_exclude.get(),
            file_path=row.get("file_path", ""),
            file_name=row.get("file_name", ""),
            new_leaf=row.get("new_leaf", ""),
            scene_title=row.get("scene_title", ""),
            scene_tags=row.get("scene_tags", ""),
            scene_markers=row.get("scene_markers", ""),
        )

    def _t4_rebuild_tree(self) -> None:
        if not hasattr(self, "_t4_tree"):
            return
        prev = self._t4_selected_indices()
        for item in self._t4_tree.get_children():
            self._t4_tree.delete(item)
        visible = [i for i, row in enumerate(self._t4_rows) if self._t4_row_visible(row)]
        visible.sort(
            key=lambda idx: self._t4_sort_key(self._t4_rows[idx], self._t4_sort_col),
            reverse=self._t4_sort_desc,
        )
        for i in visible:
            row = self._t4_rows[i]
            self._t4_tree.insert(
                "",
                "end",
                iid=str(i),
                values=(row.get("file_path", ""), row.get("file_name", ""), row.get("scene_id", "")),
            )
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

        sub = sanitize_windows_dir_component(filter_stub_for_subfolder_suggest(self._t4_filter.get())) or "moved"
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
        return row_passes_list_filters(
            self._t3_filter.get(),
            self._t3_filter_exclude.get(),
            file_path=row.get("file_path", ""),
            file_name=row.get("file_name", ""),
            new_leaf=row.get("new_leaf", ""),
            scene_title=row.get("scene_title", ""),
            scene_tags=row.get("scene_tags", ""),
            scene_markers=row.get("scene_markers", ""),
        )

    def _t3_rebuild_tree(self) -> None:
        prev = self._t3_selected_indices()
        for item in self._tree.get_children():
            self._tree.delete(item)
        visible = [i for i, row in enumerate(self._rows) if self._t3_row_visible(row)]
        visible.sort(
            key=lambda idx: self._t3_sort_key(self._rows[idx], self._t3_sort_col),
            reverse=self._t3_sort_desc,
        )
        for i in visible:
            row = self._rows[i]
            self._tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    row.get("file_path", ""),
                    row.get("file_name", ""),
                    row.get("new_leaf", ""),
                ),
            )
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
        menu.add_command(label=self._tr("ctx.t5_edit_scene_title"), command=self._t5_edit_scene_title_selected)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _t5_edit_scene_title_selected(self) -> None:
        idxs = self._t5_selected_indices()
        if not idxs:
            self._log(self._tr("log.select_item"))
            return
        first = idxs[0]
        current = ""
        if 0 <= first < len(self._t5_rows):
            current = (self._t5_rows[first].get("scene_title") or "").strip()
        entered = simpledialog.askstring(
            self._tr("dlg.t5_edit_title_title"),
            self._tr("dlg.t5_edit_title_prompt"),
            initialvalue=current,
            parent=self,
        )
        if entered is None:
            return
        new_title = entered.strip()
        for i in idxs:
            if 0 <= i < len(self._t5_rows):
                self._t5_rows[i]["scene_title"] = new_title
        self._log(self._tr("log.t5_title_updated", n=len(idxs)))
        self._t5_rebuild_tree()
        self._ttk_restore_row_selection(self._t5_tree, idxs)

    def _t3_tree_context_menu(self, event) -> None:
        row_id = self._tree.identify_row(event.y)
        if row_id:
            self._tree.selection_set(row_id)
            self._tree.focus(row_id)
        menu = Menu(self, tearoff=0)
        menu.add_command(label=self._tr("ctx.copy_folder_path"), command=self._t3_copy_selected_path)
        menu.add_command(label=self._tr("ctx.open_in_explorer"), command=self._t3_open_selected_path)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _t3_apply_leaf_selection(self) -> None:
        sel_idx = self._t3_selected_indices()
        if not sel_idx:
            self._log(self._tr("log.select_item"))
            return
        val = self._t3_edit_leaf.get().strip()
        for i in sel_idx:
            if 0 <= i < len(self._rows):
                self._rows[i]["new_leaf"] = val
        self._t3_rebuild_tree()
        self._t3_restore_selection(sel_idx)

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
        self._t3_rebuild_tree()

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
        self._t3_rebuild_tree()
        self._t3_restore_selection(indices)

    def _t3_apply_find_replace_filtered(self) -> None:
        find = self._t3_find.get()
        if not find:
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
        self._t3_rebuild_tree()
        self._save_settings()

    def _t3_apply_find_replace_selected(self) -> None:
        find = self._t3_find.get()
        if not find:
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
        only = self._t3_only_under.get().strip() or None
        dry = self._t3_dry.get()
        renamed, skipped, lines = apply_file_renames(self._rows, only_under_folder=only, dry_run=dry)
        for line in lines:
            self._log(line + "\n")
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
        moved, skipped, lines = move_files_only(
            self._t4_rows,
            indices,
            target_folder=target,
            subfolder=self._t4_subfolder.get(),
            dry_run=dry,
            per_source_subfolder=per_source,
        )
        for line in lines:
            self._log(line + "\n")
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

    def _open_settings_dialog(self) -> None:
        if self._settings_dialog is not None:
            try:
                if self._settings_dialog.winfo_exists():
                    self._settings_dialog.focus()
                    return
            except TclError:
                pass
            self._settings_dialog = None

        top = ctk.CTkToplevel(self, fg_color=_UI_SURFACE)
        self._settings_dialog = top
        top.title(self._tr("settings.title"))
        top.geometry("460x520")
        top.minsize(400, 420)
        top.transient(self)
        top.grab_set()

        pad = {"padx": 14, "pady": (8, 6)}
        outer = ctk.CTkScrollableFrame(top, fg_color=_UI_SURFACE)
        outer.pack(fill="both", expand=True, padx=4, pady=4)

        _label(
            outer,
            text=self._tr("settings.intro"),
            anchor="w",
            font=ctk.CTkFont(weight="bold"),
        ).pack(fill="x", **pad)

        appearance = ctk.StringVar(value=self._appearance_mode.get())
        delim = ctk.StringVar(value=self._t1_delim.get())
        url = ctk.StringVar(value=self._t1_url.get())
        api = ctk.StringVar(value=self._t1_api.get())
        gql = ctk.StringVar(value=self._t1_graphql_path.get())
        lang_choice = ctk.StringVar(value=self._norm_lang_code(self._ui_language.get()))

        _label(outer, text=self._tr("settings.language"), anchor="w", font=ctk.CTkFont(weight="bold")).pack(
            fill="x", **pad
        )
        ctk.CTkSegmentedButton(
            outer,
            values=["en", "de", "es", "fr"],
            variable=lang_choice,
        ).pack(anchor="w", padx=14, pady=(0, 4))
        _label(
            outer,
            text=self._tr("settings.language_hint"),
            anchor="w",
            wraplength=400,
            justify="left",
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", padx=14, pady=(0, 8))

        _label(outer, text=self._tr("settings.appearance"), anchor="w", font=ctk.CTkFont(weight="bold")).pack(
            fill="x", **pad
        )
        ctk.CTkSegmentedButton(outer, values=["dark", "light", "system"], variable=appearance).pack(
            anchor="w", padx=14, pady=(0, 4)
        )

        _label(
            outer,
            text=self._tr("settings.column_sep"),
            anchor="w",
        ).pack(fill="x", **pad)
        ctk.CTkSegmentedButton(outer, values=[";", ","], variable=delim).pack(anchor="w", padx=14, pady=(0, 8))
        _label(
            outer,
            text=self._tr("settings.csv_detect"),
            anchor="w",
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", padx=14, pady=(0, 8))

        _label(outer, text=self._tr("settings.stash_group"), anchor="w", font=ctk.CTkFont(weight="bold")).pack(
            fill="x", **pad
        )
        _label(
            outer,
            text=self._tr("settings.stash_hint"),
            anchor="w",
            wraplength=400,
            justify="left",
            text_color=_LABEL_HINT,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", **pad)

        for key, var, secret in (
            ("common.stash_url", url, False),
            ("common.api_key", api, True),
            ("settings.graphql_path_label", gql, False),
        ):
            row_f = ctk.CTkFrame(outer, fg_color=_UI_SURFACE)
            row_f.pack(fill="x", **pad)
            _label(row_f, text=self._tr(key), width=200, anchor="w").pack(side="left")
            ctk.CTkEntry(row_f, textvariable=var, show="*" if secret else None).pack(
                side="left", fill="x", expand=True, padx=(0, 8)
            )

        gql_btns = ctk.CTkFrame(outer, fg_color=_UI_SURFACE)
        gql_btns.pack(fill="x", padx=14, pady=(4, 8))
        gql_clear = self._tr("settings.graphql_clear")
        ctk.CTkButton(
            gql_btns,
            text=gql_clear,
            width=_btn_w(gql_clear),
            height=_BTN_H,
            command=lambda: gql.set(""),
        ).pack(side="left")

        btns = ctk.CTkFrame(top, fg_color=_UI_SURFACE)
        btns.pack(fill="x", padx=14, pady=(0, 12))

        def on_ok() -> None:
            old_lang = self._norm_lang_code(self._ui_language.get())
            m = (appearance.get() or "dark").strip().lower()
            if m not in ("dark", "light", "system"):
                m = "dark"
            self._appearance_mode.set(m)
            self._apply_user_appearance_setting()
            self._apply_ttk_treeview_style()

            d = delim.get().strip()
            self._t1_delim.set(d if d in (";", ",") else ";")

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
            if new_lang != old_lang:
                self._rebuild_main_ui()

        def on_cancel() -> None:
            top.grab_release()
            top.destroy()
            self._settings_dialog = None

        cancel_t = self._tr("common.cancel")
        ok_t = self._tr("common.ok")
        ctk.CTkButton(btns, text=cancel_t, width=_btn_w(cancel_t), height=_BTN_H, command=on_cancel).pack(
            side="right", padx=(8, 0)
        )
        ctk.CTkButton(
            btns, text=ok_t, width=_btn_w(ok_t, lo=52), height=_BTN_H, fg_color="#1f538d", command=on_ok
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
            "t3_only_under": self._t3_only_under.get(),
            "t3_find": self._t3_find.get(),
            "t3_replace": self._t3_replace.get(),
            "t3_replace_ci": self._t3_replace_ci.get(),
            "t3_dry": self._t3_dry.get(),
            "t4_csv": self._t4_csv.get(),
            "t4_filter": self._t4_filter.get(),
            "t4_filter_exclude": self._t4_filter_exclude.get(),
            "t4_target_folder": self._t4_target_folder.get(),
            "t4_subfolder": self._t4_subfolder.get(),
            "t4_per_source": self._t4_per_source.get(),
            "t4_dry": self._t4_dry.get(),
            "t4_use_selected": self._t4_use_selected.get(),
            "ui_language": self._ui_language.get(),
            "t5_csv": self._t5_csv.get(),
            "t5_filter": self._t5_filter.get(),
            "t5_filter_exclude": self._t5_filter_exclude.get(),
            "t5_title_max": self._t5_title_max.get(),
            "t5_include_year": self._t5_include_year.get(),
            "t5_include_resolution": self._t5_include_resolution.get(),
            "t5_include_rating": self._t5_include_rating.get(),
            "t5_resolution_mode": self._t5_resolution_mode.get(),
            "t5_dry": self._t5_dry.get(),
            "t5_use_selected": self._t5_use_selected.get(),
            "t5_tags_only_mode": self._t5_tags_only_mode.get(),
            "t5_tag_en": [self._t5_tag_en[i].get() for i in range(5)],
            "t5_tag_txt": [self._t5_tag_txt[i].get() for i in range(5)],
            "t5_preset_name": self._t5_preset_name.get(),
        }

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
        g("t3_only_under", self._t3_only_under)
        g("t3_find", self._t3_find)
        g("t3_replace", self._t3_replace)
        g("t3_replace_ci", self._t3_replace_ci)
        g("t3_dry", self._t3_dry)
        g("t4_csv", self._t4_csv)
        g("t4_filter", self._t4_filter)
        g("t4_filter_exclude", self._t4_filter_exclude)
        g("t4_target_folder", self._t4_target_folder)
        g("t4_subfolder", self._t4_subfolder)
        g("t4_per_source", self._t4_per_source)
        g("t4_dry", self._t4_dry)
        g("t4_use_selected", self._t4_use_selected)
        g("t5_csv", self._t5_csv)
        g("t5_filter", self._t5_filter)
        g("t5_filter_exclude", self._t5_filter_exclude)
        g("t5_title_max", self._t5_title_max)
        g("t5_include_year", self._t5_include_year)
        g("t5_include_resolution", self._t5_include_resolution)
        g("t5_include_rating", self._t5_include_rating)
        g("t5_resolution_mode", self._t5_resolution_mode)
        g("t5_dry", self._t5_dry)
        g("t5_use_selected", self._t5_use_selected)
        g("t5_tags_only_mode", self._t5_tags_only_mode)
        g("t5_preset_name", self._t5_preset_name)
        g("ui_language", self._ui_language)
        te = data.get("t5_tag_en")
        if isinstance(te, list):
            for i, v in enumerate(te[:5]):
                self._t5_tag_en[i].set(bool(v))
        tt = data.get("t5_tag_txt")
        if isinstance(tt, list):
            for i, v in enumerate(tt[:5]):
                self._t5_tag_txt[i].set(str(v) if v is not None else "")
        am = (self._appearance_mode.get() or "dark").strip().lower()
        if am not in ("dark", "light", "system"):
            am = "dark"
        self._appearance_mode.set(am)
        dd = self._t1_delim.get().strip()
        if dd not in (";", ","):
            self._t1_delim.set(";")
        ul = self._norm_lang_code(self._ui_language.get())
        self._ui_language.set(ul)
        rm = (self._t5_resolution_mode.get() or "heightp").strip().lower()
        if rm not in ("heightp", "wxh"):
            self._t5_resolution_mode.set("heightp")
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
