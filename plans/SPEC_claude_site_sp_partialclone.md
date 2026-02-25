# Spezifikation: Partieller Website-Klon – studiumplus.de

## Kontext

Repository: `StudiumPlus-Duales-Studium-der-THM/site_sp_partialclone`  
Ziel-Website: `https://studiumplus.de`

Dieses Dokument ist eine Spezifikation für einen Programmieragenten. Der Agent soll gezielt Teilbereiche von studiumplus.de klonen, lokal in einem Git-Repository ablegen und eine Rahmenanwendung erstellen, über die die geklonten Bereiche navigierbar und darstellbar sind.

---

## 1. Anforderungen

### 1.1 Klonen von Teilbereichen

- Zu klonende Startseiten (initiale Bereiche):
   - Root A: https://studiumplus.de/duales-studium/vor-dem-studium/studienangebot/
   - Root B: https://studiumplus.de/studiengaenge/betriebswirtschaft/
   - Root C: https://studiumplus.de/duales-studium/vor-dem-studium/freie-studienplaetze/
   - Root D: https://studiumplus.de/connect/
   - Root E: https://studiumplus.de/ueber-uns/downloads/
   - Root F: https://studiumplus.de/duales-studium/im-studium/infos-fuer-studierende/praxis-im-unternehmen/
   - Root G: https://studiumplus.de/ueber-uns/campus-team/
   - Root H: https://studiumplus.de/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/

- **Rekursives Klonen:** Jede angegebene URL wird inklusive aller Unterseiten im selben URL-Pfadbereich geklont. Beispiel: Alle Seiten unter `/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/...` werden erfasst.
- **Verzeichnisstruktur:** Die URL-Pfade werden 1:1 als Verzeichnisse im Repository abgebildet.  
  Beispiel: `https://studiumplus.de/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/` → `duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/`
- **HTML-Seiten:** Jede geklonte Seite wird als `index.html` im entsprechenden Verzeichnis gespeichert.
- **Bilder:** Alle auf den Seiten referenzierten Bilder werden lokal heruntergeladen und im Repository gespeichert. Die Bild-Pfade in den HTML-Dateien werden entsprechend umgeschrieben.
- **Externe Ressourcen (Fonts, CDN-Scripts, CSS von externen Quellen):** Werden **nicht** lokal gespeichert, sondern bleiben als externe Referenzen bestehen. Der Klon benötigt daher eine Internetverbindung zur vollständigen Darstellung.
- **Interne CSS/JS der Originalseite:** Werden lokal gespeichert, soweit für die Darstellung der geklonten Seiten notwendig.

### 1.2 Registry (Manifest)

Eine maschinenlesbare Datei (`registry.json`) im Root des Repositories hält fest, welche Bereiche geklont wurden. Struktur:

```json
{
  "source": "https://studiumplus.de",
  "last_updated": "2025-02-25T12:00:00Z",
  "areas": [
    {
      "id": "mein-weg-zu-studiumplus",
      "label": "Mein Weg zu StudiumPlus",
      "source_url": "https://studiumplus.de/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/",
      "local_path": "duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/",
      "thumbnail": "thumbnails/mein-weg-zu-studiumplus.png",
      "cloned_at": "2025-02-25T12:00:00Z",
      "pages_count": 5,
      "pages": [
        {
          "source_url": "https://studiumplus.de/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/",
          "local_path": "duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/index.html",
          "title": "Mein Weg zu StudiumPlus"
        }
      ]
    }
  ]
}
```

### 1.3 Index-Seite

- Eine `index.html` im Root des Repositories dient als Einstiegspunkt.
- Sie liest die `registry.json` per `fetch()` und zeigt eine Übersicht aller geklonten Bereiche.
- Pro Bereich: Thumbnail-Vorschaubild, Name, Quell-URL, Klondatum, Anzahl der Seiten, Link zum Viewer.
- Die Index-Seite soll ansprechend gestaltet sein (eigenes, schlichtes CSS – unabhängig vom studiumplus.de-Design).
- Die Thumbnails werden als Karten dargestellt (Card-Layout).

