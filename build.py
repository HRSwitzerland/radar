#!/usr/bin/env python3
"""Erzeugt die statische Newsplattform «HR Radar» aus data/articles.json.

Aufruf:  python3 build.py
Erzeugt: index.html, artikel/, rubrik/, woche/, rechner/, aenderungen.html, archiv.html, suche.html,
         newsletter.html, ueber.html, search.json, feed.xml, feeds/<rubrik>.xml
"""
import hashlib
import html
import re
import json
import os
import random
import shutil
from datetime import date, datetime
from email.utils import format_datetime

import tools
import newsletter as nl

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(ROOT, "data", "articles.json"), encoding="utf-8"))
SITE = DATA.get("site", {})
SITE_NAME = SITE.get("name", "HR Radar")
SITE_URL = SITE.get("url", "https://hrswitzerland.github.io/radar/").rstrip("/") + "/"
NL_ACTION = SITE.get("newsletter_form_action", "")
SUPPORT_URL = SITE.get("support_url", "")
GOATCOUNTER = SITE.get("goatcounter", "")  # z.B. "hrradar" fuer https://hrradar.goatcounter.com
PUBLISHER = SITE.get("publisher", "[Name, Adresse und E-Mail ergänzen]")
HAS_PUBLISHER = bool(PUBLISHER.strip()) and not PUBLISHER.strip().startswith("[")
e = html.escape
_TH_PATH = os.path.join(ROOT, "data", "themen.json")
THEMEN = json.load(open(_TH_PATH, encoding="utf-8")).get("themen", []) if os.path.exists(_TH_PATH) else []
SITEMAP = {}   # url -> lastmod
LASTMOD = {}   # path -> lastmod (für Artikel)
DEFAULT_DESC = "Das Wichtigste für HR- und Legal-Verantwortliche in der Schweiz: Arbeitsrecht, Gesetze, Lohn und Sozialversicherungen, Arbeitsmarkt, HR-Tech und Rechtsänderungen für KMU. Verständlich zusammengefasst, immer mit Quellen."

# Rubriken: key -> (Name, Kurzname, Beschreibung)
CATS = {
    "arbeitsrecht": ("Arbeitsrecht & Urteile", "Arbeitsrecht", "Neue Urteile des Bundesgerichts und des EGMR, eingeordnet für die HR-Praxis."),
    "gesetze": ("Gesetze & Politik", "Gesetze", "Gesetzesänderungen, Vernehmlassungen, Parlamentsentscheide und EU-Recht mit Wirkung auf die Schweiz."),
    "lohn": ("Lohn & Vorsorge", "Lohn", "Lohnrunden, AHV, BVG, Mindestlöhne, Familienzulagen und alles rund um die Lohnabrechnung."),
    "arbeitsmarkt": ("Arbeitsmarkt & Recruiting", "Arbeitsmarkt", "Arbeitslosigkeit, Fachkräftemangel, Stellenmarkt und Trends in der Personalgewinnung."),
    "gesundheit": ("Gesundheit & Führung", "Gesundheit", "Absenzen, psychische Gesundheit, BGM, Führung und Unternehmenskultur."),
    "digital": ("HR-Tech & KI", "HR-Tech", "Künstliche Intelligenz, HR-Software, Daten und die digitale Personalarbeit."),
    "praxis": ("HR-Praxis & Behörden", "Praxis", "Stellenmeldepflicht, Bewilligungen, Kontingente und Hinweise von SECO, EDÖB und Kantonen."),
    "legal": ("Legal & Compliance", "Legal", "Gesetzesänderungen für Unternehmen und KMU: Gesellschafts- und Vertragsrecht, Register, Datenschutz, Wettbewerb, Geldwäscherei und Compliance."),
}
ORDER = list(CATS)
PALETTE = {
    "arbeitsrecht": ("#5a46d6", "#efebff"),
    "gesetze": ("#d9452f", "#ffece6"),
    "lohn": ("#1f8a62", "#e3f6ec"),
    "arbeitsmarkt": ("#2b7bbd", "#e4f1fb"),
    "gesundheit": ("#c2417a", "#fde8f1"),
    "digital": ("#0f8b8d", "#dff5f4"),
    "praxis": ("#b9780a", "#fff3d6"),
    "legal": ("#3d5a80", "#e6edf6"),
}
_I = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
ICONS = {
    "arbeitsrecht": _I + '<path d="M12 3v18M5 21h14M7 7h10M7 7l-3 7a3 3 0 0 0 6 0L7 7zM17 7l-3 7a3 3 0 0 0 6 0l-3-7z"/></svg>',
    "gesetze": _I + '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/></svg>',
    "lohn": _I + '<circle cx="12" cy="12" r="9"/><path d="M15 9.5c-.5-1-1.6-1.5-3-1.5-1.7 0-3 .8-3 2s1.3 1.8 3 2 3 .8 3 2-1.3 2-3 2c-1.4 0-2.5-.5-3-1.5M12 6v2M12 16v2"/></svg>',
    "arbeitsmarkt": _I + '<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 6-6"/><path d="M16 8h4v4"/></svg>',
    "gesundheit": _I + '<path d="M20.8 5.6a5 5 0 0 0-7.1 0L12 7.3l-1.7-1.7a5 5 0 1 0-7.1 7.1L12 21.5l8.8-8.8a5 5 0 0 0 0-7.1z"/></svg>',
    "digital": _I + '<rect x="5" y="5" width="14" height="14" rx="3"/><path d="M9 9h6v6H9zM9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/></svg>',
    "praxis": _I + '<circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0M16 4a3 3 0 0 1 0 6M21 20a6 6 0 0 0-4-5.6"/></svg>',
    "legal": _I + '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18M11 13v2h2v-2"/></svg>',
}
BULB = _I + '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/></svg>'
LINK = _I + '<path d="M10 13a5 5 0 0 0 7.1 0l3-3a5 5 0 0 0-7.1-7.1l-1 1"/><path d="M14 11a5 5 0 0 0-7.1 0l-3 3a5 5 0 0 0 7.1 7.1l1-1"/></svg>'
BOOK = _I + '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5M8 7h7M8 11h7"/></svg>'
SEARCH = _I + '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>'
LOGO = '<svg class="logo-mark" viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="18" fill="var(--sun)"/><circle cx="20" cy="20" r="11.5" fill="none" stroke="var(--ink)" stroke-width="2.2" stroke-dasharray="3 3.2"/><path d="M20 20 L31 11" stroke="var(--ink)" stroke-width="2.6" stroke-linecap="round"/><circle cx="20" cy="20" r="3" fill="var(--accent)"/><circle cx="28" cy="25" r="2.4" fill="var(--accent)"/></svg>'
MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
SHORT_MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
WAVE = '<svg class="wave" viewBox="0 0 1200 46" preserveAspectRatio="none" aria-hidden="true"><path d="M0 46 V20 C 150 0 300 40 450 22 S 750 0 900 20 S 1100 40 1200 18 V46 Z" fill="currentColor"/></svg>'
WAVE_FLIP = WAVE.replace('class="wave"', 'class="wave flip"')


def d_short(iso):
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def d_long(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d}. {MONTHS[m - 1]} {y}"


def d_day(iso):
    dt = datetime.strptime(iso, "%Y-%m-%d")
    return f"{WEEKDAYS[dt.weekday()]}, {d_long(iso)}"


def reading_time(a):
    text = " ".join([a.get("teaser", ""), a.get("summary", "")] + [s.get("p", "") for s in a.get("sections", [])] + a.get("takeaways", []))
    return max(1, round(len(text.split()) / 200))


def articles():
    # Neueste zuerst; am selben Tag zählt die Reihenfolge in articles.json (oben = neuer).
    idx = {a["id"]: i for i, a in enumerate(DATA["articles"])}
    return sorted(DATA["articles"], key=lambda a: (a["published"], a.get("featured", False), -idx[a["id"]]), reverse=True)


def by_cat(k):
    return [a for a in articles() if a["category"] == k]


def page_url(path):
    path = path.replace(os.sep, "/")
    if path == "index.html":
        return SITE_URL
    if path.endswith("/index.html"):
        return SITE_URL + path[: -len("index.html")]
    return SITE_URL + path


# Suchmaschinen-Titel und -Beschreibungen für Seiten, deren Anzeigetitel kurz ist.
SEO_OVERRIDES = {
    "suche.html": ("Suche: HR-News, Urteile und Gesetze finden · HR Radar",
                   "Durchsuchen Sie alle Beiträge von HR Radar zu Arbeitsrecht, Lohn, Sozialversicherungen, Gesetzen und Legal & Compliance in der Schweiz."),
    "ueber.html": ("Über HR Radar: News für HR und Legal in der Schweiz",
                   "Was HR Radar ist, wie die Beiträge entstehen und wer dahinter steht: werktäglich eingeordnete News zu Arbeitsrecht, HR und Legal in der Schweiz."),
    "archiv.html": ("Archiv: alle HR-News und Urteile · HR Radar",
                    "Alle Beiträge von HR Radar nach Datum: Bundesgerichtsurteile, Gesetzesänderungen, Lohn und Sozialversicherungen, Arbeitsmarkt und Legal."),
    "newsletter.html": ("HR-Newsletter Schweiz: jeden Dienstag · HR Radar",
                        "Kostenloser HR-Newsletter: jeden Dienstag die wichtigsten News zu Arbeitsrecht, HR und Legal in der Schweiz, nur aus Ihren Rubriken."),
    "hintergrund.html": ("Hintergrund: HR- und Rechtsthemen vertieft · HR Radar",
                         "Ausführliche Hintergrundartikel zu Arbeitsrecht, HR-Praxis und Legal in der Schweiz: Rechtslage, Rechtsprechung, typische Fehler und Checklisten."),
    "unterstuetzen.html": ("HR Radar unterstützen: werbefrei und unabhängig",
                           "HR Radar ist kostenlos und werbefrei. Mit einem freiwilligen Beitrag unterstützen Sie die Newsplattform für HR und Legal in der Schweiz."),
    "aenderungen.html": ("Das ändert sich 2026/2027: Fristen für HR und KMU",
                         "Zeitleiste aller Inkrafttreten und Fristen für HR, Lohn und Unternehmen in der Schweiz: Gesetze, Sozialversicherungen, Register und Meldepflichten."),
    "rechner/index.html": ("HR-Rechner Schweiz: Kündigungsfrist, Lohnfortzahlung, BVG",
                           "Kostenlose HR-Rechner für die Schweiz: Kündigungsfrist und Sperrfrist, Lohnfortzahlung bei Krankheit, Ferien pro rata und BVG-Check."),
    "rechner/kuendigung.html": ("Kündigungsfrist-Rechner Schweiz mit Sperrfrist (OR)",
                                "Kündigungsfrist berechnen: Enddatum des Arbeitsverhältnisses mit Probezeit, Dienstjahren und Verlängerung durch Krankheit oder Unfall (Art. 335c, 336c OR)."),
    "rechner/lohnfortzahlung.html": ("Lohnfortzahlung bei Krankheit berechnen: Berner Skala",
                                     "Wie lange muss der Lohn bei Krankheit bezahlt werden? Rechner nach Berner, Zürcher und Basler Skala (Art. 324a OR), mit Dienstjahren."),
    "rechner/ferien.html": ("Ferienanspruch pro rata berechnen (Schweiz)",
                            "Ferientage bei Eintritt oder Austritt unter dem Jahr und bei Teilzeit berechnen: Rechner nach Art. 329a OR, mit 4, 5 oder 6 Wochen Ferien."),
    "rechner/bvg.html": ("BVG-Rechner: koordinierter Lohn und Altersgutschrift",
                         "Ist der Lohn BVG-pflichtig? Koordinierten Lohn und minimale Altersgutschriften berechnen, mit den Grenzbeträgen 2026 und 2027."),
}
for _k, (_long, _short, _d) in CATS.items():
    SEO_OVERRIDES[f"rubrik/{_k}.html"] = (f"{_long}: aktuelle News Schweiz · {SITE_NAME}"[:70],
                                          f"{_long} – aktuelle News für HR und Legal in der Schweiz: {_d}")
