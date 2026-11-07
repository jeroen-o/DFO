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
  <a href="{PORTAL}/inloggen-prs/standaard" rel="noopener">Inloggen opleidingsportaal</a>
</div></div>
<header class="site"><div class="wrap">
  <a class="logo" href="index.html" aria-label="Bureau DFO – home"><img src="assets/img/logo.png" alt="Bureau DFO – dienstverlening voor financiële ondernemers" width="613" height="145"></a>
  <button class="menu-btn" aria-expanded="false" aria-controls="mainnav">Menu</button>
  <nav class="main" id="mainnav" aria-label="Hoofdmenu"><ul>{nav}<li><a class="cta" href="contact.html">Contact</a></li></ul></nav>
</div></header>
<main id="inhoud">
{body}
</main>
<footer class="site"><div class="wrap">
  <div class="fgrid">
    <div>
      <div class="flogo"><img src="assets/img/logo.png" alt="Bureau DFO" width="613" height="145"></div>
      <p>Jouw partner waar het gaat om succesvol ondernemen in de financiële dienstverlening. Sinds 1992.</p>
      <p>{ADRES}<br><a href="{TEL_HREF}">{TEL}</a><br><a href="mailto:{MAIL}">{MAIL}</a></p>
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
    body = hero(
        "Succesvol ondernemen in de financiële dienstverlening",
        "Bureau DFO ondersteunt financieel adviseurs, aanbieders en brancheorganisaties met opleidingen, "
        "compliance, modeldocumenten, onderzoek en faciliteiten — allemaal onder één dak in Hoevelaken.",
        kicker="Bureau DFO · sinds 1992", img="assets/img/de-wel.jpg", small=False,
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
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Wat we doen</span><h2>Alles onder één dak</h2>
  <p>Van kennisontwikkeling tot uitvoering: een breed pakket aan diensten voor financiële dienstverleners en hun brancheorganisaties.</p></div>
  <div class="grid g3">
    {svc_card("opleidingen.html","cap","Opleidingen","Praktijkgerichte trainingen voor hypotheken, schade, inkomen, compliance en bedrijfsvoering — ook incompany.")}
    {svc_card("documenten.html","doc","Documenten &amp; contracten","Ruim 200 modeldocumenten: van Wft tot AVG, van hypotheken tot schade. Direct inzetbaar.")}
    {svc_card("compliance.html","shield","DFO Compliance","AFM-vergunning, Wft-audit, Wwft en AVG: grip op wet- en regelgeving met persoonlijke begeleiding.")}
    {svc_card("abonnementen.html","mail","Abonnementen","Wft-nieuwsbrief, kant-en-klare nieuwsteksten en servicepakketten met korting op opleidingen.")}
    {svc_card("zalencentrum.html","room","Zalencentrum","Zeven flexibele vergader- en cursuszalen bij knooppunt Hoevelaken, inclusief ontvangst.")}
    {svc_card("studio.html","mic","Studio","Webinar-, podcast- en videoproducties en studioverhuur met technische ondersteuning.")}
  </div>
</div></section>

<section class="alt"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Actueel</span><h2>Nieuws &amp; publicaties</h2></div>
  <div class="news">
    <a class="card img" href="assets/pdf/persbericht-bureau-dfo-meedenken-met-kantoor-bepaalt-waardering-serviceproviders.pdf">
      <div class="ph"><img src="assets/img/persbericht.jpg" alt="" loading="lazy" width="960" height="608"></div>
      <div class="body"><span class="tag">Onderzoek</span><h3>Resultaten Onderzoek serviceproviders 2026 II</h3>
      <p>Op alle acht onderzochte aspecten ligt de waardering lager dan het belang dat adviseurs eraan hechten. Meedenken met het kantoor blijkt bepalend.</p>
      <span class="more arrow">Lees het persbericht (pdf) </span></div></a>
    <a class="card img" href="https://www.dfobv.nl/wp-content/uploads/2026/10/Samenvatting-Performance-onderzoek-Kwaliteit-binnendienst-en-acceptatie-2026.pdf" rel="noopener">
      <div class="ph"><img src="assets/img/performance.jpg" alt="" loading="lazy" width="960" height="676"></div>
      <div class="body"><span class="tag">Gratis download</span><h3>Performanceonderzoek 2026 – deel II</h3>
      <p>De ervaring van het intermediair met de binnendienst van aanbieders, gemeten over twee jaar op zes onderdelen van de samenwerking.</p>
      <span class="more arrow">Download de samenvatting </span></div></a>
    <a class="card img" href="columns.html#{COLS[0]['slug']}">
      <div class="ph"><img src="assets/img/jurjen.jpg" alt="" loading="lazy" width="658" height="370"></div>
      <div class="body"><span class="tag">Column</span><h3>{E(COLS[0]['titel'])}</h3>
      <p>De nieuwste column van Jurjen Oosterbaan Martinius over de waarde van een goede buitendienst voor het intermediair.</p>
      <span class="more arrow">Lees de column </span></div></a>
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
    <span class="kicker" style="color:var(--blue)">Gratis tool</span><h2>Calculator onderhoud- en nazorgabonnement</h2>
    <p>Bereken direct online hoeveel fte er nodig is voor het abonnement dat je aanbiedt, en welk maandbedrag de gewenste winst oplevert van je onderhouds- en nazorgactiviteiten.</p>
    <p class="muted" style="font-size:.9rem">Mede mogelijk gemaakt door Blinqx Verzekering &amp; Hypotheek. De tool werkt het best op een groot scherm.</p>
    <div class="btns"><a class="btn btn-primary arrow" href="nazorg-calculator.html">Meer over de calculator</a></div>
  </div>
  <div class="media"><img src="assets/img/calculator.jpg" alt="Schermafbeelding van de calculator" loading="lazy" width="960" height="968"></div>
</div></section>

<section><div class="wrap">
  <div class="sec-head"><h2>Meer van DFO</h2></div>
  <div class="grid g4">
    {ext_card("https://www.dfosignalen.nl/","DFO Signalen","De gratis wekelijkse nieuwsbrief met actualiteiten uit de branche.")}
    {ext_card("https://sp.dfobv.nl/","Serviceproviders vergelijken","Vergelijk serviceproviders op kwaliteit, snelheid, aanbod en waardering.")}
    {ext_card("https://expertisegroepschade.nl/","Expertisegroep Schade","Het netwerk voor schadebehandelaars die op de hoogte willen blijven.")}
    {ext_card("https://www.dfonazorg.nl/","Nazorg &amp; Onderhoud","Het portaal met alle documenten over nazorg en onderhoud.")}
  </div>
</div></section>
""" + callout("Benieuwd wat Bureau DFO voor jou kan betekenen?",
              "Bel 033 258 04 60 of stuur een bericht. We reageren binnen één werkdag.")
    page("index.html", "Bureau DFO – succesvol ondernemen in de financiële dienstverlening",
         "Opleidingen, compliance, modeldocumenten, onderzoek, zalen en studio voor financieel adviseurs. Bureau DFO in Hoevelaken.",
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
  <div class="sec-head"><h2>Volledig aanbod</h2><p>Niet zeker welke opleiding bij je past? Bel <a href="{TEL_HREF}">{TEL}</a> of mail <a href="mailto:opleidingen@dfobv.nl">opleidingen@dfobv.nl</a> — we adviseren je graag.</p></div>
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
    <span class="kicker" style="color:var(--blue)">Incompany</span>
    <h2>Een opleiding bij jou op kantoor</h2>
    <p>Zie je een opleiding die interessant is voor meerdere collega’s? Kies dan voor het gemak van een incompany training. De docent komt naar jouw locatie en verzorgt de training op de gewenste dag en tijd. Het kan ook bij ons in Hoevelaken.</p>
    <ul class="check">
      <li>Op maat gemaakt voor jouw onderneming en het niveau van je medewerkers</li>
      <li>Meer tijd voor de onderwerpen die binnen jullie organisatie belangrijk zijn</li>
      <li>Alle opleidingen uit ons aanbod zijn beschikbaar als incompany</li>
    </ul>
    <div class="btns"><a class="btn btn-primary arrow" href="{mailto('opleidingen@dfobv.nl','Aanvraag incompany opleiding')}">Vraag incompany aan</a></div>
  </div>
  <div class="media"><img src="assets/img/grote-zaal.jpg" alt="Cursuszaal bij DFO in Hoevelaken" loading="lazy" width="960" height="456"></div>
</div></section>

<section class="alt"><div class="wrap grid g3">
  <div class="card"><div class="icon">{icon('users')}</div><h3>Account in het portaal</h3><p>Maak een account aan in het opleidingsportaal. Zo zie je altijd voor welke opleidingen je bent aangemeld en wat de status is.</p><a class="more arrow" href="{PORTAL}/inloggen-prs/standaard" rel="noopener">Inloggen of account maken </a></div>
  <div class="card"><div class="icon">{icon('brief')}</div><h3>Korting met servicepakket</h3><p>Met een DFO Servicepakket krijg je € 95,- korting op 2 of 3 opleidingen per jaar, plus gratis deelname aan het Webinar Actualiteiten.</p><a class="more arrow" href="abonnementen.html">Bekijk servicepakketten </a></div>
  <div class="card"><div class="icon">{icon('mail')}</div><h3>Vragen over aanmelden?</h3><p>Lukt aanmelden niet, of heb je een vraag over een opleiding? Onze afdeling Opleidingen helpt je graag.</p><a class="more arrow" href="mailto:opleidingen@dfobv.nl">opleidingen@dfobv.nl </a></div>
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
  <div class="note" style="margin-top:24px">Bestellen en downloaden gaat via de DFO-webshop. Sommige documenten staan in meerdere categorieën. Heb je een <a href="abonnementen.html">servicepakket</a>, dan krijg je 2 of 3 documenten per jaar gratis.</div>
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


def build_compliance():
    body = hero("DFO Compliance", "Jouw partner voor een beheerste en integere bedrijfsvoering. Jij richt je op je klanten, wij zorgen dat je bedrijfsprocessen structureel voldoen aan de Wft.",
                crumbs=["Compliance"], img="assets/img/robert-jan.jpg", small=False,
                btns=f'<a class="btn btn-light arrow" href="{mailto("rjvanloon@dfocompliance.nl","Vraag aan DFO Compliance")}">Neem contact op</a><a class="btn btn-ghost" href="#audit">Wft-audit</a>')
    body += f"""
<section><div class="wrap split">
  <div>
    <h2>Compliance is de basis van je dienstverlening</h2>
    <p>Compliance is in de financiële sector geen bijzaak, maar de basis waarop jouw dienstverlening rust. DFO Compliance begeleidt je door de complexe en voortdurend veranderende wet- en regelgeving, met praktische ondersteuning en modeldocumenten.</p>
    <p><strong>Robert-Jan van Loon</strong>, compliance consultant bij DFO, is jouw aanspreekpunt en begeleidt je persoonlijk.</p>
    <p><a href="mailto:rjvanloon@dfocompliance.nl">rjvanloon@dfocompliance.nl</a> · <a href="{TEL_HREF}">{TEL}</a></p>
  </div>
  <div class="grid g2">
    <div class="card"><div class="icon">{icon('shield')}</div><h3>AFM-vergunning</h3><p>Aanvragen en wijzigen, zonder vertraging.</p></div>
    <div class="card"><div class="icon">{icon('folder')}</div><h3>Geborgde bedrijfsvoering</h3><p>Alle documenten om aan je vergunning te blijven voldoen.</p></div>
    <div class="card"><div class="icon">{icon('doc')}</div><h3>Wwft, AVG &amp; MiFID</h3><p>Naleving van complexe wet- en regelgeving.</p></div>
    <div class="card"><div class="icon">{icon('chart')}</div><h3>Wft-audit</h3><p>Volledig, als second opinion of als zelfaudit.</p></div>
  </div>
</div></section>

<section class="alt"><div class="wrap split">
  <div><h2>Ondersteuning bij je AFM-vergunning</h2>
  <p>Het is cruciaal dat je de juiste vergunning hebt voor al je bedrijfsactiviteiten. De AFM hanteert een groot aantal documenten en formulieren. Wij zijn je gids in dit oerwoud en zetten daarnaast onze eigen aanvullende documenten in, zodat je aanvraag soepel verloopt.</p></div>
  <div class="card"><h3>Onze ondersteuning omvat onder meer</h3><ul class="check">
    <li>het aanvragen van een zelfstandige vergunning</li><li>het aanvragen van een collectieve vergunning</li>
    <li>het aanmelden van een aangesloten instelling</li><li>het aan- of afmelden van beleidsbepalers</li>
    <li>het doorvoeren van rechtsvormwijzigingen</li><li>EP-notificaties (Europees Paspoort) bij grensoverschrijdende dienstverlening</li></ul></div>
</div></section>

<section><div class="wrap split rev">
  <div><h2>Documenten voor een geborgde bedrijfsvoering</h2>
  <p>Na ontvangst van de vergunning is het belangrijk dat je blijft voldoen aan de voorwaarden. Dit heet borging van de bedrijfsvoering. Wij helpen je met het opstellen en actualiseren van onder andere:</p>
  <ul class="check"><li>de Dienstenwijzer en Vergelijkingskaart</li><li>procedures voor klachten- en incidentenadministratie</li>
  <li>richtlijnen voor de borging van betrouwbaarheid en vakbekwaamheid van medewerkers</li><li>het verplichte privacydocument en bijbehorende verwerkersovereenkomsten</li></ul>
  <a class="btn btn-ghost arrow" href="documenten.html#wft-wwft">Bekijk de modellen en brieven</a></div>
  <div><h2>Naleving van wet- en regelgeving</h2>
  <div class="grid" style="gap:14px">
    <div class="card"><h3>Wwft</h3><p>Risicoanalyses, gedegen beleid en een classificatiesysteem voor klanten.</p></div>
    <div class="card"><h3>AVG</h3><p>Inventarisatie van verwerkingen, meldplicht datalekken en verwerkersovereenkomsten.</p></div>
    <div class="card"><h3>Sanctiewet</h3><p>Processen die borgen dat je geen transacties aangaat met gesanctioneerde personen en bedrijven.</p></div>
    <div class="card"><h3>Nationaal Regime MiFID</h3><p>Productontwikkeling, kostentransparantie en geschiktheidstoetsen bij beleggingsdiensten.</p></div>
  </div></div>
</div></section>

<section class="alt" id="audit"><div class="wrap">
  <div class="sec-head"><h2>Ondersteuning bij je Wft-audit</h2><p>Periodiek toetsen of je bedrijfsvoering voldoet aan de Wft-principes voor een ‘beheerste en integere bedrijfsvoering’. Wij bieden de auditvorm die bij jouw situatie past.</p></div>
  <div class="grid g3">
    <div class="card"><span class="tag">Volledig uitbesteed</span><h3>Volledige audit door DFO</h3><p>Wij voeren de audit volledig uit, van het toetsen van je bedrijfsprocessen tot een onderbouwd eindoordeel. Je hoeft zelf geen tijd te investeren.</p></div>
    <div class="card"><span class="tag">Second opinion</span><h3>Beoordeling van je zelfaudit</h3><p>Al zelf een audit uitgevoerd? Wij beoordelen je bevindingen kritisch en geven een onafhankelijke second opinion.</p></div>
    <div class="card"><span class="tag">Zelf doen</span><h3>Zelfaudit met ondersteuning</h3><p>Je krijgt een compleet auditdocument en wij beantwoorden onderweg al je vragen, zodat je niet vastloopt in details.</p></div>
  </div>
  <p style="margin-top:24px">Met een gedocumenteerde ‘auditmap’ beschik je over een krachtig bewijsstuk van je interne controle. Brengt de audit verbeterpunten aan het licht, dan helpen we je met een verbeterplan.</p>
</div></section>

<section><div class="wrap grid g3">
  <a class="card" href="abonnementen.html"><div class="icon">{icon('mail')}</div><h3>Wft-nieuwsbrief</h3><p>Wekelijks scherp op actuele wetgeving, AFM-inzichten en praktische tips.</p><span class="more arrow">Abonneren </span></a>
  <a class="card" href="opleidingen.html?q=compliance"><div class="icon">{icon('cap')}</div><h3>Compliance-trainingen</h3><p>Praktijkgerichte trainingen, o.a. het AFM-vergunningentraject, Wwft en digitale weerbaarheid.</p><span class="more arrow">Bekijk trainingen </span></a>
  <a class="card" href="documenten.html#bedrijfsvoering"><div class="icon">{icon('doc')}</div><h3>Modellen en brieven</h3><p>Kant-en-klare modellen, actueel en direct inzetbaar in de dagelijkse praktijk.</p><span class="more arrow">Bekijk modellen </span></a>
</div></section>
""" + callout("Benieuwd wat DFO Compliance voor jouw onderneming kan betekenen?",
              "In een vrijblijvend gesprek kijken we samen waar je staat en wat er nodig is. We reageren binnen 1 werkdag.",
              mailto("rjvanloon@dfocompliance.nl", "Vrijblijvend gesprek DFO Compliance"), "Plan een gesprek")
    page("compliance.html", "DFO Compliance: AFM-vergunning en Wft-audit – Bureau DFO",
         "Ondersteuning bij AFM-vergunning, Wft-audit, Wwft, AVG, Sanctiewet en MiFID voor financieel advieskantoren.", body)


def build_abonnementen():
    def nb(title, text, prijs, voorbeeld, extra=""):
        return f'''<div class="card price"><h3>{title}</h3><p>{text}</p><div class="amount">{prijs}</div>{extra}
<div class="btns" style="margin-top:16px"><a class="btn btn-primary" href="#aanvragen">Aanvragen</a><a class="btn btn-ghost" href="{voorbeeld}" rel="noopener">Voorbeeld</a></div></div>'''
    sp1 = ["2× opleiding met € 95,- korting", "1× deelname Webinar Actualiteiten", "2 gratis documenten", "Wft-nieuwsbrief",
           "Helpdesk voor al je Wft-vragen", "Jaarlijks het Onderzoek waardering assurantieportefeuilles",
           "50% korting op 1 informatierapport naar keuze", "50% korting op een klanttevredenheidsonderzoek",
           "50% korting op nieuwsteksten voor particuliere relaties", "5 gratis faillissementscontroles"]
    sp2 = ["3× opleiding met € 95,- korting", "1× deelname Webinar Actualiteiten", "3 gratis documenten", "Wft-nieuwsbrief",
           "Helpdesk voor al je Wft-vragen", "Jaarlijks het Onderzoek waardering assurantieportefeuilles",
           "1 informatierapport naar keuze", "Klanttevredenheidsonderzoek", "Nieuwsteksten voor particuliere relaties",
           "10 gratis faillissementscontroles"]
    li = lambda xs: "".join(f"<li>{E(x)}</li>" for x in xs)
    faq = [
        ("Korting op DFO-opleidingen", "Jij of je collega’s kiezen elk jaar zelf welke opleiding uit ons aanbod het beste past. Op de opleiding van jullie keuze ontvang je € 95,- korting: bij het Servicepakket voor 2 opleidingen per jaar, bij het Servicepakket Plus voor 3."),
        ("Gratis deelname aan Webinar Actualiteiten", "Regelmatig organiseren we een Webinar Actualiteiten met Jurjen Oosterbaan Martinius, waarin je volledig wordt bijgepraat over alle actualiteiten uit de sector."),
        ("Keuze uit ruim 200 modeldocumenten", "Bureau DFO ontwikkelt zelf en met derden contracten, modellen en formulieren om te voldoen aan wet- en regelgeving of je bedrijfsvoering te optimaliseren. Je kiest zelf welke modellen bij je passen."),
        ("Wft-nieuwsbrief", "Blijf volledig en tijdig op de hoogte van ontwikkelingen en nieuwe wetgeving. We behandelen ook gerechtelijke uitspraken, zodat je er leermomenten uit kunt halen."),
        ("Helpdesk via de mail", "Stel al je (Wft-)vragen per e-mail aan avanekeren@dfobv.nl en je hebt binnen twee werkdagen antwoord. Is dat niet haalbaar of is een opinie van derden nodig, dan laten we je dat weten."),
        ("Onderzoek waardering assurantieportefeuilles", "Al sinds 2004 onderzoekt Bureau DFO hoe advieskantoren de waarde van hun assurantieportefeuille bepalen. Je hebt elk jaar recht op de resultaten."),
        ("Informatierapport naar keuze", "Bijvoorbeeld de salarisindicator voor het financieel advieskantoor, de reader verkeersrecht of fiscale aspecten directe beloning."),
        ("Klanttevredenheidsonderzoek", "Benieuwd hoe jouw klanten je dienstverlening waarderen? Wij voeren in jouw opdracht een onafhankelijk onderzoek uit."),
        ("Nieuwsteksten voor particuliere relaties", "Elke maand vier kant-en-klare teksten voor je website, sociale media of eigen nieuwsbrief, in nieuwsbriefformat én als Word-bestand."),
        ("Faillissementscontroles", "Je moet controleren en kunnen aantonen of een (nieuwe) medewerker eerder bij een faillissement betrokken is geweest. Wij doen die controles voor je via het Nationaal Faillissementsregister."),
    ]
    faq_html = "".join(f'<details class="card" style="padding:18px 22px"><summary style="font-weight:600;cursor:pointer">{E(q)}</summary><p style="margin:.8em 0 0">{E(a)}</p></details>' for q, a in faq)
    body = hero("Abonnementen &amp; servicepakketten",
                "Met onze nieuwsbrieven en servicepakketten blijf je op de hoogte én profiteer je van voordeel. Alle prijzen per maand, exclusief btw en maandelijks opzegbaar.",
                crumbs=["Abonnementen"], btns='<a class="btn btn-light arrow" href="#aanvragen">Direct aanvragen</a>')
    body += f"""
<section><div class="wrap">
  <div class="sec-head"><h2>Servicepakketten</h2><p>Eén pakket voor het hele bedrijf: iedereen bij jou op kantoor mag gebruikmaken van deze producten en diensten.</p></div>
  <div class="grid g2">
    <div class="card price featured"><span class="badge">MEEST GEKOZEN</span><h3>DFO Servicepakket</h3>
      <div class="amount">€ 39,50 <small>per maand excl. btw</small></div><p class="fine">€ 474,- per jaar · totale waarde € 835,- per jaar · opzegtermijn 1 maand</p>
      <ul class="check">{li(sp1)}</ul><a class="btn btn-primary" href="#aanvragen" style="margin-top:auto">Abonnement aanvragen</a></div>
    <div class="card price"><span class="badge" style="background:var(--blue-dd)">MEEST COMPLEET</span><h3>DFO Servicepakket Plus</h3>
      <div class="amount">€ 65,- <small>per maand excl. btw</small></div><p class="fine">€ 780,- per jaar · totale waarde € 1.600,- per jaar · opzegtermijn 1 maand</p>
      <ul class="check">{li(sp2)}</ul><a class="btn btn-primary" href="#aanvragen" style="margin-top:auto">Abonnement aanvragen</a></div>
  </div>
</div></section>

<section class="alt"><div class="wrap">
  <div class="sec-head"><h2>Nieuwsbrieven</h2><p>Periodieke publicaties en benchmarks.</p></div>
  <div class="grid g4">
    {nb("Wft-nieuwsbrief","Wekelijks de laatste ontwikkelingen in wet- en regelgeving rond de Wft, toegankelijk uitgelegd. Zit ook in beide servicepakketten.","€ 23,50 <small>p/m</small>","https://kennisbank.dfobv.nl/")}
    {nb("Nieuwsbrief Hypotheken","Elke maand vier kant-en-klare teksten over hypotheekontwikkelingen voor je website, social media of eigen nieuwsbrief.","€ 15,- <small>p/m</small>","https://hypotheken-update.nl/hypnwkr/113_crt/index.html")}
    {nb("Nieuwsbrief Particulier","Elke maand vier teksten voor particuliere relaties over schade, hypotheken en andere actualiteiten.","€ 15,- <small>p/m</small>","https://www.financieel-alert.nl/nwkr/365_vej/index.php")}
    {nb("DFO Signalen","Jouw wekelijkse update met signalen uit de markt, speciaal voor onafhankelijk financieel adviseurs.","Gratis","https://www.dfosignalen.nl/")}
  </div>
</div></section>

<section><div class="wrap">
  <div class="sec-head"><h2>Wat houdt alles in?</h2></div>
  <div class="grid g2" style="align-items:start">{faq_html}</div>
</div></section>

<section class="alt"><div class="wrap split">
  <div><img src="assets/img/expertisegroep.jpg" alt="Expertisegroep Schadebehandeling" loading="lazy" width="832" height="417" style="max-width:340px;margin-bottom:20px">
  <h2>Expertisegroep Schadebehandeling</h2>
  <ul class="check"><li>Actuele en praktijkgerichte workshops</li><li>Expertmeetings</li><li>Modelcontracten &amp; -formulieren</li><li>Opmerkelijk: nieuwsalert met relevante informatie</li><li>WhatsApp-groep voor deelnemers</li><li>Onderzoek en benchmark</li><li>Bewijs van deelname</li></ul>
  <div class="btns"><a class="btn btn-primary" href="#aanvragen">Aanmelden</a><a class="btn btn-ghost" href="https://expertisegroepschade.nl/informatie/" rel="noopener">Meer over de Expertisegroep</a></div></div>
  <div class="card" id="aanvragen">
    <h2 style="font-size:1.5rem">Abonnement aanvragen</h2>
    <p class="muted">Kies je abonnement(en). Je e-mailprogramma opent met een ingevulde aanvraag aan Agaat van Ekeren; wij nemen binnen 1 werkdag contact op.</p>
    <form class="f" id="aboForm">
      <div class="two"><label>Naam<input name="naam" required autocomplete="name"></label><label>Kantoor<input name="kantoor" autocomplete="organization"></label></div>
      <div class="two"><label>E-mail<input name="email" type="email" required autocomplete="email"></label><label>Telefoon<input name="tel" type="tel" autocomplete="tel"></label></div>
      <fieldset><legend>Interesse in</legend>
        {''.join(f'<label class="opt"><input type="checkbox" name="abo" value="{E(v)}"> {E(v)}</label>' for v in ["DFO Servicepakket","DFO Servicepakket Plus","Wft-nieuwsbrief","Nieuwsbrief Hypotheken","Nieuwsbrief Particulier","Signalen (gratis)","Expertisegroep Schadebehandeling","Geen abonnement, wel een vraag"])}
      </fieldset>
      <label>Opmerkingen of vragen<textarea name="opm"></textarea></label>
      <button class="btn btn-primary" type="submit">Aanvraag opstellen</button>
      <p class="hint">Je gegevens gebruiken we alleen om je aanvraag te verwerken. Liever direct mailen? <a href="mailto:avanekeren@dfobv.nl">avanekeren@dfobv.nl</a></p>
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
        ("Grote zaal", "grote-zaal", "Cursusruimte", "24–30 personen", "School / theater / U-vorm / toetsopstelling", "Scherm, flipover"),
        ("Kleine zaal", "kleine-zaal", "Cursusruimte", "12 personen", "School / U-vorm / toetsopstelling", "Scherm, flipover"),
        ("Havik", "havik", "Cursusruimte", "17 personen", "School / U-vorm / toetsopstelling", "Scherm, flipover"),
        ("Koppelpoort", "koppelpoort", "Cursusruimte", "15–18 personen", "School / U-vorm / toetsopstelling", "Scherm, flipover"),
        ("Lange Jan", "lange-jan", "Cursusruimte", "17 personen", "School / U-vorm / toetsopstelling", "Scherm, flipover"),
        ("Superzaal", "superzaal", "Bijeenkomstruimte", "50–70 personen", "Theater / cabaret (combinatie kleine + grote zaal)", "Schermen, microfoon, flipover"),
    ]
    cards = ""
    for n, img, typ, cap, ops, fac in rooms:
        cards += f'''<div class="card img room"><div class="ph"><img src="assets/img/{img}.jpg" alt="Zaal {E(n)}" loading="lazy" width="960" height="640"></div>
<div class="body"><div class="meta"><span class="tag">{typ}</span><span class="tag alt">{cap}</span></div><h3>{E(n)}</h3>
<dl><dt>Opstelling</dt><dd>{E(ops)}</dd><dt>Faciliteiten</dt><dd>{E(fac)}</dd></dl>
<a class="more arrow" href="{mailto('info@dfozalen.nl', f'Aanvraag zaal {n}', f'Ik wil graag zaal {n} reserveren.%0A%0ADatum:%0AAantal personen:%0AOpstelling:%0ACatering:%0A'.replace('%0A', chr(10)))}">Aanvragen </a></div></div>'''
    body = hero("DFO Zalencentrum", "Van boardroom tot superzaal: in Hoevelaken vind je voor elke vergadering, training of bijeenkomst de ruimte die bij je past.",
                crumbs=["Zalencentrum"], img="assets/img/superzaal.jpg", small=False,
                btns=f'<a class="btn btn-light arrow" href="{mailto("info@dfozalen.nl","Offerte aanvraag zaalhuur")}">Offerte aanvragen</a><a class="btn btn-ghost" href="#zalen">Bekijk de zalen</a>')
    body += f"""
<section><div class="wrap split">
  <div><h2>Vergaderen, trainen en ontmoeten in het hart van Nederland</h2>
  <p>Op zoek naar een locatie voor een vergadering, training, workshop of event? Onze locatie biedt volop ruimte om samen te komen, kennis te delen en nieuwe ideeën op te doen. Wij denken graag met je mee.</p>
  <ul class="check">
    <li>Centraal gelegen aan De Wel 14-16, vlak bij knooppunt Hoevelaken (A1/A28)</li>
    <li>Gratis parkeren voor de deur, met laadpalen voor elektrische auto’s</li>
    <li>Treinstation op 10 minuten lopen</li>
    <li>Zeven flexibele zalen voor groepen tot 70 personen</li>
    <li>Altijd een persoonlijke ontvangst door een van onze gastvrouwen</li>
    <li>Centrale ontmoetingsruimte en kantine</li>
  </ul></div>
  <div class="media"><img src="assets/img/kaart.jpg" alt="Kaart: DFO bij knooppunt Hoevelaken" loading="lazy" width="960" height="442"></div>
</div></section>

<section class="alt" id="zalen"><div class="wrap">
  <div class="sec-head"><h2>Ons aanbod aan zalen</h2><p>Kom gerust eens binnenlopen: de koffie staat klaar.</p></div>
  <div class="grid g4">{cards}</div>
</div></section>
""" + callout("Een ruimte reserveren of combineren?",
              "Agaat van Ekeren denkt graag mee over opstelling, beschikbaarheid en catering. Bel 033 258 04 60 of mail info@dfozalen.nl.",
              mailto("info@dfozalen.nl", "Offerte aanvraag zaalhuur"), "Vraag een offerte aan")
    page("zalencentrum.html", "Vergaderruimte huren in Hoevelaken – DFO Zalencentrum",
         "Zeven vergader- en cursuszalen voor 8 tot 70 personen bij knooppunt Hoevelaken. Gratis parkeren, persoonlijke ontvangst.", body)


