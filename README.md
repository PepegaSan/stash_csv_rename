# Stash — file list & batch rename

Small helper: export file paths from **[Stash](https://github.com/stashapp/stash)** or scan a folder, set new names in a CSV or in the GUI, then rename files on disk.

**Tab 1** talks to your running Stash instance (same idea as the Stash web UI via the API): it fetches a list of file paths linked to scenes through GraphQL and saves them as CSV. For Stash itself, login, API key, and setup, see the [Stash documentation](https://docs.stashapp.cc) and the [Stash repository](https://github.com/stashapp/stash).

**Important — keep the database in sync:** If you rename or move files **outside** Stash (e.g. with this tool), paths stored in Stash no longer match the disk. Run **Tasks → Scan** (library scan) in Stash afterward so entries match the files again. Do **not** run **Clean** before Scan if you want to keep your media.

## Quick start

- **Python 3** and **PowerShell** (Windows)
- **Install dependencies (Windows):** run **`install.bat`**, or manually: `pip install -r requirements.txt`
- Launch: **`start_file_tools.bat`** or `python gui_file_tools.py`

**Tab 2:** Scan a folder on disk (no Stash), same CSV shape.  
**Tab 3:** Load CSV, filter, adjust names, optional dry run, then rename.

CSV is **UTF-8 with BOM** (Excel-friendly, accents preserved).

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
