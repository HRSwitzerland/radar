#!/usr/bin/env python3
"""Verschickt Versandaufträge aus newsletter/outbox/ über die Brevo-API und verschiebt sie nach newsletter/sent/.

Läuft in GitHub Actions (.github/workflows/newsletter.yml). Benötigt:
  Secret   BREVO_API_KEY            API-Schlüssel aus Brevo (SMTP & API > API Keys)
  Variable BREVO_LIST_ID            ID der Newsletter-Liste (alle Abonnenten)
  Variable BREVO_ALERT_SEGMENT_ID   ID des Segments "EILMELDUNG ist wahr" (optional; ohne: keine Eilmeldungen)
  Variable SENDER_EMAIL            bei Brevo verifizierte Absenderadresse
  Variable SENDER_NAME             Absendername, z.B. "HR Radar"
Ohne API-Key passiert nichts (der Lauf endet ohne Fehler).
"""
import json
import os
import shutil
import sys
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
OUTBOX = os.path.join(ROOT, "newsletter", "outbox")
SENT = os.path.join(ROOT, "newsletter", "sent")
API = "https://api.brevo.com/v3"


def call(method, path, key, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"api-key": key, "content-type": "application/json", "accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode() or "{}"
        return json.loads(raw)


def main():
    key = os.environ.get("BREVO_API_KEY", "").strip()
    if not key:
        print("BREVO_API_KEY fehlt: Versand ist noch nicht eingerichtet. Nichts zu tun.")
        return 0
    if not os.path.isdir(OUTBOX):
        print("Kein Versand-Ausgang vorhanden.")
        return 0
    list_id = os.environ.get("BREVO_LIST_ID", "").strip()
    alert_seg = os.environ.get("BREVO_ALERT_SEGMENT_ID", "").strip()
    sender = {"email": os.environ.get("SENDER_EMAIL", "").strip(), "name": os.environ.get("SENDER_NAME", "HR Radar").strip()}
    if not list_id or not sender["email"]:
        print("BREVO_LIST_ID oder SENDER_EMAIL fehlt. Bitte als Repository-Variablen hinterlegen.")
        return 1
    os.makedirs(SENT, exist_ok=True)
    failures = 0
    for name in sorted(os.listdir(OUTBOX)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(OUTBOX, name)
        job = json.load(open(path, encoding="utf-8"))
        if job["type"] == "alert":
            if not alert_seg:
                print(f"{name}: kein Eilmeldungs-Segment konfiguriert, übersprungen.")
                continue
            recipients = {"segmentIds": [int(alert_seg)]}
        else:
            recipients = {"listIds": [int(list_id)]}
        body = {"name": job["id"], "subject": job["subject"], "previewText": job.get("preheader", ""),
                "sender": sender, "htmlContent": job["html"], "recipients": recipients, "inlineImageActivation": False}
        try:
            created = call("POST", "/emailCampaigns", key, body)
            cid = created["id"]
            call("POST", f"/emailCampaigns/{cid}/sendNow", key)
            job["brevo_campaign_id"] = cid
            with open(os.path.join(SENT, name), "w", encoding="utf-8") as f:
                json.dump({k: v for k, v in job.items() if k != "html"}, f, ensure_ascii=False, indent=1)
            os.remove(path)
            print(f"{name}: versendet (Kampagne {cid}).")
        except Exception as exc:  # Fehler melden, aber andere Aufträge weiter versuchen
            failures += 1
            print(f"{name}: Fehler beim Versand: {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