def build_studio():
    svc = [
        ("webinar", "Webinarproducties", "studio", "Een webinar is de ideale manier om je boodschap te delen, kennis over te dragen of in contact te komen met je publiek — live of on-demand.",
         ["Voorbereiding: doelen, format en doelgroep (presentatie, panel- of tafelgesprek)", "Technische ondersteuning: camera’s, microfoons, licht en een stabiel uitzendplatform", "Regie en begeleiding tijdens opname en live-uitzending", "Visuele content: slides, banners, achtergronden", "Interactie: live polls, Q&A en chat", "Rapportage na afloop: inschrijvingen, kijkersratio, kijktijd, interacties en evaluaties"]),
        ("podcast", "Podcastproducties", "podcast", "Een podcast is een krachtig middel om je verhaal te delen, een breed publiek te bereiken en langdurige connecties op te bouwen.",
         ["Conceptontwikkeling: interviewreeks, storytelling of educatieve serie", "Professionele opname in de studio of op locatie, eventueel met camerabeelden", "Audiobewerking met muziek en intro/outro", "Publicatie via DFO Signalen, Spotify en YouTube", "Promotiemateriaal: audioclips, social posts en graphics"]),
        ("video", "Videoproductie", "video", "Video is een van de krachtigste manieren om je boodschap over te brengen. Van bedrijfsfilm en promotievideo tot eventfilm en social content.",
         ["Conceptontwikkeling en script/storyboard", "Opnames met professionele camera’s, licht en geluid", "Postproductie: montage, kleurcorrectie, effecten", "Aanlevering klaar om in te sluiten op je website en social media"]),
        ("verhuur", "Studioverhuur met technische ondersteuning", "studioverhuur", "Heb je al een concept? Huur onze volledig uitgeruste studio voor opnames, livestreams of fotoshoots — met een ervaren technicus erbij.",
         ["Camera’s, microfoons, verlichting en greenscreen", "Flexibele inrichting: informeel of zakelijk", "Technicus voor opbouw en bediening", "Extra’s op maat: regie, editing, catering", "Postproductie: montage, kleurcorrectie en audiobewerking"]),
        ("content", "Contentmarketing &amp; social media", "content", "Met strategisch doordachte content vertel je jouw (merk)verhaal op een manier die opvalt, betrokkenheid creëert en resultaat oplevert.",
         ["Strategie en contentkalender", "Teksten, foto’s en video’s", "Campagnebeheer en distributie in de financiële sector", "Engagement-monitoring en rapportage"]),
        ("elearning", "Training &amp; e-learning", "elearning", "On-demand e-learning en trainingen: permanent online beschikbaar voor jouw doelgroep, van onboarding tot software-tutorials.",
         ["Leerdoelen en inhoudsontwikkeling", "Interactie: quizzen, video’s en praktijkvoorbeelden", "Visueel en technisch ontwerp", "Opname in de studio en nabewerking", "Voortgang en resultaten meetbaar"]),
    ]
    cards = "".join(f'<a class="card img" href="#{k}"><div class="ph"><img src="assets/img/{img}.jpg" alt="" loading="lazy"></div><div class="body"><h3>{t}</h3><p>{E(d)}</p><span class="more arrow">Lees meer </span></div></a>' for k, t, img, d, _ in svc)
    secs = ""
    for i, (k, t, img, d, pts) in enumerate(svc):
        secs += f'''<section id="{k}"{' class="alt"' if i % 2 == 0 else ''}><div class="wrap split{' rev' if i % 2 else ''}">
<div><h2>{t}</h2><p>{E(d)}</p><ul class="check">{"".join(f"<li>{E(p)}</li>" for p in pts)}</ul>
<a class="btn btn-primary arrow" href="{mailto(MAIL, 'DFO Studio – ' + html.unescape(t))}">Bespreek je productie</a></div>
<div class="media"><img src="assets/img/{img}.jpg" alt="" loading="lazy"></div></div></section>'''
    steps = "".join(f'<div class="step"><div><h4>{a}</h4><p>{b}</p></div></div>' for a, b in [
        ("Kennismaking en planning", "In een intake brengen we je wensen, doelen en doelgroep helder in kaart."),
        ("Voorbereiding", "Script, gasten, visuals en techniek: alles staat klaar voor de opnamedag."),
        ("Opname of live-uitzending", "Professionele regie en technische begeleiding, zodat jij je op de inhoud richt."),
        ("Afwerking en publicatie", "Montage, rapportage en distributie, ook via onze kanalen in de financiële sector.")])
    body = hero("DFO Studio", "De webcam- en webinarstudio voor de financiële dienstverlening. Wij combineren marktkennis met technische en visuele knowhow.",
                crumbs=["Studio"], img="assets/img/studio2.jpg", small=False,
                btns=f'<a class="btn btn-light arrow" href="{mailto(MAIL,"DFO Studio – kennismaking")}">Neem contact op</a>')
    body += f"""<section><div class="wrap"><div class="sec-head"><h2>Wat we maken</h2></div><div class="grid g3">{cards}</div></div></section>
{secs}
<section><div class="wrap split"><div><h2>Zo werken we</h2><p class="muted">Van kleine online presentatie tot uitgebreide live-uitzending: maatwerk met persoonlijke begeleiding.</p></div><div class="steps">{steps}</div></div></section>
""" + callout("Klaar voor je volgende productie?", "Neem contact met ons op en ontdek de mogelijkheden van DFO Studio.",
              mailto(MAIL, "DFO Studio – kennismaking"))
    page("studio.html", "DFO Studio – webinar-, podcast- en videoproducties", "Webinar-, podcast- en videoproducties, studioverhuur, contentmarketing en e-learning voor de financiële sector.", body)