SEO_OVERRIDES["woche/index.html"] = ("Wochenrückblicke: die HR-Woche in der Schweiz · HR Radar",
                                     "Jeden Freitag der Wochenrückblick von HR Radar: die wichtigsten Urteile, Gesetzesänderungen und HR-News der Woche, kurz eingeordnet.")

DESC_MAX = 158


def _short_desc(d):
    if len(d) <= DESC_MAX:
        return d
    cut = d[:DESC_MAX].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + " …"


def seo_postprocess(path, content):
    if path in SEO_OVERRIDES:
        t, d = SEO_OVERRIDES[path]
        content = re.sub(r"<title>.*?</title>", f"<title>{e(t)}</title>", content, count=1, flags=re.S)
        content = re.sub(r'(<meta (?:name|property)="(?:description|og:description|twitter:description)" content=")[^"]*"', lambda m: m.group(1) + e(d) + '"', content)
    content = re.sub(r'(<meta name="description" content=")([^"]*)"', lambda m: m.group(1) + e(_short_desc(html.unescape(m.group(2)))) + '"', content, count=1)
    if "application/ld+json" not in content and 'content="noindex' not in content and "</head>" in content:
        t = re.search(r"<title>(.*?)</title>", content, re.S)
        d = re.search(r'<meta name="description" content="([^"]*)"', content)
        ld = {"@context": "https://schema.org", "@type": "WebPage", "name": html.unescape(t.group(1)) if t else SITE_NAME,
              "description": html.unescape(d.group(1)) if d else DEFAULT_DESC, "url": page_url(path), "inLanguage": "de-CH",
              "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": SITE_URL}}
        content = content.replace("</head>", ld_script(ld) + "</head>", 1)
    return content


_INDEX_HREF = re.compile(r'href="((?:' + re.escape(SITE_URL) + r')?(?:\.\./)*)((?:[\w-]+/)*)index\.html(#[^"]*)?"')


def clean_index_links(html):
    """Interne Links auf .../index.html zeigen auf die Verzeichnisadresse (= kanonische URL)."""
    def rep(m):
        target = (m.group(1) + m.group(2)) or "./"
        return f'href="{target}{m.group(3) or ""}"'
    return _INDEX_HREF.sub(rep, html)


def write(path, content):
    if path.endswith(".html"):
        content = clean_index_links(content)
        content = seo_postprocess(path, content)
    if path.endswith(".html") and "<!--SEO:CANON-->" in content:
        url = page_url(path)
        content = content.replace("<!--SEO:CANON-->", f'<link rel="canonical" href="{e(url)}">\n<meta property="og:url" content="{e(url)}">')
        if 'name="robots" content="noindex' not in content and path != "404.html":
            SITEMAP[url] = LASTMOD.get(path, DATA.get("updated", date.today().isoformat()))
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def cover(a, cls="cover"):
    """Deterministische, verspielte Titelgrafik pro Artikel (SVG, keine Fremdbilder)."""
    fg, bg = PALETTE.get(a["category"], ("#2b2540", "#efebff"))
    rnd = random.Random(int(hashlib.md5(a["id"].encode()).hexdigest(), 16))
    accents = ["#ffd76e", "#ff6f59", "#bfe8d6", "#ddd3ff", "#ffffff"]
    shapes = []
    for _ in range(3):
        cx, cy, r = rnd.randint(40, 560), rnd.randint(20, 300), rnd.randint(50, 130)
        col = rnd.choice(accents + [fg])
        op = 0.9 if col != fg else 0.18
        shapes.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}" opacity="{op}"/>')
    x0 = rnd.randint(-40, 120)
    pts = " ".join(f"{x0 + i * 60},{rnd.randint(120, 260) + (25 if i % 2 else -25)}" for i in range(12))
    shapes.append(f'<polyline points="{pts}" fill="none" stroke="{fg}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" opacity=".55"/>')
    dots = "".join(f'<circle cx="{rnd.randint(380, 590)}" cy="{rnd.randint(20, 120)}" r="5" fill="{fg}" opacity=".5"/>' for _ in range(7))
    rx, ry = rnd.randint(30, 420), rnd.randint(30, 200)
    rect = f'<rect x="{rx}" y="{ry}" width="{rnd.randint(70, 140)}" height="{rnd.randint(70, 140)}" rx="26" fill="{rnd.choice(accents)}" transform="rotate({rnd.randint(-25, 25)} {rx + 50} {ry + 50})"/>'
    icon = ICONS[a["category"]].replace('viewBox="0 0 24 24"', 'x="248" y="108" width="104" height="104" viewBox="0 0 24 24"').replace('stroke="currentColor"', f'stroke="{fg}"').replace('stroke-width="2"', 'stroke-width="1.6"')
    badge = '<circle cx="300" cy="160" r="82" fill="#ffffff"/>'
    return f'<svg class="{cls}" viewBox="0 0 600 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration zur Rubrik {e(CATS[a["category"]][0])}"><rect width="600" height="320" fill="{bg}"/>{"".join(shapes)}{rect}{dots}{badge}{icon}</svg>'


# ---------- Farben: helle und dunkle Variante pro Rubrik, mit Kontrastprüfung ----------
DARK_BG, DARK_INK, LIGHT_INK = "#17141f", "#f3f0fa", "#2b2540"
MIN_CONTRAST = 4.5  # WCAG AA für normalen Text


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def _mix(a, b, t):
    """t = Anteil von a (0..1)."""
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(ra[i] * t + rb[i] * (1 - t) for i in range(3)))


def contrast(a, b):
    def lum(h):
        out = []
        for c in _rgb(h):
            c = c / 255
            out.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def dark_variant(fg):
    """Dunkler Hintergrund und helle Akzentfarbe für den Dunkelmodus, so gewählt, dass Text lesbar bleibt."""
    bg_d = _mix(fg, DARK_BG, 0.2)
    t = 0.45
    fg_d = _mix(fg, "#ffffff", 1 - t)
    while contrast(fg_d, bg_d) < MIN_CONTRAST and t > 0:
        t -= 0.05
        fg_d = _mix(fg, "#ffffff", 1 - t)
    return fg_d, bg_d


def light_variant(fg, bg):
    """Akzentfarbe im hellen Modus, bei Bedarf abgedunkelt, damit sie auf dem Rubrik-Hintergrund lesbar ist."""
    t, out = 1.0, fg
    while contrast(out, bg) < MIN_CONTRAST and t > 0:
        t -= 0.05
        out = _mix(fg, LIGHT_INK, t)
    return out


def palette_css():
    light = "".join(f"--cc-{k}:{light_variant(fg, bg)};--cb-{k}:{bg};" for k, (fg, bg) in PALETTE.items())
    dark = "".join(f"--cc-{k}:{dark_variant(fg)[0]};--cb-{k}:{dark_variant(fg)[1]};" for k, (fg, bg) in PALETTE.items())
    return (f"<style>:root{{{light}}}"
            f"@media (prefers-color-scheme: dark){{:root:not([data-theme=\"light\"]){{{dark}}}}}"
            f":root[data-theme=\"dark\"]{{{dark}}}</style>")


def check_contrast():
    """Bricht den Build ab, wenn Text auf einer Rubrikfarbe in Hell oder Dunkel schlecht lesbar wäre."""
    problems = []
    for k, (fg, bg) in PALETTE.items():
        fd, bd = dark_variant(fg)
        for name, a, b in (("hell: Titel auf Rubrikfarbe", LIGHT_INK, bg), ("hell: Akzent auf Rubrikfarbe", light_variant(fg, bg), bg),
                           ("dunkel: Titel auf Rubrikfarbe", DARK_INK, bd), ("dunkel: Akzent auf Rubrikfarbe", fd, bd)):
            if contrast(a, b) < MIN_CONTRAST:
                problems.append(f"{k} ({name}): Kontrast {contrast(a, b):.2f} < {MIN_CONTRAST}")
    if problems:
        raise SystemExit("FEHLER Kontrast:\n  " + "\n  ".join(problems))


def cat_style(k):
    if k not in PALETTE:
        return ""
    return f"--catc:var(--cc-{k});--catb:var(--cb-{k});"


def tag(k, up):
    return f'<a class="tag" href="{up}rubrik/{k}.html" style="{cat_style(k)}">{e(CATS[k][1])}</a>'


def og_image(cat=None):
    if cat and os.path.exists(os.path.join(ROOT, "assets", "og", f"{cat}.png")):
        return f"{SITE_URL}assets/og/{cat}.png"
    return f"{SITE_URL}assets/og/default.png"


