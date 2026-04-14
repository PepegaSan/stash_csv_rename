# Stash — file list & batch rename

> **Status: work in progress** — Export, rename, and move-on-disk flows are not fully tested end-to-end yet. Use at your own risk; feedback is welcome. This is **not** a stable or “production-ready” release.

Small helper around **[Stash](https://github.com/stashapp/stash)**: export file paths (or scan a folder), edit names in a CSV or in the GUI, then rename or move files on disk.

**Main idea:** keep your library **structured on disk** by putting **relevant scene data into the file name** (title slug, year, short tag slots, resolution, rating) instead of relying only on the database or long paths. Tab 1–2 produce a **single CSV** you can filter and work through; Tab 3 applies manual or generated names; Tab 4 moves files into folders; **Tab 5** fills **“new file name”** from a **schema** so names stay consistent across many files.

**Tab 1** talks to your running Stash instance via GraphQL (same idea as the Stash web UI): it fetches file paths linked to scenes and saves them as CSV. For Stash login, API key, and setup, see the [Stash documentation](https://docs.stashapp.cc) and the [Stash repository](https://github.com/stashapp/stash).

**Important — keep the database in sync:** If you rename or move files **outside** Stash (e.g. with this tool), paths stored in Stash no longer match the disk. Run **Tasks → Scan** (library scan) in Stash afterward so entries match the files again. Do **not** run **Clean** before Scan if you want to keep your media.

## Quick start

- **Python 3** and **PowerShell** (Windows)
- **Install dependencies (Windows):** run **`install.bat`**, or manually: `pip install -r requirements.txt`
- **Optional for Tab 5 resolution:** `ffprobe` must be installed and available in `PATH` (typically from ffmpeg builds)
- Launch: **`start_file_tools.bat`** or `python gui_file_tools.py`

**Tab 2:** Scan a folder on disk (no Stash), same CSV shape as Tab 1.  
**Tab 3:** Load CSV, search + exclude filters, edit **new file name**, optional dry run, then rename on disk.  
**Tab 4:** Move filtered/selected rows into one target folder (optional subfolder). Only the **filesystem** changes; Stash is **not** updated via the API. After moving, run **Tasks → Scan** in Stash. Options: **per-source-folder** subfolders, **selected rows only** vs all search matches, **Preview only** to log planned moves.

### Tab 5 — schema-based names (structure in the filename)

Tab 5 is for **batch-generating leaf file names** from Stash/CSV fields so **metadata lives in the name**, not only in Stash:

- **Base:** scene **title**, truncated to a max length (default 15); if the title is empty, the current **file name** is used — **not** Stash tags or markers as the main stem.
- **Year:** optional, from CSV when available, otherwise from file timestamps (creation where supported, else modification).
- **Up to five optional `[…]` slots:** map to scene tag names or fixed text you choose (checkboxes + text per slot).
- **Resolution:** optional via **ffprobe** on the file (e.g. height-based `1080p`); requires `ffprobe` in `PATH`.
- **Rating:** optional from Stash when present in the export.

Workflow: load the same CSV as on Tab 3 (re-export with **`export_stash_files.ps1`** / Tab 1 if you need the extra columns), filter rows, tune the schema, **Fill “new file name” from schema**, then **Rename** like Tab 3. **Presets** (your patterns) are stored in **`schema_rename_presets.json`** next to the app — that file is **local only** and listed in `.gitignore` so nothing personal is published.

`scene_tags` and `scene_markers` remain in the CSV for the table and search (`tags:` / `markers:` filters on Tab 3–5).

## Stash export check (Tab 1)

On **Tab 1**, **“Check CSV export”** sends the same `findScenes` shape as `export_stash_files.ps1` (one page). If it succeeds, your Stash version still supports building the export CSV. It does **not** test moving files or updating paths inside Stash.

CSV is **UTF-8 with BOM** (Excel-friendly, accents preserved).

## Languages

The GUI supports **English, German, Spanish, and French**. Choose the language under **⚙ Settings** (stored in your local settings file, not in the repo). Strings are generated from `mklocales.py` into `locales/*.json` — after editing `mklocales.py`, run `python mklocales.py` before committing.

## Recent changes (high level)

- **Tab 5** schema rename: title/year/slots/resolution/rating → **new file name** column; presets in local JSON.
- **Tab 3 / Tab 4 / Tab 5:** search field plus **exclude** filter for the row list.
- **Tab 4** only moves files on disk; it does **not** call Stash’s GraphQL API to rewrite paths. After moves, use **Tasks → Scan** in Stash when those files were already in the library.
- **Locales:** four languages; settings for appearance, CSV separator, Stash URL / API key / GraphQL path (Tab 1 export and checks).

## Privacy / what not to commit

Do **not** commit:

- `gui_file_tools_settings.json` — Stash URL, API key, paths, language  
- `schema_rename_presets.json` — your rename presets and tag text  
- exported CSVs under `file_tools_csv/` — media paths  

All `*.csv` files anywhere in the tree are ignored so path lists are harder to commit by mistake (force-add only if you intentionally ship a sample).

## Files (overview)

| File | Role |
|------|------|
| `gui_file_tools.py` | GUI (CustomTkinter) |
| `file_rename_tools.py` | CSV & rename logic |
| `export_stash_files.ps1` | Export Stash → CSV |
| `apply_stash_file_renames.ps1` | Rename from CSV (CLI) |
| `install.bat` | Install / upgrade `pip` and dependencies |
| `start_file_tools.bat` | Windows launcher |

Generated locally (not committed): `file_tools_csv/`, `gui_file_tools_settings.json`, `schema_rename_presets.json` — see `.gitignore`.

## License

[MIT](LICENSE)
