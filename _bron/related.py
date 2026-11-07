"""Zet op inhoudelijke pagina's een blok 'Verdiep je kennis' met passende DFO-opleidingen en NVHP-masterclasses.

Werkwijze: per pagina wordt het onderwerp bepaald (titel weegt zwaar, daarna de tekst). Opleidingen krijgen
een score op gedeeld onderwerp + gedeelde trefwoorden. Alleen bij voldoende overlap wordt iets getoond.
"""
import json, re, html, datetime
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(__file__).resolve().parent
E = html.escape
NVHP = json.loads((SRC / "nvhp.json").read_text())
NVHP_MC = "https://www.hypothecairplanner.nl/adviseur/kenniscentrum/masterclasses"
NVHP_PORTAL = "https://mc.hypothecairplanner.nl/"

TOPICS = {
    "hypotheken": r"hypothe|woning|financiering|nhg|overwaarde|eigenwoning|toetsinkomen|leidraad|rentemiddeling|geldverstrek|krediet|hypotheekmaster|gedragscode",
    "schade": r"schade|polis|brandverzeker|autoverzeker|aansprakelijk|cyber|clausule|verkeersrecht|avp|volmacht|opstal|motorrijtuig",
    "inkomen": r"arbeidsongeschikt|\baov\b|inkomensverzeker|woonlastenverzeker|verzuim|wia|\bbaz\b",
    "leven": r"pensioen|lijfrente|overlijdensrisico|\borv\b|uitvaart|beleg|vermogen|box ?3|mifid|langstlevende",
    "bedrijfsvoering": r"bedrijfsvoering|ondernemer|portefeuille|jaarrekening|beloning|abonnement|zakelijk financ|liquiditeit|kantoor",
    "compliance": r"\bwft\b|\bwwft\b|\bafm\b|\bavg\b|privacy|compliance|vergunning|sanctie|audit|dienstenwijzer|kifid|integriteit|datalek|zorgplicht|dossier",
    "personeel": r"personeel|medewerker|arbeidsovereenkomst|salaris|werkgever|functioneren|vakbekwaam",
    "nazorg": r"nazorg|onderhoud",
    "estate": r"testament|erfrecht|erfgen|nalaten|estate|langstlevende|wettelijke verdeling|schenk",
    "scheiding": r"scheiding|convenant|ouderschapsplan|draagplicht|alimentatie|samengestelde gezin",
    "ai": r"\bai\b|chatgpt|copilot|kunstmatige intelligentie|legalmike",
    "senioren": r"senior|overwaarde",
}
STOP = set("""deze heeft hebben wordt worden zijn voor naar over door onder tussen tegen zonder binnen buiten
alle onze jouw jullie welke waarin waarbij omdat zoals tijdens training workshop opleiding masterclass
bureau financieel financiele financiële adviseur adviseurs advies klanten klant daarnaast daarom
eendaagse meerdaagse dagdeel basis verdieping praktisch interactief webinar online module leergang
model modellen document documenten overzicht""".split())

NVHP_TOPICS = {
    "leergang financieel relatie": ["hypotheken", "nazorg"], "actualiteiten": ["hypotheken", "compliance"],
    "nbi/cbi": ["hypotheken", "inkomen"], "ai basis": ["ai", "bedrijfsvoering"], "ai gespreksverslagen": ["ai", "hypotheken", "compliance"],
    "ai onderhoud": ["ai", "nazorg", "hypotheken"], "wettelijke verdeling": ["estate"], "beleggen": ["leven"],
    "kracht van aandacht": ["bedrijfsvoering"], "pensioenwet": ["leven"], "draagplicht": ["scheiding", "hypotheken"],
    "estate planning": ["estate", "leven"], "psychologie": ["bedrijfsvoering"], "buiten gedragscode": ["hypotheken"],
    "langstlevende": ["estate", "leven"], "hypotheekmaster": ["hypotheken"], "hypotheken en vermogen": ["hypotheken", "leven"],
    "zelfstandige ondernemers": ["hypotheken", "inkomen"], "fiscaal verleden": ["hypotheken"],
    "testament": ["estate", "hypotheken"], "klimaatrisico": ["hypotheken"], "leidraad": ["hypotheken", "compliance"],
    "overwaarde slim": ["senioren", "hypotheken", "estate"], "samengestelde gezinnen": ["scheiding", "estate"],
    "adviesrapport": ["hypotheken", "compliance"], "senioren en overwaarde": ["senioren", "hypotheken"],
    "zelfstandig wonen": ["hypotheken"],
}