def ld_script(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def breadcrumb(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}


PUBLISHER_LD = {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL,
                "logo": {"@type": "ImageObject", "url": SITE_URL + "assets/og/logo.png"}}


def layout(title, body, depth=0, desc="", active="", article=False, noindex=False, ld=None, og_type="website", cat=None, extra_head=""):
    up = "../" * depth
    def nav(href, label, key, cls=""):
        cur = ' aria-current="page"' if key == active else ""
        c = f' class="{cls}"' if cls else ""
        return f'<a href="{up}{href}"{cur}{c}>{label}</a>'
    if title == SITE_NAME:
        full_title = f"{SITE_NAME} · News zu Arbeitsrecht, HR und Legal in der Schweiz"
    elif len(title) + len(SITE_NAME) + 3 <= 65:
        full_title = f"{title} · {SITE_NAME}"
    else:
        full_title = title
    desc = desc or DEFAULT_DESC
    ld_html = "".join(ld_script(x) for x in (ld or []))
    cur = lambda key: ' aria-current="page"' if active == key else ""
    cats_nav = "".join(f'<a href="{up}rubrik/{k}.html" style="{cat_style(k)}"{cur("rubrik-" + k)}>{e(CATS[k][1])}</a>' for k in ORDER) + \
        f'<span class="cats-sep" aria-hidden="true"></span><a href="{up}hintergrund.html" class="plain"{cur("hintergrund")}>Hintergrund</a><a href="{up}thema/index.html" class="plain"{cur("themen")}>Themen</a>'
    return f"""<!DOCTYPE html>
<html lang="de-CH">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
{f'<script data-goatcounter="https://{GOATCOUNTER}.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>' if GOATCOUNTER and not noindex else ""}
<meta name="description" content="{e(desc)}">
{'<meta name="robots" content="noindex, nofollow">' if noindex else '<meta name="robots" content="index, follow, max-image-preview:large">'}
<!--SEO:CANON-->
<meta property="og:site_name" content="{e(SITE_NAME)}">
<meta property="og:locale" content="de_CH">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title if title != SITE_NAME else full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{og_image(cat)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title if title != SITE_NAME else full_title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{og_image(cat)}">
<meta name="theme-color" content="#ffd76e">
<link rel="icon" href="{up}assets/og/favicon.png" type="image/png">
{extra_head}{palette_css()}{ld_html}
<link rel="alternate" type="application/rss+xml" title="{e(SITE_NAME)}" href="{up}feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT,WONK@9..144,400..700,0..100,0..1&family=Nunito:wght@400;600;700;800&family=Caveat:wght@600;700&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/style.css">
</head>
<body>
{'<div class="progress" id="progress" aria-hidden="true"></div>' if article else ''}
<header class="site-head">
  <div class="wrap head-row">
    <a class="logo" href="{up}index.html">{LOGO}<span class="logo-text">{e(SITE_NAME)}<small>Was HR heute wissen muss</small></span></a>
    <nav class="main" aria-label="Hauptnavigation">
      {nav("index.html", "Home", "home")}
      {nav("aenderungen.html", "Das ändert sich", "aenderungen")}
      {nav("rechner/index.html", "Rechner", "rechner")}
      {nav("newsletter.html", "Newsletter", "newsletter", "cta")}
      <a href="{up}suche.html" class="icon-link{' is-active' if active == 'suche' else ''}" aria-label="Suche">{SEARCH}</a>
    </nav>
  </div>
  <div class="wrap"><nav class="cats" aria-label="Rubriken">{cats_nav}</nav></div>
</header>
<main>
{body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <div>
      <h2>{e(SITE_NAME)}</h2>
      <p>Das Wichtigste für HR- und Legal-Verantwortliche in der Schweiz. Verständlich zusammengefasst, eingeordnet und immer mit Quellen.</p>
      <p><a href="{up}thema/index.html">Themen</a> · <a href="{up}hintergrund.html">Hintergrund</a> · <a href="{up}woche/index.html">Wochenrückblick</a> · <a href="{up}archiv.html">Archiv</a> · <a href="{up}suche.html">Suche</a> · <a href="{up}feed.xml">RSS-Feed</a> · <a href="{up}ueber.html">Über</a>{f' · <a href="{up}unterstuetzen.html">Unterstützen</a>' if SUPPORT_URL else ""}</p>
    </div>
    <div>
      <h2>Themen</h2>
      <p class="foot-themes">{" · ".join(f'<a href="{up}thema/{t["slug"]}.html">{e(t.get("short") or t["title"].split(":")[0])}</a>' for t in THEMEN)} · <a href="{up}thema/{neuerungen_slug()}.html">Neuerungen {neuerungen_year()}</a></p>
    </div>
    <div>
      <h2>Gut zu wissen</h2>
      <p>Die Beiträge fassen öffentlich zugängliche Quellen zusammen und ersetzen keine Rechtsberatung. Massgebend sind die verlinkten Originalquellen. Inhalte werden mit KI-Unterstützung recherchiert und redaktionell zusammengestellt.</p>
    </div>
    <div>
      <h2>{"Impressum" if HAS_PUBLISHER else "Aktualität"}</h2>
      {f'<p>Herausgeber: {e(PUBLISHER)}</p>' if HAS_PUBLISHER else ""}
      <p>Letzte Aktualisierung: {d_short(DATA["updated"])}</p>
    </div>
  </div>
</footer>
<script>
var pb = document.getElementById('print-btn');
if (pb) {{ pb.addEventListener('click', function () {{ try {{ window.print(); }} catch (err) {{}} }}); }}
document.querySelectorAll('[data-filter]').forEach(function (group) {{
  var cards = document.querySelectorAll(group.getAttribute('data-filter'));
  group.querySelectorAll('.chip').forEach(function (b) {{
    b.addEventListener('click', function () {{
      group.querySelectorAll('.chip').forEach(function (x) {{ x.setAttribute('aria-pressed', String(x === b)); }});
      var c = b.getAttribute('data-cat');
      cards.forEach(function (card) {{ card.classList.toggle('hidden', c !== 'alle' && card.getAttribute('data-cat') !== c); }});
    }});
  }});
}});
var bar = document.getElementById('progress');
if (bar) {{
  var onScroll = function () {{
    var h = document.documentElement, max = h.scrollHeight - h.clientHeight;
    bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + '%';
  }};
  window.addEventListener('scroll', onScroll, {{ passive: true }}); onScroll();
}}
var copy = document.getElementById('copy-link');
if (copy) {{
  copy.addEventListener('click', function () {{
    var done = function () {{ copy.querySelector('span').textContent = 'Link kopiert'; }};
    try {{ navigator.clipboard.writeText(location.href).then(done, function () {{}}); }} catch (err) {{}}
  }});
}}
</script>
</body>
</html>
"""


def meta(a, up, long=False, rt=True):
    eff = f'<span class="eff">gilt ab {d_short(a["effective"])}</span>' if a.get("effective") else ""
    when = d_long(a["published"]) if long else d_short(a["published"])
    rts = f'<span class="dot-sep">{reading_time(a)} Min. Lesezeit</span>' if rt else ""
    bg = '<span class="bg-badge">Hintergrund</span>' if a.get("type") == "hintergrund" else ""
    alert = '<span class="alert-badge">Eilmeldung</span>' if a.get("alert") else ""
    return f'<div class="meta">{alert}{bg}{tag(a["category"], up)}<time datetime="{a["published"]}">{when}</time>{eff}{rts}</div>'


def card(a, up, size=""):
    href = f'{up}artikel/{a["id"]}.html'
    teaser = a["teaser"]
    if len(teaser) > 170:
        teaser = teaser[:170].rsplit(" ", 1)[0] + " …"
    return f"""<article class="card {size}" data-cat="{a['category']}" style="{cat_style(a['category'])}">
  <a class="card-link" href="{href}" tabindex="-1" aria-hidden="true"></a>
  <div class="card-cover">{cover(a)}</div>
  <div class="card-body">{meta(a, up, rt=False)}<h3><a href="{href}">{e(a['title'])}</a></h3><p>{e(teaser)}</p><span class="more">Weiterlesen</span></div>
</article>"""


def mini_row(a, up):
    return f'<a class="mini-row" href="{up}artikel/{a["id"]}.html" style="{cat_style(a["category"])}"><span class="mini-ico" aria-hidden="true">{ICONS[a["category"]]}</span><span><span class="mini-cat">{e(CATS[a["category"]][1])}</span><b>{e(a["title"])}</b></span></a>'


def kennzahlen_panel():
    kz = DATA.get("kennzahlen")
    if not kz:
        return ""
    rows = "".join(
        f'<tr><th scope="row">{e(r["label"])}</th><td>{e(r["alt"])}</td><td class="{"chg" if r["alt"] != r["neu"] else ""}">{e(r["neu"])}</td></tr>'
        for r in kz["rows"])
    return f"""<div class="panel"><h3>{e(kz['title'])}</h3>
<table><thead><tr><th scope="col">Wert</th><th scope="col">bisher</th><th scope="col">neu</th></tr></thead><tbody>{rows}</tbody></table>
<p class="note">{e(kz.get('note', ''))}</p></div>"""


def cal(iso):
    y, m, d = iso.split("-")
    return f'<span class="cal" aria-hidden="true"><span class="m">{SHORT_MONTHS[int(m) - 1]}</span><span class="d">{int(d)}</span><span class="y">{y}</span></span>'


def termine_panel(limit=None):
    today = date.today().isoformat()
    ts = sorted([t for t in DATA.get("termine", []) if t["date"] >= today], key=lambda t: t["date"])
    if limit:
        ts = ts[:limit]
    if not ts:
        return ""
    lis = "".join(f'<li>{cal(t["date"])}<span><span class="sr-only">{d_short(t["date"])}: </span>{e(t["label"])}</span></li>' for t in ts)
    return f'<div class="panel"><h3>Termine und Fristen</h3><ul class="dates">{lis}</ul></div>'


def chips(target, present):
    btns = ['<button type="button" class="chip" data-cat="alle" aria-pressed="true">Alle</button>']
    for k in ORDER:
        if k in present:
            btns.append(f'<button type="button" class="chip" data-cat="{k}" aria-pressed="false" style="{cat_style(k)}">{ICONS[k]}{e(CATS[k][1])}</button>')
    return f'<div class="chips" role="group" aria-label="Nach Rubrik filtern" data-filter="{target}">{"".join(btns)}</div>'


# ---------- Seiten ----------

def build_home():
    arts = articles()
    # Top-Thema: ein "featured"-Artikel nur, wenn er vom neuesten Erscheinungstag ist;
    # sonst der neueste Artikel. So bleibt kein älteres Top-Thema über neuen Beiträgen stehen.
    lead = next((a for a in arts if a.get("featured") and a["published"] == arts[0]["published"]), arts[0])
    rest = [a for a in arts if a is not lead]
    side = rest[:4]
    latest = rest[4:16]
    newest_day = arts[0]["published"]
    today_count = sum(1 for a in arts if a["published"] == newest_day)
    sections = ""
    for k in ORDER:
        items = [a for a in by_cat(k) if a is not lead][:3]
        if len(items) < 2:
            continue
        sections += f"""<section class="cat-section" style="{cat_style(k)}"><div class="block-head"><span class="cat-kicker">{ICONS[k]}{e(CATS[k][0])}</span><a class="see-all" href="rubrik/{k}.html">Alle {len(by_cat(k))} Beiträge</a></div>
<div class="grid three">{"".join(card(a, "") for a in items)}</div></section>"""
    tags = {}
    for a in arts:
        for t in a.get("tags", []):
            tags[t] = tags.get(t, 0) + 1
    tag_html = "".join(f'<a class="topic" href="suche.html#{e(t)}">{e(t)}<span>{n}</span></a>' for t, n in sorted(tags.items(), key=lambda x: (-x[1], x[0]))[:18])
    body = f"""<section class="hero"><span class="blob b1"></span><span class="blob b2"></span><div class="wrap">
  <div class="today"><span class="hand">Heute auf dem Radar</span><span class="today-date">{d_day(newest_day)} · {today_count} {"neuer Beitrag" if today_count == 1 else "neue Beiträge"}</span></div>
  <div class="hero-grid">
    <article class="lead-story" style="{cat_style(lead['category'])}">
      <a class="card-link" href="artikel/{lead['id']}.html" tabindex="-1" aria-hidden="true"></a>
      <div class="lead-cover">{cover(lead)}<span class="sticker">Top-Thema</span></div>
      <div class="lead-body">{meta(lead, '')}<h1><a href="artikel/{lead['id']}.html">{e(lead['title'])}</a></h1><p>{e(lead['teaser'])}</p><span class="btn">Ganzen Beitrag lesen</span></div>
    </article>
    <aside class="side-stories" aria-label="Weitere Top-Beiträge"><h2 class="hand">Ebenfalls wichtig</h2>{"".join(mini_row(a, "") for a in side)}</aside>
  </div>
</div></section>
<section class="block"><div class="wrap">
  <div class="block-head"><div><span class="hand">Frisch eingetroffen</span><h2>Neueste Beiträge</h2></div>{chips('#latest .card', {a['category'] for a in latest})}</div>
  <div class="grid" id="latest">{"".join(card(a, "") for a in latest)}</div>
</div></section>
{home_extras()}
{WAVE}
<section class="block band"><div class="wrap">
  <div class="block-head"><div><span class="hand">Zum Nachschlagen</span><h2>Auf einen Blick</h2></div><a class="see-all" href="aenderungen.html">Alle Änderungen</a></div>
  <div class="two">{kennzahlen_panel()}{termine_panel(6)}</div>
</div></section>
{WAVE_FLIP}
{home_background()}
<section class="block"><div class="wrap">
  <div class="block-head"><div><span class="hand">Nach Themen stöbern</span><h2>Die Rubriken</h2></div></div>
  {sections}
  <div class="topics-box"><h3>Beliebte Stichworte</h3><div class="topics">{tag_html}</div></div>
</div></section>"""
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL, "inLanguage": "de-CH",
           "description": DEFAULT_DESC, "publisher": PUBLISHER_LD,
           "potentialAction": {"@type": "SearchAction", "target": {"@type": "EntryPoint", "urlTemplate": SITE_URL + "suche.html?q={search_term_string}"}, "query-input": "required name=search_term_string"}},
          dict({"@context": "https://schema.org"}, **PUBLISHER_LD)]
    write("index.html", layout(SITE_NAME, body, 0, active="home", ld=ld))


