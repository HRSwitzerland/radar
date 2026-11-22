# HR-Recht Radar Schweiz

Wöchentlicher Newsdienst im Blog-Format zu Arbeitsrecht, Bundesgerichtsurteilen, Gesetzgebung, Sozialversicherungen und HR-Praxis in der Schweiz.

## So funktioniert die Seite
- `data/news.json` – die einzige Inhaltsquelle: Einstellungen (`site`), Ausgaben, Meldungen, Kennzahlen, Termine
- `build.py` – erzeugt daraus alle Seiten: `python3 build.py`
- `assets/style.css` – das Design
- Erzeugt werden: `index.html` (Startseite), `ausgaben/` (eine Seite pro Ausgabe + Archiv), `meldungen/` (eine Detailseite pro Meldung), `newsletter.html`, `ueber.html`, `feed.xml` und `feeds/<thema>.xml`

Jeden Montag ergänzt eine geplante Aufgabe `data/news.json`, führt `build.py` aus und pusht. GitHub Pages veröffentlicht automatisch.

## Einstellungen in `data/news.json` → `site`
- `url` – öffentliche Adresse (nach dem Domainwechsel anpassen, wird für RSS-Links gebraucht)
- `publisher` – Angaben fürs Impressum
- `newsletter_form_action` – Formular-URL des Newsletter-Dienstes; leer = Anmeldung noch nicht aktiv
