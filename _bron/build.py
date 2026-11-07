#!/usr/bin/env python3
"""Genereert de statische DFO-website (HTML in de root van de repo).

Gebruik:  python3 _bron/build.py
Bron-data: _bron/opleidingen.json, _bron/documenten.json, _bron/columns.json
De gegenereerde .html-bestanden worden gewoon gecommit; GitHub Pages heeft geen build-step nodig.
"""
import json, html, re, datetime, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_bron"
E = html.escape

OPL = json.loads((SRC / "opleidingen.json").read_text())
DOCS = json.loads((SRC / "documenten.json").read_text())
COLS = json.loads((SRC / "columns.json").read_text())

PORTAL = "https://www.dfo-opleidingen.nl"
SHOP = "https://www.dfobv.nl"
TEL = "033 258 04 60"
TEL_HREF = "tel:+31332580460"
MAIL = "info@dfobv.nl"
ADRES = "De Wel 14–16, 3871 MV Hoevelaken"

NAV = [
    ("opleidingen.html", "Opleidingen"),
    ("documenten.html", "Documenten"),
    ("themas.html", "Thema’s"),
    ("compliance.html", "Compliance"),
    ("abonnementen.html", "Abonnementen"),
    ("zalencentrum.html", "Zalen"),
    ("studio.html", "Studio"),
    ("over-dfo.html", "Over DFO"),
]

ICONS = {
    "cap": '<path d="M22 10L12 5 2 10l10 5 10-5z"/><path d="M6 12v5c3 2 9 2 12 0v-5"/>',
    "doc": '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M8 13h8M8 17h6"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "room": '<rect x="3" y="4" width="18" height="12" rx="1"/><path d="M8 20h8M12 16v4"/>',
    "mic": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2 20c.8-3.5 3.6-5.5 7-5.5s6.2 2 7 5.5"/><circle cx="17.5" cy="9" r="2.5"/><path d="M17 14.5c2.6.2 4.4 2 5 5"/>',
    "calc": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 11h2M12 11h0M16 11h0M8 15h2M12 15h0M16 15v3"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "event": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "brief": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18"/>',
}


def icon(name):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def page(fname, title, desc, body, extra_head="", scripts=""):
    nav = "".join(
        f'<li><a href="{h}"{" aria-current=page" if h == fname else ""}>{E(t)}</a></li>' for h, t in NAV)
    year = datetime.date.today().year
    doc = f"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#005EA9">
<link rel="icon" type="image/png" href="assets/img/favicon.png">
<link rel="preload" href="assets/fonts/poppins-regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/site.css">
{extra_head}
</head>
<body>
<a class="skip" href="#inhoud">Naar de inhoud</a>
<div class="topbar"><div class="wrap">
  <a href="{TEL_HREF}">☎ {TEL}</a>
  <a href="mailto:{MAIL}">{MAIL}</a>
  <a href="{SHOP}/agenda/" rel="noopener">Agenda</a>
  <a href="https://kennisbank.dfobv.nl/" rel="noopener">Kennisbank</a>
  <a href="{SHOP}/mijn-account/" rel="noopener">Mijn account</a>
  <a href="{PORTAL}/inloggen-prs/standaard" rel="noopener">Inloggen opleidingsportaal</a>
</div></div>
<header class="site"><div class="wrap">
  <a class="logo" href="index.html" aria-label="Bureau DFO – home"><img src="assets/img/logo.png" alt="Bureau DFO – dienstverlening voor financiële ondernemers" width="613" height="145"></a>
  <button class="menu-btn" aria-expanded="false" aria-controls="mainnav">Menu</button>
  <nav class="main" id="mainnav" aria-label="Hoofdmenu"><ul>{nav}<li><a href="zoeken.html" aria-label="Zoeken" title="Zoeken"{" aria-current=page" if fname == "zoeken.html" else ""}><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true" style="vertical-align:-3px"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg><span class="sr"> Zoeken</span></a></li><li><a class="cta" href="contact.html">Contact</a></li></ul></nav>
</div></header>
<main id="inhoud">
{body}
</main>
<footer class="site"><div class="wrap">
  <div class="fgrid">
    <div>
      <div class="flogo"><img src="assets/img/logo.png" alt="Bureau DFO" width="613" height="145"></div>
      <p>Jouw partner waar het gaat om succesvol ondernemen in de financiële dienstverlening. Sinds 1992.</p>
      <p>{ADRES}<br>Tel: <a href="{TEL_HREF}">{TEL}</a><br>Mail: <a href="mailto:{MAIL}">{MAIL}</a></p>
      <h4 style="margin-top:22px">Op de hoogte blijven?</h4>
      <p class="fnews">Schrijf je dan in voor onze nieuwsbrief</p>
      <a class="btn btn-light" href="abonnementen.html#aanvragen" style="padding:9px 16px">Aanmelden</a>
    </div>
    <div><h4>Aanbod</h4><ul>
      <li><a href="opleidingen.html">Opleidingen &amp; agenda</a></li>
      <li><a href="documenten.html">Modeldocumenten &amp; contracten</a></li>
      <li><a href="compliance.html">DFO Compliance</a></li>
      <li><a href="abonnementen.html">Abonnementen &amp; servicepakketten</a></li>
      <li><a href="onderzoek.html">Onderzoek</a></li>
      <li><a href="nazorg-calculator.html">Calculator nazorgabonnement</a></li>
    </ul></div>
    <div><h4>Faciliteiten</h4><ul>
      <li><a href="zalencentrum.html">DFO Zalencentrum</a></li>
      <li><a href="studio.html">DFO Studio</a></li>
      <li><a href="congressen.html">Congressen</a></li>
      <li><a href="secretariaten.html">Secretariaatsvoering</a></li>
      <li><a href="columns.html">Columns Jurjen Oosterbaan</a></li>
      <li><a href="themas.html">Thema’s</a></li>
      <li><a href="https://www.youtube.com/@bureaudfo6854/videos" rel="noopener">Webinars op YouTube</a></li>
      <li><a href="https://www.youtube.com/@VIPcongres/videos" rel="noopener">Videoproducties op YouTube</a></li>
      <li><a href="zoeken.html">Zoeken</a></li>
    </ul></div>
    <div><h4>Webshop &amp; portalen</h4><ul>
      <li><a href="{SHOP}/agenda/" rel="noopener">Agenda opleidingen</a></li>
      <li><a href="{SHOP}/product/bureau-dfo-kennisflits/" rel="noopener">DFO Kennisflits</a></li>
      <li><a href="{SHOP}/product/bureau-dfo-servicepakket/" rel="noopener">DFO – Servicepakket</a></li>
      <li><a href="{SHOP}/product-categorie/hypotheken/" rel="noopener">Hypotheken</a></li>
      <li><a href="{SHOP}/product-categorie/bedrijfsvoering/" rel="noopener">Bedrijfsvoering</a></li>
      <li><a href="{SHOP}/product-categorie/inkomen/" rel="noopener">Inkomen</a></li>
      <li><a href="{SHOP}/product-categorie/levenpensioen/" rel="noopener">Leven &amp; Pensioen</a></li>
      <li><a href="{SHOP}/product-categorie/personeel/" rel="noopener">Personeel / HR</a></li>
      <li><a href="{SHOP}/product-categorie/schade/" rel="noopener">Schade</a></li>
      <li><a href="{SHOP}/product-categorie/alle-opleidingen/" rel="noopener">Alle opleidingen</a></li>
      <li><a href="https://kennisbank.dfobv.nl/" rel="noopener">Kennisbank</a></li>
      <li><a href="{SHOP}/mijn-account/" rel="noopener">Mijn account</a></li>
    </ul></div>
    <div><h4>Bureau DFO</h4><ul>
      <li><a href="over-dfo.html">Over ons</a></li>
      <li><a href="over-dfo.html#team">Ons team</a></li>
      <li><a href="over-dfo.html#werken-bij">Werken bij</a></li>
      <li><a href="contact.html">Contact &amp; route</a></li>
      <li><a href="{SHOP}/algemene-leveringsvoorwaarden/" rel="noopener">Algemene leveringsvoorwaarden</a></li>
      <li><a href="{SHOP}/klachtenprocedure/" rel="noopener">Klachtenprocedure</a></li>
      <li><a href="{SHOP}/privacyverklaring-en-cookies/" rel="noopener">Privacyverklaring</a></li>
    </ul></div>
  </div>
  <div class="fbottom"><span>© {year} Bureau DFO B.V.</span><span><a href="https://www.linkedin.com/company/bureaudfo" rel="noopener">LinkedIn</a> · <a href="https://www.dfosignalen.nl/" rel="noopener">DFO Signalen</a></span></div>
</div></footer>
<script>
(function(){{var b=document.querySelector('.menu-btn'),n=document.getElementById('mainnav');
if(b)b.addEventListener('click',function(){{var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)}});}})();
</script>
{scripts}
</body>
</html>
"""
    (ROOT / fname).write_text(doc)


def hero(title, lead="", kicker="", crumbs=None, img=None, btns="", small=True):
    cr = ""
    if crumbs:
        cr = '<div class="crumbs"><a href="index.html">Home</a> › ' + " › ".join(crumbs) + "</div>"
    im = f'<div class="img"><img src="{img}" alt="" width="960" height="640"></div>' if img else ""
    k = f'<span class="kicker">{kicker}</span>' if kicker else ""
    return f"""<section class="hero{' small' if small and not img else ''}"><div class="wrap">
<div>{cr}{k}<h1>{title}</h1>{f'<p class="lead">{lead}</p>' if lead else ''}{f'<div class="btns">{btns}</div>' if btns else ''}</div>{im}
</div></section>"""


def callout(title, text, btn_href="contact.html", btn_txt="Neem contact op"):
    return f"""<section class="tight"><div class="wrap"><div class="callout">
