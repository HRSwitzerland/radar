#!/usr/bin/env python3
"""Erzeugt die statische Webseite «HR-Recht Radar» aus data/news.json.

Aufruf:  python3 build.py
Erzeugt: index.html, ausgaben/, meldungen/, newsletter.html, ueber.html, feed.xml, feeds/*.xml
"""
import html
import json
import os
import re
import shutil
from datetime import date, datetime
from email.utils import format_datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(ROOT, "data", "news.json"), encoding="utf-8"))
SITE = DATA.get("site", {})
SITE_NAME = SITE.get("name", "HR-Recht Radar")
SITE_URL = SITE.get("url", "https://hrswitzerland.github.io/radar/").rstrip("/") + "/"
NL_ACTION = SITE.get("newsletter_form_action", "")
PUBLISHER = SITE.get("publisher", "[Name, Adresse und E-Mail ergänzen]")

CATS = {
    "rechtsprechung": ("Rechtsprechung", "Neue Urteile des Bundesgerichts und des EGMR mit Bezug zum Arbeitsverhältnis."),
    "gesetzgebung": ("Gesetzgebung", "Gesetzes- und Verordnungsänderungen, Vernehmlassungen und Inkraftsetzungen."),
    "sozialversicherung": ("Sozialversicherungen & Lohn", "AHV, BVG, UVG, ALV, Kurzarbeit, Familienzulagen und Mindestlöhne."),
    "praxis": ("HR-Praxis & Behörden", "Stellenmeldepflicht, Kontingente, Hinweise von SECO, EDÖB und Kantonen."),
}
ORDER = list(CATS)
ICONS = {
    "rechtsprechung": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v18M5 21h14M7 7h10M7 7l-3 7a3 3 0 0 0 6 0L7 7zM17 7l-3 7a3 3 0 0 0 6 0l-3-7z"/></svg>',
    "gesetzgebung": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/></svg>',
    "sozialversicherung": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-7-4.4-7-10V5l7-2 7 2v6c0 5.6-7 10-7 10z"/><path d="M9 12l2 2 4-4"/></svg>',
    "praxis": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0M16 4a3 3 0 0 1 0 6M21 20a6 6 0 0 0-4-5.6"/></svg>',
}
BULB = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/></svg>'
LOGO = '<svg class="logo-mark" viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="18" fill="var(--sun)"/><circle cx="20" cy="20" r="11.5" fill="none" stroke="var(--ink)" stroke-width="2.2" stroke-dasharray="3 3.2"/><path d="M20 20 L31 11" stroke="var(--ink)" stroke-width="2.6" stroke-linecap="round"/><circle cx="20" cy="20" r="3" fill="var(--accent)"/><circle cx="28" cy="25" r="2.4" fill="var(--accent)"/></svg>'
SHORT_MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
WAVE = '<svg class="wave" viewBox="0 0 1200 46" preserveAspectRatio="none" aria-hidden="true"><path d="M0 46 V20 C 150 0 300 40 450 22 S 750 0 900 20 S 1100 40 1200 18 V46 Z" fill="currentColor"/></svg>'

MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

e = html.escape


def d_short(iso):
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def d_long(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d}. {MONTHS[m - 1]} {y}"


def reading_time(item):
    text = " ".join([item.get("summary", ""), item.get("todo", "")] + [s.get("p", "") for s in item.get("details", [])])
    return max(1, round(len(text.split()) / 200))


def editions():
    return sorted(DATA["editions"], key=lambda x: x["date"], reverse=True)


def items_of(ed_id):
    its = [i for i in DATA["items"] if i["edition"] == ed_id]
    return sorted(its, key=lambda i: (ORDER.index(i["category"]) if i["category"] in ORDER else 9, -int(i["date"].replace("-", ""))))


