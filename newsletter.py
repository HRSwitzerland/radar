"""Newsletter-Bausteine für HR Radar: Ausgaben jeden Montag, Eilmeldungen, Versand-Ausgang.

Die E-Mails werden über Brevo verschickt (siehe send_newsletter.py und .github/workflows/newsletter.yml).
Die Themenwahl wird über Kontakt-Attribute in Brevo umgesetzt (THEMA_<RUBRIK> = true/false, EILMELDUNG = true/false):
Jede Rubrik ist in der E-Mail in einen Brevo-Bedingungsblock {% if contact.THEMA_... %} gepackt.
"""
import html
import json
import os
from datetime import date, datetime, timedelta

e = html.escape
ATTR = {
    "arbeitsrecht": "THEMA_ARBEITSRECHT",
    "gesetze": "THEMA_GESETZE",
    "lohn": "THEMA_LOHN",
    "arbeitsmarkt": "THEMA_ARBEITSMARKT",
    "gesundheit": "THEMA_GESUNDHEIT",
    "digital": "THEMA_DIGITAL",
    "praxis": "THEMA_PRAXIS",
    "legal": "THEMA_LEGAL",
}
ALERT_ATTR = "EILMELDUNG"
SUPPORT_URL = ""  # wird von write_outbox aus data/articles.json (site.support_url) gesetzt
MAX_AGE_DAYS = 3  # ältere, nicht versendete Ausgaben werden nicht mehr verschickt


INK, MUTED, LINE, CORAL, SUN, SUN_SOFT, LILAC, BG = "#2b2540", "#6b6580", "#ece8f2", "#d9452f", "#ffd76e", "#fff4d1", "#ddd3ff", "#f6f3ee"
SERIF = "'Fraunces',Georgia,'Times New Roman',serif"
SANS = "'Nunito','Segoe UI','Helvetica Neue',Arial,sans-serif"


def _btn(url, label, color=INK):
    return f'<a href="{url}" style="display:inline-block;background:{color};color:#ffffff;text-decoration:none;font-weight:800;padding:13px 24px;border-radius:999px;font-family:{SANS};font-size:15px;">{label}</a>'


def _rubric_head(title, color, soft):
    return f'<span style="display:inline-block;background:{soft};color:{color};font-family:{SANS};font-weight:800;font-size:12px;letter-spacing:.06em;text-transform:uppercase;padding:6px 14px;border-radius:999px;">{e(title)}</span>'


