# site_sp_partialclone

Partieller Klon ausgewählter Bereiche von [studiumplus.de](https://studiumplus.de) inklusive Viewer-Rahmenanwendung (Vanilla JS).

## Architektur

- `scripts/clone.py`: Playwright-basierter Bereichs-Klon (rekursiv im URL-Prefix)
- `registry.json`: Manifest der geklonten Bereiche
- `index.html`: Karten-Übersicht aller Bereiche
- `viewer.html`: SPA mit Navigationsleiste + `iframe` für isolierte Darstellung
- `assets/app.css`: Eigenes Styling für Übersicht und Viewer

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
playwright install chromium
```

## Bereiche klonen

Einzelner Bereich:

```bash
python scripts/clone.py https://studiumplus.de/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/
```

Mehrere Bereiche:

```bash
python scripts/clone.py \
  https://studiumplus.de/duales-studium/vor-dem-studium/studienangebot/ \
  https://studiumplus.de/studiengaenge/betriebswirtschaft/ \
  https://studiumplus.de/duales-studium/vor-dem-studium/freie-studienplaetze/ \
  https://studiumplus.de/connect/ \
  https://studiumplus.de/ueber-uns/downloads/ \
  https://studiumplus.de/duales-studium/im-studium/infos-fuer-studierende/praxis-im-unternehmen/ \
  https://studiumplus.de/ueber-uns/campus-team/ \
  https://studiumplus.de/duales-studium/vor-dem-studium/mein-weg-zu-studiumplus/
```

Optionen:

```bash
python scripts/clone.py --max-depth 5 --delay 1.0 --output-dir . <URL ...>
```

## Lokal starten

```bash
python -m http.server
```

Danach:

- Übersicht: `http://localhost:8000/index.html`
- Viewer: `http://localhost:8000/viewer.html#<local_path>`

## Verzeichnisstruktur (Kurzform)

```text
site_sp_partialclone/
├── README.md
├── registry.json
├── index.html
├── viewer.html
├── assets/
│   └── app.css
├── thumbnails/
├── _shared_assets/
├── duales-studium/
├── studiengaenge/
└── scripts/
    ├── clone.py
    ├── requirements.txt
    └── clone.log
```
