# Experiment-Workflow

Dieses Verzeichnis dokumentiert lokale UX-Optimierungen an bereits geklonten Seiten.

## Zielbild

- `clone.py` bleibt unverändert.
- `viewer.html` bleibt unverändert.
- Anpassungen erfolgen direkt in den geklonten Inhalten.
- Jede Variante ist über Branch, Commit und Log-Eintrag nachvollziehbar.

## Branching-Konvention

- Ein Experiment pro Branch: `exp/<thema>-<nn>-<slug>`
- Für Hero-Tests:
  - `exp/hero-01-static-compact`
  - `exp/hero-02-compact-plus-spacing`
  - `exp/hero-03-timed-collapse`

## Commit-Messaging-Konvention

Format:

`exp(<thema>): <variante> - <ziel>`

Beispiele:

- `exp(hero): static compact - reduce first-screen hero dominance`
- `exp(hero): compact plus spacing - surface body copy earlier`
- `exp(hero): timed collapse - test progressive header reduction`

Empfohlener Body:

- `Hypothesis:` erwartete Verbesserung
- `Change:` konkrete CSS/HTML-Anpassung
- `Expected:` sichtbarer Effekt in der Vorschau

## Log-Datei

Laufendes Protokoll: `experiments/hero-image-betriebswirtschaft.md`

- Baseline mit Messwerten und Screenshots
- Ein Abschnitt pro Experiment
- Entscheidung: behalten / verwerfen / nachschärfen

## Screenshot-Tooling

Für reproduzierbare Vergleichsbilder nutzen wir:

- `experiments/capture_hero_screenshots.py`

Das Skript klickt vor jedem Screenshot das Borlabs-Cookie-Banner weg (primär per `Speichern`, mit Fallback auf andere Consent-Aktionen), damit die Seite im Bild frei sichtbar ist.