def _shell(site_name, site_url, preheader, inner, footer_extra="", unsubscribe=True, footer_text="Die Beiträge fassen öffentlich zugängliche Quellen zusammen und ersetzen keine Rechtsberatung."):
    logo = f"{site_url}assets/og/logo.png"
    links = (f'<a href="{site_url}aenderungen.html" style="color:{INK};text-decoration:none;font-weight:700;">Das ändert sich</a> &nbsp;·&nbsp; '
             f'<a href="{site_url}rechner/" style="color:{INK};text-decoration:none;font-weight:700;">Rechner</a> &nbsp;·&nbsp; '
             f'<a href="{site_url}thema/" style="color:{INK};text-decoration:none;font-weight:700;">Themen</a>')
    unsub = f' &nbsp;·&nbsp; <a href="{{{{ unsubscribe }}}}" style="color:{MUTED};">Newsletter abbestellen</a>' if unsubscribe else ""
    return f"""<!DOCTYPE html><html lang="de-CH"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light"><title>{e(site_name)}</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Nunito:wght@400;700;800&display=swap" rel="stylesheet">
<style>@media (max-width:640px){{.pad{{padding-left:20px!important;padding-right:20px!important}}.h1{{font-size:26px!important}}}}</style></head>
<body style="margin:0;padding:0;background:{BG};">
<span style="display:none;max-height:0;overflow:hidden;opacity:0;">{e(preheader)}</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};"><tr><td align="center" style="padding:28px 12px;">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">
<tr><td class="pad" style="padding:0 8px 18px;">
<table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td style="vertical-align:middle;padding-right:12px;"><a href="{site_url}"><img src="{logo}" width="44" height="44" alt="" style="display:block;border:0;border-radius:50%;"></a></td>
<td style="vertical-align:middle;"><a href="{site_url}" style="text-decoration:none;"><div style="font-family:{SERIF};font-size:24px;font-weight:700;color:{INK};line-height:1.1;">{e(site_name)}</div>
<div style="font-family:{SERIF};font-size:15px;font-weight:600;color:{CORAL};line-height:1.3;">Was HR heute wissen muss</div></a></td></tr></table></td></tr>
<tr><td style="background:#ffffff;border-radius:26px;overflow:hidden;border:1px solid {LINE};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td class="pad" style="padding:30px 36px 34px;font-family:{SANS};font-size:16px;line-height:1.65;color:{INK};">
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 20px;"><tr><td width="44" height="6" style="background:{SUN};border-radius:3px;font-size:0;line-height:0;">&nbsp;</td><td width="6" style="font-size:0;">&nbsp;</td><td width="20" height="6" style="background:#ff6f59;border-radius:3px;font-size:0;line-height:0;">&nbsp;</td><td width="6" style="font-size:0;">&nbsp;</td><td width="28" height="6" style="background:{LILAC};border-radius:3px;font-size:0;line-height:0;">&nbsp;</td><td width="6" style="font-size:0;">&nbsp;</td><td width="14" height="6" style="background:#bfe8d6;border-radius:3px;font-size:0;line-height:0;">&nbsp;</td></tr></table>
{inner}</td></tr></table>
</td></tr>
<tr><td class="pad" style="padding:22px 12px 0;font-family:{SANS};font-size:14px;line-height:1.6;color:{INK};text-align:center;">{links}</td></tr>
<tr><td class="pad" style="padding:12px 24px 8px;font-family:{SANS};font-size:12px;line-height:1.65;color:{MUTED};text-align:center;">
{footer_text}{footer_extra}<br>
<a href="{site_url}" style="color:{MUTED};">hr-radar.ch</a>{unsub}
</td></tr></table></td></tr></table></body></html>"""


def _item(a, site_url, cats, color, first=False):
    url = f"{site_url}artikel/{a['id']}.html"
    eff = f' · gilt ab {a["effective"][8:10]}.{a["effective"][5:7]}.{a["effective"][:4]}' if a.get("effective") else ""
    border = "" if first else f"border-top:1px solid {LINE};"
    return f"""<tr><td style="padding:16px 0;{border}">
<div style="font-family:{SANS};font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:{color};">{e(cats[a['category']][1])}{eff}</div>
<a href="{url}" style="display:block;font-family:{SERIF};font-size:20px;font-weight:700;color:{INK};text-decoration:none;line-height:1.3;margin:4px 0 6px;">{e(a['title'])}</a>
<div style="color:#4a4560;font-size:15px;">{e(a['teaser'])}</div>
<a href="{url}" style="display:inline-block;margin-top:6px;color:{CORAL};font-weight:800;text-decoration:none;font-size:14px;">Weiterlesen →</a></td></tr>"""


def issue_items(articles, issue_date, days=7):
    start = (datetime.strptime(issue_date, "%Y-%m-%d") - timedelta(days=days)).date().isoformat()
    return [a for a in articles if start <= a["published"] <= issue_date and a.get("type") != "entwurf"]


def build_issue_html(issue, articles, cats, palette, order, site_name, site_url, upcoming, personalized=True):
    items = issue_items(articles, issue["date"])
    sections = ""
    for k in order:
        group = [a for a in items if a["category"] == k][:4]
        if not group:
            continue
        color, soft = palette[k]
        block = f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:30px 0 0;">