COFFEE = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9h13v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M17 10h1.5a2.5 2.5 0 0 1 0 5H17"/><path d="M8 3v3M12 3v3"/></svg>'


def support_box(up):
    """Dezenter Unterstuetzen-Kasten. Erscheint erst, wenn site.support_url gesetzt ist."""
    if not SUPPORT_URL:
        return ""
    return f"""<aside class="support-box" aria-label="HR Radar unterstützen"><span class="icon">{COFFEE}</span><div><h2>Hat Ihnen dieser Beitrag geholfen?</h2><p>{e(SITE_NAME)} ist kostenlos, werbefrei und unabhängig. Wenn Sie die Arbeit daran unterstützen möchten, freuen wir uns über einen Kaffee.</p></div><a class="btn" href="{e(SUPPORT_URL)}" target="_blank" rel="noopener">Einen Kaffee spendieren</a></aside>"""


def build_support():
    if not SUPPORT_URL:
        return
    body = f"""<div class="narrow page">
<span class="eyebrow"><span class="pill">Unterstützen</span></span>
<h1>{e(SITE_NAME)} unterstützen</h1>
<p class="lead">{e(SITE_NAME)} ist kostenlos, ohne Werbung und ohne Paywall. Jeden Werktag fassen wir zusammen, was HR- und Legal-Verantwortliche in der Schweiz wissen müssen, immer mit Quellen.</p>
<p>Recherche, Hosting, Newsletter-Versand und die Pflege der Themenseiten und Rechner kosten Zeit und etwas Geld. Wenn Ihnen {e(SITE_NAME)} im Arbeitsalltag hilft, können Sie die Arbeit mit einem freiwilligen Beitrag unterstützen. Jeder Betrag hilft, auch ein einzelner Kaffee.</p>
<p><a class="btn red" href="{e(SUPPORT_URL)}" target="_blank" rel="noopener">Einen Kaffee spendieren</a></p>
<h2>Gut zu wissen</h2>
<ul><li>Die Zahlung läuft über Buy Me a Coffee. Wir sehen keine Kartendaten.</li><li>Der Beitrag ist freiwillig und an keine Gegenleistung gebunden. Alle Inhalte bleiben für alle frei zugänglich.</li><li>{e(SITE_NAME)} ist keine gemeinnützige Organisation. Beiträge sind deshalb nicht steuerlich abziehbar.</li></ul>
<p>Andere Wege, uns zu helfen: <a href="newsletter.html">Newsletter abonnieren</a> und {e(SITE_NAME)} Kolleginnen und Kollegen weiterempfehlen.</p>
</div>"""
    write("unterstuetzen.html", layout("Unterstützen", body, 0, desc=f"{SITE_NAME} ist kostenlos und werbefrei. Mit einem freiwilligen Beitrag unterstützen Sie die Arbeit an der Newsplattform für HR und Legal in der Schweiz."))


def build_article(a, draft=False):
    up = "../"
    k = a["category"]
    secs = "".join(f"<h2>{e(s['h'])}</h2><p>{e(s['p'])}</p>" for s in a.get("sections", []))
    tldr = f'<div class="tldr"><span class="hand">In 30 Sekunden</span><p>{e(a["summary"])}</p></div>' if a.get("sections") else f'<div class="body"><p>{e(a["summary"])}</p></div>'
    takeaways = "".join(f"<li>{e(t)}</li>" for t in a.get("takeaways", []))
    refs = "".join(f'<span class="ref">{e(r)}</span>' for r in a.get("refs", []))
    srcs = "".join(f'<li><a href="{e(s["url"])}" rel="noopener">{e(s["label"])}</a></li>' for s in a.get("sources", []))
    tags_html = "".join(f'<a class="topic" href="{up}suche.html#{e(t)}">{e(t)}</a>' for t in a.get("tags", []))
    related = [x for x in by_cat(k) if x["id"] != a["id"]][:3]
    if len(related) < 3:
        related += [x for x in articles() if x["id"] != a["id"] and x not in related][:3 - len(related)]
    event = f'<p class="event">Ereignis vom {d_long(a["date"])}</p>' if a.get("date") and a["date"] != a["published"] else ""
    refs_block = f'<p class="refs-label">Rechtsgrundlagen und Stichworte</p><div class="refs">{refs}</div>' if refs else ""
    themes_html = "".join(f'<a class="topic theme-link" href="{up}thema/{t["slug"]}.html">Themenseite: {e(t.get("short") or t["title"].split(":")[0])}</a>' for t in themes_for(a))
    practice_h = "Das heisst für Legal" if k == "legal" else "Das heisst für HR"
    banner = '<div class="draft-banner"><b>Entwurf, nicht veröffentlicht.</b> Diese Vorschau ist nur über den direkten Link erreichbar und erscheint nirgends auf der Seite.</div>' if draft else ""
    body = f"""{banner}<article class="post" style="{cat_style(k)}">
  <div class="post-hero"><div class="narrow">
    <div class="crumbs"><a href="{up}index.html">Aktuell</a> › <a href="{up}rubrik/{k}.html">{e(CATS[k][0])}</a></div>
    {meta(a, up, True)}
    <h1>{e(a['title'])}</h1>
    <p class="lead">{e(a['teaser'])}</p>
    {event}
  </div></div>
  <div class="narrow">
    <div class="post-cover">{cover(a)}</div>
    {tldr}
    <div class="body">{secs}</div>
    <div class="practice"><span class="icon">{BULB}</span><h2>{practice_h}</h2><ul>{takeaways}</ul></div>
    <section class="sources" aria-labelledby="q-h"><h2 id="q-h">Quellen</h2><ol>{srcs}</ol>{refs_block}</section>
    <div class="post-foot"><div class="topics">{themes_html}{tags_html}</div><button class="btn ghost" id="copy-link" type="button">{LINK}<span>Link kopieren</span></button></div>
    {support_box(up)}
  </div>
</article>
<section class="block band-soft"><div class="wrap"><div class="block-head"><div><span class="hand">Weiterlesen</span><h2>Das könnte Sie auch interessieren</h2></div></div>
<div class="grid three">{"".join(card(x, up) for x in related)}</div></div></section>"""
    if draft:
        write(f"vorschau/{a['id']}.html", layout("Entwurf: " + a["title"], body, 1, desc=a["teaser"][:160], article=True, noindex=True))
    else:
        url = f"{SITE_URL}artikel/{a['id']}.html"
        mod = a.get("updated", a["published"])
        LASTMOD[f"artikel/{a['id']}.html"] = mod
        art_ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": a["title"][:110],
                  "description": a["teaser"], "datePublished": a["published"], "dateModified": mod,
                  "inLanguage": "de-CH", "articleSection": CATS[k][0], "keywords": ", ".join(a.get("tags", [])),
                  "image": [og_image(k)], "mainEntityOfPage": url,
                  "author": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL}, "publisher": PUBLISHER_LD,
                  "isAccessibleForFree": True, "citation": [s["url"] for s in a.get("sources", [])]}
        crumbs = breadcrumb([("Aktuell", SITE_URL), (CATS[k][0], f"{SITE_URL}rubrik/{k}.html"), (a["title"], url)])
        extra = f'<meta property="article:published_time" content="{a["published"]}">\n<meta property="article:modified_time" content="{mod}">\n<meta property="article:section" content="{e(CATS[k][0])}">\n' + "".join(f'<meta property="article:tag" content="{e(t)}">\n' for t in a.get("tags", []))
        desc = (a["teaser"] if len(a["teaser"]) <= 160 else a["teaser"][:157].rsplit(" ", 1)[0] + " …")
        write(f"artikel/{a['id']}.html", layout(a["title"], body, 1, desc=desc, article=True, ld=[art_ld, crumbs], og_type="article", cat=k, extra_head=extra))