# pagina's waar een opleidingsblok niet logisch is
SKIP = {"index.html", "contact.html", "zoeken.html", "404.html", "zalencentrum.html", "vergadercentrum.html", "over-dfo.html",
        "secretariaten.html", "webshop.html", "agenda-archief.html", "artikelen.html", "info.html", "opleidingen.html",
        "actievoorwaarden-nieuwsbrief-wft.html", "signalen.html", "serviceproviders.html", "performance.html",
        "info-algemene-leveringsvoorwaarden.html", "info-klachtenprocedure.html", "info-privacyverklaring-en-cookies.html",
        "info-onafhankelijkheidsverklaring.html", "info-contact.html", "info-ons-team.html", "info-over-dfo.html",
        "info-home.html", "info-zaalverhuur.html", "info-stemapparatuur.html", "info-congressen.html", "info-blog.html",
        "info-opinie.html", "congressen.html", "kennisbank.html"}
SKIP_PREFIX = ("studio",)


def topics_of(text):
    t = text.lower()
    return {k: len(re.findall(p, t)) for k, p in TOPICS.items() if re.search(p, t)}


def tokens(text):
    return {w for w in re.findall(r"[a-zà-ÿ]{5,}", text.lower()) if w not in STOP}


def nvhp_items():
    nxt = {}
    today = datetime.date.today().isoformat()
    for d in sorted(NVHP["data"], key=lambda x: x["d"]):
        if d["d"] >= today:
            k = d["t"].lower()[:25]
            nxt.setdefault(k, d)
    out = []
    for c in NVHP["cursussen"]:
        if "intervisie" in c["t"].lower():
            continue
        tl = c["t"].lower()
        tp = next((v for k, v in NVHP_TOPICS.items() if k in tl), [])
        nd = nxt.get(tl[:25])
        out.append({"t": c["t"], "u": c["u"], "prijs": c["prijs"], "topics": set(tp), "tok": tokens(c["t"]),
                    "next": nd, "src": "NVHP"})
    return out


GENERIC = {"bedrijfsvoering", "personeel"}
WG_TOPIC = {"Hypotheken": "hypotheken", "Schade": "schade", "Inkomen, leven & pensioen": "leven", "Bedrijfsvoering": "bedrijfsvoering",
            "Compliance": "compliance"}
TITLE_TOPICS = {k: v for k, v in TOPICS.items() if k not in GENERIC}


def dfo_items(cursussen, agenda):
    nxt = {}
    for a in agenda:
        nxt.setdefault(a["u"], a)
    out = []
    for c in cursussen:
        text = c["t"] + " " + c["wg"] + " " + c["s"]
        tp = {k for k, p in TITLE_TOPICS.items() if re.search(p, c["t"].lower())}
        if c.get("cat") in WG_TOPIC:
            tp.add(WG_TOPIC[c["cat"]])
        if re.search(r"inkomen", c["wg"].lower()):
            tp.add("inkomen")
        out.append({"t": c["t"], "u": c["u"], "prijs": c["prijs"], "topics": set(tp), "tok": tokens(text),
                    "next": nxt.get(c["u"]), "src": "DFO", "type": c["type"]})
    return out


MAAND = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]


def card(it):
    nd = it.get("next")
    when = ""
    if nd:
        d = datetime.date.fromisoformat(nd["d"])
        loc = nd.get("loc", "")
        when = f'<p class="fine" style="font-size:.82rem;color:var(--muted);margin:.2em 0 0">Eerstvolgende: {d.day} {MAAND[d.month-1]} {d.year}{" · " + E(loc) if loc else ""}</p>'
    tag = '<span class="tag alt">NVHP-masterclass</span>' if it["src"] == "NVHP" else f'<span class="tag">{E(it.get("type") or "Opleiding")}</span>'
    return (f'<a class="card" href="{E(it["u"])}" rel="noopener">{tag}<h3 style="font-size:1rem">{E(it["t"])}</h3>{when}'
            f'<div style="margin-top:auto;padding-top:10px;font-weight:600">{E(it["prijs"])}</div><span class="more arrow">{"Masterclass volgen" if it["src"] == "NVHP" else "Bekijk &amp; inschrijven"} </span></a>')


def same(a, b):
    ta, tb = tokens(a), tokens(b)
    return bool(ta) and len(ta & tb) / max(len(ta), 1) >= 0.6


def pick(items, ptop, ptok, n, min_score, title="", nvhp=False):
    scored = []
    for it in items:
        if title and same(it["t"], title):
            continue
        spec = [t for t in it["topics"] if t not in GENERIC and t in ptop]
        if nvhp and not spec:
            continue
        shared_t = sum(min(ptop.get(t, 0), 6) * (0.5 if t in GENERIC else 1) for t in it["topics"])
        shared_w = len(it["tok"] & ptok)
        s = shared_t * 2 + shared_w * 3
        if not spec and shared_w < 2:
            continue
        if s >= min_score:
            scored.append((s, it))
    scored.sort(key=lambda x: (-x[0], x[1]["t"]))
    seen, res = set(), []
    for s, it in scored:
        k = it["t"].lower()[:30]
        if k not in seen:
            seen.add(k); res.append(it)
        if len(res) == n:
            break
    return res


