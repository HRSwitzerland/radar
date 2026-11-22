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
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,500;8..60,650&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/style.css">
</head>
<body>
<header class="site-head">
  <div class="wrap">
    <a class="logo" href="{up}index.html"><span class="cross" aria-hidden="true"></span>{e(SITE_NAME)}</a>
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
      <h2>Hinweis</h2>
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
</script>
</body>
</html>
"""


def tag(cat):
    return f'<span class="tag">{e(CATS.get(cat, (cat,))[0])}</span>'


def card(it, up, feature=False):
    eff = f'<span class="eff">gilt ab {d_short(it["effective"])}</span>' if it.get("effective") else ""
    meta = f'<div class="meta">{tag(it["category"])}<time datetime="{it["date"]}">{d_short(it["date"])}</time>{eff}<span>{reading_time(it)} Min.</span></div>'
    href = f'{up}meldungen/{it["id"]}.html'
    if feature:
        return f"""<a class="card feature cat-{it['category']}" href="{href}" data-cat="{it['category']}">
  <div>{meta}<h3>{e(it['title'])}</h3><p>{e(it['summary'])}</p><span class="more">Ganzen Beitrag lesen →</span></div>
  <div class="feature-side"><b>Für die Praxis</b><span>{e(it['todo'])}</span></div>
</a>"""
    summary = it["summary"]
    if len(summary) > 230:
        summary = summary[:230].rsplit(" ", 1)[0] + " …"
    return f"""<a class="card cat-{it['category']}" href="{href}" data-cat="{it['category']}">
  {meta}<h3>{e(it['title'])}</h3><p>{e(summary)}</p><span class="more">Weiterlesen →</span>
</a>"""


def chips(present, target):
    btns = ['<button type="button" class="chip" data-cat="alle" aria-pressed="true">Alle</button>']
    for k in ORDER:
        if k in present:
            btns.append(f'<button type="button" class="chip" data-cat="{k}" aria-pressed="false">{e(CATS[k][0])}</button>')
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


def termine_panel():
    today = date.today().isoformat()
    ts = sorted([t for t in DATA.get("termine", []) if t["date"] >= today], key=lambda t: t["date"])
    if not ts:
        return ""
    lis = "".join(f'<li><time datetime="{t["date"]}">{d_short(t["date"])}</time><span>{e(t["label"])}</span></li>' for t in ts)
    return f'<div class="panel"><h3>Termine und Fristen</h3><ul class="dates">{lis}</ul></div>'


def nl_band(up):
    return f"""<section class="band nl-band"><div class="wrap">
<div><h2>Nur das, was Sie betrifft</h2><p>Wählen Sie Ihre Themen und erhalten Sie jeden Montag eine kompakte Übersicht mit genau diesen Meldungen.</p></div>
<div><a class="btn red" href="{up}newsletter.html">Newsletter einrichten</a></div>
</div></section>"""


# ---------- Seiten ----------

def build_home():
    eds = editions()
    cur = eds[0]
    its = items_of(cur["id"])
    feature = next((i for i in its if i["category"] == "rechtsprechung"), its[0] if its else None)
    rest = [i for i in its if i is not feature]
    # ältere Meldungen der letzten Ausgaben ergänzen
    older = [i for ed in eds[1:3] for i in items_of(ed["id"])]
    hl = "".join(f"<li>{e(h)}</li>" for h in cur.get("highlights", []))
    cards = (card(feature, "", True) if feature else "") + "".join(card(i, "") for i in rest)
    older_html = ""
    if older:
        older_html = f"""<section class="block"><div class="wrap"><div class="block-head"><h2>Aus den letzten Ausgaben</h2><a href="ausgaben/index.html">Alle Ausgaben →</a></div>
<div class="grid">{"".join(card(i, "") for i in older[:6])}</div></div></section>"""
    body = f"""<section class="hero"><div class="wrap">
<div>
  <span class="kicker">Ausgabe {e(cur['label'])} · {d_long(cur['date'])}</span>
  <h1>Was diese Woche im HR-Recht zählt</h1>
  <p class="lead">Neue Urteile, Gesetzesänderungen und Zahlen aus den Sozialversicherungen. Kurz eingeordnet, mit einem konkreten Hinweis, was HR jetzt tun sollte.</p>
  <div class="btn-row"><a class="btn" href="ausgaben/{cur['id']}.html">Ganze Ausgabe lesen</a><a class="btn ghost" href="newsletter.html">Newsletter</a></div>