def build_category(k):
    up = "../"
    items = by_cat(k)
    body = f"""<section class="cat-hero" style="{cat_style(k)}"><span class="blob b1"></span><div class="wrap">
  <span class="cat-big" aria-hidden="true">{ICONS[k]}</span>
  <div><span class="hand">Rubrik</span><h1>{e(CATS[k][0])}</h1><p class="lead">{e(CATS[k][2])}</p><p class="count">{len(items)} Beiträge</p></div>
</div></section>
<section class="block"><div class="wrap"><div class="grid">{"".join(card(a, up) for a in items) or '<p class="empty">Noch keine Beiträge in dieser Rubrik. Schauen Sie bald wieder vorbei.</p>'}</div></div></section>"""
    url = f"{SITE_URL}rubrik/{k}.html"
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": CATS[k][0], "description": CATS[k][2], "url": url, "inLanguage": "de-CH",
           "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{SITE_URL}artikel/{a['id']}.html"} for i, a in enumerate(items[:20])]}},
          breadcrumb([("Aktuell", SITE_URL), (CATS[k][0], url)])]
    write(f"rubrik/{k}.html", layout(CATS[k][0], body, 1, desc=CATS[k][2] + " Alle Beiträge mit Quellen.", active="rubrik-" + k, ld=ld, cat=k))


def week_top(items, n=5):
    return sorted(items, key=lambda a: (a.get("featured", False), len(a.get("sources", [])), a["published"]), reverse=True)[:n]


def weeks_map():
    m = {}
    for a in articles():
        m.setdefault(tools.iso_week(a["published"]), []).append(a)
    return m


def home_extras():
    wm = weeks_map()
    wid = max(wm)
    mon, sun = tools.week_range(wid)
    top = week_top(wm[wid], 3)
    lis = "".join(f'<li><a href="artikel/{a["id"]}.html">{e(a["title"])}</a></li>' for a in top)
    calc = "".join(f'<a class="tool-chip" href="rechner/{k}.html" style="{cat_style(c)}">{ICONS[c]}{e(t)}</a>' for k, t, _, c in tools.RECHNER)
    y, w = wid.split("-")
    return f"""<section class="block"><div class="wrap"><div class="extras">
  <a class="extra-card week-card" href="woche/{wid}.html"><span class="hand">Die Woche im HR</span><h3>KW {int(w)}/{y}: Das Wichtigste</h3><ol>{lis}</ol><span class="more">Zum Wochenrückblick</span></a>
  <div class="extra-card tools-card"><span class="hand">Werkzeugkiste</span><h3>HR-Rechner</h3><p>Fristen, Lohnfortzahlung, Ferien und BVG in Sekunden berechnet.</p><div class="tool-chips">{calc}</div></div>
</div></div></section>"""


def build_changes():
    today = date.today().isoformat()
    entries = []
    for a in articles():
        if a.get("effective") and a["effective"] >= today:
            entries.append({"date": a["effective"], "label": a["title"], "href": f"artikel/{a['id']}.html", "cat": a["category"], "text": a["teaser"]})
    for t in DATA.get("termine", []):
        if t["date"] >= today:
            entries.append({"date": t["date"], "label": t["label"], "href": "", "cat": "", "text": ""})
    entries.sort(key=lambda x: (x["date"], x["href"] == ""))
    months = {}
    for en in entries:
        months.setdefault(en["date"][:7], []).append(en)
    blocks = ""
    for ym in sorted(months):
        y, m = ym.split("-")
        rows = ""
        for en in months[ym]:
            if en["href"]:
                rows += f'<li class="chg-item" style="{cat_style(en["cat"])}">{cal(en["date"])}<div><span class="mini-cat">{e(CATS[en["cat"]][1])} · gilt ab {d_short(en["date"])}</span><a href="{en["href"]}"><b>{e(en["label"])}</b></a><p>{e(en["text"])}</p></div></li>'
            else:
                rows += f'<li class="chg-item termin">{cal(en["date"])}<div><span class="mini-cat">Termin · {d_short(en["date"])}</span><b>{e(en["label"])}</b></div></li>'
        blocks += f'<section class="chg-month"><h2 class="hand">{MONTHS[int(m) - 1]} {y}</h2><ul class="chg-list">{rows}</ul></section>'
    body = f"""<section class="cat-hero chg-hero"><span class="blob b1"></span><div class="wrap">
  <span class="cat-big" aria-hidden="true">{ICONS['gesetze']}</span>
  <div><span class="hand">Zeitleiste</span><h1>Das ändert sich</h1><p class="lead">Alle kommenden Inkrafttreten, Fristen und Termine für HR auf einen Blick, nach Monat geordnet. Zum Ausdrucken für Lohnbuchhaltung und Geschäftsleitung.</p>
  <div class="btn-row no-print"><button class="btn" id="print-btn" type="button">Seite drucken</button><a class="btn ghost" href="rubrik/gesetze.html">Alle Gesetzesbeiträge</a></div></div>
</div></section>
<div class="narrow page">{blocks or '<p class="empty">Aktuell sind keine kommenden Änderungen erfasst.</p>'}
<p class="hint">Stand {d_long(DATA['updated'])}. Die Übersicht wird mit jedem neuen Beitrag automatisch aktualisiert. Massgebend sind die verlinkten Quellen.</p></div>"""
    write("aenderungen.html", layout("Das ändert sich", body, 0, desc="Alle kommenden Gesetzesänderungen, Inkrafttreten und Fristen für HR in der Schweiz auf einen Blick.", active="aenderungen"))


def build_weeks():
    up = "../"
    wm = weeks_map()
    intros = {w["id"]: w for w in DATA.get("weeks", [])}
    rows = ""
    for wid in sorted(wm, reverse=True):
        items = wm[wid]
        mon, sun = tools.week_range(wid)
        y, w = wid.split("-")
        top = week_top(items)
        ed = intros.get(wid, {})
        intro = ed.get("intro") or f"Diese Woche sind {len(items)} Beiträge erschienen. Hier die fünf wichtigsten im Überblick."
        top_html = "".join(f'<li class="wk-top" style="{cat_style(a["category"])}"><span class="wk-num">{i + 1}</span><div><span class="mini-cat">{e(CATS[a["category"]][1])}</span><a href="{up}artikel/{a["id"]}.html"><b>{e(a["title"])}</b></a><p>{e(a["summary"])}</p></div></li>' for i, a in enumerate(top))
        others = [a for a in items if a not in top]
        rest = f'<h2>Alle weiteren Beiträge der Woche</h2><div class="day-list">{"".join(mini_row(a, up) for a in others)}</div>' if others else ""
        title = f"Die Woche im HR: KW {int(w)}/{y}"
        body = f"""<div class="narrow page">
<div class="crumbs"><a href="{up}index.html">Aktuell</a> › <a href="index.html">Wochenrückblicke</a></div>
<span class="eyebrow"><span class="pill">KW {int(w)}/{y}</span>{d_short(mon.isoformat())} bis {d_short(sun.isoformat())}</span>
<h1>{e(ed.get('title') or 'Die Woche im HR')}</h1>
<p class="lead">{e(intro)}</p>
<h2 class="hand top5">Die Top {len(top)} der Woche</h2>
<ol class="wk-list">{top_html}</ol>
{rest}
</div>"""
        write(f"woche/{wid}.html", layout(title, body, 1, desc=intro[:160], active="woche"))
        first = ed.get("title") or (top[0]["title"] if top else "")
        rows += f'<a class="list-row" href="{wid}.html"><div class="meta"><span class="pill-s">KW {int(w)}/{y}</span><span>{d_short(mon.isoformat())} bis {d_short(sun.isoformat())}</span><span class="dot-sep">{len(items)} Beiträge</span></div><h3>{e(first)}</h3><p>{e(intro)}</p></a>'
    body = f"""<div class="narrow page">
<span class="eyebrow"><span class="pill">Wochenrückblick</span></span>
<h1>Die Woche im HR</h1>
<p class="lead">Keine Zeit, jeden Tag reinzuschauen? Jede Woche fassen wir die wichtigsten Beiträge zusammen. Die aktuelle Woche wird laufend ergänzt, am Freitag erscheint die Einordnung der Redaktion.</p>
{rows}
</div>"""
    write("woche/index.html", layout("Wochenrückblicke", body, 1, active="woche"))


def build_calculators():
    up = "../"
    cards = ""
    for k, title, desc, c in tools.RECHNER:
        form, js, refs = tools.CALCS[k]
        others = "".join(f'<a class="tool-chip" href="{kk}.html" style="{cat_style(cc)}">{ICONS[cc]}{e(tt)}</a>' for kk, tt, _, cc in tools.RECHNER if kk != k)
        related = [t for t in THEMEN if k in t.get("tools", [])]
        related_html = ("<h2>Mehr zum Thema</h2><div class=\"tool-chips\">" + "".join(f'<a class="tool-chip" href="{up}thema/{t["slug"]}.html" style="{cat_style(t.get("category", "praxis"))}">{ICONS[t.get("category", "praxis")]}{e(t["title"])}</a>' for t in related) + "</div>") if related else ""
        body = f"""<section class="cat-hero" style="{cat_style(c)}"><span class="blob b1"></span><div class="wrap">
  <span class="cat-big" aria-hidden="true">{ICONS[c]}</span>
  <div><div class="crumbs"><a href="{up}index.html">Aktuell</a> › <a href="index.html">Rechner</a></div><h1>{e(title)}</h1><p class="lead">{e(desc)}</p></div>
</div></section>
<div class="narrow page calc-page" style="{cat_style(c)}">
{form}
<div class="calc-note"><p><b>Wichtig:</b> Der Rechner bildet die gesetzliche Grundregel ab und dient der ersten Orientierung. Vertrag, Reglement, GAV und Einzelfall können zu anderen Ergebnissen führen. Keine Rechtsberatung.</p>
<p class="refs-label">Rechtsgrundlagen</p><div class="refs">{"".join(f'<span class="ref">{e(r)}</span>' for r in refs)}</div></div>
{related_html}
<h2>Weitere Rechner</h2><div class="tool-chips">{others}</div>
</div>
<script>{tools.JS_HELPERS}{js}</script>"""
        write(f"rechner/{k}.html", layout(title, body, 1, desc=desc, active="rechner"))
        cards += f'<a class="tool-card" href="{k}.html" style="{cat_style(c)}"><span class="mini-ico" aria-hidden="true">{ICONS[c]}</span><h3>{e(title)}</h3><p>{e(desc)}</p><span class="more">Rechner öffnen</span></a>'
    body = f"""<section class="cat-hero chg-hero"><span class="blob b1"></span><div class="wrap">
  <span class="cat-big" aria-hidden="true">{ICONS['digital']}</span>
  <div><span class="hand">Werkzeugkiste</span><h1>HR-Rechner</h1><p class="lead">Die häufigsten Fragen aus dem HR-Alltag in Sekunden beantwortet, mit Erklärung jedes Rechenschritts und den gesetzlichen Grundlagen.</p></div>
</div></section>
<section class="block"><div class="wrap"><div class="tool-grid">{cards}</div></div></section>"""
    write("rechner/index.html", layout("HR-Rechner", body, 1, desc="Kostenlose HR-Rechner für die Schweiz: Kündigungsfrist und Sperrfrist, Lohnfortzahlung, Ferien pro rata, BVG.", active="rechner"))


