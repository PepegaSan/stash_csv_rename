#!/usr/bin/env python3
"""Visual-only mockup for a cleaner, compact GUI layout.

This file intentionally contains no real business logic.
It is a style sandbox to evaluate spacing, path-row density, and tab structure.
"""

from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_UI_SURFACE = ("gray95", "gray17")
_LABEL_HINT = ("#1a1a1a", "#d0d0d0")
_BTN_H = 28


def _btn_w(s: str, lo: int = 60, hi: int = 320) -> int:
    return max(lo, min(hi, int(len(s) * 6.8 + 20)))


class DesignTestApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__(fg_color=_UI_SURFACE)
        self.title("Stashmarker — Design Test (visual only)")
        self.geometry("1100x860")
        self.minsize(900, 620)

        top = ctk.CTkFrame(self, fg_color=_UI_SURFACE)
        top.pack(fill="x", padx=12, pady=(10, 6))
        ctk.CTkLabel(
            top,
            text="Design-Test: kompaktere Zeilen, kürzere Path-Inputs, aufgeräumte Abschnitte",
            text_color=_LABEL_HINT,
            fg_color=_UI_SURFACE,
        ).pack(side="left")
        ctk.CTkSwitch(top, text="Light Mode (optisch)").pack(side="right")

        tabs = ctk.CTkTabview(self, fg_color=_UI_SURFACE)
        tabs.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        t1 = tabs.add("Tab 1 Export")
        t3 = tabs.add("Tab 3 Rename")
        t4 = tabs.add("Tab 4 Move")
        t5 = tabs.add("Tab 5 Schema")

        self._build_export_tab(t1)
        self._build_rename_tab(t3)
        self._build_move_tab(t4)
        self._build_schema_tab(t5)

        log_head = ctk.CTkFrame(self, fg_color=_UI_SURFACE)
        log_head.pack(fill="x", padx=12, pady=(0, 4))
        ctk.CTkLabel(log_head, text="Log (Mockup)", fg_color=_UI_SURFACE).pack(side="left")
        ctk.CTkButton(log_head, text="Hide", width=70, height=_BTN_H).pack(side="right")

        self.log = ctk.CTkTextbox(self, height=130)
        self.log.pack(fill="both", expand=False, padx=12, pady=(0, 10))
        self.log.insert(
            "1.0",
            "[INFO] This is a visual-only test UI.\n"
            "[INFO] Buttons/inputs are non-functional placeholders.\n",
        )
        self.log.configure(state="disabled")

    def _section(self, parent: ctk.CTkFrame, title: str) -> ctk.CTkFrame:
        wrap = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        wrap.pack(fill="x", padx=10, pady=(4, 4))
        ctk.CTkLabel(
            wrap,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=_UI_SURFACE,
        ).pack(anchor="w", pady=(2, 4))
        body = ctk.CTkFrame(wrap, fg_color=_UI_SURFACE)
        body.pack(fill="x")
        return body

    def _path_row(self, parent: ctk.CTkFrame, label: str, placeholder: str = "") -> None:
        row = ctk.CTkFrame(parent, fg_color=_UI_SURFACE, height=32)
        row.pack(fill="x", pady=(0, 4))
        row.pack_propagate(False)
        ctk.CTkLabel(row, text=label, width=160, anchor="w", fg_color=_UI_SURFACE).pack(side="left")
        ctk.CTkEntry(row, placeholder_text=placeholder, height=30).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        ctk.CTkButton(row, text="Browse", width=86, height=_BTN_H).pack(side="right", padx=(4, 0))
        ctk.CTkButton(row, text="Open", width=72, height=_BTN_H).pack(side="right")

    def _small_action_row(self, parent: ctk.CTkFrame, labels: list[str]) -> None:
        row = ctk.CTkFrame(parent, fg_color=_UI_SURFACE, height=34)
        row.pack(fill="x", pady=(0, 4))
        row.pack_propagate(False)
        for i, lbl in enumerate(labels):
            ctk.CTkButton(row, text=lbl, width=_btn_w(lbl), height=_BTN_H).pack(side="left", padx=(0, 6 if i < len(labels) - 1 else 0))

    def _mock_table(self, parent: ctk.CTkFrame, cols: tuple[str, ...], rows: list[tuple[str, ...]]) -> None:
        frame = ctk.CTkFrame(parent, fg_color=_UI_SURFACE)
        frame.pack(fill="both", expand=True, padx=10, pady=(4, 6))
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=170 if c != "path" else 430, minwidth=80, stretch=False)
        for i, r in enumerate(rows):
            tree.insert("", "end", iid=str(i), values=r)
        tree.grid(row=0, column=0, sticky="nsew")
        y.grid(row=0, column=1, sticky="ns")
        x.grid(row=1, column=0, sticky="ew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

    def _build_export_tab(self, tab: ctk.CTkFrame) -> None:
        s = self._section(tab, "Stash Export (optik)")
        self._path_row(s, "PowerShell Script", "export_stash_files.ps1")
        self._path_row(s, "Output CSV", "file_tools_csv/stash_files.csv")
        row = ctk.CTkFrame(s, fg_color=_UI_SURFACE, height=32)
        row.pack(fill="x", pady=(0, 4))
        row.pack_propagate(False)
        ctk.CTkLabel(row, text="Stash URL", width=160, anchor="w", fg_color=_UI_SURFACE).pack(side="left")
        ctk.CTkEntry(row, height=30, placeholder_text="http://127.0.0.1:9999").pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        ctk.CTkButton(row, text="Check Export", width=120, height=_BTN_H).pack(side="right", padx=(4, 0))
        ctk.CTkButton(row, text="Run Export", width=100, height=_BTN_H).pack(side="right")
        self._small_action_row(s, ["Push to Tab 3", "Push to Tab 4", "Push to Tab 5"])

    def _build_rename_tab(self, tab: ctk.CTkFrame) -> None:
        s = self._section(tab, "Rename (optik)")
        self._path_row(s, "CSV File", "file_tools_csv/stash_files.csv")
        sr = ctk.CTkFrame(s, fg_color=_UI_SURFACE, height=32)
        sr.pack(fill="x", pady=(0, 4))
        sr.pack_propagate(False)
        ctk.CTkLabel(sr, text="Search", width=160, anchor="w", fg_color=_UI_SURFACE).pack(side="left")
        ctk.CTkEntry(sr, height=30, placeholder_text='path:"D:\\1_" tags:...').pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        ctk.CTkEntry(sr, width=280, height=30, placeholder_text="Exclude").pack(side="right")
        self._mock_table(
            tab,
            ("path", "name", "new_leaf"),
            [
                (r"D:\1\scene_a.mp4", "scene_a.mp4", "Scene A (2023) - [Tag].mp4"),
                (r"D:\1_2\scene_b.mp4", "scene_b.mp4", "Scene B (2022) - [Tag].mp4"),
            ],
        )
        self._small_action_row(s, ["Fill names", "Rename disk", "Clear new names"])

    def _build_move_tab(self, tab: ctk.CTkFrame) -> None:
        s = self._section(tab, "Move (optik)")
        self._path_row(s, "CSV File", "file_tools_csv/stash_files.csv")
        self._path_row(s, "Target Folder", r"D:\sorted")
        row = ctk.CTkFrame(s, fg_color=_UI_SURFACE, height=32)
        row.pack(fill="x", pady=(0, 4))
        row.pack_propagate(False)
        ctk.CTkLabel(row, text="Subfolder", width=160, anchor="w", fg_color=_UI_SURFACE).pack(side="left")
        ctk.CTkEntry(row, height=30, placeholder_text="optional").pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkCheckBox(row, text="per-source").pack(side="right")
        self._mock_table(
            tab,
            ("path", "name", "scene_id"),
            [
                (r"D:\1\clip_001.mp4", "clip_001.mp4", "10234"),
                (r"D:\1_2\clip_002.mp4", "clip_002.mp4", "10235"),
            ],
        )
        self._small_action_row(s, ["Preview only", "Selected only", "Move on disk"])

    def _build_schema_tab(self, tab: ctk.CTkFrame) -> None:
        s = self._section(tab, "Schema Rename (optik)")
        self._path_row(s, "CSV File", "file_tools_csv/stash_files.csv")

        row_a = ctk.CTkFrame(s, fg_color=_UI_SURFACE, height=32)
        row_a.pack(fill="x", pady=(0, 2))
        row_a.pack_propagate(False)
        ctk.CTkLabel(row_a, text="Title max length", width=160, anchor="w", fg_color=_UI_SURFACE).pack(side="left")
        ctk.CTkEntry(row_a, width=70, height=30).pack(side="left", padx=(0, 10))
        ctk.CTkCheckBox(row_a, text="Year (YYYY)").pack(side="left", padx=(0, 10))
        ctk.CTkCheckBox(row_a, text="Resolution").pack(side="left", padx=(0, 10))
        ctk.CTkCheckBox(row_a, text="Rating").pack(side="left")

        row_b = ctk.CTkFrame(s, fg_color=_UI_SURFACE, height=32)
        row_b.pack(fill="x", pady=(0, 2))
        row_b.pack_propagate(False)
        ctk.CTkLabel(row_b, text="Resolution label", width=160, anchor="w", fg_color=_UI_SURFACE).pack(side="left")
        ctk.CTkRadioButton(row_b, text="Height tier", value=1, variable=ctk.IntVar(value=1)).pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(row_b, text="Width x height", value=2, variable=ctk.IntVar(value=1)).pack(side="left")
        ctk.CTkButton(row_b, text="ffprobe start", width=120, height=_BTN_H).pack(side="right")

        ctk.CTkCheckBox(
            s,
            text="only add tags",
            fg_color=_UI_SURFACE,
        ).pack(anchor="w", pady=(0, 4))
        for n in range(1, 6):
            tr = ctk.CTkFrame(s, fg_color=_UI_SURFACE, height=30)
            tr.pack(fill="x", pady=(0, 2))
            tr.pack_propagate(False)
            ctk.CTkLabel(tr, text=f"Tag {n}", width=70, anchor="w", fg_color=_UI_SURFACE).pack(side="left")
            ctk.CTkCheckBox(tr, text="").pack(side="left", padx=(0, 6))
            ctk.CTkEntry(tr, height=28, placeholder_text="tag text").pack(side="left", fill="x", expand=True)

        self._mock_table(
            tab,
            ("path", "file_name", "scene_title", "scene_date", "proposed"),
            [
                (r"D:\1\clip_001.mp4", "clip_001.mp4", "Sample Scene", "2024-01-10", "Sample Sc (2024) - [tag].mp4"),
                (r"D:\1_2\clip_002.mp4", "clip_002.mp4", "Another Scene", "2023-03-11", "Another S (2023) - [tag].mp4"),
            ],
        )
        self._small_action_row(s, ["Fill names", "Rename disk", "Save preset"])


def main() -> None:
    app = DesignTestApp()
    app.mainloop()


if __name__ == "__main__":
    main()
