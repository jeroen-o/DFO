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
    ("kennisbank.html", "Kennisbank"),
    ("compliance.html", "Compliance"),
    ("abonnementen.html", "Abonnementen"),
    ("vergadercentrum.html", "Vergaderruimte"),
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
  <a href="webshop.html">Webshop</a>
  <a href="opleidingen.html#agenda">Agenda</a>
  <a href="https://kennisbank.dfobv.nl/" rel="noopener">Wft-kennisbank</a>
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
      <p>{ADRES}<br>Tel: <a href="{TEL_HREF}">{TEL}</a><br>Mail: <a href="mailto:{MAIL}">{MAIL}</a><br><a href="https://www.google.com/maps/place/Bureau+DFO+BV/@52.1669977,5.4650031,183m/data=!3m1!1e3!4m12!1m5!3m4!2zNTLCsDEwJzAwLjciTiA1wrAyNyc1Ni4yIkU!8m2!3d52.166857!4d5.465621!3m5!1s0x47c6461e8b92bf4b:0x111d772b352974aa!8m2!3d52.1668573!4d5.4656206!16s%2Fg%2F1tdzv" rel="noopener">Route via Google Maps</a></p>
      <h4 style="margin-top:22px">Op de hoogte blijven?</h4>
      <p class="fnews">Schrijf je dan in voor onze nieuwsbrief</p>
      <a class="btn btn-light" href="abonnementen.html#aanvragen" style="padding:9px 16px">Aanmelden</a>
    </div>
    <div><h4>Aanbod</h4><ul>
      <li><a href="opleidingen.html">Opleidingen &amp; agenda</a></li>
      <li><a href="opleidingen.html#nvhp">NVHP-masterclasses</a></li>
      <li><a href="documenten.html">Modeldocumenten &amp; contracten</a></li>
      <li><a href="compliance.html">DFO Compliance</a></li>
      <li><a href="abonnementen.html">Abonnementen &amp; servicepakketten</a></li>
      <li><a href="onderzoek.html">Onderzoek</a></li>
      <li><a href="nazorg-calculator.html">Calculator nazorgabonnement</a></li>
    </ul></div>
    <div><h4>Faciliteiten</h4><ul>
      <li><a href="vergadercentrum.html">DFO Vergadercentrum</a></li>
      <li><a href="studio.html">DFO Studio</a></li>
      <li><a href="congressen.html">Congressen</a></li>
      <li><a href="secretariaten.html">Secretariaatsvoering</a></li>
      <li><a href="columns.html">Columns Jurjen Oosterbaan</a></li>
      <li><a href="signalen.html">DFO Signalen</a></li>
      <li><a href="serviceproviders.html">Serviceproviders vergelijken</a></li>
      <li><a href="nazorg.html">Nazorg &amp; Onderhoud Portal</a></li>
      <li><a href="de-mening-van.html">De mening van</a></li>
      <li><a href="performance.html">Performance-onderzoek</a></li>
      <li><a href="kennisbank.html">Kennisbank begrippen</a></li>
      <li><a href="themas.html">Thema’s</a></li>
      <li><a href="https://www.youtube.com/@bureaudfo6854/videos" rel="noopener">Webinars op YouTube</a></li>
      <li><a href="https://www.youtube.com/@VIPcongres/videos" rel="noopener">Videoproducties op YouTube</a></li>
      <li><a href="zoeken.html">Zoeken</a></li>
    </ul></div>
    <div><h4>Webshop &amp; portalen</h4><ul>
      <li><a href="webshop.html">Webshop (alle producten)</a></li>
      <li><a href="artikelen.html">Artikelen &amp; opinie</a></li>
      <li><a href="agenda-archief.html">Agenda-archief</a></li>
      <li><a href="{SHOP}/agenda/" rel="noopener">Agenda opleidingen</a></li>
      <li><a href="product-bureau-dfo-kennisflits.html">DFO Kennisflits</a></li>
      <li><a href="product-bureau-dfo-servicepakket.html">DFO – Servicepakket</a></li>
      <li><a href="webshop.html#hypotheken">Hypotheken</a></li>
      <li><a href="webshop.html#bedrijfsvoering">Bedrijfsvoering</a></li>
      <li><a href="webshop.html#inkomen">Inkomen</a></li>
      <li><a href="webshop.html#levenpensioen">Leven &amp; Pensioen</a></li>
      <li><a href="webshop.html#personeel">Personeel / HR</a></li>
      <li><a href="webshop.html#schade">Schade</a></li>
      <li><a href="webshop.html#alle-opleidingen">Alle opleidingen</a></li>
      <li><a href="https://kennisbank.dfobv.nl/" rel="noopener">Wft-kennisbank</a></li>
      <li><a href="{SHOP}/mijn-account/" rel="noopener">Mijn account</a></li>
    </ul></div>
    <div><h4>Bureau DFO</h4><ul>
      <li><a href="over-dfo.html">Over ons</a></li>
      <li><a href="over-dfo.html#team">Ons team</a></li>
      <li><a href="over-dfo.html#werken-bij">Werken bij</a></li>
      <li><a href="contact.html">Contact &amp; route</a></li>
      <li><a href="info-algemene-leveringsvoorwaarden.html">Algemene leveringsvoorwaarden</a></li>
      <li><a href="info-klachtenprocedure.html">Klachtenprocedure</a></li>
      <li><a href="info-onafhankelijkheidsverklaring.html">Onafhankelijkheidsverklaring</a></li>
      <li><a href="info-privacyverklaring-en-cookies.html">Privacyverklaring</a></li>
      <li><a href="info.html">Overige pagina’s dfobv.nl</a></li>
      <li><a href="actievoorwaarden-nieuwsbrief-wft.html">Actievoorwaarden Wft-nieuwsbrief</a></li>
    </ul></div>
  </div>
  <div class="fbottom"><span>© {year} Bureau DFO B.V.</span><span><a href="https://www.linkedin.com/company/bureaudfo" rel="noopener">LinkedIn</a> · <a href="https://twitter.com/BureauDFO" rel="noopener">Twitter / X</a> · <a href="https://www.dfosignalen.nl/" rel="noopener">DFO Signalen</a></span></div>
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
    "expertisegroepschade": "expertisegroep", "performance-ii-corporate-infographic-cover": "performance", "persbericht-serviceproviders-ii-1200x760": "persbericht", "de-wel-14-16": "de-wel", "1-superzaal": "superzaal",
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
    <div class="card img">
      <a class="ph" href="https://www.dfobv.nl/product/gratis-vakpaper-serviceproviders-onderzoek-2026/" rel="noopener"><img src="assets/img/persbericht.jpg" alt="Gratis vakpaper Serviceproviders-onderzoek 2026" loading="lazy" width="960" height="608"></a>
      <div class="body"><span class="tag">Onderzoek</span><h3>{E(t1)}</h3><p>{get(t1)}</p>
      <a class="more arrow" href="assets/pdf/persbericht-bureau-dfo-meedenken-met-kantoor-bepaalt-waardering-serviceproviders.pdf">Lees hier het persbericht </a>
      <a class="more arrow" href="https://www.dfobv.nl/product/gratis-vakpaper-serviceproviders-onderzoek-2026/" rel="noopener" style="margin-top:6px">Gratis vakpaper Serviceproviders-onderzoek 2026 </a></div></div>
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

