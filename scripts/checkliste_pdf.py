"""Erzeugt das PDF der Jahreswechsel-Checkliste aus data/themen.json (einmalig lokal ausführen, braucht Playwright)."""
import json, html, base64, pathlib, sys
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).resolve().parent.parent
slug = sys.argv[1] if len(sys.argv) > 1 else "jahreswechsel-checkliste-2027"
t = next(x for x in json.load(open(root / "data/themen.json", encoding="utf-8"))["themen"] if x["slug"] == slug)
e = html.escape
logo = base64.b64encode((root / "assets/og/logo.png").read_bytes()).decode()
groups = ""
for g in t["checklist"]:
    items = "".join(f'<li><span class="box"></span><div><b>{e(i["t"])}</b>{("<br><span>" + e(i["d"]) + "</span>") if i.get("d") else ""}</div></li>' for i in g["items"])
    groups += f'<section><h2>{e(g["h"])}</h2><ul>{items}</ul></section>'
doc = f"""<!DOCTYPE html><html lang="de-CH"><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 16mm 15mm 18mm; }}
body {{ font-family: 'Nunito','Helvetica Neue',Arial,sans-serif; color:#2b2540; font-size:10.5pt; line-height:1.45; margin:0; }}
header {{ display:flex; align-items:center; gap:12px; border-bottom:3px solid #ffd76e; padding-bottom:10px; margin-bottom:14px; }}
header img {{ width:42px; height:42px; }}
.brand b {{ font-family: Georgia,serif; font-size:17pt; display:block; }}
.brand span {{ color:#d9452f; font-family:Georgia,serif; font-size:10pt; font-weight:600; }}
h1 {{ font-family: Georgia,serif; font-size:21pt; margin:6px 0 6px; }}
.lead {{ color:#4a4560; margin:0 0 14px; }}
h2 {{ font-family: Georgia,serif; font-size:13pt; margin:16px 0 6px; color:#2b2540; padding:5px 10px; background:#fff4d1; border-radius:8px; }}
ul {{ list-style:none; padding:0; margin:0; }}
li {{ display:flex; gap:10px; padding:6px 4px; border-bottom:1px solid #ece8f2; break-inside:avoid; }}
li span:not(.box) {{ color:#4a4560; }}
.box {{ flex:none; width:12px; height:12px; border:1.6px solid #2b2540; border-radius:3px; margin-top:3px; }}
section {{ break-inside:auto; }}
footer {{ margin-top:18px; font-size:8.5pt; color:#6b6580; border-top:1px solid #ece8f2; padding-top:8px; }}
</style></head><body>
<header><img src="data:image/png;base64,{logo}"><div class="brand"><b>HR Radar</b><span>Was HR heute wissen muss</span></div></header>
<h1>{e(t["title"])}</h1>
<p class="lead">{e(t["intro"])}</p>
{groups}
<footer>Stand: November 2026. Allgemeine Information, keine Rechtsberatung; massgebend sind Gesetz, Vertrag, GAV und die Vorgaben Ihrer Ausgleichskasse, Versicherer und Ihres Kantons. Details und Quellen zu jedem Punkt: hr-radar.ch/thema/{slug}.html · Newsletter jeden Dienstag: hr-radar.ch/newsletter.html</footer>
</body></html>"""
out = root / "assets/downloads" / f"hr-radar-{slug}.pdf"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); pg.set_content(doc); pg.wait_for_timeout(300)
    pg.pdf(path=str(out), format="A4", print_background=True, margin={"top": "16mm", "bottom": "18mm", "left": "15mm", "right": "15mm"})
    b.close()
print("PDF:", out, out.stat().st_size // 1024, "KB")
