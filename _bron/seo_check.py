"""Wekelijkse sitecheck: SEO/GEO, interne links, zoeker, portalen en webshoplinks.

Schrijft _bron/rapport/sitecheck.md (en de samenvatting naar $GITHUB_STEP_SUMMARY als die bestaat).
Exitcode 1 bij kritieke fouten (kapotte interne links, ongeldige JSON-LD, portaal niet bijgewerkt,
bestelknop naar verdwenen product), zodat GitHub de eigenaar een melding stuurt.
"""
import json, re, os, sys, html, glob, datetime, collections, urllib.request
from pathlib import Path
from urllib.parse import urlparse, unquote

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
sys.path.insert(0, str(SRC))
import seo, portalen

kritiek, waarsch, info = [], [], []
today = datetime.date.today()


def head(url):
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0 (DFO-sitecheck)"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


# 1. pagina's: titel, omschrijving, h1, canonical, JSON-LD, alt-teksten, dubbele titels
pages = {f.name: f.read_text() for f in sorted(ROOT.glob("*.html"))}
titles, descs = collections.defaultdict(list), collections.defaultdict(list)
ids = {}
noalt = 0
lang, kortd = [], []
for fn, s in pages.items():
    ids[fn] = set(re.findall(r'id="([^"]+)"', s))
    if 'http-equiv="refresh"' in s:
        continue
    t = re.search(r"<title>(.*?)</title>", s, re.S)
    t = html.unescape(t.group(1)) if t else ""
    d = seo.meta(s, "description")
    titles[t].append(fn); descs[d].append(fn)
    if not t:
        kritiek.append(f"{fn}: geen titel")
    elif len(t) > 70:
        lang.append(fn)
    if len(d) < 50:
        kortd.append(fn)
    n1 = len(re.findall(r"<h1[ >]", s))
    if n1 != 1:
        waarsch.append(f"{fn}: {n1} h1-koppen")
    if s.count('rel="canonical"') != 1:
        kritiek.append(f"{fn}: canonical ontbreekt of dubbel")
    ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    if len(ld) != 1:
        kritiek.append(f"{fn}: {len(ld)} JSON-LD-blokken")
    else:
        try:
            json.loads(ld[0])
        except Exception as e:
            kritiek.append(f"{fn}: ongeldige JSON-LD ({e})")
    noalt += len(re.findall(r"<img(?![^>]*\balt=)[^>]*>", s))
if lang:
    waarsch.append(f"{len(lang)} pagina's met een titel langer dan 70 tekens (wordt in Google afgekapt), bijv. " + ", ".join(lang[:5]))
if kortd:
    waarsch.append(f"{len(kortd)} pagina's met een korte omschrijving (< 50 tekens): " + ", ".join(kortd[:8]))
for t, fs in titles.items():
    if len(fs) > 1 and t:
        waarsch.append(f"dubbele titel '{t[:60]}' op {len(fs)} pagina's: {', '.join(fs[:4])}")
if noalt:
    waarsch.append(f"{noalt} afbeeldingen zonder alt-tekst")

# 2. interne links en ankers (ankers die via script filteren tellen niet als fout)
SCRIPT_HASH = {"webshop.html", "kennisbank.html", "nieuws.html", "opleidingen.html"}
kapot = collections.Counter()
for fn, s in pages.items():
    for v in re.findall(r'(?:href|src)="([^"]+)"', s):
        if re.match(r"(https?:|mailto:|tel:|data:|javascript:|//|#|/)", v) or "${" in v:
            continue
        u = urlparse(v)
        p = unquote(u.path)
        if not p:
            continue
        if not (ROOT / p).exists():
            kapot[(fn, v)] += 1
        elif u.fragment and p.endswith(".html") and p not in SCRIPT_HASH and u.fragment not in ids.get(p, set()):
            kapot[(fn, v)] += 1
if kapot:
    kritiek.append(f"{len(kapot)} kapotte interne links, bijv. " + "; ".join(f"{a} → {b}" for a, b in list(kapot)[:8]))

# 3. sitemap en GEO-bestanden
sm = (ROOT / "sitemap.xml").read_text() if (ROOT / "sitemap.xml").exists() else ""
in_sm = set(re.findall(r"<loc>([^<]+)</loc>", sm))
idx_pages = [fn for fn, s in pages.items() if 'http-equiv="refresh"' not in s and fn not in seo.NOINDEX]
mist = [fn for fn in idx_pages if (seo.BASE + ("" if fn == "index.html" else fn)) not in in_sm]
if mist:
    kritiek.append(f"{len(mist)} pagina's ontbreken in sitemap.xml: {', '.join(mist[:6])}")
