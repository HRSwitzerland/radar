"""Newsletter-Bausteine für HR Radar: Ausgaben alle zwei Wochen, Eilmeldungen, Versand-Ausgang.

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
MAX_AGE_DAYS = 3  # ältere, nicht versendete Ausgaben werden nicht mehr verschickt


def _btn(url, label, color="#2b2540"):
    return f'<a href="{url}" style="display:inline-block;background:{color};color:#ffffff;text-decoration:none;font-weight:700;padding:11px 20px;border-radius:999px;font-family:Arial,Helvetica,sans-serif;font-size:15px;">{label}</a>'


def _shell(site_name, site_url, preheader, inner, footer_extra=""):
    return f"""<!DOCTYPE html><html lang="de-CH"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(site_name)}</title></head>
<body style="margin:0;padding:0;background:#f6f4fb;">
<span style="display:none;max-height:0;overflow:hidden;opacity:0;">{e(preheader)}</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f6f4fb;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;background:#ffffff;border-radius:22px;overflow:hidden;">
<tr><td style="background:#ffd76e;padding:22px 28px;font-family:Georgia,'Times New Roman',serif;font-size:24px;font-weight:bold;color:#2b2540;">{e(site_name)}<div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;font-weight:normal;margin-top:4px;">Was HR heute wissen muss</div></td></tr>
<tr><td style="padding:26px 28px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#2b2540;">{inner}</td></tr>
<tr><td style="padding:18px 28px 26px;font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.6;color:#6b6580;border-top:1px solid #ece8f2;">
Die Beiträge fassen öffentlich zugängliche Quellen zusammen und ersetzen keine Rechtsberatung.{footer_extra}<br>
<a href="{site_url}" style="color:#6b6580;">{e(site_url)}</a> · <a href="{{{{ unsubscribe }}}}" style="color:#6b6580;">Newsletter abbestellen</a>
</td></tr></table></td></tr></table></body></html>"""


def _item(a, site_url, cats, color):
    url = f"{site_url}artikel/{a['id']}.html"
    eff = f' · gilt ab {a["effective"][8:10]}.{a["effective"][5:7]}.{a["effective"][:4]}' if a.get("effective") else ""
    return f"""<tr><td style="padding:0 0 18px;">
<div style="font-size:12px;font-weight:bold;letter-spacing:.05em;text-transform:uppercase;color:{color};">{e(cats[a['category']][1])}{eff}</div>
<a href="{url}" style="font-family:Georgia,'Times New Roman',serif;font-size:19px;font-weight:bold;color:#2b2540;text-decoration:none;line-height:1.3;">{e(a['title'])}</a>
<div style="color:#4a4560;margin-top:4px;">{e(a['teaser'])}</div>
<a href="{url}" style="color:{color};font-weight:bold;text-decoration:none;font-size:14px;">Weiterlesen →</a></td></tr>"""


def issue_items(articles, issue_date, days=14):
    start = (datetime.strptime(issue_date, "%Y-%m-%d") - timedelta(days=days)).date().isoformat()
    return [a for a in articles if start <= a["published"] <= issue_date and a.get("type") != "entwurf"]


def build_issue_html(issue, articles, cats, palette, order, site_name, site_url, upcoming, personalized=True):
    items = issue_items(articles, issue["date"])
    sections = ""
    for k in order:
        group = [a for a in items if a["category"] == k][:4]
        if not group:
            continue
        color = palette[k][0]
        block = f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:26px 0 0;">
<tr><td style="padding:0 0 12px;"><span style="display:inline-block;background:{palette[k][1]};color:{color};font-weight:bold;font-size:14px;padding:5px 12px;border-radius:999px;">{e(cats[k][0])}</span></td></tr>
{"".join(_item(a, site_url, cats, color) for a in group)}</table>"""
        sections += f"{{% if contact.{ATTR[k]} %}}{block}{{% endif %}}" if personalized else block
    hint = ""
    if upcoming:
        lis = "".join(f'<li style="margin:0 0 6px;"><b>{d[8:10]}.{d[5:7]}.{d[:4]}</b>: {e(label)}</li>' for d, label in upcoming[:4])
        hint = f"""<div style="background:#fff4d1;border-radius:16px;padding:16px 18px;margin:28px 0 0;"><div style="font-weight:bold;margin-bottom:8px;">Demnächst</div><ul style="margin:0;padding-left:18px;">{lis}</ul>
<div style="margin-top:8px;"><a href="{site_url}aenderungen.html" style="color:#d9452f;font-weight:bold;text-decoration:none;">Alle Änderungen →</a></div></div>"""
    greeting = "Guten Tag"
    inner = f"""<p style="margin:0 0 6px;font-size:13px;color:#6b6580;">Ausgabe {e(issue['label'])}</p>
<h1 style="font-family:Georgia,'Times New Roman',serif;font-size:26px;line-height:1.25;margin:0 0 14px;">{e(issue.get('title') or 'Die wichtigsten HR-News der letzten zwei Wochen')}</h1>
<p style="margin:0 0 6px;">{greeting}</p>
<p style="margin:0;">{e(issue.get('intro', ''))}</p>
{sections}
{hint}
<p style="margin:28px 0 0;">{_btn(site_url, 'Alle Beiträge auf HR Radar')}</p>
<p style="margin:16px 0 0;font-size:13px;color:#6b6580;">Sie erhalten nur die Rubriken, die Sie gewählt haben. <a href="{site_url}rechner/index.html" style="color:#6b6580;">HR-Rechner</a> · <a href="{site_url}woche/index.html" style="color:#6b6580;">Wochenrückblicke</a></p>"""
    return _shell(site_name, site_url, issue.get("intro", "")[:120], inner)


def build_alert_html(a, cats, palette, site_name, site_url):
    color = palette[a["category"]][0]
    url = f"{site_url}artikel/{a['id']}.html"
    takeaways = "".join(f'<li style="margin:0 0 6px;">{e(t)}</li>' for t in a.get("takeaways", []))
    inner = f"""<p style="margin:0 0 10px;"><span style="display:inline-block;background:#d9452f;color:#fff;font-weight:bold;font-size:13px;padding:5px 12px;border-radius:999px;">Eilmeldung</span>
<span style="font-size:13px;font-weight:bold;color:{color};margin-left:8px;">{e(cats[a['category']][0])}</span></p>
<h1 style="font-family:Georgia,'Times New Roman',serif;font-size:26px;line-height:1.25;margin:0 0 14px;">{e(a['title'])}</h1>
<p style="margin:0 0 16px;">{e(a['summary'])}</p>
<div style="background:{palette[a['category']][1]};border-radius:16px;padding:16px 18px;margin:0 0 20px;"><div style="font-weight:bold;color:{color};margin-bottom:8px;">Das heisst für HR</div><ul style="margin:0;padding-left:18px;">{takeaways}</ul></div>
<p style="margin:0;">{_btn(url, 'Ganzen Beitrag lesen', '#d9452f')}</p>"""
    return _shell(site_name, site_url, a["teaser"][:120], inner, " Sie erhalten Eilmeldungen, weil Sie diese Option gewählt haben.")


def write_outbox(root, data, articles, cats, palette, order, site_name, site_url, upcoming):
    """Legt Versandaufträge in newsletter/outbox/ ab, wenn sie noch nicht verschickt wurden."""
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