def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def layout(title, body, depth=0, desc="", active=""):
    up = "../" * depth
    def nav(href, label, key, cls=""):
        cur = ' aria-current="page"' if key == active else ""
        c = f' class="{cls}"' if cls else ""
        return f'<a href="{up}{href}"{cur}{c}>{label}</a>'
    full_title = f"{title} · {SITE_NAME}" if title != SITE_NAME else f"{SITE_NAME} Schweiz"
    return f"""<!DOCTYPE html>
<html lang="de-CH">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc or 'Wöchentliche News zu Arbeitsrecht, Bundesgerichtsurteilen, Gesetzgebung und Sozialversicherungen für HR in der Schweiz.')}">
<link rel="alternate" type="application/rss+xml" title="{e(SITE_NAME)}" href="{up}feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT,WONK@9..144,400..700,0..100,0..1&family=Nunito:wght@400;600;700;800&family=Caveat:wght@600;700&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/style.css">
</head>
<body>
<div class="progress" id="progress" aria-hidden="true"></div>
<header class="site-head">
  <div class="wrap">
    <a class="logo" href="{up}index.html">{LOGO}<span class="logo-text">{e(SITE_NAME)}<small>HR-Recht, jede Woche frisch</small></span></a>
    <nav class="main" aria-label="Hauptnavigation">
      {nav("index.html", "Aktuell", "home")}
      {nav("ausgaben/index.html", "Ausgaben", "ausgaben")}
      {nav("ueber.html", "Über", "ueber")}
      {nav("newsletter.html", "Newsletter", "newsletter", "cta")}
    </nav>
  </div>
</header>
<main>
{body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <div>
      <h2>{e(SITE_NAME)}</h2>
      <p>Wöchentliche News zu Arbeitsrecht, Rechtsprechung, Gesetzgebung und Sozialversicherungen für HR in der Schweiz. Erscheint jeden Montag.</p>
      <p><a href="{up}feed.xml">RSS-Feed</a> · <a href="{up}newsletter.html">Newsletter</a></p>
    </div>
    <div>
      <h2>Gut zu wissen</h2>
      <p>Die Beiträge fassen öffentlich zugängliche Quellen zusammen und ersetzen keine Rechtsberatung. Massgebend sind die verlinkten Originalquellen. Inhalte werden mit KI-Unterstützung recherchiert und redaktionell zusammengestellt.</p>
    </div>
    <div>
      <h2>Impressum</h2>
      <p>Herausgeber: {e(PUBLISHER)}</p>
      <p>Letzte Aktualisierung: {d_short(DATA["updated"])}</p>
    </div>
  </div>
</footer>
<script>
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
if (bar && document.querySelector('article.post')) {{
  var onScroll = function () {{
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + '%';
  }};
  window.addEventListener('scroll', onScroll, {{ passive: true }}); onScroll();
}}
</script>
</body>
</html>
"""


def tag(cat):
    return f'<span class="tag">{e(CATS.get(cat, (cat,))[0])}</span>'


def mini(cat):
    return f'<span class="mini" aria-hidden="true">{ICONS.get(cat, "")}</span>'


def card(it, up, feature=False, sticker=""):
    eff = f'<span class="eff">gilt ab {d_short(it["effective"])}</span>' if it.get("effective") else ""
    meta = f'<div class="meta">{tag(it["category"])}<time datetime="{it["date"]}">{d_short(it["date"])}</time>{eff}<span class="dot-sep">{reading_time(it)} Min.</span></div>'
    href = f'{up}meldungen/{it["id"]}.html'
    stk = f'<span class="sticker">{e(sticker)}</span>' if sticker else ""
    if feature:
        return f"""<a class="card feature cat-{it['category']}" href="{href}" data-cat="{it['category']}">{stk}
  <div>{meta}<h3>{e(it['title'])}</h3><p>{e(it['summary'])}</p><span class="more">Ganzen Beitrag lesen</span></div>
  <div class="feature-side"><b>Für die Praxis</b>{e(it['todo'])}</div>
</a>"""
    summary = it["summary"]
    if len(summary) > 200:
        summary = summary[:200].rsplit(" ", 1)[0] + " …"
    return f"""<a class="card cat-{it['category']}" href="{href}" data-cat="{it['category']}">
  <span class="icon" aria-hidden="true">{ICONS.get(it['category'], '')}</span>{meta}<h3>{e(it['title'])}</h3><p>{e(summary)}</p><span class="more">Weiterlesen</span>
</a>"""


