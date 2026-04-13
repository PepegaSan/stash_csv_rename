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
row("common.save_log", "Save log to file…", "Protokoll speichern…", "Guardar registro en archivo…", "Enregistrer le journal…")
row("common.clear_log", "Clear log", "Protokoll leeren", "Vaciar registro", "Vider le journal")
row("common.csv_file", "CSV file", "CSV-Datei", "Archivo CSV", "Fichier CSV")
row("common.search", "Search", "Suche", "Buscar", "Recherche")
row("common.stash_url", "Stash URL", "Stash-URL", "URL de Stash", "URL Stash")
row("common.api_key", "API key (if login enabled)", "API-Schlüssel (falls Login aktiv)", "Clave API (si hay inicio de sesión)", "Clé API (si connexion activée)")
row("common.find", "Find", "Suchen", "Buscar", "Rechercher")
row("common.replace_with", "Replace with", "Ersetzen durch", "Reemplazar por", "Remplacer par")
row("common.prefix", "Prefix", "Präfix", "Prefijo", "Préfixe")
row("common.folder", "Folder", "Ordner", "Carpeta", "Dossier")
row("common.new_name", "New name", "Neuer Name", "Nombre nuevo", "Nouveau nom")

# tab titles (must match tabs.add / _scroll_wrap)
row("tab.1", "1 · Stash file CSV", "1 · Stash-Datei-CSV", "1 · CSV de archivos Stash", "1 · CSV fichiers Stash")
row("tab.2", "2 · Disk scan", "2 · Datenträger-Scan", "2 · Escaneo de disco", "2 · Analyse disque")
row("tab.3", "3 · Rename", "3 · Umbenennen", "3 · Renombrar", "3 · Renommer")
row("tab.4", "4 · Move + Stash update", "4 · Verschieben + Stash-Update", "4 · Mover + actualizar Stash", "4 · Déplacer + MAJ Stash")

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
    "Theme and column separator (; or ,) for saved CSV files, plus Stash URL/API (Tab 1 + Tab 4): ⚙ top-right. Tabs 3 and 4 detect ; or , when you load a file. Saved CSVs use UTF-8 with BOM for Excel.",
    "Design und Spaltentrenner (; oder ,) für gespeicherte CSVs sowie Stash-URL/API (Tab 1 + Tab 4): ⚙ oben rechts. Tabs 3 und 4 erkennen ; oder , beim Laden. Gespeicherte CSVs: UTF-8 mit BOM für Excel.",
    "Tema y separador de columnas (; o ,) para CSV guardados y URL/API de Stash (pestañas 1 y 4): ⚙ arriba a la derecha. Las pestañas 3 y 4 detectan ; o , al cargar. CSV guardados: UTF-8 con BOM para Excel.",
    "Thème et séparateur de colonnes (; ou ,) pour les CSV enregistrés, plus URL/API Stash (onglets 1 et 4) : ⚙ en haut à droite. Les onglets 3 et 4 détectent ; ou , à l’ouverture. CSV enregistrés : UTF-8 avec BOM pour Excel.",
)
row("t1.batch_size", "Batch size (scenes per request)", "Stapelgröße (Szenen pro Anfrage)", "Tamaño de lote (escenas por solicitud)", "Taille du lot (scènes par requête)")
row("t1.filters_title", "Optional filters (all boxes must match)", "Optionale Filter (alle Felder müssen passen)", "Filtros opcionales (todas las casillas deben coincidir)", "Filtres optionnels (toutes les cases doivent correspondre)")
row("t1.path_prefix", "Path prefix (e.g. D:\\Media\\X)", "Pfad-Präfix (z. B. D:\\Medien\\X)", "Prefijo de ruta (p. ej. D:\\Media\\X)", "Préfixe de chemin (ex. D:\\Media\\X)")
row("t1.path_contains", "Path contains", "Pfad enthält", "La ruta contiene", "Le chemin contient")
row("t1.name_contains", "File name contains", "Dateiname enthält", "El nombre de archivo contiene", "Le nom de fichier contient")
row("t1.name_regex", "File name — regex (PowerShell)", "Dateiname — Regex (PowerShell)", "Nombre de archivo — regex (PowerShell)", "Nom de fichier — regex (PowerShell)")
row("t1.run_export", "Run Stash export", "Stash-Export starten", "Ejecutar exportación Stash", "Lancer l’export Stash")
row("t1.test_connection", "Test Stash connection", "Stash-Verbindung testen", "Probar conexión con Stash", "Tester la connexion Stash")
row("t1.check_path_update", "Check path-update support", "Pfad-Update-Unterstützung prüfen", "Comprobar soporte de actualización de rutas", "Vérifier la prise en charge MAJ chemins")
row("t1.open_out_folder", "Open output folder", "Ausgabeordner öffnen", "Abrir carpeta de salida", "Ouvrir le dossier de sortie")
row("t1.send_csv_to", "Send CSV to", "CSV senden an", "Enviar CSV a", "Envoyer le CSV vers")
row("t1.tab3_rename", "Tab 3 — rename", "Tab 3 — Umbenennen", "Pestaña 3 — renombrar", "Onglet 3 — renommer")
row("t1.tab4_move", "Tab 4 — move", "Tab 4 — Verschieben", "Pestaña 4 — mover", "Onglet 4 — déplacer")
row("t1.label.save_csv", "Save list as (CSV)", "Liste speichern als (CSV)", "Guardar lista como (CSV)", "Enregistrer la liste (CSV)")

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
    "Steps: 1) Load CSV  2) Use Search to narrow the list  3) Keep Preview only checked to try safely  4) Rename files on disk.\nEverything under \"Advanced (optional)\" is extra — you can skip it for simple renames.",
    "Schritte: 1) CSV laden  2) Suche nutzen  3) „Nur Vorschau“ zum Testen anlassen  4) Dateien auf der Festplatte umbenennen.\nAlles unter „Erweitert (optional)“ ist Zusatz — für einfache Umbenennungen kannst du es weglassen.",
    "Pasos: 1) Cargar CSV  2) Usar búsqueda  3) Dejar solo vista previa para probar  4) Renombrar archivos en disco.\nTodo bajo «Avanzado (opcional)» es extra — puedes omitirlo para renombres simples.",
    "Étapes : 1) Charger le CSV  2) Affiner avec Recherche  3) Garder Aperçu seulement pour tester  4) Renommer les fichiers sur disque.\nTout sous « Avancé (optionnel) » est en plus — vous pouvez l’ignorer pour des renommages simples.",
)
row(
    "t3.hint_csv",
    "Load: ; or , is read from the file. Save: separator from ⚙ Settings (; or ,).",
    "Laden: ; oder , wird aus der Datei gelesen. Speichern: Trenner aus ⚙ Einstellungen (; oder ,).",
    "Cargar: ; o , se lee del archivo. Guardar: separador desde ⚙ Ajustes (; o ,).",
    "Chargement : ; ou , lu dans le fichier. Enregistrement : séparateur des ⚙ réglages (; ou ,).",
)
row("t3.save_csv", "Save CSV", "CSV speichern", "Guardar CSV", "Enregistrer CSV")
row("t3.search_label", "Search (matching items stay visible)", "Suche (passende Einträge bleiben sichtbar)", "Búsqueda (los elementos coincidentes siguen visibles)", "Recherche (les éléments correspondants restent visibles)")
row(
    "t3.filter_placeholder",
    "path, file name, or new file name…",
    "Pfad, Dateiname oder neuer Dateiname…",
    "ruta, nombre de archivo o nuevo nombre…",
    "chemin, nom de fichier ou nouveau nom…",
)
row("t3.col.path", "Full path", "Voller Pfad", "Ruta completa", "Chemin complet")
row("t3.col.name", "Current file name", "Aktueller Dateiname", "Nombre de archivo actual", "Nom de fichier actuel")
row("t3.col.new_leaf", "New file name", "Neuer Dateiname", "Nuevo nombre de archivo", "Nouveau nom de fichier")
row("t3.selected", "Selected:", "Ausgewählt:", "Seleccionado:", "Sélection :")
row("t3.copy_folder", "Copy folder path", "Ordnerpfad kopieren", "Copiar ruta de carpeta", "Copier le chemin du dossier")
row("t3.open_explorer", "Open in Explorer", "Im Explorer öffnen", "Abrir en el Explorador", "Ouvrir dans l’Explorateur")
row(
    "t3.advanced_hint",
    "Advanced (optional): build or edit \"New file name\" before you rename on disk.",
    "Erweitert (optional): „Neuer Dateiname“ vor dem Umbenennen auf der Festplatte bearbeiten.",
    "Avanzado (opcional): crear o editar «Nuevo nombre de archivo» antes de renombrar en disco.",
    "Avancé (optionnel) : définir ou modifier « Nouveau nom de fichier » avant le renommage sur disque.",
)
row("t3.new_name_selected", "New file name (selected items)", "Neuer Dateiname (ausgewählte Einträge)", "Nuevo nombre (elementos seleccionados)", "Nouveau nom (éléments sélectionnés)")
row("t3.apply_selected", "Apply to selected items", "Auf ausgewählte Einträge anwenden", "Aplicar a elementos seleccionados", "Appliquer aux éléments sélectionnés")
row("t3.suffix_before_ext", "Suffix (before .ext)", "Suffix (vor .ext)", "Sufijo (antes de .ext)", "Suffixe (avant .ext)")
row("t3.apply_search", "Apply to search matches", "Auf Suchtreffer anwenden", "Aplicar a coincidencias de búsqueda", "Appliquer aux résultats de recherche")
row("t3.ignore_case", "Ignore capital letters (A = a)", "Groß/Klein ignorieren (A = a)", "Ignorar mayúsculas (A = a)", "Ignorer la casse (A = a)")
row("t3.fr_search", "Find/replace — search matches", "Suchen/Ersetzen — Suchtreffer", "Buscar/reemplazar — coincidencias", "Rechercher/remplacer — résultats recherche")
row("t3.fr_selected", "Find/replace — selected items", "Suchen/Ersetzen — Auswahl", "Buscar/reemplazar — selección", "Rechercher/remplacer — sélection")
row(
    "t3.fr_hint",
    "If an item already has a new file name, find/replace uses that — you can click Apply repeatedly.",
    "Wenn ein Eintrag schon einen neuen Dateinamen hat, nutzt Suchen/Ersetzen diesen — „Anwenden“ kann mehrfach geklickt werden.",
    "Si un elemento ya tiene un nombre nuevo, buscar/reemplazar usa ese — puedes pulsar Aplicar varias veces.",
    "Si un élément a déjà un nouveau nom, rechercher/remplacer part de celui-ci — vous pouvez cliquer Appliquer plusieurs fois.",
)
row("t3.limit_folder", "Limit to folder (optional)", "Auf Ordner beschränken (optional)", "Limitar a carpeta (opcional)", "Limiter au dossier (optionnel)")
row("t3.preview_only", "Preview only (no changes on disk)", "Nur Vorschau (keine Änderungen auf der Festplatte)", "Solo vista previa (sin cambios en disco)", "Aperçu seulement (aucun changement sur disque)")
row("t3.rename_disk", "Rename files on disk", "Dateien auf der Festplatte umbenennen", "Renombrar archivos en disco", "Renommer les fichiers sur disque")
row("t3.update_stash_search", "Update Stash paths (search matches)", "Stash-Pfade aktualisieren (Suchtreffer)", "Actualizar rutas Stash (coincidencias)", "Mettre à jour chemins Stash (résultats)")
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
    "t4.steps",
    "Steps (Stash not required for moving files): 1) Load CSV  2) Search  3) Set where files should go (folder below + optional Subfolder)  4) Keep Preview only checked to verify  5) Move files (search matches or selected items).",
    "Schritte (Stash nicht nötig zum Verschieben): 1) CSV laden  2) Suche  3) Ziel setzen (Ordner unten + optionaler Unterordner)  4) „Nur Vorschau“ zur Kontrolle  5) Dateien verschieben (Suchtreffer oder Auswahl).",
    "Pasos (Stash no obligatorio para mover): 1) Cargar CSV  2) Buscar  3) Definir destino (carpeta + subcarpeta opcional)  4) Vista previa para comprobar  5) Mover archivos (coincidencias o selección).",
    "Étapes (Stash non requis pour déplacer) : 1) Charger le CSV  2) Recherche  3) Définir la cible (dossier + sous-dossier optionnel)  4) Aperçu seulement pour vérifier  5) Déplacer (résultats recherche ou sélection).",
)
row(
    "t4.hint_stash",
    "Updating Stash is optional: turn on \"Update Stash paths after move\" only if the CSV has a scene_id column (from a Stash export) and you want Stash updated right away.",
    "Stash zu aktualisieren ist optional: „Stash-Pfade nach Verschieben aktualisieren“ nur einschalten, wenn die CSV eine scene_id-Spalte hat (Stash-Export) und Stash sofort angepasst werden soll.",
    "Actualizar Stash es opcional: activa «Actualizar rutas Stash tras mover» solo si el CSV tiene scene_id (export Stash) y quieres actualizar ya.",
    "Mettre à jour Stash est optionnel : activez « Mettre à jour les chemins Stash après déplacement » seulement si le CSV a scene_id (export Stash) et que vous voulez une MAJ immédiate.",
)
row(
    "t4.hint_csv",
    "Load: ; or , is read from the file. Export: separator from ⚙ Settings (; or ,).",
    "Laden: ; oder , aus der Datei. Export: Trenner aus ⚙ Einstellungen (; oder ,).",
    "Cargar: ; o , del archivo. Exportar: separador desde ⚙ Ajustes (; o ,).",
    "Chargement : ; ou , dans le fichier. Export : séparateur des ⚙ réglages (; ou ,).",
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
    "Default: every file you move is placed inside “Where to move files”, plus “Subfolder under that path” if you filled it (that folder is created if needed). The CSV path at the top is only the list — not the move target.",
    "Standard: jede verschobene Datei landet in „Wohin verschieben“, plus „Unterordner darunter“, falls ausgefüllt (Ordner wird angelegt). Der CSV-Pfad oben ist nur die Liste — kein Ziel.",
    "Por defecto: cada archivo va a «Dónde mover», más «Subcarpeta» si la rellenas (se crea si hace falta). La ruta CSV arriba es solo la lista, no el destino.",
    "Par défaut : chaque fichier va dans « Où déplacer », plus « Sous-dossier » si renseigné (créé si besoin). Le chemin CSV en haut est seulement la liste, pas la cible.",
)
row(
    "t4.per_source",
    "Instead: next to each file's current folder — ignores “Where to move files” above; each file goes to <its current folder>\\Subfolder\\",
    "Stattdessen: neben dem aktuellen Ordner jeder Datei — ignoriert „Wohin verschieben“; jede Datei nach <ihr Ordner>\\Unterordner\\",
    "En su lugar: junto a la carpeta actual de cada archivo — ignora «Dónde mover»; cada archivo a <su carpeta>\\Subcarpeta\\",
    "Sinon : à côté du dossier actuel de chaque fichier — ignore « Où déplacer » ; chaque fichier vers <son dossier>\\Sous-dossier\\",
)
row(
    "t4.tip_settings",
    "Tip: use ⚙ Settings to set URL and API for Tab 1 and Tab 4 together. GraphQL path is always from Tab 1.",
    "Tipp: ⚙ Einstellungen für URL/API von Tab 1 und Tab 4 gemeinsam. GraphQL-Pfad kommt immer aus Tab 1.",
    "Consejo: ⚙ Ajustes para URL/API de pestañas 1 y 4 juntas. La ruta GraphQL siempre es de la pestaña 1.",
    "Astuce : ⚙ réglages pour URL/API des onglets 1 et 4. Le chemin GraphQL vient toujours de l’onglet 1.",
)
row(
    "t4.preview_only",
    "Preview only (no moves, no Stash update — log what would happen)",
    "Nur Vorschau (kein Verschieben, kein Stash-Update — protokolliert geplante Aktionen)",
    "Solo vista previa (sin mover ni actualizar Stash — registra lo planeado)",
    "Aperçu seulement (pas de déplacement ni MAJ Stash — journal des actions prévues)",
)
row(
    "t4.selected_only",
    "Use selected items only (otherwise all items that match Search)",
    "Nur ausgewählte Einträge (sonst alle Suchtreffer)",
    "Solo elementos seleccionados (si no, todos los que coinciden)",
    "Seulement les éléments sélectionnés (sinon tout ce qui correspond à Recherche)",
)
row("t4.update_stash_after", "Update Stash paths after move", "Stash-Pfade nach Verschieben aktualisieren", "Actualizar rutas Stash tras mover", "Mettre à jour chemins Stash après déplacement")
row("t4.rollback", "Move file back if updating Stash fails", "Datei zurück, wenn Stash-Update fehlschlägt", "Volver a mover si falla actualización Stash", "Remettre le fichier si échec MAJ Stash")
row(
    "t4.stash_id_hint",
    "Hint: Stash updates need a scene_id value on each item (Stash export) and a running Stash server you can reach.",
    "Hinweis: Stash-Updates brauchen scene_id pro Eintrag (Stash-Export) und einen erreichbaren Stash-Server.",
    "Aviso: actualizar Stash requiere scene_id en cada elemento (export Stash) y un servidor Stash accesible.",
    "Indice : les MAJ Stash nécessitent scene_id par élément (export Stash) et un serveur Stash joignable.",
)
row("t4.move_disk", "Move files on disk", "Dateien auf Festplatte verschieben", "Mover archivos en disco", "Déplacer les fichiers sur disque")
row("t4.plan_empty", "Plan: —", "Plan: —", "Plan: —", "Plan : —")
row("t4.preview_title", "Preview (first items that match Search)", "Vorschau (erste Einträge der Suche)", "Vista previa (primeros elementos de la búsqueda)", "Aperçu (premiers éléments correspondant à Recherche)")
row("t4.refresh_preview", "Refresh preview", "Vorschau aktualisieren", "Actualizar vista previa", "Actualiser l’aperçu")