def build_archive():
    days = {}
    for a in articles():
        days.setdefault(a["published"], []).append(a)
    blocks = ""
    for day in sorted(days, reverse=True):
        rows = "".join(mini_row(a, "") for a in days[day])
        blocks += f'<section class="day"><h2 class="hand">{d_day(day)}</h2><div class="day-list">{rows}</div></section>'
    body = f"""<div class="narrow page">
<span class="eyebrow"><span class="pill">Archiv</span>{len(DATA['articles'])} Beiträge</span>
<h1>Alle Beiträge nach Datum</h1>
<p class="lead">Jeden Tag kommt mindestens ein neuer Beitrag dazu. Hier finden Sie alles, was bisher erschienen ist.</p>
{blocks}
</div>"""
    write("archiv.html", layout("Archiv", body, 0, active="archiv"))


def build_search():
    index = [{"id": a["id"], "t": a["title"], "x": a["teaser"], "c": a["category"], "cn": CATS[a["category"]][1],
              "g": a.get("tags", []), "r": a.get("refs", []), "d": a["published"]} for a in articles()]
    write("search.json", json.dumps(index, ensure_ascii=False))
    colors = json.dumps({k: [f"var(--cc-{k})", f"var(--cb-{k})"] for k in PALETTE})
    body = f"""<div class="narrow page">
<span class="eyebrow"><span class="pill">Suche</span></span>
<h1>Was suchen Sie?</h1>
<div class="search-box">{SEARCH}<input type="search" id="q" placeholder="z.B. Kündigung, BVG, KI, Art. 336 OR" aria-label="Beiträge durchsuchen" autocomplete="off"></div>
<p class="search-status" id="status" aria-live="polite"></p>
<div id="results" class="day-list"></div>
</div>
<script>
(function () {{
  var COLORS = {colors};
  var input = document.getElementById('q'), out = document.getElementById('results'), status = document.getElementById('status');
  var data = [];
  function render() {{
    var q = input.value.trim().toLowerCase();
    out.textContent = '';
    if (!q) {{ status.textContent = data.length + ' Beiträge durchsuchbar.'; return; }}
    var hits = data.filter(function (a) {{
      return [a.t, a.x, a.cn, a.g.join(' '), a.r.join(' ')].join(' ').toLowerCase().indexOf(q) !== -1;
    }});
    status.textContent = hits.length ? hits.length + ' Treffer' : 'Keine Treffer. Versuchen Sie einen anderen Begriff.';
    hits.forEach(function (a) {{
      var link = document.createElement('a');
      link.className = 'mini-row'; link.href = 'artikel/' + a.id + '.html';
      link.style.setProperty('--catc', COLORS[a.c][0]); link.style.setProperty('--catb', COLORS[a.c][1]);
      var wrap = document.createElement('span');
      var cat = document.createElement('span'); cat.className = 'mini-cat'; cat.textContent = a.cn;
      var b = document.createElement('b'); b.textContent = a.t;
      var p = document.createElement('span'); p.className = 'mini-teaser'; p.textContent = a.x;
      wrap.appendChild(cat); wrap.appendChild(b); wrap.appendChild(p); link.appendChild(wrap); out.appendChild(link);
    }});
  }}
  input.addEventListener('input', render);
  fetch('search.json').then(function (r) {{ return r.json(); }}).then(function (d) {{
    data = d;
    var qp = new URLSearchParams(location.search).get('q');
    if (qp) {{ input.value = qp; }} else if (location.hash) {{ input.value = decodeURIComponent(location.hash.slice(1)); }}
    render();
  }}).catch(function () {{ status.textContent = 'Die Suche konnte nicht geladen werden. Bitte laden Sie die Seite neu.'; }});
}})();
</script>"""
    write("suche.html", layout("Suche", body, 0, active="suche"))


def background_articles():
    return [a for a in articles() if a.get("type") == "hintergrund"]


def home_background():
    items = background_articles()[:3]
    if not items:
        return ""
    return f"""<section class="block"><div class="wrap"><div class="bg-box">
<div class="block-head"><div><span class="hand">Tiefer eintauchen</span><h2>Hintergrund &amp; Analyse</h2></div><a class="see-all" href="hintergrund.html">Alle Hintergrundartikel</a></div>
<div class="grid three">{"".join(card(a, "") for a in items)}</div></div></div></section>"""


def build_background_page():
    items = background_articles()
    body = f"""<section class="cat-hero bg-hero"><span class="blob b1"></span><div class="wrap">
  <span class="cat-big" aria-hidden="true">{BOOK}</span>
  <div><span class="hand">Tiefer eintauchen</span><h1>Hintergrund &amp; Analyse</h1><p class="lead">Ausführliche Beiträge zu den grossen HR-Themen: Zusammenhänge, Rechtslage, Praxisbeispiele und Checklisten. Jeder Hintergrundartikel wird vor der Veröffentlichung redaktionell geprüft.</p><p class="count">{len(items)} Beiträge</p></div>
</div></section>
<section class="block"><div class="wrap"><div class="grid">{"".join(card(a, "") for a in items) or '<p class="empty">Der erste Hintergrundartikel erscheint in Kürze.</p>'}</div></div></section>"""
    write("hintergrund.html", layout("Hintergrund & Analyse", body, 0, desc="Ausführliche Hintergrundartikel zu HR-Themen in der Schweiz.", active="hintergrund"))


def build_drafts():
    ddir = os.path.join(ROOT, "data", "drafts")
    n = 0
    if os.path.isdir(ddir):
        for name in sorted(os.listdir(ddir)):
            if name.endswith(".json"):
                a = json.load(open(os.path.join(ddir, name), encoding="utf-8"))
                build_article(a, draft=True)
                n += 1
    return n


def upcoming_list():
    today = date.today().isoformat()
    items = [(a["effective"], a["title"]) for a in articles() if a.get("effective") and a["effective"] >= today]
    items += [(t["date"], t["label"]) for t in DATA.get("termine", []) if t["date"] >= today]
    return sorted(items)


def build_newsletter_archive():
    up = "../../"
    issues = sorted(DATA.get("newsletters", []), key=lambda i: i["date"], reverse=True)
    rows = ""
    for i in issues:
        html_web = nl.build_issue_html(i, articles(), CATS, PALETTE, ORDER, SITE_NAME, SITE_URL, upcoming_list(), personalized=False)
        html_web = html_web.replace('<a href="{{ unsubscribe }}" style="color:#6b6580;">Newsletter abbestellen</a>', f'<a href="{SITE_URL}newsletter.html" style="color:#6b6580;">Newsletter abonnieren</a>')
        write(f"newsletter/archiv/{i['id']}.html", html_web)
        rows += f'<a class="list-row" href="newsletter/archiv/{i["id"]}.html"><div class="meta"><span class="pill-s">{e(i["label"])}</span><span>{d_long(i["date"])}</span></div><h3>{e(i.get("title") or "Newsletter")}</h3><p>{e(i.get("intro", ""))}</p></a>'
    return rows