def chips(present, target):
    btns = ['<button type="button" class="chip" data-cat="alle" aria-pressed="true">Alle</button>']
    for k in ORDER:
        if k in present:
            btns.append(f'<button type="button" class="chip cat-{k}" data-cat="{k}" aria-pressed="false">{ICONS[k]}{e(CATS[k][0])}</button>')
    return f'<div class="chips" role="group" aria-label="Nach Thema filtern" data-filter="{target}">{"".join(btns)}</div>'


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


def termine_panel():
    today = date.today().isoformat()
    ts = sorted([t for t in DATA.get("termine", []) if t["date"] >= today], key=lambda t: t["date"])
    if not ts:
        return ""
    lis = "".join(f'<li>{cal(t["date"])}<span><span class="sr-date">{d_short(t["date"])}: </span>{e(t["label"])}</span></li>' for t in ts)
    return f'<div class="panel"><h3>Termine und Fristen</h3><ul class="dates">{lis}</ul></div>'


def nl_band(up):
    return f"""<section class="nl-band"><div class="wrap"><div class="nl-box">
<div><span class="hand">Ihr Montag, sortiert</span><h2>Nur die Themen, die Sie wirklich brauchen</h2><p>Themen auswählen, und jeden Montag kommt eine kurze Mail mit genau diesen Meldungen. Kein Rauschen.</p></div>
<div><a class="btn" href="{up}newsletter.html">Newsletter einrichten</a></div>
</div></div></section>"""


# ---------- Seiten ----------

def build_home():
    eds = editions()
    cur = eds[0]
    its = items_of(cur["id"])
    feature = next((i for i in its if i["category"] == "rechtsprechung"), its[0] if its else None)
    rest = [i for i in its if i is not feature]
    older = [i for ed in eds[1:3] for i in items_of(ed["id"])]
    hl = "".join(f"<li>{e(h)}</li>" for h in cur.get("highlights", []))
    cards = (card(feature, "", True, "Top-Thema") if feature else "") + "".join(card(i, "") for i in rest)
    older_html = ""
    if older:
        older_html = f"""<section class="block"><div class="wrap"><div class="block-head"><div><span class="hand">Falls Sie es verpasst haben</span><h2>Aus den letzten Ausgaben</h2></div><a href="ausgaben/index.html">Alle Ausgaben</a></div>
<div class="grid">{"".join(card(i, "") for i in older[:6])}</div></div></section>"""
    body = f"""<section class="hero"><span class="blob b1"></span><span class="blob b2"></span><span class="blob b3"></span><div class="wrap">
<div>
  <span class="eyebrow"><span class="pill">Ausgabe {e(cur['label'])}</span>{d_long(cur['date'])}</span>
  <h1>Was diese Woche im <span class="squiggle">HR-Recht</span> zählt</h1>
  <p class="lead">Neue Urteile, Gesetzesänderungen und Zahlen aus den Sozialversicherungen. Verständlich erklärt, mit einem konkreten Tipp, was Sie im HR jetzt tun können.</p>
  <div class="btn-row"><a class="btn" href="ausgaben/{cur['id']}.html">Ganze Ausgabe lesen</a><a class="btn ghost" href="newsletter.html">Newsletter</a></div>
</div>
<div class="note-card"><h2>Kurz &amp; knapp</h2><ol>{hl}</ol></div>
</div></section>
<section class="block"><div class="wrap">
<div class="block-head"><div><span class="hand">Frisch eingetroffen</span><h2>Neueste Beiträge</h2></div>{chips({i['category'] for i in its}, '#latest .card')}</div>
<div class="grid" id="latest">{cards}</div>
</div></section>
{nl_band('')}
{WAVE}
<section class="block band"><div class="wrap"><div class="block-head"><div><span class="hand">Zum Nachschlagen</span><h2>Auf einen Blick</h2></div></div>
<div class="two">{kennzahlen_panel()}{termine_panel()}</div></div></section>
<svg class="wave flip" viewBox="0 0 1200 46" preserveAspectRatio="none" aria-hidden="true"><path d="M0 46 V20 C 150 0 300 40 450 22 S 750 0 900 20 S 1100 40 1200 18 V46 Z" fill="currentColor"/></svg>
{older_html}"""
    write("index.html", layout(SITE_NAME, body, 0, active="home"))


