"""HR-Stellen direkt von den Karriereseiten der Arbeitgeber holen.

Läuft täglich in der GitHub Action .github/workflows/stellen.yml (nicht in build.py,
weil dort kein Netz gebraucht werden soll). Quellen: data/stellen_quellen.json.
Ergebnis: data/stellen.json, das build.py zur Seite stellen.html verarbeitet.

Genutzt werden nur die öffentlichen Stellen-Schnittstellen, welche die Arbeitgeber
über ihr Bewerbermanagement-System selbst bereitstellen (Workday, Greenhouse,
SmartRecruiters, Lever, Recruitee, Personio, Teamtailor, Ashby). Übernommen werden
nur Titel, Firma, Ort, Datum und der Link zum Originalinserat.
"""
import json
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "stellen_quellen.json")
OUT = os.path.join(ROOT, "data", "stellen.json")
UA = "HR-Radar-Stellen/1.0 (+https://hr-radar.ch/stellen.html)"
MAX_AGE_DAYS = 60
PAUSE = 0.5

HR = re.compile(
    r"\bHR\b|\bHRBP\b|\bHRIS\b|Human Resource|Personal(?:fach|leit|berat|administ|wesen|assist|referent|chef|dienst|abteil|entwickl|manag|verantw|sachbearb|spezial|bereich|gewinn|marketing|planung|controll)"
    r"|People (?:&|and) Culture|People Partner|People Operations|People Experience|People Business Partner|People Analytics|People Advisor|People Specialist|Head of People|Chief People|VP,? People"
    r"|Payroll|Lohn(?:buchhalt|administ|spezial|verantw|wesen|abrechn)|Gehaltsabrechn|Recruit|Talent Acquisition|Talent Management|Talent Partner|Sourc(?:er|ing Specialist)"
    r"|Compensation|Total Rewards|Reward|Ressources humaines|\bRH\b|Gestionnaire (?:de )?(?:la )?(?:paie|salaires|personnel)|\bpaie\b|Responsable du personnel|Risorse umane"
    r"|Learning (?:&|and) Development|Employer Branding|Arbeitsrecht|Employee Relations|Workforce Planning|Onboarding Specialist",
    re.I)
NOT_HR = re.compile(r"Patient|Clinical|Procurement|Einkauf|Klinisch|Personal Banker|Personal Trainer|Fitness|HR-Software Vertrieb|Account Executive|Sales", re.I)

CH = re.compile(
    r"Switzerland|Schweiz|Suisse|Svizzera|\bCH\b|Z(?:ü|u)rich|Basel|\bBern\b|Gen(?:è|e)v|\bGenf\b|Lausanne|Luzern|Lucerne|\bZug\b|St\.? ?Gallen|Winterthur|Lugano|Aarau|(?<!-)\bBaden\b(?!-)"
    r"|Biel|Bienne|Fribourg|Neuch(?:â|a)tel|Schaffhausen|\bChur\b|\bThun\b|Olten|Solothurn|\bSion\b|Rapperswil|Opfikon|Kloten|\bBaar\b|Rotkreuz|Allschwil|Muttenz|Pratteln"
    r"|Kaiseraugst|\bVisp\b|\bStans\b|Schlieren|D(?:ü|u)bendorf|Wallisellen|Horgen|\bCham\b|\bBulle\b|Yverdon|\bNyon\b|Morges|Vevey|Montreux|Martigny|Bellinzona|Locarno|Mendrisio"
    r"|Glattbrugg|R(?:ü|u)schlikon|Kriens|Emmen|Uster|Wetzikon|Frauenfeld|Kreuzlingen|Herisau|Wil SG|Liestal|Reinach BL|Burgdorf|Langenthal|Spreitenbach|Dietikon|Regensdorf|Ecublens|Plan-les-Ouates|Meyrin|Carouge|Vernier",
    re.I)


def get(url, data=None, headers=None, timeout=25):
    h = {"User-Agent": UA, "Accept": "application/json, text/xml, application/xml, */*"}
    if data is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def jget(url, data=None):
    return json.loads(get(url, data))


def iso(v):
    if not v:
        return ""
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v / 1000 if v > 1e11 else v, timezone.utc).date().isoformat()
        v = str(v)
        if re.match(r"\d{4}-\d{2}-\d{2}", v):
            return v[:10]
        return parsedate_to_datetime(v).date().isoformat()
    except Exception:
        return ""


def job(title, company, loc, date, url, src):
    return {"t": " ".join(str(title).split()), "c": company, "o": " ".join(str(loc or "").split()), "d": iso(date), "u": url, "s": src}


# ---------- Anbieter ----------

def workday(s):
    host, site = s["host"], s["site"]
    tenant = host.split(".")[0]
    base = f"https://{host}/wday/cxs/{tenant}/{site}"
    seen, out = set(), []
    for q in ("HR", "Human Resources", "People", "Payroll", "Recruit", "Talent", "Personal", "Compensation"):
        posts = []
        for off in (0, 20, 40):
            try:
                res = jget(base + "/jobs", {"appliedFacets": {}, "limit": 20, "offset": off, "searchText": q})
            except Exception:
                break
            posts += res.get("jobPostings", [])
            if off + 20 >= res.get("total", 0):
                break
            time.sleep(PAUSE)
        for p in posts:
            path = p.get("externalPath")
            if not path or path in seen or not HR.search(re.sub(r"\([^)]*\)", " ", p.get("title", ""))):
                continue
            seen.add(path)
            loc, date = p.get("locationsText", ""), ""
            try:
                d = jget(base + path).get("jobPostingInfo", {})
                locs = [d.get("location", "")] + list(d.get("additionalLocations") or [])
                loc = "; ".join(x for x in locs if x)
                cc = (d.get("country") or {}).get("descriptor", "")
                if cc:
                    loc = f"{loc} ({cc})" if cc not in loc else loc
                date = d.get("startDate") or d.get("postedOn")
            except Exception:
                pass
            out.append(job(p["title"], s["name"], loc, date, f"https://{host}/{site}{path}", "Workday"))
            time.sleep(PAUSE)
        time.sleep(PAUSE)
    return out