<div><h2>{title}</h2><p>{text}</p></div>
<div><a class="btn btn-light arrow" href="{btn_href}">{btn_txt}</a></div>
</div></div></section>"""


def mailto(to, subject, body=""):
    from urllib.parse import quote
    q = f"?subject={quote(subject)}"
    if body:
        q += f"&body={quote(body)}"
    return f"mailto:{to}{q}"


# ---------------------------------------------------------------- woordelijke omzetting oude pagina's
from verbatim import blocks as vblocks

IMGMAP = {
    "podcastproducties": "podcast", "dfo-studio": "studio", "provider": "video",
    "studio-verhuur-met-technische-ondersteuning": "studioverhuur", "screenshot-2025-01-20-at-10-52-21": "content",
    "whatsapp-image-2025-01-20-at-10-55-13": "studio2", "training-en-e-learning-modules-doelgericht-leren": "elearning",
    "robert-jan-van-loon-linkedin": "robert-jan", "congress": "congres", "vip-2024-960x0": "vip",
    "webinar-echtscheiding-250x184": "inkomen", "motiveren-leenruimte-buiten-trhk-250x184": "hypotheken",
    "leven-en-pesioen": "leven", "schade": "schade", "opleidingen": "opleidingen",
    "adult-blond-hair-blurred-background": "personeel", "opleiding3-250x184-1-250x184": "opleiding3",
    "business-services-21": "bedrijfsvoering", "singalen": "signalen", "clausules-250x184": "clausules",
    "wsorv": "lijfrente", "nazorg-onderhoud": "nazorg", "jurjen-oosterbaan": "jurjen", "agaat-1": "agaat",
    "expertisegroepschade": "expertisegroep", "de-wel-14-16": "de-wel", "1-superzaal": "superzaal",
}


def img_src(old):
    base = old.split("/")[-1]
    base = re.sub(r"\.(\d+x\d+(x\d+x\d+)?)\.", ".", base)
    name, ext = base.rsplit(".", 1)
    new = IMGMAP.get(name)
    if not new:
        return None
    return f"assets/img/{new}.svg" if ext == "svg" else f"assets/img/{new}.jpg"


def li_fmt(item):
    # "<strong>Label</strong><br>tekst" -> label op eigen regel
    item = re.sub(r"^<strong>(.*?)</strong>\s*(<br>)?\s*", r"<strong>\1</strong> ", item)
    return f"<li>{item}</li>"


def btn_html(t, u, cls="btn-primary"):
    ext = ' rel="noopener"' if u.startswith("http") else ""
    if u == "contact.html" and cls == "btn-primary":
        pass
    return f'<a class="btn {cls} arrow" href="{E(u)}"{ext}>{E(t)}</a>'


def yt_html(ids):
    frames = "".join(
        f'<div class="yt"><iframe src="https://www.youtube-nocookie.com/embed/{i}?rel=0" title="Video Bureau DFO" loading="lazy" '
        f'allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div>'
        for i in ids)
    return f'<div class="yt-grid">{frames}</div>'


def render_units(bl):
    """Rendert een reeks blokken. Reeksen [img?] h3 p* btn? worden kaarten."""
    out, i, n = [], 0, len(bl)
    units, pend_img = [], None

    def flush_units():
        nonlocal units
        if not units:
            return
        if len(units) == 1 and not units[0]["img"]:
            u = units[0]
            out.append(f'<h3>{E(u["h"])}</h3>' + "".join(u["body"]) + "".join(u["btns"]))
        else:
            cols = "g3" if len(units) % 3 == 0 or len(units) > 4 else ("g2" if len(units) in (2, 4) else "g3")
            cards = ""
            for u in units:
                im = f'<div class="ph"><img src="{u["img"]}" alt="" loading="lazy"></div>' if u["img"] else ""
                link = u["btns_raw"][0][1] if u["btns_raw"] else None
                body = "".join(u["body"])
                more = "".join(f'<a class="more arrow" href="{E(x[1])}"{" rel=noopener" if x[1].startswith("http") else ""}>{E(x[0])} </a>' for x in u["btns_raw"])
                cards += (f'<div class="card{" img" if im else ""}">{im}<div class="body">' if im else '<div class="card">') + \
                         f'<h3>{E(u["h"])}</h3>{body}{more}' + ("</div></div>" if im else "</div>")
            out.append(f'<div class="grid {cols} cards-inline">{cards}</div>')
        units = []

    cur = None
    while i < n:
        k, v = bl[i]
        if k == "img":
            pend_img = img_src(v)
            i += 1
            continue
        if k == "h3":
            if cur:
                units.append(cur)
            cur = {"h": v, "img": pend_img, "body": [], "btns": [], "btns_raw": []}
            pend_img = None
            i += 1
            continue
        if cur is not None and k == "btn" and cur["btns_raw"]:
            units.append(cur); cur = None; flush_units()
            continue
        if cur is not None:
            if k == "p":
                cur["body"].append(f"<p>{v}</p>")
            elif k in ("ul", "ol"):
                cur["body"].append(f'<ul class="check">{"".join(li_fmt(x) for x in v)}</ul>')
            elif k == "btn":
                cur["btns_raw"].append(v)
                cur["btns"].append(f'<div class="btns">{btn_html(*v)}</div>')
            elif k == "yt":
                cur["body"].append(yt_html([v]))
            i += 1
            # een p na een kaart die al een knop had, hoort niet meer bij de kaart
            if i < n and cur["btns_raw"] and bl[i][0] in ("p", "ul", "ol"):
                units.append(cur); cur = None; flush_units()
            continue
        flush_units()
        if k == "p":
            out.append(f"<p>{v}</p>")
        elif k == "ul":
            out.append(f'<ul class="check">{"".join(li_fmt(x) for x in v)}</ul>')
        elif k == "ol":
            out.append(f'<ol class="steps-ol">{"".join(li_fmt(x) for x in v)}</ol>')
        elif k == "btn":
            btns = [v]
            while i + 1 < n and bl[i + 1][0] == "btn":
                i += 1; btns.append(bl[i][1])
            out.append('<div class="btns">' + "".join(btn_html(t, u, "btn-primary" if j == 0 else "btn-ghost") for j, (t, u) in enumerate(btns)) + "</div>")
        elif k == "yt":
            ids = [v]
            while i + 1 < n and bl[i + 1][0] == "yt":
                i += 1; ids.append(bl[i][1])
            out.append(yt_html(ids))
        i += 1
    if cur:
        units.append(cur)
    flush_units()
    return "".join(out)


def render_verbatim(rel, crumbs, side_img=None, hero_img=None, skip_until_h1=True, cta_last=True):
    """Hele oude pagina woordelijk: h1 + eerste alinea's -> hero, elke h2 -> eigen sectie."""
    bl = vblocks(rel)
    title, lead, sub = None, [], None
    rest = []
    seen_h1 = False
    for idx, (k, v) in enumerate(bl):
        if not seen_h1 and k == "h1":
            title, seen_h1 = v, True
            continue
        rest.append((k, v))
    # lead: alinea's direct na h1 tot eerste kop/knop
    while rest and rest[0][0] in ("p", "img") and (rest[0][0] == "img" or len(lead) < 3):
        if rest[0][0] == "p":
            lead.append(rest[0][1])
        rest.pop(0)
    if title is None and rest and rest[0][0] == "h2":
        title = rest.pop(0)[1]
        while rest and rest[0][0] in ("p", "img"):
            if rest[0][0] == "p":
                lead.append(rest[0][1])
            rest.pop(0)
    # secties
    secs, cur = [], (None, [])
    for k, v in rest:
        if k == "h2":
            secs.append(cur); cur = (v, [])
        else:
            cur[1].append((k, v))
    secs.append(cur)
    secs = [s for s in secs if s[0] or s[1]]
    html_ = ""
    for j, (h, bl2) in enumerate(secs):
        is_cta = cta_last and j == len(secs) - 1 and h and len(bl2) <= 3 and any(k == "btn" for k, _ in bl2) and not any(k == "yt" for k, _ in bl2)
        if is_cta:
            txt = " ".join(re.sub(r"<[^>]+>", "", v) for k, v in bl2 if k == "p")
            b = next(v for k, v in bl2 if k == "btn")
            html_ += f'<section class="tight"><div class="wrap"><div class="callout"><div><h2>{E(h)}</h2><p>{txt}</p></div><div><a class="btn btn-light arrow" href="{E(b[1])}">{E(b[0])}</a></div></div></div></section>'
            continue
        inner = render_units(bl2)
        head = f"<h2>{E(h)}</h2>" if h else ""
        cls = ' class="alt"' if j % 2 == 1 else ""
        html_ += f'<section{cls}><div class="wrap"><div class="prose">{head}{inner}</div></div></section>'
    crumbs = [c.replace("{t}", E(title or "")) for c in crumbs]
    hero_html = hero(E(title or ""), " ".join(lead), crumbs=crumbs, img=hero_img, small=hero_img is None)
    return title, " ".join(re.sub(r"<[^>]+>", "", x) for x in lead), hero_html + html_



def sections_of(rel):
    out, cur = {}, None
    for k, v in vblocks(rel):
        if k in ("h1", "h2"):
            cur = v; out[cur] = []
        elif cur is not None:
            out[cur].append((k, v))
    return out


# ---------------------------------------------------------------- data opleidingen
def clean(s):
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()


def werkgebied_hoofd(w):
    w = w.lower()
    if "schade" in w:
        return "Schade"
    if "hypothe" in w:
        return "Hypotheken"
    if "compliance" in w:
        return "Compliance"
    if "bedrijfsvoering" in w:
        return "Bedrijfsvoering"
    if "inkomen" in w or "leven" in w or "pensioen" in w:
        return "Inkomen, leven & pensioen"
    return "Overig"


cursussen = []
for r in OPL["cursussen"]:
    c = r["cols"] + ["", "", "", ""]
    cursussen.append({
        "t": clean(c[0]), "type": clean(c[1]), "wg": clean(c[2]), "cat": werkgebied_hoofd(c[2]),
        "prijs": clean(c[3]).replace("€", "€ ").replace("€  ", "€ "), "u": PORTAL + (r["href"] or "/cursussen/cursussen"),
        "s": clean(r.get("summary", "")),
    })
cursussen.sort(key=lambda x: x["t"].lower())


def match_course(title):
    t = title.lower()
    best, score = None, 0
    tw = set(re.findall(r"[a-zà-ü]{4,}", t))
    for c in cursussen:
        cw = set(re.findall(r"[a-zà-ü]{4,}", c["t"].lower()))
        if not cw:
            continue
        s = len(tw & cw) / max(len(tw | cw), 1)
        if s > score:
            best, score = c, s
    return best if score >= 0.45 else None


agenda = []
for r in OPL["evenementen"]:
    c = r["cols"] + [""] * 6
    try:
        d = datetime.datetime.strptime(c[1].strip(), "%d-%m-%Y").date()
    except ValueError:
        continue
    m = match_course(c[0])
    agenda.append({"t": clean(c[0]), "d": d.isoformat(), "loc": clean(c[2]), "doc": clean(c[3]),
                   "prijs": clean(c[5]), "u": m["u"] if m else PORTAL + "/alle-cursus-evenementen/overzicht",
                   "cat": m["cat"] if m else ""})
agenda.sort(key=lambda x: x["d"])
MAANDEN = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
MAANDEN_LANG = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september",
                "oktober", "november", "december"]

# ---------------------------------------------------------------- pagina's

