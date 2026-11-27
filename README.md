# HR Radar

Tägliche Newsplattform für HR-Profis in der Schweiz: Arbeitsrecht, Gesetze, Lohn und Vorsorge, Arbeitsmarkt, Gesundheit und Führung, HR-Tech und KI, HR-Praxis, dazu die Rubrik Legal & Compliance mit Rechtsänderungen für Unternehmen und KMU. Jeder Beitrag mit Quellen.

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
  "category": "arbeitsrecht | gesetze | lohn | arbeitsmarkt | gesundheit | digital | praxis | legal",
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
`featured: true` macht einen Artikel zum Top-Thema auf der Startseite, aber nur am Tag seiner Veröffentlichung (Erscheinungstag = neuester Tag). Sobald neuere Artikel erscheinen, rückt automatisch der neueste Artikel nach oben.

Legal-Beiträge (`category: "legal"`) werden **nie Top-Thema**: `featured` bei Legal-Artikeln nicht setzen; build.py überspringt sie ohnehin. Auch sonst zeigt die Startseite Legal zurückhaltend (höchstens 1 Legal-Beitrag bei «Ebenfalls wichtig», 2 bei «Neueste Beiträge», keiner in der Wochenkarte, 1 im Hintergrund-Block; einstellbar in `HOME_MAX` in build.py). In der Rubrik Legal, im Archiv und im Newsletter erscheinen weiterhin alle Legal-Beiträge.

Jeden Tag ergänzt eine geplante Aufgabe neue Artikel, führt `build.py` aus und pusht. GitHub Pages veröffentlicht automatisch.

## Rubrik Legal & Compliance
`legal`: Gesetzes- und Verordnungsänderungen für Unternehmen und KMU ausserhalb des Arbeitsrechts, z.B. Gesellschaftsrecht, Handels- und Transparenzregister, Vertrags- und Haftpflichtrecht, Datenschutz, Wettbewerbs- und Kartellrecht, Geldwäscherei, Immaterialgüterrecht, Mehrwertsteuer-Verfahren, Digitalisierung (E-ID), Lieferketten und Nachhaltigkeit sowie EU-Recht mit Wirkung auf Schweizer Firmen. Arbeitsrechtliche Gesetzgebung bleibt in `gesetze`.

## Farben und Lesbarkeit
Jede Rubrik hat in `build.py` (`PALETTE`) eine Akzent- und eine Hintergrundfarbe. `build.py` leitet daraus automatisch eine helle und eine dunkle Variante (Dunkelmodus) ab und prüft bei jedem Build den Kontrast nach WCAG AA (mindestens 4,5:1) für Titel und Akzenttext auf dem Rubrik-Hintergrund. Ist ein Wert zu tief, bricht der Build mit «FEHLER Kontrast» ab. Farben nie direkt in HTML oder Artikeltexte schreiben, sondern nur über `PALETTE`.

## Themenseiten (Landingpages) und SEO
- `data/themen.json`: evergreen Themenseiten unter `thema/<slug>.html` (Grundlagen, FAQ, Rechner, automatisch verlinkte Beiträge über `match.tags` und `match.words`). Dazu `thema/index.html` und die automatische Seite `thema/neuerungen-<Jahr>.html` aus allen `effective`-Daten und `termine` des kommenden Jahres.
- `build.py` erzeugt pro Seite Canonical-URL, Open-Graph- und Twitter-Tags, strukturierte Daten (NewsArticle, BreadcrumbList, CollectionPage, FAQPage, WebSite mit Suche), `sitemap.xml`, `robots.txt` und `404.html`.
- Vorschaubilder für soziale Medien liegen in `assets/og/` (je Rubrik ein Bild, dazu `default.png`, `logo.png`, `favicon.png`).
- Bei eigener Domain: `site.url` in `data/articles.json` anpassen, dann stimmen Canonical-URLs, Sitemap und robots.txt automatisch.

## Wochenrückblick
Wochenseiten entstehen automatisch aus allen Artikeln einer ISO-Kalenderwoche (Top 5: Top-Thema, dann Anzahl Quellen).
Optional ergänzt die Freitags-Ausgabe eine redaktionelle Einordnung in `weeks`:
```json
"weeks": [{"id": "2026-48", "title": "Kurzer Titel der Woche", "intro": "3-5 Sätze Einordnung"}]
```

## Hintergrundartikel (mit Freigabe)
- Entwürfe liegen als einzelne Datei in `data/drafts/<id>.json` (gleiches Format wie ein Artikel, dazu `"type": "hintergrund"`).
- `build.py` erzeugt dafür eine Vorschau unter `vorschau/<id>.html` (noindex, nirgends verlinkt, mit Entwurfs-Banner).
- Freigabe: Datei aus `data/drafts/` löschen, Artikel mit `published` = Freigabedatum OBEN in `articles` einfügen, `python3 build.py`, pushen.
- Veröffentlichte Hintergrundartikel erscheinen auf der Startseite («Hintergrund & Analyse») und unter `hintergrund.html`.

## Newsletter (jeden Dienstag) und Eilmeldungen
- Ausgaben stehen in `newsletters`: `{"id": "JJJJ-WW", "label": "KW WW/JJJJ", "date": "JJJJ-MM-TT", "title": "...", "intro": "..."}`. Eine Ausgabe enthält alle Beiträge der letzten 7 Tage, pro Rubrik höchstens 4. Die Redaktion legt jeden Dienstag in der Morgenausgabe eine Ausgabe an.
- Eilmeldung: im Artikel `"alert": true` setzen (nur bei sehr grosser Tragweite).
- `build.py` legt Versandaufträge in `newsletter/outbox/` ab (nur wenn nicht schon in `newsletter/sent/` und höchstens 3 Tage alt). Webversionen: `newsletter/archiv/<id>.html`.
- Versand: GitHub Action `.github/workflows/newsletter.yml` ruft `send_newsletter.py` auf (Brevo-API). Benötigt Secret `BREVO_API_KEY` und Variablen `BREVO_LIST_ID`, `BREVO_ALERT_SEGMENT_ID`, `SENDER_EMAIL`, `SENDER_NAME`. Ohne Key passiert nichts.
- Themenwahl: Brevo-Kontaktattribute `THEMA_ARBEITSRECHT`, `THEMA_GESETZE`, `THEMA_LOHN`, `THEMA_ARBEITSMARKT`, `THEMA_GESUNDHEIT`, `THEMA_DIGITAL`, `THEMA_PRAXIS`, `THEMA_LEGAL`, `EILMELDUNG` (Typ Boolean), `VORNAME` (Text).
- Anmeldeformular: Formular-URL von Brevo in `site.newsletter_form_action` eintragen.


## SEO-Feinschliff
- `SEO_OVERRIDES` in build.py setzt Suchmaschinen-Titel und -Beschreibungen für Übersichtsseiten, Rubriken und Rechner.
- Titel über 65 Zeichen erhalten keinen Zusatz «· HR Radar»; Beschreibungen werden auf 158 Zeichen gekürzt.
- Seiten ohne eigene strukturierte Daten erhalten automatisch ein WebPage-JSON-LD.
- Rechner verlinken unter «Mehr zum Thema» auf Themenseiten, die den Rechner in `tools` führen.