TEAM = [
    ("Jurjen Oosterbaan Martinius", "Algemeen directeur", "jurjen", "joosterbaan@dfobv.nl", "Al 36 jaar eigenaar van Bureau DFO en autoriteit op het gebied van de Wft. Veelgevraagd spreker en sparringpartner over ondernemerschap, strategie en efficiënte bedrijfsvoering."),
    ("Agaat van Ekeren", "Relatiemanager", "agaat", "avanekeren@dfobv.nl", "Verantwoordelijk voor klanttevredenheid en alle abonnementen, zoals het Wft-servicepakket en de nieuwsbrieven."),
    ("Robert-Jan van Loon", "Consultant compliance", "robert-jan", "rjvanloon@dfocompliance.nl", "Begeleidt Wft-vergunningaanvragen en beantwoordt Wft- en compliancevragen van klanten."),
    ("Tjeerd Erkens", "Onderzoeker", "tjeerd", "terkens@dfobv.nl", "Verantwoordelijk voor alle marktonderzoeken, zoals het jaarlijkse Serviceprovideronderzoek."),
    ("Ronald van Hamersveld", "Financial controller", "ronald", "rvanhamersveld@dfobv.nl", "Verzorgt de financiële administratie van het bureau, partners en de verenigingen waarvoor we het secretariaat voeren."),
    ("Nico den Besten", "Medewerker digitale innovatie", "nico", "ndenbesten@dfobv.nl", "Opmaak en verzending van digitale nieuwsbrieven, website, social media en ontwerp van logo’s en huisstijlen."),
    ("Ilona Vellekoop", "Bestuurssecretaresse", "ilona", "ivellekoop@dfobv.nl", "Secretaresse voor de NVHP."),
    ("Martine Verhagen", "Bestuurssecretaresse", "martine", "mverhagen@dfobv.nl", "Secretaresse voor een aantal secretariaten."),
    ("Sheila Boon", "Secretaresse", "sheila", "sboon@dfobv.nl", "Allround secretaresse op de afdeling managementsupport."),
    ("Trineke Kuijer", "Secretaresse", "trineke", "tkuijer@dfobv.nl", "Telefoon, ondersteuning van de afdelingen, verzending van webshopbestellingen en ontvangst van bezoekers."),
    ("Tanja Heerze", "Administratief medewerker", "tanja", "theerze@dfobv.nl", "Facturatie en debiteurenbeheer, en ondersteuning van het secretariaat."),
    ("Anja Heetmayer Knorth", "Administratief medewerker / gastvrouw", "anja", "aheetmayer@dfobv.nl", "Heet je welkom en zorgt dat je deelname aan onze bijeenkomsten prettig verloopt."),
    ("Tiny Floris", "Gastvrouw", "tiny", "gastvrouw@dfobv.nl", "Voor veel cursisten het gezicht van DFO; verzorgt de catering voor ruim 3.000 deelnemers per jaar."),
    ("Gea van Esveld", "Gastvrouw", "gea", "gastvrouw@dfobv.nl", "Heet je welkom en zorgt dat je deelname aan onze bijeenkomsten prettig verloopt."),
    ("Willie van Puurveen – van den Berg", "Gastvrouw", "willie", "gastvrouw@dfobv.nl", "Heet je welkom en zorgt dat je deelname aan onze bijeenkomsten prettig verloopt."),
    ("Gijs", "Huisvriend", "gijs", "", "Vaste bewoner van het pand in Hoevelaken."),
]