def build_home():
    upcoming = agenda[:4]
    up_html = "".join(date_row(a) for a in upcoming)
    bl = vblocks("index.html")
    get = lambda h: next(bl[i + 1][1] for i, (k, v) in enumerate(bl) if k == "h2" and v == h)
    t1 = "Resultaten Onderzoek serviceproviders 2026 II zijn bekend"
    t2 = "Aangeboden door de winnaars"
    calc = get("Gratis calculator 'Onderhoud- en nazorgabonnement'")
    calc_extra = [v for k, v in bl[[i for i, b in enumerate(bl) if b == ("p", calc)][0] + 1:] if k == "p"][:2]
    start = [i for i, b in enumerate(bl) if b == ("h3", "Hypotheken")][0] - 1
    tiles = [(k, v.replace("Doucmenten", "Documenten").replace("alle document<br>", "alle documenten<br>") if k == "p" else v) for k, v in bl[start:]]
    body = hero(
        "Bureau DFO",
        "Jouw partner waar het gaat om succesvol ondernemen in de financiële dienstverlening",
        kicker="Sinds 1992 · Hoevelaken", img="assets/img/de-wel.jpg", small=False,
        btns='<a class="btn btn-light arrow" href="opleidingen.html">Bekijk opleidingen</a>'
             '<a class="btn btn-ghost" href="contact.html">Neem contact op</a>')
    body += f"""
<section class="tight alt"><div class="wrap"><div class="stats">
  <div class="stat"><b>{len(cursussen)}</b><span>opleidingen &amp; trainingen</span></div>
  <div class="stat"><b>200+</b><span>modeldocumenten &amp; contracten</span></div>
  <div class="stat"><b>7</b><span>zalen voor groepen tot 70 personen</span></div>
  <div class="stat"><b>3.000+</b><span>cursisten per jaar in Hoevelaken</span></div>
</div></div></section>

<section><div class="wrap">
  <div class="news">
    <a class="card img" href="assets/pdf/persbericht-bureau-dfo-meedenken-met-kantoor-bepaalt-waardering-serviceproviders.pdf">
      <div class="ph"><img src="assets/img/persbericht.jpg" alt="" loading="lazy" width="960" height="608"></div>
      <div class="body"><span class="tag">Onderzoek</span><h3>{E(t1)}</h3><p>{get(t1)}</p>
      <span class="more arrow">Lees hier het persbericht </span></div></a>
    <a class="card img" href="https://www.dfobv.nl/wp-content/uploads/2026/10/Samenvatting-Performance-onderzoek-Kwaliteit-binnendienst-en-acceptatie-2026.pdf" rel="noopener">
      <div class="ph"><img src="assets/img/performance.jpg" alt="" loading="lazy" width="960" height="676"></div>
      <div class="body"><span class="tag">Gratis download</span><h3>{E(t2)}</h3><p>{get(t2)}</p>
      <span class="more arrow">Download hier de samenvatting </span></div></a>
    <a class="card img" href="columns.html#{COLS[0]['slug']}">
      <div class="ph"><img src="assets/img/jurjen.jpg" alt="" loading="lazy" width="658" height="370"></div>
      <div class="body"><span class="tag">Column</span><h3>{E(COLS[0]['titel'])}</h3>
      <p>Lees hier de nieuwste column van Jurjen Oosterbaan Martinius</p>
      <span class="more arrow">Lees de column </span></div></a>
  </div>
</div></section>

<section class="alt"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Wat we doen</span><h2>Alles onder één dak</h2>
  <p>Van kennisontwikkeling tot uitvoering: Bureau DFO biedt financiële dienstverleners en hun brancheorganisaties een breed pakket aan diensten, allemaal onder één dak in Hoevelaken.</p></div>
  <div class="grid g3">
    {svc_card("opleidingen.html","cap","Opleidingen","— praktijkgerichte kennis voor financieel adviseurs")}
    {svc_card("secretariaten.html","users","Secretariaten","— ledenadministratie en bestuursondersteuning uit handen genomen")}
    {svc_card("zalencentrum.html","room","Zalen","— vergader- en cursusruimtes inclusief ontvangst")}
    {svc_card("studio.html","mic","Studio","— webinar-, podcast- en videoproducties")}
    {svc_card("compliance.html","shield","Compliance","— grip op wet- en regelgeving, van Wft tot AVG")}
    {svc_card("onderzoek.html","chart","Onderzoek","— onafhankelijk onderzoek voor de financiële adviesketen")}
  </div>
</div></section>

<section><div class="wrap split">
  <div>
    <span class="kicker" style="color:var(--blue)">Binnenkort</span><h2>Eerstvolgende opleidingen</h2>
    <p class="muted">Een greep uit de agenda. Aanmelden gaat via het DFO-opleidingsportaal.</p>
    <div class="btns"><a class="btn btn-primary arrow" href="opleidingen.html#agenda">Volledige agenda</a></div>
  </div>
  <div class="list">{up_html}</div>
</div></section>

<section class="alt"><div class="wrap split rev">
  <div>
    <span class="kicker" style="color:var(--blue)">Gratis tool</span><h2>Gratis calculator ‘Onderhoud- en nazorgabonnement’</h2>
    <p>{calc}</p>{"".join(f'<p class="muted" style="font-size:.92rem">{x}</p>' for x in calc_extra)}
    <div class="btns"><a class="btn btn-primary arrow" href="https://www2.dfobv.nl/abonnement-dashboard/" target="_blank" rel="noopener">Naar de online calculator</a><a class="btn btn-ghost" href="nazorg-calculator.html">Meer informatie</a></div>
  </div>
  <div class="media"><img src="assets/img/calculator.jpg" alt="Schermafbeelding van de calculator" loading="lazy" width="960" height="968"></div>
</div></section>

<section><div class="wrap">
  <div class="sec-head"><h2>Meer informatie</h2></div>
  {render_units(tiles)}
</div></section>
""" + callout("Benieuwd wat wij voor u kunnen betekenen?",
              "Neem telefonisch contact op via 033 258 04 60, wij denken graag met u mee. Of stuur een mail naar info@dfobv.nl en wij reageren binnen één werkdag.")
    page("index.html", "Bureau DFO – succesvol ondernemen in de financiële dienstverlening",
         "Bureau DFO - Jouw partner waar het gaat om succesvol ondernemen in de financiële dienstverlening",
         body)


def svc_card(href, ic, title, text):
    return f'<a class="card" href="{href}"><div class="icon">{icon(ic)}</div><h3>{title}</h3><p>{text}</p><span class="more arrow">Meer informatie </span></a>'


def ext_card(href, title, text):
    return f'<a class="card" href="{href}" rel="noopener"><h3>{title}</h3><p>{text}</p><span class="more arrow">Bezoek website </span></a>'


def date_row(a):
    d = datetime.date.fromisoformat(a["d"])
    meta = " · ".join(x for x in [a["loc"], a["doc"]] if x)
    return (f'<a class="date" href="{E(a["u"])}" rel="noopener"><div class="d"><b>{d.day}</b><span>{MAANDEN[d.month-1]}</span></div>'
            f'<div><div class="t">{E(a["t"])}</div><div class="m">{E(meta)}</div></div><div class="p">{E(a["prijs"])}</div></a>')


def build_opleidingen():
    cats = ["Hypotheken", "Schade", "Inkomen, leven & pensioen", "Bedrijfsvoering", "Compliance", "Overig"]
    cats = [c for c in cats if any(x["cat"] == c for x in cursussen)]
    types = sorted({c["type"] for c in cursussen if c["type"]})
    chips = '<button class="chip" data-cat="" aria-pressed="true">Alle</button>' + "".join(
        f'<button class="chip" data-cat="{E(c)}" aria-pressed="false">{E(c)}</button>' for c in cats)
    topts = '<option value="">Alle vormen</option>' + "".join(f'<option>{E(t)}</option>' for t in types)
    locs = sorted({a["loc"] for a in agenda if a["loc"]})
    lopts = '<option value="">Alle locaties</option>' + "".join(f'<option>{E(l)}</option>' for l in locs)
    body = hero("Opleidingen voor financieel dienstverleners",
                "Praktijkgerichte trainingen, masterclasses en meerdaagse leergangen. Kies een opleiding en meld je direct aan via het DFO-opleidingsportaal.",
                crumbs=["Opleidingen"],
                btns='<a class="btn btn-light arrow" href="#aanbod">Bekijk het aanbod</a><a class="btn btn-ghost" href="#agenda">Agenda</a>')
    body += f"""
<section id="aanbod"><div class="wrap">
  <div class="sec-head"><h2>Overzicht cursussen</h2><p>Hier vind je ons volledige aanbod opleidingen. Niet helemaal duidelijk welke opleiding voor jou de juiste is? We geven je graag advies!</p></div>
  <div class="chips" id="catChips" role="group" aria-label="Werkgebied">{chips}</div>
  <div class="filters">
    <input type="search" id="q" placeholder="Zoek op onderwerp, bijv. AI, Wwft, AOV…" aria-label="Zoek opleiding">
    <select id="type" aria-label="Vorm">{topts}</select>
  </div>
  <div class="count" id="cnt"></div>
  <div class="list" id="courses"></div>
</div></section>

<section class="alt" id="agenda"><div class="wrap">
  <div class="sec-head"><h2>Agenda</h2><p>Geplande opleidingsdagen. Klik op een datum voor details en aanmelden in het opleidingsportaal.</p></div>
  <div class="filters"><select id="loc" aria-label="Locatie">{lopts}</select></div>
  <div class="list" id="dates"></div>
  <p class="muted" style="font-size:.85rem;margin-top:12px">Beschikbaarheid en actuele data vind je altijd in het <a href="{PORTAL}/alle-cursus-evenementen/overzicht" rel="noopener">opleidingsportaal</a>.</p>
</div></section>

<section><div class="wrap split">
  <div>
    <span class="kicker" style="color:var(--blue)">Incompany workshops</span>
    <h2>Zie je een opleiding die interessant is voor diverse collega’s?</h2>
    <p>Kies dan voor het gemak van het verzorgen van de opleiding bij jou op kantoor. De docent komt naar jouw locatie toe en zal daar de training verzorgen op de gewenste dag en tijd.</p>
    <h3>Wat kun je verwachten van ons bij een incompany aanvraag?</h3>
    <p>Een workshop op maat gemaakt voor jouw onderneming, die past bij het niveau van de medewerkers. Het is bij jullie op kantoor, of een eigen gekozen locatie (dit scheelt reistijd) maar het kan ook bij ons op locatie in Hoevelaken. Doordat het een op maat gemaakte opleiding is, is het mogelijk om langer stil te staan bij de punten die binnen jullie organisatie belangrijk zijn.</p>
    <h3>Welke workshops zijn beschikbaar voor incompany?</h3>
    <p>Alle opleidingen die je op onze website ziet zijn beschikbaar voor incompany.</p>
    <h3>Hoe vraag je informatie aan voor een incompany workshop?</h3>
    <p>Je kunt een incompany opleiding vrijblijvend aanvragen door een aanvraag te mailen naar: <a href="mailto:opleidingen@dfobv.nl">opleidingen@dfobv.nl</a>. Wij nemen dan zo spoedig mogelijk contact met je op.</p>
    <div class="btns"><a class="btn btn-primary arrow" href="{mailto('opleidingen@dfobv.nl','Aanvraag incompany opleiding')}">Vraag incompany aan</a></div>
  </div>
  <div class="media"><img src="assets/img/grote-zaal.jpg" alt="Cursuszaal bij DFO in Hoevelaken" loading="lazy" width="960" height="456"></div>
</div></section>

<section class="alt"><div class="wrap grid g3">
  <div class="card"><div class="icon">{icon('users')}</div><h3>Welkom op het opleidingsportaal</h3><p>Je kunt je direct aanmelden voor een opleiding als je een account aanmaakt. Dat is handig, want zo kan je zelf altijd terugvinden voor welke opleidingen je ooit bent aangemeld en wat de status daarvan is.</p><a class="more arrow" href="{PORTAL}/inloggen-prs/standaard" rel="noopener">Inloggen of account maken </a></div>
  <div class="card"><div class="icon">{icon('brief')}</div><h3>Korting met servicepakket</h3><p>Met een DFO Servicepakket krijg je € 95,- korting op 2 of 3 opleidingen per jaar, plus gratis deelname aan het Webinar Actualiteiten.</p><a class="more arrow" href="abonnementen.html">Bekijk servicepakketten </a></div>
  <div class="card"><div class="icon">{icon('mail')}</div><h3>Heb je vragen over onze opleidingen of lukt aanmelden niet?</h3><p>Wij helpen je graag verder! Neem contact op met onze afdeling Opleidingen. Wij zijn bereikbaar op 033-258 04 60 of per mail via opleidingen@dfobv.nl.</p><a class="more arrow" href="mailto:opleidingen@dfobv.nl">opleidingen@dfobv.nl </a></div>
</div></section>
"""
    data = json.dumps({"c": cursussen, "a": agenda}, ensure_ascii=False)
    js = """<script>
const D=__DATA__;const M=['jan','feb','mrt','apr','mei','jun','jul','aug','sep','okt','nov','dec'];
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let cat='';const q=document.getElementById('q'),ty=document.getElementById('type'),lo=document.getElementById('loc');
function renderC(){const t=q.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);
 const r=D.c.filter(c=>(!cat||c.cat===cat)&&(!ty.value||c.type===ty.value)&&t.every(w=>(c.t+' '+c.s+' '+c.wg).toLowerCase().includes(w)));
 document.getElementById('cnt').textContent=r.length+(r.length===1?' opleiding':' opleidingen');
 document.getElementById('courses').innerHTML=r.length?'<div class="row head"><span>Opleiding</span><span>Werkgebied</span><span>Vorm</span><span style="text-align:right">Prijs</span></div>'+r.map(c=>`<a class="row" href="${esc(c.u)}" rel="noopener"><div><div class="t">${esc(c.t)}</div>${c.s?`<div class="s">${esc(c.s)}</div>`:''}</div><div class="m">${esc(c.wg)}</div><div class="m">${esc(c.type)}</div><div class="p">${esc(c.prijs)}</div></a>`).join(''):'<div class="empty">Geen opleidingen gevonden. Probeer een andere zoekterm.</div>';}
function renderA(){const r=D.a.filter(a=>!lo.value||a.loc===lo.value);
 document.getElementById('dates').innerHTML=r.length?r.map(a=>{const d=new Date(a.d+'T12:00');return `<a class="date" href="${esc(a.u)}" rel="noopener"><div class="d"><b>${d.getDate()}</b><span>${M[d.getMonth()]} ${String(d.getFullYear()).slice(2)}</span></div><div><div class="t">${esc(a.t)}</div><div class="m">${esc([a.loc,a.doc].filter(Boolean).join(' · '))}</div></div><div class="p">${esc(a.prijs)}</div></a>`}).join(''):'<div class="empty">Geen geplande data voor deze locatie.</div>';}
document.querySelectorAll('#catChips .chip').forEach(b=>b.addEventListener('click',()=>{cat=b.dataset.cat;document.querySelectorAll('#catChips .chip').forEach(x=>x.setAttribute('aria-pressed',x===b));renderC();}));
q.addEventListener('input',renderC);ty.addEventListener('change',renderC);lo.addEventListener('change',renderA);
const h=new URLSearchParams(location.search).get('q');if(h){q.value=h;}
renderC();renderA();
</script>""".replace("__DATA__", data)
    page("opleidingen.html", "Opleidingen & agenda – Bureau DFO",
         "Het volledige opleidingsaanbod van Bureau DFO voor financieel adviseurs: hypotheken, schade, inkomen, compliance en bedrijfsvoering. Met agenda en incompany.",
         body, scripts=js)


