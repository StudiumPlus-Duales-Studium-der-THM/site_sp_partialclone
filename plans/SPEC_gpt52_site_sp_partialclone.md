# Spezifikation: Partieller Website-Klon + Viewer (studiumplus.de)

## Kontext & Ziel
Dieses Repository dient als **partieller Klon** ausgewählter Seiten und Unterseiten von https://studiumplus.de, um Anpassungen zu testen und Demos zu erstellen. (Siehe Repo-README.)  
Der Klon soll **nicht** die ganze Website spiegeln, sondern gezielte Teilbereiche.

## Muss-Ziele (funktional)
1. **Teilbereiche klonen (Startumfang)**
   - Root A: https://studiumplus.de/duales-studium/vor-dem-studium/studienangebot/
   - Root B: https://studiumplus.de/studiengaenge/betriebswirtschaft/
   - Root C: https://studiumplus.de/duales-studium/vor-dem-studium/freie-studienplaetze/
   - Root D: https://studiumplus.de/connect/
   - Root E: https://studiumplus.de/ueber-uns/downloads/
   - Root F: https://studiumplus.de/duales-studium/im-studium/infos-fuer-studierende/praxis-im-unternehmen/
   - Root G: https://studiumplus.de/ueber-uns/campus-team/
   - Root H: https://studiumplus.de/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/

   - Für jeden Root sollen passende **Unterseiten** mit geklont werden (Scope-Regeln siehe unten).

2. **Strukturabbildung 1:1**
   - Die URL-Pfade werden im Repo als Ordnerstruktur gespiegelt.
   - Beispiel:
     - URL: `/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/`
     - Repo-Pfad: `duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/index.html`

3. **Vollständigkeit der Darstellung**
   - Jede geklonte Seite soll **offline** auf einem Webserver aus dem Repo heraus funktionieren:
     - HTML
     - CSS
     - JS
     - Bilder (auch lazy-loaded)
     - Fonts
     - sonstige Ressourcen, die die Seite benötigt (z. B. SVG, JSON, PDF sofern verlinkt und im Scope)
   - Ressourcen sollen lokal gespeichert und die Referenzen so umgeschrieben werden, dass sie lokal laden.

4. **Indexseite (Übersicht)**
   - Es muss eine zentrale Indexseite geben (z. B. `/index.html` oder `/viewer/index.html`),
     die zeigt:
     - Welche Root-Bereiche konfiguriert sind
     - Welche Seiten bereits geklont wurden
     - Status (OK/Fehler), Zeitstempel des letzten Klons
     - Link zum lokalen Klon (und optional Link zur Original-URL)

5. **Registry/Manifest**
   - Es muss eine maschinenlesbare Registry geben, die den Clone-Zustand abbildet
     (z. B. `registry.json` oder `registry.sqlite`).
   - Diese Registry ist die Grundlage für die Indexseite.
   - Minimalfelder:
     - `roots[]`: Liste der Root-Bereiche (Start-URLs)
     - `pages[url]`: pro Seite: localPath, lastFetchedAt, httpStatus, contentHash, outLinks[], assets[]
     - `assets[url]`: pro Asset: localPath, contentType, size, lastFetchedAt, hash
     - `errors[]`: url, type, message, timestamp

6. **Viewer-Rahmen (“Hülle”) mit Rücksprung**
   - Wenn man lokale geklonte Seiten aufruft, soll optional ein Rahmen/Overlay existieren mit:
     - “Zurück zum Index”
     - “Original öffnen”
     - Toggle “Rahmen ausblenden”
   - Der Rahmen muss deaktivierbar sein:
     - per Query-Parameter `?plain=1` oder
     - per separatem Pfad-Schema (z. B. `/plain/...` ohne Rahmen) oder
     - per lokalem UI-Button, der sich merkt (localStorage).

## Soll-Ziele (nice to have)
- Inkrementelles Update: Nur Seiten/Assets neu laden, wenn Hash/ETag/Last-Modified sich geändert hat.
- CLI-Optionen: `--roots`, `--maxDepth`, `--concurrency`, `--rateLimit`, `--dryRun`.
- Erkennung & Download von Background-Images in CSS (`url(...)`).
- Report (Markdown/HTML) über Änderungen seit letztem Lauf.

## Nicht-Ziele
- Kein vollständiger Mirror der gesamten Domain.
- Kein “Crawler ohne Grenzen”.
- Keine serverseitige Re-Implementierung von WordPress.

---

## Scope-Regeln (entscheidend)
### Domain
- Erlaubt ist nur `https://studiumplus.de` (und ggf. Subdomains nur, wenn explizit whitelisted).
- Externe Links (thm.de, moodle.thm.de, terminland.de etc.) werden **nicht** geklont.
  - Sie bleiben als externe Links erhalten oder werden optional im UI als “extern” markiert.

### Welche Unterseiten gehören dazu?
Für jeden Root-Bereich gilt:
- Nur URLs, deren Pfad **mit dem Root-Pfad beginnt**, gehören in den Clone.
  - Root A: `/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/…`
  - Root B: `/studiengaenge/betriebswirtschaft/…`
- Zusätzlich dürfen Assets von überall auf `studiumplus.de` geladen werden,
  wenn sie von geklonten Seiten referenziert werden (CSS/JS/Bilder/Fonts).