def build_item(it):
    up = "../"
    ed = next((x for x in DATA["editions"] if x["id"] == it["edition"]), None)
    eff = f'<span class="eff">gilt ab {d_short(it["effective"])}</span>' if it.get("effective") else ""
    details = it.get("details")
    if details:
        body_html = f'<div class="tldr"><span class="hand">In 30 Sekunden</span><p>{e(it["summary"])}</p></div><div class="body">' + "".join(f"<h2>{e(s['h'])}</h2><p>{e(s['p'])}</p>" for s in details) + "</div>"
        lead = ""
    else:
        body_html = ""
        lead = f'<p class="lead">{e(it["summary"])}</p>'
    refs = "".join(f'<span class="ref">{e(r)}</span>' for r in it.get("refs", []))
    src = it.get("source")
    src_html = f'<a href="{e(src["url"])}" rel="noopener">{e(src["label"])}</a>' if src else "–"
    related = [i for i in items_of(it["edition"]) if i["id"] != it["id"]][:5]
    rel_html = ""
    if related:
        lis = "".join(f'<li><a class="cat-{i["category"]}" href="{i["id"]}.html">{mini(i["category"])}{e(i["title"])}</a></li>' for i in related)
        rel_html = f'<div class="related"><h2>Lesen Sie auch</h2><ul>{lis}</ul></div>'
    crumb_ed = f' › <a href="{up}ausgaben/{ed["id"]}.html">Ausgabe {e(ed["label"])}</a>' if ed else ""
    body = f"""<div class="narrow cat-{it['category']}">
<div class="crumbs"><a href="{up}index.html">Aktuell</a>{crumb_ed}</div>
<article class="post">
  <div class="meta">{tag(it['category'])}<time datetime="{it['date']}">{d_long(it['date'])}</time>{eff}<span class="dot-sep">{reading_time(it)} Min. Lesezeit</span></div>
  <h1>{e(it['title'])}</h1>
  {lead}{body_html}
  <div class="practice"><span class="icon">{BULB}</span><h2>Für die Praxis</h2><p>{e(it['todo'])}</p></div>
  <dl class="facts">
    <div><dt>Rechtsgrundlagen und Fundstellen</dt><dd class="refs">{refs}</dd></div>
    <div><dt>Quelle</dt><dd>{src_html}</dd></div>
  </dl>
</article>
{rel_html}
</div>
{nl_band(up)}"""
    write(f"meldungen/{it['id']}.html", layout(it["title"], body, 1, desc=it["summary"][:160]))


def build_edition(ed):
    up = "../"
    its = items_of(ed["id"])
    hl = "".join(f"<li>{e(h)}</li>" for h in ed.get("highlights", []))
    groups = ""
    for k in ORDER:
        g = [i for i in its if i["category"] == k]
        if not g:
            continue
        rows = "".join(
            f'<a class="list-row cat-{k}" href="{up}meldungen/{i["id"]}.html"><div class="meta"><time datetime="{i["date"]}">{d_short(i["date"])}</time>'
            + (f'<span class="eff">gilt ab {d_short(i["effective"])}</span>' if i.get("effective") else "")
            + f'<span class="dot-sep">{reading_time(i)} Min.</span></div><h3>{e(i["title"])}</h3><p>{e(i["summary"])}</p></a>'
            for i in g)
        groups += f'<div class="edition-group cat-{k}"><h2>{mini(k)}{e(CATS[k][0])}</h2>{rows}</div>'
    body = f"""<div class="narrow">
<div class="crumbs"><a href="{up}index.html">Aktuell</a> › <a href="index.html">Ausgaben</a></div>
<article class="post">
  <span class="eyebrow"><span class="pill">{len(its)} Beiträge</span>{d_long(ed['date'])}</span>
  <h1>Ausgabe {e(ed['label'])}</h1>
  <div class="note-card edition-hl"><h2>Kurz &amp; knapp</h2><ol>{hl}</ol></div>
  {groups}
</article>
</div>
{nl_band(up)}"""
    write(f"ausgaben/{ed['id']}.html", layout(f"Ausgabe {ed['label']}", body, 1, active="ausgaben"))