def build_documenten():
    total = len({i["u"] for d in DOCS for g in d["groups"] for i in g["items"]})
    chips = '<button class="chip" data-cat="" aria-pressed="true">Alle</button>' + "".join(
        f'<button class="chip" data-cat="{d["slug"]}" aria-pressed="false">{E(d["title"])}</button>' for d in DOCS)
    docicon = icon("doc")
    cats_html = ""
    for d in DOCS:
        n = sum(len(g["items"]) for g in d["groups"])
        groups = ""
        for g in d["groups"]:
            items = "".join(
                f'<li><a href="{E(i["u"])}" rel="noopener" data-t="{E(i["t"].lower())}">{docicon}<span>{E(i["t"])}</span></a></li>'
                for i in g["items"])
            groups += f'<div class="doc-group"><h4>{E(g["name"])}</h4><ul class="doc-list">{items}</ul></div>'
        cats_html += f'<div class="doc-cat" id="{d["slug"]}" data-cat="{d["slug"]}"><h3>{E(d["title"])} <span class="n">{n}</span></h3>{groups}</div>'
    body = hero("Modeldocumenten &amp; contracten",
                f"Van Wft tot AVG, van hypotheken tot schade: {total} praktische modellen, checklists en contracten die je direct op kantoor kunt inzetten.",
                crumbs=["Documenten"],
                btns='<a class="btn btn-light arrow" href="#zoeken">Zoek een document</a><a class="btn btn-ghost" href="abonnementen.html">Gratis documenten met servicepakket</a>')
    body += f"""
<section id="zoeken"><div class="wrap">
  <div class="filters"><input type="search" id="dq" placeholder="Zoek bijv. ‘dienstenwijzer’, ‘Wwft’ of ‘convenant’…" aria-label="Zoek document"></div>
  <div class="chips" id="dChips" role="group" aria-label="Categorie">{chips}</div>
  <div class="count" id="dcnt"></div>
  <div id="docs">{cats_html}</div>
  <div class="empty" id="dempty" hidden>Geen documenten gevonden.</div>
  <div class="note" style="margin-top:24px"><a href="https://www.dfobv.nl/wp-content/uploads/2019/08/DFO-Overzicht-van-alle-modeldocumenten-en-contracten.pdf" rel="noopener"><strong>Download het overzicht van alle modeldocumenten en contracten (pdf)</strong></a><br>Bestellen en downloaden gaat via de DFO-webshop. Sommige documenten staan in meerdere categorieën. Heb je een <a href="abonnementen.html">servicepakket</a>, dan krijg je 2 of 3 documenten per jaar gratis.</div>
</div></section>
""" + callout("Hulp nodig bij het inrichten van je bedrijfsvoering?",
              "DFO Compliance helpt je met een geborgde bedrijfsvoering: van dienstenwijzer tot Wwft-beleid.",
              "compliance.html", "Naar DFO Compliance")
    js = """<script>
const dq=document.getElementById('dq');let dc='';
function f(){const t=dq.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);let n=new Set();
 document.querySelectorAll('.doc-cat').forEach(c=>{let cv=0;const catOk=!dc||c.dataset.cat===dc;
  c.querySelectorAll('.doc-group').forEach(g=>{let gv=0;g.querySelectorAll('li').forEach(li=>{const a=li.firstElementChild;const ok=catOk&&t.every(w=>a.dataset.t.includes(w));li.hidden=!ok;if(ok){gv++;n.add(a.href)}});g.hidden=!gv;cv+=gv});
  c.hidden=!cv});
 document.getElementById('dcnt').textContent=n.size+(n.size===1?' document':' documenten');document.getElementById('dempty').hidden=n.size>0;}
document.querySelectorAll('#dChips .chip').forEach(b=>b.addEventListener('click',()=>{dc=b.dataset.cat;document.querySelectorAll('#dChips .chip').forEach(x=>x.setAttribute('aria-pressed',x===b));f();}));
dq.addEventListener('input',f);
if(location.hash){const b=document.querySelector('#dChips .chip[data-cat="'+location.hash.slice(1)+'"]');if(b)b.click();}
f();
</script>"""
    page("documenten.html", "Modeldocumenten & contracten – Bureau DFO",
         "Ruim 200 modeldocumenten, checklists en contracten voor financieel advieskantoren: Wft, Wwft, AVG, hypotheken, schade, inkomen, personeel en nazorg.",
         body, scripts=js)