### Tiefe
- Standard: keine künstliche maxDepth, sondern “prefix-based” wie oben.
- Optional: `--maxPages` als Sicherheitsgurt.

---

## Technischer Ansatz (empfohlen)
### Variante (präferiert): Headless Browser Crawler (Playwright)
Implementiere einen Crawler, der:
1. Start-URLs lädt
2. Alle Seiten im Scope besucht (BFS/Queue)
3. Pro Seite:
   - Finales DOM/HTML nach Laden speichern
   - Alle Netzwerk-Requests (document, script, stylesheet, image, font, xhr/fetch) mitschneiden
   - Responses in Dateien schreiben (inkl. binärer Inhalte)
4. Danach:
   - HTML/CSS so umschreiben, dass Links/Assets lokal referenziert werden
   - Registry aktualisieren

### Rewriting-Regeln
- Jede Seite wird als `.../index.html` gespeichert.
- Links:
  - Interne, im Scope: auf relative lokale Pfade umschreiben (z. B. `/studiengaenge/.../` → `../../studiengaenge/.../index.html`)
  - Interne, aber **nicht** im Scope: als absolute `https://studiumplus.de/...` belassen oder als “extern” markieren.
  - Extern: unverändert lassen.
- Assets:
  - Wenn im HTML absolute URLs vorkommen (`https://studiumplus.de/wp-content/...`), lokal speichern und Referenz ersetzen.
  - Wenn Query-Strings existieren (`style.css?ver=123`), lokal speichern mit stabiler Namensstrategie:
    - z. B. Hash in Dateiname oder Query normalisieren.

### Speicherlayout im Repo (Vorschlag)
- `duales-studium/.../index.html` (geklarte Seiten)
- `studiengaenge/.../index.html`
- `_assets/` für zentral gespeicherte Assets (optional) oder originalgetreue Pfade:
  - Option 1 (originalgetreu): `wp-content/...` exakt spiegeln
  - Option 2 (zentral): `_assets/<hash>.<ext>` plus Mapping in Registry
- `viewer/` (Index + Rahmen-UI, falls getrennt gehalten)
- `registry.json` (oder `registry.sqlite`)

**Empfehlung:** Assets möglichst **in originaler Pfadstruktur** speichern (z. B. `wp-content/...`),
weil das Rewriting dann einfacher und verständlicher bleibt.

---

## CLI / Bedienung (Muss)
Stelle ein Kommando bereit (Node oder Python), z. B.:
- `npm run clone` oder `python -m clone`
Parameter:
- `--config clone.config.json`
- `--roots <url1,url2,...>` (optional override)
- `--concurrency 2..6`
- `--rateLimitMs 200..1000`
- `--userAgent "site_sp_partialclone-bot/1.0"`
- `--outputDir .`

Die Default-Konfiguration enthält die zwei Start-Roots.

---

## Indexseite / Viewer (Muss)
### Anforderungen
- Zeige Roots als Karten/Liste:
  - Titel (aus URL oder aus konfigurierbarem Label)
  - Anzahl geklonter Seiten
  - letzter Lauf
  - Status
  - Button: “Öffnen (lokal)”
  - Button: “Original (extern)”
- Zeige optional Liste der geklonten Seiten pro Root (aufklappbar)
- Link “Rebuild Index” (kann einfach: Index wird beim Clone-Lauf neu generiert)

### Rahmen/Overlay
- Technisch z. B. per JS-Injection beim Speichern:
  - In jedes gespeicherte HTML einen kleinen Script/CSS-Block einfügen,
    der oben eine Leiste rendert (Index/Original/Toggle).
- Toggle “plain”:
  - Wenn URL `?plain=1`, wird Leiste nicht angezeigt
  - Zusätzlich speichert Toggle-Status in `localStorage` (optional)

---

## Robustheit / Qualität
- Respektiere `robots.txt` und setze konservatives Rate-Limit.
- Timeouts & Retries:
  - 2 Retries bei transienten Fehlern (5xx, Timeout)
- Logging:
  - Konsolen-Ausgabe + `logs/clone.log`
- Fehler sollen in `registry` landen, ohne den Gesamtprozess abzubrechen.

---

## Akzeptanzkriterien (Tests)
1. Nach `clone` existieren:
   - `duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/index.html`
   - `studiengaenge/betriebswirtschaft/index.html`
   - zugehörige Assets lokal
   - `registry.json`
   - Indexseite (z. B. `index.html`)
2. Lokales Hosting (z. B. `python -m http.server`) zeigt:
   - Indexseite funktioniert
   - Von Index aus kann man beide Bereiche öffnen
   - Seiten laden ohne kaputte Bild-URLs (Network-Tab: nur localhost)
3. Rahmen lässt sich ausblenden (plain-Modus) und Index ist erreichbar.

---

## Deliverables (vom Agenten zu erstellen)
- Quellcode für Crawler + Rewriter + Index-Generator
- `clone.config.json` (Roots + Einstellungen)
- `registry.json` (oder alternative Registry)
- `index.html` (Viewer)
- Kurze `DEVELOPMENT.md` mit:
  - Setup
  - Run clone
  - Run local server
  - How to add new root