for f in ("robots.txt", "llms.txt", "llms-full.txt", "assets/img/og-dfo.jpg"):
    if not (ROOT / f).exists():
        kritiek.append(f"{f} ontbreekt")
info.append(f"{len(in_sm)} pagina's in sitemap.xml; {len(idx_pages)} indexeerbare pagina's")

# 4. portalen: actualiteit en aantallen t.o.v. vorige week
tel_f = SRC / "rapport" / "portalen-telling.json"
tel_f.parent.mkdir(exist_ok=True)
vorige = json.loads(tel_f.read_text()) if tel_f.exists() else {}
nu = {}
P = portalen.load()
for key, eigen, oms in portalen.VOLGORDE:
    if key not in P:
        kritiek.append(f"portaal {key}: geen data")
        continue
    p = P[key]
    n = len(p["items"]); nu[key] = n
    age = (today - datetime.date.fromisoformat(p["bijgewerkt"])).days if p["bijgewerkt"] else 999
    regel = f"{p['naam']}: {n} pagina's, bijgewerkt {p['bijgewerkt']}"
    if key in vorige and vorige[key]:
        regel += f" (vorige week {vorige[key]})"
        if n < vorige[key] * 0.7:
            waarsch.append(f"{p['naam']}: aantal pagina's flink gedaald ({vorige[key]} → {n})")
    if age > 9:
        kritiek.append(f"{p['naam']}: data {age} dagen oud (uitlezen mislukt?)")
    st = head(p["home"])
    if st != 200:
        waarsch.append(f"{p['naam']}: {p['home']} geeft HTTP {st}")
    info.append(regel)
for f, label in (("opleidingen.json", "Opleidingsportaal"), ("nvhp.json", "NVHP-planning"), ("nieuws/nieuws.json", "Nieuws")):
    age = (datetime.datetime.now().timestamp() - (SRC / f).stat().st_mtime) / 86400
    d = json.loads((SRC / f).read_text())
    n = len(d.get("cursussen", d.get("items", d.get("data", []))))
    info.append(f"{label}: {n} items")
tel_f.write_text(json.dumps(nu, indent=1))

# 5. zoeker
z = pages.get("zoeken.html", "")
nz = len(re.findall(r'"u":', z))
info.append(f"zoeker: {nz} doorzoekbare items, waarvan {z.count('Portaal · ')} uit de portalen")
if nz < 1000:
    kritiek.append(f"zoeker bevat maar {nz} items")

# 6. bestelknoppen en webshoplinks
prod = sorted({u for s in pages.values() for u in re.findall(r'href="(https://www\.dfobv\.nl/product/[^"]+)"', s)})
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(12) as ex:
    status = dict(zip(prod, ex.map(head, prod)))
dood = [u for u in prod if status[u] == 404]
knop = [u for u in dood if any(f'href="{u}" rel="noopener">Bestellen in de webshop' in s for s in pages.values())]
if knop:
    kritiek.append(f"{len(knop)} bestelknoppen naar verdwenen webshopproducten: " + ", ".join(knop[:6]))
if dood:
    waarsch.append(f"{len(dood)} links naar verdwenen webshopproducten (toevoegen aan _bron/dode_producten.json): " + ", ".join(dood[:8]))
info.append(f"{len(prod)} webshoplinks gecontroleerd, {len(dood)} niet meer bereikbaar")

# rapport
md = [f"# Wekelijkse sitecheck – {today.isoformat()}", "",
      f"**Status:** {'❌ actie nodig' if kritiek else ('⚠️ aandachtspunten' if waarsch else '✅ alles in orde')}", "",
      "## Kritiek", *(f"- {x}" for x in kritiek or ["geen"]), "",
      "## Aandachtspunten", *(f"- {x}" for x in waarsch[:60] or ["geen"]), *([f"- … en {len(waarsch) - 60} meer"] if len(waarsch) > 60 else []), "",
      "## Overzicht", *(f"- {x}" for x in info), ""]
out = "\n".join(md)
(SRC / "rapport" / "sitecheck.md").write_text(out)
if os.environ.get("GITHUB_STEP_SUMMARY"):
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as fh:
        fh.write(out)
print(out)
sys.exit(1 if kritiek else 0)