def build_abonnementen():
    def nb(title, text, prijs, voorbeeld, extra="", lees=None, vlabel="Voorbeeld nieuwsbrief", alabel="Abonnement aanvragen", ahref="#aanvragen"):
        lm = f'<a class="more arrow" href="{lees}" rel="noopener" style="margin:0 0 .6em">Lees meer </a>' if lees else ""
        return f'''<div class="card price"><h3>{title}</h3><p>{text}</p>{lm}<div class="amount" style="margin-top:auto">{prijs}</div>{extra}
<div class="btns" style="margin-top:16px"><a class="btn btn-primary" href="{ahref}"{' rel="noopener"' if ahref.startswith("http") else ""}>{alabel}</a><a class="btn btn-ghost" href="{voorbeeld}" rel="noopener">{vlabel}</a></div></div>'''
    sp1 = ["2x opleiding met € 95,- korting", "1x deelname aan Webinar Actualiteiten", "2 gratis documenten", "Wft nieuwsbrief", "Helpdesk voor al je Wft vragen", "Jaarlijks het Onderzoek waardering assurantieportefeuilles", "50% korting op 1 informatierapport naar keuze", "50% korting op een Klanttevredenheidsonderzoek", "50% korting op nieuwsteksten voor je particuliere relaties", "5 gratis faillissementscontroles"]
    sp2 = ["3x opleiding met € 95,- korting", "1x deelname aan Webinar Actualiteiten", "3 gratis documenten", "Wft nieuwsbrief", "Helpdesk voor al je Wft vragen", "Jaarlijks het Onderzoek waardering assurantieportefeuilles", "Keuze uit 1 informatierapport", "Klanttevredenheidsonderzoek", "Nieuwsteksten voor je particuliere relaties", "10 gratis faillissementscontroles"]
    li = lambda xs: "".join(f"<li>{E(x)}</li>" for x in xs)
    sec = sections_of("diensten/onze-abonnementen/index.html")
    faq, curq = [], None
    for k, v in sec["Niet zeker wat alles inhoudt?"]:
        if k == "h3":
            curq = [v, []]; faq.append(curq)
        elif curq and k == "p":
            curq[1].append(v)
    faq_html = "".join(f'<details class="card" style="padding:18px 22px"><summary style="font-weight:600;cursor:pointer">{E(q)}</summary>{"".join(f"<p style=\'margin:.8em 0 0\'>{p}</p>" for p in ps)}</details>' for q, ps in faq)
    body = hero("Onze abonnementen",
                "Met onze nieuwsbrieven en servicepakketten blijf je op de hoogte én profiteer je van voordeel. Kies wat bij je past.",
                crumbs=["Abonnementen"], btns='<a class="btn btn-light arrow" href="#aanvragen">Direct aanvragen</a>')
    body += f"""
<section><div class="wrap">
  <div class="sec-head"><h2>Servicepakketten</h2><p>Een pakket voor het hele bedrijf. Iedereen bij jou op kantoor mag gebruik maken van deze producten en diensten.</p></div>
  <div class="grid g2">
    <div class="card price featured"><span class="badge">MEEST GEKOZEN</span><h3>DFO Servicepakket</h3>
      <div class="amount">€ 39,50 <small>per maand excl. btw</small></div><p class="fine">Totale waarde € 835,- per jaar<br>Je betaalt € 39,50 per maand, excl. btw (€ 474,- per jaar)<br>Maandelijks opzegbaar, opzegtermijn 1 maand</p>
      <ul class="check">{li(sp1)}</ul><a class="btn btn-primary" href="#aanvragen" style="margin-top:auto">Abonnement aanvragen</a></div>
    <div class="card price"><span class="badge" style="background:var(--blue-dd)">MEEST COMPLEET</span><h3>DFO Servicepakket - Plus</h3>
      <div class="amount">€ 65,- <small>per maand excl. btw</small></div><p class="fine">Totale waarde € 1.600,- per jaar<br>Je betaalt € 65,- per maand, excl. btw (€ 780,- per jaar)<br>Maandelijks opzegbaar, opzegtermijn 1 maand</p>
      <ul class="check">{li(sp2)}</ul><a class="btn btn-primary" href="#aanvragen" style="margin-top:auto">Abonnement aanvragen</a></div>
  </div>
</div></section>

<section class="alt"><div class="wrap">
  <div class="sec-head"><h2>Nieuwsbrieven</h2><p>Onze periodieke publicaties en benchmarks. Alle prijzen zijn per maand, exclusief btw en maandelijks opzegbaar.</p></div>
  <div class="grid g4">
    {nb("Wft Nieuwsbrief","Blijf op de hoogte met deze wekelijkse nieuwsbrief van de laatste ontwikkelingen in wet- en regelgeving rond de Wft. Toegankelijk uitgelegd en direct toepasbaar in de praktijk. Zit ook in beide servicepakketten.","€ 23,50 <small>per maand</small>","https://kennisbank.dfobv.nl/", lees="https://www.dfobv.nl/product/nieuwsbrief-wft/")}
    {nb("Nieuwsbrief Hypotheken","Elke maand bieden wij je vier kant-en-klare teksten over hypotheekontwikkelingen die je kunt inzetten op je website, sociale media of in je eigen nieuwsbrief.","€ 15,- <small>per maand</small>","https://hypotheken-update.nl/hypnwkr/113_crt/index.html", lees="https://www.dfobv.nl/product/commerciele-hypotheek-artikelen-nieuwsbrief-hypotheken-voor-particulieren/")}
    {nb("Nieuwsbrief Particulier","Elke maand bieden wij je vier kant-en-klare teksten voor jouw particuliere relaties. Denk aan nieuwsberichten op het gebied van schade, hypotheken en diversen andere actuele ontwikkelingen, die je kunt inzetten op je website, sociale media of in je eigen nieuwsbrief. Met het servicepakket krijg je 50% korting op deze nieuwsbrief, bij het servicepakket plus is die inbegrepen.","€ 15,- <small>per maand</small>","https://www.financieel-alert.nl/nwkr/365_vej/index.php", lees="https://www.dfobv.nl/product/commerciele-teksten-particuliere-klanten/")}
    {nb("Signalen","Jouw wekelijkse update met signalen uit de markt, speciaal voor onafhankelijk financieel adviseurs.","€ Gratis","https://www.dfosignalen.nl/", vlabel="Voorbeeld signaal", alabel="Gratis aanmelden", ahref="https://c.spotler.com/ct/m13/k1/9pW48L55hi0RE83hRjww-Hd3uMqXFZGIQCHugsxWgB97fqn8ZL7W6w87AC_kFwQ78iEMI_KouOA-T5fJ06QX3_zpXI9Vdj1NHcjMiQSKt0M/fXUsq5LID7H9H5Z")}
  </div>
</div></section>

<section><div class="wrap">
  <div class="sec-head"><h2>Niet zeker wat alles inhoudt?</h2><p>Geen probleem, hier onder staat per punt wat je kunt verwachten.</p></div>
  <div class="grid g2" style="align-items:start">{faq_html}</div>
</div></section>

<section class="alt"><div class="wrap split">
  <div><img src="assets/img/expertisegroep.jpg" alt="Expertisegroep Schadebehandeling" loading="lazy" width="832" height="417" style="max-width:340px;margin-bottom:20px">
  <h2>Expertisegroep Schadebehandeling</h2><p>Activiteiten van de Expertisegroep Schadebehandeling</p>
  <ul class="check"><li>Actuele en praktijkgerichte workshops;</li><li>Expertmeetings;</li><li>Modelcontracten &amp; -formulieren;</li><li>Opmerkelijk (nieuwsalert met relevante informatie);</li><li>WhatsApp groep voor de deelnemers van de Expertisegroep;</li><li>Eén plek voor alle informatie;</li><li>Onderzoek en benchmark;</li><li>Bewijs van deelname.</li></ul>
  <h3 style="margin-top:28px">Toch nog een vraag?</h3><p>Neem direct contact op met Agaat van Ekeren, relatiemanager bij Bureau DFO. Zij is verantwoordelijk voor onze abonnementen en helpt je graag verder.</p><p><a href="mailto:avanekeren@dfobv.nl">avanekeren@dfobv.nl</a></p>
  <div class="btns"><a class="btn btn-primary" href="#aanvragen">Aanmelden</a><a class="btn btn-ghost" href="https://expertisegroepschade.nl/informatie/" rel="noopener">Meer over de Expertisegroep</a></div></div>
  <div class="card" id="aanvragen">
    <h2 style="font-size:1.5rem">Abonneer op een of meerdere van onze nieuwsbrieven of servicepakketten</h2>
    <p class="muted">Weet je al welk abonnement je wilt? Vraag het dan aan via het formulier hieronder. Wij nemen dan contact met jou op. (Je e-mailprogramma opent met de ingevulde aanvraag.)</p>
    <form class="f" id="aboForm">
      <div class="two"><label>Naam<input name="naam" required autocomplete="name"></label><label>Kantoor<input name="kantoor" autocomplete="organization"></label></div>
      <div class="two"><label>E-mail<input name="email" type="email" required autocomplete="email"></label><label>Telefoon<input name="tel" type="tel" autocomplete="tel"></label></div>
      <fieldset><legend>Interesse in</legend>
        {''.join(f'<label class="opt"><input type="checkbox" name="abo" value="{E(v)}"> {E(v)}</label>' for v in ["Wft Nieuwsbrief","Nieuwsbrief Hypotheken","Nieuwsbrief Particulier","Signalen","DFO Servicepakket","DFO Servicepakket - Plus","Ik wil lid worden van de Expertisegroep Schadebehandeling","Wil geen abonnementen maar heb vragen over een product"])}
      </fieldset>
      <label>Opmerkingen of vragen<textarea name="opm"></textarea></label>
      <button class="btn btn-primary" type="submit">Aanvraag opstellen</button>
      <p class="hint">We reageren binnen 1 werkdag. Je gegevens gebruiken we alleen om je aanvraag te verwerken.</p>
    </form>
  </div>
</div></section>
"""
    js = """<script>
document.getElementById('aboForm').addEventListener('submit',e=>{e.preventDefault();const f=new FormData(e.target);
const abo=f.getAll('abo');const b=`Naam: ${f.get('naam')}\\nKantoor: ${f.get('kantoor')}\\nE-mail: ${f.get('email')}\\nTelefoon: ${f.get('tel')}\\n\\nInteresse in:\\n- ${abo.join('\\n- ')||'(niet opgegeven)'}\\n\\nOpmerkingen:\\n${f.get('opm')}`;
location.href='mailto:avanekeren@dfobv.nl?subject='+encodeURIComponent('Aanvraag abonnement – '+(abo[0]||'DFO'))+'&body='+encodeURIComponent(b);});
</script>"""
    page("abonnementen.html", "Abonnementen: Wft-nieuwsbrief en servicepakketten – Bureau DFO",
         "DFO Servicepakket, Wft-nieuwsbrief, nieuwsbrieven Hypotheken en Particulier en DFO Signalen. Maandelijks opzegbaar.",
         body, scripts=js)


def build_zalen():
    rooms = [
        ("Boardroom", "boardroom", "Vergaderruimte", "tot 12 personen", "Vergadering / hybride vergadering", "Scherm, camera, flipover"),
        ("Muurhuizen", "muurhuizen", "Vergaderruimte", "tot 8 personen", "Vergadering / hybride vergadering", "Scherm, camera, flipover"),
        ("Grote zaal", "grote-zaal", "Cursusruimte", "24 - 30 personen", "School / Theater / U-vorm / Toetsopstelling", "Scherm, flipover"),
        ("Kleine zaal", "kleine-zaal", "Cursusruimte", "12 personen", "School / U-vorm / Toetsopstelling", "Scherm, flipover"),
        ("Havik", "havik", "Cursusruimte", "17 personen", "School / U-vorm / Toetsopstelling", "Scherm, flipover"),
        ("Koppelpoort", "koppelpoort", "Cursusruimte", "15 - 18 personen", "School / U-vorm / Toetsopstelling", "Scherm, flipover"),
        ("Lange Jan", "lange-jan", "Cursusruimte", "17 personen", "School / U-vorm / Toetsopstelling", "Scherm, flipover"),
        ("Superzaal (combi kleine + grote zaal)", "superzaal", "Bijeenkomstruimte", "50 - 70 personen", "Theater / cabaret", "Schermen, microfoon, flipover"),
    ]
    cards = ""
    for n, img, typ, cap, ops, fac in rooms:
        cards += f'''<div class="card img room"><div class="ph"><img src="assets/img/{img}.jpg" alt="Zaal {E(n)}" loading="lazy" width="960" height="640"></div>
<div class="body"><h3>{E(n)}</h3>
<p style="font-size:.9rem">{E(typ)} • {E(cap)}<br>Opstelling: {E(ops)}<br>Faciliteiten: {E(fac)}</p>
<a class="more arrow" href="{mailto('info@dfozalen.nl', f'Aanvraag zaal {n}', f'Ik wil graag zaal {n} reserveren.%0A%0ADatum:%0AAantal personen:%0AOpstelling:%0ACatering:%0A'.replace('%0A', chr(10)))}">Aanvragen </a></div></div>'''
    zs = sections_of("diensten/dfo-zalencentrum/index.html")
    intro = render_units([b for b in zs["Alle ruimte om samen te komen, te leren én te inspireren!"] if b[0] != "btn"])
    body = hero("DFO Zalencentrum", "Van boardroom tot superzaal: in Hoevelaken vind je voor elke vergadering, training of bijeenkomst de ruimte die bij je past.",
                crumbs=["Zalencentrum"], img="assets/img/superzaal.jpg", small=False,
                btns=f'<a class="btn btn-light arrow" href="{mailto("info@dfozalen.nl","Offerte aanvraag zaalhuur")}">Offerte aanvragen</a><a class="btn btn-ghost" href="#zalen">Bekijk de zalen</a>')
    body += f"""
<section><div class="wrap split">
  <div><h2>Alle ruimte om samen te komen, te leren én te inspireren!</h2>{intro}</div>
  <div class="media"><img src="assets/img/kaart.jpg" alt="Kaart: DFO bij knooppunt Hoevelaken" loading="lazy" width="960" height="442"></div>
</div></section>

<section class="alt" id="zalen"><div class="wrap">
  <div class="sec-head"><h2>Vergaderruimtes, cursusruimtes en bijeenkomstruimte</h2></div>
  <div class="grid g4">{cards}</div>
</div></section>
<section class="tight"><div class="wrap"><div class="note"><strong>Ontvangst en kantine</strong><br>Bij het huren van onze zalen word je altijd ontvangen door een van onze gastvrouwen en heb je toegang tot onze kantine.</div></div></section>
""" + callout("Een ruimte reserveren of combineren?",
              "We denken graag mee over de beste opstelling en logistiek. Neem contact met ons op voor beschikbaarheid en cateringopties. Werkt de knop niet? Stuur dan een mail naar info@dfozalen.nl.",
              mailto("info@dfozalen.nl", "Offerte aanvraag zaalhuur"), "Vraag een offerte aan")
    page("zalencentrum.html", "Vergaderruimte huren in Hoevelaken – DFO Zalencentrum",
         "Zeven vergader- en cursuszalen voor 8 tot 70 personen bij knooppunt Hoevelaken. Gratis parkeren, persoonlijke ontvangst.", body)


