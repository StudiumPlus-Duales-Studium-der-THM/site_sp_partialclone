# Experiment-Log: Hero-Optimierung

- Seite lokal: `studiengaenge/betriebswirtschaft/index.html`
- Viewer-URL: `viewer.html#studiengaenge/betriebswirtschaft/`
- Ziel: mehr relevanten Inhalt direkt im ersten Screen sichtbar machen
- Scope: nur geklonte Inhalte (kein `clone.py`, kein `viewer.html`)

## Erfolgskriterien

- Desktop (1280x800): erster Inhaltsblock startet deutlich früher als in der Baseline.
- Mobile (390x844): Hero bleibt visuell stimmig, ohne den gesamten First Screen zu belegen.
- Keine regressiven Brüche bei Header/Breadcrumb/H1.

## Experiment-Reihenfolge

1. `exp/hero-01-static-compact`
   - Hero-Höhe per `clamp(...)` begrenzen.
2. `exp/hero-02-compact-plus-spacing`
   - zusätzlich vertikale Abstände unter Hero/Intro reduzieren.
3. `exp/hero-03-timed-collapse` (optional)
   - Hero groß starten, dann zeitgesteuert einklappen.

## Baseline (Ausgangszustand)

- Datum: `2026-02-25T22:40:40Z`
- Commit: `08285e2` (`main`)
- Screenshot(s):
  - `experiments/screenshots/hero-baseline-desktop.png`
  - `experiments/screenshots/hero-baseline-mobile.png`
- Messwerte:
  - Desktop: `heroHeight=800`, `firstContentTop=945`
  - Mobile: `heroHeight=468`, `firstContentTop=777`
- Cookie-Banner: vor Screenshot automatisch per `Speichern` bestätigt.
- Beobachtung: Hero dominiert den ersten Viewport; inhaltlicher Einstieg ist erst nach deutlichem Scrollen sichtbar.

---

## Laufende Einträge

### EXP-01 `exp/hero-01-static-compact`

- Status: umgesetzt
- Commit: offen
- Geänderte Datei(en):
  - `studiengaenge/betriebswirtschaft/index.html`
- Änderung:
  - statische Begrenzung der Hero-Höhe per CSS (`clamp`), inklusive sauberem Bild-Cropping.
- Screenshot(s):
  - `experiments/screenshots/hero-exp01-static-compact-desktop.png`
  - `experiments/screenshots/hero-exp01-static-compact-mobile.png`
- Messwerte:
  - Desktop: `heroHeight=240`, `firstContentTop=385`
  - Mobile: `heroHeight=203`, `firstContentTop=511`
- Cookie-Banner: vor Screenshot automatisch per `Speichern` bestätigt.
- Ergebnis (Desktop): erster Inhaltsblock deutlich früher sichtbar.
- Ergebnis (Mobile): Hero weiterhin präsent, aber nicht mehr bildschirmfüllend.
- Bewertung: klarer Gewinn für „direkt mehr Inhalt sehen“.
- Entscheidung: behalten als Referenzvariante, danach EXP-02 testen.

### EXP-02 `exp/hero-02-compact-plus-spacing`

- Status: geplant
- Commit:
- Geänderte Datei(en):
- Änderung:
- Ergebnis (Desktop):
- Ergebnis (Mobile):
- Bewertung:
- Entscheidung: behalten / verwerfen / nachschärfen

### EXP-03 `exp/hero-03-timed-collapse`

- Status: geplant
- Commit:
- Geänderte Datei(en):
- Änderung:
- Ergebnis (Desktop):
- Ergebnis (Mobile):
- Bewertung:
- Entscheidung: behalten / verwerfen / nachschärfen