### 1.4 Rahmenanwendung (Viewer-SPA)

Die Rahmenanwendung ist eine **Vanilla-JS Single Page Application** (`viewer.html`), die geklonte Seiten in einem **iframe** als Rendering-Container darstellt. Der iframe dient der CSS-Isolation – das Styling der geklonten Originalseite kann nicht mit der Rahmenanwendung kollidieren und umgekehrt.

#### Aufbau

- **Obere Navigationsleiste** (Teil der SPA, außerhalb des iframe):
  - Link zurück zur Index-Seite
  - Anzeige des aktuellen Bereichsnamens und der Original-Quell-URL
  - Button „Rahmen ausblenden" → blendet die Navigationsleiste aus
- **Hauptbereich:** `<iframe>` zeigt die geklonte Seite an
- **Ausblendmodus:** Navigationsleiste verschwindet, iframe wird vollflächig. Ein diskreter, schwebender Button (z.B. halbtransparent unten rechts) erlaubt das Wiedereinblenden.

#### Navigation im iframe

- Klicks auf Links innerhalb des geklonten Bereichs funktionieren normal im iframe
- Die SPA überwacht die iframe-URL (soweit Same-Origin es erlaubt) und aktualisiert ggf. die Navigationsleiste
- Links, die aus dem geklonten Bereich herausführen, sollen die Original-URL auf studiumplus.de in einem neuen Tab öffnen

#### Routing

Hash-basiertes Routing, damit kein Server-seitiges Routing nötig ist:

```
viewer.html#duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/
```

Die SPA liest den Hash, lädt die `registry.json`, ermittelt den Bereich und setzt die iframe-`src` entsprechend.

### 1.5 Repository-Struktur

```
site_sp_partialclone/
├── README.md                          # Projektbeschreibung
├── registry.json                      # Manifest der geklonten Bereiche
├── index.html                         # Übersichts-/Einstiegsseite
├── viewer.html                        # Rahmenanwendung (Viewer-SPA)
├── assets/                            # Assets der Rahmenanwendung
│   └── app.css
├── thumbnails/                        # Screenshots der geklonten Startseiten
│   ├── mein-weg-zu-studiumplus.png
│   └── betriebswirtschaft.png
├── duales-studium/                    # Geklonte Bereiche (URL-Struktur)
│   └── vor-dem-studium/
│       └── mein-weg-zu-studiumplus/
│           ├── index.html
│           └── _assets/               # Lokale Bilder dieser Seite
│               ├── bild1.jpg
│               └── bild2.png
├── studiengaenge/
│   └── betriebswirtschaft/
│       ├── index.html
│       └── _assets/
│           └── ...
└── scripts/                           # Klon-Skript und Hilfsdateien
    ├── clone.py                       # Hauptskript (Playwright-basiert)
    └── requirements.txt               # Python-Abhängigkeiten
```

**Hinweis zu `_assets/`:** Bilder werden in einem `_assets/`-Unterverzeichnis pro geklonter Seite gespeichert. Der Unterstrich verhindert Kollisionen mit tatsächlichen URL-Pfaden.

---

## 2. Klon-Skript (Playwright-basiert)

### 2.1 Warum Playwright

Das Klon-Skript nutzt **Playwright** (Python) statt einfacher HTTP-Requests, weil:

- Seiten vollständig gerendert werden (inkl. JavaScript-generierter Inhalte, Lazy-Loaded-Bilder, dynamischer Menüs)
- Consent-Banner/Cookie-Dialoge behandelt werden können
- Screenshots für Thumbnails erstellt werden können
- Das Ergebnis dem entspricht, was ein Nutzer tatsächlich im Browser sieht

### 2.2 Abhängigkeiten

