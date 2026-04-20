# -*- coding: utf-8 -*-
"""Regenerate locales/*.json — run: python mklocales.py"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "locales"
EN: dict[str, str] = {}
DE: dict[str, str] = {}
ES: dict[str, str] = {}
FR: dict[str, str] = {}


def row(key: str, en: str, de: str, es: str, fr: str) -> None:
    EN[key] = en
    DE[key] = de
    ES[key] = es
    FR[key] = fr


# --- app & common ---
row(
    "app.window_title",
    "Stashmarker — file list & rename",
    "Stashmarker — Dateiliste & Umbenennen",
    "Stashmarker — lista de archivos y renombrado",
    "Stashmarker — liste de fichiers et renommage",
)
row("app.brand", "Stashmarker", "Stashmarker", "Stashmarker", "Stashmarker")
row("common.browse", "Browse…", "Durchsuchen…", "Examinar…", "Parcourir…")
row("common.load", "Load", "Laden", "Cargar", "Charger")
row("common.save", "Save", "Speichern", "Guardar", "Enregistrer")
row("common.cancel", "Cancel", "Abbrechen", "Cancelar", "Annuler")
row("common.ok", "OK", "OK", "Aceptar", "OK")
row("common.default", "Default", "Standard", "Predeterminado", "Défaut")
row("common.log", "Log", "Protokoll", "Registro", "Journal")
row(
    "common.progress_rename",
    "Rename on disk: {cur} / {total}",
    "Umbenennen: {cur} / {total}",
    "Renombrar en disco: {cur} / {total}",
    "Renommage sur disque : {cur} / {total}",
)
row(
    "common.progress_move",
    "Move on disk: {cur} / {total}",
    "Verschieben: {cur} / {total}",
    "Mover en disco: {cur} / {total}",
    "Déplacement sur disque : {cur} / {total}",
)
row(
    "common.progress_fill",
    "Fill new names: {cur} / {total}",
    "Namen füllen: {cur} / {total}",
    "Rellenar nombres: {cur} / {total}",
    "Remplir les noms : {cur} / {total}",
)
row(
    "common.progress_probe",
    "ffprobe: {cur} / {total}",
    "ffprobe: {cur} / {total}",
    "ffprobe: {cur} / {total}",
    "ffprobe : {cur} / {total}",
)
row(
    "common.work_background",
    "Working in background — the window stays responsive.",
    "Arbeitet im Hintergrund — das Fenster bleibt bedienbar.",
    "Trabajando en segundo plano — la ventana sigue respondiendo.",
    "Travail en arrière-plan — la fenêtre reste utilisable.",
)
row(
    "log.busy_export",
    "Tab 1: export already running — wait until it finishes.\n",
    "Tab 1: Export läuft bereits — bitte warten.\n",
    "Tab 1: exportación en curso — espere a que termine.\n",
    "Tab 1 : export déjà en cours — patientez.\n",
)
row(
    "log.busy_scan",
    "Tab 2: scan already running — wait until it finishes.\n",
    "Tab 2: Scan läuft bereits — bitte warten.\n",
    "Tab 2: análisis en curso — espere a que termine.\n",
    "Tab 2 : analyse déjà en cours — patientez.\n",
)
row(
    "log.busy_probe",
    "Tab 5: ffprobe batch already running — wait until it finishes.\n",
    "Tab 5: ffprobe-Lauf aktiv — bitte warten.\n",
    "Tab 5: ffprobe en curso — espere a que termine.\n",
    "Tab 5 : ffprobe déjà en cours — patientez.\n",
)
row("common.save_log", "Save log to file…", "Protokoll speichern…", "Guardar registro en archivo…", "Enregistrer le journal…")
row("common.clear_log", "Clear log", "Protokoll leeren", "Vaciar registro", "Vider le journal")
row(
    "common.log_collapse",
    "Hide log panel",
    "Log einklappen",
    "Ocultar registro",
    "Masquer le journal",
)
row(
    "common.log_expand",
    "Show log panel",
    "Log ausklappen",
    "Mostrar registro",
    "Afficher le journal",
)
row(
    "common.undo_last_rename",
    "Undo last rename",
    "Letzte Umbenennung rückgängig",
    "Deshacer último renombrado",
    "Annuler le dernier renommage",
)
row(
    "common.undo_last_move",
    "Undo last move",
    "Letzte Verschiebung rückgängig",
    "Deshacer último movimiento",
    "Annuler le dernier déplacement",
)
row(
    "common.undo_header",
    "Undo disk action (repeat)",
    "Festplatten-Aktion rückgängig (mehrfach)",
    "Deshacer acción en disco (repetir)",
    "Annuler action disque (répéter)",
)
row("common.csv_file", "CSV file", "CSV-Datei", "Archivo CSV", "Fichier CSV")
row("common.search", "Search", "Suche", "Buscar", "Recherche")
row(
    "common.search_syntax_hint",
    "Syntax: name: / path: / new: / title: / tags: / markers: = only that column (new: = CSV “new name”, often empty until filled; title: uses scene title or file stem if title empty) · ; = and · > § | OR = or · \"phrase\" = exact",
    "Kurz: name: / path: / new: / title: / tags: / markers: = nur diese Spalte (new: = CSV-Spalte „Neuer Name“, oft leer bis Füllen; title: = Szenentitel oder Dateiname ohne Endung wenn Titel leer) · ; = und · > § | OR = oder · \"Text\" = genau",
    "Resumen: name: / path: / new: / title: / tags: / markers: = solo esa columna (new: = «nuevo nombre» del CSV, vacío hasta rellenar; title: = título o nombre de archivo sin extensión si título vacío) · ; = y · > § | OR = o · \"texto\" = exacto",
    "Syntaxe : name: / path: / new: / title: / tags: / markers: = cette colonne (new: = colonne « nouveau nom », souvent vide ; title: = titre scène ou nom de fichier sans extension si titre vide) · ; = et · > § | OR = ou · « phrase » = exact",
)
row("common.exclude_filter", "Exclude (hide items)", "Ausschluss (Einträge ausblenden)", "Excluir (ocultar elementos)", "Exclure (masquer les éléments)")
row(
    "common.exclude_placeholder",
    "Words, comma-separated — or tags:… ; path:… (advanced)",
    "Komma-getrennt — oder tags:… ; path:… (Fortgeschritten)",
    "Palabras con comas — o tags:… ; path:… (avanzado)",
    "Mots séparés par des virgules — ou tags:… ; path:… (avancé)",
)
row(
    "common.exclude_syntax_hint",
    "Exclude uses the same syntax as search. Any item that matches the exclude box is hidden (after applying search). Leave empty to show all matches.",
    "Ausschluss nutzt dieselbe Syntax wie die Suche. Jeder Eintrag, der hier passt, wird ausgeblendet (nach der Suche). Leer lassen = alle Suchtreffer zeigen.",
    "La exclusión usa la misma sintaxis. Los elementos que coincidan se ocultan (después del filtro de búsqueda). Vacío = mostrar todos los resultados de búsqueda.",
    "L’exclusion utilise la même syntaxe. Les éléments qui correspondent sont masqués (après la recherche). Vide = afficher tous les résultats de la recherche.",
)
row("common.stash_url", "Stash URL", "Stash-URL", "URL de Stash", "URL Stash")
row("common.api_key", "API key (if login enabled)", "API-Schlüssel (falls Login aktiv)", "Clave API (si hay inicio de sesión)", "Clé API (si connexion activée)")
row("common.find", "Find", "Suchen", "Buscar", "Rechercher")
row("common.replace_with", "Replace with", "Ersetzen durch", "Reemplazar por", "Remplacer par")
row("common.prefix", "Prefix", "Präfix", "Prefijo", "Préfixe")
row("common.folder", "Folder", "Ordner", "Carpeta", "Dossier")
row("common.new_name", "New name", "Neuer Name", "Nombre nuevo", "Nouveau nom")
row(
    "common.ph.csv_path",
    "Path to your CSV file…",
    "Pfad zur CSV-Datei…",
    "Ruta al archivo CSV…",
    "Chemin vers le fichier CSV…",
)
row(
    "t3.ph.fold_src",
    "Full path of the folder to rename…",
    "Vollständiger Pfad des umzubenennenden Ordners…",
    "Ruta completa de la carpeta a renombrar…",
    "Chemin complet du dossier à renommer…",
)
row(
    "common.filter_ui_hint",
    "Menus pick the column and whether comma-separated words are combined with AND or OR. Commas separate words; quotes keep commas inside a phrase. Advanced: you can still type ; and | / OR in the box.",
    "Die Menüs wählen Spalte und ob Komma-Wörter mit UND bzw. ODER verknüpft werden. Kommas trennen Wörter; Anführungszeichen schützen Kommas im Text. Fortgeschritten: ; und | / OR direkt eingeben.",
    "Los menús eligen la columna y si las palabras separadas por comas van con Y u O. Las comas separan palabras; las comillas protegen comas dentro. Avanzado: ; y | / OR en el cuadro.",
    "Les menus choisissent la colonne et si les mots séparés par des virgules sont en ET ou OU. Les virgules séparent les mots ; les guillemets protègent une virgule à l’intérieur. Avancé : ; et | / OR dans la zone.",
)
row("filter.field.all", "All columns", "Alle Spalten", "Todas las columnas", "Toutes les colonnes")
row("filter.field.path", "Path", "Pfad", "Ruta", "Chemin")
row("filter.field.name", "File name", "Dateiname", "Nombre de archivo", "Nom de fichier")
row("filter.field.file_extension", "Extension", "Endung", "Extensión", "Extension")
row("filter.field.new_leaf", "New file name", "Neuer Dateiname", "Nuevo nombre", "Nouveau nom (col.)")
row("filter.field.scene_title", "Scene title", "Szenentitel", "Título de escena", "Titre scène")
row("filter.field.scene_tags", "Tags", "Tags", "Etiquetas", "Tags")
row("filter.field.scene_markers", "Markers", "Marker", "Marcadores", "Marqueurs")
row("filter.field.scene_id", "Scene ID", "Szenen-ID", "ID de escena", "ID scène")
row("filter.field.scene_date", "Date", "Datum", "Fecha", "Date")
row("filter.field.proposed", "Proposed name", "Vorschlagsname", "Nombre propuesto", "Nom proposé")
row("filter.combine.and", "AND", "UND", "Y", "ET")
row("filter.combine.or", "OR", "ODER", "O", "OU")

# tab titles (must match tabs.add / _scroll_wrap)
row("tab.1", "1 · Stash file CSV", "1 · Stash-Datei-CSV", "1 · CSV de archivos Stash", "1 · CSV fichiers Stash")
row("tab.2", "2 · Disk scan", "2 · Datenträger-Scan", "2 · Escaneo de disco", "2 · Analyse disque")
row("tab.3", "3 · Rename", "3 · Umbenennen", "3 · Renombrar", "3 · Renommer")
row("tab.4", "4 · Move on disk", "4 · Auf Festplatte verschieben", "4 · Mover en disco", "4 · Déplacer sur disque")
row("tab.5", "5 · Schema names", "5 · Schema-Namen", "5 · Nombres (esquema)", "5 · Noms (schéma)")
row("tab.6", "6 · Name sync", "6 · Namensabgleich", "6 · Sincronizar nombres", "6 · Sync noms")
row("tab.7", "7 · File sync", "7 · Datei-Sync", "7 · Sincronizar archivos", "7 · Sync fichiers")

# Tab 1
row(
    "t1.intro",
    "Export a file list from Stash (GraphQL findScenes). The CSV is saved as Excel-friendly UTF-8 with a BOM (byte order mark) so characters like ä, ö, ü, Ä, Ö, Ü, ß stay correct in Excel and here.",
    "Exportiert eine Dateiliste aus Stash (GraphQL findScenes). Die CSV wird als Excel-freundliches UTF-8 mit BOM gespeichert, damit Zeichen wie ä, ö, ü, ß in Excel und hier korrekt bleiben.",
    "Exporta una lista de archivos desde Stash (GraphQL findScenes). El CSV se guarda en UTF-8 con BOM compatible con Excel para que caracteres como ä, ö, ü se vean bien en Excel y aquí.",
    "Exporte une liste de fichiers depuis Stash (GraphQL findScenes). Le CSV est enregistré en UTF-8 avec BOM pour Excel, afin que ä, ö, ü, etc. restent corrects dans Excel et ici.",
)
row(
    "t1.hint_scan",
    "Keep Stash updated. If you rename or move files outside Stash, run Stash → Tasks → Scan so the database matches your disk — this export only shows paths Stash already knows.",
    "Halte Stash aktuell. Wenn du Dateien außerhalb von Stash umbenennst oder verschiebst: Stash → Tasks → Scan ausführen, damit die Datenbank zur Festplatte passt — der Export zeigt nur Pfade, die Stash schon kennt.",
    "Mantén Stash al día. Si renombras o mueves archivos fuera de Stash, ejecuta Stash → Tasks → Scan para que la base coincida con el disco: la exportación solo muestra rutas que Stash ya conoce.",
    "Gardez Stash à jour. Si vous renommez ou déplacez des fichiers hors de Stash, lancez Stash → Tasks → Scan pour que la base corresponde au disque — l’export ne montre que les chemins déjà connus de Stash.",
)
row("t1.export_script", "Export script (.ps1)", "Export-Skript (.ps1)", "Script de exportación (.ps1)", "Script d’export (.ps1)")
row("t1.graphql_path", "GraphQL path", "GraphQL-Pfad", "Ruta GraphQL", "Chemin GraphQL")
row(
    "t1.graphql_placeholder",
    "/graphql (default if empty)",
    "/graphql (Standard wenn leer)",
    "/graphql (predeterminado si está vacío)",
    "/graphql (défaut si vide)",
)
row(
    "t1.hint_settings",
    "Theme and column separator (; or ,) for saved CSV files, plus Stash URL/API for Tab 1 export: ⚙ top-right. Tabs 3 and 4 detect ; or , when you load a file. Saved CSVs use UTF-8 with BOM for Excel.",
    "Design und Spaltentrenner (; oder ,) für gespeicherte CSVs sowie Stash-URL/API für Tab-1-Export: ⚙ oben rechts. Tabs 3 und 4 erkennen ; oder , beim Laden. Gespeicherte CSVs: UTF-8 mit BOM für Excel.",
    "Tema y separador (; o ,) para CSV guardados y URL/API de Stash para export en pestaña 1: ⚙ arriba a la derecha. Las pestañas 3 y 4 detectan ; o , al cargar. CSV: UTF-8 con BOM para Excel.",
    "Thème et séparateur (; ou ,) pour les CSV enregistrés, plus URL/API Stash pour l’export (onglet 1) : ⚙ en haut à droite. Les onglets 3 et 4 détectent ; ou , à l’ouverture. CSV : UTF-8 avec BOM pour Excel.",
)
row("t1.batch_size", "Batch size (scenes per request)", "Stapelgröße (Szenen pro Anfrage)", "Tamaño de lote (escenas por solicitud)", "Taille du lot (scènes par requête)")
row("t1.filters_title", "Optional filters (all boxes must match)", "Optionale Filter (alle Felder müssen passen)", "Filtros opcionales (todas las casillas deben coincidir)", "Filtres optionnels (toutes les cases doivent correspondre)")
row("t1.path_prefix", "Path prefix (e.g. D:\\Media\\X)", "Pfad-Präfix (z. B. D:\\Medien\\X)", "Prefijo de ruta (p. ej. D:\\Media\\X)", "Préfixe de chemin (ex. D:\\Media\\X)")
row("t1.path_contains", "Path contains", "Pfad enthält", "La ruta contiene", "Le chemin contient")
row("t1.name_contains", "File name contains", "Dateiname enthält", "El nombre de archivo contiene", "Le nom de fichier contient")
row("t1.name_regex", "File name — regex (PowerShell)", "Dateiname — Regex (PowerShell)", "Nombre de archivo — regex (PowerShell)", "Nom de fichier — regex (PowerShell)")
row("t1.run_export", "Run Stash export", "Stash-Export starten", "Ejecutar exportación Stash", "Lancer l’export Stash")
row("t1.test_connection", "Test Stash connection", "Stash-Verbindung testen", "Probar conexión con Stash", "Tester la connexion Stash")
row(
    "t1.check_csv_export",
    "Check CSV export (GraphQL)",
    "CSV-Export prüfen (GraphQL)",
    "Comprobar exportación CSV (GraphQL)",
    "Vérifier export CSV (GraphQL)",
)
row("t1.open_out_folder", "Open output folder", "Ausgabeordner öffnen", "Abrir carpeta de salida", "Ouvrir le dossier de sortie")
row("t1.send_csv_to", "Send CSV to", "CSV senden an", "Enviar CSV a", "Envoyer le CSV vers")
row("t1.tab3_rename", "Tab 3 — rename", "Tab 3 — Umbenennen", "Pestaña 3 — renombrar", "Onglet 3 — renommer")
row("t1.tab4_move", "Tab 4 — move", "Tab 4 — Verschieben", "Pestaña 4 — mover", "Onglet 4 — déplacer")
row("t1.tab5_schema", "Tab 5 — schema", "Tab 5 — Schema", "Pestaña 5 — esquema", "Onglet 5 — schéma")
row("t1.label.save_csv", "Save list as (CSV)", "Liste speichern als (CSV)", "Guardar lista como (CSV)", "Enregistrer la liste (CSV)")
row(
    "t1.hint_connection_in_settings",
    "Stash connection details (URL, API key, GraphQL path, export script) are under \u2699 Settings.",
    "Stash-Zugang (URL, API-Schlüssel, GraphQL-Pfad, Export-Skript) steht unter \u2699 Einstellungen.",
    "Datos de conexión Stash (URL, API, GraphQL, script de exportación) están en \u2699 Ajustes.",
    "Connexion Stash (URL, clé API, chemin GraphQL, script d’export) : menu \u2699 Réglages.",
)
row(
    "t1.section_export_actions",
    "Export & checks",
    "Export & Prüfungen",
    "Exportación y comprobaciones",
    "Export et vérifications",
)
row(
    "settings.export_script_hint",
    "Used when you click “Run Stash export” on Tab 1.",
    "Wird beim Klick auf „Stash-Export starten“ in Tab 1 verwendet.",
    "Se usa al ejecutar el export en la pestaña 1.",
    "Utilisé quand vous lancez l’export Stash (onglet 1).",
)

# Tab 2
row(
    "t2.intro",
    "Scan a folder on your PC (no Stash). Produces the same CSV columns as Tab 1 so Tab 3 can open it. Unicode paths (äöü…) are kept. When you save, the separator is from ⚙ Settings; when you open a file, ; or , is detected automatically.",
    "Scannt einen Ordner auf dem PC (ohne Stash). Erzeugt dieselben CSV-Spalten wie Tab 1, damit Tab 3 öffnen kann. Unicode-Pfade (äöü…) bleiben erhalten. Beim Speichern: Trenner aus ⚙ Einstellungen; beim Öffnen werden ; oder , automatisch erkannt.",
    "Escanea una carpeta en tu PC (sin Stash). Produce las mismas columnas CSV que la pestaña 1 para abrirla en la 3. Se conservan rutas Unicode (äöü…). Al guardar, el separador viene de ⚙ Ajustes; al abrir, se detectan ; o , automáticamente.",
    "Analyse un dossier sur votre PC (sans Stash). Produit les mêmes colonnes CSV que l’onglet 1 pour l’onglet 3. Les chemins Unicode (äöü…) sont conservés. À l’enregistrement, le séparateur vient des ⚙ réglages ; à l’ouverture, ; ou , est détecté automatiquement.",
)
row("t2.folder_scan", "Folder to scan", "Zu durchsuchender Ordner", "Carpeta a analizar", "Dossier à analyser")
row(
    "t2.recursive",
    "Include files inside subfolders (all levels below the folder you pick)",
    "Dateien in Unterordnern einbeziehen (alle Ebenen unter dem gewählten Ordner)",
    "Incluir archivos en subcarpetas (todos los niveles bajo la carpeta elegida)",
    "Inclure les fichiers des sous-dossiers (tous les niveaux sous le dossier choisi)",
)
row("t2.file_types", "File types (optional)", "Dateitypen (optional)", "Tipos de archivo (opcional)", "Types de fichiers (optionnel)")
row(
    "t2.patterns_placeholder",
    "e.g. *.mp4;*.mkv  (empty = all files)",
    "z. B. *.mp4;*.mkv  (leer = alle Dateien)",
    "p. ej. *.mp4;*.mkv  (vacío = todos los archivos)",
    "ex. *.mp4;*.mkv  (vide = tous les fichiers)",
)
row("t2.save_list_csv", "Save list as (CSV)", "Liste speichern als (CSV)", "Guardar lista como (CSV)", "Enregistrer la liste (CSV)")
row("t2.run_scan", "Run disk scan", "Datenträger-Scan starten", "Escanear disco", "Lancer l’analyse disque")

# Tab 3
row(
    "t3.steps",
    "Steps: 1) Load CSV  2) Search / exclude (column + AND/OR menus, comma-separated words)  3) Batch rules (expand section): new name, prefix/suffix, find/replace, folder limit  4) Preview only  5) Rename on disk.\nMulti-select rows (Ctrl/Shift-click or drag): use Find/replace — selected items (or prefix/suffix on selected) so each file gets its own proposed name from that row. «Rename on disk: selected rows only» turns on after any «apply to selected» batch action and off after «apply to search matches»; change it before step 5 if you need a different scope.\nRight-click a list item for folder path / Explorer. Stash checks: Tab 1 (\u2699 Settings).",
    "Schritte: 1) CSV laden  2) Suche / Ausschluss (Spalte + UND/ODER, Komma-getrennt)  3) Batch-Regeln (aufklappen): neuer Name, Präfix/Suffix, Suchen/Ersetzen, Ordnerlimit  4) Nur Vorschau  5) Umbenennen.\nMehrfachauswahl (Strg-/Umschalt-Klick oder ziehen): Suchen/Ersetzen auf «Auswahl» (oder Präfix/Suffix auf Auswahl) erzeugt pro Datei einen eigenen Vorschlagsnamen. «Umbenennen: nur Auswahl» schaltet sich nach jedem «Auf ausgewählte Einträge anwenden» ein und nach «Auf Suchtreffer anwenden» aus — vor Schritt 5 bei Bedarf manuell ändern.\nRechtsklick: Ordner / Explorer. Stash: Tab 1 (\u2699 Einstellungen).",
    "Pasos: 1) CSV  2) Buscar / excluir (columna + Y/O, palabras con comas)  3) Reglas por lotes (desplegar)  4) Vista previa  5) Renombrar.\nSelección múltiple (Ctrl/Mayús o arrastrar): buscar/reemplazar en «selección» (o prefijo/sufijo en selección) propone un nombre distinto por fila. «Renombrar: solo selección» se activa tras «Aplicar a elementos seleccionados» y se desactiva tras «Aplicar a coincidencias»; ajústelo antes del paso 5 si hace falta.\nClic derecho: carpeta / Explorador. Stash: pestaña 1 (\u2699 Ajustes).",
    "Étapes : 1) CSV  2) Recherche / exclusion (colonne + ET/OU, mots séparés par des virgules)  3) Règles groupées (section repliable)  4) Aperçu  5) Renommer.\nSélection multiple (Ctrl/Maj ou glisser) : rechercher/remplacer sur « sélection » (ou préfixe/suffixe sur sélection) construit un nom proposé par ligne. « Renommer : lignes sélectionnées » s’active après « Appliquer aux éléments sélectionnés » et se désactive après « Appliquer aux résultats de recherche » ; modifiez-la avant l’étape 5 si besoin.\nClic droit : dossier / Explorateur. Stash : onglet 1 (\u2699 Réglages).",
)
row(
    "t3.section_batch_title",
    "Batch rules (prefix, find/replace, folder limit)",
    "Batch-Regeln (Präfix, Suchen/Ersetzen, Ordnerlimit)",
    "Reglas por lotes (prefijo, buscar/reemplazar, límite de carpeta)",
    "Règles groupées (préfixe, rechercher/remplacer, limite de dossier)",
)
row(
    "t3.section_folder_title",
    "Rename folder on disk (dangerous) — click to open",
    "Ordner auf der Festplatte umbenennen (gefährlich) — zum Öffnen klicken",
    "Renombrar carpeta en disco (peligroso) — pulsar para abrir",
    "Renommer un dossier sur disque (dangereux) — cliquer pour ouvrir",
)
row(
    "t3.hint_csv",
    "Load: ; or , is read from the file. Save: separator from ⚙ Settings (; or ,).",
    "Laden: ; oder , wird aus der Datei gelesen. Speichern: Trenner aus ⚙ Einstellungen (; oder ,).",
    "Cargar: ; o , se lee del archivo. Guardar: separador desde ⚙ Ajustes (; o ,).",
    "Chargement : ; ou , lu dans le fichier. Enregistrement : séparateur des ⚙ réglages (; ou ,).",
)
row(
    "t3.tree_context_hint",
    "Tip: right-click — copy folder path, file name, extension, or open Explorer. Multi-select with Ctrl/Shift or drag for batch rules on «selected items».",
    "Tipp: Rechtsklick — Ordnerpfad, Dateiname, Endung kopieren oder Explorer. Mehrfachauswahl mit Strg/Umschalt oder Ziehen für Batch auf «Auswahl».",
    "Consejo: clic derecho — copiar carpeta, nombre, extensión o Explorador. Multiselección con Ctrl/Mayús o arrastrar para reglas en «selección».",
    "Astuce : clic droit — copier dossier, nom, extension ou Explorateur. Multi-sélection (Ctrl/Maj ou glisser) pour les règles sur « sélection ».",
)
row("t3.save_csv", "Save CSV", "CSV speichern", "Guardar CSV", "Enregistrer CSV")
row(
    "t3.search_label",
    "Search (matching items stay visible)",
    "Suche (passende Einträge bleiben sichtbar)",
    "Búsqueda (los coincidentes siguen visibles)",
    "Recherche (les éléments correspondants restent visibles)",
)
row(
    "t3.filter_placeholder",
    "Words, comma-separated (e.g. vacation, 1080p) — or type path:… ; … | …",
    "Wörter, kommagetrennt (z. B. Urlaub, 1080p) — oder path:… ; … | …",
    "Palabras separadas por comas (p. ej. vacaciones, 1080p) — o path:… ; … | …",
    "Mots séparés par des virgules (ex. vacances, 1080p) — ou path:… ; … | …",
)
row(
    "t3.ph.new_leaf",
    "New file name for selected items",
    "Neuer Dateiname für ausgewählte Einträge",
    "Nuevo nombre para elementos seleccionados",
    "Nouveau nom pour les éléments sélectionnés",
)
row(
    "t3.ph.prefix",
    "Prefix to add",
    "Präfix anfügen",
    "Prefijo a añadir",
    "Préfixe à ajouter",
)
row(
    "t3.ph.suffix",
    "Suffix before extension",
    "Suffix vor der Endung",
    "Sufijo antes de la extensión",
    "Suffixe avant l’extension",
)
row(
    "t3.ph.find",
    "Text to find in file / new name",
    "Zu suchender Text (Datei / neuer Name)",
    "Texto a buscar en archivo / nombre",
    "Texte à chercher (fichier / nouveau nom)",
)
row(
    "t3.ph.replace",
    "Replace with",
    "Ersetzen durch",
    "Reemplazar por",
    "Remplacer par",
)
row(
    "t3.ph.only_under",
    "Only items under this folder path (optional)",
    "Nur Einträge unter diesem Ordner (optional)",
    "Solo elementos bajo esta carpeta (opcional)",
    "Seulement les éléments sous ce dossier (optionnel)",
)
row("t3.col.path", "Full path", "Voller Pfad", "Ruta completa", "Chemin complet")
row("t3.col.path_gap", "\u2502", "\u2502", "\u2502", "\u2502")
row("t3.col.name", "Current file name", "Aktueller Dateiname", "Nombre de archivo actual", "Nom de fichier actuel")
row("t3.col.ext", "Ext.", "Endung", "Ext.", "Ext.")
row("t3.col.new_leaf", "New file name", "Neuer Dateiname", "Nuevo nombre de archivo", "Nouveau nom de fichier")
row("t3.copy_folder", "Copy folder path", "Ordnerpfad kopieren", "Copiar ruta de carpeta", "Copier le chemin du dossier")
row("t3.open_explorer", "Open in Explorer", "Im Explorer öffnen", "Abrir en el Explorador", "Ouvrir dans l’Explorateur")
row("t3.new_name_selected", "New file name (selected items)", "Neuer Dateiname (ausgewählte Einträge)", "Nuevo nombre (elementos seleccionados)", "Nouveau nom (éléments sélectionnés)")
row("t3.apply_selected", "Apply to selected items", "Auf ausgewählte Einträge anwenden", "Aplicar a elementos seleccionados", "Appliquer aux éléments sélectionnés")
row("t3.suffix_before_ext", "Suffix (before .ext)", "Suffix (vor .ext)", "Sufijo (antes de .ext)", "Suffixe (avant .ext)")
row("t3.apply_search", "Apply to search matches", "Auf Suchtreffer anwenden", "Aplicar a coincidencias de búsqueda", "Appliquer aux résultats de recherche")
row("t3.ignore_case", "Ignore capital letters (A = a)", "Groß/Klein ignorieren (A = a)", "Ignorar mayúsculas (A = a)", "Ignorer la casse (A = a)")
row("t3.fr_search", "Find/replace — search matches", "Suchen/Ersetzen — Suchtreffer", "Buscar/reemplazar — coincidencias", "Rechercher/remplacer — résultats recherche")
row("t3.fr_selected", "Find/replace — selected items", "Suchen/Ersetzen — Auswahl", "Buscar/reemplazar — selección", "Rechercher/remplacer — sélection")
row(
    "t3.fr_hint",
    "Find/replace runs on **New file name** when your find text matches there (click Apply repeatedly to chain). If that column is filled but your find text is only in the **current file name**, the current name is used instead.",
    "Suchen/Ersetzen nutzt **Neuer Dateiname**, wenn der Suchtext dort vorkommt (mehrfach „Anwenden“ = Kette). Steht dort schon Text, der Suchtext aber nur im **aktuellen Dateinamen**, wird von dort ersetzt.",
    "Buscar/reemplazar usa **nuevo nombre** si ahí aparece el texto buscado (Aplicar varias veces encadena). Si esa columna tiene texto pero el buscado solo está en el **nombre actual**, se usa el nombre actual.",
    "Rechercher/remplacer utilise **nouveau nom** si le texte y est trouvé (Appliquer plusieurs fois enchaîne). Si cette colonne a du texte mais le texte cherché n’est que dans le **nom actuel**, le nom actuel est pris.",
)
row("t3.limit_folder", "Limit to folder (optional)", "Auf Ordner beschränken (optional)", "Limitar a carpeta (opcional)", "Limiter au dossier (optionnel)")
row("t3.preview_only", "Preview only (no changes on disk)", "Nur Vorschau (keine Änderungen auf der Festplatte)", "Solo vista previa (sin cambios en disco)", "Aperçu seulement (aucun changement sur disque)")
row(
    "t3.rename_selected_only",
    "Rename on disk: selected rows only",
    "Umbenennen: nur markierte Zeilen",
    "Renombrar en disco: solo filas seleccionadas",
    "Renommer sur disque : lignes sélectionnées seulement",
)
row("t3.rename_disk", "Rename files on disk", "Dateien auf der Festplatte umbenennen", "Renombrar archivos en disco", "Renommer les fichiers sur disque")
row("t3.clear_new_names", 'Clear "New file name" on search matches', "„Neuer Dateiname“ bei Suchtreffern leeren", "Borrar «nuevo nombre» en coincidencias", "Effacer « nouveau nom » sur les résultats")
row(
    "t3.folder_warn",
    "WARNING — RENAME A FOLDER (RISKY)\nRenames one folder on disk. Stash, shortcuts, and this CSV will point to old paths until you run Stash → Tasks → Scan and reload the CSV. This tool cannot undo the folder rename. Use only if you understand that.",
    "WARNUNG — ORDNER UMBENENNEN (RISKANT)\nBenennt einen Ordner auf der Festplatte um. Stash, Verknüpfungen und diese CSV zeigen auf alte Pfade, bis du Stash → Tasks → Scan ausführst und die CSV neu lädst. Dieses Tool kann das nicht rückgängig machen. Nur nutzen, wenn du das verstehst.",
    "ADVERTENCIA — RENOMBRAR CARPETA (RIESGO)\nRenombra una carpeta en disco. Stash, accesos directos y este CSV seguirán rutas viejas hasta ejecutar Stash → Tasks → Scan y recargar el CSV. La herramienta no puede deshacerlo. Úsalo solo si lo entiendes.",
    "AVERTISSEMENT — RENOMMER UN DOSSIER (RISQUÉ)\nRenomme un dossier sur disque. Stash, raccourcis et ce CSV pointeront vers d’anciens chemins jusqu’à Stash → Tasks → Scan et rechargement du CSV. L’outil ne peut pas annuler. À utiliser seulement si vous comprenez.",
)
row(
    "t3.fold_confirm",
    "I understand this may break Stash paths and I will run a library scan afterward.",
    "Ich verstehe, dass Stash-Pfade dadurch fehlerhaft werden können und ich danach einen Bibliotheks-Scan ausführe.",
    "Entiendo que puede romper rutas en Stash y ejecutaré un escaneo de biblioteca después.",
    "Je comprends que les chemins Stash peuvent casser et je lancerai un scan de bibliothèque ensuite.",
)
row("t3.fold_rename_btn", "Rename folder (dangerous)", "Ordner umbenennen (gefährlich)", "Renombrar carpeta (peligroso)", "Renommer le dossier (dangereux)")
row(
    "t3.fold_new_placeholder",
    "new folder name only, no path",
    "nur neuer Ordnername, kein Pfad",
    "solo nombre de carpeta nueva, sin ruta",
    "nouveau nom de dossier seulement, pas de chemin",
)

# Tab 4 (part 1)
row(
    "t4.intro_block",
    "A) Load CSV, search, set the move folder (optional subfolder), use Preview only first, then move.\nB) The CSV path is your file list, not the move target. When loading, ; or , is read from the file; CSV export uses the separator in ⚙ Settings. Stash URL / API / GraphQL for exports: ⚙ Settings.\nC) After moves, if Stash already knew those files: run Tasks → Scan. This tab does not call the Stash API.",
    "A) CSV laden, suchen, Zielordner setzen (optionaler Unterordner), zuerst „Nur Vorschau“, dann verschieben.\nB) Der CSV-Pfad ist die Dateiliste, nicht das Verschiebeziel. Beim Laden werden ; oder , aus der Datei gelesen; CSV-Export nutzt den Trenner aus ⚙ Einstellungen. Stash-URL / API / GraphQL für Exporte: ⚙ Einstellungen.\nC) Nach dem Verschieben, wenn Stash die Dateien kannte: Tasks → Scan. Dieser Tab ruft die Stash-API nicht auf.",
    "A) Cargar CSV, buscar, carpeta destino (subcarpeta opcional), vista previa primero, luego mover.\nB) La ruta del CSV es la lista de archivos, no el destino. Al cargar se leen ; o , del archivo; al exportar CSV se usa el separador de ⚙ Ajustes. URL / API / GraphQL de Stash para exportes: ⚙ Ajustes.\nC) Tras mover, si Stash ya indexó esos archivos: Tasks → Scan. Esta pestaña no llama a la API de Stash.",
    "A) Charger le CSV, recherche, dossier cible (sous-dossier optionnel), aperçu d’abord, puis déplacer.\nB) Le chemin CSV est la liste des fichiers, pas la cible. Au chargement, ; ou , vient du fichier ; à l’export CSV, le séparateur vient des ⚙ réglages. URL / API / GraphQL Stash pour l’export : ⚙ Réglages.\nC) Après déplacement, si Stash connaissait déjà ces fichiers : Tasks → Scan. Cet onglet n’appelle pas l’API Stash.",
)
row(
    "t4.section_path_tips_title",
    "Path tips (target vs list, subfolder, selected item…)",
    "Pfad-Hinweise (Ziel vs Liste, Unterordner, markierter Eintrag …)",
    "Consejos de rutas (destino vs lista, subcarpeta, elemento seleccionado…)",
    "Astuces chemins (cible vs liste, sous-dossier, élément sélectionné…)",
)
row("t4.export_csv", "Export CSV…", "CSV exportieren…", "Exportar CSV…", "Exporter CSV…")
row("t4.col.scene_id", "Stash scene ID (scene_id)", "Stash-Szenen-ID (scene_id)", "ID de escena Stash (scene_id)", "ID scène Stash (scene_id)")
row("t4.stats_empty", "Items: —", "Einträge: —", "Elementos: —", "Éléments : —")
row("t4.where_move", "Where to move files (full path)", "Wohin Dateien verschieben (voller Pfad)", "Dónde mover archivos (ruta completa)", "Où déplacer les fichiers (chemin complet)")
row(
    "t4.where_placeholder",
    "e.g. D:\\Archive — all moved files end up here (unless checkbox below)",
    "z. B. D:\\Archiv — alle verschobenen Dateien landen hier (außer Checkbox unten)",
    "p. ej. D:\\Archivo — todos los archivos movidos van aquí (salvo la casilla de abajo)",
    "ex. D:\\Archive — tous les fichiers déplacés vont ici (sauf la case ci-dessous)",
)
row(
    "t4.target_from_row",
    "Use selected item's folder",
    "Ordner aus markiertem Eintrag",
    "Carpeta del elemento seleccionado",
    "Dossier de l’élément sélectionné",
)
row("t4.subfolder_label", "Subfolder under that path (optional)", "Unterordner unter diesem Pfad (optional)", "Subcarpeta bajo esa ruta (opcional)", "Sous-dossier sous ce chemin (optionnel)")
row(
    "t4.sub_placeholder",
    "e.g. Sorted  →  final path is <move-folder>\\Sorted\\",
    "z. B. Sortiert  →  Ziel ist <Zielordner>\\Sortiert\\",
    "p. ej. Ordenado  →  ruta final <carpeta>\\Ordenado\\",
    "ex. Trié  →  chemin final <dossier>\\Trié\\",
)
row("t4.suggest", "Suggest from search matches", "Aus Suchtreffern vorschlagen", "Sugerir desde coincidencias", "Suggérer depuis la recherche")
row(
    "t4.move_hint",
    "Default: every file you move is placed inside “Where to move files”, plus “Subfolder under that path” if you filled it (that folder is created if needed). The CSV path at the top is only the list — not the move target. Tip: “Use selected item's folder” (next to Browse) copies the parent folder of a file you selected in the list into the move target.",
    "Standard: jede verschobene Datei landet in „Wohin verschieben“, plus „Unterordner darunter“, falls ausgefüllt (Ordner wird angelegt). Der CSV-Pfad oben ist nur die Liste — kein Ziel. Tipp: „Ordner aus markiertem Eintrag“ (neben Durchsuchen) übernimmt den Ordner der markierten Datei aus der Liste.",
    "Por defecto: cada archivo va a «Dónde mover», más «Subcarpeta» si la rellenas (se crea si hace falta). La ruta CSV arriba es solo la lista, no el destino. Consejo: «Carpeta del elemento seleccionado» (junto a Examinar) copia la carpeta superior del archivo seleccionado al destino.",
    "Par défaut : chaque fichier va dans « Où déplacer », plus « Sous-dossier » si renseigné (créé si besoin). Le chemin CSV en haut est seulement la liste, pas la cible. Astuce : « Dossier de l’élément sélectionné » (à côté de Parcourir) met le dossier parent du fichier sélectionné dans la cible.",
)
row(
    "t4.per_source",
    "Instead: next to each file's current folder — ignores “Where to move files” above; each file goes to <its current folder>\\Subfolder\\",
    "Stattdessen: neben dem aktuellen Ordner jeder Datei — ignoriert „Wohin verschieben“; jede Datei nach <ihr Ordner>\\Unterordner\\",
    "En su lugar: junto a la carpeta actual de cada archivo — ignora «Dónde mover»; cada archivo a <su carpeta>\\Subcarpeta\\",
    "Sinon : à côté du dossier actuel de chaque fichier — ignore « Où déplacer » ; chaque fichier vers <son dossier>\\Sous-dossier\\",
)
row(
    "t4.preview_only",
    "Preview only (no moves — log what would happen)",
    "Nur Vorschau (kein Verschieben — protokolliert geplante Aktionen)",
    "Solo vista previa (sin mover — registra lo planeado)",
    "Aperçu seulement (pas de déplacement — journal des actions prévues)",
)
row(
    "t4.selected_only",
    "Use selected items only (otherwise all items that match Search)",
    "Nur ausgewählte Einträge (sonst alle Suchtreffer)",
    "Solo elementos seleccionados (si no, todos los que coinciden)",
    "Seulement les éléments sélectionnés (sinon tout ce qui correspond à Recherche)",
)
row("t4.move_disk", "Move files on disk", "Dateien auf Festplatte verschieben", "Mover archivos en disco", "Déplacer les fichiers sur disque")
row("t4.plan_empty", "Plan: —", "Plan: —", "Plan: —", "Plan : —")
row(
    "t4.preview_section_title",
    "Move preview (first matching items — click to show or hide)",
    "Verschiebe-Vorschau (erste Treffer — zum Ein-/Ausblenden klicken)",
    "Vista previa de movimiento (primeras coincidencias — clic para mostrar/ocultar)",
    "Aperçu du déplacement (premières correspondances — clic pour afficher/masquer)",
)
row("t4.refresh_preview", "Refresh preview", "Vorschau aktualisieren", "Actualizar vista previa", "Actualiser l’aperçu")

# Tab 5 — schema-based file names (resolution via ffprobe); long intro lives in docs/tab5_explanation.md
row(
    "t5.title_max",
    "Title max (characters; 0 = full length).",
    "Titel max. (Zeichen; 0 = volle Länge).",
    "Título máx. (caracteres; 0 = longitud completa).",
    "Titre max. (caractères ; 0 = longueur entière).",
)
row(
    "t5.preserve_tags_on_shorten",
    "Protect tags",
    "Tags schonen",
    "Proteger etiquetas",
    "Protéger les tags",
)
row(
    "t5.preserve_tags_hint",
    "**`Title max.`** is applied first when a name is shortened.\n\n**Protect tags** only applies with **Full schema name:** it keeps the `[…]` blocks at the **end** of the name (including tags that were already there).\n\nWith **Add tags** or **Replace other tags**, only the **front title** is shortened — the tag block at the end is not cut off.",
    "**`Titel max.`** gilt zuerst, wenn ein Name gekürzt wird.\n\n**Tags schonen** wirkt nur bei **Voller Schema-Name:** Die `[…]` am **Ende** bleiben (auch schon vorhandene Tags).\n\nBei **Tags anhängen** und **Andere Tags ersetzen** wird nur der **vordere Titel** gekürzt — die Tags am Ende bleiben unangetastet.",
    "**`Título máx.`** se aplica primero al acortar.\n\n**Proteger etiquetas** solo con **nombre completo del esquema:** conserva los `[…]` del **final** (incluidas etiquetas que ya hubiera).\n\nCon **Añadir etiquetas** o **Reemplazar otras**, solo se acorta el **título delantero**; el bloque final de etiquetas no se corta.",
    "**`Titre max.`** s’applique en premier lors du raccourcissement.\n\n**Protéger les tags** uniquement avec **nom complet (schéma) :** conserve les `[…]` en **fin** de nom (y compris les tags déjà présents).\n\nAvec **Ajouter des tags** ou **Remplacer les autres**, seul le **titre de tête** est raccourci — le bloc de tags en fin n’est pas tronqué.",
)
row(
    "t5.from_csv_label",
    "Year, resolution, rating (CSV / ffprobe / file)",
    "Jahr, Auflösung, Bewertung (CSV / ffprobe / Datei)",
    "Año, resolución, valoración (CSV / ffprobe / archivo)",
    "Année, résolution, note (CSV / ffprobe / fichier)",
)
row(
    "t5.append_tags_only",
    "Add tags",
    "Tags dranhängen",
    "Añadir etiquetas",
    "Ajouter des tags",
)
row(
    "t5.append_tags_hint_short",
    "On: Only checked tag slots below are appended (unchecked = nothing added). Off: Checked slots are built into the full schema name and replace old […] tags.",
    "An: Nur angehakte Tag-Slots unten werden angehängt (ohne Haken = kein Anhängen). Aus: Angehakte Slots gehen in den vollen Schema-Namen und ersetzen alte […]-Tags.",
    "Activado: solo las ranuras marcadas se añaden (sin marcar = no se añade nada). Desactivado: las marcadas entran en el nombre completo y sustituyen […] antiguos.",
    "Activé : seuls les emplacements cochés s’ajoutent (décoché = rien n’est ajouté). Désactivé : les cases cochées entrent dans le nom complet et remplacent les anciens […].",
)
row(
    "t5.name_mode.full_schema",
    "Full schema name",
    "Voller Schema-Name",
    "Nombre completo del esquema",
    "Nom complet (schéma)",
)
row(
    "t5.name_mode.tags_append",
    "Add tags",
    "Tags anhängen",
    "Añadir etiquetas",
    "Ajouter des tags",
)
row(
    "t5.name_mode.tags_replace_except_auto",
    "Replace other tags (keep year / res / rating)",
    "Andere Tags ersetzen (Jahr / Auflösung / Bewertung behalten)",
    "Reemplazar otras etiquetas (conservar año / res / valoración)",
    "Remplacer les autres tags (garder année / rés. / note)",
)
row(
    "t5.name_mode_hint",
    "**Full schema name**\nRebuilds the whole file name from your choices.\n\n**Add tags**\nKeeps every existing `[…]` block. Appends only the checked tag slots. Year, resolution, and rating: checkbox on adds them, off removes them when the rules allow.\n\n**Replace other tags**\nRemoves custom `[…]` blocks. Keeps resolution text (for example `1080p`) and star ratings `[1]`–`[5]`. Rebuilds checked slots. Year, resolution, and rating are only added when still missing — nothing already in the name is overwritten.",
    "**Voller Schema-Name**\nBaut den ganzen Dateinamen neu.\n\n**Tags anhängen**\nAlle `[…]` bleiben. Nur angehakte Slots werden angehängt. Jahr, Auflösung, Bewertung: Haken an legt sie an, Haken aus entfernt sie (wenn möglich).\n\n**Andere Tags ersetzen**\nEigene `[…]` werden entfernt; Auflösung (z. B. `1080p`) und Sterne `[1]`–`[5]` bleiben. Slots werden neu gesetzt. Jahr, Auflösung, Bewertung: nur nachtragen, wenn sie im Namen noch fehlen — nichts wird überschrieben.",
    "**Nombre completo del esquema**\nRehace todo el nombre del archivo.\n\n**Añadir etiquetas**\nConserva todos los `[…]`. Añade solo las ranuras marcadas. Año, resolución y valoración: marcado las añade; sin marcar, intenta quitarlas si aplica.\n\n**Reemplazar otras**\nQuita `[…]` personalizados; conserva resolución (p. ej. `1080p`) y notas `[1]`–`[5]`. Vuelve a crear las ranuras. Año/res/valoración solo si faltan en el nombre — no sustituye lo que ya hay.",
    "**Nom complet (schéma)**\nReconstruit tout le nom du fichier.\n\n**Ajouter des tags**\nConserve tous les `[…]`. N’ajoute que les emplacements cochés. Année, résolution, note : la case cochée ajoute, décochée retire quand c’est possible.\n\n**Remplacer les autres**\nSupprime les `[…]` personnalisés ; garde la résolution (ex. `1080p`) et les notes `[1]`–`[5]`. Recrée les emplacements. Année/rés/note seulement si absent du nom — rien n’est écrasé.",
)
row(
    "t5.help.window_title",
    "Schema rename — help",
    "Schema-Umbenennen — Hilfe",
    "Renombre por esquema — ayuda",
    "Renommage (schéma) — aide",
)
row(
    "t5.help.intro",
    "The table shows each row’s path, current file name, and proposed name. Below you pick how names are built or adjusted. The sections in this window explain each option in more detail.",
    "Die Tabelle zeigt Pfad, aktuellen Dateinamen und den Vorschlagsnamen. Darunter stellst du ein, wie Namen gebaut oder angepasst werden. Die Abschnitte hier erklären die Optionen ausführlicher.",
    "La tabla muestra ruta, nombre actual y propuesta. Abajo eliges cómo se construyen los nombres; estas secciones lo detallan.",
    "Le tableau montre chemin, nom actuel et proposition. En dessous vous choisissez la construction du nom ; ces sections détaillent chaque option.",
)
row("t5.help.heading_modes", "Naming modes", "Namens-Modi", "Modos de nombre", "Modes de nommage")
row(
    "t5.help.heading_protect",
    "Protect tags (full schema)",
    "Tags schonen (volles Schema)",
    "Proteger etiquetas (esquema completo)",
    "Protéger les tags (schéma complet)",
)
row("t5.help.heading_tags", "Tag slots (1–5)", "Tag-Slots (1–5)", "Ranuras de etiquetas (1–5)", "Emplacements de tags (1–5)")
row(
    "t5.help.heading_metadata",
    "Year, resolution, rating & ffprobe",
    "Jahr, Auflösung, Bewertung & ffprobe",
    "Año, resolución, valoración y ffprobe",
    "Année, résolution, note et ffprobe",
)
row(
    "t5.help.body_metadata",
    "The three checkboxes add or remove year (from the CSV or the file’s date where available), resolution (from video dimensions after you run ffprobe), and rating (from the CSV). When a box is off, matching tokens are removed from the name when the logic allows.\n\nResolution text uses common height labels such as 1080p; if the height does not match a standard step, width×height is used instead.",
    "Die drei Checkboxen steuern Jahr (CSV oder Datum der Datei, wo das OS es hergibt), Auflösung (aus den Abmessungen nach ffprobe) und Bewertung (CSV). Ist eine Option aus, werden passende Teile im Namen entfernt, wenn die Regeln das zulassen.\n\nAuflösung: übliche Stufen wie 1080p; passt die Höhe in keine Stufe, wird Breite×Höhe verwendet.",
    "Las tres casillas añaden o quitan año (CSV o fecha del archivo), resolución (tras ffprobe) y valoración (CSV). Desmarcar intenta quitar esos trozos del nombre cuando corresponde.\n\nResolución: etiquetas por altura (p. ej. 1080p); si no encaja, ancho×alto.",
    "Les trois cases ajoutent ou retirent l’année (CSV ou date du fichier), la résolution (après ffprobe) et la note (CSV). Décochée, la valeur correspondante est retirée du nom quand c’est possible.\n\nRésolution : libellés par hauteur (ex. 1080p) ; sinon largeur×hauteur.",
)
row(
    "t5.include_year",
    "Year (YYYY) from CSV or file (creation if available)",
    "Jahr (JJJJ) aus CSV oder Datei (Erstellung wo verfügbar)",
    "Año (AAAA) desde CSV o archivo (creación si existe)",
    "Année (AAAA) depuis CSV ou fichier (création si dispo)",
)
row("t5.include_resolution", "Resolution (ffprobe)", "Auflösung (ffprobe)", "Resolución (ffprobe)", "Résolution (ffprobe)")
row("t5.include_rating", "Rating from CSV", "Bewertung aus CSV", "Valoración desde CSV", "Note depuis CSV")
row("t5.resolution_mode", "Resolution label", "Auflösungs-Anzeige", "Etiqueta de resolución", "Libellé résolution")
row("t5.res_heightp", "Height tier (e.g. 1080p)", "Höhenstufe (z. B. 1080p)", "Por altura (p. ej. 1080p)", "Par hauteur (ex. 1080p)")
row("t5.res_wxh", "Width × height", "Breite × Höhe", "Ancho × alto", "Largeur × hauteur")
row(
    "t5.ffprobe_resolution_hint",
    "Resolution tag: common height labels (e.g. 1080p); for uncommon heights, width×height is used.",
    "Auflösung: übliche Stufen wie 1080p; passt die Höhe in keine Stufe, wird Breite×Höhe verwendet.",
    "Resolución: etiquetas por altura habituales (p. ej. 1080p); si la altura no encaja, se usa ancho×alto.",
    "Résolution : libellés par hauteur courants (ex. 1080p) ; sinon largeur×hauteur.",
)
row(
    "t5.tag_slot_ph",
    "Tag {n} — word if checked",
    "Tag {n} — Wort wenn aktiv",
    "Etiqueta {n} — texto si marcado",
    "Étiquette {n} — mot si coché",
)
row(
    "t5.tag_structure_hint",
    "Optional layout idea — e.g. slot 1=[Cat], 2=[Yard], 3=[Morning]; slots 4–5 for extras (Dog, notes, …). Only checked slots appear; order in the file name is slot 1→5, then resolution and rating.",
    "Optional: klare Struktur — z. B. Slot 1=[Katze], 2=[Garten], 3=[Morgen]; Slot 4–5 für Extras (Hund, Notiz …). Nur angehakte Slots; Reihenfolge im Namen: Slot 1→5, danach Auflösung und Bewertung.",
    "Idea opcional: ranura 1=[Gato], 2=[Jardín], 3=[Mañana]; 4–5 extras (perro, notas …). Solo ranuras marcadas; en el nombre: 1→5, luego resolución y valoración.",
    "Option : structure claire — ex. emplacement 1=[Chat], 2=[Jardin], 3=[Matin] ; 4–5 en plus (chien, notes …). Seules les cases cochées ; ordre dans le nom : 1→5, puis résolution et note.",
)
row("t5.col.scene_id", "Scene ID", "Szenen-ID", "ID de escena", "ID scène")
row("t5.col.scene_date", "Date (CSV)", "Datum (CSV)", "Fecha (CSV)", "Date (CSV)")
row("t5.col.scene_tags", "Stash tags", "Stash-Tags", "Etiquetas Stash", "Tags Stash")
row("t5.col.scene_markers", "Markers", "Marker", "Marcadores", "Marqueurs")
row("t5.col.proposed", "Proposed name", "Vorschlagsname", "Nombre propuesto", "Nom proposé")
row("t5.refresh_probe", "ffprobe start", "ffprobe start", "ffprobe start", "ffprobe start")
row(
    "t5.fill_new_leaf",
    "Fill new file names",
    "Neue Dateinamen füllen",
    "Rellenar nombres nuevos",
    "Remplir les nouveaux noms",
)
row(
    "t5.selected_only",
    "Selected items only — Fill and Rename apply to the highlighted items",
    "Nur ausgewählte Einträge — Füllen und Umbenennen nur für die markierten Einträge",
    "Solo elementos seleccionados — rellenar y renombrar solo los resaltados",
    "Uniquement les éléments sélectionnés — remplir et renommer pour les éléments surlignés",
)
row(
    "t5.selection_hint",
    "Selection: Ctrl or Shift+click, or click and drag across items (same on Tab 3 & 4).",
    "Auswahl: Strg- oder Umschalt+Klick, oder mit gedrückter Maustaste über Einträge ziehen (ebenso Tab 3 & 4).",
    "Selección: Ctrl o Mayús+clic, o arrastrar sobre elementos (igual en pestañas 3 y 4).",
    "Sélection : Ctrl ou Maj+clic, ou glisser sur les éléments (idem onglets 3 et 4).",
)
row("t5.preset_label", "Preset", "Voreinstellung", "Preajuste", "Préréglage")
row("t5.preset_none", "—", "—", "—", "—")
row("t5.preset_name_ph", "new preset name", "Name für Voreinstellung", "nombre del preajuste", "nom du préréglage")
row("t5.preset_save", "Save preset", "Voreinstellung speichern", "Guardar preajuste", "Enregistrer préréglage")
row("t5.preset_delete", "Delete preset", "Voreinstellung löschen", "Borrar preajuste", "Supprimer préréglage")

# Tab 6 — sync file names from a reference tree (size + extension; renames on target only)
row("t6.heading", "Name sync (reference → local)", "Namensabgleich (Referenz → lokal)", "Sincronizar nombres (referencia → local)", "Sync noms (référence → local)")
row(
    "t6.intro",
    "Match files by exact byte size and extension (optionally plus SHA-256 of the first 1 MiB). When exactly one source file and one target file share the same key, the target file is renamed in place to the source file’s name (same subfolder on the target). Nothing is copied, moved, or deleted. Optional: leave target files unchanged when their name already ends with Tab-5-style trailing “ [tag]” groups (schema tags). Turn off “Preview only” to apply renames.",
    "Abgleich über exakte Dateigröße und Endung (optional plus SHA-256 der ersten 1 MiB). Gibt es genau eine Quell- und eine Zieldatei mit demselben Schlüssel, wird die Zieldatei vor Ort nach dem Namen der Quelldatei umbenannt (gleicher Unterordner auf dem Ziel). Es wird nichts kopiert, verschoben oder gelöscht. Optional: Zieldateien mit Tab-5-typischen angehängten „ [Tag]“-Gruppen nicht umbenennen. „Nur Vorschau“ deaktivieren, um umzubenennen.",
    "Empareja por tamaño exacto en bytes y extensión (opcionalmente más SHA-256 del primer 1 MiB). Si hay exactamente un origen y un destino con la misma clave, el destino se renombra in situ al nombre del origen (misma subcarpeta). No se copia, mueve ni borra nada. Opcional: no renombrar destinos cuyo nombre ya termina en grupos “ [etiqueta]” al estilo de la pestaña 5. Desactiva “Solo vista previa” para aplicar.",
    "Correspondance par taille exacte (octets) et extension (optionnellement + SHA-256 du premier 1 Mio). S’il y a exactement une source et une cible avec la même clé, la cible est renommée sur place comme la source (même sous-dossier). Aucune copie, déplacement ou suppression. Option : ne pas renommer les cibles dont le nom se termine déjà par des groupes « [balise] » comme à l’onglet 5. Désactivez « Aperçu seulement » pour appliquer.",
)
row(
    "t6.source_dir",
    "Source folder (renamed reference, e.g. backup drive)",
    "Quellordner (Referenz mit neuen Namen, z. B. Backup)",
    "Carpeta origen (referencia ya renombrada, p. ej. copia de seguridad)",
    "Dossier source (référence déjà renommée, ex. sauvegarde)",
)
row(
    "t6.target_dir",
    "Target folder (old names; files here are renamed only)",
    "Zielordner (alte Namen; hier wird nur umbenannt)",
    "Carpeta destino (nombres antiguos; solo se renombra aquí)",
    "Dossier cible (anciens noms ; renommage sur place seulement)",
)
row(
    "t6.partial_hash",
    "Include SHA-256 of first 1 MiB in match key (safer if many same-size files)",
    "SHA-256 der ersten 1 MiB im Schlüssel (sicherer bei vielen gleich großen Dateien)",
    "Incluir SHA-256 del primer 1 MiB en la clave (más seguro con muchos archivos del mismo tamaño)",
    "Inclure le SHA-256 du premier 1 Mio dans la clé (plus sûr si beaucoup de fichiers identiques)",
)
row(
    "t6.keep_bracket_tags",
    "Do not rename targets that already end with Tab-5-style “ [tag]” suffixes",
    "Ziele mit Tab-5-„ [Tag]“-Suffix am Dateinamen nicht umbenennen",
    "No renombrar destinos que ya terminan en sufijos “ [etiqueta]” (estilo pestaña 5)",
    "Ne pas renommer les cibles qui se terminent déjà par des suffixes « [balise] » (onglet 5)",
)
row("t6.run", "Scan & sync names", "Scannen & Namen abgleichen", "Escanear y sincronizar nombres", "Analyser et synchroniser les noms")
row("t6.dlg_source", "Choose source folder", "Quellordner wählen", "Elegir carpeta origen", "Choisir le dossier source")
row("t6.dlg_target", "Choose target folder", "Zielordner wählen", "Elegir carpeta destino", "Choisir le dossier cible")
row(
    "log.busy_t6",
    "Tab 6: name sync already running — wait until it finishes.\n",
    "Tab 6: Namensabgleich läuft bereits — bitte warten.\n",
    "Tab 6: sincronización de nombres en curso — espere.\n",
    "Tab 6 : synchronisation des noms déjà en cours — patientez.\n",
)
row(
    "log.t6_header",
    "Tab 6 — name sync (size + extension; renames on target only)\n",
    "Tab 6 — Namensabgleich (Größe + Endung; nur Umbenennen im Ziel)\n",
    "Tab 6 — sync de nombres (tamaño + extensión; solo renombrar en destino)\n",
    "Tab 6 — sync noms (taille + extension ; renommage cible seulement)\n",
)
row(
    "log.t6_need_paths",
    "Tab 6: set both source and target folders.\n",
    "Tab 6: Quell- und Zielordner angeben.\n",
    "Tab 6: indique carpeta origen y destino.\n",
    "Tab 6 : renseignez dossier source et dossier cible.\n",
)
row(
    "log.t6_need_dirs",
    "Tab 6: source and target must be existing folders.\n",
    "Tab 6: Quelle und Ziel müssen vorhandene Ordner sein.\n",
    "Tab 6: origen y destino deben ser carpetas existentes.\n",
    "Tab 6 : la source et la cible doivent être des dossiers existants.\n",
)
row(
    "log.t6_fail",
    "Tab 6: name sync failed: {e}\n",
    "Tab 6: Namensabgleich fehlgeschlagen: {e}\n",
    "Tab 6: error en sync de nombres: {e}\n",
    "Tab 6 : échec sync noms : {e}\n",
)
row("t6.undo", "Undo last name sync", "Letzten Namensabgleich rückgängig", "Deshacer último sync de nombres", "Annuler dernier sync noms")
row(
    "log.t6_undo_header",
    "Tab 6 — undo last name-sync batch\n",
    "Tab 6 — letzten Namensabgleich rückgängig\n",
    "Tab 6 — deshacer último lote de sync de nombres\n",
    "Tab 6 — annuler le dernier lot de sync noms\n",
)
row(
    "log.t6_undo_nothing",
    "Tab 6: nothing to undo — run a real name sync (preview off) first.\n",
    "Tab 6: nichts rückgängig — zuerst echten Namensabgleich ausführen (Vorschau aus).\n",
    "Tab 6: nada que deshacer — ejecute antes un sync real (sin vista previa).\n",
    "Tab 6 : rien à annuler — lancez d’abord un sync réel (sans aperçu).\n",
)
row(
    "log.t6_undo_done",
    "Tab 6 undo: reverted {n} path(s) on disk.\n",
    "Tab 6 Rückgängig: {n} Pfad/Pfade auf der Festplatte zurückgesetzt.\n",
    "Tab 6 deshacer: {n} ruta(s) revertida(s) en el disco.\n",
    "Tab 6 annulation : {n} chemin(s) restauré(s) sur le disque.\n",
)
row(
    "log.t6_undo_done_preview",
    "Tab 6 undo preview: {n} step(s) logged (disk unchanged — turn off preview and click Undo again to apply).\n",
    "Tab 6 Rückgängig-Vorschau: {n} Schritt(e) im Log (Festplatte unverändert — Vorschau aus, erneut klicken).\n",
    "Tab 6 vista previa deshacer: {n} paso(s) (disco sin cambios — desactive vista previa y repita).\n",
    "Tab 6 aperçu annulation : {n} étape(s) (disque inchangé — désactivez l’aperçu puis réessayez).\n",
)
row(
    "log.t6_undo_more",
    "{m} more Tab 6 name-sync batch(es) can still be undone (Tab 6 button).\n",
    "Noch {m} Namensabgleich-Stapel rückgängig machbar (Button in Tab 6).\n",
    "Aún se puede deshacer {m} lote(s) de sync en tab 6.\n",
    "Encore {m} lot(s) de sync (onglet 6) annulable(s).\n",
)
row(
    "t6.dup_title",
    "Duplicate / ambiguous matches (last run)",
    "Duplikate / mehrdeutige Treffer (letzter Lauf)",
    "Duplicados / coincidencias ambiguas (última ejecución)",
    "Doublons / correspondances ambiguës (dernier lancement)",
)
row(
    "t6.dup_hint",
    "Rows with the same «Group» number are one collision cluster (same match fingerprint, not necessarily the same filename). «Match» shows size, extension, and optional hash prefix. «Path» is the full path on disk. «Which folder» = source tree vs target tree (the two paths at the top of Tab 6). Right-click: Explorer, Stash (Tab 1 URL + API), delete.",
    "Gleiche «Gruppe» = eine Kollision (gleiches Abgleich-Merkmal, Dateiname kann trotzdem anders sein). «Merkmal» = Größe, Endung, ggf. Hash-Anfang. «Pfad» = voller Dateipfad. «Welcher Ordner» = Quell- vs. Zielbaum (die beiden Ordner oben). Rechtsklick: Explorer, Stash, Löschen.",
    "Mismo «Grupo» = mismo choque (huella de coincidencia; el nombre puede diferir). «Coincidencia» = tamaño, extensión, hash opcional. «Ruta» completa. Clic derecho: Explorador, Stash, borrar.",
    "Même « Groupe » = même collision (empreinte ; les noms peuvent différer). «Critère » = taille, extension, hash optionnel. Chemin complet. Clic droit : Explorateur, Stash, supprimer.",
)
row(
    "t6.dup_path_explain",
    "Tip: the list is sorted by group so related rows sit together. Same «Group» + same «Match» = same internal key the sync uses (bytes + extension [+ partial hash]).",
    "Tipp: sortiert nach Gruppe — zusammengehörige Zeilen stehen direkt untereinander. Gleiche «Gruppe» + gleiches «Merkmal» = derselbe interne Schlüssel (Bytes + Endung [+ Hash]).",
    "Consejo: ordenado por grupo; misma «Coincidencia» = misma clave interna.",
    "Astuce : tri par groupe ; même « Critère » = même clé interne.",
)
row("t6.dup_col.group", "Group", "Gruppe", "Grupo", "Groupe")
row(
    "t6.dup_col.match",
    "Match fingerprint",
    "Abgleich-Merkmal",
    "Huella de coincidencia",
    "Critère de paire",
)
row("t6.dup_col.side", "Which folder", "Welcher Ordner", "Carpeta", "Dossier")
row("t6.dup_col.reason", "Reason", "Grund", "Motivo", "Motif")
row(
    "t6.side_source",
    "Source folder (above)",
    "Quellordner (oben)",
    "Carpeta origen (arriba)",
    "Dossier source (haut)",
)
row(
    "t6.side_target",
    "Target folder (above)",
    "Zielordner (oben)",
    "Carpeta destino (arriba)",
    "Dossier cible (haut)",
)
row(
    "t6.dup_reason.group",
    "Same size + ext. (and hash if enabled) as other file(s)",
    "Gleiche Größe + Endung (ggf. Hash) wie andere Datei(en)",
    "Mismo tamaño + ext. (y hash si aplica) que otro(s)",
    "Même taille + ext. (et hash si activé) qu’un autre",
)
row(
    "t6.dup_reason.multi_source",
    "Several source files match this target key",
    "Mehrere Quelldateien passen zu diesem Ziel-Schlüssel",
    "Varios archivos origen coinciden con esta clave",
    "Plusieurs sources correspondent à cette clé cible",
)
row(
    "t6.ctx_delete_file",
    "Delete file from disk…",
    "Datei von der Festplatte löschen…",
    "Borrar archivo del disco…",
    "Supprimer le fichier du disque…",
)
row(
    "t6.delete_confirm_title",
    "Delete file(s)?",
    "Datei(en) löschen?",
    "¿Borrar archivo(s)?",
    "Supprimer le(s) fichier(s) ?",
)
row(
    "t6.delete_confirm_body",
    "Permanently delete {n} selected file(s) from disk? This cannot be undone (except from the recycle bin if the OS keeps one).",
    "{n} ausgewählte Datei(en) dauerhaft von der Festplatte löschen? Nur rückgängig falls der Papierkorb greift.",
    "¿Borrar permanentemente {n} archivo(s)? Solo recuperable si la papelera del SO aplica.",
    "Supprimer définitivement {n} fichier(s) ? Récupération possible seulement via la corbeille.",
)
row(
    "t6.delete_confirm_body_preview",
    "Preview only is on: show which of the {n} selected file(s) would be deleted — nothing will be removed from disk yet. Continue?",
    "«Nur Vorschau» ist an: Es wird nur simuliert, welche der {n} Datei(en) gelöscht würden — noch nichts von der Festplatte. Fortfahren?",
    "«Solo vista previa» activada: solo se mostrará qué {n} archivo(s) se borrarían; no se toca el disco. ¿Continuar?",
    "«Aperçu seulement» est activé : affichage des {n} fichier(s) qui seraient supprimés — rien n’est encore effacé sur le disque. Continuer ?",
)
row(
    "log.t6_dup_deleted",
    "Tab 6: deleted {n} file(s) from disk.\n",
    "Tab 6: {n} Datei(en) von der Festplatte gelöscht.\n",
    "Tab 6: {n} archivo(s) borrado(s) del disco.\n",
    "Tab 6 : {n} fichier(s) supprimé(s) du disque.\n",
)
row(
    "log.t6_dup_delete_preview",
    "Tab 6 [preview only]: no files deleted — {n} path(s) would be removed if preview is turned off.\n",
    "Tab 6 [Nur Vorschau]: nichts gelöscht — {n} Pfad/Pfade würden ohne Vorschau entfernt.\n",
    "Tab 6 [solo vista previa]: nada borrado — {n} ruta(s) se borrarían sin la vista previa.\n",
    "Tab 6 [aperçu seulement] : rien supprimé — {n} chemin(s) le seraient sans l’aperçu.\n",
)
row(
    "log.t6_dup_delete_preview_line",
    "Tab 6 [preview] would delete: {path}\n",
    "Tab 6 [Vorschau] würde löschen: {path}\n",
    "Tab 6 [vista previa] borraría: {path}\n",
    "Tab 6 [aperçu] supprimerait : {path}\n",
)
row(
    "log.t6_dup_delete_fail",
    "Tab 6: could not delete {path}: {e}\n",
    "Tab 6: Löschen fehlgeschlagen {path}: {e}\n",
    "Tab 6: no se pudo borrar {path}: {e}\n",
    "Tab 6 : suppression impossible {path} : {e}\n",
)
row(
    "log.t6_dup_delete_all_mirror",
    "Tab 6: nothing deleted — all {n} selected path(s) belong to mirrored source/target pairs (same relative path under both roots).\n",
    "Tab 6: nichts gelöscht — alle {n} markierten Pfade sind gespiegelte Quell-/Ziel-Paare (gleicher relativer Pfad unter beiden Wurzeln).\n",
    "Tab 6: nada borrado: las {n} ruta(s) son pares espejo origen/destino (misma ruta relativa).\n",
    "Tab 6 : rien supprimé — les {n} chemin(s) font partie de paires miroir source/cible (même chemin relatif).\n",
)
row(
    "log.t6_dup_delete_skipped_mirror",
    "Tab 6: {n} selected path(s) are mirrored (same relative path on source and target) and will not be deleted.\n",
    "Tab 6: {n} Pfad(e) sind gespiegelt (gleicher relativer Pfad) und werden nicht gelöscht.\n",
    "Tab 6: {n} ruta(s) espejadas; no se borrarán.\n",
    "Tab 6 : {n} chemin(s) miroir — non supprimé(s).\n",
)
row(
    "log.t6_stash_resolve_fail",
    "Tab 6: could not resolve Stash scene for this path: {err}\n",
    "Tab 6: keine Stash-Szene für diesen Pfad: {err}\n",
    "Tab 6: no se encontró escena Stash para la ruta: {err}\n",
    "Tab 6 : scène Stash introuvable pour ce chemin : {err}\n",
)
row(
    "log.t6_stash_browser_fail",
    "Tab 6: could not open browser: {e}\n",
    "Tab 6: Browser konnte nicht geöffnet werden: {e}\n",
    "Tab 6: no se pudo abrir el navegador: {e}\n",
    "Tab 6 : impossible d’ouvrir le navigateur : {e}\n",
)
row(
    "log.t6_stash_first_only",
    "Tab 6: opened Stash for the first selected path only ({n} selected).\n",
    "Tab 6: Stash nur für den ersten gewählten Pfad geöffnet ({n} markiert).\n",
    "Tab 6: Stash solo para la primera ruta seleccionada ({n}).\n",
    "Tab 6 : Stash ouvert pour le premier chemin seulement ({n} sélectionnés).\n",
)
row(
    "log.t6_dup_many_explorer",
    "Tab 6: opening Explorer for the first 8 of {n} selected paths.\n",
    "Tab 6: Explorer für die ersten 8 von {n} Pfaden.\n",
    "Tab 6: abriendo Explorador para los primeros 8 de {n}.\n",
    "Tab 6 : Explorateur pour les 8 premiers chemins sur {n}.\n",
)
row(
    "t6.dedupe_bar_hint",
    "Bulk: in each «Group», delete extra copies (destructive). Same relative path under Source and Target roots is always kept on both sides so mirrors stay aligned. If «Prefer [tag] names» is checked, files with Tab-5-style trailing bracket tags in the leaf sort before others in that group; the three radio options then break ties (and apply alone when no file in the group has tags). Then confirm.",
    "Mengenlöschung: pro «Gruppe» Überzählige löschen (irreversibel). Gleicher relativer Pfad unter Quell- und Zielordner bleibt immer auf beiden Seiten erhalten (Spiegel). Häkchen „[Tag]-Namen bevorzugen“: Dateien mit Tab-5-Suffix am Namensende stehen in der Gruppe vorne; die drei Radio-Optionen entscheiden bei Gleichstand (und allein, wenn niemand in der Gruppe Tags hat). Dann bestätigen.",
    "Por «Grupo»: borrar copias sobrantes (destructivo). La misma ruta relativa bajo origen y destino siempre se conserva en ambos lados (espejo). Si marca «Preferir nombres con [etiqueta]», los archivos con sufijos entre corchetes (estilo pestaña 5) van primero en el grupo; los tres botones de opción desempatan (y bastan si nadie tiene tags). Confirme.",
    "Par « Groupe » : supprimer les copies en trop (destructif). Le même chemin relatif sous source et cible est toujours conservé des deux côtés (miroir). Case « Préférer noms avec [balise] » : les fichiers avec suffixe crochets (onglet 5) passent avant les autres du groupe ; les trois options radio servent d’égalité (et seules si personne n’a de tags). Confirmez.",
)
row(
    "t6.dedupe_keep_alpha",
    "Keep: first path (A–Z)",
    "Behalten: alphabetisch erster Pfad",
    "Conservar: primera ruta (A-Z)",
    "Conserver : premier chemin (A-Z)",
)
row(
    "t6.dedupe_keep_source",
    "Keep: prefer source tree",
    "Behalten: bevorzugt Quellordner",
    "Conservar: preferir carpeta origen",
    "Conserver : préférer la source",
)
row(
    "t6.dedupe_keep_target",
    "Keep: prefer target tree",
    "Behalten: bevorzugt Zielordner",
    "Conservar: preferir carpeta destino",
    "Conserver : préférer la cible",
)
row(
    "t6.dedupe_tag_priority",
    "Prefer files whose name ends with Tab-5-style “ [tag]” groups (then use the option below)",
    "„[Tag]“-Namen bevorzugen (Tab 5-Suffix; Tiebreaker / ohne Tags = Option darunter)",
    "Preferir archivos con sufijos “ [etiqueta]” estilo pestaña 5 (luego la opción de abajo)",
    "Préférer les noms se terminant par des « [balise] » style onglet 5 (puis l’option ci-dessous)",
)
row(
    "t6.dedupe_button",
    "Delete extras in all groups…",
    "Überzählige in allen Gruppen löschen…",
    "Borrar extras en todos los grupos…",
    "Supprimer les extras dans tous les groupes…",
)
row(
    "t6.dedupe_confirm_title",
    "Delete duplicate files?",
    "Duplikat-Dateien löschen?",
    "¿Borrar archivos duplicados?",
    "Supprimer les fichiers en double ?",
)
row(
    "t6.dedupe_confirm_body",
    "This will permanently delete files on disk so that each of the {groups} duplicate group(s) keeps only one file ({files} delete(s) planned). Continue?",
    "Es werden dauerhaft {files} Datei(en) gelöscht, sodass von {groups} Gruppe(n) jeweils nur eine Datei übrig bleibt. Fortfahren?",
    "Se borrarán {files} archivo(s) para dejar un archivo por grupo ({groups} grupo(s)). ¿Continuar?",
    "Suppression définitive de {files} fichier(s) pour ne garder qu’un fichier par groupe ({groups}). Continuer ?",
)
row(
    "t6.dedupe_confirm_body_preview",
    "Preview only is on: list which of the {files} file(s) would be deleted across {groups} group(s) — nothing removed from disk yet. Continue?",
    "«Nur Vorschau» ist an: Auflistung der {files} Datei(en) in {groups} Gruppe(n), die ohne Vorschau gelöscht würden — Festplatte unverändert. Fortfahren?",
    "«Solo vista previa»: se listarían los {files} archivo(s) en {groups} grupo(s); no se borra nada aún. ¿Continuar?",
    "«Aperçu seulement» : liste des {files} fichier(s) sur {groups} groupe(s) qui seraient supprimés — disque intact pour l’instant. Continuer ?",
)
row(
    "log.t6_dedupe_empty",
    "Tab 6: duplicate list is empty — run scan & sync first.\n",
    "Tab 6: Duplikatliste leer — zuerst Scannen & Abgleich ausführen.\n",
    "Tab 6: lista de duplicados vacía — ejecute primero el análisis.\n",
    "Tab 6 : liste des doublons vide — lancez d’abord l’analyse.\n",
)
row(
    "log.t6_dedupe_nothing",
    "Tab 6: nothing to bulk-delete (no extras, or only mirrored source/target pairs remain).\n",
    "Tab 6: nichts zu löschen (keine Überzähligen, oder nur gespiegelte Quell-/Ziel-Paare).\n",
    "Tab 6: nada que borrar en bloque (sin extras, o solo pares espejados origen/destino).\n",
    "Tab 6 : rien à supprimer en masse (pas d’extras, ou seulement des paires miroir source/cible).\n",
)
row(
    "log.t6_dedupe_need_roots",
    "Tab 6 bulk dedupe: set both source and target folders (existing paths) so mirrored relative paths can be detected.\n",
    "Tab 6 Mengenlöschung: Quell- und Zielordner müssen gesetzt und vorhanden sein, damit gespiegelte Pfade erkannt werden.\n",
    "Tab 6: indique carpetas origen y destino existentes para detectar rutas espejo.\n",
    "Tab 6 : définissez dossiers source et cible existants pour détecter les chemins miroir.\n",
)
row(
    "log.t6_dedupe_done",
    "Tab 6 bulk dedupe: deleted {deleted} of {planned} planned file(s) from disk.\n",
    "Tab 6 Mengenlöschung: {deleted} von {planned} geplanten Datei(en) gelöscht.\n",
    "Tab 6: borrados {deleted} de {planned} archivos previstos.\n",
    "Tab 6 : {deleted} / {planned} fichiers supprimés.\n",
)
row(
    "log.t6_dedupe_preview",
    "Tab 6 [preview only]: bulk dedupe — no files deleted; {planned} path(s) would be removed if preview is turned off.\n",
    "Tab 6 [Nur Vorschau]: Mengenlöschung — nichts gelöscht; {planned} Pfad/Pfade würden ohne Vorschau entfernt.\n",
    "Tab 6 [solo vista previa]: nada borrado en bloque; {planned} ruta(s) sin vista previa.\n",
    "Tab 6 [aperçu seulement] : rien supprimé en masse ; {planned} chemin(s) sans aperçu.\n",
)
row(
    "log.t6_dedupe_preview_line",
    "Tab 6 [preview] would delete: {path}\n",
    "Tab 6 [Vorschau] würde löschen: {path}\n",
    "Tab 6 [vista previa] borraría: {path}\n",
    "Tab 6 [aperçu] supprimerait : {path}\n",
)

# Tab 7 — file sync: incremental update or full mirror
row("t7.heading", "File sync (update or mirror)", "Datei-Sync (Aktualisieren oder Spiegeln)", "Sincronizar archivos (actualizar o espejo)", "Sync fichiers (mise à jour ou miroir)")
row(
    "t7.intro",
    "Choose a mode, then run with or without preview. Update (incremental): copy missing files into the same relative paths under the target, and refresh files whose size or modification time differs from the source — nothing is deleted on the target. Mirror (exact clone): the target’s file tree is made to match the source — extra files under the target are removed, missing files are copied, and differing files are replaced. If a mirrored path cannot be used, new files may land in the target root with a disambiguated name. Source and target folders must not overlap.",
    "Modus wählen, dann mit oder ohne Vorschau ausführen. Aktualisieren (inkrementell): fehlende Dateien unter dem gleichen relativen Pfad im Ziel anlegen; bei abweichender Größe oder Änderungszeit die Zieldatei von der Quelle überschreiben — im Ziel wird nichts gelöscht. Spiegeln (exakter Klon): der Zielbaum entspricht der Quelle — zusätzliche Dateien im Ziel werden entfernt, fehlende kopiert, abweichende ersetzt. Spiegelpfad unmöglich → neue Dateien ggf. im Zielroot mit eindeutigem Namen. Quell- und Zielordner dürfen sich nicht überlappen.",
    "Elija modo y ejecute con o sin vista previa. Actualizar (incremental): copia rutas faltantes y sobrescribe si tamaño o fecha difieren — no borra en destino. Espejo (clon exacto): el destino queda igual que el origen — borra sobrantes en destino, copia faltantes y reemplaza distintos. Si falla la ruta espejo, nuevos archivos pueden ir a la raíz con nombre único. Origen y destino no deben solaparse.",
    "Choisissez un mode, puis exécutez avec ou sans aperçu. Mise à jour (incrémentielle) : copie les chemins manquants et remplace si taille ou date diffère — aucune suppression côté cible. Miroir (clone exact) : la cible reproduit la source — supprime les fichiers en trop sous la cible, copie les manquants, remplace les différents. Chemin miroir impossible → nouveaux fichiers éventuellement à la racine avec nom unique. Source et cible ne doivent pas se chevaucher.",
)
row("t7.mode_label", "Mode", "Modus", "Modo", "Mode")
row(
    "t7.mode.update",
    "Update (incremental — add & refresh, no deletes)",
    "Aktualisieren (inkrementell — ergänzen & aktualisieren, kein Löschen)",
    "Actualizar (incremental — añadir y refrescar, sin borrar)",
    "Mise à jour (incrémentielle — ajouter / rafraîchir, sans suppression)",
)
row(
    "t7.mode.mirror",
    "Mirror (exact clone — match source, delete extras on target)",
    "Spiegeln (exakter Klon — wie Quelle, Überzähliges im Ziel löschen)",
    "Espejo (clon exacto — igual que origen, borrar extras en destino)",
    "Miroir (clone exact — comme la source, supprime l’excédent sur la cible)",
)
row(
    "t7.mode_hint",
    "For files that already exist on both sides, refresh compares size and last-modified time only (not a full byte-by-byte compare).",
    "„Aktualisieren“ und „Spiegeln“ vergleichen bei vorhandenen Dateien nur Größe und Änderungszeit (kein Byte-für-Byte-Vergleich).",
    "Para archivos ya presentes, «Actualizar» y «Espejo» solo comparan tamaño y fecha de modificación (no todo el contenido).",
    "Pour les fichiers déjà présents, « Mise à jour » et « Miroir » comparent taille et date de modification seulement (pas octet à octet).",
)
row(
    "t7.source_dir",
    "Source folder (copy from)",
    "Quellordner (von hier kopieren)",
    "Carpeta origen (copiar desde)",
    "Dossier source (copier depuis)",
)
row(
    "t7.target_dir",
    "Target folder (copy into)",
    "Zielordner (hierhin kopieren)",
    "Carpeta destino (copiar aquí)",
    "Dossier cible (copier ici)",
)
row("t7.run", "Scan & apply", "Scannen & Anwenden", "Escanear y aplicar", "Analyser et appliquer")
row("t7.dlg_source", "Choose source folder", "Quellordner wählen", "Elegir carpeta origen", "Choisir le dossier source")
row("t7.dlg_target", "Choose target folder", "Zielordner wählen", "Elegir carpeta destino", "Choisir le dossier cible")
row("t7.undo", "Undo last copy batch", "Letzte Kopie rückgängig", "Deshacer último lote de copias", "Annuler dernier lot de copies")
row(
    "t7.undo_hint",
    "Undo only removes files that this tool created in the last non-preview run; it does not restore mirror deletes or reverse overwrites.",
    "Rückgängig löscht nur Dateien, die dieses Tool im letzten Lauf ohne Vorschau neu angelegt hat — keine Wiederherstellung nach Spiegel-Löschungen oder Überschreibungen.",
    "Deshacer solo quita archivos nuevos creados por la herramienta en el último pase real; no restaura borrados del espejo ni sobrescrituras.",
    "Annuler supprime seulement les fichiers que l’outil a créés au dernier passage réel ; pas de restauration après suppressions miroir ni après écrasements.",
)
row(
    "t7.tree_title",
    "Planned / last run (all operations)",
    "Geplant / letzter Lauf (alle Schritte)",
    "Planificado / última ejecución (todas las operaciones)",
    "Prévu / dernier passage (toutes les opérations)",
)
row(
    "t7.tree_hint",
    "After «Scan & apply» (with or without preview), this list shows what would happen or what happened: source path, destination path, and status. Undo (toolbar) only applies to newly created files from the last real run — not to rows you remove here.",
    "Nach «Scannen & Anwenden» (mit oder ohne Vorschau): Quelle, Ziel, Status. Die Toolbar «Rückgängig» gilt nur für neu angelegte Dateien des letzten echten Laufs — nicht für Zeilen, die Sie hier aus der Liste entfernen.",
    "Tras «Escanear y aplicar» (con o sin vista previa): origen, destino, estado. El botón Deshacer solo afecta a archivos nuevos del último pase real.",
    "Après «Analyser et appliquer» (avec ou sans aperçu) : source, destination, statut. Le bouton Annuler du bas ne concerne que les fichiers créés au dernier passage réel.",
)
row(
    "t7.tree_sel_hint",
    "Selection: Ctrl or Shift+click, or click-drag across rows (same as Tabs 3–5). With the mouse button held, drag near the top or bottom edge of the list to scroll quickly while extending the selection. Right-click: open the row’s primary path in Explorer, load source files into Tab 5 (schema rename), or delete that file from disk (the list updates).",
    "Mehrfachauswahl: Strg- oder Umschalt+Klick oder mit gedrückter Maustaste über Zeilen ziehen (wie Tab 3–5). Mit gedrückter Taste am oberen oder unteren Listenrand ziehen — schnelles Scrollen während der Markierung. Rechtsklick: Explorer für den Hauptpfad der Zeile, Quellen in Tab 5 (Schema-Umbenennung) laden, oder Datei von der Festplatte löschen (Liste wird angepasst).",
    "Selección: Ctrl o Mayús+clic, o arrastrar (igual pestañas 3–5). Con el botón pulsado, arrastre cerca del borde superior o inferior para desplazarse rápido. Clic derecho: Explorador, cargar orígenes en pestaña 5 (renombrado por esquema), o borrar archivo (se actualiza la lista).",
    "Sélection : Ctrl ou Maj+clic, ou glisser (onglets 3–5). Bouton enfoncé près du bord haut ou bas : défilement rapide. Clic droit : Explorateur, charger les sources dans l’onglet 5 (renommage schéma), ou supprimer le fichier (liste mise à jour).",
)
row(
    "t7.ctx_tab5",
    "Load source files in Tab 5 (schema)…",
    "Quellen in Tab 5 (Schema) laden…",
    "Cargar orígenes en pestaña 5 (esquema)…",
    "Charger les sources dans l’onglet 5 (schéma)…",
)
row(
    "t7.tree_delete_confirm_title",
    "Delete selected file(s)?",
    "Markierte Datei(en) löschen?",
    "¿Borrar archivos seleccionados?",
    "Supprimer les fichiers sélectionnés ?",
)
row(
    "t7.tree_delete_confirm_body",
    "Permanently delete {n} file(s) from disk (the paths tied to the selected rows)? The list below updates; this is not the Tab 7 undo stack.",
    "{n} Datei(en) dauerhaft löschen (Pfade der markierten Zeilen)? Die Liste unten wird angepasst; das ist nicht der Tab-7-Rückgängig-Stapel.",
    "¿Borrar permanentemente {n} archivo(s)? La lista se actualiza; no es el historial Deshacer del tab 7.",
    "Supprimer définitivement {n} fichier(s) ? La liste est mise à jour ; ce n’est pas la pile Annuler de l’onglet 7.",
)
row(
    "t7.tree_delete_confirm_body_preview",
    "Preview only is on: show which of the {n} file(s) would be deleted — nothing removed from disk; the list below stays unchanged. Continue?",
    "«Nur Vorschau» ist an: Es wird nur simuliert, welche der {n} Datei(en) gelöscht würden — Festplatte und Liste unverändert. Fortfahren?",
    "«Solo vista previa»: solo se muestra qué {n} archivo(s) se borrarían; disco y lista sin cambios. ¿Continuar?",
    "«Aperçu seulement» : affichage des {n} fichier(s) qui seraient supprimés — disque et liste inchangés. Continuer ?",
)
row(
    "log.t7_many_explorer",
    "Tab 7: opening Explorer for the first 8 of {n} selected paths.\n",
    "Tab 7: Explorer für die ersten 8 von {n} Pfaden.\n",
    "Tab 7: abriendo Explorador para los primeros 8 de {n}.\n",
    "Tab 7 : Explorateur pour les 8 premiers chemins sur {n}.\n",
)
row(
    "log.t7_tree_deleted",
    "Tab 7: deleted {n} file(s) from disk (list updated).\n",
    "Tab 7: {n} Datei(en) von der Festplatte gelöscht (Liste aktualisiert).\n",
    "Tab 7: {n} archivo(s) borrado(s) (lista actualizada).\n",
    "Tab 7 : {n} fichier(s) supprimé(s) (liste mise à jour).\n",
)
row(
    "log.t7_tree_delete_preview",
    "Tab 7 [preview only]: no files deleted — {n} path(s) would be removed if preview is turned off.\n",
    "Tab 7 [Nur Vorschau]: nichts gelöscht — {n} Pfad/Pfade würden ohne Vorschau entfernt.\n",
    "Tab 7 [solo vista previa]: nada borrado — {n} ruta(s) sin vista previa.\n",
    "Tab 7 [aperçu seulement] : rien supprimé — {n} chemin(s) sans aperçu.\n",
)
row(
    "log.t7_tree_delete_preview_line",
    "Tab 7 [preview] would delete: {path}\n",
    "Tab 7 [Vorschau] würde löschen: {path}\n",
    "Tab 7 [vista previa] borraría: {path}\n",
    "Tab 7 [aperçu] supprimerait : {path}\n",
)
row(
    "log.t7_tree_delete_fail",
    "Tab 7: could not delete {path}: {e}\n",
    "Tab 7: Löschen fehlgeschlagen {path}: {e}\n",
    "Tab 7: no se pudo borrar {path}: {e}\n",
    "Tab 7 : suppression impossible {path} : {e}\n",
)
row(
    "log.t7_tab5_nothing",
    "Tab 7 → Tab 5: nothing to load (pick rows with a source path that exists on disk as a regular file).\n",
    "Tab 7 → Tab 5: nichts zu laden (Zeilen mit Quellpfad wählen, der auf der Festplatte als normale Datei existiert).\n",
    "Tab 7 → pestaña 5: nada que cargar (filas con ruta de origen que exista como archivo).\n",
    "Tab 7 → onglet 5 : rien à charger (lignes avec un chemin source existant comme fichier).\n",
)
row(
    "log.t7_tab5_skipped",
    "Tab 7 → Tab 5: skipped {n} path(s) (not a regular file on disk).\n",
    "Tab 7 → Tab 5: {n} Pfad/Pfade übersprungen (keine normale Datei auf der Festplatte).\n",
    "Tab 7 → pestaña 5: omitidas {n} ruta(s) (no son archivo en disco).\n",
    "Tab 7 → onglet 5 : {n} chemin(s) ignoré(s) (pas un fichier ordinaire sur le disque).\n",
)
row(
    "log.t7_tab5_write_fail",
    "Tab 7 → Tab 5: could not write the buffer CSV: {e}\n",
    "Tab 7 → Tab 5: Puffer-CSV konnte nicht geschrieben werden: {e}\n",
    "Tab 7 → pestaña 5: no se pudo escribir el CSV temporal: {e}\n",
    "Tab 7 → onglet 5 : écriture du CSV tampon impossible : {e}\n",
)
row(
    "log.t7_tab5_loaded",
    "Tab 7 → Tab 5: loaded {n} file row(s) into Tab 5 ({path}).\n",
    "Tab 7 → Tab 5: {n} Dateizeile(n) in Tab 5 geladen ({path}).\n",
    "Tab 7 → pestaña 5: cargadas {n} fila(s) de archivo ({path}).\n",
    "Tab 7 → onglet 5 : {n} ligne(s) fichier chargée(s) ({path}).\n",
)
row("t7.col.dest", "Destination", "Ziel", "Destino", "Destination")
row("t7.col.status", "Status", "Status", "Estado", "État")
row("t7.status.dry_mirror", "Preview: mirrored path", "Vorschau: Spiegelpfad", "Vista previa: ruta espejo", "Aperçu : chemin miroir")
row("t7.status.dry_fallback", "Preview: target root (fallback)", "Vorschau: Zielroot (Ausweich)", "Vista previa: raíz destino (reserva)", "Aperçu : racine cible (repli)")
row("t7.status.copied", "Copied (mirrored path)", "Kopiert (Spiegelpfad)", "Copiado (ruta espejo)", "Copié (chemin miroir)")
row("t7.status.copied_fallback", "Copied (target root)", "Kopiert (Zielroot)", "Copiado (raíz destino)", "Copié (racine cible)")
row("t7.status.error", "Error", "Fehler", "Error", "Erreur")
row("t7.status.dry_delete", "Preview: delete on target", "Vorschau: Löschen im Ziel", "Vista previa: borrar en destino", "Aperçu : suppression cible")
row("t7.status.deleted", "Deleted on target", "Im Ziel gelöscht", "Borrado en destino", "Supprimé sur la cible")
row("t7.status.error_delete", "Delete failed", "Löschen fehlgeschlagen", "Error al borrar", "Échec suppression")
row("t7.status.dry_update", "Preview: refresh file", "Vorschau: Datei aktualisieren", "Vista previa: actualizar", "Aperçu : mise à jour fichier")
row("t7.status.copied_update", "Refreshed (overwritten)", "Aktualisiert (überschrieben)", "Actualizado (sobrescrito)", "Rafraîchi (écrasé)")
row("t7.status.error_update", "Refresh failed", "Aktualisieren fehlgeschlagen", "Error al actualizar", "Échec mise à jour")
row(
    "log.busy_t7",
    "Tab 7: file sync already running — wait until it finishes.\n",
    "Tab 7: Datei-Sync läuft bereits — bitte warten.\n",
    "Tab 7: sincronización en curso — espere.\n",
    "Tab 7 : sync fichiers déjà en cours — patientez.\n",
)
row(
    "log.t7_header",
    "Tab 7 — file sync (update or mirror)\n",
    "Tab 7 — Datei-Sync (Aktualisieren oder Spiegeln)\n",
    "Tab 7 — sync archivos (actualizar o espejo)\n",
    "Tab 7 — sync fichiers (mise à jour ou miroir)\n",
)
row(
    "log.t7_need_paths",
    "Tab 7: set both source and target folders.\n",
    "Tab 7: Quell- und Zielordner angeben.\n",
    "Tab 7: indique origen y destino.\n",
    "Tab 7 : renseignez source et cible.\n",
)
row(
    "log.t7_need_dirs",
    "Tab 7: source and target must be existing folders.\n",
    "Tab 7: Quelle und Ziel müssen vorhandene Ordner sein.\n",
    "Tab 7: origen y destino deben ser carpetas existentes.\n",
    "Tab 7 : source et cible doivent être des dossiers existants.\n",
)
row(
    "log.t7_overlap",
    "Tab 7: source and target folders must not overlap or be the same (unsafe to walk and copy).\n",
    "Tab 7: Quell- und Zielordner dürfen nicht identisch sein und nicht ineinander liegen (unsicher).\n",
    "Tab 7: origen y destino no deben solaparse ni ser iguales.\n",
    "Tab 7 : la source et la cible ne doivent pas se chevaucher ni être identiques.\n",
)
row(
    "log.t7_fail",
    "Tab 7: file sync failed: {e}\n",
    "Tab 7: Datei-Sync fehlgeschlagen: {e}\n",
    "Tab 7: error en sync: {e}\n",
    "Tab 7 : échec sync : {e}\n",
)
row(
    "log.t7_log_truncated",
    "Tab 7: only the first {shown} operations are listed in the log below ({total} total); the result table still shows all rows.\n",
    "Tab 7: im Protokoll nur die ersten {shown} von {total} Einträgen — die Ergebnistabelle zeigt alle Zeilen.\n",
    "Tab 7: solo las primeras {shown} entradas en el registro ({total} en total); la tabla muestra todas.\n",
    "Tab 7 : seules les {shown} premières lignes dans le journal ({total} au total) ; le tableau liste tout.\n",
)
row(
    "log.t7_summary",
    "Tab 7 summary — copy/new: {copied}, refresh (overwrite): {refreshed}, mirror deletes (target only): {deleted}, errors: {errors}.{suffix}\n",
    "Tab 7 summary — copy/new: {copied}, refresh (overwrite): {refreshed}, mirror deletes (target only): {deleted}, errors: {errors}.{suffix}\n",
    "Tab 7 summary — copy/new: {copied}, refresh (overwrite): {refreshed}, mirror deletes (target only): {deleted}, errors: {errors}.{suffix}\n",
    "Tab 7 summary — copy/new: {copied}, refresh (overwrite): {refreshed}, mirror deletes (target only): {deleted}, errors: {errors}.{suffix}\n",
)
row(
    "log.t7_nothing",
    "Tab 7: nothing to do — trees already match the chosen mode (no missing copies, no refreshes, no mirror deletes).\n",
    "Tab 7: nichts zu tun — für den gewählten Modus ist bereits alles abgeglichen.\n",
    "Tab 7: nada que hacer — ya coincide con el modo elegido.\n",
    "Tab 7 : rien à faire — déjà conforme au mode choisi.\n",
)
row(
    "log.t7_line_dry_mirror",
    "Tab 7 [dry] {src} -> {dest}\n",
    "Tab 7 [Vorschau] {src} -> {dest}\n",
    "Tab 7 [dry] {src} -> {dest}\n",
    "Tab 7 [dry] {src} -> {dest}\n",
)
row(
    "log.t7_line_dry_fallback",
    "Tab 7 [dry, fallback] {src} -> {dest}\n",
    "Tab 7 [Vorschau, Ausweich] {src} -> {dest}\n",
    "Tab 7 [dry, reserva] {src} -> {dest}\n",
    "Tab 7 [dry, repli] {src} -> {dest}\n",
)
row(
    "log.t7_line_copied",
    "Tab 7 copied: {src} -> {dest}\n",
    "Tab 7 kopiert: {src} -> {dest}\n",
    "Tab 7 copiado: {src} -> {dest}\n",
    "Tab 7 copié : {src} -> {dest}\n",
)
row(
    "log.t7_line_fallback",
    "Tab 7 copied (fallback): {src} -> {dest}\n",
    "Tab 7 kopiert (Ausweich): {src} -> {dest}\n",
    "Tab 7 copiado (reserva): {src} -> {dest}\n",
    "Tab 7 copié (repli) : {src} -> {dest}\n",
)
row(
    "log.t7_line_error",
    "Tab 7 error (not copied): {src} -> {dest}\n",
    "Tab 7 Fehler (nicht kopiert): {src} -> {dest}\n",
    "Tab 7 error (no copiado): {src} -> {dest}\n",
    "Tab 7 erreur (non copié) : {src} -> {dest}\n",
)
row(
    "log.t7_line_dry_delete",
    "Tab 7 [dry, mirror] would delete: {path}\n",
    "Tab 7 [Vorschau, Spiegeln] würde löschen: {path}\n",
    "Tab 7 [dry, espejo] borraría: {path}\n",
    "Tab 7 [dry, miroir] supprimerait : {path}\n",
)
row(
    "log.t7_line_deleted",
    "Tab 7 deleted (mirror): {path}\n",
    "Tab 7 gelöscht (Spiegeln): {path}\n",
    "Tab 7 borrado (espejo): {path}\n",
    "Tab 7 supprimé (miroir) : {path}\n",
)
row(
    "log.t7_line_error_delete",
    "Tab 7 error (not deleted): {path}\n",
    "Tab 7 Fehler (nicht gelöscht): {path}\n",
    "Tab 7 error (no borrado): {path}\n",
    "Tab 7 erreur (non supprimé) : {path}\n",
)
row(
    "log.t7_line_dry_update",
    "Tab 7 [dry] would refresh: {src} -> {dest}\n",
    "Tab 7 [Vorschau] würde aktualisieren: {src} -> {dest}\n",
    "Tab 7 [dry] actualizaría: {src} -> {dest}\n",
    "Tab 7 [dry] mettrait à jour : {src} -> {dest}\n",
)
row(
    "log.t7_line_copied_update",
    "Tab 7 refreshed: {src} -> {dest}\n",
    "Tab 7 aktualisiert: {src} -> {dest}\n",
    "Tab 7 actualizado: {src} -> {dest}\n",
    "Tab 7 rafraîchi : {src} -> {dest}\n",
)
row(
    "log.t7_line_error_update",
    "Tab 7 error (not refreshed): {src} -> {dest}\n",
    "Tab 7 Fehler (nicht aktualisiert): {src} -> {dest}\n",
    "Tab 7 error (no actualizado): {src} -> {dest}\n",
    "Tab 7 erreur (non mis à jour) : {src} -> {dest}\n",
)
row(
    "log.t7_undo_nothing",
    "Tab 7: nothing to undo — run a real copy (preview off) first.\n",
    "Tab 7: nichts rückgängig — zuerst echte Kopie ausführen (Vorschau aus).\n",
    "Tab 7: nada que deshacer — ejecute antes una copia real.\n",
    "Tab 7 : rien à annuler — lancez d’abord une copie réelle.\n",
)
row(
    "t7.undo_confirm_title",
    "Delete copied files?",
    "Kopierte Dateien löschen?",
    "¿Borrar archivos copiados?",
    "Supprimer les fichiers copiés ?",
)
row(
    "t7.undo_confirm_body",
    "Permanently delete the {n} file(s) from the last Tab 7 copy batch from disk? Folders created empty may remain.",
    "Die {n} Datei(en) aus dem letzten Tab-7-Kopiervorgang dauerhaft löschen? Leere angelegte Ordner können bleiben.",
    "¿Borrar permanentemente los {n} archivo(s) del último lote de copia de la pestaña 7? Pueden quedar carpetas vacías.",
    "Supprimer définitivement les {n} fichier(s) du dernier lot de copies (onglet 7) ? Des dossiers vides peuvent rester.",
)
row(
    "log.t7_undo_header",
    "Tab 7 — undo last copy batch\n",
    "Tab 7 — letzte Kopie rückgängig\n",
    "Tab 7 — deshacer último lote de copias\n",
    "Tab 7 — annuler dernier lot de copies\n",
)
row(
    "log.t7_undo_done",
    "Tab 7 undo: deleted {n} file(s) from disk.\n",
    "Tab 7 Rückgängig: {n} Datei(en) von der Festplatte gelöscht.\n",
    "Tab 7 deshacer: {n} archivo(s) borrado(s).\n",
    "Tab 7 annulation : {n} fichier(s) supprimé(s).\n",
)
row(
    "log.t7_undo_fail",
    "Tab 7 undo: could not delete {path}: {e}\n",
    "Tab 7 Rückgängig: Löschen fehlgeschlagen {path}: {e}\n",
    "Tab 7 deshacer: no se pudo borrar {path}: {e}\n",
    "Tab 7 annulation : suppression impossible {path} : {e}\n",
)

# Settings
row("settings.title", "Settings", "Einstellungen", "Ajustes", "Réglages")
row(
    "settings.version_caption",
    "Version {version}",
    "Version {version}",
    "Versión {version}",
    "Version {version}",
)
row(
    "settings.intro",
    "These options apply across all tabs.",
    "Diese Optionen gelten für alle Registerkarten.",
    "Estas opciones aplican a todas las pestañas.",
    "Ces options s’appliquent à tous les onglets.",
)
row("settings.language", "Language", "Sprache", "Idioma", "Langue")
row(
    "settings.language_hint",
    "Interface language (EN / DE / ES / FR). English is the fallback for missing translations.",
    "Oberflächensprache (EN / DE / ES / FR). Englisch ist Fallback für fehlende Übersetzungen.",
    "Idioma de la interfaz (EN / DE / ES / FR). El inglés es respaldo si falta traducción.",
    "Langue de l’interface (EN / DE / ES / FR). L’anglais complète les traductions manquantes.",
)
row("settings.appearance", "Appearance", "Erscheinungsbild", "Apariencia", "Apparence")
row(
    "settings.column_sep",
    "Column separator (; or ,) — used whenever this app writes a CSV (export, disk scan, Save, Tab 4 export)",
    "Spaltentrenner (; oder ,) — wird beim Schreiben jeder CSV verwendet (Export, Scan, Speichern, Tab-4-Export)",
    "Separador de columnas (; o ,) — al escribir cualquier CSV (exportación, escaneo, guardar, export tab 4)",
    "Séparateur de colonnes (; ou ,) — à chaque écriture CSV (export, analyse disque, enregistrer, export onglet 4)",
)
row(
    "settings.csv_detect",
    "When you open a CSV, ; or , is detected from the file automatically.",
    "Beim Öffnen einer CSV werden ; oder , automatisch aus der Datei erkannt.",
    "Al abrir un CSV, ; o , se detectan automáticamente del archivo.",
    "À l’ouverture d’un CSV, ; ou , est détecté automatiquement dans le fichier.",
)
row("settings.stash_group", "Stash (Tab 1 export)", "Stash (Tab-1-Export)", "Stash (export pestaña 1)", "Stash (export onglet 1)")
row(
    "settings.stash_hint",
    "Used for Tab 1 export and the “Check CSV export” button (same URL, API key, GraphQL path).",
    "Für Tab-1-Export und den Button „CSV-Export prüfen“ (dieselbe URL, API-Schlüssel, GraphQL-Pfad).",
    "Para export en pestaña 1 y «Comprobar exportación CSV» (misma URL, API y GraphQL).",
    "Pour l’export onglet 1 et « Vérifier export CSV » (même URL, clé API, chemin GraphQL).",
)
row("settings.graphql_path_label", "GraphQL path (empty = /graphql)", "GraphQL-Pfad (leer = /graphql)", "Ruta GraphQL (vacío = /graphql)", "Chemin GraphQL (vide = /graphql)")
row("settings.graphql_clear", "GraphQL default (clear)", "GraphQL-Standard (leeren)", "GraphQL predeterminado (borrar)", "GraphQL par défaut (effacer)")
row(
    "settings.saved_log",
    "Settings saved (appearance, column separator for CSV saves, Stash URL/API/GraphQL for export).",
    "Einstellungen gespeichert (Erscheinungsbild, CSV-Trenner, Stash-URL/API/GraphQL für Export).",
    "Ajustes guardados (apariencia, separador CSV, URL/API/GraphQL Stash para export).",
    "Réglages enregistrés (apparence, séparateur CSV, URL/API/GraphQL Stash pour l’export).",
)

# Dialog titles
row("dlg.save_log", "Save log", "Protokoll speichern", "Guardar registro", "Enregistrer le journal")
row("dlg.folder_scan", "Folder to scan", "Zu durchsuchender Ordner", "Carpeta a analizar", "Dossier à analyser")
row("dlg.restrict_rename", "Restrict renames to files under this folder", "Umbenennen auf Dateien unter diesem Ordner beschränken", "Limitar renombres a archivos bajo esta carpeta", "Limiter les renommages aux fichiers sous ce dossier")
row("dlg.folder_danger", "Folder to rename (dangerous)", "Umzubenennender Ordner (gefährlich)", "Carpeta a renombrar (peligroso)", "Dossier à renommer (dangereux)")
row("dlg.move_target", "Where to move files — choose folder (full path)", "Wohin verschieben — Ordner wählen (voller Pfad)", "Dónde mover archivos — elegir carpeta (ruta completa)", "Où déplacer — choisir le dossier (chemin complet)")
row("dlg.export_t4", "Export Tab 4 CSV", "Tab-4-CSV exportieren", "Exportar CSV pestaña 4", "Exporter CSV onglet 4")
row("dlg.choose_ps1", "Choose export_stash_files.ps1", "export_stash_files.ps1 wählen", "Elegir export_stash_files.ps1", "Choisir export_stash_files.ps1")
# Context menu (Tab 3 tree)
row("ctx.copy_folder_path", "Copy folder path", "Ordnerpfad kopieren", "Copiar ruta de carpeta", "Copier le chemin du dossier")
row("ctx.copy_file_name", "Copy file name", "Dateinamen kopieren", "Copiar nombre de archivo", "Copier le nom du fichier")
row(
    "ctx.copy_file_stem",
    "Copy name without extension",
    "Namen ohne Endung kopieren",
    "Copiar nombre sin extensión",
    "Copier le nom sans extension",
)
row(
    "ctx.copy_extension",
    "Copy extension only (e.g. .webm)",
    "Nur Endung kopieren (z. B. .webm)",
    "Copiar solo extensión (p. ej. .webm)",
    "Copier l’extension seulement (ex. .webm)",
)
row(
    "ctx.t3_name_to_find",
    "Put file name (no extension) in Find",
    "Dateiname ohne Endung in «Suchen»",
    "Poner nombre sin extensión en Buscar",
    "Mettre le nom (sans extension) dans Rechercher",
)
row(
    "ctx.t3_name_to_replace",
    "Put file name (no extension) in Replace",
    "Dateiname ohne Endung in «Ersetzen durch»",
    "Poner nombre sin extensión en Reemplazar por",
    "Mettre le nom (sans extension) dans Remplacer par",
)
row("ctx.open_in_explorer", "Open in Explorer", "Im Explorer öffnen", "Abrir en el Explorador", "Ouvrir dans l’Explorateur")
row("ctx.open_in_stash", "Open in Stash", "In Stash öffnen", "Abrir en Stash", "Ouvrir dans Stash")

# --- log & dynamic (templates use {placeholders}) ---
row("log.saved_log_to", "Saved log to {path}\n", "Protokoll gespeichert unter {path}\n", "Registro guardado en {path}\n", "Journal enregistré dans {path}\n")
row("log.save_log_failed", "Save log failed: {e}\n", "Protokoll speichern fehlgeschlagen: {e}\n", "Error al guardar registro: {e}\n", "Échec enregistrement journal : {e}\n")
row("log.folder_not_found", "Folder not found: {folder}\n", "Ordner nicht gefunden: {folder}\n", "Carpeta no encontrada: {folder}\n", "Dossier introuvable : {folder}\n")
row("log.t1_need_ps1", "Tab 1: set a valid path to export_stash_files.ps1.\n", "Tab 1: gültigen Pfad zu export_stash_files.ps1 setzen.\n", "Tab 1: ruta válida a export_stash_files.ps1.\n", "Tab 1 : chemin valide vers export_stash_files.ps1.\n")
row("log.batch_size_int", "Batch size (scenes per request) must be a whole number.\n", "Stapelgröße muss eine ganze Zahl sein.\n", "El tamaño de lote debe ser un número entero.\n", "La taille du lot doit être un entier.\n")
row("log.t1_export_header", "\n--- Tab 1: Stash file export ---\n", "\n--- Tab 1: Stash-Dateiexport ---\n", "\n--- Tab 1: exportación de archivos Stash ---\n", "\n--- Tab 1 : export fichiers Stash ---\n")
row("log.powershell_fail", "Failed to start PowerShell: {e}\n", "PowerShell konnte nicht gestartet werden: {e}\n", "No se pudo iniciar PowerShell: {e}\n", "Échec du démarrage de PowerShell : {e}\n")
row("log.exit_code", "\nExit code: {code}\n", "\nExit-Code: {code}\n", "\nCódigo de salida: {code}\n", "\nCode de sortie : {code}\n")
row("log.tip_tab3_csv", "Tip: switched Tab 3 CSV path to: {path}\n", "Hinweis: Tab-3-CSV-Pfad gesetzt auf: {path}\n", "Aviso: ruta CSV pestaña 3: {path}\n", "Astuce : chemin CSV onglet 3 : {path}\n")
row(
    "log.tip_shared_csv_tabs",
    "Tip: Tab 4 and Tab 5 CSV path set to the same file — click Load on those tabs (or reload) so title/date columns appear.\n",
    "Hinweis: Tab 4 und 5 zeigen dieselbe CSV-Datei — dort „Laden“ klicken (oder neu laden), damit Titel/Datum-Spalten erscheinen.\n",
    "Aviso: pestañas 4 y 5 usan el mismo CSV — pulse Cargar (o recargue) para ver título/fecha.\n",
    "Astuce : onglets 4 et 5 pointent sur le même CSV — cliquez Charger (ou rechargez) pour titre/date.\n",
)
row("log.t2_pick_folder", "Tab 2: choose a folder to scan.\n", "Tab 2: Ordner zum Scannen wählen.\n", "Tab 2: elija carpeta para escanear.\n", "Tab 2 : choisissez un dossier à analyser.\n")
row("log.not_directory", "Not a directory: {root}\n", "Kein Ordner: {root}\n", "No es un directorio: {root}\n", "Ce n’est pas un dossier : {root}\n")
row("log.t2_scanning", "\n--- Tab 2: scanning {root} (include subfolders={sub}) ---\n", "\n--- Tab 2: Scan {root} (Unterordner={sub}) ---\n", "\n--- Tab 2: escaneando {root} (subcarpetas={sub}) ---\n", "\n--- Tab 2 : analyse {root} (sous-dossiers={sub}) ---\n")
row("log.wrote_items", "Wrote {n} item(s) to {out}\n", "{n} Eintrag/Einträge nach {out} geschrieben\n", "Escritos {n} elemento(s) en {out}\n", "{n} élément(s) écrits dans {out}\n")
row("log.tip_t3_set", "Tip: Tab 3 CSV path set to: {path}\n", "Hinweis: Tab-3-CSV-Pfad: {path}\n", "Aviso: ruta CSV pestaña 3: {path}\n", "Astuce : chemin CSV onglet 3 : {path}\n")
row("log.t1_push_fail", "Tab 1: run export first or set a valid output CSV.\n", "Tab 1: zuerst exportieren oder gültige Ausgabe-CSV setzen.\n", "Tab 1: ejecute exportación o CSV de salida válido.\n", "Tab 1 : lancez l’export ou définissez un CSV de sortie valide.\n")
row("log.t2_push_fail", "Tab 2: run a scan first or set a valid output CSV.\n", "Tab 2: zuerst scannen oder gültige Ausgabe-CSV setzen.\n", "Tab 2: ejecute escaneo o CSV de salida válido.\n", "Tab 2 : lancez l’analyse ou définissez un CSV de sortie valide.\n")
row("log.t4_suggest_no_match", "Tab 4 suggest: no items match the current search.\n", "Tab 4 Vorschlag: keine Treffer für die aktuelle Suche.\n", "Tab 4 sugerencia: ningún elemento coincide con la búsqueda.\n", "Tab 4 suggestion : aucun élément ne correspond à la recherche.\n")
row("log.t4_suggest_no_paths", "Tab 4 suggest: no usable source paths.\n", "Tab 4 Vorschlag: keine brauchbaren Quellpfade.\n", "Tab 4 sugerencia: sin rutas de origen usables.\n", "Tab 4 suggestion : pas de chemins source utilisables.\n")
row(
    "log.t4_target_folder_select_row",
    "Tab 4: select one or more items in the list first, then click again.\n",
    "Tab 4: bitte zuerst einen oder mehrere Einträge in der Liste markieren, dann erneut klicken.\n",
    "Tab 4: primero selecciona uno o más elementos en la lista y vuelve a pulsar.\n",
    "Tab 4 : sélectionnez d’abord un ou plusieurs éléments dans la liste, puis recliquez.\n",
)
row(
    "log.t4_target_folder_no_path",
    "Tab 4: selected item has no file_path.\n",
    "Tab 4: markierter Eintrag hat keinen file_path.\n",
    "Tab 4: el elemento seleccionado no tiene file_path.\n",
    "Tab 4 : l’élément sélectionné n’a pas de file_path.\n",
)
row(
    "log.t4_target_folder_set",
    "Tab 4: move target set to: {path}\n",
    "Tab 4: Zielordner gesetzt auf: {path}\n",
    "Tab 4: destino de movimiento: {path}\n",
    "Tab 4 : cible de déplacement : {path}\n",
)
row(
    "log.t4_target_folder_multi",
    "Tab 4: {n} rows selected — using parent folder of the first selected row: {path}\n",
    "Tab 4: {n} Zeilen markiert — es wird der Ordner der ersten markierten Zeile verwendet: {path}\n",
    "Tab 4: {n} filas seleccionadas — se usa la carpeta superior de la primera fila: {path}\n",
    "Tab 4 : {n} lignes sélectionnées — dossier parent de la première ligne : {path}\n",
)
row("log.t4_mixed_drives", "Tab 4 suggest: mixed drives/roots detected, using first source root.\n", "Tab 4 Vorschlag: verschiedene Laufwerke/Wurzeln — erste Quelle genutzt.\n", "Tab 4: varias unidades/raíces; se usa la primera.\n", "Tab 4 : lecteurs/racines mixtes, utilisation de la première source.\n")
row(
    "log.t4_suggest_per_source",
    "Tab 4 suggest: next-to-original mode uses each file's own parent folder as base; subfolder set to {sub!r}.\n",
    "Tab 4 Vorschlag: Modus „neben Original“ nutzt jeweils den Elternordner; Unterordner {sub!r}.\n",
    "Tab 4 sugerencia: modo junto al original usa la carpeta padre; subcarpeta {sub!r}.\n",
    "Tab 4 suggestion : mode à côté de l’original ; sous-dossier {sub!r}.\n",
)
row(
    "log.t4_suggest_target",
    "Tab 4 suggest: target set to {base} and subfolder to {sub!r}.\n",
    "Tab 4 Vorschlag: Ziel {base}, Unterordner {sub!r}.\n",
    "Tab 4 sugerencia: destino {base}, subcarpeta {sub!r}.\n",
    "Tab 4 suggestion : cible {base}, sous-dossier {sub!r}.\n",
)
row("log.t4_need_csv", "Tab 4: set a valid CSV path.\n", "Tab 4: gültigen CSV-Pfad setzen.\n", "Tab 4: ruta CSV válida.\n", "Tab 4 : chemin CSV valide.\n")
row("log.t4_read_fail", "Tab 4: failed to read CSV: {e}\n", "Tab 4: CSV lesen fehlgeschlagen: {e}\n", "Tab 4: error al leer CSV: {e}\n", "Tab 4 : échec lecture CSV : {e}\n")
row(
    "log.t4_loaded",
    "Tab 4: loaded {n} item(s) from {path} (detected column separator: {sniff!r})\n",
    "Tab 4: {n} Eintrag/Einträge aus {path} geladen (Trenner: {sniff!r})\n",
    "Tab 4: cargados {n} elemento(s) desde {path} (separador: {sniff!r})\n",
    "Tab 4 : {n} élément(s) chargés depuis {path} (séparateur : {sniff!r})\n",
)
row("log.t4_export_empty", "Tab 4: nothing to export — load CSV first.\n", "Tab 4: nichts zu exportieren — zuerst CSV laden.\n", "Tab 4: nada que exportar — cargue CSV.\n", "Tab 4 : rien à exporter — chargez d’abord le CSV.\n")
row("log.t4_exported", "Tab 4: exported {n} item(s) to {path}\n", "Tab 4: {n} Eintrag/Einträge nach {path} exportiert\n", "Tab 4: exportados {n} elemento(s) a {path}\n", "Tab 4 : {n} élément(s) exportés vers {path}\n")
row("log.t4_export_fail", "Tab 4: export failed: {e}\n", "Tab 4: Export fehlgeschlagen: {e}\n", "Tab 4: error al exportar: {e}\n", "Tab 4 : échec export : {e}\n")
row(
    "log.t4_stats",
    "Items: {n} loaded · {f} match Search · {s} selected",
    "Einträge: {n} geladen · {f} passen zur Suche · {s} ausgewählt",
    "Elementos: {n} cargados · {f} coinciden · {s} seleccionados",
    "Éléments : {n} chargés · {f} correspondent · {s} sélectionnés",
)
row(
    "log.t4_preview_nextto",
    "Next-to-each-file mode: enter a valid subfolder name.",
    "Modus „neben Datei“: gültigen Unterordnernamen eingeben.",
    "Modo junto a cada archivo: nombre de subcarpeta válido.",
    "Mode à côté de chaque fichier : saisir un nom de sous-dossier valide.",
)
row(
    "log.t4_preview_mode_line",
    "Mode: next to each file's folder (destination = <that file's parent>\\{sub}\\<file>)",
    "Modus: neben Ordner jeder Datei (Ziel = <Elternordner>\\{sub}\\<Datei>)",
    "Modo: junto a la carpeta de cada archivo (destino = <padre>\\{sub}\\<archivo>)",
    "Mode : à côté du dossier de chaque fichier (destination = <parent>\\{sub}\\<fichier>)",
)
row("log.t4_empty_path_csv", "(missing path in CSV)", "(Pfad in CSV fehlt)", "(falta ruta en CSV)", "(chemin manquant dans le CSV)")
row("log.t4_more_items", "... and {n} more matching item(s) not shown.", "... und {n} weitere Treffer nicht angezeigt.", "... y {n} coincidencias más no mostradas.", "... et {n} correspondances de plus non affichées.")
row(
    "log.t4_preview_set_move",
    "Set Where to move files (full path, e.g. D:\\\\Media\\\\Sorted) to see destinations in the preview.",
    "„Wohin verschieben“ (voller Pfad, z. B. D:\\\\Medien\\\\Sortiert) setzen, um Ziele in der Vorschau zu sehen.",
    "Indique «Dónde mover» (ruta completa, p. ej. D:\\\\Media\\\\Sorted) para ver destinos en la vista previa.",
    "Renseignez « Où déplacer » (chemin complet, ex. D:\\\\Media\\\\Tri) pour voir les destinations dans l’aperçu.",
)
row("log.t4_dest_root", "Destination root: {root}", "Zielwurzel: {root}", "Raíz de destino: {root}", "Racine de destination : {root}")
row("log.t4_invalid_target", "Invalid target folder.", "Ungültiger Zielordner.", "Carpeta de destino no válida.", "Dossier cible invalide.")
row(
    "log.t4_preview_arrow_err",
    "  -> (preview error: {e})",
    "  -> (Vorschaufehler: {e})",
    "  -> (error de vista previa: {e})",
    "  -> (erreur d’aperçu : {e})",
)
row(
    "log.t4_name_only",
    "{fp} (file not found on disk — name-only preview)",
    "{fp} (Datei nicht auf der Festplatte — nur Namensvorschau)",
    "{fp} (archivo no encontrado — vista previa solo por nombre)",
    "{fp} (fichier introuvable — aperçu sur le nom seulement)",
)
row(
    "log.t4_plan",
    "Plan: {run} · {source} · {place}",
    "Plan: {run} · {source} · {place}",
    "Plan: {run} · {source} · {place}",
    "Plan : {run} · {source} · {place}",
)
row("plan.run.preview", "preview only", "nur Vorschau", "solo vista previa", "aperçu seulement")
row("plan.run.real", "apply for real", "wirklich ausführen", "aplicar de verdad", "exécution réelle")
row("plan.source.selected", "selected items only", "nur Auswahl", "solo seleccionados", "sélection seulement")
row("plan.source.all_search", "all items matching Search", "alle Suchtreffer", "todos los que coinciden", "tout ce qui correspond à Recherche")
row("plan.place.next", "next to each file's folder", "neben Ordner jeder Datei", "junto a carpeta de cada archivo", "à côté du dossier de chaque fichier")
row("plan.place.one", "one destination folder", "ein Zielordner", "una carpeta de destino", "un dossier de destination")
row("log.t3_need_csv", "Tab 3: set a valid CSV path.\n", "Tab 3: gültigen CSV-Pfad setzen.\n", "Tab 3: ruta CSV válida.\n", "Tab 3 : chemin CSV valide.\n")
row("log.csv_read_fail", "Failed to read CSV: {e}\n", "CSV lesen fehlgeschlagen: {e}\n", "Error al leer CSV: {e}\n", "Échec lecture CSV : {e}\n")
row(
    "log.t3_loaded",
    "Loaded {n} item(s) from {path} (detected column separator: {sniff!r})\n",
    "{n} Eintrag/Einträge aus {path} geladen (Trenner: {sniff!r})\n",
    "Cargados {n} elemento(s) desde {path} (separador: {sniff!r})\n",
    "{n} élément(s) chargés depuis {path} (séparateur : {sniff!r})\n",
)
row("log.t3_saved", "Saved {n} item(s) to {path}\n", "{n} Eintrag/Einträge nach {path} gespeichert\n", "Guardados {n} elemento(s) en {path}\n", "{n} élément(s) enregistrés dans {path}\n")
row("log.save_failed", "Save failed: {e}\n", "Speichern fehlgeschlagen: {e}\n", "Error al guardar: {e}\n", "Échec enregistrement : {e}\n")
row("log.select_item_path", "Select an item that has a file path first.\n", "Zuerst einen Eintrag mit Dateipfad wählen.\n", "Seleccione un elemento con ruta de archivo.\n", "Sélectionnez d’abord un élément avec un chemin fichier.\n")
row("log.clipboard_fail", "Clipboard unavailable.\n", "Zwischenablage nicht verfügbar.\n", "Portapapeles no disponible.\n", "Presse-papiers indisponible.\n")
row("log.copied_path", "Copied folder path to clipboard.\n", "Ordnerpfad in Zwischenablage kopiert.\n", "Ruta de carpeta copiada.\n", "Chemin du dossier copié dans le presse-papiers.\n")
row("log.copied_file_name", "Copied file name to clipboard.\n", "Dateiname in die Zwischenablage kopiert.\n", "Nombre de archivo copiado al portapapeles.\n", "Nom de fichier copié dans le presse-papiers.\n")
row(
    "log.copied_file_stem",
    "Copied file name (no extension) to clipboard.\n",
    "Dateinamen ohne Endung in die Zwischenablage kopiert.\n",
    "Nombre sin extensión copiado al portapapeles.\n",
    "Nom sans extension copié dans le presse-papiers.\n",
)
row("log.copied_extension", "Copied extension to clipboard.\n", "Dateiendung in die Zwischenablage kopiert.\n", "Extensión copiada al portapapeles.\n", "Extension copiée dans le presse-papiers.\n")
row("log.no_extension", "That file name has no extension to copy.\n", "Dieser Dateiname hat keine Endung zum Kopieren.\n", "Ese nombre no tiene extensión para copiar.\n", "Ce nom n’a pas d’extension à copier.\n")
row(
    "log.empty_stem",
    "Name-without-extension is empty — nothing copied.\n",
    "Name ohne Endung ist leer — nichts kopiert.\n",
    "El nombre sin extensión está vacío — no se copió nada.\n",
    "Le nom sans extension est vide — rien n’a été copié.\n",
)
row("log.select_item", "Select an item first.\n", "Zuerst einen Eintrag wählen.\n", "Seleccione un elemento primero.\n", "Sélectionnez d’abord un élément.\n")
row("log.path_semicolon", "Path contains \"; opening parent folder only.\n", "Pfad enthält \"; nur übergeordneten Ordner öffnen.\n", "La ruta contiene «;»; abriendo solo carpeta padre.\n", "Le chemin contient « ; » ; ouverture du dossier parent seulement.\n")
row("log.path_not_found", "Path not found: {fp!r}\n", "Pfad nicht gefunden: {fp!r}\n", "Ruta no encontrada: {fp!r}\n", "Chemin introuvable : {fp!r}\n")
row("log.prefix_sep", "Prefix/suffix must not contain path separators.\n", "Präfix/Suffix darf keine Pfadtrenner enthalten.\n", "Prefijo/sufijo no debe contener separadores de ruta.\n", "Préfixe/suffixe sans séparateurs de chemin.\n")
row(
    "log.applied_prefix_search",
    "Applied prefix/suffix to {n} item(s) matching Search.\n",
    "Präfix/Suffix auf {n} Suchtreffer angewendet.\n",
    "Prefijo/sufijo aplicado a {n} coincidencias.\n",
    "Préfixe/suffixe appliqué à {n} résultats de recherche.\n",
)
row("log.select_multi", "Select one or more items first.\n", "Einen oder mehrere Einträge wählen.\n", "Seleccione uno o más elementos.\n", "Sélectionnez un ou plusieurs éléments.\n")
row(
    "log.applied_prefix_sel",
    "Applied prefix/suffix to {n} selected item(s).\n",
    "Präfix/Suffix auf {n} ausgewählte Einträge angewendet.\n",
    "Prefijo/sufijo aplicado a {n} seleccionados.\n",
    "Préfixe/suffixe appliqué à {n} éléments sélectionnés.\n",
)
row(
    "log.t3_ext_inherited",
    "Added the current file's extension to \"New file name\" on {n} row(s) where it was missing.\n",
    "Bei {n} Zeile(n) wurde die fehlende Dateiendung vom aktuellen Dateinamen an „Neuer Dateiname“ angehängt.\n",
    "Se añadió la extensión del archivo actual a «nuevo nombre» en {n} fila(s) donde faltaba.\n",
    "Extension du fichier actuelle ajoutée au « nouveau nom » sur {n} ligne(s) lorsqu’elle manquait.\n",
)
row(
    "log.t3_disambiguate",
    "Adjusted \"New file name\" on {n} row(s) so no two files in the same folder would get the same new name (including names already on disk).\n",
    "„Neuer Dateiname“ bei {n} Zeile(n) angepasst, damit im gleichen Ordner keine Namenskollision entsteht (inkl. schon vorhandener Dateien).\n",
    "Se ajustó «nuevo nombre» en {n} fila(s) para evitar el mismo nombre en la misma carpeta (incl. nombres ya existentes).\n",
    "« Nouveau nom » ajusté sur {n} ligne(s) pour éviter un doublon dans le même dossier (y compris noms déjà présents).\n",
)
row("log.fr_find_empty", "Find/replace: \"Find\" must not be empty.\n", "Suchen/Ersetzen: „Suchen“ darf nicht leer sein.\n", "Buscar/reemplazar: «Buscar» no puede estar vacío.\n", "Rechercher/remplacer : « Rechercher » ne doit pas être vide.\n")
row(
    "log.fr_replace_invalid",
    "Find/replace: replacement must not contain \\ / : (file name only).\n",
    "Suchen/Ersetzen: Ersetzung ohne \\ / : (nur Dateiname).\n",
    "Buscar/reemplazar: el reemplazo sin \\ / : (solo nombre).\n",
    "Rechercher/remplacer : le remplacement sans \\ / : (nom de fichier seul).\n",
)
row("log.no_items_list", "No items in the list (load a CSV and/or change Search).\n", "Keine Einträge in der Liste (CSV laden und/oder Suche ändern).\n", "No hay elementos (cargue CSV y/o cambie búsqueda).\n", "Aucun élément (chargez un CSV et/ou modifiez Recherche).\n")
row(
    "log.fr_applied_search",
    "Find/replace: set new file name on {u} item(s){skip} (items matching Search).\n",
    "Suchen/Ersetzen: neuer Dateiname für {u} Eintrag/Einträge{skip} (Suchtreffer).\n",
    "Buscar/reemplazar: nuevo nombre en {u} elemento(s){skip} (coincidencias).\n",
    "Rechercher/remplacer : nouveau nom sur {u} élément(s){skip} (résultats recherche).\n",
)
row(
    "log.fr_applied_sel",
    "Find/replace: set new file name on {u} item(s){skip} (selected items).\n",
    "Suchen/Ersetzen: neuer Dateiname für {u} Eintrag/Einträge{skip} (Auswahl).\n",
    "Buscar/reemplazar: nuevo nombre en {u} elemento(s){skip} (selección).\n",
    "Rechercher/remplacer : nouveau nom sur {u} élément(s){skip} (sélection).\n",
)
row(
    "log.fr_zero_hits",
    "Find/replace: no matches in the current file name or in \"New file name\" (where filled). The Path column is not searched — use text that appears in those name columns, or clear \"New file name\" if it hides the text you want to match.\n",
    "Suchen/Ersetzen: kein Treffer im aktuellen Dateinamen oder in „Neuer Dateiname“ (falls ausgefüllt). Die Pfad-Spalte wird nicht durchsucht — der Suchtext muss in diesen Namen vorkommen, oder „Neuer Dateiname“ leeren, falls er stört.\n",
    "Buscar/reemplazar: sin coincidencias en el nombre actual ni en «nuevo nombre» (si hay). La columna de ruta no se busca — use texto que aparezca en esos nombres o vacíe «nuevo nombre» si bloquea.\n",
    "Rechercher/remplacer : aucune occurrence dans le nom actuel ou le « nouveau nom » (s’il est rempli). La colonne chemin n’est pas prise en compte — utilisez du texte présent dans ces noms, ou videz « nouveau nom » s’il masque le texte.\n",
)
row("log.skip_invalid_suffix", ", skipped {n} invalid", ", {n} ungültige übersprungen", ", omitidos {n} no válidos", ", {n} invalides ignorés")
row(
    "log.cleared_new_names",
    'Cleared "New file name" on items matching Search.\n',
    "„Neuer Dateiname“ bei Suchtreffern geleert.\n",
    "Borrado «nuevo nombre» en coincidencias.\n",
    "« Nouveau nom » effacé sur les résultats de recherche.\n",
)
row(
    "log.t3_rename_need_selection",
    "Tab 3: turn off «Rename on disk: selected rows only» or select one or more rows before renaming.\n",
    "Tab 3: «Umbenennen: nur markierte Zeilen» deaktivieren oder Zeilen markieren, dann umbenennen.\n",
    "Tab 3: desactive «Renombrar: solo selección» o seleccione filas antes de renombrar.\n",
    "Tab 3 : décochez « Renommer : lignes sélectionnées » ou sélectionnez des lignes avant de renommer.\n",
)
row("log.load_csv_first", "Load a CSV first.\n", "Zuerst eine CSV laden.\n", "Cargue primero un CSV.\n", "Chargez d’abord un CSV.\n")
row(
    "log.t3_rename_done",
    "\n{preview}Processed: {renamed} rename(s), {skipped} skipped.\n",
    "\n{preview}Verarbeitet: {renamed} Umbenennung(en), {skipped} übersprungen.\n",
    "\n{preview}Procesado: {renamed} renombre(s), {skipped} omitidos.\n",
    "\n{preview}Traité : {renamed} renommage(s), {skipped} ignorés.\n",
)
row("log.preview_prefix", "Preview only — ", "Nur Vorschau — ", "Solo vista previa — ", "Aperçu seulement — ")
row("log.fold_confirm_first", "Folder rename: enable the confirmation checkbox first.\n", "Ordner umbenennen: zuerst Bestätigung aktivieren.\n", "Renombrar carpeta: active la confirmación primero.\n", "Renommage dossier : cochez d’abord la confirmation.\n")
row("log.fold_need_values", "Folder rename: set folder and new name.\n", "Ordner umbenennen: Ordner und neuen Namen setzen.\n", "Renombrar carpeta: indique carpeta y nombre.\n", "Renommage dossier : dossier et nouveau nom requis.\n")
row("log.fold_result", "Folder rename: {msg}\n", "Ordner umbenennen: {msg}\n", "Renombrar carpeta: {msg}\n", "Renommage dossier : {msg}\n")
row("log.t4_load_first", "Load a CSV first in Tab 4.\n", "Zuerst CSV in Tab 4 laden.\n", "Cargue CSV en pestaña 4.\n", "Chargez d’abord un CSV dans l’onglet 4.\n")
row("log.t4_no_items_mode", "Tab 4: no items to process ({mode}).\n", "Tab 4: keine Einträge zu verarbeiten ({mode}).\n", "Tab 4: no hay elementos para procesar ({mode}).\n", "Tab 4 : aucun élément à traiter ({mode}).\n")
row(
    "log.t4_need_dest",
    "Tab 4: set a full destination folder path (e.g. D:\\Media\\Sorted).\n",
    "Tab 4: vollen Zielordner setzen (z. B. D:\\Medien\\Sortiert).\n",
    "Tab 4: ruta completa de destino (p. ej. D:\\Media\\Sorted).\n",
    "Tab 4 : chemin complet du dossier cible (ex. D:\\Media\\Tri).\n",
)
row(
    "log.t4_dest_absolute",
    "Tab 4: destination must be a full path from the drive letter, got: {target!r}\n",
    "Tab 4: Ziel muss voller Pfad ab Laufwerksbuchstabe sein, erhalten: {target!r}\n",
    "Tab 4: el destino debe ser ruta completa desde la unidad: {target!r}\n",
    "Tab 4 : destination = chemin complet depuis la lettre de lecteur, reçu : {target!r}\n",
)
row(
    "log.t4_move_only_header",
    "\n--- Tab 4: move only ({mode}) ---\n",
    "\n--- Tab 4: nur Verschieben ({mode}) ---\n",
    "\n--- Tab 4: solo mover ({mode}) ---\n",
    "\n--- Tab 4 : déplacement seul ({mode}) ---\n",
)
row(
    "log.t4_move_only_done",
    "\n{preview}Processed: moved {moved}, skipped {skipped}.\n",
    "\n{preview}Verarbeitet: verschoben {moved}, übersprungen {skipped}.\n",
    "\n{preview}Procesado: movidos {moved}, omitidos {skipped}.\n",
    "\n{preview}Traité : déplacés {moved}, ignorés {skipped}.\n",
)
row("log.t5_need_csv", "Tab 5: set a valid CSV path.\n", "Tab 5: gültigen CSV-Pfad setzen.\n", "Tab 5: ruta CSV válida.\n", "Tab 5 : chemin CSV valide.\n")
row(
    "log.t5_loaded",
    "Tab 5: loaded {n} item(s) from {path} (delimiter {sniff}).\n",
    "Tab 5: {n} Eintrag/Einträge aus {path} geladen (Trenner {sniff}).\n",
    "Tab 5: {n} elemento(s) desde {path} (delimitador {sniff}).\n",
    "Tab 5 : {n} élément(s) depuis {path} (délimiteur {sniff}).\n",
)
row(
    "log.t5_saved",
    "Tab 5: saved {n} item(s) to {path}\n",
    "Tab 5: {n} Eintrag/Einträge nach {path} gespeichert\n",
    "Tab 5: guardados {n} elemento(s) en {path}\n",
    "Tab 5 : {n} élément(s) enregistrés dans {path}\n",
)
row(
    "log.t5_no_ffprobe",
    "Tab 5: ffprobe not found — install FFmpeg and ensure ffprobe is on PATH.\n",
    "Tab 5: ffprobe nicht gefunden — FFmpeg installieren, ffprobe im PATH.\n",
    "Tab 5: ffprobe no encontrado — instale FFmpeg y PATH.\n",
    "Tab 5 : ffprobe introuvable — installez FFmpeg et le PATH.\n",
)
row(
    "log.t5_probed",
    "Tab 5: ffprobe OK for {ok} of {total} file path(s); list refreshed.\n",
    "Tab 5: ffprobe für {ok} von {total} Dateipfad(en) OK; Liste aktualisiert.\n",
    "Tab 5: ffprobe OK en {ok} de {total} ruta(s) de archivo; lista actualizada.\n",
    "Tab 5 : ffprobe OK pour {ok} sur {total} chemin(s) fichier ; liste actualisée.\n",
)
row(
    "log.t5_probe_row_fail",
    "Tab 5 ffprobe skip {path}: {err}\n",
    "Tab 5 ffprobe überspringe {path}: {err}\n",
    "Tab 5 ffprobe omitir {path}: {err}\n",
    "Tab 5 ffprobe ignorer {path} : {err}\n",
)
row(
    "log.t5_fill_done",
    "Tab 5: filled new_leaf on {n} item(s).\n",
    "Tab 5: „Neuer Dateiname“ bei {n} Eintrag/Einträgen gesetzt.\n",
    "Tab 5: new_leaf rellenado en {n} elemento(s).\n",
    "Tab 5 : new_leaf rempli pour {n} élément(s).\n",
)
row(
    "log.t5_append_tags_done",
    "Tab 5: appended checked tags on {n} item(s).\n",
    "Tab 5: angehakte Tags bei {n} Eintrag/Einträgen angehängt.\n",
    "Tab 5: etiquetas marcadas añadidas en {n} elemento(s).\n",
    "Tab 5 : tags cochés ajoutés sur {n} élément(s).\n",
)
row(
    "log.t5_open_stash",
    "Tab 5: opened in browser: {url}\n",
    "Tab 5: im Browser geöffnet: {url}\n",
    "Tab 5: abierto en el navegador: {url}\n",
    "Tab 5 : ouvert dans le navigateur : {url}\n",
)
row(
    "log.t5_stash_need_scene_id",
    "Tab 5: selected row(s) have no scene_id — set Tab 1 «Stash URL» if needed, and use a Stash CSV export so scene_id is filled.\n",
    "Tab 5: bei der Auswahl fehlt scene_id — ggf. Stash-URL in Tab 1 prüfen; CSV aus Stash-Export nutzen, damit scene_id gefüllt ist.\n",
    "Tab 5: la selección no tiene scene_id — revise la URL en pestaña 1 y use un CSV exportado desde Stash con scene_id.\n",
    "Tab 5 : pas de scene_id sur la sélection — vérifiez l’URL Stash (onglet 1) et un CSV exporté depuis Stash avec scene_id.\n",
)
row(
    "log.t5_open_stash_fail",
    "Tab 5: could not open browser: {e}\n",
    "Tab 5: Browser konnte nicht geöffnet werden: {e}\n",
    "Tab 5: no se pudo abrir el navegador: {e}\n",
    "Tab 5 : impossible d’ouvrir le navigateur : {e}\n",
)
row(
    "log.t5_open_stash_fail_browser",
    "Tab 5: the system returned no browser for this URL (webbrowser.open).\n",
    "Tab 5: das System hat keinen Browser für diese URL gemeldet (webbrowser.open).\n",
    "Tab 5: el sistema no devolvió navegador para esta URL (webbrowser.open).\n",
    "Tab 5 : aucun navigateur pour cette URL (webbrowser.open).\n",
)
row(
    "log.t5_rename_need_selection",
    "Tab 5: select at least one item, or turn off “Selected items only”.\n",
    "Tab 5: mindestens einen Eintrag markieren oder „Nur ausgewählte Einträge“ deaktivieren.\n",
    "Tab 5: elija al menos un elemento o desactive «Solo elementos seleccionados».\n",
    "Tab 5 : sélectionnez au moins un élément ou désactivez « Uniquement les éléments sélectionnés ».\n",
)
row(
    "log.t5_rename_summary",
    "Tab 5 rename: done (dry_run={dry}). Renamed: {renamed}, skipped: {skipped}.\n",
    "Tab 5 Umbenennen: fertig (dry_run={dry}). Umbenannt: {renamed}, übersprungen: {skipped}.\n",
    "Tab 5 renombrar: hecho (dry_run={dry}). Renombrados: {renamed}, omitidos: {skipped}.\n",
    "Tab 5 renommage : terminé (dry_run={dry}). Renommés : {renamed}, ignorés : {skipped}.\n",
)
row(
    "log.undo_rename_nothing",
    "Nothing to undo — run a real disk rename or move (preview off) first.\n",
    "Nichts rückgängig zu machen — zuerst echtes Umbenennen oder Verschieben (Vorschau aus).\n",
    "Nada que deshacer — ejecute antes un renombrado o movimiento real (sin vista previa).\n",
    "Rien à annuler — lancez d’abord un renommage ou un déplacement réel (sans aperçu).\n",
)
row(
    "log.undo_rename_done",
    "Undo: reverted {n} path(s) on disk.\n",
    "Rückgängig: {n} Pfad/Pfade auf der Festplatte zurückgesetzt.\n",
    "Deshacer: {n} ruta(s) revertida(s) en el disco.\n",
    "Annulation : {n} chemin(s) restauré(s) sur le disque.\n",
)
row(
    "log.undo_rename_done_preview",
    "Undo preview: {n} step(s) logged (disk unchanged — turn off preview and undo again to apply).\n",
    "Rückgängig-Vorschau: {n} Schritt(e) im Log (Festplatte unverändert — Vorschau aus, erneut rückgängig zum Anwenden).\n",
    "Vista previa de deshacer: {n} paso(s) en el registro (disco sin cambios — desactive la vista previa y repita).\n",
    "Aperçu d’annulation : {n} étape(s) dans le journal (disque inchangé — désactivez l’aperçu puis réessayez).\n",
)
row(
    "log.undo_rename_more_available",
    "{m} more disk action(s) can still be undone (header button).\n",
    "Noch {m} Festplatten-Aktion(en) rückgängig machbar (Kopfzeilen-Button).\n",
    "Aún se puede deshacer {m} acción(es) en disco (botón superior).\n",
    "Encore {m} action(s) disque annulable(s) (bouton d’en-tête).\n",
)
row(
    "log.undo_stack_trimmed",
    "Undo history: dropped {n} oldest batch(es) (limit {max} disk actions kept in memory).\n",
    "Rückgängig-Verlauf: {n} älteste Stapel verworfen (max. {max} Aktionen im Speicher).\n",
    "Historial de deshacer: descartados {n} lote(s) antiguo(s) (límite {max} acciones en memoria).\n",
    "Historique d’annulation : {n} lot(s) le/la plus vieux ignorés (limite {max} actions en mémoire).\n",
)
row(
    "log.t5_preset_save_fail",
    "Tab 5: could not save presets file: {e}\n",
    "Tab 5: Voreinstellungsdatei nicht speicherbar: {e}\n",
    "Tab 5: no se pudo guardar preajustes: {e}\n",
    "Tab 5 : impossible d’enregistrer les préréglages : {e}\n",
)
row("log.t5_preset_need_name", "Tab 5: enter a preset name before saving.\n", "Tab 5: Namen für die Voreinstellung eingeben.\n", "Tab 5: nombre del preajuste.\n", "Tab 5 : saisissez un nom de préréglage.\n")
row("log.t5_preset_bad_name", "Tab 5: that preset name is reserved.\n", "Tab 5: dieser Name ist reserviert.\n", "Tab 5: nombre reservado.\n", "Tab 5 : nom réservé.\n")
row(
    "log.t5_preset_saved",
    "Tab 5: preset “{name}” saved to schema_rename_presets.json\n",
    "Tab 5: Voreinstellung „{name}“ in schema_rename_presets.json gespeichert\n",
    "Tab 5: preajuste «{name}» guardado en schema_rename_presets.json\n",
    "Tab 5 : préréglage « {name} » enregistré dans schema_rename_presets.json\n",
)
row("log.t5_preset_none_selected", "Tab 5: select a preset to delete (not “—”).\n", "Tab 5: zu löschende Voreinstellung wählen (nicht „—“).\n", "Tab 5: elija un preajuste para borrar.\n", "Tab 5 : choisissez un préréglage à supprimer.\n")
row(
    "log.t5_preset_deleted",
    "Tab 5: deleted preset “{name}”.\n",
    "Tab 5: Voreinstellung „{name}“ gelöscht.\n",
    "Tab 5: preajuste «{name}» borrado.\n",
    "Tab 5 : préréglage « {name} » supprimé.\n",
)
row(
    "log.test_stash",
    "\n--- Test Stash connection ({url}{gql}) ---\n",
    "\n--- Stash-Verbindung testen ({url}{gql}) ---\n",
    "\n--- Probar conexión Stash ({url}{gql}) ---\n",
    "\n--- Test connexion Stash ({url}{gql}) ---\n",
)
row("log.ok_prefix", "OK: ", "OK: ", "OK: ", "OK : ")
row("log.fail_prefix", "FAIL: ", "FEHLER: ", "FALLO: ", "ÉCHEC : ")
row(
    "log.probe_csv_export",
    "\n--- Check Stash CSV export ({url}{gql}) ---\n",
    "\n--- Stash-CSV-Export prüfen ({url}{gql}) ---\n",
    "\n--- Comprobar exportación CSV Stash ({url}{gql}) ---\n",
    "\n--- Vérifier export CSV Stash ({url}{gql}) ---\n",
)
row(
    "log.export_line_ok",
    "OK — {detail}",
    "OK — {detail}",
    "OK — {detail}",
    "OK — {detail}",
)
row(
    "log.export_line_fail",
    "FAIL — {detail}",
    "FEHLER — {detail}",
    "FALLO — {detail}",
    "ÉCHEC — {detail}",
)

# mode labels passed to logs (already translated)
row("mode.selected_items", "selected items", "ausgewählte Einträge", "elementos seleccionados", "éléments sélectionnés")
row("mode.search_matches", "items matching Search", "Suchtreffer", "coincidencias de búsqueda", "résultats de recherche")


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "en.json").write_text(json.dumps(EN, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "de.json").write_text(json.dumps(DE, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "es.json").write_text(json.dumps(ES, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "fr.json").write_text(json.dumps(FR, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", len(EN), "keys to locales/*.json")


if __name__ == "__main__":
    main()
