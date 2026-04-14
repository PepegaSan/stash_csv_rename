# Tab 5 — Schema names (reference)

Longer help that used to appear at the top of **Tab 5** in the app. The GUI stays compact; read this when you need detail.

---

## English

**What Tab 5 does**

Proposed file names use the scene title (truncated); if the title is empty, the current file name is used — not Stash tags/markers. Tags and markers are still exported in the CSV and shown in the list for search (`tags:` / `markers:`). Optional year/rating, five custom tag slots, optional ffprobe. Pattern: `ShortTitle (YYYY) - [custom] … [1080p] [rating].ext` — then fill “new file name” and rename like Tab 3.

**ffprobe / resolution**

After loading the CSV, click **ffprobe start** (next to the resolution options) so `[1080p]` etc. are filled. **ffprobe** comes with **FFmpeg**; install FFmpeg and ensure it is on your `PATH`.

**CSV columns**

Re-export from Tab 1 / `export_stash_files.ps1` for `scene_date`, `scene_rating`, `scene_tags` (all tag names), and `scene_markers` (marker titles). The year in `(YYYY)` uses `scene_date` when that cell has a usable year; otherwise it uses the file’s creation time on Windows, birth time on macOS when available, otherwise last modification (Linux often has no true creation time). Without title/tags/marker columns, Tab 5 falls back to the file name where needed.

---

## Deutsch

**Was Tab 5 macht**

Vorschlagsnamen nutzen den Szenentitel (gekürzt); ist der leer, den aktuellen Dateinamen — nicht die Stash-Tags/Marker. Tags/Marker stehen trotzdem in der CSV und in der Liste (Suche: `tags:` / `markers:`). Optional Jahr/Bewertung, fünf freie Tags, ffprobe.

**ffprobe / Auflösung**

Nach dem CSV-Laden **ffprobe start** klicken (neben den Auflösungsoptionen), damit `[1080p]` usw. gefüllt werden. **ffprobe** gehört zu **FFmpeg**; FFmpeg installieren und im `PATH` verfügbar machen.

**CSV-Spalten**

Neu exportieren (Tab 1 / `.ps1`) für `scene_date`, `scene_rating`, `scene_tags` und `scene_markers`. Das Jahr in „(JJJJ)“ nutzt `scene_date`, wenn daraus ein Jahr lesbar ist — sonst unter Windows das Erstellungsdatum der Datei, unter macOS den Geburtszeitstempel (birth time) falls vorhanden, sonst die letzte Änderung (unter Linux oft kein echtes Erstellungsdatum). Ohne Titel/Tags/Marker nutzt Tab 5 den Dateinamen.

---

## Español (resumen)

El nombre propuesto usa el título de escena; si falta, el nombre de archivo — no las etiquetas ni marcadores de Stash (siguen en CSV y lista; búsqueda `tags:` / `markers:`). Tras cargar el CSV, pulsa **ffprobe start** para rellenar `[1080p]` etc. (FFmpeg en PATH). Reexporta (tab 1 / `.ps1`) para `scene_date`, `scene_rating`, `scene_tags` y `scene_markers`.

---

## Français (résumé)

Le nom proposé utilise le titre de scène ; sinon le nom de fichier — pas les tags/marqueurs Stash (toujours dans le CSV et la liste ; recherche `tags:` / `markers:`). Après le CSV, cliquez sur **ffprobe start** pour remplir `[1080p]` etc. (FFmpeg dans le PATH). Réexportez (onglet 1 / `.ps1`) pour `scene_date`, `scene_rating`, `scene_tags` et `scene_markers`.
