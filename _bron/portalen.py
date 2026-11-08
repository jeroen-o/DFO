"""Inhoud van de DFO-portalen (uitgelezen door portalen/fetch.js) op de site: overzichtspagina, zoeker en archieven.

  python3 _bron/portalen.py --sync   werkt signalen.json (archief DFO Signalen) bij vanuit de portaldata
"""
import json, re, html, datetime, sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
D = SRC / "portalen"
E = html.escape
MAAND = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]

VOLGORDE = [  # key, eigen pagina op deze site, korte omschrijving
    ("signalen", "signalen.html", "Wekelijkse nieuwsbrief met signalen uit de markt voor onafhankelijk financieel adviseurs."),
    ("serviceproviders", "serviceproviders.html", "Vergelijk serviceproviders op kwaliteit, snelheid en dienstverlening; met profielen en bijeenkomsten."),
    ("pawft", "", "Permanente educatie Wft: per module wat er nieuw is, oefenvragen, begrippen en het vakbekwaamheidsdossier."),
    ("aipa", "", "AI-verordening en AVG voor advieskantoren: AI-geletterdheid, register, kennistoets en praktijkthema's."),
    ("nazorg", "nazorg.html", "Documentatie en ondersteuning voor nazorg en onderhoud op financiële producten."),
    ("vergaderruimte", "vergadercentrum.html", "Vergaderruimte huren in Amersfoort en Hoevelaken."),
]
GENERIEK = re.compile(r"^(agenda opleidingen|ook een signaal|jouw wekelijkse update|introductie|primaire diensten|aanvullende diensten|kerngegevens|contact|terug naar)", re.I)


def schoon(s):
    s = re.sub(r"^(Sluiten\s+)?(033 258 04 60\s+)?(info@dfobv\.nl\s+)?", "", s or "").strip()
    s = re.sub(r"^Terug naar overzicht\s+", "", s)
    return re.sub(r"\s+", " ", s)


def kort(s, n=220):
    s = schoon(s)
    if len(s) <= n:
        return s
    k = s[:n].rsplit(" ", 1)[0]
    return k.rstrip(",.;:") + "…"


def week_maandag(w, j):
    return datetime.date.fromisocalendar(j, w, 1)


def load():
    out = {}
    for key, eigen, oms in VOLGORDE:
        f = D / f"{key}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        items = []
        for it in d["items"]:
            if re.search(r"-kopie(-\d+)?/?$", it["u"]):  # dubbele conceptpagina's
                continue
            it = dict(it)
            heads = [h for h in it.get("h", []) if not GENERIEK.match(h)]
            if key == "signalen":
                m = re.search(r"week-(\d+)-(20\d\d)", it["u"])
                if m:
                    w, j = int(m.group(1)), int(m.group(2))
                    it["t"] = f"DFO Signalen week {w} – {j}"
                    it["d"] = week_maandag(w, j).isoformat()
                elif "archief" in it["u"]:
                    it["t"] = "Archief DFO Signalen"
                else:
                    it["t"] = "DFO Signalen – de wekelijkse nieuwsbrief"
                it["x"] = ("In deze editie: " + "; ".join(heads[:6]) + ".") if heads else kort(it.get("tekst", ""))
            else:
                if not it.get("x") or len(it["x"]) < 40:
                    it["x"] = kort(it.get("tekst", ""))
                it["x"] = kort(it["x"], 260)
            it["heads"] = heads
            items.append(it)
        if key == "signalen":
            items.sort(key=lambda i: i.get("d") or "", reverse=True)
        out[key] = {"naam": d["portaal"], "home": d["home"], "eigen": eigen, "oms": oms, "bijgewerkt": d.get("bijgewerkt", "")[:10], "items": items}
    return out


def zoekitems():
    """Items voor de site-zoeker."""
    res = []
    for key, p in load().items():
        for it in p["items"]:
            res.append({"u": it["u"], "p": "Portaal · " + p["naam"], "h": it["t"],
                        "x": (it["x"] + " " + " ".join(it["heads"]) + " " + schoon(it.get("tekst", "")))[:1400]})
    return res