def build_over():
    team = "".join(f'''<div class="person"><div class="ph"><img src="assets/img/team/{img}.jpg" alt="{E(n)}" loading="lazy" width="240" height="240"></div>
<div class="body"><h3>{E(n)}</h3><div class="role">{E(r)}</div><p>{E(t)}</p>{f'<a href="mailto:{m}">{m}</a>' if m else ''}</div></div>''' for n, r, img, m, t in TEAM)
    body = hero("Over Bureau DFO", "Jouw partner waar het gaat om succesvol ondernemen in de financiële dienstverlening. Opgericht in 1992, gevestigd in Hoevelaken.",
                crumbs=["Over DFO"], img="assets/img/pand.jpg", small=False)
    body += f"""
<section><div class="wrap split">
  <div><h2>Maak kennis met Bureau DFO</h2>
  <p>Wij geloven dat goede financiële dienstverlening begint bij persoonlijke betrokkenheid. Vanuit ons kantoor in Hoevelaken zetten we ons iedere dag in om professionals en organisaties in de financiële sector verder te helpen. We volgen ontwikkelingen op de voet, delen onze kennis en denken mee over praktische oplossingen die écht het verschil maken.</p>
  <p>Wat ons kenmerkt? Een persoonlijke aanpak, korte lijnen en oprechte interesse in de mensen en organisaties met wie we samenwerken. Of het nu gaat om Wft-advies, onderzoek, kennisdeling of ondersteuning bij actuele vraagstukken: wij combineren deskundigheid met betrokkenheid.</p></div>
  <div class="grid" style="gap:14px">
    <div class="card"><h3>Financieel adviseurs</h3><p>De partner voor kennisontwikkeling en compliance, zodat je je kunt richten op je klanten.</p></div>
    <div class="card"><h3>Brancheorganisaties</h3><p>Voor verenigingen en stichtingen voeren wij het volledige secretariaat.</p></div>
    <div class="card"><h3>Aanbieders en verzekeraars</h3><p>Een betrouwbare partner voor inzicht en samenwerking, onder meer via ons onderzoek.</p></div>
  </div>
</div></section>

<section class="alt"><div class="wrap">
  <div class="sec-head"><h2>Bureau DFO ontzorgt op meerdere fronten</h2></div>
  <div class="grid g3">
    {svc_card("opleidingen.html","cap","Opleidingen","Praktijkgerichte kennis voor financieel adviseurs.")}
    {svc_card("secretariaten.html","users","Secretariaten","Ledenadministratie en bestuursondersteuning uit handen genomen.")}
    {svc_card("zalencentrum.html","room","Zalen","Vergader- en cursusruimtes inclusief ontvangst.")}
    {svc_card("studio.html","mic","Studio","Webinar-, podcast- en videoproducties.")}
    {svc_card("compliance.html","shield","Compliance","Grip op wet- en regelgeving, van Wft tot AVG.")}
    {svc_card("onderzoek.html","chart","Onderzoek","Onafhankelijk onderzoek voor de financiële adviesketen.")}
  </div>
</div></section>

<section id="team"><div class="wrap">
  <div class="sec-head"><h2>Ons team</h2><p>Alle medewerkers zijn bereikbaar via <a href="{TEL_HREF}">{TEL}</a>.</p></div>
  <div class="team">{team}</div>
</div></section>

<section class="alt" id="werken-bij"><div class="wrap split">
  <div><h2>Werken bij Bureau DFO</h2>
  <p>De beste resultaten ontstaan wanneer mensen met plezier samenwerken. Daarom zijn we altijd op zoek naar enthousiaste collega’s die willen meebouwen aan onze organisatie én aan de toekomst van onze relaties.</p>
  <p>Of je nu zeer ervaren bent of aan het begin van je carrière staat: bij Bureau DFO krijg je de ruimte om jezelf te ontwikkelen, initiatief te nemen en écht impact te maken. Staat jouw ideale functie er niet tussen? Mail gerust naar <a href="mailto:avanekeren@dfobv.nl">Agaat van Ekeren</a> — we maken graag vrijblijvend kennis.</p></div>
  <div class="grid" style="gap:14px">
    <a class="card" href="assets/pdf/vacature-secretaresse-bestuur.pdf"><span class="tag">Vacature</span><h3>Secretaresse | Bestuur</h3><span class="more arrow">Bekijk de vacature (pdf) </span></a>
    <a class="card" href="assets/pdf/vacature-secretaresse-allround.pdf"><span class="tag">Vacature</span><h3>Secretaresse | Allround</h3><span class="more arrow">Bekijk de vacature (pdf) </span></a>
  </div>
</div></section>
""" + callout("Benieuwd wat wij voor je kunnen betekenen?", "Bel 033 258 04 60 of mail info@dfobv.nl — we reageren binnen één werkdag.")
    page("over-dfo.html", "Over Bureau DFO – team en werken bij", "Bureau DFO in Hoevelaken: sinds 1992 partner van financieel adviseurs, brancheorganisaties en aanbieders. Maak kennis met ons team.", body)


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
    page("columns.html", "Columns Jurjen Oosterbaan Martinius – Bureau DFO", "Columns van Jurjen Oosterbaan Martinius, algemeen directeur van Bureau DFO, over de financiële adviesbranche.", body)


