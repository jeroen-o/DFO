"""Trainers, docenten en dagvoorzitters: overzicht (trainers.html) en een pagina per persoon (trainer-<slug>.html).

Bron: _bron/trainers.json  [{slug, naam, aliassen, functie, rollen, bio, foto, organisatie, bronnen}]
Opleidingen en data per persoon komen uit opleidingen.json (DFO) en nvhp.json (alleen Hoevelaken, net als elders op de site).
"""
import json, re, html, datetime
from pathlib import Path
from urllib.parse import quote

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
E = html.escape
MAAND = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
ROLVOLGORDE = ["Dagvoorzitter", "Spreker", "DFO-trainer", "NVHP-docent", "Compliance"]
MAIL = "info@dfobv.nl"


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"\b(trainer en opleider)\b", "", (s or "").lower())).strip()


def initialen(naam):
    w = [x for x in re.split(r"[\s-]+", naam) if x and x[0].isupper()]
    return (w[0][0] + (w[-1][0] if len(w) > 1 else "")).upper() if w else "?"


def foto(p, cls="tr-foto"):
    if p.get("foto") and (ROOT / p["foto"]).exists():
        return f'<img class="{cls}" src="{E(p["foto"])}" alt="{E(p["naam"])}" width="400" height="400" loading="lazy">'
    return f'<div class="{cls} tr-init" aria-hidden="true">{E(initialen(p["naam"]))}</div>'


def boekmail(p, dag=False, spreker=False):
    rol = "dagvoorzitter" if dag else ("spreker" if spreker else "trainer/docent")
    onderwerp = {"dagvoorzitter": "Dagvoorzitter inhuren: ", "spreker": "Spreker boeken: "}.get(rol, "Trainer boeken: ") + p["naam"]
    body = (f"Beste Bureau DFO,\n\nIk wil graag {p['naam']} boeken als {rol}.\n\n"
            "Datum / periode:\nLocatie:\nOnderwerp / doelgroep:\nAantal deelnemers:\n\nMet vriendelijke groet,\n\nNaam:\nOrganisatie:\nTelefoon:\n")
    return f"mailto:{MAIL}?subject={quote(onderwerp)}&body={quote(body)}"


