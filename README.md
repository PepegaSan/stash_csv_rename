# Stash — file list & batch rename

> **Status: work in progress** — Export, rename, and move-on-disk flows are not fully tested end-to-end yet. Use at your own risk; feedback is welcome. This is **not** a stable or “production-ready” release.

Small helper: export file paths from **[Stash](https://github.com/stashapp/stash)** or scan a folder, set new names in a CSV or in the GUI, then rename files on disk.

**Tab 1** talks to your running Stash instance (same idea as the Stash web UI via the API): it fetches a list of file paths linked to scenes through GraphQL and saves them as CSV. For Stash itself, login, API key, and setup, see the [Stash documentation](https://docs.stashapp.cc) and the [Stash repository](https://github.com/stashapp/stash).

**Important — keep the database in sync:** If you rename or move files **outside** Stash (e.g. with this tool), paths stored in Stash no longer match the disk. Run **Tasks → Scan** (library scan) in Stash afterward so entries match the files again. Do **not** run **Clean** before Scan if you want to keep your media.

## Quick start

- **Python 3** and **PowerShell** (Windows)
- **Install dependencies (Windows):** run **`install.bat`**, or manually: `pip install -r requirements.txt`
- Launch: **`start_file_tools.bat`** or `python gui_file_tools.py`

**Tab 2:** Scan a folder on disk (no Stash), same CSV shape.  
**Tab 3:** Load CSV, filter, adjust names, optional dry run, then rename.  
**Tab 4:** Move currently filtered/selected rows into one target folder (optional subfolder). Only the **filesystem** is changed; Stash is **not** updated via the API. After moving, run **Tasks → Scan** in Stash so the library matches disk again. You can load the CSV, filter like on Tab 3, use **Preview only** to log the planned moves, and collapse the preview panel when you do not need it. Options include **per-source-folder** subfolders and **selected rows only** vs all search matches.

## Stash export check (Tab 1)

On **Tab 1**, the button **“Check CSV export”** sends the same `findScenes` shape as `export_stash_files.ps1` (one page). If it succeeds, your Stash version still supports building the export CSV. It does **not** test moving files or updating paths inside Stash.

CSV is **UTF-8 with BOM** (Excel-friendly, accents preserved).

## Languages

The GUI supports **English, German, Spanish, and French**. Choose the language under **⚙ Settings** (stored in your local settings file, not in the repo). Strings are generated from `mklocales.py` into `locales/*.json` — after editing `mklocales.py`, run `python mklocales.py` before committing.

## Recent changes (high level)

- **Tab 4** only moves files on disk; it does **not** call Stash’s GraphQL API to rewrite paths. After moves, use **Tasks → Scan** in Stash when those files were already in the library.
- **Tab 3 / Tab 4 UI:** Long hints and batch tools are grouped in **collapsible sections** so the main path stays short; Stash connection / CSV export checks live on **Tab 1** only (no duplicate buttons on Tab 3).
- **Locales:** four languages, one settings panel for appearance, CSV separator, and Stash URL / API key / GraphQL path used for Tab 1 export and checks.

## Privacy / what not to commit

Do **not** commit `gui_file_tools_settings.json` (API key, paths, language) or exported CSVs under `file_tools_csv/` — they are listed in `.gitignore`. All `*.csv` files anywhere in the tree are ignored too, so path lists are harder to commit by mistake (force-add only if you intentionally ship a sample).

## Files (overview)

| File | Role |
|------|------|
| `gui_file_tools.py` | GUI (CustomTkinter) |
| `file_rename_tools.py` | CSV & rename logic |
| `export_stash_files.ps1` | Export Stash → CSV |
| `apply_stash_file_renames.ps1` | Rename from CSV (CLI) |
| `install.bat` | Install / upgrade `pip` and dependencies |
| `start_file_tools.bat` | Windows launcher |

Generated locally (not committed): `file_tools_csv/`, `gui_file_tools_settings.json` — see `.gitignore`.

## License

[MIT](LICENSE)