def build_congressen():
    body = hero("Congresorganisatie", "Een congres is meer dan een reeks presentaties: het is een platform voor kennisdeling, netwerken en het versterken van de gemeenschap binnen jullie vakgebied.",
                crumbs=["Congressen"], img="assets/img/congres.jpg", small=False,
                btns=f'<a class="btn btn-light arrow" href="{mailto(MAIL,"Congresorganisatie – mogelijkheden bespreken")}">Bespreek de mogelijkheden</a>')
    body += f"""
<section><div class="wrap split">
  <div><h2>Onze kracht in congresorganisatie</h2>
  <p>Al jaren organiseren we congressen voor onder meer de NVHP (Nederlandse Vereniging van Hypothecair Planners), de KPS (Kring van Pensioenspecialisten) en ons eigen VIPcongres voor de Contactgroep Automatisering.</p>
  <p>We kennen de financiële sector en spreken jullie taal. Met onze uitingen en nieuwsbrieven bereiken we de hele sector. Zo stemmen we de inhoud perfect af op het publiek. Van conceptfase tot evaluatie nemen wij de complete organisatie uit handen.</p></div>
  <div class="media"><img src="assets/img/vip.jpg" alt="VIPcongres 2024" loading="lazy" width="960" height="640"></div>
</div></section>
<section class="alt"><div class="wrap"><div class="sec-head"><h2>Wij zorgen voor</h2></div><div class="grid g4">
  <div class="card"><div class="icon">{icon('room')}</div><h3>Locatie en catering</h3><p>De ideale locatie die past bij de grootte en het karakter van jullie evenement.</p></div>
  <div class="card"><div class="icon">{icon('users')}</div><h3>Sprekers en programma</h3><p>Een aantrekkelijk programma met inspirerende sprekers uit de branche.</p></div>
  <div class="card"><div class="icon">{icon('mic')}</div><h3>Logistiek en techniek</h3><p>Registratie, audiovisuele ondersteuning en begeleiding van sprekers op de dag zelf.</p></div>
  <div class="card"><div class="icon">{icon('mail')}</div><h3>Communicatie en marketing</h3><p>Uitnodigingen en promotie voor een optimale opkomst.</p></div>
</div></div></section>
""" + callout("Benieuwd wat wij voor jullie organisatie kunnen betekenen?", "Neem contact op om de mogelijkheden te bespreken.",
              mailto(MAIL, "Congresorganisatie – mogelijkheden bespreken"), "Bespreek de mogelijkheden")
    page("congressen.html", "Congresorganisatie – Bureau DFO", "Bureau DFO organiseert congressen voor de financiële sector, zoals het VIPcongres en ledendagen van de NVHP en KPS.", body)