def aansluiten(n_mensen, n_cursussen):
    """Sectie: aansluiten als trainer, docent of dagvoorzitter."""
    body = ("Beste Bureau DFO,\n\nIk wil graag aansluiten als trainer / docent / dagvoorzitter (doorhalen wat niet van toepassing is).\n\n"
            "Naam:\nOrganisatie:\nTelefoon:\nVakgebied(en):\nErvaring als trainer of dagvoorzitter:\nWebsite of LinkedIn:\n\n"
            "Een foto en korte biografie stuur ik als bijlage mee.\n\nMet vriendelijke groet,\n")
    href = f"mailto:{MAIL}?subject={quote('Aansluiten als trainer, docent of dagvoorzitter')}&body={quote(body)}"
    kaart = lambda t, items: f'<div class="card"><h3 style="font-size:1.05rem">{t}</h3><ul class="tr-voordelen">' + "".join(f"<li>{x}</li>" for x in items) + "</ul></div>"
    return f"""
<section class="alt" id="aansluiten"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Samenwerken</span><h2>Wil je ook aansluiten als trainer, docent of dagvoorzitter?</h2>
  <p>Bureau DFO werkt sinds 1992 voor en met financieel dienstverleners. We zoeken vakmensen die hun kennis en ervaring willen delen: in een training, een NVHP-masterclass, een webinar of als dagvoorzitter van een congres of bijeenkomst. Stuur een mail naar <a href="mailto:{MAIL}">{MAIL}</a>.</p></div>

  <h3 class="tr-h2" style="margin-top:6px">Waarom samenwerken met Bureau DFO interessant is</h3>
  <div class="grid g3" style="margin-bottom:26px">
    {kaart("Een vaste plek in de branche", ["Bureau DFO is al sinds 1992 actief in de financiële dienstverlening en kent de adviespraktijk van binnenuit.", f"Een breed opleidingsaanbod ({n_cursussen} opleidingen) in hypotheken, schade, inkomen, pensioen, compliance en bedrijfsvoering.", "Bureau DFO voert het secretariaat van de NVHP; veel NVHP-masterclasses vinden plaats in Hoevelaken."])}
    {kaart("Alles geregeld rond je training", ["Een eigen opleidingslocatie in Hoevelaken: het DFO Vergadercentrum, centraal in het land.", "Inschrijving en deelnemersadministratie via het DFO-opleidingsportaal.", "DFO Studio voor webinars, e-learning en video, zodat je kennis ook online een publiek vindt."])}
    {kaart("Zichtbaarheid bij je doelgroep", ["Een eigen profielpagina op deze site, gekoppeld aan je opleidingen en data.", "Promotie via de website, de agenda en de wekelijkse nieuwsbrief DFO Signalen.", "Bereik onder onafhankelijk financieel adviseurs, kantoren, serviceproviders en brancheorganisaties."])}
  </div>

  <h3 class="tr-h2">Wat de samenwerking alle partijen brengt</h3>
  <div class="grid g2 tr-partijen">
    {kaart("Voor jou als trainer, docent of dagvoorzitter", ["Je richt je op de inhoud en het geven van de training; de organisatie ligt bij Bureau DFO.", "Nieuwe opdrachten: ook incompany-trainingen, lezingen en dagvoorzitterschappen worden via Bureau DFO aangevraagd.", "Contact met collega-trainers en vakspecialisten, en signalen uit de markt voor nieuwe onderwerpen."])}
    {kaart("Voor adviseurs en kantoren", ["Actuele, praktijkgerichte kennis van mensen die het vak zelf uitoefenen.", "Opleidingen en masterclasses die aansluiten op wet- en regelgeving en permanente educatie.", "Eén vertrouwd adres voor opleidingen, modeldocumenten, compliance en kennis."])}
    {kaart("Voor opdrachtgevers van congressen en bijeenkomsten", ["Een dagvoorzitter of spreker die de financiële sector en haar taal kent.", "Bureau DFO denkt mee over programma, sprekers en organisatie, met ervaring in congresorganisatie.", "Eén aanspreekpunt voor de inhoud, de locatie en de techniek."])}
    {kaart("Voor Bureau DFO en de NVHP", ["Een breed en actueel aanbod met specialisten uit de praktijk.", "Kennis die in opleidingen, webinars, nieuwsbrieven en documenten terugkomt.", "Een netwerk dat de kwaliteit van het financieel advies in Nederland versterkt."])}
  </div>

  <div class="tr-boek" style="margin-top:26px"><h3 class="tr-h2" style="margin-top:0">Aansluiten? Stuur ons een mail</h3>
    <p>Vertel kort wie je bent, in welk vakgebied je traint of presenteert en welke ervaring je hebt. Stuur gerust een foto en een korte biografie mee. We nemen contact met je op voor een kennismaking.</p>
    <div class="btns"><a class="btn btn-primary arrow" href="{href}">Mail naar {MAIL}</a><a class="btn btn-ghost" href="tel:+31332580460">Bel 033 258 04 60</a></div></div>
</div></section>"""