<tr><td style="padding:0 0 4px;">{_rubric_head(cats[k][0], color, soft)}</td></tr>
{"".join(_item(a, site_url, cats, color, i == 0) for i, a in enumerate(group))}</table>"""
        sections += f"{{% if contact.{ATTR[k]} %}}{block}{{% endif %}}" if personalized else block
    hint = ""
    if upcoming:
        lis = "".join(f'<tr><td style="padding:4px 12px 4px 0;font-weight:800;white-space:nowrap;vertical-align:top;color:{CORAL};">{d[8:10]}.{d[5:7]}.{d[:4]}</td><td style="padding:4px 0;vertical-align:top;">{e(label)}</td></tr>' for d, label in upcoming[:4])
        hint = f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:32px 0 0;background:{SUN_SOFT};border-radius:20px;"><tr><td style="padding:20px 22px;">
<div style="font-family:{SERIF};font-size:20px;font-weight:700;color:{CORAL};margin-bottom:8px;">Demnächst</div>
<table role="presentation" cellpadding="0" cellspacing="0" style="font-size:15px;">{lis}</table>
<div style="margin-top:10px;"><a href="{site_url}aenderungen.html" style="color:{INK};font-weight:800;text-decoration:none;">Alle Änderungen im Überblick →</a></div></td></tr></table>"""
    d = issue["date"]
    inner = f"""<div style="font-family:{SANS};font-size:13px;font-weight:700;color:{MUTED};">Ausgabe {e(issue['label'])} · {d[8:10]}.{d[5:7]}.{d[:4]}</div>
<div style="font-family:{SERIF};font-size:18px;font-weight:600;color:{CORAL};margin:14px 0 4px;">Neu auf dem Radar</div>
<h1 class="h1" style="font-family:{SERIF};font-size:30px;line-height:1.2;font-weight:700;margin:0 0 16px;color:{INK};">{e(issue.get('title') or 'Die wichtigsten HR-News der Woche')}</h1>
<p style="margin:0 0 4px;">Guten Tag</p>
<p style="margin:0;">{e(issue.get('intro', ''))}</p>
{sections}
{hint}
<p style="margin:32px 0 0;text-align:center;">{_btn(site_url, 'Alle Beiträge auf HR Radar')}</p>
<p style="margin:16px 0 0;font-size:13px;color:{MUTED};text-align:center;">Sie erhalten nur die Rubriken, die Sie gewählt haben.</p>
{_support_box()}"""
    return _shell(site_name, site_url, issue.get("intro", "")[:120], inner)


def _support_box():
    if not SUPPORT_URL:
        return ""
    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:30px 0 0;border-top:1px solid {LINE};"><tr><td style="padding:24px 0 0;text-align:center;">
<div style="font-family:{SERIF};font-size:19px;font-weight:700;color:{INK};margin-bottom:6px;">Hilft Ihnen HR Radar?</div>
<div style="font-size:15px;color:#4a4560;margin:0 auto 14px;max-width:440px;">HR Radar ist kostenlos, werbefrei und unabhängig. Wenn Sie die Arbeit daran unterstützen möchten, freuen wir uns über einen Kaffee.</div>
<a href="{SUPPORT_URL}" style="display:inline-block;background:{SUN};color:{INK};text-decoration:none;font-weight:800;padding:11px 22px;border-radius:999px;font-family:{SANS};font-size:15px;">&#9749; Einen Kaffee spendieren</a></td></tr></table>"""


def build_alert_html(a, cats, palette, site_name, site_url):
    color, soft = palette[a["category"]]
    url = f"{site_url}artikel/{a['id']}.html"
    practice = "Das heisst für Legal" if a["category"] == "legal" else "Das heisst für HR"
    takeaways = "".join(f'<li style="margin:0 0 6px;">{e(t)}</li>' for t in a.get("takeaways", []))
    inner = f"""<p style="margin:0 0 14px;"><span style="display:inline-block;background:{CORAL};color:#fff;font-weight:800;font-size:12px;letter-spacing:.06em;text-transform:uppercase;padding:6px 14px;border-radius:999px;">Eilmeldung</span>
&nbsp;{_rubric_head(cats[a['category']][0], color, soft)}</p>
<h1 class="h1" style="font-family:{SERIF};font-size:30px;line-height:1.2;font-weight:700;margin:0 0 14px;color:{INK};">{e(a['title'])}</h1>
<p style="margin:0 0 20px;">{e(a['summary'])}</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{SUN_SOFT};border-radius:20px;margin:0 0 24px;"><tr><td style="padding:18px 22px;">
<div style="font-family:{SERIF};font-size:19px;font-weight:700;color:{CORAL};margin-bottom:8px;">{practice}</div><ul style="margin:0;padding-left:18px;">{takeaways}</ul></td></tr></table>
<p style="margin:0;text-align:center;">{_btn(url, 'Ganzen Beitrag lesen', CORAL)}</p>"""
    return _shell(site_name, site_url, a["teaser"][:120], inner, " Sie erhalten Eilmeldungen, weil Sie diese Option gewählt haben.")