</div>
<div class="highlights"><h2>Das Wichtigste in Kürze</h2><ol>{hl}</ol></div>
</div></section>
<section class="block"><div class="wrap">
<div class="block-head"><h2>Neueste Beiträge</h2>{chips({i['category'] for i in its}, '#latest .card')}</div>
<div class="grid" id="latest">{cards}</div>
</div></section>
{nl_band('')}
<section class="block"><div class="wrap"><div class="block-head"><h2>Auf einen Blick</h2></div>
<div class="two">{kennzahlen_panel()}{termine_panel()}</div></div></section>
{older_html}"""
    write("index.html", layout(SITE_NAME, body, 0, active="home"))


def build_item(it):
    up = "../"
    ed = next((x for x in DATA["editions"] if x["id"] == it["edition"]), None)
    eff = f'<span class="eff">gilt ab {d_short(it["effective"])}</span>' if it.get("effective") else ""
    details = it.get("details")
    if details:
        det_html = "".join(f"<h2>{e(s['h'])}</h2><p>{e(s['p'])}</p>" for s in details)
    else:
        det_html = ""
    refs = "".join(f'<span class="ref">{e(r)}</span>' for r in it.get("refs", []))
    src = it.get("source")
    src_html = f'<a href="{e(src["url"])}" rel="noopener">{e(src["label"])}</a>' if src else "–"
    related = [i for i in items_of(it["edition"]) if i["id"] != it["id"]][:5]
    rel_html = ""
    if related:
        lis = "".join(f'<li><a href="{i["id"]}.html">{e(i["title"])}</a></li>' for i in related)
        rel_html = f'<div class="related"><h2>Mehr aus der Ausgabe {e(ed["label"]) if ed else ""}</h2><ul>{lis}</ul></div>'
    crumb_ed = f' › <a href="{up}ausgaben/{ed["id"]}.html">Ausgabe {e(ed["label"])}</a>' if ed else ""
    body = f"""<div class="narrow cat-{it['category']}">
<div class="crumbs"><a href="{up}index.html">Aktuell</a>{crumb_ed}</div>
<article class="post">
  <div class="meta">{tag(it['category'])}<time datetime="{it['date']}">{d_long(it['date'])}</time>{eff}<span>{reading_time(it)} Min. Lesezeit</span></div>
  <h1>{e(it['title'])}</h1>
  <p class="lead">{e(it['summary'])}</p>
  {det_html}
  <div class="practice"><h2>Für die Praxis</h2><p>{e(it['todo'])}</p></div>
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
            f'<a class="list-row" href="{up}meldungen/{i["id"]}.html"><div class="meta"><time datetime="{i["date"]}">{d_short(i["date"])}</time>'
            + (f'<span class="eff">gilt ab {d_short(i["effective"])}</span>' if i.get("effective") else "")
            + f'</div><h3>{e(i["title"])}</h3><p>{e(i["summary"])}</p></a>'
            for i in g)
        groups += f'<div class="edition-group cat-{k}"><h2><span class="dot" aria-hidden="true"></span>{e(CATS[k][0])}</h2>{rows}</div>'
    body = f"""<div class="narrow">
<div class="crumbs"><a href="{up}index.html">Aktuell</a> › <a href="index.html">Ausgaben</a></div>
<article class="post">
  <span class="kicker">{d_long(ed['date'])} · {len(its)} Beiträge</span>
  <h1>Ausgabe {e(ed['label'])}</h1>
  <div class="highlights"><h2>Das Wichtigste in Kürze</h2><ol>{hl}</ol></div>
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
<article class="post"><span class="kicker">Archiv</span><h1>Alle Ausgaben</h1>
<p class="lead">Jeden Montag erscheint eine neue Ausgabe. Hier finden Sie alle bisherigen Ausgaben.</p>{rows}</article>
</div>"""
    write("ausgaben/index.html", layout("Alle Ausgaben", body, 1, active="ausgaben"))


def build_newsletter():
    interests = "".join(
        f'<label class="interest cat-{k}"><input type="checkbox" name="interessen" value="{k}" checked><div><b>{e(v[0])}</b><span>{e(v[1])}</span></div></label>'
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
  <span class="kicker">Newsletter</span>
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
  <span class="kicker">Über</span>
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