def build(page, hero, callout, cursussen, agenda):
    f = SRC / "trainers.json"
    if not f.exists():
        return 0
    mensen = json.loads(f.read_text())
    nvhp = json.loads((SRC / "nvhp.json").read_text())
    opl = json.loads((SRC / "opleidingen.json").read_text())
    today = datetime.date.today().isoformat()

    for p in mensen:
        namen = {norm(p["naam"])} | {norm(a) for a in p.get("aliassen", [])}
        # DFO: data uit de agenda (docent per datum) → cursus
        dfo = {}
        for a in agenda:
            if norm(a.get("doc", "")) in namen:
                dfo.setdefault(a["u"], {"t": a["t"], "u": a["u"], "data": []})["data"].append(a)
        # NVHP: cursussen met een docent-datum; data alleen in Hoevelaken (bij Bureau DFO)
        nv = {}
        for d in nvhp["data"]:
            if norm(d.get("doc", "")) in namen:
                c = next((c for c in nvhp["cursussen"] if c["t"].lower()[:25] == d["t"].lower()[:25]), None)
                if not c:
                    continue
                x = nv.setdefault(c["u"], {"t": c["t"], "u": c["u"], "prijs": c["prijs"], "data": []})
                if d["d"] >= today and "hoevelaken" in d["loc"].lower():
                    x["data"].append(d)
        p["_dfo"], p["_nvhp"] = list(dfo.values()), list(nv.values())
        rollen = set(p.get("rollen", []))
        if p["_dfo"]:
            rollen.add("DFO-trainer")
        if p["_nvhp"]:
            rollen.add("NVHP-docent")
        p["rollen"] = [r for r in ROLVOLGORDE if r in rollen] + sorted(rollen - set(ROLVOLGORDE))

    def tags(p):
        return "".join(f'<span class="tag{" alt" if r in ("Dagvoorzitter", "Spreker") else ""}">{E(r)}</span>' for r in p["rollen"])

    def kaart(p):
        fn = f'<p class="tr-fn">{E(p["functie"])}</p>' if p.get("functie") else ""
        return (f'<a class="card tr-card" href="trainer-{p["slug"]}.html" data-r="{E(" ".join(p["rollen"]))}">{foto(p)}'
                f'<h3>{E(p["naam"])}</h3>{fn}'
                f'<div class="tr-tags">{tags(p)}</div><span class="more arrow">Bekijk profiel </span></a>')

    # --- subpagina's
    for p in mensen:
        dag = "Dagvoorzitter" in p["rollen"]
        spreker = "Spreker" in p["rollen"] and not dag

        def lijst(items, nvhp_=False):
            out = ""
            for c in items:
                ds = sorted((x for x in c["data"] if (x.get("d") or "") >= today), key=lambda x: x["d"])[:4]
                dt = " · ".join(f'{int(x["d"][8:])} {MAAND[int(x["d"][5:7]) - 1]} {x["d"][:4]}' + (f' ({E(x["loc"])})' if x.get("loc") else "") for x in ds)
                out += (f'<li><a href="{E(c["u"])}" rel="noopener">{E(c["t"])}</a>'
                        f'<br><span class="muted">{("Eerstvolgende: " + dt) if dt else "Data en locaties: zie het opleidingsportaal"}</span></li>')
            return f'<ul class="wb-list">{out}</ul>'
        aanbod = ""
        if p["_dfo"]:
            aanbod += f'<h2 class="tr-h2">Opleidingen bij Bureau DFO</h2>{lijst(p["_dfo"])}'
        if p["_nvhp"]:
            aanbod += (f'<h2 class="tr-h2">NVHP-masterclasses in Hoevelaken</h2><p class="muted" style="font-size:.9rem">Ook toegankelijk voor adviseurs die geen NVHP-lid zijn.</p>'
                       f'{lijst(p["_nvhp"], True)}')
        org = f'<p class="tr-org">{E(p["organisatie"])}</p>' if p.get("organisatie") else ""
        if p.get("links"):
            org += '<p class="tr-org">' + "<br>".join(f'<a href="{E(u)}" rel="noopener">{E(t)}</a>' for t, u in p["links"]) + "</p>"
        bio = "".join(f"<p>{E(x)}</p>" for x in re.split(r"\n{2,}", p.get("bio") or "") if x.strip()) or \
            f'<p class="muted">Meer weten over {E(p["naam"])}? Neem contact op met Bureau DFO.</p>'
        kwal = ""
        if p.get("historie"):
            kwal += f'<h2 class="tr-h2">Loopbaan</h2><ul class="tr-hist">' + "".join(f"<li>{E(h)}</li>" for h in p["historie"]) + "</ul>"
        if p.get("kwaliteiten"):
            kwal += f'<h2 class="tr-h2">Kwaliteiten van {E(p["naam"].split()[0])}</h2><ul class="tr-kwal">' + "".join(f"<li>{E(k)}</li>" for k in p["kwaliteiten"]) + "</ul>"
        if p.get("waarom"):
            kwal += f'<h2 class="tr-h2">Waarom {E(p["naam"])} boeken?</h2><p>{E(p["waarom"])}</p>'
        knop = (f'<a class="btn btn-primary arrow" href="{boekmail(p, dag, spreker)}">{"Boek als dagvoorzitter" if dag else ("Boek als spreker" if spreker else "Boek deze trainer")}</a>'
                + (f'<a class="btn btn-ghost" href="{boekmail(p)}">Boek als trainer</a>' if (dag or spreker) and (p["_dfo"] or p["_nvhp"] or "DFO-trainer" in p["rollen"]) else ""))
        body = hero(E(p["naam"]), E(p.get("functie") or ", ".join(p["rollen"])), crumbs=['<a href="trainers.html">Trainers en docenten</a>', E(p["naam"])])
        body += f"""
<section><div class="wrap tr-profiel">
  <div class="tr-side">{foto(p, "tr-foto tr-groot")}<div class="tr-tags">{tags(p)}</div>{org}</div>
  <div class="tr-main">
    {bio}
    {kwal}
    {aanbod}
    <div class="tr-boek"><h2 class="tr-h2">Wil je {E(p["naam"])} boeken?</h2>
      <p>Neem contact op met Bureau DFO via <a href="mailto:{MAIL}">{MAIL}</a> of bel 033 258 04 60. Je mailprogramma opent met een concept dat je nog kunt aanvullen.</p>
      <div class="btns">{knop}</div></div>
  </div>
</div></section>
""" + callout("Alle trainers en docenten", "Bekijk met welke trainers, docenten en dagvoorzitters Bureau DFO samenwerkt.", "trainers.html", "Naar het overzicht")
        desc = f"{p['naam']}: {(p.get('functie') or ', '.join(p['rollen']))}. " + (re.sub(r'\s+', ' ', p.get('bio') or '')[:110])
        page(f"trainer-{p['slug']}.html", f"{p['naam']} – trainer en docent – Bureau DFO", desc.strip()[:158], body)

    # --- overzicht: eerst de trainers en docenten, daarna de dagvoorzitters en sprekers
    TR = ("DFO-trainer", "NVHP-docent", "Compliance")
    trainers = [p for p in mensen if set(TR) & set(p["rollen"])]
    dagv = [p for p in mensen if "Dagvoorzitter" in p["rollen"] or "Spreker" in p["rollen"]]
    dagv.sort(key=lambda p: ("Dagvoorzitter" not in p["rollen"], p["naam"].split()[-1].lower()))
    cnt = {r: sum(1 for p in trainers if r in p["rollen"]) for r in TR}
    chips = f'<button class="chip" data-r="" aria-pressed="true">Alle trainers ({len(trainers)})</button>' + "".join(
        f'<button class="chip" data-r="{r}" aria-pressed="false">{ {"DFO-trainer": "DFO-trainers", "NVHP-docent": "NVHP-docenten", "Compliance": "Compliance"}[r] } ({cnt[r]})</button>'
        for r in TR if cnt[r])
    body = hero("Trainers, docenten en dagvoorzitters",
                "Met deze trainers en docenten werkt Bureau DFO samen: de trainers van DFO Opleidingen en DFO Compliance en de docenten van de NVHP-masterclasses. Daaronder vind je de dagvoorzitters en sprekers voor je congres of bijeenkomst. Boeken gaat via Bureau DFO.",
                crumbs=['<a href="opleidingen.html">Opleidingen</a>', "Trainers en docenten"],
                btns=f'<a class="btn btn-light arrow" href="#alle">Alle trainers</a><a class="btn btn-ghost" href="#dagvoorzitters">Dagvoorzitters en sprekers</a><a class="btn btn-ghost" href="#aansluiten">Zelf aansluiten</a>')
    body += f"""
<section id="alle"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">{len(trainers)} trainers en docenten</span><h2>Met wie wij samenwerken</h2></div>
  <div class="chips" id="trc" role="group" aria-label="Filter">{chips}</div>
  <div class="grid tr-grid" id="trl">{"".join(kaart(p) for p in trainers)}</div>
  <div class="note" style="margin-top:26px"><strong>Wil je een trainer boeken?</strong> Voor een incompany-training of workshop: neem contact op met <a href="mailto:{MAIL}?subject={quote('Trainer boeken')}">{MAIL}</a> of bel 033 258 04 60.</div>
</div></section>"""
    if dagv:
        body += f"""
<section class="alt" id="dagvoorzitters"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Te boeken</span><h2>Dagvoorzitters en sprekers inhuren</h2>
  <p>Een ervaren dagvoorzitter of spreker die de financiële sector kent, maakt je congres, seminar of netwerkbijeenkomst inhoudelijk sterk en levendig. Deze dagvoorzitters en sprekers kun je via Bureau DFO inhuren.</p></div>
  <div class="grid tr-grid">{"".join(kaart(p) for p in dagv)}</div>
  <div class="btns"><a class="btn btn-primary arrow" href="mailto:{MAIL}?subject={quote('Dagvoorzitter of spreker inhuren')}">Vraag een dagvoorzitter of spreker aan</a><a class="btn btn-ghost" href="congressen.html">Congresorganisatie</a></div>
</div></section>"""
    body += aansluiten(len(mensen), len(cursussen)) + callout("Liever direct een opleiding volgen?", "Bekijk het actuele aanbod van Bureau DFO en de NVHP-masterclasses in Hoevelaken.", "opleidingen.html", "Naar de opleidingen")
    js = """<script>
document.querySelectorAll('#trc .chip').forEach(b=>b.onclick=()=>{const r=b.dataset.r;document.querySelectorAll('#trc .chip').forEach(x=>x.setAttribute('aria-pressed',x===b));
document.querySelectorAll('#trl .tr-card').forEach(c=>c.hidden=!!r&&!c.dataset.r.split(' ').includes(r));});
</script>"""
    page("trainers.html", "Trainers, docenten en dagvoorzitters – Bureau DFO",
         f"Met deze {len(mensen)} trainers, docenten en dagvoorzitters werkt Bureau DFO samen: DFO Opleidingen, DFO Compliance en NVHP-masterclasses. Boek een trainer via info@dfobv.nl.", body, scripts=js)
    congres_blokken(mensen, kaart)
    return len(mensen)