# Settings
row("settings.title", "Settings", "Einstellungen", "Ajustes", "Réglages")
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
row("settings.stash_group", "Stash (Tab 1 + Tab 4)", "Stash (Tab 1 + Tab 4)", "Stash (pestaña 1 + 4)", "Stash (onglets 1 + 4)")
row(
    "settings.stash_hint",
    "Saving applies URL and API key to both Tab 1 and Tab 4. GraphQL path is shared everywhere.",
    "Speichern übernimmt URL und API-Schlüssel für Tab 1 und Tab 4. GraphQL-Pfad ist überall gleich.",
    "Al guardar se aplican URL y clave API a pestañas 1 y 4. La ruta GraphQL es compartida.",
    "Enregistrer applique URL et clé API aux onglets 1 et 4. Le chemin GraphQL est partout le même.",
)
row("settings.graphql_path_label", "GraphQL path (empty = /graphql)", "GraphQL-Pfad (leer = /graphql)", "Ruta GraphQL (vacío = /graphql)", "Chemin GraphQL (vide = /graphql)")
row("settings.graphql_clear", "GraphQL default (clear)", "GraphQL-Standard (leeren)", "GraphQL predeterminado (borrar)", "GraphQL par défaut (effacer)")
row(
    "settings.saved_log",
    "Settings saved (appearance, column separator for CSV saves, Stash URL/API/GraphQL for all tabs).",
    "Einstellungen gespeichert (Erscheinungsbild, CSV-Trenner, Stash-URL/API/GraphQL für alle Tabs).",
    "Ajustes guardados (apariencia, separador CSV, URL/API/GraphQL Stash para todas las pestañas).",
    "Réglages enregistrés (apparence, séparateur CSV, URL/API/GraphQL Stash pour tous les onglets).",
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
row("ctx.open_in_explorer", "Open in Explorer", "Im Explorer öffnen", "Abrir en el Explorador", "Ouvrir dans l’Explorateur")

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
row("log.t2_pick_folder", "Tab 2: choose a folder to scan.\n", "Tab 2: Ordner zum Scannen wählen.\n", "Tab 2: elija carpeta para escanear.\n", "Tab 2 : choisissez un dossier à analyser.\n")
row("log.not_directory", "Not a directory: {root}\n", "Kein Ordner: {root}\n", "No es un directorio: {root}\n", "Ce n’est pas un dossier : {root}\n")
row("log.t2_scanning", "\n--- Tab 2: scanning {root} (include subfolders={sub}) ---\n", "\n--- Tab 2: Scan {root} (Unterordner={sub}) ---\n", "\n--- Tab 2: escaneando {root} (subcarpetas={sub}) ---\n", "\n--- Tab 2 : analyse {root} (sous-dossiers={sub}) ---\n")
row("log.wrote_items", "Wrote {n} item(s) to {out}\n", "{n} Eintrag/Einträge nach {out} geschrieben\n", "Escritos {n} elemento(s) en {out}\n", "{n} élément(s) écrits dans {out}\n")
row("log.tip_t3_set", "Tip: Tab 3 CSV path set to: {path}\n", "Hinweis: Tab-3-CSV-Pfad: {path}\n", "Aviso: ruta CSV pestaña 3: {path}\n", "Astuce : chemin CSV onglet 3 : {path}\n")
row("log.t1_push_fail", "Tab 1: run export first or set a valid output CSV.\n", "Tab 1: zuerst exportieren oder gültige Ausgabe-CSV setzen.\n", "Tab 1: ejecute exportación o CSV de salida válido.\n", "Tab 1 : lancez l’export ou définissez un CSV de sortie valide.\n")
row("log.t2_push_fail", "Tab 2: run a scan first or set a valid output CSV.\n", "Tab 2: zuerst scannen oder gültige Ausgabe-CSV setzen.\n", "Tab 2: ejecute escaneo o CSV de salida válido.\n", "Tab 2 : lancez l’analyse ou définissez un CSV de sortie valide.\n")
row("log.t4_suggest_no_match", "Tab 4 suggest: no items match the current search.\n", "Tab 4 Vorschlag: keine Treffer für die aktuelle Suche.\n", "Tab 4 sugerencia: ningún elemento coincide con la búsqueda.\n", "Tab 4 suggestion : aucun élément ne correspond à la recherche.\n")
row("log.t4_suggest_no_paths", "Tab 4 suggest: no usable source paths.\n", "Tab 4 Vorschlag: keine brauchbaren Quellpfade.\n", "Tab 4 sugerencia: sin rutas de origen usables.\n", "Tab 4 suggestion : pas de chemins source utilisables.\n")
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
    "log.t4_stash_path_line",
    "Path written to Stash (forward slashes, for the database): {p}/…",
    "In Stash geschriebener Pfad (Schrägstriche, für die DB): {p}/…",
    "Ruta escrita en Stash (barras, para la BD): {p}/…",
    "Chemin écrit dans Stash (slashes, pour la base) : {p}/…",
)
row(
    "log.t4_plan",
    "Plan: {run} · {source} · {place} · {stash} · {rollback}",
    "Plan: {run} · {source} · {place} · {stash} · {rollback}",
    "Plan: {run} · {source} · {place} · {stash} · {rollback}",
    "Plan : {run} · {source} · {place} · {stash} · {rollback}",
)
row("plan.run.preview", "preview only", "nur Vorschau", "solo vista previa", "aperçu seulement")
row("plan.run.real", "apply for real", "wirklich ausführen", "aplicar de verdad", "exécution réelle")
row("plan.source.selected", "selected items only", "nur Auswahl", "solo seleccionados", "sélection seulement")
row("plan.source.all_search", "all items matching Search", "alle Suchtreffer", "todos los que coinciden", "tout ce qui correspond à Recherche")
row("plan.place.next", "next to each file's folder", "neben Ordner jeder Datei", "junto a carpeta de cada archivo", "à côté du dossier de chaque fichier")
row("plan.place.one", "one destination folder", "ein Zielordner", "una carpeta de destino", "un dossier de destination")
row("plan.stash.move_update", "move files + update Stash", "verschieben + Stash aktualiser", "mover + actualizar Stash", "déplacer + MAJ Stash")
row("plan.stash.move_only", "move files only", "nur verschieben", "solo mover", "déplacement seulement")
row("plan.roll.back", "move back if Stash update fails", "zurück bei Stash-Fehler", "volver si falla Stash", "retour si échec MAJ Stash")
row("plan.roll.no", "no automatic undo", "kein automatisches Rückgängig", "sin deshacer automático", "pas d’annulation auto")
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
row("log.skip_invalid_suffix", ", skipped {n} invalid", ", {n} ungültige übersprungen", ", omitidos {n} no válidos", ", {n} invalides ignorés")
row(
    "log.cleared_new_names",
    'Cleared "New file name" on items matching Search.\n',
    "„Neuer Dateiname“ bei Suchtreffern geleert.\n",
    "Borrado «nuevo nombre» en coincidencias.\n",
    "« Nouveau nom » effacé sur les résultats de recherche.\n",
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
row("log.t3_stash_no_items", "No items matching Search to update.\n", "Keine Suchtreffer zum Aktualisieren.\n", "No hay coincidencias para actualizar.\n", "Aucun résultat de recherche à mettre à jour.\n")
row("log.t3_stash_header", "\n--- Tab 3: Stash update (search matches) ---\n", "\n--- Tab 3: Stash-Update (Suchtreffer) ---\n", "\n--- Tab 3: actualización Stash (coincidencias) ---\n", "\n--- Tab 3 : MAJ Stash (résultats recherche) ---\n")
row(
    "log.t3_stash_done",
    "\n{preview}Processed: stash updated {updated}, skipped {skipped}.\n",
    "\n{preview}Verarbeitet: Stash aktualisiert {updated}, {skipped} übersprungen.\n",
    "\n{preview}Procesado: Stash actualizado {updated}, omitidos {skipped}.\n",
    "\n{preview}Traité : Stash mis à jour {updated}, {skipped} ignorés.\n",
)
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
    "log.t4_move_stash_header",
    "\n--- Tab 4: move + stash update ({mode}) ---\n",
    "\n--- Tab 4: Verschieben + Stash-Update ({mode}) ---\n",
    "\n--- Tab 4: mover + actualizar Stash ({mode}) ---\n",
    "\n--- Tab 4 : déplacement + MAJ Stash ({mode}) ---\n",
)
row(
    "log.t4_move_stash_done",
    "\n{preview}Processed: moved {moved}, stash updated {updated}, skipped {skipped}.\n",
    "\n{preview}Verarbeitet: verschoben {moved}, Stash {updated}, übersprungen {skipped}.\n",
    "\n{preview}Procesado: movidos {moved}, Stash {updated}, omitidos {skipped}.\n",
    "\n{preview}Traité : déplacés {moved}, Stash {updated}, ignorés {skipped}.\n",
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
row(
    "log.t4_stash_no_scene",
    "Tab 4: Update Stash is on, but none of the target items have a scene_id value.\nLoad a CSV exported from Stash (it includes scene_id), or turn off \"Update Stash paths after move\".\n",
    "Tab 4: Stash-Update ist an, aber kein Zieleintrag hat scene_id.\nCSV aus Stash exportieren (enthält scene_id) oder „Stash nach Verschieben“ aus.\n",
    "Tab 4: actualizar Stash activado, pero ningún elemento tiene scene_id.\nCargue CSV exportado de Stash o desactive actualizar rutas.\n",
    "Tab 4 : MAJ Stash activée, mais aucun élément cible n’a de scene_id.\nChargez un CSV exporté depuis Stash ou désactivez la MAJ des chemins.\n",
)
row(
    "log.t4_stash_partial",
    "Tab 4 note: Update Stash is on. {with_scene} item(s) have scene_id; {missing} item(s) have no scene_id and will be skipped.\n",
    "Tab 4: Stash-Update an. {with_scene} mit scene_id; {missing} ohne scene_id werden übersprungen.\n",
    "Tab 4: {with_scene} con scene_id; {missing} sin scene_id se omitirán.\n",
    "Tab 4 : {with_scene} avec scene_id ; {missing} sans scene_id seront ignorés.\n",
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
    "log.probe_stash",
    "\n--- Check path-update support ({url}{gql}) ---\n",
    "\n--- Pfad-Update prüfen ({url}{gql}) ---\n",
    "\n--- Comprobar actualización de rutas ({url}{gql}) ---\n",
    "\n--- Vérification MAJ chemins ({url}{gql}) ---\n",
)
row("log.compat_prefix", "COMPATIBLE: ", "KOMPATIBEL: ", "COMPATIBLE: ", "COMPATIBLE : ")
row("log.check_prefix", "CHECK: ", "PRÜFUNG: ", "REVISAR: ", "VÉRIF. : ")

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
