#!/usr/bin/env python3
"""CustomTkinter: Tab1 Stash file CSV, Tab2 disk scan CSV, Tab3 preview/search/rename (UTF-8 CSV)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from tkinter import Menu, TclError, filedialog, Scrollbar, ttk

import customtkinter as ctk

from file_rename_tools import (
    apply_file_renames,
    apply_find_replace_to_rows,
    apply_prefix_suffix_to_rows,
    read_rename_csv,
    rename_folder_dangerous,
    scan_folder_files,
    write_rename_csv,
)

_SETTINGS_PATH = Path(__file__).resolve().parent / "gui_file_tools_settings.json"
_DEFAULT_STASH_PS1 = Path(__file__).resolve().parent / "export_stash_files.ps1"
_ROOT = Path(__file__).resolve().parent


def _default_file_tools_csv_dir() -> Path:
    d = _ROOT / "file_tools_csv"
    d.mkdir(parents=True, exist_ok=True)
    return d


class FileToolsApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Stashmarker — file list & rename")
        self.geometry("960x900")
        self.minsize(640, 520)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._rows: list[dict[str, str]] = []
        self._csv_delim: str = ";"
        self._last_shared_csv = ""

        # Tab 1
        self._t1_ps1 = ctk.StringVar(value=str(_DEFAULT_STASH_PS1) if _DEFAULT_STASH_PS1.is_file() else "")
        self._t1_url = ctk.StringVar(value="http://127.0.0.1:9999")
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

        self._build_ui()
        self._load_settings()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _log(self, msg: str) -> None:
        self._log_box.configure(state="normal")
        self._log_box.insert("end", msg)
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _build_ui(self) -> None:
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=10, pady=(10, 4))
        tabs.add("1 · Stash file CSV")
        tabs.add("2 · Disk scan")
        tabs.add("3 · Rename")

        def _scroll_wrap(tab_label: str) -> ctk.CTkScrollableFrame:
            inner = ctk.CTkScrollableFrame(tabs.tab(tab_label), fg_color="transparent")
            inner.pack(fill="both", expand=True)
            return inner

        self._build_tab1(_scroll_wrap("1 · Stash file CSV"))
        self._build_tab2(_scroll_wrap("2 · Disk scan"))
        self._build_tab3(_scroll_wrap("3 · Rename"))

        log_f = ctk.CTkFrame(self)
        log_f.pack(fill="both", expand=False, padx=10, pady=(4, 10))
        ctk.CTkLabel(log_f, text="Log", anchor="w").pack(fill="x")
        self._log_box = ctk.CTkTextbox(log_f, height=200, activate_scrollbars=True)
        self._log_box.pack(fill="both", expand=True)
        self._log_box.configure(state="disabled")

    def _pad(self) -> dict:
        return {"padx": 10, "pady": (4, 6)}

    def _build_tab1(self, parent: ctk.CTkFrame) -> None:
        pad = self._pad()
        ctk.CTkLabel(
            parent,
            text="Export a file list from Stash (GraphQL findScenes). CSV is UTF-8 with BOM — "
            "paths keep ä, ö, ü, Ä, Ö, Ü, ß correctly for Excel and this tool.",
            anchor="w",
            wraplength=860,
            justify="left",
        ).pack(fill="x", **pad)
        ctk.CTkLabel(
            parent,
            text="Keep Stash on a current version. After you rename or move files outside Stash, run "
            "Stash → Tasks → Scan so the library matches disk — the export only reflects paths stored in Stash.",
            anchor="w",
            wraplength=860,
            justify="left",
            text_color=("gray25", "gray70"),
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", padx=10, pady=(0, 6))

        r = ctk.CTkFrame(parent, fg_color="transparent")
        r.pack(fill="x", **pad)
        ctk.CTkLabel(r, text="export_stash_files.ps1", width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(r, textvariable=self._t1_ps1).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(r, text="Browse…", width=90, command=self._browse_t1_ps1).pack(side="right")

        for label, var in (
            ("Stash URL", self._t1_url),
            ("API key (if login enabled)", self._t1_api),
            ("Output CSV", self._t1_out),
        ):
            rr = ctk.CTkFrame(parent, fg_color="transparent")
            rr.pack(fill="x", **pad)
            ctk.CTkLabel(rr, text=label, width=160, anchor="w").pack(side="left")
            ctk.CTkEntry(rr, textvariable=var, show="*" if "key" in label.lower() else None).pack(
                side="left", fill="x", expand=True, padx=(0, 8)
            )
            if "CSV" in label:
                ctk.CTkButton(rr, text="Browse…", width=90, command=self._browse_t1_out).pack(side="right")

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", **pad)
        ctk.CTkLabel(row, text="Delimiter", width=160, anchor="w").pack(side="left")
        seg = ctk.CTkSegmentedButton(row, values=[";", ","], variable=self._t1_delim)
        seg.pack(side="left")

        row2 = ctk.CTkFrame(parent, fg_color="transparent")
        row2.pack(fill="x", **pad)
        ctk.CTkLabel(row2, text="Per page", width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(row2, textvariable=self._t1_per_page, width=80).pack(side="left")

        ctk.CTkLabel(parent, text="Filters (optional, combined)", anchor="w").pack(fill="x", **pad)
        for label, var in (
            ("Path prefix (e.g. D:\\Media\\X)", self._t1_path_prefix),
            ("Path contains", self._t1_path_contains),
            ("File name contains", self._t1_name_contains),
            ("File name regex (PowerShell)", self._t1_name_regex),
        ):
            rr = ctk.CTkFrame(parent, fg_color="transparent")
            rr.pack(fill="x", **pad)
            ctk.CTkLabel(rr, text=label, width=200, anchor="w").pack(side="left")
            ctk.CTkEntry(rr, textvariable=var).pack(side="left", fill="x", expand=True)

        bf = ctk.CTkFrame(parent, fg_color="transparent")
        bf.pack(fill="x", **pad)
        ctk.CTkButton(bf, text="Run Stash export", height=36, command=self._run_t1_export).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(bf, text="Open output folder", command=self._open_t1_out_dir).pack(side="left", padx=(0, 8))
        ctk.CTkButton(bf, text="Load result in Tab 3", command=self._t1_push_to_tab3).pack(side="left")

    def _build_tab2(self, parent: ctk.CTkFrame) -> None:
        pad = self._pad()
        ctk.CTkLabel(
            parent,
            text="Scan a folder on disk (no Stash). Creates the same CSV columns as Tab 1 so you can use Tab 3. "
            "Unicode paths (äöü…) are preserved.",
            anchor="w",
            wraplength=860,
            justify="left",
        ).pack(fill="x", **pad)

        r = ctk.CTkFrame(parent, fg_color="transparent")
        r.pack(fill="x", **pad)
        ctk.CTkLabel(r, text="Folder to scan", width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(r, textvariable=self._t2_folder).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(r, text="Browse…", width=90, command=self._browse_t2_folder).pack(side="right")

        ctk.CTkCheckBox(parent, text="Include subfolders (recursive)", variable=self._t2_recursive).pack(
            anchor="w", **pad
        )

        rr = ctk.CTkFrame(parent, fg_color="transparent")
        rr.pack(fill="x", **pad)
        ctk.CTkLabel(rr, text="Name patterns (optional)", width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(rr, textvariable=self._t2_patterns, placeholder_text="e.g. *.mp4;*.mkv  (empty = all files)").pack(
            side="left", fill="x", expand=True
        )

        ro = ctk.CTkFrame(parent, fg_color="transparent")
        ro.pack(fill="x", **pad)
        ctk.CTkLabel(ro, text="Output CSV", width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(ro, textvariable=self._t2_out).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(ro, text="Browse…", width=90, command=self._browse_t2_out).pack(side="right")

        bf = ctk.CTkFrame(parent, fg_color="transparent")
        bf.pack(fill="x", **pad)
        ctk.CTkButton(bf, text="Run disk scan", height=36, command=self._run_t2_scan).pack(side="left", padx=(0, 8))
        ctk.CTkButton(bf, text="Load result in Tab 3", command=self._t2_push_to_tab3).pack(side="left")

    def _build_tab3(self, parent: ctk.CTkFrame) -> None:
        pad = self._pad()
        ctk.CTkLabel(
            parent,
            text="Load a CSV from Tab 1 or 2. Search filters the table. Use Ctrl/Shift-click to select multiple "
            "rows — Apply to selection / prefix-suffix on selected / find-replace on selected. Or use the "
            "“filtered rows” actions for all visible rows. After real renames, run Stash → Tasks → Scan.",
            anchor="w",
            wraplength=860,
            justify="left",
        ).pack(fill="x", **pad)

        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", **pad)
        ctk.CTkLabel(top, text="CSV file", width=100, anchor="w").pack(side="left")
        ctk.CTkEntry(top, textvariable=self._t3_csv).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(top, text="Browse…", width=80, command=self._browse_t3_csv).pack(side="right", padx=(4, 0))
        ctk.CTkButton(top, text="Load", width=70, command=self._t3_load_csv).pack(side="right", padx=(4, 0))
        ctk.CTkButton(top, text="Save CSV", width=90, command=self._t3_save_csv).pack(side="right")

        sf = ctk.CTkFrame(parent, fg_color="transparent")
        sf.pack(fill="x", **pad)
        ctk.CTkLabel(sf, text="Search / filter rows", width=160, anchor="w").pack(side="left")
        ent = ctk.CTkEntry(sf, textvariable=self._t3_filter, placeholder_text="path or file name substring…")
        ent.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ent.bind("<KeyRelease>", lambda e: self._t3_rebuild_tree())

        tree_frame = ctk.CTkFrame(parent)
        tree_frame.pack(fill="both", expand=True, **pad)
        style = ttk.Style()
        try:
            style.theme_use("clam")
            style.configure(
                "Treeview",
                background="#2b2b2b",
                foreground="#dce4ee",
                fieldbackground="#2b2b2b",
                rowheight=22,
            )
            style.configure("Treeview.Heading", background="#1f538d", foreground="#dce4ee")
        except Exception:
            pass

        scroll_y = Scrollbar(tree_frame, orient="vertical")
        self._tree = ttk.Treeview(
            tree_frame,
            columns=("path", "name", "new_leaf"),
            show="headings",
            height=14,
            yscrollcommand=scroll_y.set,
            selectmode="extended",
        )
        scroll_y.config(command=self._tree.yview)
        self._tree.heading("path", text="file_path")
        self._tree.heading("name", text="file_name")
        self._tree.heading("new_leaf", text="new_leaf")
        self._tree.column("path", width=420, minwidth=80)
        self._tree.column("name", width=160, minwidth=60)
        self._tree.column("new_leaf", width=220, minwidth=60)
        self._tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        self._tree.bind("<<TreeviewSelect>>", self._t3_on_select)
        self._tree.bind("<Double-1>", lambda e: self._t3_focus_edit_leaf())
        self._tree.bind("<Button-3>", self._t3_tree_context_menu)

        t3_path_btns = ctk.CTkFrame(parent, fg_color="transparent")
        t3_path_btns.pack(fill="x", padx=10, pady=(0, 4))
        ctk.CTkLabel(t3_path_btns, text="Selection:", width=90, anchor="w").pack(side="left")
        ctk.CTkButton(t3_path_btns, text="Copy folder path", width=140, command=self._t3_copy_selected_path).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(
            t3_path_btns,
            text="Reveal in file manager",
            width=180,
            command=self._t3_open_selected_path,
        ).pack(side="left")

        edit_row = ctk.CTkFrame(parent, fg_color="transparent")
        edit_row.pack(fill="x", **pad)
        ctk.CTkLabel(edit_row, text="new_leaf (selection)", width=180, anchor="w").pack(side="left")
        ctk.CTkEntry(edit_row, textvariable=self._t3_edit_leaf).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(edit_row, text="Apply to selection", width=140, command=self._t3_apply_leaf_selection).pack(
            side="right"
        )

        rule = ctk.CTkFrame(parent, fg_color="transparent")
        rule.pack(fill="x", **pad)
        ctk.CTkLabel(rule, text="Prefix", width=80, anchor="w").pack(side="left")
        ctk.CTkEntry(rule, textvariable=self._t3_prefix, width=120).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(rule, text="Suffix before ext", width=120, anchor="w").pack(side="left")
        ctk.CTkEntry(rule, textvariable=self._t3_suffix, width=120).pack(side="left", padx=(0, 12))
        rule_btns = ctk.CTkFrame(rule, fg_color="transparent")
        rule_btns.pack(side="left", padx=(8, 0))
        ctk.CTkButton(rule_btns, text="Apply to filtered rows", width=170, command=self._t3_apply_rule_filtered).pack(
            side="left", padx=(0, 6)
        )
        ctk.CTkButton(rule_btns, text="Apply to selected rows", width=170, command=self._t3_apply_rule_selected).pack(
            side="left"
        )

        fr_row = ctk.CTkFrame(parent, fg_color="transparent")
        fr_row.pack(fill="x", **pad)
        ctk.CTkLabel(fr_row, text="Find", width=80, anchor="w").pack(side="left")
        ctk.CTkEntry(fr_row, textvariable=self._t3_find, width=140).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(fr_row, text="Replace with", width=100, anchor="w").pack(side="left")
        ctk.CTkEntry(fr_row, textvariable=self._t3_replace, width=140).pack(side="left", padx=(0, 8))
        ctk.CTkCheckBox(fr_row, text="Case-insensitive", variable=self._t3_replace_ci).pack(
            side="left", padx=(0, 8)
        )
        fr_btns = ctk.CTkFrame(fr_row, fg_color="transparent")
        fr_btns.pack(side="left", padx=(4, 0))
        ctk.CTkButton(
            fr_btns, text="Find/replace filtered", width=150, command=self._t3_apply_find_replace_filtered
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            fr_btns, text="Find/replace selected", width=150, command=self._t3_apply_find_replace_selected
        ).pack(side="left")

        fr_hint = ctk.CTkFrame(parent, fg_color="transparent")
        fr_hint.pack(fill="x", padx=(0, 0), pady=(0, 4))
        ctk.CTkLabel(
            fr_hint,
            text="Uses current new_leaf when already set — you can Apply several times to chain replacements.",
            anchor="w",
            text_color=("gray30", "gray65"),
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=(80, 0))

        ou = ctk.CTkFrame(parent, fg_color="transparent")
        ou.pack(fill="x", **pad)
        ctk.CTkLabel(ou, text="Only under folder (optional)", width=180, anchor="w").pack(side="left")
        ctk.CTkEntry(ou, textvariable=self._t3_only_under).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(ou, text="Browse…", width=80, command=self._browse_t3_only_under).pack(side="right")

        runf = ctk.CTkFrame(parent, fg_color="transparent")
        runf.pack(fill="x", **pad)
        ctk.CTkCheckBox(runf, text="Dry run (no renames on disk)", variable=self._t3_dry).pack(side="left", padx=(0, 12))
        ctk.CTkButton(runf, text="Execute file renames", height=34, fg_color="#1f538d", command=self._t3_run_renames).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(runf, text="Clear new_leaf on filtered rows", command=self._t3_clear_filtered_leaves).pack(
            side="left"
        )

        warn_fr = ctk.CTkFrame(parent, fg_color=("#8b3a3a", "#5c1f1f"), corner_radius=8)
        warn_fr.pack(fill="x", **pad)
        ctk.CTkLabel(
            warn_fr,
            text="WARNING — FOLDER RENAME (DANGEROUS)\nRenames one directory on disk. Breaks stored paths in Stash, "
            "shortcuts, and this CSV until you rescan / reload. Not reversible from this tool. Use only if you "
            "understand the impact.",
            text_color=("#fff", "#ffcccc"),
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=10, pady=8)

        fr = ctk.CTkFrame(warn_fr, fg_color="transparent")
        fr.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(fr, text="Folder", width=80, anchor="w").pack(side="left")
        ctk.CTkEntry(fr, textvariable=self._t3_fold_src).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(fr, text="Browse…", width=80, command=self._browse_t3_fold_src).pack(side="right")

        fr2 = ctk.CTkFrame(warn_fr, fg_color="transparent")
        fr2.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(fr2, text="New name", width=80, anchor="w").pack(side="left")
        ctk.CTkEntry(fr2, textvariable=self._t3_fold_new, placeholder_text="new folder name only, no path").pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )

        ctk.CTkCheckBox(
            warn_fr,
            text="I understand this may break Stash paths and I will run a library scan afterward.",
            variable=self._t3_fold_confirm,
            text_color=("#fff", "#eee"),
        ).pack(anchor="w", padx=10, pady=(0, 6))

        ctk.CTkButton(
            warn_fr,
            text="Rename folder (dangerous)",
            fg_color="#8b0000",
            hover_color="#a52a2a",
            command=self._t3_run_folder_rename,
        ).pack(anchor="w", padx=10, pady=(0, 10))

    # --- Tab 1 ---
    def _browse_t1_ps1(self) -> None:
        p = filedialog.askopenfilename(filetypes=[("PowerShell", "*.ps1"), ("All", "*.*")])
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
            self._log(f"Folder not found: {folder}\n")

    def _run_t1_export(self) -> None:
        ps1 = self._t1_ps1.get().strip()
        if not ps1 or not Path(ps1).is_file():
            self._log("Tab 1: set a valid path to export_stash_files.ps1.\n")
            return
        out = self._t1_out.get().strip()
        if not out:
            out = str(_default_file_tools_csv_dir() / "stash_files.csv")
            self._t1_out.set(out)
        try:
            per_page = int(self._t1_per_page.get().strip())
        except ValueError:
            self._log("Per page must be an integer.\n")
            return
        delim = self._t1_delim.get().strip()
        if delim not in (";", ","):
            delim = ";"
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

        self._log("\n--- Tab 1: Stash file export ---\n")
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
            self._log(f"Failed to start PowerShell: {e}\n")
            return
        if r.stdout:
            self._log(r.stdout)
        if r.stderr:
            self._log(r.stderr)
        self._log(f"\nExit code: {r.returncode}\n")
        if r.returncode == 0:
            self._last_shared_csv = str(Path(out).resolve())
            self._t3_csv.set(self._last_shared_csv)
            self._log(f"Tip: switched Tab 3 CSV path to: {self._last_shared_csv}\n")
            self._save_settings()

    # --- Tab 2 ---
    def _browse_t2_folder(self) -> None:
        p = filedialog.askdirectory(title="Folder to scan")
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
            self._log("Tab 2: choose a folder to scan.\n")
            return
        root = Path(folder)
        if not root.is_dir():
            self._log(f"Not a directory: {root}\n")
            return
        out = self._t2_out.get().strip()
        if not out:
            out = str(_default_file_tools_csv_dir() / "disk_scan.csv")
            self._t2_out.set(out)
        patterns = self._parse_patterns()
        self._log(f"\n--- Tab 2: scanning {root} (recursive={self._t2_recursive.get()}) ---\n")
        rows = scan_folder_files(root, recursive=self._t2_recursive.get(), patterns=patterns or None)
        delim = ";"
        write_rename_csv(Path(out), rows, delim)
        self._log(f"Wrote {len(rows)} row(s) to {out}\n")
        self._last_shared_csv = str(Path(out).resolve())
        self._t3_csv.set(self._last_shared_csv)
        self._log(f"Tip: Tab 3 CSV path set to: {self._last_shared_csv}\n")
        self._save_settings()

    def _push_csv_path_to_tab3(self, out: str, err_msg: str) -> None:
        out = out.strip()
        if out and Path(out).is_file():
            self._t3_csv.set(str(Path(out).resolve()))
            self._t3_load_csv()
        else:
            self._log(err_msg)

    def _t1_push_to_tab3(self) -> None:
        self._push_csv_path_to_tab3(self._t1_out.get(), "Tab 1: run export first or set a valid output CSV.\n")

    def _t2_push_to_tab3(self) -> None:
        self._push_csv_path_to_tab3(self._t2_out.get(), "Tab 2: run a scan first or set a valid output CSV.\n")

    # --- Tab 3 ---
    def _browse_t3_csv(self) -> None:
        p = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if p:
            self._t3_csv.set(p)

    def _browse_t3_only_under(self) -> None:
        p = filedialog.askdirectory(title="Restrict renames to files under this folder")
        if p:
            self._t3_only_under.set(p)

    def _browse_t3_fold_src(self) -> None:
        p = filedialog.askdirectory(title="Folder to rename (dangerous)")
        if p:
            self._t3_fold_src.set(p)

    def _t3_load_csv(self) -> None:
        path = self._t3_csv.get().strip()
        if not path or not Path(path).is_file():
            self._log("Tab 3: set a valid CSV path.\n")
            return
        try:
            self._rows, self._csv_delim = read_rename_csv(Path(path))
        except OSError as e:
            self._log(f"Failed to read CSV: {e}\n")
            return
        self._log(f"Loaded {len(self._rows)} row(s) from {path}\n")
        self._t3_rebuild_tree()
        self._save_settings()

    def _t3_save_csv(self) -> None:
        path = self._t3_csv.get().strip()
        if not path:
            path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
            if not path:
                return
            self._t3_csv.set(path)
        try:
            write_rename_csv(Path(path), self._rows, self._csv_delim)
            self._log(f"Saved {len(self._rows)} row(s) to {path}\n")
        except OSError as e:
            self._log(f"Save failed: {e}\n")

    def _t3_row_visible(self, row: dict[str, str]) -> bool:
        q = self._t3_filter.get().strip().lower()
        if not q:
            return True
        fp = (row.get("file_path") or "").lower()
        fn = (row.get("file_name") or "").lower()
        nl = (row.get("new_leaf") or "").lower()
        return q in fp or q in fn or q in nl

    def _t3_rebuild_tree(self) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)
        for i, row in enumerate(self._rows):
            if not self._t3_row_visible(row):
                continue
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

    def _t3_selected_indices(self) -> list[int]:
        out: list[int] = []
        for iid in self._tree.selection():
            try:
                out.append(int(iid))
            except ValueError:
                continue
        return out

    def _t3_restore_selection(self, indices: list[int]) -> None:
        want = {str(i) for i in indices}
        have = [c for c in self._tree.get_children() if c in want]
        if not have:
            return
        self._tree.selection_set(have[0])
        for c in have[1:]:
            self._tree.selection_add(c)

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
            self._log("Select a row with a file_path first.\n")
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(folder)
            self.update()
        except TclError:
            self._log("Clipboard unavailable.\n")
            return
        self._log("Copied folder path to clipboard.\n")

    def _t3_open_selected_path(self) -> None:
        fp = self._t3_selected_file_path()
        if not fp:
            self._log("Select a row first.\n")
            return
        p = Path(fp).expanduser()
        try:
            rp = p.resolve(strict=False)
        except OSError:
            rp = p
        if sys.platform == "win32":
            if rp.is_file():
                ep = os.path.normpath(str(rp))
                if '"' in ep:
                    self._log("Path contains \"; opening parent folder only.\n")
                    if rp.parent.is_dir():
                        subprocess.Popen(f'explorer "{rp.parent}"', shell=True)
                    return
                subprocess.run(f'explorer /select,"{ep}"', shell=True, check=False)
            elif rp.is_dir():
                os.startfile(str(rp))  # type: ignore[attr-defined]
            elif rp.parent.is_dir():
                subprocess.Popen(f'explorer "{os.path.normpath(str(rp.parent))}"', shell=True)
            else:
                self._log(f"Path not found: {fp!r}\n")
        elif sys.platform == "darwin":
            if rp.is_file():
                subprocess.run(["open", "-R", str(rp)], check=False)
            elif rp.is_dir():
                subprocess.run(["open", str(rp)], check=False)
            elif rp.parent.is_dir():
                subprocess.run(["open", str(rp.parent)], check=False)
            else:
                self._log(f"Path not found: {fp!r}\n")
        else:
            if rp.is_dir():
                subprocess.run(["xdg-open", str(rp)], check=False)
            elif rp.parent.is_dir():
                subprocess.run(["xdg-open", str(rp.parent)], check=False)
            else:
                self._log(f"Path not found: {fp!r}\n")

    def _t3_tree_context_menu(self, event) -> None:
        row_id = self._tree.identify_row(event.y)
        if row_id:
            self._tree.selection_set(row_id)
            self._tree.focus(row_id)
        menu = Menu(self, tearoff=0)
        menu.add_command(label="Copy folder path", command=self._t3_copy_selected_path)
        menu.add_command(label="Reveal in file manager", command=self._t3_open_selected_path)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _t3_apply_leaf_selection(self) -> None:
        sel_idx = self._t3_selected_indices()
        if not sel_idx:
            self._log("Select a row first.\n")
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
            self._log("Prefix/suffix must not contain path separators.\n")
            return
        indices: list[int] = []
        for item in self._tree.get_children():
            try:
                indices.append(int(item))
            except ValueError:
                continue
        apply_prefix_suffix_to_rows(self._rows, indices, prefix=prefix, suffix_before_ext=suffix)
        self._log(f"Applied prefix/suffix to {len(indices)} visible row(s).\n")
        self._t3_rebuild_tree()

    def _t3_apply_rule_selected(self) -> None:
        prefix = self._t3_prefix.get()
        suffix = self._t3_suffix.get()
        if "\\" in prefix or "/" in prefix or "\\" in suffix or "/" in suffix:
            self._log("Prefix/suffix must not contain path separators.\n")
            return
        indices = self._t3_selected_indices()
        if not indices:
            self._log("Select one or more rows first.\n")
            return
        apply_prefix_suffix_to_rows(self._rows, indices, prefix=prefix, suffix_before_ext=suffix)
        self._log(f"Applied prefix/suffix to {len(indices)} selected row(s).\n")
        self._t3_rebuild_tree()
        self._t3_restore_selection(indices)

    def _t3_apply_find_replace_filtered(self) -> None:
        find = self._t3_find.get()
        if not find:
            self._log("Find/replace: \"Find\" must not be empty.\n")
            return
        replace_with = self._t3_replace.get()
        if "\\" in replace_with or "/" in replace_with or ":" in replace_with:
            self._log("Find/replace: replacement must not contain \\ / : (file name only).\n")
            return
        indices: list[int] = []
        for item in self._tree.get_children():
            try:
                indices.append(int(item))
            except ValueError:
                continue
        if not indices:
            self._log("No visible rows (load CSV and/or adjust filter).\n")
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
        self._log(
            f"Find/replace: set new_leaf on {updated} row(s)"
            f"{f', skipped {skipped} invalid' if skipped else ''} (visible rows).\n"
        )
        self._t3_rebuild_tree()
        self._save_settings()

    def _t3_apply_find_replace_selected(self) -> None:
        find = self._t3_find.get()
        if not find:
            self._log("Find/replace: \"Find\" must not be empty.\n")
            return
        replace_with = self._t3_replace.get()
        if "\\" in replace_with or "/" in replace_with or ":" in replace_with:
            self._log("Find/replace: replacement must not contain \\ / : (file name only).\n")
            return
        indices = self._t3_selected_indices()
        if not indices:
            self._log("Select one or more rows first.\n")
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
        self._log(
            f"Find/replace: set new_leaf on {updated} row(s)"
            f"{f', skipped {skipped} invalid' if skipped else ''} (selected rows).\n"
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
        self._log("Cleared new_leaf on visible rows.\n")

    def _t3_run_renames(self) -> None:
        if not self._rows:
            self._log("Load a CSV first.\n")
            return
        only = self._t3_only_under.get().strip() or None
        dry = self._t3_dry.get()
        renamed, skipped, lines = apply_file_renames(self._rows, only_under_folder=only, dry_run=dry)
        for line in lines:
            self._log(line + "\n")
        self._log(
            f"\n{'Dry run — ' if dry else ''}Processed: {renamed} rename(s), {skipped} skipped.\n"
        )
        self._t3_rebuild_tree()
        self._save_settings()

    def _t3_run_folder_rename(self) -> None:
        if not self._t3_fold_confirm.get():
            self._log("Folder rename: enable the confirmation checkbox first.\n")
            return
        src = self._t3_fold_src.get().strip()
        new_name = self._t3_fold_new.get().strip()
        if not src or not new_name:
            self._log("Folder rename: set folder and new name.\n")
            return
        old_p = Path(src)
        ok, msg = rename_folder_dangerous(old_p, new_name)
        self._log(f"Folder rename: {msg}\n")
        if ok:
            self._t3_fold_confirm.set(False)
        self._save_settings()

    # --- settings ---
    def _gather_settings(self) -> dict:
        return {
            "t1_ps1": self._t1_ps1.get(),
            "t1_url": self._t1_url.get(),
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
            "t3_only_under": self._t3_only_under.get(),
            "t3_find": self._t3_find.get(),
            "t3_replace": self._t3_replace.get(),
            "t3_replace_ci": self._t3_replace_ci.get(),
            "t3_dry": self._t3_dry.get(),
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
        g("t1_ps1", self._t1_ps1)
        g("t1_url", self._t1_url)
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
        g("t3_only_under", self._t3_only_under)
        g("t3_find", self._t3_find)
        g("t3_replace", self._t3_replace)
        g("t3_replace_ci", self._t3_replace_ci)
        g("t3_dry", self._t3_dry)

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