def build_newsletter():
    archive_rows = build_newsletter_archive()
    interests = "".join(
        f'<label class="interest" style="{cat_style(k)}"><span class="mini-ico" aria-hidden="true">{ICONS[k]}</span><div><b>{e(v[0])}</b><span>{e(v[2])}</span></div><input type="checkbox" name="{nl.ATTR[k]}" value="1" checked></label>'
        for k, v in CATS.items())
    if NL_ACTION:
        action, notice, disabled = f'action="{e(NL_ACTION)}" method="post"', "", ""
    else:
        action = 'action="#" onsubmit="return false"'
        notice = '<p class="notice">Der Newsletter startet in Kürze. Bis dahin finden Sie alle Beiträge hier auf der Seite und im <a href="feed.xml">RSS-Feed</a>.</p>'
        disabled = " disabled"
    archive = f'<h2>Bisherige Ausgaben</h2>{archive_rows}' if archive_rows else ""
    body = f"""<div class="narrow page">
<span class="eyebrow"><span class="pill">Newsletter</span>jeden Dienstag</span>
<h1>Ihr persönlicher HR Radar</h1>
<p class="lead">Jeden Dienstag die wichtigsten HR-News der Woche, nur aus den Rubriken, die Sie wählen. Und wenn etwas wirklich Wichtiges passiert, auf Wunsch sofort eine Eilmeldung.</p>
<div class="nl-points"><div><b>Jeden Dienstag</b><span>am Morgen, kompakt, mit Link zu jedem Beitrag</span></div><div><b>Nur Ihre Themen</b><span>Sie wählen die Rubriken, der Rest bleibt draussen</span></div><div><b>Eilmeldungen</b><span>nur bei Entscheiden mit grosser Tragweite für HR</span></div></div>
{notice}
<div class="nl-gift" id="anmelden"><b>Dankeschön für neue Abonnentinnen und Abonnenten:</b> die <a href="thema/jahreswechsel-checkliste-2027.html">Jahreswechsel-Checkliste 2027</a> für HR und Legal als PDF.</div>
<form class="nl" {action}>
  <div class="field"><label for="nl-email">E-Mail-Adresse</label><input type="email" id="nl-email" name="EMAIL" required autocomplete="email" placeholder="vorname.name@firma.ch"></div>
  <div class="field"><label for="nl-name">Vorname (optional)</label><input type="text" id="nl-name" name="VORNAME" autocomplete="given-name"></div>
  <fieldset><legend>Welche Rubriken interessieren Sie?</legend><div class="interest-grid">{interests}</div></fieldset>
  <label class="interest alert-opt"><span class="mini-ico" aria-hidden="true">{ICONS['gesetze']}</span><div><b>Eilmeldungen</b><span>Sofort informiert bei sehr wichtigen Entscheiden, etwa einem wegweisenden Urteil oder einer kurzfristigen Gesetzesänderung. Höchstens wenige Male pro Jahr.</span></div><input type="checkbox" name="{nl.ALERT_ATTR}" value="1" checked></label>
  <label class="consent"><input type="checkbox" id="nl-consent" name="OPT_IN" value="1" required><span>Ich möchte den Newsletter erhalten und bin einverstanden, dass meine E-Mail-Adresse, mein Vorname und meine Themenwahl dafür gespeichert und vom Versanddienst Brevo verarbeitet werden. Abmelden ist jederzeit über den Link in jeder E-Mail möglich.</span></label>
  <input type="text" name="email_address_check" value="" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;opacity:0">
  <input type="hidden" name="locale" value="de"><input type="hidden" name="html_type" value="simple">
  <div><button class="btn red" type="submit"{disabled}>Newsletter abonnieren</button></div>
  <p class="nl-hint">Nach dem Absenden erhalten Sie eine E-Mail mit einem Bestätigungslink. Erst nach dem Klick darauf ist die Anmeldung aktiv.</p>
</form>
{support_box("")}
{archive}
</div>"""
    write("newsletter.html", layout("Newsletter", body, 0, active="newsletter", desc="Der HR Radar Newsletter: jeden Dienstag die wichtigsten News zu Arbeitsrecht, HR und Legal in der Schweiz, nur aus den Rubriken, die Sie wählen. Kostenlos, jederzeit abbestellbar."))
    GIFT = """<div class="pdf-cta"><div><b>Ihr Dankeschön: Jahreswechsel-Checkliste 2027</b><p>Alles, was HR, Lohn und Legal zum Jahreswechsel erledigen müssen, zum Ausdrucken und Abhaken.</p></div><a class="btn red" href="assets/downloads/hr-radar-jahreswechsel-checkliste-2027.pdf" download>PDF herunterladen</a></div>"""
    for slug, title, lead, text in (
        ("newsletter-danke", "Fast geschafft: Bitte bestätigen Sie Ihre Anmeldung",
         "Wir haben Ihnen eine E-Mail mit einem Bestätigungslink geschickt.",
         "Klicken Sie auf den Link in dieser E-Mail, damit Ihre Anmeldung aktiv wird. Sie finden die E-Mail nicht? Schauen Sie im Spam- oder Werbeordner nach. Die E-Mail kommt von newsletter@hr-radar.ch."),
        ("newsletter-bestaetigt", "Willkommen beim HR Radar Newsletter",
         "Ihre Anmeldung ist bestätigt. Danke für Ihr Interesse!",
         "Die nächste Ausgabe kommt am Dienstagmorgen in Ihr Postfach, mit den Themen, die Sie gewählt haben. Bis dahin finden Sie alle aktuellen Beiträge hier auf der Seite.")):
        page = f"""<div class="narrow page"><span class="eyebrow"><span class="pill">Newsletter</span></span>
<h1>{e(title)}</h1><p class="lead">{e(lead)}</p><p>{e(text)}</p>
{GIFT if slug == "newsletter-bestaetigt" else ""}
<p><a class="btn" href="index.html">Zu den aktuellen Beiträgen</a> <a class="btn ghost" href="thema/index.html">Themen</a></p></div>"""
        write(f"{slug}.html", layout(title, page, 0, active="newsletter", noindex=True))


def build_about():
    RUBRIK_WORT = {7: "Sieben", 8: "Acht", 9: "Neun", 10: "Zehn"}.get(len(CATS), str(len(CATS)))
    cats = "".join(f'<li style="{cat_style(k)}"><span class="mini-ico" aria-hidden="true">{ICONS[k]}</span><div><b>{e(v[0])}</b><span>{e(v[2])}</span></div></li>' for k, v in CATS.items())
    body = f"""<div class="narrow page">
<span class="eyebrow"><span class="pill">Über</span></span>
<h1>Was HR heute wissen muss</h1>
<p class="lead">{e(SITE_NAME)} ist die Newsplattform für HR-Leiterinnen, HR-Leiter und HR-Fachleute in der Schweiz. Jeden Werktag fassen wir zusammen, was sich bewegt: neue Urteile, Gesetze, Zahlen, Studien und Trends, dazu in der Rubrik Legal die wichtigsten Rechtsänderungen für Unternehmen und KMU.</p>
<h2>{RUBRIK_WORT} Rubriken</h2><ul class="cat-list">{cats}</ul>
<h2>Themenseiten</h2><p>Für die häufigsten Fragen gibt es <a href="thema/index.html">Themenseiten</a> mit den Grundlagen, häufigen Fragen, Rechnern und allen aktuellen Beiträgen.</p>
<h2>So entstehen die Beiträge</h2>
<p>Grundlage sind öffentlich zugängliche Quellen: Urteile, Medienmitteilungen von Bund und Kantonen, Studien, Fachpublikationen und Medienberichte. Die Inhalte werden mit KI-Unterstützung recherchiert, in eigenen Worten zusammengefasst und redaktionell zusammengestellt. Jeder Beitrag nennt seine Quellen, damit Sie das Original nachlesen können.</p>
<h2>Keine Rechtsberatung</h2>
<p>Die Beiträge dienen der allgemeinen Information und ersetzen keine Beratung im Einzelfall. Trotz sorgfältiger Prüfung wird keine Gewähr für Vollständigkeit, Richtigkeit und Aktualität übernommen.</p>
{f"<h2>Impressum</h2><p>Herausgeber: {e(PUBLISHER)}</p>" if HAS_PUBLISHER else ""}
{"<h2>Datenschutz</h2><p>Wir zählen Seitenaufrufe anonym mit GoatCounter, um zu sehen, welche Beiträge gelesen werden. Dabei werden keine Cookies gesetzt und keine Personendaten gespeichert. Die Newsletter-Anmeldung läuft über Brevo, Beiträge zur Unterstützung über Buy Me a Coffee.</p>" if GOATCOUNTER else ""}
</div>"""
    write("ueber.html", layout("Über", body, 0, active="ueber"))


