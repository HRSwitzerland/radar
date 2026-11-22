# HR Radar

Tägliche Newsplattform für HR-Profis in der Schweiz: Arbeitsrecht, Gesetze, Lohn und Vorsorge, Arbeitsmarkt, Gesundheit und Führung, HR-Tech und KI, HR-Praxis. Jeder Beitrag mit Quellen.

## Aufbau
- `data/articles.json` – einzige Inhaltsquelle: Einstellungen (`site`), Artikel, Kennzahlen, Termine
- `build.py` – erzeugt alle Seiten: `python3 build.py` (prüft Pflichtfelder und bricht bei Fehlern ab)
- `assets/style.css` – Design
- `tools.py` – Rechner (Kündigung/Sperrfrist, Lohnfortzahlung, Ferien, BVG) und Hilfsfunktionen; die Rechner laufen im Browser
- Erzeugt: `aenderungen.html` (Zeitleiste aus `effective`-Daten und `termine`), `woche/<JJJJ-WW>.html` (Wochenrückblicke), `rechner/`, `index.html`, `artikel/<id>.html`, `rubrik/<rubrik>.html`, `archiv.html`, `suche.html` + `search.json`, `newsletter.html`, `ueber.html`, `feed.xml`, `feeds/<rubrik>.xml`

## Artikelformat (in `articles`, neue Artikel OBEN einfügen)
```json
{
  "id": "slug-a-z-0-9",
  "published": "JJJJ-MM-TT",
  "date": "JJJJ-MM-TT (Datum des Ereignisses, optional)",
  "category": "arbeitsrecht | gesetze | lohn | arbeitsmarkt | gesundheit | digital | praxis",
  "featured": true,
  "tags": ["Stichwort"],
  "title": "...",
  "teaser": "1-2 Sätze für Karten und Einleitung",
  "summary": "In 30 Sekunden: 2-4 Sätze",
  "sections": [{"h": "Zwischentitel", "p": "Absatz"}],
  "takeaways": ["Das heisst für HR: konkreter Hinweis"],
  "refs": ["Art. 336 OR"],
  "effective": "JJJJ-MM-TT (optional)",
  "sources": [{"label": "Quelle, Datum", "url": "https://..."}]
}
```
`featured: true` macht einen Artikel zum Top-Thema auf der Startseite (immer nur der jüngste zählt).

Jeden Tag ergänzt eine geplante Aufgabe neue Artikel, führt `build.py` aus und pusht. GitHub Pages veröffentlicht automatisch.

## Wochenrückblick
Wochenseiten entstehen automatisch aus allen Artikeln einer ISO-Kalenderwoche (Top 5: Top-Thema, dann Anzahl Quellen).
Optional ergänzt die Freitags-Ausgabe eine redaktionelle Einordnung in `weeks`:
```json
"weeks": [{"id": "2026-48", "title": "Kurzer Titel der Woche", "intro": "3-5 Sätze Einordnung"}]
```