{portals_section()}

<section><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Wat we doen</span><h2>Alles onder één dak</h2>
  <p>Van kennisontwikkeling tot uitvoering: Bureau DFO biedt financiële dienstverleners en hun brancheorganisaties een breed pakket aan diensten, allemaal onder één dak in Hoevelaken.</p></div>
  <div class="grid g3">
    {svc_card("opleidingen.html","cap","Opleidingen","— praktijkgerichte kennis voor financieel adviseurs")}
    {svc_card("secretariaten.html","users","Secretariaten","— ledenadministratie en bestuursondersteuning uit handen genomen")}
    {svc_card("vergadercentrum.html","room","Vergaderruimte","— vergader- en cursusruimtes inclusief ontvangst")}
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
                btns='<a class="btn btn-light arrow" href="#aanbod">Bekijk het aanbod</a><a class="btn btn-ghost" href="#agenda">Agenda</a><a class="btn btn-ghost" href="#nvhp">NVHP-masterclasses</a>')
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
  <p class="muted" style="font-size:.85rem;margin-top:12px">Beschikbaarheid en actuele data vind je altijd in het <a href="{PORTAL}/alle-cursus-evenementen/overzicht" rel="noopener">opleidingsportaal</a>. Bekijk ook <a href="{PORTAL}/cursussen/cursussen" rel="noopener">alle opleidingen in het portaal</a>.</p>
</div></section>