def build_secretariaten():
    body = hero("Secretariaatsvoering", "Voor verenigingen en stichtingen in de financiële sector voeren wij het volledige secretariaat: ledenadministratie en bestuursondersteuning uit handen genomen.",
                crumbs=["Secretariaten"])
    body += f"""
<section><div class="wrap split">
  <div><h2>Uw vereniging in vertrouwde handen</h2>
  <p>Onze bestuurssecretaresses werken dagelijks voor brancheorganisaties zoals de NVHP. Met kennis van de financiële sector, een eigen financial controller en faciliteiten als zalen, studio en congresorganisatie onder één dak, ontzorgen we besturen volledig.</p>
  <ul class="check"><li>Ledenadministratie</li><li>Bestuursondersteuning door ervaren bestuurssecretaresses</li><li>Financiële administratie door onze financial controller</li><li>Organisatie van ledendagen en congressen</li></ul></div>
  <div class="media"><img src="assets/img/boardroom.jpg" alt="Boardroom bij DFO" loading="lazy" width="960" height="478"></div>
</div></section>
""" + callout("Meer weten over secretariaatsvoering?", "Neem contact op met Jurjen Oosterbaan Martinius via Agaat van Ekeren.",
              mailto("avanekeren@dfobv.nl", "Secretariaatsvoering"), "Neem contact op")
    page("secretariaten.html", "Secretariaatsvoering voor brancheorganisaties – Bureau DFO", "Bureau DFO voert het volledige secretariaat voor verenigingen en stichtingen in de financiële sector.", body)


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