def build_related(cursussen, agenda):
    dfo, nv = dfo_items(cursussen, agenda), nvhp_items()
    count = 0
    for f in sorted(ROOT.glob("*.html")):
        if f.name in SKIP or f.name.startswith(SKIP_PREFIX):
            continue
        raw = f.read_text()
        if 'id="verdiep"' in raw or "<main" not in raw:
            continue
        s = BeautifulSoup(raw, "html.parser")
        main = s.find("main")
        h1 = main.find("h1")
        title = h1.get_text(" ", strip=True) if h1 else (s.title.string or "")
        body = main.get_text(" ", strip=True)
        ptop = topics_of(title + " ")
        ptop = {k: v * 4 for k, v in ptop.items()}
        for k, v in topics_of(body).items():
            ptop[k] = ptop.get(k, 0) + v
        # alleen onderwerpen die echt dominant zijn
        if not ptop:
            continue
        top = max(ptop.values())
        ptop = {k: v for k, v in ptop.items() if v >= max(2, top * 0.35)}
        if not ptop:
            continue
        ptok = tokens(title) | {w for w in tokens(body) if body.lower().count(w) >= 2}
        d = pick(dfo, ptop, ptok, 3, 9, title)
        n = pick(nv, ptop, ptok, 3, 9, title, nvhp=True)
        if not d and not n:
            continue
        cols = ""
        inner = "grid" if (d and n) else "grid g3"
        if d:
            cols += f'<div><h3 style="margin-bottom:12px">Opleidingen van Bureau DFO</h3><div class="{inner}" style="gap:14px">{"".join(card(x) for x in d)}</div>' \
                    f'<p style="margin-top:12px"><a class="more arrow" href="opleidingen.html">Alle DFO-opleidingen </a></p></div>'
        if n:
            cols += f'<div><h3 style="margin-bottom:4px">Masterclasses van de NVHP</h3><p class="muted" style="font-size:.88rem;margin:0 0 12px">Ook toegankelijk voor adviseurs die geen NVHP-lid zijn.</p><div class="{inner}" style="gap:14px">{"".join(card(x) for x in n)}</div>' \
                    f'<p style="margin-top:12px"><a class="more arrow" href="{NVHP_MC}" rel="noopener">Alle NVHP-masterclasses </a></p></div>'
        block = (f'<section class="alt" id="verdiep"><div class="wrap"><div class="sec-head"><span class="kicker" style="color:var(--blue)">Verdiep je kennis</span>'
                 f'<h2>Passende opleidingen en masterclasses</h2></div><div class="grid {"g2" if d and n else ""}" style="align-items:start">{cols}</div></div></section>')
        raw = raw.replace("</main>", block + "\n</main>", 1)
        f.write_text(raw)
        count += 1
    return count


def nvhp_section():
    """Volledig NVHP-overzicht voor de opleidingenpagina."""
    items = [x for x in nvhp_items()]
    cards = "".join(card(x) for x in sorted(items, key=lambda x: x["t"].lower()))
    today = datetime.date.today().isoformat()
    rows = ""
    for d in sorted(NVHP["data"], key=lambda x: (x["d"], x["tijd"])):
        if d["d"] < today:
            continue
        dd = datetime.date.fromisoformat(d["d"])
        cur = next((c for c in NVHP["cursussen"] if c["t"].lower()[:20] == d["t"].lower()[:20]), None)
        href = cur["u"] if cur else NVHP_PORTAL
        rows += (f'<a class="date" href="{E(href)}" rel="noopener"><div class="d"><b>{dd.day}</b><span>{MAAND[dd.month-1]}</span></div>'
                 f'<div><div class="t">{E(d["t"])}</div><div class="m">{E(d["tijd"])} · {E(d["loc"])} · {E(d["doc"])}</div></div><div class="p">NVHP</div></a>')
    return f"""<section id="nvhp"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Open voor alle financieel adviseurs</span><h2>Masterclasses van de NVHP</h2>
  <p>De masterclasses van de NVHP staan open voor iedere financieel adviseur, ook als je geen lid bent van de NVHP. Bureau DFO voert het secretariaat van de NVHP. Voor Erkend Hypothecair Planners tellen de masterclasses mee voor hun permanente educatie: zij volgen per kalenderjaar minimaal drie verschillende masterclasses om de titel te mogen blijven voeren. De prijs ligt in 2026 tussen € 162,50 en € 243,50 per masterclass. Inschrijven gaat via het <a href="{NVHP_PORTAL}" rel="noopener">NVHP-opleidingsportaal</a>; niet-leden maken daar een account aan, leden loggen in zodat hun gegevens al zijn ingevuld.</p></div>
  <div class="grid g3">{cards}</div>
  <h3 style="margin-top:36px">Geplande data NVHP</h3>
  <div class="list">{rows}</div>
  <div class="btns"><a class="btn btn-primary arrow" href="{NVHP_PORTAL}" rel="noopener">Masterclass volgen</a><a class="btn btn-ghost" href="{NVHP_MC}" rel="noopener">Regels en voorwaarden masterclasses</a></div>
</div></section>"""