TEAM = [
    ("Agaat van Ekeren", "Relatiemanager", "agaat", "avanekeren@dfobv.nl", ["Agaat is verantwoordelijk voor de klanttevredenheid van al onze klanten en werkt samen met Jurjen Oosterbaan Martinius aan diversen projecten. Daarnaast is zij verantwoordelijk voor alle abonnementen die wij aanbieden. Denk hierbij aan het Wft Serviceabonnement en nieuwsbrieven die u bij ons kunt afnemen. Ben je benieuwd naar onze dienstverlening, of wat wij voor je kunnen betekenen, neem dan contact op met Agaat."]),
    ("Anja Heetmayer Knorth", "Administratief medewerker/gastvrouw", "anja", "aheetmayer@dfobv.nl", ["Anja heet je welkom als gastvrouw bij Bureau DFO en doet er alles aan om jouw deelname aan onze bijeenkomsten prettig te laten verlopen."]),
    ("Gijs", "Huisvriend", "gijs", "", []),
    ("Gea van Esveld", "Gastvrouw", "gea", "gastvrouw@dfobv.nl", ["Gea heet je welkom als gastvrouw bij Bureau DFO en doet er alles aan om jouw deelname aan onze bijeenkomsten prettig te laten verlopen."]),
    ("Ilona Vellekoop", "Bestuurssecretaresse", "ilona", "ivellekoop@dfobv.nl", ["Ilona is bij Bureau DFO werkzaam als secretaresse voor de NVHP"]),
    ("Jurjen Oosterbaan Martinius", "Algemeen directeur", "jurjen", "joosterbaan@dfobv.nl", ["Al 36 jaar is Jurjen eigenaar van Bureau DFO, in ons kantoorpand in Hoevelaken. Jurjen is een autoriteit op het gebied van Wft. Hij kan je ondersteunen op het gebied van ondernemerschap en strategische vraagstukken en is een veelgevraagd spreker en fungeert vaak als sparringspartner.", "Je kunt hem o.a. benaderen over de volgende onderwerpen: Wft, klankborden, strategie, efficiënte bedrijfsvoering en het schrijven van columns. Wil je weten wat hij voor jou kan betekenen? Neem contact op met Agaat van Ekeren."]),
    ("Martine Verhagen", "Bestuurssecretaresse", "martine", "mverhagen@dfobv.nl", ["Martine is bij Bureau DFO werkzaam als secretaresse voor een aantal secretariaten."]),
    ("Nico den Besten", "Medewerker digitale innovatie", "nico", "ndenbesten@dfobv.nl", ["Nico is verantwoordelijk voor de opmaak en verzending van diverse digitale nieuwsbrieven. Daarbij onderhoudt en actualiseert hij de website, biedt hij technische ondersteuning aan gebruikers en is hij betrokken bij de diverse uitingen die Bureau DFO plaatst op social media.", "Het ontwerp van een logo, huisstijl of document neemt Nico ook voor zijn rekening."]),
    ("Robert-Jan van Loon", "Consultant", "robert-jan", "rjvanloon@dfocompliance.nl", ["Robert-Jan is als consultant verantwoordelijk voor het begeleiden van wft-vergunningaanvragen en het beantwoorden van wft- en compliance gerelateerde vragen van klanten."]),
    ("Ronald van Hamersveld", "Financial controller", "ronald", "rvanhamersveld@dfobv.nl", ["Ronald is verantwoordelijk voor de financiële administratie van ons Bureau, haar partners en de diverse verenigingen waar wij het secretariaat voor verzorgen."]),
    ("Sheila Boon", "Secretaresse", "sheila", "sboon@dfobv.nl", ["Sheila is bij Bureau DFO werkzaam als allround secretaresse op de afdeling managementsupport."]),
    ("Tanja Heerze", "Administratief medewerker", "tanja", "theerze@dfobv.nl", ["Tanja verzorgt de facturatie van de producten die bij ons worden besteld en is verantwoordelijk voor het debiteurenbeheer. Tevens ondersteunt ze het secretariaat op het gebied van facturatie en doet ze hand-en-spandiensten binnen de administratie."]),
    ("Tiny Floris", "Gastvrouw", "tiny", "gastvrouw@dfobv.nl", ["Tiny is voor veel cursisten het gezicht van Bureau DFO. Als gastvrouw verzorgt zij de catering voor ruim 3.000 deelnemers die per jaar de opleidingszalen van ons pand betreden."]),
    ("Tjeerd Erkens", "Onderzoeker", "tjeerd", "terkens@dfobv.nl", ["Tjeerd is bij Bureau DFO verantwoordelijk voor alle marktonderzoeken zoals bijvoorbeeld het jaarlijkse Serviceprovider onderzoek. Voor DFO werkte hij als marktonderzoeker bij DTG (en haar voorloper Telefoongids en Gouden Gids) en bij een aantal bedrijven in de farmaceutische industrie."]),
    ("Trineke Kuijer", "Secretaresse", "trineke", "tkuijer@dfobv.nl", ["Trineke is al enige jaren in dienst van Bureau DFO. Haar werkzaamheden zijn dan ook heel erg divers; van het afhandelen van de binnenkomende telefoontjes, ondersteunende werkzaamheden binnen de verschillende afdelingen, het verzenden van de verschillende bestellingen via onze webshop tot het ontvangen van bezoekers."]),
    ("Willie van Puurveen – van den Berg", "Gastvrouw", "willie", "gastvrouw@dfobv.nl", ["Willie heet je welkom als gastvrouw bij Bureau DFO en doet er alles aan om jouw deelname aan onze bijeenkomsten prettig te laten verlopen."]),
]


def build_over():
    team = "".join(f'''<div class="person"><div class="ph"><img src="assets/img/team/{img}.jpg" alt="{E(n)}" loading="lazy" width="240" height="240"></div>
<div class="body"><h3>{E(n)}</h3><div class="role">Functie: {E(r)}</div>{"".join(f"<p>{E(x)}</p>" for x in t)}{f'<a href="mailto:{m}">{m}</a><br>' if m else ''}{'<a href="tel:+31332580460">033 258 0460</a>' if m else ''}</div></div>''' for n, r, img, m, t in TEAM)
    bs = sections_of("over-dfo/bureau-dfo/index.html")
    ws = sections_of("over-dfo/werken-bij/index.html")
    wk = list(ws.values())[0]
    w_txt = render_units([b for b in wk if b[0] == "p"])
    vac = [(v, wk[i + 1][1]) for i, (k, v) in enumerate(wk) if k == "h3" and i + 1 < len(wk) and wk[i + 1][0] == "btn" and v.startswith("Secretaresse")]
    vac_html = "".join(f'<a class="card" href="{E(u[1])}"><span class="tag">Vacature</span><h3>{E(t)}</h3><span class="more arrow">{E(u[0])} </span></a>' for t, u in vac)
    body = hero("Over Bureau DFO", "Jouw partner waar het gaat om succesvol ondernemen in de financiële dienstverlening",
                crumbs=["Over DFO"], img="assets/img/pand.jpg", small=False)
    body += f"""
<section><div class="wrap split" style="align-items:start">
  <div class="prose"><h2>Maak kennis met Bureau DFO</h2>{render_units(bs["Maak kennis met Bureau DFO"])}</div>
  <div class="media"><img src="assets/img/de-wel.jpg" alt="Het pand van Bureau DFO aan De Wel in Hoevelaken" loading="lazy" width="960" height="578"></div>
</div></section>
<section class="alt"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Alles onder één dak</span><h2>Bureau DFO ontzorgt op meerdere fronten</h2>
  <p>Van kennisontwikkeling tot uitvoering: Bureau DFO biedt financiële dienstverleners en hun brancheorganisaties een breed pakket aan diensten, allemaal onder één dak in Hoevelaken.</p></div>
  <div class="grid g3">
    {svc_card("opleidingen.html","cap","Opleidingen","— praktijkgerichte kennis voor financieel adviseurs")}
    {svc_card("secretariaten.html","users","Secretariaten","— ledenadministratie en bestuursondersteuning uit handen genomen")}
    {svc_card("zalencentrum.html","room","Zalen","— vergader- en cursusruimtes inclusief ontvangst")}
    {svc_card("studio.html","mic","Studio","— webinar-, podcast- en videoproducties")}
    {svc_card("compliance.html","shield","Compliance","— grip op wet- en regelgeving, van Wft tot AVG")}
    {svc_card("onderzoek.html","chart","Onderzoek","— onafhankelijk onderzoek voor de financiële adviesketen")}
  </div>
</div></section>
<section><div class="wrap"><div class="sec-head"><h2>Voor wie?</h2></div>{render_units(bs["Voor wie?"])}</div></section>
<section class="alt" id="team"><div class="wrap">
  <div class="sec-head"><h2>Ons team</h2></div>
  <div class="team">{team}</div>
</div></section>
<section id="werken-bij"><div class="wrap split" style="align-items:start">
  <div class="prose"><h2>Werken bij Bureau DFO</h2>{w_txt}</div>
  <div class="grid" style="gap:14px">{vac_html}<div class="card"><h3>Je kunt hier kennismaken met het team DFO</h3><a class="more arrow" href="#team">Ons team </a></div></div>
</div></section>
<section class="alt"><div class="wrap"><div class="sec-head"><h2>Benieuwd wat wij voor u kunnen betekenen?</h2><p>Neem contact met ons op of vul het contactformulier in zodat wij contact met u opnemen.</p></div>
  <div class="grid g3">
    <a class="card" href="tel:+31332580460"><div class="icon">{icon('users')}</div><h3>Telefonisch</h3><p>Neem telefonisch contact op via 033 258 04 60, wij denken graag met u mee.</p></a>
    <a class="card" href="mailto:info@dfobv.nl"><div class="icon">{icon('mail')}</div><h3>Via mail</h3><p>Stuur een mail naar info@dfobv.nl en wij reageren binnen één werkdag.</p></a>
    <a class="card" href="contact.html"><div class="icon">{icon('doc')}</div><h3>Contactformulier</h3><p>Stuur ons een bericht via het contactformulier.</p><span class="more arrow">Naar het formulier </span></a>
  </div></div></section>
"""
    page("over-dfo.html", "Over Bureau DFO – team en werken bij", "Bureau DFO is opgericht in 1992 en richt zich specifiek op de financiële dienstverlening. Maak kennis met ons team.", body)