def build_archive():
    up = "../"
    rows = ""
    for ed in editions():
        its = items_of(ed["id"])
        first = ed.get("highlights", [""])[0]
        rows += f'<a class="list-row" href="{ed["id"]}.html"><div class="meta"><time datetime="{ed["date"]}">{d_long(ed["date"])}</time><span>{len(its)} Beiträge</span></div><h3>Ausgabe {e(ed["label"])}</h3><p>{e(first)}</p></a>'
    body = f"""<div class="narrow archive">
<div class="crumbs"><a href="{up}index.html">Aktuell</a></div>
<article class="post"><span class="eyebrow"><span class="pill">Archiv</span></span><h1>Alle Ausgaben</h1>
<p class="lead">Jeden Montag erscheint eine neue Ausgabe. Hier finden Sie alle bisherigen Ausgaben.</p>{rows}</article>
</div>"""
    write("ausgaben/index.html", layout("Alle Ausgaben", body, 1, active="ausgaben"))


def build_newsletter():
    interests = "".join(
        f'<label class="interest cat-{k}"><span class="mini" aria-hidden="true">{ICONS[k]}</span><div><b>{e(v[0])}</b><span>{e(v[1])}</span></div><input type="checkbox" name="interessen" value="{k}" checked></label>'
        for k, v in CATS.items())
    feeds = "".join(f'<li><a href="feeds/{k}.xml">{e(v[0])}</a> <code>feeds/{k}.xml</code></li>' for k, v in CATS.items())
    if NL_ACTION:
        action = f'action="{e(NL_ACTION)}" method="post"'
        notice = ""
        disabled = ""
    else:
        action = 'action="#" onsubmit="return false"'
        notice = '<p class="notice">Die Anmeldung wird in Kürze freigeschaltet. Bis dahin können Sie die Themen über die RSS-Feeds unten abonnieren.</p>'
        disabled = " disabled"
    body = f"""<div class="narrow">
<div class="crumbs"><a href="index.html">Aktuell</a></div>
<article class="post">
  <span class="eyebrow"><span class="pill">Newsletter</span></span>
  <h1>Ihr persönlicher HR-Recht Radar</h1>
  <p class="lead">Wählen Sie die Themen, die für Sie relevant sind. Jeden Montag erhalten Sie eine E-Mail mit genau diesen Meldungen, kurz zusammengefasst und mit Link zum ausführlichen Beitrag.</p>
  {notice}
  <form class="nl" {action}>
    <div class="field"><label for="nl-email">E-Mail-Adresse</label><input type="email" id="nl-email" name="email" required autocomplete="email" placeholder="vorname.name@firma.ch"></div>
    <div class="field"><label for="nl-name">Vorname (optional)</label><input type="text" id="nl-name" name="vorname" autocomplete="given-name"></div>
    <fieldset><legend>Welche Themen interessieren Sie?</legend><div class="interest-grid">{interests}</div></fieldset>
    <label class="consent"><input type="checkbox" id="nl-consent" name="einwilligung" required><span>Ich möchte den Newsletter erhalten und bin einverstanden, dass meine E-Mail-Adresse und meine Themenwahl dafür gespeichert werden. Ich kann mich jederzeit über den Link in jeder E-Mail abmelden.</span></label>
    <div><button class="btn red" type="submit"{disabled}>Newsletter abonnieren</button></div>
  </form>
  <h2>RSS-Feeds pro Thema</h2>
  <p>Für Feed-Reader oder Tools wie Outlook und Teams gibt es jedes Thema auch als eigenen Feed. Alle Meldungen: <a href="feed.xml">feed.xml</a></p>
  <ul class="feeds">{feeds}</ul>
</article>
</div>"""
    write("newsletter.html", layout("Newsletter", body, 0, active="newsletter"))