`scripts/requirements.txt`:
```
playwright>=1.40
beautifulsoup4>=4.12
lxml>=5.0
```

Setup:
```bash
pip install -r scripts/requirements.txt
playwright install chromium
```

### 2.3 Aufruf

```bash
# Einen Bereich klonen
python scripts/clone.py https://studiumplus.de/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/

# Mehrere Bereiche klonen
python scripts/clone.py \
  https://studiumplus.de/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/ \
  https://studiumplus.de/studiengaenge/betriebswirtschaft/

# Optionen
python scripts/clone.py --max-depth 5 --delay 1.0 --output-dir . <URL>
```

### 2.4 Funktionsweise des Skripts

1. **Startseite laden:** Playwright öffnet die URL, wartet auf vollständiges Rendering (`networkidle`), behandelt ggf. Cookie-Banner.
2. **Links extrahieren:** Alle internen Links auf der Seite finden, die innerhalb des URL-Prefix liegen.
3. **Rekursiv crawlen:** Gefundene Links abarbeiten (Breadth-First), dabei nur URLs verfolgen, deren Pfad mit dem Startpfad beginnt (Prefix-Match).
4. **Pro Seite:**
   - Gerenderten HTML-Quelltext speichern (nach JS-Ausführung, via `page.content()`)
   - Bilder von `studiumplus.de` herunterladen → in `_assets/` ablegen
   - Bild-Pfade im HTML umschreiben auf lokale `_assets/`-Pfade
   - Interne CSS/JS-Dateien der Originalseite lokal speichern (soweit nötig)
   - Links innerhalb des geklonten Bereichs auf lokale Pfade umschreiben
   - Links zu nicht-geklonten Bereichen auf die Original-URL belassen
   - HTML-Kommentar einfügen: `<!-- Cloned from: {source_url} at {timestamp} -->`
5. **Screenshot erstellen:** Für die Startseite jedes Bereichs ein Thumbnail (1280×800 Viewport, als PNG) in `thumbnails/` speichern.
6. **Registry aktualisieren:** `registry.json` mit den neuen/aktualisierten Bereichen befüllen.

### 2.5 Abgrenzung beim Crawling

- Nur Seiten klonen, deren URL-Pfad **mit dem Startpfad beginnt** (Prefix-Match)
- Links zu anderen Bereichen der Website oder externen Seiten werden **nicht** verfolgt
- Maximale Crawl-Tiefe: konfigurierbar (Default: 5 Ebenen)
- Verzögerung zwischen Seitenaufrufen: konfigurierbar (Default: 1 Sekunde), um den Server nicht zu überlasten

### 2.6 Bild-Handling

- Bilder von `studiumplus.de` → lokal speichern in `_assets/` des jeweiligen Verzeichnisses
- Bilder von externen Domains (CDNs etc.) → externe URL beibehalten
- Unterstützte Formate: JPG, PNG, SVG, WebP, GIF
- Dateinamen aus der Original-URL ableiten; bei Duplikaten nummerieren
- Lazy-Loaded-Bilder (`data-src`, `loading="lazy"` etc.) ebenfalls erfassen, da Playwright die Seite vollständig rendert

### 2.7 CSS/JS-Handling

- CSS-Dateien, die von `studiumplus.de` geladen werden, lokal speichern in einem gemeinsamen `_shared_assets/`-Verzeichnis (da sie oft seitenübergreifend genutzt werden)
- JS-Dateien der Originalseite lokal speichern, soweit sie für die Darstellung relevant sind
- Externe CSS/JS (Google Fonts, CDN-Libraries) bleiben als externe Referenzen
- Pfade in den HTML-Dateien entsprechend umschreiben

### 2.8 Fehlerbehandlung