def build_columns():
    toc = ""
    arts = ""
    for c in COLS:
        toc += f'<a class="card" href="#{c["slug"]}"><span class="tag">{E(c["maand"])}</span><h3>{E(c["titel"])}</h3><span class="more arrow">Lees de column </span></a>'
        out = ""
        inlist = False
        for kind, t in c["blocks"]:
            t = re.sub(r"\s+\.", ".", t)
            t = re.sub(r"\s*'Vaste contactpersonen dragen bij aan een sterke relatie' 1 VVP SPECIAL OKTOBER 2026\s*", " ", t)
            if t.startswith("Continuïteit in de relatie"):
                kind = "li"
            if kind != "li" and inlist:
                out += "</ul>"; inlist = False
            if kind == "li":
                if not inlist:
                    out += "<ul>"; inlist = True
                m = re.match(r"^(Continuïteit in de relatie|Deskundigheid|Bereikbaarheid|Meedenken over het ondernemerschap)\.?\s*(.*)", t)
                out += f"<li><strong>{E(m.group(1))}</strong>{'.' if m and not t.startswith('Bereikbaarheid') else ''} {E(m.group(2))}</li>" if m else f"<li>{E(t)}</li>"
            elif kind == "h" and t.startswith('"'):
                out += f"<blockquote>{E(t.strip(chr(34)))}</blockquote>"
            elif kind == "h":
                out += f"<h3>{E(t.capitalize() if t.isupper() else t)}</h3>"
            elif t.startswith("[1] http"):
                u = t[4:].strip()
                out += f'<p style="font-size:.85rem">[1] <a href="{E(u)}" rel="noopener">Uitspraak CG-Kifid 2025-0108</a></p>'
            else:
                out += f"<p>{E(t).replace(' [1] ', '<sup>[1]</sup> ').replace(' [1]', '<sup>[1]</sup>')}</p>"
        if inlist:
            out += "</ul>"
        arts += f'''<section id="{c["slug"]}" class="{'alt' if COLS.index(c) % 2 else ''}"><div class="wrap"><article class="article">
<span class="kicker" style="color:var(--blue)">Column · {E(c["maand"])}</span><h2>{E(c["titel"])}</h2>
<div class="byline"><img src="assets/img/team/jurjen.jpg" alt=""><div><strong>Jurjen Oosterbaan Martinius</strong><small>Algemeen directeur Bureau DFO</small></div></div>
{out}</article></div></section>'''
    body = hero("Columns van Jurjen Oosterbaan Martinius", "Scherpe observaties over het vak van financieel adviseur, de rol van aanbieders en de normen in onze sector.",
                crumbs=["Columns"])
    body += f'<section class="tight"><div class="wrap grid g3">{toc}</div></section>{arts}'
    body += callout("Lees ook de andere blogs van Jurjen", "Alle columns en opiniestukken vind je op de opiniepagina van Bureau DFO.", "https://www.dfobv.nl/opinie/", "Lees alle andere columns")
    page("columns.html", "Columns Jurjen Oosterbaan Martinius – Bureau DFO", "Columns van Jurjen Oosterbaan Martinius, algemeen directeur van Bureau DFO, over de financiële adviesbranche.", body)


def build_onderzoek():
    body = hero("Onderzoek", "Onafhankelijk onderzoek voor de financiële adviesketen. Wij meten met regelmaat hoe het intermediair de samenwerking met aanbieders en serviceproviders ervaart.",
                crumbs=["Onderzoek"])
    body += f"""
<section><div class="wrap news">
  <a class="card img" href="assets/pdf/persbericht-bureau-dfo-meedenken-met-kantoor-bepaalt-waardering-serviceproviders.pdf"><div class="ph"><img src="assets/img/persbericht.jpg" alt="" loading="lazy"></div><div class="body"><span class="tag">2026 II</span><h3>Onderzoek serviceproviders</h3><p>De marktgerichtheid van serviceproviders blijft achter bij wat adviseurs belangrijk vinden. Meedenken met het kantoor is bepalend voor waardering én aanbeveling.</p><span class="more arrow">Persbericht (pdf) </span></div></a>
  <a class="card img" href="https://www.dfobv.nl/wp-content/uploads/2026/10/Samenvatting-Performance-onderzoek-Kwaliteit-binnendienst-en-acceptatie-2026.pdf" rel="noopener"><div class="ph"><img src="assets/img/performance.jpg" alt="" loading="lazy"></div><div class="body"><span class="tag">2026 II</span><h3>Performanceonderzoek aanbieders</h3><p>Kwaliteit van binnendienst en acceptatie, gemeten over twee jaar op zes onderdelen van de samenwerking.</p><span class="more arrow">Samenvatting (pdf) </span></div></a>
  <a class="card img" href="https://www.dfobv.nl/product/onderzoeksrapport-waardering-assurantieportefeuilles-2026/" rel="noopener"><div class="ph"><img src="assets/img/bedrijfsvoering.jpg" alt="" loading="lazy"></div><div class="body"><span class="tag">Sinds 2004</span><h3>Waardering assurantieportefeuilles</h3><p>Hoe bepalen advieskantoren de waarde van hun assurantieportefeuille? Met trenddata over vijftien jaar.</p><span class="more arrow">Bekijk het rapport </span></div></a>
</div></section>
<section class="alt"><div class="wrap split">
  <div><h2>Serviceproviders vergelijken</h2><p>Vergelijk alle serviceproviders op kwaliteit, snelheid, aanbod en waardering in onze online vergelijker.</p><a class="btn btn-primary arrow" href="https://sp.dfobv.nl/" rel="noopener">Naar de vergelijker</a></div>
  <div><h2>Klanttevredenheidsonderzoek</h2><p>Wil je weten hoe jouw klanten je dienstverlening waarderen? Wij voeren in jouw opdracht een onafhankelijk onderzoek uit. Met een servicepakket krijg je korting of is het inbegrepen.</p><a class="btn btn-ghost arrow" href="abonnementen.html">Bekijk servicepakketten</a></div>
</div></section>
""" + callout("Onderzoek in opdracht?", "Tjeerd Erkens vertelt je graag meer over de mogelijkheden.", mailto("terkens@dfobv.nl", "Onderzoek in opdracht"), "Mail Tjeerd")
    page("onderzoek.html", "Onderzoek – Bureau DFO", "Onafhankelijk onderzoek van Bureau DFO: serviceproviders, performance van aanbieders en waardering van assurantieportefeuilles.", body)


def build_contact():
    body = hero("Contact", "Heb je een vraag? Bel, mail of stuur een bericht. We reageren binnen één werkdag.", crumbs=["Contact"])
    body += f"""
<section><div class="wrap split" style="align-items:start">
  <div>
    <div class="grid g2" style="margin-bottom:28px">
      <a class="card" href="{TEL_HREF}"><div class="icon">{icon('users')}</div><h3>Telefonisch</h3><p>{TEL}</p></a>
      <a class="card" href="mailto:{MAIL}"><div class="icon">{icon('mail')}</div><h3>E-mail</h3><p>{MAIL}</p></a>
      <a class="card" href="mailto:opleidingen@dfobv.nl"><div class="icon">{icon('cap')}</div><h3>Opleidingen</h3><p>opleidingen@dfobv.nl</p></a>
      <a class="card" href="mailto:info@dfozalen.nl"><div class="icon">{icon('room')}</div><h3>Zalencentrum</h3><p>info@dfozalen.nl</p></a>
    </div>
    <h2>Bezoekadres</h2>
    <p>Bureau DFO<br>{ADRES}</p>
    <ul class="check"><li>Vlak bij knooppunt Hoevelaken (A1/A28)</li><li>Gratis parkeren voor de deur, met laadpalen</li><li>Station Hoevelaken op 10 minuten lopen</li></ul>
    <p><a class="btn btn-ghost arrow" href="https://www.google.com/maps/search/?api=1&query=De+Wel+14+Hoevelaken" rel="noopener">Route plannen</a></p>
    <img src="assets/img/kaart.jpg" alt="Kaart van de omgeving" loading="lazy" width="960" height="442" style="border-radius:14px;margin-top:16px">
  </div>
  <div class="card">
    <h2 style="font-size:1.5rem">Contact met DFO BV</h2>
    <p class="muted">Heeft u vragen laat het ons weten. (Je e-mailprogramma opent met je bericht al ingevuld.)</p>
    <form class="f" id="cForm">
      <label>Onderwerp<select name="ond">
        <option value="{MAIL}">Algemene vraag</option><option value="opleidingen@dfobv.nl">Opleidingen</option>
        <option value="rjvanloon@dfocompliance.nl">Compliance / AFM-vergunning</option><option value="avanekeren@dfobv.nl">Abonnementen &amp; servicepakketten</option>
        <option value="info@dfozalen.nl">Zaalhuur</option><option value="{MAIL}">Studio &amp; producties</option></select></label>
      <div class="two"><label>Naam<input name="naam" required autocomplete="name"></label><label>Kantoor / organisatie<input name="org" autocomplete="organization"></label></div>
      <div class="two"><label>E-mail<input name="email" type="email" required autocomplete="email"></label><label>Telefoon<input name="tel" type="tel" autocomplete="tel"></label></div>
      <label>Bericht<textarea name="msg" required></textarea></label>
      <button class="btn btn-primary" type="submit">Bericht opstellen</button>
    </form>
  </div>
</div></section>
"""
    js = """<script>
document.getElementById('cForm').addEventListener('submit',e=>{e.preventDefault();const f=new FormData(e.target);const s=e.target.ond;
const b=`${f.get('msg')}\\n\\n--\\n${f.get('naam')}\\n${f.get('org')}\\n${f.get('email')}\\n${f.get('tel')}`;
location.href='mailto:'+s.value+'?subject='+encodeURIComponent('Contact via website – '+s.options[s.selectedIndex].text)+'&body='+encodeURIComponent(b);});
</script>"""
    page("contact.html", "Contact – Bureau DFO", "Contact met Bureau DFO in Hoevelaken: 033 258 04 60, info@dfobv.nl. Route en bezoekadres.", body, scripts=js)


def build_404():
    body = hero("Pagina niet gevonden", "Deze pagina bestaat niet (meer). Kijk in het menu of ga terug naar de homepage.",
                btns='<a class="btn btn-light arrow" href="index.html">Naar home</a>')
    page("404.html", "Pagina niet gevonden – Bureau DFO", "Pagina niet gevonden.", body,
         extra_head='<base href="/DFO/">')