def build_about():
    cats = "".join(f"<li><b>{e(v[0])}:</b> {e(v[1])}</li>" for v in CATS.values())
    body = f"""<div class="narrow">
<div class="crumbs"><a href="index.html">Aktuell</a></div>
<article class="post">
  <span class="eyebrow"><span class="pill">Über</span></span>
  <h1>Über den {e(SITE_NAME)}</h1>
  <p class="lead">Der {e(SITE_NAME)} fasst jede Woche zusammen, was sich im Schweizer Arbeitsrecht und rund um HR bewegt. Er richtet sich an HR-Leiterinnen und HR-Leiter, HR-Fachleute und alle, die Arbeitsverhältnisse gestalten.</p>
  <h2>Themen</h2><ul>{cats}</ul>
  <h2>So entstehen die Beiträge</h2>
  <p>Grundlage sind öffentlich zugängliche Quellen: Urteile des Bundesgerichts und des EGMR, Medienmitteilungen des Bundesrats und der Bundesämter sowie Fachpublikationen. Die Inhalte werden mit KI-Unterstützung recherchiert, zusammengefasst und redaktionell zusammengestellt. Jeder Beitrag verlinkt seine Quelle.</p>
  <h2>Keine Rechtsberatung</h2>
  <p>Die Beiträge dienen der allgemeinen Information und ersetzen keine Beratung im Einzelfall. Trotz sorgfältiger Prüfung wird keine Gewähr für Vollständigkeit, Richtigkeit und Aktualität übernommen. Massgebend sind die Originalquellen.</p>
  <h2>Impressum</h2>
  <p>Herausgeber: {e(PUBLISHER)}</p>
</article>
</div>"""
    write("ueber.html", layout("Über", body, 0, active="ueber"))


def rss(path, title, items):
    def rfc(iso):
        return format_datetime(datetime.strptime(iso, "%Y-%m-%d").replace(hour=6))
    entries = ""
    for it in items:
        link = f"{SITE_URL}meldungen/{it['id']}.html"
        desc = f"<p>{e(it['summary'])}</p><p><b>Für die Praxis:</b> {e(it['todo'])}</p>"
        ed = next((x for x in DATA["editions"] if x["id"] == it["edition"]), {"date": it["date"]})
        entries += f"""<item><title>{e(it['title'])}</title><link>{link}</link><guid isPermaLink="true">{link}</guid>
<pubDate>{rfc(ed['date'])}</pubDate><category>{e(CATS.get(it['category'], (it['category'],))[0])}</category>
<description>{e(desc)}</description></item>
"""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>{e(title)}</title><link>{SITE_URL}</link>
<description>Wöchentliche News zu Arbeitsrecht und HR in der Schweiz</description>
<language>de-ch</language><lastBuildDate>{rfc(DATA['updated'])}</lastBuildDate>
{entries}</channel></rss>
"""
    write(path, xml)


def build_feeds():
    eds = {x["id"]: x["date"] for x in DATA["editions"]}
    all_items = sorted(DATA["items"], key=lambda i: (eds.get(i["edition"], ""), i["date"]), reverse=True)[:60]
    rss("feed.xml", SITE_NAME, all_items)
    for k, v in CATS.items():
        rss(f"feeds/{k}.xml", f"{SITE_NAME}: {v[0]}", [i for i in all_items if i["category"] == k])


def main():
    for d in ("meldungen", "ausgaben", "feeds"):
        shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)
    build_home()
    for ed in editions():
        build_edition(ed)
    build_archive()
    for it in DATA["items"]:
        build_item(it)
    build_newsletter()
    build_about()
    build_feeds()
    print(f"OK: {len(DATA['editions'])} Ausgaben, {len(DATA['items'])} Meldungen")


if __name__ == "__main__":
    main()