def congres_blokken(mensen, kaart):
    """Op congressen.html: eerst de trainers, dan de dagvoorzitters en sprekers (vervangt de plaatshouder)."""
    f = ROOT / "congressen.html"
    raw = f.read_text()
    if "<!--congres-mensen-->" not in raw:
        return
    trainers = [p for p in mensen if {"DFO-trainer", "NVHP-docent", "Compliance"} & set(p["rollen"])]
    dagsp = [p for p in mensen if {"Dagvoorzitter", "Spreker"} & set(p["rollen"])]
    dagsp.sort(key=lambda p: ("Dagvoorzitter" not in p["rollen"], p["naam"].split()[-1].lower()))
    html_ = f"""<section id="trainers"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Trainers</span><h2>Trainers en docenten voor je congres of bijeenkomst</h2>
  <p>Voor een inhoudelijke sessie, workshop of masterclass op je congres: deze {len(trainers)} trainers en docenten van DFO Opleidingen, DFO Compliance en de NVHP zijn via Bureau DFO te boeken.</p></div>
  <div class="grid tr-grid">{"".join(kaart(p) for p in trainers)}</div>
  <div class="btns"><a class="btn btn-ghost arrow" href="trainers.html">Alle trainers en profielen</a></div>
</div></section>
<section class="alt" id="dagvoorzitters"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Dagvoorzitters en sprekers</span><h2>Dagvoorzitters en sprekers inhuren</h2>
  <p>Een dagvoorzitter of spreker die de financiële sector en haar taal kent, maakt het verschil. Wil je iemand boeken? Neem contact op met <a href="mailto:{MAIL}">{MAIL}</a>.</p></div>
  <div class="grid tr-grid">{"".join(kaart(p) for p in dagsp)}</div>
  <div class="btns"><a class="btn btn-primary arrow" href="mailto:{MAIL}?subject={quote('Dagvoorzitter of spreker inhuren')}">Vraag een dagvoorzitter of spreker aan</a></div>
</div></section>"""
    f.write_text(raw.replace("<!--congres-mensen-->", html_, 1))