- HTTP-Fehler (404, 500 etc.) loggen und Seite überspringen
- Timeouts loggen und Seite überspringen
- Fehlerhafte Bilder loggen, Platzhalter-Referenz beibehalten
- Log-Datei: `scripts/clone.log` mit Timestamp, URL und Fehlerbeschreibung
- Das Skript soll idempotent sein: Erneutes Ausführen des Skripts für einen bereits geklonten Bereich soll diesen aktualisieren, nicht duplizieren

---

## 3. Technische Details der Rahmenanwendung

### 3.1 Architektur

Die Rahmenanwendung besteht aus zwei HTML-Dateien, die ohne Build-Prozess, ohne Framework und ohne Server-seitige Logik funktionieren:

| Datei | Zweck |
|-------|-------|
| `index.html` | Übersichtsseite mit Karten-Layout aller geklonten Bereiche |
| `viewer.html` | SPA mit Navigationsleiste + iframe für die Darstellung geklonter Seiten |

Beide laden `registry.json` per `fetch()` und generieren die UI dynamisch.

### 3.2 index.html – Übersichtsseite

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   StudiumPlus – Partieller Website-Klon                     │
│   Übersicht der geklonten Bereiche                          │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  [Thumbnail]     │  │  [Thumbnail]     │                 │
│  │                  │  │                  │                 │
│  │  Mein Weg zu     │  │  Betriebswirt-   │                 │
│  │  StudiumPlus     │  │  schaft          │                 │
│  │                  │  │                  │                 │
│  │  5 Seiten        │  │  8 Seiten        │                 │
│  │  Geklont: ...    │  │  Geklont: ...    │                 │
│  │  [Anzeigen]      │  │  [Anzeigen]      │                 │
│  └──────────────────┘  └──────────────────┘                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

- Karten-Layout (CSS Grid oder Flexbox)
- Jede Karte zeigt: Thumbnail, Bereichsname, Seitenanzahl, Klondatum
- Klick auf eine Karte öffnet `viewer.html#<local_path>`
- Schlichtes, eigenständiges Design (nicht das studiumplus.de-Design)

### 3.3 viewer.html – Viewer-SPA

```
┌─────────────────────────────────────────────────────────────┐
│  [← Übersicht]   Mein Weg zu StudiumPlus                    │
│  Quelle: studiumplus.de/...               [Rahmen ausblenden]│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                      <iframe>                               │
│               (geklonte Seite wird hier                     │
│                 angezeigt, volle Breite                     │
│                 und Höhe)                                   │
│                                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Bei ausgeblendetem Rahmen:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              (geklonte Seite vollflächig)                    │
│                                                             │
│                                                             │
│                                                    [≡]      │
│                                         (schwebender Button) │
└─────────────────────────────────────────────────────────────┘
```

#### Verhalten:

- **Hash-Routing:** `viewer.html#duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/` → SPA setzt iframe-src auf den lokalen Pfad
- **Navigationsleiste:** Zeigt Bereichsname (aus registry.json), Link zur Original-URL, Button zum Ausblenden
- **Rahmen-Toggle:** 
  - „Rahmen ausblenden" → Navigationsleiste verschwindet, iframe wird vollflächig, schwebender halbtransparenter Button erscheint (unten rechts)
  - Klick auf schwebenden Button → Navigationsleiste erscheint wieder
- **iframe-Überwachung:** SPA prüft periodisch oder per Event, welche Seite im iframe geladen ist (Same-Origin), und aktualisiert ggf. die Navigationsleiste

### 3.4 Responsive Design

- Desktop und Tablet: vollständig unterstützt
- Mobile: nice-to-have, nicht zwingend erforderlich

---

## 4. Arbeitsschritte für den Programmieragenten

### Phase 1: Klon-Infrastruktur

1. Klon-Skript `scripts/clone.py` erstellen (Playwright + BeautifulSoup)
2. `scripts/requirements.txt` bereitstellen
3. Registry-Management implementieren (`registry.json` lesen/schreiben)
4. Thumbnail-Generierung implementieren
5. Testen mit der ersten URL: `https://studiumplus.de/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/`