def build(page, hero, callout):
    P = load()
    if not P:
        return 0
    nav = "".join(f'<a href="#{k}">{E(p["naam"])}</a>' for k, p in P.items())
    secties = ""
    for i, (k, p) in enumerate(P.items()):
        rows = ""
        for it in p["items"]:
            dt = ""
            if it.get("d") and k in ("signalen", "serviceproviders", "pawft", "aipa"):
                try:
                    d = datetime.date.fromisoformat(it["d"][:10])
                    dt = f'<time datetime="{d.isoformat()}">{d.day} {MAAND[d.month-1]} {d.year}</time> · '
                except ValueError:
                    pass
            rows += (f'<li><a href="{E(it["u"])}" rel="noopener">{E(it["t"])}</a>'
                     f'<p class="muted">{dt}{E(it["x"])}</p></li>')
        eigen = f'<a class="btn btn-ghost" href="{p["eigen"]}">Meer op deze site</a>' if p["eigen"] else ""
        secties += f"""<section{' class="alt"' if i % 2 else ''} id="{k}"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">{len(p["items"])} pagina's</span><h2>{E(p["naam"])}</h2><p>{E(p["oms"])}</p>
  <div class="btns"><a class="btn btn-primary arrow" href="{E(p["home"])}" rel="noopener">Naar het portaal</a>{eigen}</div></div>
  <ul class="pt-list">{rows}</ul>
</div></section>"""
    body = hero("Alle DFO-portalen", "Alles uit de portalen van Bureau DFO op één plek: DFO Signalen, Serviceproviders, Wft Permanent Actueel, AI Permanent Actueel, Nazorg & Onderhoud en Vergaderruimte Amersfoort. Elke week bijgewerkt.",
                crumbs=["Portalen"])
    body += f'<section class="tight"><div class="wrap"><div class="wb-nav">{nav}</div></div></section>' + secties
    body += callout("Zoek je iets specifieks?", "De zoeker bovenaan elke pagina doorzoekt ook alle portalen.", "zoeken.html", "Naar de zoeker")
    n = sum(len(p["items"]) for p in P.values())
    page("portalen.html", "Alle DFO-portalen – Signalen, Serviceproviders, Wft en AI Permanent Actueel – Bureau DFO",
         f"Overzicht van {n} pagina's uit de DFO-portalen: DFO Signalen, Serviceproviders, Wft Permanent Actueel, AI Permanent Actueel, Nazorg & Onderhoud en Vergaderruimte Amersfoort.", body)
    return n


def sync():
    """signalen.json (archief op signalen.html) bijwerken uit de portaldata."""
    P = load()
    msg = []
    if "signalen" in P:
        ed = []
        for it in P["signalen"]["items"]:
            m = re.search(r"week-(\d+)-(20\d\d)/?$", it["u"])
            if not m:
                continue
            w, j = int(m.group(1)), int(m.group(2))
            a = week_maandag(w, j); b = a + datetime.timedelta(days=6)
            if a.month == b.month:
                rng = f"{a.day} - {b.day} {MAAND[b.month-1]} {b.year}"
            else:
                rng = f"{a.day} {MAAND[a.month-1]}{' ' + str(a.year) if a.year != b.year else ''} - {b.day} {MAAND[b.month-1]} {b.year}"
            ed.append({"t": f"DFO signalen week {w}", "d": rng, "u": it["u"], "_k": (j, w)})
        ed.sort(key=lambda e: e["_k"], reverse=True)
        oud = json.loads((SRC / "signalen.json").read_text())
        if len(ed) >= len(oud) * 0.8:
            (SRC / "signalen.json").write_text(json.dumps([{k: v for k, v in e.items() if k != "_k"} for e in ed], ensure_ascii=False, indent=1))
            msg.append(f"signalen.json: {len(ed)} edities (was {len(oud)})")
    return msg


if __name__ == "__main__" and "--sync" in sys.argv:
    print("\n".join(sync()) or "niets bijgewerkt")