STUDIO = [
    ("studio/webinar-producties/index.html", "studio-webinar.html", "studio"),
    ("studio/podcastproducties/index.html", "studio-podcast.html", "podcast"),
    ("studio/videoproductie/index.html", "studio-video.html", "video"),
    ("studio/studio-verhuur-met-technische-ondersteuning-professionele-producties-zorgeloos-geregeld/index.html", "studio-verhuur.html", "studio2"),
    ("studio/contentmarketing-social-media-productie/index.html", "studio-contentmarketing.html", "content"),
    ("studio/training-en-e-learning-modules-doelgericht-leren/index.html", "studio-elearning.html", "elearning"),
]


def build_compliance():
    t, lead, body = render_verbatim("diensten/compliance/index.html", ["Compliance"], hero_img="assets/img/robert-jan.jpg")
    body = body.replace('<h1>Jij kunt je richten op je kernactiviteiten</h1>',
                        '<span class="kicker">DFO Compliance</span><h1>Jij kunt je richten op je kernactiviteiten</h1>')
    page("compliance.html", "Compliance: AFM-vergunning en Wft-audit – Bureau DFO",
         "DFO Compliance: ondersteuning bij AFM-vergunning, geborgde bedrijfsvoering, Wwft, AVG, Sanctiewet, MiFID en Wft-audit.", body)


def build_studio():
    bl = vblocks("studio/index.html")
    sub = next(v for k, v in bl if k == "h3")
    bl = [b for b in bl if b != ("h3", sub) and b[0] not in ("h1",)]
    last = bl.pop() if bl[-1][0] == "btn" else None
    body = hero("DFO Studio", sub, crumbs=["Studio"], img="assets/img/studio2.jpg", small=False)
    body += f'<section><div class="wrap">{render_units(bl)}'
    if last:
        body += f'<div class="btns" style="justify-content:center;margin-top:28px">{btn_html(*last[1])}</div>'
    body += '</div></section>'
    page("studio.html", "DFO Studio – webinar-, podcast- en videoproducties",
         "DFO Studio: de webcam- en webinarstudio voor de financiële dienstverlening.", body)
    for rel, fname, img in STUDIO:
        t, lead, body = render_verbatim(rel, ['<a href="studio.html">Studio</a>', "{t}"], hero_img=f"assets/img/{img}.jpg")
        page(fname, f"{t} – DFO Studio", lead[:155], body)


def build_congressen():
    t, lead, body = render_verbatim("congressen/index.html", ["Congressen"], hero_img="assets/img/congres.jpg")
    body = body.replace('<section><div class="wrap"><div class="prose">',
                        '<section><div class="wrap"><div class="prose"><img src="assets/img/vip.jpg" alt="VIPcongres 2024" loading="lazy" style="border-radius:14px;margin-bottom:24px">', 1)
    page("congressen.html", "Congressen – Bureau DFO", "Congresorganisatie door Bureau DFO voor de financiële sector, o.a. VIPcongres, NVHP en KPS.", body)


def build_themas():
    bl = vblocks("themas/index.html")
    body = hero("Thema’s", "Jouw partner voor een beheerste en integere bedrijfsvoering", crumbs=["Thema’s"])
    body += f'<section><div class="wrap">{render_units(bl)}</div></section>'
    page("themas.html", "Thema’s – Bureau DFO", "Hypotheken & Kredieten, Inkomen, Leven & Pensioen, Schade, Bedrijfsvoering en Personeel: thema’s van Bureau DFO.", body)


def build_secretariaten():
    ver = [("NVHP – Nederlandse Vereniging van Hypothecair Planners", "https://www.hypothecairplanner.nl/"),
           ("PIA Pensioen", "http://piapensioen.nl"), ("VEZIS", "http://www.vezis.nl/"),
           ("KPS – Kring van Pensioenspecialisten", "http://www.kps.nl"),
           ("Stichting Contactgroep Automatisering", "http://contactgroepautomatisering.nl")]
    vl = "".join(f'<a class="card" href="{u}" rel="noopener"><h3>{E(n)}</h3><span class="more arrow">Bezoek website </span></a>' for n, u in ver)
    body = hero("Secretariaten", "Bureau DFO beheert het secretariaat van diverse verenigingen.", crumbs=["Secretariaten"])
    body += f"""
<section><div class="wrap split" style="align-items:start"><div class="prose">
<p>Nederland kent tienduizenden (belangen) verenigingen die zich inzetten voor een bepaalde doelgroep of doelstelling. Vaak draait een dergelijke instelling op de inbreng van vrijwilligers. Echter, in de huidige samenleving wordt het steeds moeilijker om vrijwilligers bereid te vinden om veel tijd te besteden aan de vereniging. Terwijl de noodzakelijke werkzaamheden wel doorgaan. Denkt u aan zaken als:</p>
<ul class="check"><li>Beheer telefoon en mailverkeer</li><li>Ledenadministratie en boekhouding</li><li>Website onderhoud</li><li>Administratie en postverwerking</li><li>Infrastructuur en 24-uurs bereik.</li></ul>
<p>Bureau DFO beheert het secretariaat van diverse verenigingen. Hiervoor is een team van dames beschikbaar dat fulltime beschikbaar is vanuit een reeds bestaande infrastructuur.</p>
<p>Het is mogelijk om een eigen servicepakket samen te stellen voor uw vereniging met de werkzaamheden waar u behoefte aan heeft, tegen beperkte kosten. Neemt u hierover gerust contact op met Agaat van Ekeren – Relatiemanager van Bureau DFO – middels <a href="mailto:avanekeren@dfobv.nl">avanekeren@dfobv.nl</a></p>
</div><div class="media"><img src="assets/img/boardroom.jpg" alt="Boardroom bij Bureau DFO" loading="lazy" width="960" height="478"></div></div></section>
<section class="alt"><div class="wrap"><div class="sec-head"><h2>Op dit moment voert Bureau DFO voor de volgende verenigingen het secretariaat:</h2></div>
<div class="grid g3">{vl}</div></div></section>
""" + callout("Heeft u interesse?", "Laat het ons weten via het contactformulier of mail Agaat van Ekeren.",
              mailto("avanekeren@dfobv.nl", "Interesse secretariaatsvoering"), "Neem contact op")
    page("secretariaten.html", "Secretariaten – Bureau DFO", "Bureau DFO beheert het secretariaat van diverse verenigingen in de financiële sector.", body)


def build_calculator():
    t, lead, body = render_verbatim("abonnement-dashboard/toelichting-calculator-onderhoud-en-nazorg/index.html",
                                    ["Calculator"], cta_last=False)
    body = body.replace('<a class="btn btn-primary arrow" href="https://www2.dfobv.nl/abonnement-dashboard/" rel="noopener">',
                        '<a class="btn btn-primary arrow" href="https://www2.dfobv.nl/abonnement-dashboard/" target="_blank" rel="noopener">')
    body = body.replace('</h1>', '</h1>', 1)
    body = body.replace('<section><div class="wrap"><div class="prose">',
                        '<section><div class="wrap"><div class="prose"><img src="assets/img/calculator.jpg" alt="Schermafbeelding calculator" loading="lazy" style="border-radius:14px;margin-bottom:24px;max-width:520px">', 1)
    page("nazorg-calculator.html", "Calculator onderhoud en nazorg – Bureau DFO",
         "Tool voor gratis indicatie kosten / opbrengsten serviceabonnementen voor onderhoud en nazorg.", body)


def build_zoeken():
    from bs4 import BeautifulSoup
    idx = []
    for f in sorted(ROOT.glob("*.html")):
        if f.name in ("404.html", "zoeken.html"):
            continue
        s = BeautifulSoup(f.read_text(), "html.parser")
        main = s.find("main")
        for t in main(["script", "style"]):
            t.decompose()
        title = s.title.string.split(" – ")[0]
        # per sectie een item, zodat resultaten naar de juiste plek springen
        for sec in main.find_all("section"):
            h = sec.find(["h1", "h2"])
            txt = re.sub(r"\s+", " ", sec.get_text(" ", strip=True))
            if len(txt) < 40:
                continue
            anchor = ("#" + sec["id"]) if sec.get("id") else ""
            idx.append({"u": f.name + anchor, "p": title, "h": h.get_text(" ", strip=True) if h else title, "x": txt[:1500]})
    for c in cursussen:
        idx.append({"u": c["u"], "p": "Opleiding", "h": c["t"], "x": c["s"] + " " + c["wg"] + " " + c["prijs"]})
    for d in DOCS:
        for g in d["groups"]:
            for it in g["items"]:
                idx.append({"u": it["u"], "p": "Document · " + d["title"], "h": it["t"], "x": g["name"]})
    seen, uniq = set(), []
    for it in idx:
        k = (it["u"], it["h"])
        if k not in seen:
            seen.add(k); uniq.append(it)
    body = hero("Zoeken", "Hier kunt u zoeken naar alles op de DFO website", crumbs=["Zoeken"])
    body += """<section><div class="wrap" style="max-width:880px">
<div class="filters"><input type="search" id="zq" placeholder="Zoek op pagina’s, opleidingen en documenten…" aria-label="Zoeken" autofocus></div>
<div class="count" id="zc"></div><div class="list" id="zr"></div></div></section>"""
    js = """<script>
const I=__IDX__;const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const q=document.getElementById('zq');
function snip(x,w){const i=x.toLowerCase().indexOf(w);if(i<0)return x.slice(0,160)+'…';const s=Math.max(0,i-70);return (s?'…':'')+x.slice(s,s+180)+'…';}
function go(){const t=q.value.trim().toLowerCase().split(/\\s+/).filter(w=>w.length>1);
 if(!t.length){document.getElementById('zr').innerHTML='';document.getElementById('zc').textContent='';return;}
 const r=I.map(it=>{const h=it.h.toLowerCase(),x=it.x.toLowerCase();let sc=0;for(const w of t){if(h.includes(w))sc+=5;else if(x.includes(w))sc+=1;else return null;}return [sc,it];}).filter(Boolean).sort((a,b)=>b[0]-a[0]).slice(0,60);
 document.getElementById('zc').textContent=r.length+(r.length===60?'+':'')+' resultaten';
 document.getElementById('zr').innerHTML=r.length?r.map(([s,it])=>`<a class="row" style="grid-template-columns:1fr" href="${esc(it.u)}"${it.u.startsWith('http')?' rel="noopener"':''}><div><div class="m" style="display:block">${esc(it.p)}</div><div class="t">${esc(it.h)}</div><div class="s">${esc(snip(it.x,t[0]))}</div></div></a>`).join(''):'<div class="empty">Niets gevonden.</div>';
 history.replaceState(null,'','?q='+encodeURIComponent(q.value));}
q.addEventListener('input',go);const p=new URLSearchParams(location.search).get('q');if(p){q.value=p;}go();
</script>""".replace("__IDX__", json.dumps(uniq, ensure_ascii=False))
    page("zoeken.html", "Zoeken – Bureau DFO", "Zoek op de website van Bureau DFO.", body, scripts=js)


if __name__ == "__main__":
    for fn in [build_home, build_opleidingen, build_documenten, build_compliance, build_abonnementen, build_zalen,
               build_studio, build_over, build_columns, build_congressen, build_secretariaten, build_onderzoek,
               build_calculator, build_contact, build_themas, build_404, build_zoeken]:
        fn()
    print("OK –", len(cursussen), "cursussen,", len(agenda), "data")
