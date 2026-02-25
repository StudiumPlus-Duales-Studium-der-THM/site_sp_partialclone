# site_sp_partialclone

**Kurzbeschreibung:** Partieller Klon ausgewählter Seiten und Unterseiten von studiumplus.de – nicht die gesamte Website, sondern gezielt besonders relevante Bereiche. Dient zum Verproben von Anpassungen und zu Demo-Zwecken.

## Ziel

Dieses Repository enthält einen partiellen Klon der Website [studiumplus.de](https://www.studiumplus.de). Es werden nicht alle Seiten der Website gespiegelt, sondern nur bestimmte Bereiche, die von besonderer Bedeutung sind – inklusive der jeweiligen Unterseiten.

## Zweck

- **Anpassungen verproben:** Änderungen an der Website können in diesem Repository getestet werden, ohne die Live-Seite zu beeinflussen.
- **Demo-Zwecke:** Der Klon dient als Grundlage für Präsentationen und Demonstrationen.

## Architekturübersicht

Das Projekt besteht aus drei Teilen:

1. **Klon-Skript** (`scripts/clone.py`) – Playwright-basiertes Python-Skript, das Seiten rendert, Screenshots erstellt, Bilder/CSS/JS herunterlädt und die Registry aktualisiert.
2. **Index-Seite** (`index.html`) – Übersichtsseite mit Karten-Layout, die alle geklonten Bereiche aus `registry.json` anzeigt.
3. **Viewer-SPA** (`viewer.html`) – Single Page Application mit iframe, Navigationsleiste und Hash-Routing zur Darstellung geklonter Seiten.

Alle Frontend-Dateien sind reines HTML/CSS/JS ohne Build-Prozess oder Framework.

## Setup

### Voraussetzungen

- Python 3.10+
- pip

### Installation

```bash
# Abhängigkeiten installieren
pip install -r scripts/requirements.txt

# Playwright-Browser installieren
playwright install chromium
```

## Bereiche klonen

```bash
# Einen Bereich klonen
python scripts/clone.py https://studiumplus.de/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/

# Mehrere Bereiche klonen
python scripts/clone.py \
  https://studiumplus.de/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/ \
  https://studiumplus.de/studiengaenge/betriebswirtschaft/

# Mit Optionen
python scripts/clone.py --max-depth 5 --delay 1.0 --output-dir . <URL>
```

### Zu klonende Bereiche (Übersicht)

| Bereich | URL |
|---------|-----|
| Studienangebot | `https://studiumplus.de/duales-studium/vor-dem-studium/studienangebot/` |
| Betriebswirtschaft | `https://studiumplus.de/studiengaenge/betriebswirtschaft/` |
| Freie Studienplätze | `https://studiumplus.de/duales-studium/vor-dem-studium/freie-studienplaetze/` |
| Connect | `https://studiumplus.de/connect/` |
| Downloads | `https://studiumplus.de/ueber-uns/downloads/` |
| Praxis im Unternehmen | `https://studiumplus.de/duales-studium/im-studium/infos-fuer-studierende/praxis-im-unternehmen/` |
| Campus-Team | `https://studiumplus.de/ueber-uns/campus-team/` |
| Mein Weg zu StudiumPlus | `https://studiumplus.de/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/` |

## Lokalen Webserver starten

Die geklonten Seiten und die Rahmenanwendung benötigen einen HTTP-Server (wegen `fetch()` für `registry.json`):

```bash
# Im Repository-Root ausführen:
python -m http.server 8000
```

Dann im Browser öffnen: [http://localhost:8000](http://localhost:8000)

## Verzeichnisstruktur

```
site_sp_partialclone/
├── README.md                          # Diese Datei
├── registry.json                      # Manifest der geklonten Bereiche
├── index.html                         # Übersichts-/Einstiegsseite
├── viewer.html                        # Rahmenanwendung (Viewer-SPA)
├── assets/                            # Assets der Rahmenanwendung
│   └── app.css
├── thumbnails/                        # Screenshots der geklonten Startseiten
│   └── *.png
├── _shared_assets/                    # Gemeinsame CSS/JS der Originalseite
│   └── *.css / *.js
├── duales-studium/                    # Geklonte Bereiche (URL-Struktur)
│   └── vor-dem-studium/
│       └── mein-weg-zu-studiumplus/
│           ├── index.html
│           └── _assets/               # Lokale Bilder dieser Seite
│               └── *.jpg / *.png
├── studiengaenge/
│   └── betriebswirtschaft/
│       ├── index.html
│       └── _assets/
│           └── ...
└── scripts/                           # Klon-Skript und Hilfsdateien
    ├── clone.py                       # Hauptskript (Playwright-basiert)
    └── requirements.txt               # Python-Abhängigkeiten
```

## Hinweise

- **Internetverbindung erforderlich:** Externe Ressourcen (Fonts, CDN-Scripts) werden nicht lokal gespeichert. Für die vollständige Darstellung ist eine Internetverbindung nötig.
- **Idempotenz:** Das Klon-Skript kann wiederholt ausgeführt werden. Bereits geklonte Bereiche werden aktualisiert, nicht dupliziert.
- **Fehlerbehandlung:** HTTP-Fehler, Timeouts und fehlerhafte Bilder werden in `scripts/clone.log` protokolliert und führen nicht zum Abbruch.
- Dies ist kein vollständiger Klon der Website studiumplus.de. Es handelt sich um eine gezielte Auswahl relevanter Bereiche.