{__import__("related").nvhp_section()}

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
    import dfobv_site
    docicon = icon("doc")
    cats_html = ""
    for d in DOCS:
        n = sum(len(g["items"]) for g in d["groups"])
        groups = ""
        for g in d["groups"]:
            items = "".join(
                f'<li><a href="{E(dfobv_site.rewrite(i["u"]))}" data-t="{E(i["t"].lower())}">{docicon}<span>{E(i["t"])}</span></a></li>'
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
<a class="more arrow" href="{mailto('info@dfozalen.nl', f'Aanvraag {n.split(" (")[0]}', f'Ik wil graag zaal {n} reserveren.%0A%0ADatum:%0AAantal personen:%0AOpstelling:%0ACatering:%0A'.replace('%0A', chr(10)))}">Aanvragen </a></div></div>'''
    zs = sections_of("diensten/dfo-zalencentrum/index.html")
    intro = render_units([b for b in zs["Alle ruimte om samen te komen, te leren én te inspireren!"] if b[0] != "btn"]).replace("DFO Zalencentrum", "DFO Vergadercentrum")
    body = hero("DFO Vergadercentrum", "Van boardroom tot superzaal: in Hoevelaken vind je voor elke vergadering, training of bijeenkomst de ruimte die bij je past.",
                crumbs=["Vergadercentrum"], img="assets/img/superzaal.jpg", small=False,
                btns=f'<a class="btn btn-light arrow" href="{mailto("info@dfozalen.nl","Offerteaanvraag DFO Vergadercentrum")}">Offerte aanvragen</a><a class="btn btn-ghost" href="#zalen">Bekijk de zalen</a>')
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
              mailto("info@dfozalen.nl", "Offerteaanvraag DFO Vergadercentrum"), "Vraag een offerte aan") + f'<section class="tight" style="padding-top:0"><div class="wrap center"><a class="btn btn-ghost arrow" href="{mailto("info@dfozalen.nl", "Vraag over DFO Vergadercentrum")}">Of heb je vragen? Mail ons</a> <a class="btn btn-ghost arrow" href="https://www.google.com/maps/place/Bureau+DFO+BV/@52.1669977,5.4650031,183m/data=!3m1!1e3!4m12!1m5!3m4!2zNTLCsDEwJzAwLjciTiA1wrAyNyc1Ni4yIkU!8m2!3d52.166857!4d5.465621!3m5!1s0x47c6461e8b92bf4b:0x111d772b352974aa!8m2!3d52.1668573!4d5.4656206!16s%2Fg%2F1tdzv" rel="noopener">Route via Google Maps</a></div></section>'
    page("vergadercentrum.html", "Vergaderruimte huren in Hoevelaken – DFO Vergadercentrum",
         "Zeven vergader- en cursuszalen voor 8 tot 70 personen bij knooppunt Hoevelaken. Gratis parkeren, persoonlijke ontvangst.", body)


TEAM = [
    ("Agaat van Ekeren", "Relatiemanager", "agaat", "avanekeren@dfobv.nl", ["Agaat is verantwoordelijk voor de klanttevredenheid van al onze klanten en werkt samen met Jurjen Oosterbaan Martinius aan diversen projecten. Daarnaast is zij verantwoordelijk voor alle abonnementen die wij aanbieden. Denk hierbij aan het Wft Serviceabonnement en nieuwsbrieven die u bij ons kunt afnemen. Ben je benieuwd naar onze dienstverlening, of wat wij voor je kunnen betekenen, neem dan contact op met Agaat."]),
    ("Anja Heetmayer Knorth", "Administratief medewerker/gastvrouw", "anja", "aheetmayer@dfobv.nl", ["Anja heet je welkom als gastvrouw bij Bureau DFO en doet er alles aan om jouw deelname aan onze bijeenkomsten prettig te laten verlopen."]),
    ("Gijs", "Huisvriend", "gijs", "", ["Gijs is het vaste en zeer geliefde gezicht op kantoor. Met zijn vriendelijke en energieke karakter weet hij bij iedereen een glimlach op het gezicht te toveren. Hij krijgt volop aandacht van collega’s en draagt dagelijks bij aan een positieve en ontspannen werksfeer. Gijs is voor velen het hoogtepunt van de werkdag."]),
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
    {svc_card("vergadercentrum.html","room","Vergaderruimte","— vergader- en cursusruimtes inclusief ontvangst")}
    {svc_card("studio.html","mic","Studio","— webinar-, podcast- en videoproducties")}
    {svc_card("compliance.html","shield","Compliance","— grip op wet- en regelgeving, van Wft tot AVG")}
    {svc_card("onderzoek.html","chart","Onderzoek","— onafhankelijk onderzoek voor de financiële adviesketen")}
  </div>
</div></section>
<section><div class="wrap"><div class="sec-head"><h2>Voor wie?</h2></div>{render_units(bs["Voor wie?"])}</div></section>
<section class="alt" id="team"><div class="wrap">
  <div class="sec-head"><h2>Ons team</h2><p>We stellen graag een aantal collega’s aan u voor. In totaal staan 17 medewerkers voor u klaar om u te helpen bij het succesvol invullen van uw ondernemerschap. Neem contact met ons op om te bespreken hoe we u van dienst kunnen zijn.</p></div>
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
    body += f'<section class="tight"><div class="wrap"><a class="card" href="de-mening-van.html" style="max-width:520px"><span class="tag">Ook lezen</span><h3>De mening van…</h3><p>Professionals uit de sector over actuele ontwikkelingen: Jan Hamburger, Janthony Wielink en Paul Schuiling.</p><span class="more arrow">Lees de bijdragen </span></a></div></section>'
    body += callout("Lees ook de andere blogs van Jurjen", "Alle columns en opiniestukken vind je op de opiniepagina van Bureau DFO.", "https://www.dfobv.nl/opinie/", "Lees alle andere columns")
    page("columns.html", "Columns Jurjen Oosterbaan Martinius – Bureau DFO", "Columns van Jurjen Oosterbaan Martinius, algemeen directeur van Bureau DFO, over de financiële adviesbranche.", body)


def build_onderzoek():
    body = hero("Onderzoek", "Onafhankelijk onderzoek voor de financiële adviesketen. Wij meten met regelmaat hoe het intermediair de samenwerking met aanbieders en serviceproviders ervaart.",
                crumbs=["Onderzoek"])
    body += f"""
<section><div class="wrap grid g4">
  <a class="card img" href="assets/pdf/persbericht-bureau-dfo-meedenken-met-kantoor-bepaalt-waardering-serviceproviders.pdf"><div class="ph"><img src="assets/img/persbericht.jpg" alt="" loading="lazy"></div><div class="body"><span class="tag">2026 II</span><h3>Onderzoek serviceproviders</h3><p>De marktgerichtheid van serviceproviders blijft achter bij wat adviseurs belangrijk vinden. Meedenken met het kantoor is bepalend voor waardering én aanbeveling.</p><span class="more arrow">Persbericht (pdf) </span></div></a>
  <a class="card img" href="https://www.dfobv.nl/product/gratis-vakpaper-serviceproviders-onderzoek-2026/" rel="noopener"><div class="ph"><img src="assets/img/signalen.jpg" alt="" loading="lazy"></div><div class="body"><span class="tag">Gratis</span><h3>Vakpaper Serviceproviders-onderzoek 2026</h3><p>Download het gratis vakpaper bij het Serviceproviders-onderzoek 2026 in de DFO-webshop.</p><span class="more arrow">Naar het vakpaper </span></div></a>
  <a class="card img" href="https://www.dfobv.nl/wp-content/uploads/2026/10/Samenvatting-Performance-onderzoek-Kwaliteit-binnendienst-en-acceptatie-2026.pdf" rel="noopener"><div class="ph"><img src="assets/img/performance.jpg" alt="" loading="lazy"></div><div class="body"><span class="tag">2026 II</span><h3>Performanceonderzoek aanbieders</h3><p>Kwaliteit van binnendienst en acceptatie, gemeten over twee jaar op zes onderdelen van de samenwerking.</p><span class="more arrow">Samenvatting (pdf) </span></div></a>
  <a class="card img" href="https://www.dfobv.nl/product/onderzoeksrapport-waardering-assurantieportefeuilles-2026/" rel="noopener"><div class="ph"><img src="assets/img/bedrijfsvoering.jpg" alt="" loading="lazy"></div><div class="body"><span class="tag">Sinds 2004</span><h3>Waardering assurantieportefeuilles</h3><p>Hoe bepalen advieskantoren de waarde van hun assurantieportefeuille? Met trenddata over vijftien jaar.</p><span class="more arrow">Bekijk het rapport </span></div></a>
</div></section>
<section class="alt"><div class="wrap">
  <div class="sec-head"><h2>Performance-onderzoek</h2><p>Samenvattingen Meting I en II 2026, de winnaars van 2025, de Maand van de Performance en de Week van de Serviceprovider.</p></div>
  <div class="grid g4">
    <a class="card" href="performance.html#samenvattingen-2026"><span class="tag">2026</span><h3>Samenvattingen Meting I en II</h3><span class="more arrow">Downloaden </span></a>
    <a class="card" href="performance.html#winnaars-2025"><span class="tag">2025</span><h3>Winnaars Performance onderzoek</h3><span class="more arrow">Bekijken </span></a>
    <a class="card" href="performance.html#maand-van-de-performance"><span class="tag">2024</span><h3>Maand van de Performance</h3><span class="more arrow">Vakpapers </span></a>
    <a class="card" href="performance.html#week-van-de-serviceprovider"><span class="tag">2024</span><h3>Week van de Serviceprovider</h3><span class="more arrow">Winnaars &amp; video’s </span></a>
  </div>
</div></section>
<section><div class="wrap split">
  <div><h2>Serviceproviders vergelijken</h2><p>Vergelijk alle serviceproviders op kwaliteit, snelheid, aanbod en waardering in onze online vergelijker.</p><a class="btn btn-primary arrow" href="serviceproviders.html">Naar de vergelijker</a></div>
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
      <a class="card" href="mailto:info@dfozalen.nl"><div class="icon">{icon('room')}</div><h3>Vergadercentrum</h3><p>info@dfozalen.nl</p></a>
    </div>
    <h2>Bezoekadres</h2>
    <p>Bureau DFO<br>{ADRES}</p>
    <ul class="check"><li>Vlak bij knooppunt Hoevelaken (A1/A28)</li><li>Gratis parkeren voor de deur, met laadpalen</li><li>Station Hoevelaken op 10 minuten lopen</li></ul>
    <p><a class="btn btn-ghost arrow" href="https://www.google.com/maps/place/Bureau+DFO+BV/@52.1669977,5.4650031,183m/data=!3m1!1e3!4m12!1m5!3m4!2zNTLCsDEwJzAwLjciTiA1wrAyNyc1Ni4yIkU!8m2!3d52.166857!4d5.465621!3m5!1s0x47c6461e8b92bf4b:0x111d772b352974aa!8m2!3d52.1668573!4d5.4656206!16s%2Fg%2F1tdzv" rel="noopener">Route plannen</a></p>
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


def build_redirects():
    for old, new in [("zalencentrum.html", "vergadercentrum.html")]:
        (ROOT / old).write_text(f'''<!doctype html><html lang="nl"><head><meta charset="utf-8"><title>Doorverwijzing</title>
<link rel="canonical" href="{new}"><meta http-equiv="refresh" content="0; url={new}"><meta name="robots" content="noindex">
<script>location.replace("{new}"+location.hash)</script></head><body><p>Deze pagina is verhuisd naar <a href="{new}">{new}</a>.</p></body></html>
''')


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
        if f.name in ("404.html", "zoeken.html", "kennisbank.html"):
            continue
        s = BeautifulSoup(f.read_text(), "html.parser")
        main = s.find("main")
        if main is None:
            continue
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
            lim = 500 if f.name.startswith(("product-", "artikel-", "info-")) else 1500
            idx.append({"u": f.name + anchor, "p": title, "h": h.get_text(" ", strip=True) if h else title, "x": txt[:lim]})
    for c in cursussen:
        idx.append({"u": c["u"], "p": "Opleiding", "h": c["t"], "x": c["s"] + " " + c["wg"] + " " + c["prijs"]})
    import kennisbank
    for it in kennisbank.load():
        idx.append({"u": f"kennisbank.html#{it['id']}", "p": "Kennisbank · " + it["domnaam"], "h": it["term"] + (f" ({it['afk']})" if it.get("afk") else ""), "x": it["def"]})
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


EXTRA = Path(__file__).resolve().parent / "bron-www2-extra"


def xblocks(rel):
    bl = vblocks(rel, EXTRA)
    out = []
    for k, v in bl:
        if k in ("h2", "h3") and v.startswith("Lees ook de andere"):
            break
        if k == "h3" and v.startswith("Jouw partner waar het gaat"):
            continue
        out.append((k, v))
    return out


def ximg(src):
    base = re.sub(r"\.\d+x\d+(x\d+x\d+)?\.", ".", src.split("/")[-1]).rsplit(".", 1)[0]
    p = ROOT / "assets/img" / (base + ".jpg")
    return f"assets/img/{base}.jpg" if p.exists() else img_src(src)


def extra_columns():
    """De 3 columns die alleen via de sitemap bereikbaar waren, in hetzelfde formaat als columns.json."""
    res = []
    for slug, maand in [("januari-2025-2", "januari 2025"), ("januari-2025", "januari 2025"), ("december-2024", "december 2024")]:
        bl = xblocks(f"columns-jurjen-oosterbaan/column-jurjen-oosterbaan-{slug}/index.html")
        title, blocks_ = None, []
        for k, v in bl:
            t = html.unescape(re.sub(r"<[^>]+>", "", v)).strip() if isinstance(v, str) else ""
            if k == "h2" and title is None:
                title = t
                continue
            if k == "h2":
                blocks_.append(["h", t])
            elif k == "p" and t:
                blocks_.append(["p", t])
        res.append({"slug": slug, "maand": maand, "titel": title, "blocks": blocks_})
    return res


def build_performance():
    sam = xblocks("samenvattingen-onderzoek-performance-2026/index.html")
    win = xblocks("winnaars-performance-onderzoek-2025/index.html")
    maand = xblocks("maand-van-de-performance/index.html")
    week = xblocks("week-van-de-serviceproviders/index.html")
    intro26 = next(v for k, v in sam if k == "p").replace("<br>", "").strip()
    imgs26 = [ximg(v) for k, v in sam if k == "img" and "puzzle" not in v]
    dl26 = [v for k, v in sam if k == "btn"]
    labels = ["Meting I – Kwaliteit accountmanagement en buitendienst", "Meting II – Kwaliteit binnendienst en acceptatie"]
    cards26 = "".join(
        f'<a class="card img" href="{E(u)}" rel="noopener"><div class="ph" style="aspect-ratio:auto"><img src="{im}" alt="" loading="lazy"></div>'
        f'<div class="body"><h3>{lab}</h3><span class="more arrow">{E(t)} </span></div></a>'
        for im, (t, u), lab in zip(imgs26, dl26, labels))
    wp = [v for k, v in win if k == "p"]
    wdl = next(v for k, v in win if k == "btn")
    mdl = next(v for k, v in maand if k == "btn")
    cards, cur = [], None
    for k, v in maand:
        if k == "h2":
            cur = {"h": v, "img": None, "p": "", "btn": None}
            cards.append(cur)
        elif cur and k == "img":
            cur["img"] = ximg(v)
        elif cur and k == "p":
            cur["p"] = v
        elif cur and k == "btn":
            cur["btn"] = v
    mcards = "".join(
        f'<div class="card img"><div class="ph" style="aspect-ratio:auto"><img src="{c["img"]}" alt="" loading="lazy"></div>'
        f'<div class="body"><span class="tag">{E(c["h"])}</span><p>{c["p"]}</p>'
        f'<a class="more arrow" href="{E(c["btn"][1])}" rel="noopener">{E(c["btn"][0])} </a></div></div>' for c in cards)
    wk_intro = next(v for k, v in week if k == "p")
    il = [v for k, v in week if k == "imglink"]
    winners, prev = [], None
    for k, v in week:
        if k == "p" and v != wk_intro:
            prev = v
        elif k == "yt" and prev:
            winners.append((prev.replace("Hypotkeken", "Hypotheken"), v))
            prev = None
    wcards = "".join(f'<div class="card"><p style="color:var(--ink);font-weight:600">{p}</p>{yt_html([y])}</div>' for p, y in winners)
    body = hero("Performance-onderzoek",
                "Hoe waardeert het intermediair de dienstverlening van aanbieders en serviceproviders? Download de gratis samenvattingen en vakpapers.",
                crumbs=['<a href="onderzoek.html">Onderzoek</a>', "Performance"])
    rest = "".join(f"<p>{x}</p>" for x in wp[1:])
    body += f"""
<section id="samenvattingen-2026"><div class="wrap">
  <div class="sec-head"><h2>Performance Onderzoek 2026 Samenvattingen Meting I en II</h2><p>{intro26}</p></div>
  <div class="grid g2">{cards26}</div>
</div></section>
<section class="alt" id="winnaars-2025"><div class="wrap split">
  <div class="prose"><h2>Winnaars Performance onderzoek 2025</h2><p>{wp[0]}</p>
  <h3><a href="{E(wdl[1])}" rel="noopener">Download hier de gratis samenvatting van het Performance onderzoek 2025 voor financieel adviseurs</a></h3>
  {rest}
  <div class="btns"><a class="btn btn-primary arrow" href="{E(wdl[1])}" rel="noopener">Download de samenvatting 2025</a></div></div>
  <div class="media"><img src="assets/img/winnaars-performance-onderzoek2.jpg" alt="Winnaars Performance onderzoek 2025" loading="lazy"></div>
</div></section>
<section id="maand-van-de-performance"><div class="wrap">
  <div class="split" style="margin-bottom:28px"><div><h2>Oktober: Maand van de Performance</h2>
  <p><a href="{E(mdl[1])}" rel="noopener"><strong>Download hier de gratis samenvatting van het Performance onderzoek 2024 voor financieel adviseurs</strong></a></p></div>
  <div><a href="{E(mdl[1])}" rel="noopener"><img src="assets/img/dfo-maand-van-de-performance.jpg" alt="Maand van de Performance" loading="lazy" style="max-width:240px"></a></div></div>
  <div class="grid g3">{mcards}</div>
</div></section>
<section class="alt" id="week-van-de-serviceprovider"><div class="wrap">
  <div class="split" style="margin-bottom:28px"><div class="prose"><h2>Week van de Serviceprovider</h2><p>{wk_intro}</p>
  <div class="btns"><a class="btn btn-primary arrow" href="{E(il[1][1])}" rel="noopener">Vakpaper Serviceproviders 2024 (pdf)</a><a class="btn btn-ghost arrow" href="{E(il[0][1])}" rel="noopener">Gratis vakpaper in de webshop</a></div></div>
  <div><a href="{E(il[0][1])}" rel="noopener"><img src="assets/img/week-van-de-serviceproviderwitte-achtegrond.jpg" alt="Week van de Serviceprovider" loading="lazy"></a>
  <a href="{E(il[1][1])}" rel="noopener"><img src="assets/img/met-randtekstlijn2024-1.jpg" alt="Vakpaper Serviceproviders 2024" loading="lazy" style="max-width:200px;margin-top:16px"></a></div></div>
  <div class="grid g3">{wcards}</div>
</div></section>
"""
    page("performance.html", "Performance-onderzoek – Bureau DFO",
         "Samenvattingen en vakpapers van het DFO Performance-onderzoek en de Week van de Serviceprovider.", body)


def build_mening():
    ov = xblocks("www2-dfobv-nl/de-mening-van-columns/index.html")
    intro = [v for k, v in ov if k == "p"][:2]
    arts, toc = "", ""
    for i, (slug, img) in enumerate([("de-mening-van-jan-hamburger", "janweb-1"),
                                      ("de-mening-van-janthony-wielink", "janthonie-wielink"),
                                      ("de-mening-van-paul-schuiling", "paul-schuiling")]):
        bl = xblocks(f"de-mening-van-columns/{slug}/index.html")
        if slug.endswith("hamburger"):
            bl = bl[[j for j, b in enumerate(bl) if b == ("h2", "DE MENING VAN")][0]:]
        name_p = next(v for k, v in bl if k == "p")
        parts = name_p.split("<br>")
        name = re.sub(r"<[^>]+>", "", parts[0]).strip()
        role = html.unescape(re.sub(r"<[^>]+>", "", parts[1])).strip() if len(parts) > 1 else ""
        out = ""
        for k, v in bl:
            if v == name_p or (k == "h2" and v == "DE MENING VAN") or k in ("img", "imglink", "btn"):
                continue
            if k == "h2":
                out += f"<blockquote>{E(v.strip(chr(34)))}</blockquote>" if v.startswith('"') else f"<h3>{E(v)}</h3>"
            elif k == "p":
                out += f"<p>{v}</p>"
        aid = slug.replace("de-mening-van-", "")
        alt = ' class="alt"' if i % 2 == 0 else ""
        toc += (f'<a class="card" href="#{aid}"><span class="tag">De mening van</span><h3>{E(name)}</h3>'
                f'<p>{E(role)}</p><span class="more arrow">Lees meer </span></a>')
        arts += (f'<section id="{aid}"{alt}><div class="wrap"><article class="article">'
                 f'<span class="kicker" style="color:var(--blue)">De mening van</span><h2>{E(name)}</h2>'
                 f'<div class="byline"><img src="assets/img/{img}.jpg" alt="{E(name)}"><div><strong>{E(name)}</strong><small>{E(role)}</small></div></div>'
                 f'{out}</article></div></section>')
    clean_intro = [re.sub(r"</?em>", "", x) for x in intro]
    body = hero("De mening van", clean_intro[0], crumbs=["De mening van"], img="assets/img/dfo-de-mening-van.jpg", small=False)
    body += f'<section class="tight"><div class="wrap"><p class="muted">{clean_intro[1]}</p><div class="grid g3">{toc}</div></div></section>{arts}'
    body += callout("Lees alle andere ‘de mening van’", "Eerdere bijdragen vind je op de website van Bureau DFO.",
                    "https://www.dfobv.nl/?s=de+mening+van", "Lees alle andere ‘de mening van’")
    page("de-mening-van.html", "De mening van – Bureau DFO",
         "Professionals uit de financiële sector geven hun mening over actuele ontwikkelingen.", body)


def build_actievoorwaarden():
    bl = xblocks("actievoorwaarden-nieuwsbrief-wft/index.html")
    t = next(v for k, v in bl if k == "h1")
    items = next(v for k, v in bl if k == "ul")
    lis = "".join(f"<li>{x}</li>" for x in items)
    ps = "".join(f"<p>{v}</p>" for k, v in bl if k == "p")
    body = hero(E(t), "", crumbs=['<a href="abonnementen.html">Abonnementen</a>', "Actievoorwaarden"])
    body += (f'<section><div class="wrap"><div class="prose"><ul class="check">{lis}</ul>{ps}'
             '<div class="btns"><a class="btn btn-primary arrow" href="abonnementen.html">Naar onze abonnementen</a></div></div></div></section>')
    page("actievoorwaarden-nieuwsbrief-wft.html", "Actievoorwaarden DFO Nieuwsbrief Wft – Bureau DFO",
         "Actievoorwaarden aanbod DFO Nieuwsbrief Wft.", body)



SIG = json.loads((SRC / "signalen.json").read_text())
SIG_SP = json.loads((SRC / "signalen-speciaal.json").read_text())
SIG_AANMELD = "https://cdn.flxml.eu/f-1b07d67d3b31b795"
for e in SIG:
    m = re.search(r"week-(\d+)-(\d{4})", e["u"])
    e["jaar"] = m.group(2) if m else ""


def sig_row(e):
    return (f'<a class="date" href="{E(e["u"])}" rel="noopener"><div class="d"><b>{E(e["t"].split()[-1])}</b><span>wk {E(e["jaar"][2:])}</span></div>'
            f'<div><div class="t">{E(e["t"])} – {E(e["jaar"])}</div><div class="m">{E(e["d"])}</div></div><div class="p">Lezen →</div></a>')


def signalen_tile():
    rows = "".join(sig_row(e) for e in SIG[:3])
    return f"""<section class="alt" id="signalen"><div class="wrap"><div class="card" style="padding:0;overflow:hidden"><div class="split" style="gap:0;align-items:stretch">
  <div style="padding:34px">
    <span class="kicker" style="color:var(--blue)">Gratis wekelijkse nieuwsbrief</span>
    <h2>DFO Signalen</h2>
    <p>Jouw wekelijkse update met signalen uit de markt, speciaal voor onafhankelijk financieel adviseurs.</p>
    <div class="btns"><a class="btn btn-primary arrow" href="{SIG_AANMELD}" rel="noopener">Aanmelden nieuwsbrief</a><a class="btn btn-ghost" href="signalen.html">Alle edities &amp; speciale signalen</a></div>
  </div>
  <div style="background:var(--bg);padding:24px 24px 24px 0"><div class="list">{rows}</div></div>
</div></div></div></section>"""


def build_signalen():
    years = []
    for e in SIG:
        if not years or years[-1][0] != e["jaar"]:
            years.append((e["jaar"], []))
        years[-1][1].append(e)
    arch = "".join(f'<h3 style="margin-top:28px">{y}</h3><div class="list">{"".join(sig_row(e) for e in es)}</div>' for y, es in years)
    sp = "".join(f'<div class="card"><span class="tag">Speciale DFO Signalen</span><h3>{E(i["t"])}</h3>{"".join(f"<p>{E(p)}</p>" for p in i["p"])}</div>' for i in SIG_SP)
    body = hero("DFO Signalen", "Jouw wekelijkse update met signalen uit de markt, speciaal voor onafhankelijk financieel adviseurs.",
                crumbs=["DFO Signalen"], img="assets/img/signalen.jpg", small=False,
                btns=f'<a class="btn btn-light arrow" href="{SIG_AANMELD}" rel="noopener">Aanmelden nieuwsbrief</a><a class="btn btn-ghost" href="#archief">Alle edities</a>')
    body += f"""
<section><div class="wrap">
  <div class="sec-head"><h2>Speciale DFO Signalen</h2><p>Alsjeblieft! Cijfers en analyses uit het onderzoek van Bureau DFO naar de advies- en bemiddelingsmarkt.</p></div>
  <div class="grid g3" style="align-items:start">{sp}</div>
</div></section>
<section class="alt" id="archief"><div class="wrap" style="max-width:900px">
  <div class="sec-head"><h2>Alle edities</h2><p>{len(SIG)} edities van DFO Signalen. Klik op een week om de nieuwsbrief te lezen op dfosignalen.nl.</p></div>
  {arch}
</div></section>
""" + callout("Meld je gratis aan", "Ontvang DFO Signalen elke week in je mailbox. Vragen of tips? Mail naar signalen@dfobv.nl.", SIG_AANMELD, "Meld je gratis aan")
    page("signalen.html", "DFO Signalen – de nieuwsbrief voor de financieel adviseur",
         "DFO Signalen: jouw wekelijkse update met signalen uit de markt, speciaal voor onafhankelijk financieel adviseurs.", body)



SP = "https://sp.dfobv.nl"
SP_AZ = json.loads((SRC / "serviceproviders.json").read_text())
SP_FEAT = [
    ("Capsearch", "Serviceprovider voor vastgoed en bedrijfsfinanciering.", "/serviceprovider/capsearch"),
    ("certe assuradeuren", "Bij certe groep zetten we ons dagelijks in om risicoadviseurs en hun klanten in heel Nederland duurzaam te ondersteunen.", "/serviceprovider/certe-assuradeuren/"),
    ("Financieel fit", "Wij zorgen ervoor dat consumenten financieel fit zijn en blijven dankzij een sterke digitale ondersteuning.", "/serviceprovider/financieel-fit/"),
    ("Financieel Zeker", "Je financiën op orde. Financieel Zeker ziet het als haar verantwoordelijkheid. Je financiën moeten goed geregeld zijn.", "/serviceprovider/financieel-zeker"),
    ("Heinenoord", "Volmachtbedrijf en serviceprovider. Al meer dan 30 jaar persoonlijke service en betrouwbare kwaliteit.", "/serviceprovider/heinenoord-assuradeuren/"),
    ("Hoeksche Waard Assuradeuren", "Volledig gedigitaliseerde ondersteunende infrastructuur.", "/serviceprovider/hoeksche-waard-assuradeuren/"),
    ("Home Invest", "Home Invest is een landelijke hypotheek serviceprovider met persoonlijk contact en veel expertise, onafhankelijk van aanbieders.", "/serviceprovider/home-invest/"),
    ("Huismerk", "Volledige ondersteuning via dossier support via het Huismerk Serviceteam", "/serviceprovider/huismerk/"),
    ("LNI", "LNI is een kwalitatief hoogstaande dienstverlener “serviceprovider” voor het intermediair", "/serviceprovider/landelijk-netwerk-inkoopcombinatie/"),
    ("Turien & Co Assuradeuren", "Turien & Co. Assuradeuren, een assuradeur met een mix van Nederlandse en buitenlandse volmachten.", "/serviceprovider/turien-amp-co-assuradeuren"),
    ("VCN Verzekeringen", "VCN zorgt ervoor dat advies mensenwerk blijft.", "/serviceprovider/vcn/"),
    ("VCN Kredieten", "Beste serviceprovider voor consumptieve leningen, zakelijke kredieten en alternatieve financieringen.", "/serviceprovider/vcn-kredieten"),
    ("VCN Hypotheken", "Het breedste aanbod aan hypotheekverstrekkers, het hoogste kennisniveau en vaste aanspreekpunten.", "/serviceprovider/vcn-hypotheken"),
    ("VKG", "VKG biedt u toegang tot de gehele financiële markt. Efficiënt en doelgericht.", "/serviceprovider/vkg"),
    ("Voogd", "Voogd is dé serviceprovider voor particuliere en zakelijke schadeverzekeringen.", "/serviceprovider/voogd-en-voogd/"),
]
SP_DOCS = [
    ("Persbericht 2026", "https://www.dfobv.nl/wp-content/uploads/2026/06/260622-Persbericht-Waardering-serviceproviders.pdf"),
    ("Vakpaper Serviceproviders 2026 – meting 1", "https://www.dfobv.nl/wp-content/uploads/2026/06/Vakpaper-Serviceproviders-2026-meting-1.pdf"),
    ("Alle persberichten", "https://sp.dfobv.nl/wp-content/persberichten.pdf"),
    ("Serviceproviderscongres", "https://www.serviceproviderscongres.nl/"),
]


def spu(u):
    return u if u.startswith("http") else SP + u


def serviceproviders_tile():
    feat = "".join(f'<a class="chip" href="{E(spu(u))}" rel="noopener" style="text-decoration:none">{E(n)}</a>' for n, _, u in SP_FEAT[:8])
    return f"""<section id="serviceproviders-tegel"><div class="wrap"><div class="card" style="padding:0;overflow:hidden"><div class="split rev" style="gap:0;align-items:stretch">
  <div style="padding:34px">
    <span class="kicker" style="color:var(--blue)">Vergelijker</span>
    <h2>DFO Serviceproviders</h2>
    <p>Vergelijk de serviceproviders op kwaliteit, snelheid, aanbod en waardering. Bureau DFO vergelijkt {len(SP_AZ)} serviceproviders op kerngegevens, primaire en aanvullende diensten, samenwerking en meer.</p>
    <div class="chips">{feat}</div>
    <div class="btns"><a class="btn btn-primary arrow" href="serviceproviders.html">Vergelijk alle serviceproviders</a><a class="btn btn-ghost" href="{SP_DOCS[0][1]}" rel="noopener">Persbericht 2026</a></div>
  </div>
  <div style="background:var(--bg)"><img src="assets/img/video.jpg" alt="" loading="lazy" style="width:100%;height:100%;object-fit:cover"></div>
</div></div></div></section>"""


def build_serviceproviders():
    letters = {}
    for a in sorted(SP_AZ, key=lambda x: x["t"].lower()):
        letters.setdefault(a["t"][0].upper(), []).append(a)
    az = "".join(f'<div class="doc-group"><h4>{L}</h4><ul class="doc-list">' + "".join(
        f'<li><a href="{E(spu(a["u"]))}" rel="noopener">{icon("brief")}<span>{E(a["t"])}</span></a></li>' for a in xs) + "</ul></div>"
        for L, xs in letters.items())
    feat = "".join(f'<a class="card" href="{E(spu(u))}" rel="noopener"><h3>{E(n)}</h3><p>{E(d)}</p><span class="more arrow">Meer info </span></a>' for n, d, u in SP_FEAT)
    chap = "".join(f'<div class="card"><h3>{E(t)}</h3><p>{E(d)}</p></div>' for t, d in [
        ("Kerngegevens", "Alle feitelijke informatie over de serviceprovider"),
        ("Primaire diensten", "Alle diensten die bijdragen aan het primaire proces van adviseren en bemiddelen in financiële producten"),
        ("Aanvullende diensten", "Diensten die aanvullend worden aangeboden"),
        ("Samenwerking / deelnemerschap", "De vorm waarin de diensten worden aangeboden en de zaken die te maken hebben met de aansluiting bij de betreffende serviceprovider"),
        ("Diversen", "Extra informatie vanuit de serviceprovider.")])
    docs = "".join(f'<a class="card" href="{E(u)}" rel="noopener"><div class="icon">{icon("doc")}</div><h3>{E(t)}</h3><span class="more arrow">Openen </span></a>' for t, u in SP_DOCS)
    body = hero("Welkom op de website van serviceproviders", "Vergelijk de serviceproviders op kwaliteit, snelheid, aanbod en waardering.",
                crumbs=['<a href="onderzoek.html">Onderzoek</a>', "Serviceproviders"],
                btns='<a class="btn btn-light arrow" href="#alle">Klik hier voor alle serviceproviders</a><a class="btn btn-ghost" href="' + SP_DOCS[0][1] + '" rel="noopener">Persbericht 2026</a>')
    body += f"""
<section><div class="wrap split" style="align-items:start">
  <div class="prose"><h2>Meerwaarde Serviceproviders</h2>
  <p>Bureau DFO constateert onder intermediairs een groeiende belangstelling voor het inschakelen van de dienstverlening van een zogenaamde serviceprovider.</p>
  <p>Veel van deze serviceproviders hebben verzekeringsvolmachten van maatschappijen of offertevolmachten van geldverstrekkers. Deze volmachten kunnen van grote meerwaarde zijn voor het acceptatie- of offertetraject van verzekeringen, resp. kredieten.</p>
  <p>Er is inmiddels een groot aantal serviceproviders met een aanzienlijke verscheidenheid in het dienstenaanbod. Dit maakt het voor een financieel dienstverlener lastig om zich objectief te oriënteren op een serviceprovider die aansluit bij het gewenst profiel.</p>
  <p>Daarom heeft Bureau DFO aan bekende serviceproviders gevraagd een aantal vragen over hun dienstverlening te beantwoorden. De resultaten van deze inventarisatie vindt u op de volgende pagina’s.</p>
  <p>Bureau DFO hoopt dat deze overzichten bijdragen aan een goed onderbouwde keuze van de financieel dienstverlener voor een serviceprovider. Heeft u vragen over deze informatie, neemt u dan contact op met Agaat van Ekeren via 033 2542019.</p></div>
  <div><h3>In de pers: Waardering serviceproviders 2026</h3><div class="grid" style="gap:14px">{docs}</div></div>
</div></section>
<section class="alt"><div class="wrap"><div class="sec-head"><span class="kicker" style="color:var(--blue)">De beste match · Complete check</span><h2>Wij vergelijken…</h2><p>De dienstverlening is onderverdeeld in de volgende ‘hoofdstukken’</p></div>
  <div class="grid g3">{chap}</div></div></section>
<section><div class="wrap"><div class="sec-head"><h2>Uitgelichte serviceproviders</h2><p>Ons complete aanbod vindt u, alfabetisch gerangschikt onderaan deze pagina.</p></div>
  <div class="grid g3">{feat}</div></div></section>
<section class="alt" id="alle"><div class="wrap"><div class="sec-head"><h2>Ons gehele aanbod van serviceproviders</h2><p>Hieronder vindt u een compleet overzicht van alle serviceproviders die wij vergelijken. Klik op de provider waar u meer informatie over wilt, om alle details te bekijken.</p></div>
  {az}</div></section>
""" + callout("Vragen over de vergelijking?", "Neem contact op met Agaat van Ekeren, relatiemanager bij Bureau DFO.", mailto("avanekeren@dfobv.nl", "Vraag over Serviceproviders"), "Mail Agaat")
    page("serviceproviders.html", "DFO Serviceproviders – vergelijk serviceproviders", "Vergelijk de serviceproviders op kwaliteit, snelheid, aanbod en waardering.", body)



NAZ = "https://www.dfonazorg.nl"
NAZ_LOGIN = "https://inloggen.dfonazorg.nl/inloggen/"


def build_nazorg():
    body = hero("Nazorg &amp; Onderhoud Portal", "Welkom bij de Nazorg &amp; Onderhoud Portal van Bureau DFO!",
                crumbs=["Nazorg &amp; Onderhoud"],
                btns=f'<a class="btn btn-light arrow" href="{NAZ}/aanmelden/" rel="noopener">Account aanmaken</a><a class="btn btn-ghost" href="{NAZ_LOGIN}" rel="noopener">Inloggen</a>')
    body = body.replace('<div class="img"><img src="assets/img/nazorg.svg"', '<div class="img" style="background:#fff;display:grid;place-items:center;padding:30px"><img src="assets/img/nazorg.svg" style="object-fit:contain"')
    body += f"""
<section><div class="wrap split" style="align-items:start">
  <div class="prose">
  <p>Nazorg op financiële producten staat in het middelpunt van de belangstelling. Niet alleen is het zo dat toezichthouder AFM haar wens heeft geuit om te komen tot een wettelijke inkadering van deze nazorg. Ook groeit de hoeveelheid jurisprudentie over de invulling van nazorg door financiële dienstverleners.</p>
  <p>Maar bovenal heeft de ‘intelligente lock down’ als gevolg van de coronapandemie bij veel kantoren het besef gekweekt dat planmatig onderhoud van lopende financiële producten bij de bestaande klanten (= nazorg) een waardevol en rendabel onderdeel kan zijn van hun dienstverlening. Goed gepland en efficiënt uitgevoerd onderhoud zorgt voor tevreden klanten en een stabiele omzet.</p>
  <p>Bureau DFO helpt u graag om de door uw onderneming te leveren nazorg op een goede en doordachte manier in te vullen. In deze portal vindt u een groot aantal modeldocumenten die u kunnen helpen bij het maken van afspraken met klanten over, en het vastleggen van uw nazorgverplichtingen. Ook heeft Bureau DFO voor u alle relevante publicaties van de AFM over nazorg verzameld en gemakkelijk toegankelijk gemaakt. En tot slot is er een enorme hoeveelheid jurisprudentie voor u ontsloten, waaruit blijkt hoe rechters of Kifid aankijken tegen geschillen over het al dan niet correct uitvoeren van nazorg door financiële dienstverleners.</p>
  <p>Op deze portal treft u alle op dit moment beschikbare nazorgdocumenten aan. Deze worden indien nodig geactualiseerd. Heeft u vragen mail ons dan op <a href="mailto:info@dfobv.nl">info@dfobv.nl</a></p>
  <div class="btns"><a class="btn btn-primary arrow" href="{NAZ_LOGIN}" rel="noopener">Naar alle nazorg documenten</a></div>
  </div>
  <div class="grid" style="gap:16px">
    <div class="card"><h3>Heeft u al een account bij Nazorg Portal?</h3><p>Klik hier, login en download direct uw bestanden.</p><a class="more arrow" href="{NAZ_LOGIN}" rel="noopener">Klik hier </a></div>
    <div class="card price"><h3>Nog geen account? Maak er snel één aan!</h3><p>Door het aanmaken van een account krijg u toegang tot alle downloads/bestanden.</p>
      <p>Fijn dat u interesse heeft om toegang te krijgen tot de documentatie in de DFO Portal Nazorg &amp; Onderhoud. De documentatie in deze omgeving is zorgvuldig samengesteld en wordt continue geüpdatet en voorzien van nieuwe informatie/documenten.</p>
      <div class="amount">€ 195,- <small>eenmalig, exclusief btw</small></div>
      <p class="fine">Uw aanvraag nemen wij in behandeling, u ontvangt een bevestiging in uw inbox. Na bevestiging van uw aanmelding krijgt u toegang tot alle documenten en ontvangt u automatisch nieuwe documenten en updates.</p>
      <a class="btn btn-primary arrow" href="{NAZ}/aanmelden/" rel="noopener" style="margin-top:10px">Account aanmaken</a></div>
  </div>
</div></section>
<section class="alt"><div class="wrap grid g3">
  <a class="card" href="documenten.html#nazorg"><div class="icon">{icon('doc')}</div><h3>Modeldocumenten nazorg</h3><p>Alle nazorgdocumenten uit de DFO-webshop, per onderwerp.</p><span class="more arrow">Bekijk documenten </span></a>
  <a class="card" href="nazorg-calculator.html"><div class="icon">{icon('calc')}</div><h3>Calculator onderhoud- en nazorgabonnement</h3><p>Bereken het benodigde maandbedrag en de fte voor je abonnement.</p><span class="more arrow">Naar de calculator </span></a>
  <a class="card" href="{NAZ}/" rel="noopener"><div class="icon">{icon('folder')}</div><h3>dfonazorg.nl</h3><p>De DFO Portal Nazorg &amp; Onderhoud.</p><span class="more arrow">Bezoek de portal </span></a>
</div></section>
"""
    page("nazorg.html", "Nazorg & Onderhoud Portal – Bureau DFO",
         "De Nazorg & Onderhoud Portal van Bureau DFO: modeldocumenten, AFM-publicaties en jurisprudentie over nazorg.", body)


def portals_section():
    """Vier tegels voor de DFO-portalen."""
    sig = "".join(f'<li><a href="{E(e["u"])}" rel="noopener">{E(e["t"])} – {E(e["d"])}</a></li>' for e in SIG[:3])
    cats = ["Hypotheken", "Schade", "Inkomen, leven & pensioen", "Bedrijfsvoering", "Compliance"]
    nxt = agenda[0] if agenda else None
    nd = datetime.date.fromisoformat(nxt["d"]) if nxt else None
    nxt_html = f'<p class="fine" style="font-size:.86rem;color:var(--muted)">Eerstvolgende: <strong>{nd.day} {MAANDEN_LANG[nd.month-1]}</strong> – {E(nxt["t"])}</p>' if nxt else ""
    tiles = [
        ("opleidingen.html", "cap", "Opleidingsportaal", f"Het opleidingsportaal voor financieel dienstverleners: {len(cursussen)} opleidingen in hypotheken, schade, inkomen, compliance en bedrijfsvoering.",
         nxt_html + '<div class="chips" style="margin:6px 0 0">' + "".join(f'<span class="tag">{E(c)}</span>' for c in cats) + "</div>",
         [("opleidingen.html", "Alle opleidingen"), ("opleidingen.html#agenda", "Agenda"), (PORTAL + "/inloggen-prs/standaard", "Inloggen")]),
        ("signalen.html", "mail", "DFO Signalen", "Jouw wekelijkse update met signalen uit de markt, speciaal voor onafhankelijk financieel adviseurs.",
         f'<ul class="mini">{sig}</ul>', [("signalen.html", "Alle edities"), (SIG_AANMELD, "Gratis aanmelden")]),
        ("serviceproviders.html", "chart", "Serviceproviders", f"Vergelijk {len(SP_AZ)} serviceproviders op kwaliteit, snelheid, aanbod en waardering.",
         '<p class="fine" style="font-size:.86rem;color:var(--muted)">Kerngegevens · primaire en aanvullende diensten · samenwerking · diversen</p>',
         [("serviceproviders.html", "Vergelijk alle serviceproviders"), (SP_DOCS[0][1], "Persbericht 2026")]),
        ("nazorg.html", "folder", "Nazorg &amp; Onderhoud", "Het portaal met alle documenten over nazorg en onderhoud: modeldocumenten, AFM-publicaties en jurisprudentie.",
         '<p class="fine" style="font-size:.86rem;color:var(--muted)">Toegang: eenmalig € 195,- excl. btw</p>',
         [("nazorg.html", "Meer over de portal"), (NAZ_LOGIN, "Inloggen")]),
    ]
    html_ = ""
    for href, ic, t, d, extra, links in tiles:
        ls = "".join(f'<a class="more arrow" href="{E(u)}"{" rel=noopener" if u.startswith("http") else ""} style="display:block;margin-top:6px">{E(lt)} </a>' for u, lt in links)
        html_ += f'<div class="card portal"><a href="{href}" class="portal-head"><div class="icon">{icon(ic)}</div><h3>{t}</h3></a><p>{d}</p>{extra}<div style="margin-top:auto;padding-top:14px">{ls}</div></div>'
    return f"""<section class="alt" id="portalen"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Portalen</span><h2>Alle DFO-portalen op één plek</h2></div>
  <div class="grid g4">{html_}</div>
</div></section>"""



def build_kennisbank_page():
    import kennisbank
    print("kennisbank:", kennisbank.build_kennisbank(page, hero, callout, icon, cursussen, agenda), "begrippen")


def build_related_pages():
    import related
    print("opleidingsblokken toegevoegd op", related.build_related(cursussen, agenda), "pagina's")


if __name__ == "__main__":
    COLS.extend(c for c in extra_columns() if c["slug"] not in {x["slug"] for x in COLS})

    # www.dfobv.nl: pagina's, artikelen, webshop, agenda-archief
    import dfobv_site
    stats = dfobv_site.build_dfobv({"page": page, "hero": hero, "callout": callout, "icon": icon})
    print("dfobv.nl:", stats, "nieuwe afbeeldingen:", dfobv_site.download_images())
    for fn in [build_home, build_opleidingen, build_documenten, build_compliance, build_abonnementen, build_zalen,
               build_studio, build_over, build_columns, build_congressen, build_secretariaten, build_onderzoek,
               build_calculator, build_contact, build_themas, build_performance, build_mening, build_actievoorwaarden, build_signalen, build_serviceproviders, build_nazorg, build_kennisbank_page, build_404, build_related_pages, build_zoeken, build_redirects]:
        fn()
    print("OK –", len(cursussen), "cursussen,", len(agenda), "data")