def rss(path, title, items):
    def rfc(iso):
        return format_datetime(datetime.strptime(iso, "%Y-%m-%d").replace(hour=6))
    entries = ""
    for a in items:
        link = f"{SITE_URL}artikel/{a['id']}.html"
        desc = f"<p>{e(a['teaser'])}</p>"
        entries += f"""<item><title>{e(a['title'])}</title><link>{link}</link><guid isPermaLink="true">{link}</guid>
<pubDate>{rfc(a['published'])}</pubDate><category>{e(CATS[a['category']][0])}</category><description>{e(desc)}</description></item>
"""
    write(path, f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{e(title)}</title><link>{SITE_URL}</link>
<description>Täglich das Wichtigste für HR-Profis in der Schweiz</description><language>de-ch</language>
<lastBuildDate>{rfc(DATA['updated'])}</lastBuildDate>
{entries}</channel></rss>
""")


def build_feeds():
    arts = articles()[:80]
    rss("feed.xml", SITE_NAME, arts)
    for k, v in CATS.items():
        rss(f"feeds/{k}.xml", f"{SITE_NAME}: {v[0]}", [a for a in arts if a["category"] == k])


# ---------- Themenseiten (Landingpages) und SEO-Dateien ----------

def neuerungen_year():
    t = date.today()
    return t.year + 1 if t.month >= 9 else t.year


def neuerungen_slug():
    return f"neuerungen-{neuerungen_year()}"


def themes_for(a):
    tags = {x.lower() for x in a.get("tags", [])}
    title = a["title"].lower()
    by_tag, by_word = [], []
    for t in THEMEN:
        m = t.get("match", {})
        if tags & {x.lower() for x in m.get("tags", [])}:
            by_tag.append(t)
        elif any(w.lower() in title for w in m.get("words", [])):
            by_word.append(t)
    return (by_tag + by_word)[:3]


def theme_articles(t):
    return [a for a in articles() if t in themes_for(a) or t["slug"] in [x["slug"] for x in themes_for(a)]]


def build_themes():
    up = "../"
    import tools
    calc = {r[0]: r for r in tools.RECHNER}
    cards = ""
    for t in THEMEN:
        k = t.get("category", "praxis")
        items = theme_articles(t)
        url = f"{SITE_URL}thema/{t['slug']}.html"
        secs = "".join(f"<h2>{e(x['h'])}</h2><p>{e(x['p'])}</p>" for x in t.get("sections", []))
        art_ids = {a["id"] for a in articles()}
        theme_slugs = {x["slug"] for x in THEMEN}
        for grp in t.get("checklist", []):
            lis = ""
            for it in grp["items"]:
                links = []
                if it.get("a") in art_ids:
                    links.append(f'<a href="{up}artikel/{it["a"]}.html">Zum Beitrag</a>')
                if it.get("th") in theme_slugs:
                    links.append(f'<a href="{it["th"]}.html">Zum Thema</a>')
                more = f' <span class="cl-links">{" · ".join(links)}</span>' if links else ""
                lis += f'<li><label><input type="checkbox"><span><b>{e(it["t"])}</b>{(" – " + e(it["d"])) if it.get("d") else ""}{more}</span></label></li>'
            secs += f'<h2>{e(grp["h"])}</h2><ul class="checklist">{lis}</ul>'
        if t.get("pdf"):
            secs = f"""<div class="pdf-cta"><div><b>Die Checkliste als PDF</b><p>Zum Ausdrucken und Abhaken im Team. Sie erhalten das PDF als Dankeschön, wenn Sie den HR Radar Newsletter abonnieren – jeden Dienstag die wichtigsten News für HR und Legal.</p></div><a class="btn red" href="{up}newsletter.html#anmelden">Newsletter abonnieren und PDF erhalten</a></div>""" + secs
        faq = "".join(f'<details class="faq-item"><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>' for f in t.get("faq", []))
        tools_html = "".join(f'<a class="tool-card" href="{up}rechner/{c}.html" style="{cat_style(calc[c][3])}"><span class="mini-ico" aria-hidden="true">{ICONS[calc[c][3]]}</span><h3>{e(calc[c][1])}</h3><p>{e(calc[c][2])}</p><span class="more">Rechner öffnen</span></a>' for c in t.get("tools", []) if c in calc)
        refs = "".join(f'<span class="ref">{e(r)}</span>' for r in t.get("refs", []))
        others = "".join(f'<a class="topic" href="{x["slug"]}.html">{e(x.get("short") or x["title"].split(":")[0])}</a>' for x in THEMEN if x is not t)
        grid = "".join(card(a, up) for a in items[:12]) or '<p class="empty">Zu diesem Thema erscheinen laufend neue Beiträge.</p>'
        body = f"""<section class="cat-hero" style="{cat_style(k)}"><span class="blob b1"></span><div class="wrap">
  <span class="cat-big" aria-hidden="true">{ICONS[k]}</span>
  <div><div class="crumbs"><a href="{up}index.html">Aktuell</a> › <a href="index.html">Themen</a></div><span class="hand">Thema</span><h1>{e(t['title'])}</h1><p class="lead">{e(t['intro'])}</p>{f'<p class="count">{len(items)} {"Beitrag" if len(items) == 1 else "Beiträge"} zum Thema</p>' if items else ""}</div>
</div></section>
<div class="narrow theme-body" style="{cat_style(k)}">
  <div class="body">{secs}</div>
  {f'<p class="refs-label">Rechtsgrundlagen</p><div class="refs">{refs}</div>' if refs else ''}
  {f'<h2>Häufige Fragen</h2><div class="faq">{faq}</div>' if faq else ''}
  {f'<h2>Passender Rechner</h2><div class="tool-grid">{tools_html}</div>' if tools_html else ''}
  <p class="theme-note">Allgemeine Information, keine Rechtsberatung. Massgebend sind Gesetz, Vertrag, GAV und die Umstände des Einzelfalls. Stand: {d_short(DATA['updated'])}.</p>
</div>
<section class="block band-soft"><div class="wrap"><div class="block-head"><div><span class="hand">Aktuell</span><h2>Beiträge zum Thema</h2></div></div>
<div class="grid">{grid}</div>
<div class="topics more-themes"><b>Weitere Themen:</b> {others}</div></div></section>"""
        ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": t["title"], "description": t["description"], "url": url, "inLanguage": "de-CH",
               "dateModified": DATA["updated"], "publisher": PUBLISHER_LD, "about": t.get("refs", [])}, breadcrumb([("Aktuell", SITE_URL), ("Themen", SITE_URL + "thema/"), (t["title"], url)])]
        if t.get("faq"):
            ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in t["faq"]]})
        write(f"thema/{t['slug']}.html", layout(t.get("seo_title", t["title"]), body, 1, desc=t["description"], active="themen", ld=ld, cat=k))
        cards += f'<a class="tool-card" href="{t["slug"]}.html" style="{cat_style(k)}"><span class="mini-ico" aria-hidden="true">{ICONS[k]}</span><h3>{e(t["title"])}</h3><p>{e(t["description"])}</p><span class="more">{(str(len(items)) + (" Beitrag" if len(items) == 1 else " Beiträge") + " · ") if items else ""}Thema öffnen</span></a>'
    # Neuerungen des kommenden Jahres
    y = str(neuerungen_year())
    entries = []
    for a in articles():
        if (a.get("effective") or "").startswith(y):
            entries.append((a["effective"], a["title"], f"{up}artikel/{a['id']}.html", a["category"], a["teaser"]))
    for tm in DATA.get("termine", []):
        if tm["date"].startswith(y):
            entries.append((tm["date"], tm["label"], "", "", ""))
    entries.sort(key=lambda x: (x[0], x[2] == ""))
    rows = ""
    for dt, label, href, c, txt in entries:
        st = cat_style(c) if c else ""
        kicker = f'{e(CATS[c][1])} · ' if c else ""
        inner = f'<a href="{href}"><b>{e(label)}</b></a><p>{e(txt)}</p>' if href else f'<b>{e(label)}</b>'
        rows += f'<li class="chg-item" style="{st}">{cal(dt)}<div><span class="mini-cat">{kicker}ab {d_short(dt)}</span>{inner}</div></li>'
    nurl = f"{SITE_URL}thema/{neuerungen_slug()}.html"
    body = f"""<section class="cat-hero chg-hero"><span class="blob b1"></span><div class="wrap">
  <span class="cat-big" aria-hidden="true">{ICONS['gesetze']}</span>
  <div><div class="crumbs"><a href="{up}index.html">Aktuell</a> › <a href="index.html">Themen</a></div><span class="hand">Jahreswechsel</span><h1>Neuerungen {y}: Was sich für HR und Unternehmen ändert</h1><p class="lead">Alle Gesetzesänderungen, neuen Werte und Fristen {y} für Arbeitgeber, HR und Legal in der Schweiz auf einen Blick, chronologisch und mit Link zum ausführlichen Beitrag.</p><p class="count">{len(entries)} Einträge</p></div>
</div></section>
<section class="block"><div class="narrow"><ul class="chg-list">{rows or '<li>Noch keine Einträge.</li>'}</ul>
<p class="theme-note">Laufend ergänzt. Die vollständige Zeitleiste über alle Jahre finden Sie unter <a href="{up}aenderungen.html">Das ändert sich</a>.</p></div></section>"""
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": f"Neuerungen {y} für HR und Unternehmen in der Schweiz", "url": nurl, "inLanguage": "de-CH", "dateModified": DATA["updated"], "publisher": PUBLISHER_LD},
          breadcrumb([("Aktuell", SITE_URL), ("Themen", SITE_URL + "thema/"), (f"Neuerungen {y}", nurl)])]
    write(f"thema/{neuerungen_slug()}.html", layout(f"Neuerungen {y} für HR, Lohn und Unternehmen in der Schweiz", body, 1,
          desc=f"Was ändert sich {y} für Arbeitgeber in der Schweiz? AHV, BVG, Kurzarbeit, Transparenzregister, Patentrecht und weitere Neuerungen mit Datum und Quellen.", active="themen", ld=ld, cat="gesetze"))
    cards = f'<a class="tool-card" href="{neuerungen_slug()}.html" style="{cat_style("gesetze")}"><span class="mini-ico" aria-hidden="true">{ICONS["gesetze"]}</span><h3>Neuerungen {y}</h3><p>Alle Änderungen und Fristen {y} für HR und Unternehmen auf einen Blick.</p><span class="more">{len(entries)} Einträge · öffnen</span></a>' + cards
    body = f"""<section class="cat-hero chg-hero"><span class="blob b1"></span><div class="wrap">
  <span class="cat-big" aria-hidden="true">{BOOK}</span>
  <div><span class="hand">Wissen kompakt</span><h1>Themen für HR und Legal</h1><p class="lead">Die Grundlagen zu den wichtigsten Fragen aus dem Alltag von HR- und Legal-Verantwortlichen, mit häufigen Fragen, Rechnern und allen aktuellen Beiträgen zum Thema.</p></div>
</div></section>
<section class="block"><div class="wrap"><div class="tool-grid">{cards}</div></div></section>"""
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Themen für HR und Legal", "url": SITE_URL + "thema/", "inLanguage": "de-CH"},
          breadcrumb([("Aktuell", SITE_URL), ("Themen", SITE_URL + "thema/")])]
    write("thema/index.html", layout("Themen: Arbeitsrecht, Lohn und Legal kompakt erklärt", body, 1,
          desc="Kündigung, Sperrfristen, Massenentlassung, Lohnfortzahlung, Ferien, Arbeitszeugnis, Datenschutz, Lohngleichheit, Transparenzregister: die Grundlagen mit FAQ und aktuellen Beiträgen.", active="themen", ld=ld))


def build_404():
    body = f"""<div class="narrow page"><span class="eyebrow"><span class="pill">404</span></span>
<h1>Diese Seite gibt es nicht (mehr)</h1>
<p class="lead">Vielleicht hilft die Suche weiter, oder Sie starten bei den aktuellen Beiträgen.</p>
<div class="search-box">{SEARCH}<form action="{SITE_URL}suche.html" method="get"><input type="search" name="q" placeholder="z.B. Kündigung, BVG, Transparenzregister" aria-label="Suche"></form></div>
<p><a class="btn" href="{SITE_URL}index.html">Zur Startseite</a> <a class="btn ghost" href="{SITE_URL}thema/index.html">Themen</a></p></div>"""
    html_ = layout("Seite nicht gefunden", body, 0, noindex=True)
    html_ = re.sub(r'(href|src)="(?!https?:|#|mailto:|/)([^"]+)"', lambda m: f'{m.group(1)}="{SITE_URL}{m.group(2)}"', html_)
    write("404.html", html_)


def build_sitemap():
    rows = "".join(f"<url><loc>{e(u)}</loc><lastmod>{m}</lastmod></url>" for u, m in sorted(SITEMAP.items()))
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{rows}</urlset>\n')
    from urllib.parse import urlparse
    base = urlparse(SITE_URL).path or "/"
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: {base}vorschau/\nDisallow: {base}assets/downloads/\n\nSitemap: {SITE_URL}sitemap.xml\n")


def check():
    ids = set()
    for a in DATA["articles"]:
        assert a["category"] in CATS, f"Unbekannte Rubrik: {a['category']} ({a['id']})"
        assert a["id"] not in ids, f"Doppelte id: {a['id']}"
        assert a.get("sources"), f"Keine Quellen: {a['id']}"
        for f in ("title", "teaser", "summary", "published"):
            assert a.get(f), f"Feld {f} fehlt: {a['id']}"
        ids.add(a["id"])


def main():
    check()
    check_contrast()
    for d in ("artikel", "rubrik", "thema", "feeds", "meldungen", "ausgaben", "woche", "rechner", "vorschau", os.path.join("newsletter", "archiv")):
        shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)
    build_home()
    for a in DATA["articles"]:
        build_article(a)
    for k in ORDER:
        build_category(k)
    build_changes()
    build_weeks()
    build_calculators()
    build_archive()
    build_search()
    build_background_page()
    drafts = build_drafts()
    build_newsletter()
    nl.write_outbox(ROOT, DATA, articles(), CATS, PALETTE, ORDER, SITE_NAME, SITE_URL, upcoming_list())
    build_about()
    build_support()
    build_feeds()
    build_themes()
    build_404()
    build_sitemap()
    print(f"OK: {len(DATA['articles'])} Artikel in {len(CATS)} Rubriken, {drafts} Entwürfe")


if __name__ == "__main__":
    main()