def build_doi_html(site_name, site_url):
    """Bestaetigungsmail (Double-Opt-in) fuer Brevo. {{ doubleoptin }} ist der Bestaetigungslink."""
    inner = f"""<div style="font-family:{SERIF};font-size:18px;font-weight:600;color:{CORAL};margin:0 0 4px;">Fast geschafft</div>
<h1 class="h1" style="font-family:{SERIF};font-size:30px;line-height:1.2;font-weight:700;margin:0 0 16px;color:{INK};">Bitte bestätigen Sie Ihre Anmeldung</h1>
<p style="margin:0 0 4px;">Guten Tag</p>
<p style="margin:0 0 24px;">Vielen Dank für Ihr Interesse am {e(site_name)} Newsletter. Bitte bestätigen Sie mit einem Klick, dass Sie ihn erhalten möchten. Erst dann ist Ihre Anmeldung aktiv.</p>
<p style="margin:0 0 28px;text-align:center;">{_btn('{{ doubleoptin }}', 'Anmeldung bestätigen', CORAL)}</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{SUN_SOFT};border-radius:20px;"><tr><td style="padding:18px 22px;font-size:15px;">
<div style="font-family:{SERIF};font-size:19px;font-weight:700;color:{INK};margin-bottom:6px;">Das erwartet Sie</div>
<ul style="margin:0;padding-left:18px;"><li style="margin:0 0 4px;">Jeden Montagmorgen die wichtigsten News der Woche zu Arbeitsrecht, HR und Legal</li><li style="margin:0 0 4px;">Nur aus den Rubriken, die Sie gewählt haben</li><li style="margin:0;">Auf Wunsch Eilmeldungen bei sehr wichtigen Entscheiden</li></ul></td></tr></table>
<p style="margin:24px 0 0;font-size:13px;color:{MUTED};">Sie haben sich nicht angemeldet? Dann ignorieren Sie diese E-Mail einfach. Ohne Bestätigung erhalten Sie keine weiteren E-Mails von uns.</p>"""
    return _shell(site_name, site_url, "Ein Klick, dann sind Sie dabei.", inner, unsubscribe=False, footer_text="Sie erhalten diese E-Mail, weil diese Adresse auf hr-radar.ch für den Newsletter angemeldet wurde.")


def write_outbox(root, data, articles, cats, palette, order, site_name, site_url, upcoming):
    """Legt Versandaufträge in newsletter/outbox/ ab, wenn sie noch nicht verschickt wurden."""
    global SUPPORT_URL
    SUPPORT_URL = data.get("site", {}).get("support_url", "")
    today = date.today()
    outbox = os.path.join(root, "newsletter", "outbox")
    sent = os.path.join(root, "newsletter", "sent")
    os.makedirs(outbox, exist_ok=True)
    os.makedirs(sent, exist_ok=True)
    jobs = []
    for issue in data.get("newsletters", []):
        jobs.append(("ausgabe-" + issue["id"], issue["date"], lambda i=issue: {
            "type": "issue", "subject": f"HR Radar {i['label']}: {i.get('title') or 'Die wichtigsten HR-News'}",
            "preheader": i.get("intro", "")[:120], "date": i["date"],
            "html": build_issue_html(i, articles, cats, palette, order, site_name, site_url, upcoming)}))
    for a in articles:
        if a.get("alert"):
            jobs.append(("eilmeldung-" + a["id"], a["published"], lambda x=a: {
                "type": "alert", "subject": f"Eilmeldung HR Radar: {x['title']}", "preheader": x["teaser"][:120],
                "date": x["published"], "html": build_alert_html(x, cats, palette, site_name, site_url)}))
    for job_id, d, make in jobs:
        if os.path.exists(os.path.join(sent, job_id + ".json")):
            continue
        age = (today - datetime.strptime(d, "%Y-%m-%d").date()).days
        path = os.path.join(outbox, job_id + ".json")
        if age < 0 or age > MAX_AGE_DAYS:
            if os.path.exists(path):
                os.remove(path)
            continue
        payload = make()
        payload["id"] = job_id
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