### Phase 2: Rahmenanwendung

6. `index.html` erstellen (liest `registry.json`, Karten-Layout mit Thumbnails)
7. `viewer.html` erstellen (SPA mit iframe, Navigationsleiste, Hash-Routing)
8. `assets/app.css` erstellen (schlichtes, eigenständiges Design)
9. Rahmen-Toggle (Ausblenden/Einblenden) implementieren

### Phase 3: Vollständiger Klon

10. Beide Bereiche klonen:
    - `https://studiumplus.de/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/`
    - `https://studiumplus.de/studiengaenge/betriebswirtschaft/`
11. `registry.json` befüllen, Thumbnails generieren
12. Gesamttest: Index → Viewer → Navigation im iframe → Rahmen-Toggle → Zurück zur Übersicht

### Phase 4: Dokumentation

13. `README.md` aktualisieren mit:
    - Projektbeschreibung und Architekturübersicht
    - Setup-Anleitung (Python, Playwright installieren)
    - Anleitung zum Klonen neuer Bereiche (Skript-Aufruf)
    - Anleitung zum Starten eines lokalen Webservers (`python -m http.server`)
    - Erklärung der Verzeichnisstruktur

---

## 5. Qualitätskriterien

- [ ] Geklonte Seiten sehen visuell identisch zum Original aus (bei bestehender Internetverbindung für externe Ressourcen)
- [ ] Alle Bilder von studiumplus.de innerhalb geklonter Seiten werden korrekt lokal angezeigt
- [ ] Lazy-Loaded-Bilder und JS-generierte Inhalte sind im Klon enthalten
- [ ] Thumbnails werden für jeden geklonten Bereich generiert und in der Übersicht angezeigt
- [ ] Die Index-Seite zeigt alle geklonten Bereiche korrekt als Karten an
- [ ] Die Viewer-SPA stellt geklonte Seiten im iframe dar mit funktionierender Navigationsleiste
- [ ] Der Rahmen lässt sich ein- und ausblenden (Toggle-Button)
- [ ] Hash-Routing funktioniert: Direktlinks auf `viewer.html#<pfad>` laden den richtigen Bereich
- [ ] Das Klon-Skript ist idempotent und kann erneut ausgeführt werden
- [ ] Die `registry.json` ist korrekt und aktuell nach jedem Klon-Durchlauf
- [ ] Das Repository kann mit `python -m http.server` gestartet und vollständig genutzt werden
- [ ] Fehler beim Crawling werden geloggt und führen nicht zum Abbruch des gesamten Skripts

---

## 6. Hinweise für den Agenten

- **Kein Build-Prozess:** Die Rahmenanwendung muss ohne npm, webpack o.ä. funktionieren. Reines HTML/CSS/JS.
- **Kein Frontend-Framework:** Kein React, Vue, Angular etc. Vanilla JS.
- **Python + Playwright für das Klon-Skript:** Abhängigkeiten in `requirements.txt`. Setup inkl. `playwright install chromium`.
- **Encoding:** Alle Dateien in UTF-8.
- **Git-freundlich:** Bilder in angemessener Qualität. Thumbnails komprimieren (PNG, max. 200KB pro Thumbnail).
- **Robustheit:** Das Klon-Skript soll mit Fehlern umgehen können (404, Timeouts, fehlerhafte Links) und diese loggen.
- **Rate-Limiting:** Zwischen Seitenaufrufen eine konfigurierbare Pause einlegen (Default: 1 Sekunde).
- **Cookie-Banner:** Playwright soll nach dem Laden einer Seite prüfen, ob ein Cookie-/Consent-Banner sichtbar ist, und diesen ggf. schließen (Reject/Accept-Button klicken), bevor der Seiteninhalt und Screenshot erfasst werden.
- **Idempotenz:** Erneutes Ausführen des Skripts für einen bereits geklonten Bereich soll diesen aktualisieren, nicht duplizieren.