def build_calculator():
    body = hero("Calculator onderhoud- en nazorgabonnement", "Gratis rekentool voor een indicatie van kosten en opbrengsten van serviceabonnementen. Een ‘cadeautje’ van DFO.",
                crumbs=["Calculator"], btns='<a class="btn btn-light arrow" href="https://www2.dfobv.nl/abonnement-dashboard/" target="_blank" rel="noopener">Open de calculator</a>')
    body += """
<section><div class="wrap split">
  <div><h2>Waarom deze tool?</h2>
  <p>Onderhoud en nazorg zijn cruciaal om consumenten echte zekerheid te geven over hun financiële producten. Toch is een breed, goed werkend systeem van abonnementen nog niet van de grond gekomen. Bij een klassiek model (goud/zilver/brons) zeggen klanten die een tijd geen gebruik maken van de diensten, het abonnement ook weer makkelijk op.</p>
  <p>Wij vinden het belangrijk dat adviseurs blijven nadenken over hoe onderhoud en nazorg een financieel gezond onderdeel van hun bedrijfsvoering kunnen worden. Daarom hebben we deze praktische rekentool ontwikkeld.</p>
  <h3>De rekentool houdt rekening met</h3>
  <ul class="check"><li>de diensten die onder het abonnement vallen (maximaal 20)</li><li>de gemiddelde frequentie van gebruik per dienst</li><li>de salariskosten van junior- en seniormedewerkers</li><li>de gemiddelde tijdsbesteding per dienst</li><li>de kostenopslag van het kantoor</li><li>het gewenste rendement (winstpercentage)</li></ul>
  <p>Het resultaat zie je direct: het benodigde abonnementsbedrag én het tijdsbeslag (fte) per medewerker. Je kunt het printen of naar Excel exporteren.</p></div>
  <div><div class="media"><img src="assets/img/calculator.jpg" alt="Schermafbeelding calculator" loading="lazy" width="960" height="968"></div>
  <div class="note" style="margin-top:20px"><strong>Tips:</strong> pas algemene instellingen en handelingen aan, voeg handelingen toe met de groene knop of verwijder ze met de rode knop, en dupliceer een handeling voor verdere invulling. De tool werkt alleen op een groot scherm en opent in een apart tabblad. Alles draait in je browser: er worden geen gegevens opgeslagen.</div>
  <p class="muted" style="font-size:.88rem;margin-top:12px">Mede mogelijk gemaakt door Blinqx Verzekering &amp; Hypotheek.</p></div>
</div></section>
""" + callout("Open de calculator", "Speel ermee en zie in één oogopslag het benodigde abonnementsbedrag en het tijdsbeslag.",
              "https://www2.dfobv.nl/abonnement-dashboard/", "Naar de calculator")
    page("nazorg-calculator.html", "Calculator onderhoud- en nazorgabonnement – Bureau DFO", "Gratis rekentool: bereken het benodigde maandbedrag en de fte voor een onderhoud- en nazorgabonnement.", body)


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
    <h2 style="font-size:1.5rem">Stuur een bericht</h2>
    <p class="muted">Je e-mailprogramma opent met je bericht al ingevuld.</p>
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


if __name__ == "__main__":
    for fn in [build_home, build_opleidingen, build_documenten, build_compliance, build_abonnementen, build_zalen,
               build_studio, build_over, build_columns, build_congressen, build_secretariaten, build_onderzoek,
               build_calculator, build_contact, build_404]:
        fn()
    print("OK –", len(cursussen), "cursussen,", len(agenda), "data")