def greenhouse(s):
    res = jget(f"https://boards-api.greenhouse.io/v1/boards/{s['slug']}/jobs")
    return [job(j["title"], s["name"], (j.get("location") or {}).get("name", ""), j.get("first_published") or j.get("updated_at"), j["absolute_url"], "Greenhouse")
            for j in res.get("jobs", [])]


def smartrecruiters(s):
    out, offset = [], 0
    while True:
        res = jget(f"https://api.smartrecruiters.com/v1/companies/{s['slug']}/postings?country=ch&limit=100&offset={offset}")
        for j in res.get("content", []):
            l = j.get("location") or {}
            out.append(job(j["name"], s["name"], ", ".join(x for x in (l.get("city"), "Schweiz") if x), j.get("releasedDate"),
                           f"https://jobs.smartrecruiters.com/{s['slug']}/{j['id']}", "SmartRecruiters"))
        offset += 100
        if offset >= res.get("totalFound", 0) or offset > 1000:
            return out


def lever(s):
    host = "api.eu.lever.co" if s.get("eu") else "api.lever.co"
    res = jget(f"https://{host}/v0/postings/{s['slug']}?mode=json")
    return [job(j["text"], s["name"], (j.get("categories") or {}).get("location", ""), j.get("createdAt"), j["hostedUrl"], "Lever") for j in res]


def recruitee(s):
    res = jget(f"https://{s['slug']}.recruitee.com/api/offers/")
    return [job(j["title"], s["name"], ", ".join(x for x in (j.get("city"), j.get("country")) if x), j.get("published_at") or j.get("created_at"),
                j.get("careers_url"), "Recruitee") for j in res.get("offers", [])]


def personio(s):
    root = ET.fromstring(get(f"https://{s['slug']}.jobs.personio.de/xml?language=de"))
    out = []
    for p in root.iter("position"):
        f = lambda k: (p.findtext(k) or "").strip()
        out.append(job(f("name"), s["name"], f("office"), f("createdAt"), f"https://{s['slug']}.jobs.personio.de/job/{f('id')}", "Personio"))
    return out


def teamtailor(s):
    root = ET.fromstring(get(f"https://{s['slug']}.teamtailor.com/jobs.rss"))
    out = []
    for it in root.iter("item"):
        locs = [x.text or "" for x in it.iter() if x.tag.endswith("city") or x.tag.endswith("name") and "location" in x.tag]
        out.append(job(it.findtext("title"), s["name"], ", ".join(l for l in locs if l), it.findtext("pubDate"), it.findtext("link"), "Teamtailor"))
    return out


def ashby(s):
    res = jget(f"https://api.ashbyhq.com/posting-api/job-board/{s['slug']}")
    out = []
    for j in res.get("jobs", []):
        if not j.get("isListed", True):
            continue
        cc = (((j.get("address") or {}).get("postalAddress") or {}).get("addressCountry") or "")
        loc = j.get("location", "") + (f" ({cc})" if cc else "")
        out.append(job(j["title"], s["name"], loc, j.get("publishedAt"), j.get("jobUrl"), "Ashby"))
    return out


FETCH = {"workday": workday, "greenhouse": greenhouse, "smartrecruiters": smartrecruiters, "lever": lever,
         "recruitee": recruitee, "personio": personio, "teamtailor": teamtailor, "ashby": ashby}


def main():
    sources = json.load(open(SRC, encoding="utf-8"))["quellen"]
    cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)).date().isoformat()
    jobs, report = {}, []
    for s in sources:
        if s.get("aus"):
            continue
        try:
            raw = FETCH[s["typ"]](s)
        except Exception as ex:
            report.append(f"FEHLER  {s['typ']:<15} {s['name']}: {type(ex).__name__} {str(ex)[:80]}")
            continue
        hits = 0
        for j in raw:
            core = re.sub(r"\([^)]*\)|\[[^]]*\]", " ", j["t"])
            if not j["u"] or not j["t"] or not HR.search(core) or NOT_HR.search(core):
                continue
            if not (s.get("nur_ch") or CH.search(j["o"])):
                continue
            if j["d"] and j["d"] < cutoff:
                continue
            jobs[j["u"]] = j
            hits += 1
        report.append(f"ok      {s['typ']:<15} {s['name']}: {len(raw)} Stellen, davon {hits} HR in CH")
        time.sleep(PAUSE)
    out = sorted(jobs.values(), key=lambda j: (j["d"] or "0000", j["t"]), reverse=True)
    old = {}
    if os.path.exists(OUT):
        old = json.load(open(OUT, encoding="utf-8"))
    ok = sum(1 for r in report if r.startswith("ok"))
    if ok == 0 and old.get("jobs"):
        print("\n".join(report))
        print("Keine Quelle erreichbar, bisherige Liste bleibt.")
        return
    data = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "jobs": out}
    if old.get("jobs") == out:
        data["updated"] = old.get("updated", data["updated"])
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("\n".join(report))
    print(f"\n{len(out)} HR-Stellen in der Schweiz gespeichert ({ok}/{len(report)} Quellen erreichbar).")


if __name__ == "__main__":
    sys.exit(main())
