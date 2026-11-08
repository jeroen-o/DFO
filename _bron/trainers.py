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
ROLVOLGORDE = ["Dagvoorzitter", "DFO-trainer", "NVHP-docent", "Compliance"]
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


def boekmail(p, dag=False):
    onderwerp = ("Dagvoorzitter inhuren: " if dag else "Trainer boeken: ") + p["naam"]
    body = (f"Beste Bureau DFO,\n\nIk wil graag {p['naam']} boeken als {'dagvoorzitter' if dag else 'trainer/docent'}.\n\n"
            "Datum / periode:\nLocatie:\nOnderwerp / doelgroep:\nAantal deelnemers:\n\nMet vriendelijke groet,\n\nNaam:\nOrganisatie:\nTelefoon:\n")
    return f"mailto:{MAIL}?subject={quote(onderwerp)}&body={quote(body)}"


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
        return "".join(f'<span class="tag{" alt" if r == "Dagvoorzitter" else ""}">{E(r)}</span>' for r in p["rollen"])

    def kaart(p):
        fn = f'<p class="tr-fn">{E(p["functie"])}</p>' if p.get("functie") else ""
        return (f'<a class="card tr-card" href="trainer-{p["slug"]}.html" data-r="{E(" ".join(p["rollen"]))}">{foto(p)}'
                f'<h3>{E(p["naam"])}</h3>{fn}'
                f'<div class="tr-tags">{tags(p)}</div><span class="more arrow">Bekijk profiel </span></a>')

    # --- subpagina's
    for p in mensen:
        dag = "Dagvoorzitter" in p["rollen"]

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
        bio = "".join(f"<p>{E(x)}</p>" for x in re.split(r"\n{2,}", p.get("bio") or "") if x.strip()) or \
            f'<p class="muted">Meer weten over {E(p["naam"])}? Neem contact op met Bureau DFO.</p>'
        knop = (f'<a class="btn btn-primary arrow" href="{boekmail(p, dag)}">{"Boek als dagvoorzitter" if dag else "Boek deze trainer"}</a>'
                + (f'<a class="btn btn-ghost" href="{boekmail(p)}">Boek als trainer</a>' if dag and (p["_dfo"] or p["_nvhp"] or "DFO-trainer" in p["rollen"]) else ""))
        body = hero(E(p["naam"]), E(p.get("functie") or ", ".join(p["rollen"])), crumbs=['<a href="trainers.html">Trainers en docenten</a>', E(p["naam"])])
        body += f"""
<section><div class="wrap tr-profiel">
  <div class="tr-side">{foto(p, "tr-foto tr-groot")}<div class="tr-tags">{tags(p)}</div>{org}</div>
  <div class="tr-main">
    {bio}
    {aanbod}
    <div class="tr-boek"><h2 class="tr-h2">Wil je {E(p["naam"])} boeken?</h2>
      <p>Neem contact op met Bureau DFO via <a href="mailto:{MAIL}">{MAIL}</a> of bel 033 258 04 60. Je mailprogramma opent met een concept dat je nog kunt aanvullen.</p>
      <div class="btns">{knop}</div></div>
  </div>
</div></section>
""" + callout("Alle trainers en docenten", "Bekijk met welke trainers, docenten en dagvoorzitters Bureau DFO samenwerkt.", "trainers.html", "Naar het overzicht")
        desc = f"{p['naam']}: {(p.get('functie') or ', '.join(p['rollen']))}. " + (re.sub(r'\s+', ' ', p.get('bio') or '')[:110])
        page(f"trainer-{p['slug']}.html", f"{p['naam']} – trainer en docent – Bureau DFO", desc.strip()[:158], body)

    # --- overzicht
    dagv = [p for p in mensen if "Dagvoorzitter" in p["rollen"]]
    cnt = {r: sum(1 for p in mensen if r in p["rollen"]) for r in ROLVOLGORDE}
    chips = f'<button class="chip" data-r="" aria-pressed="true">Iedereen ({len(mensen)})</button>' + "".join(
        f'<button class="chip" data-r="{r}" aria-pressed="false">{ {"DFO-trainer": "DFO-trainers", "NVHP-docent": "NVHP-docenten", "Compliance": "Compliance", "Dagvoorzitter": "Dagvoorzitters"}[r] } ({cnt[r]})</button>'
        for r in ROLVOLGORDE if cnt[r])
    body = hero("Trainers, docenten en dagvoorzitters",
                "Met deze trainers en docenten werkt Bureau DFO samen: de trainers van DFO Opleidingen en DFO Compliance en de docenten van de NVHP-masterclasses. Ook voor je eigen bijeenkomst of congres boek je ze via Bureau DFO.",
                crumbs=['<a href="opleidingen.html">Opleidingen</a>', "Trainers en docenten"],
                btns=f'<a class="btn btn-light arrow" href="#dagvoorzitters">Dagvoorzitter inhuren</a><a class="btn btn-ghost" href="#alle">Alle trainers</a>')
    if dagv:
        body += f"""
<section class="alt" id="dagvoorzitters"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Te boeken</span><h2>Dagvoorzitter inhuren</h2>
  <p>Een ervaren dagvoorzitter die de financiële sector kent, houdt je congres, seminar of netwerkbijeenkomst strak en levendig. Deze dagvoorzitters kun je via Bureau DFO inhuren.</p></div>
  <div class="grid tr-grid">{"".join(kaart(p) for p in dagv)}</div>
  <div class="btns"><a class="btn btn-primary arrow" href="mailto:{MAIL}?subject={quote('Dagvoorzitter inhuren')}">Vraag een dagvoorzitter aan</a><a class="btn btn-ghost" href="congressen.html">Congresorganisatie</a></div>
</div></section>"""
    body += f"""
<section id="alle"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">{len(mensen)} trainers en docenten</span><h2>Met wie wij samenwerken</h2></div>
  <div class="chips" id="trc" role="group" aria-label="Filter">{chips}</div>
  <div class="grid tr-grid" id="trl">{"".join(kaart(p) for p in mensen)}</div>
  <div class="note" style="margin-top:26px"><strong>Wil je een trainer boeken?</strong> Voor een incompany-training, een lezing of een dagvoorzitterschap: neem contact op met <a href="mailto:{MAIL}?subject={quote('Trainer boeken')}">{MAIL}</a> of bel 033 258 04 60.</div>
</div></section>
""" + callout("Liever direct een opleiding volgen?", "Bekijk het actuele aanbod van Bureau DFO en de NVHP-masterclasses in Hoevelaken.", "opleidingen.html", "Naar de opleidingen")
    js = """<script>
document.querySelectorAll('#trc .chip').forEach(b=>b.onclick=()=>{const r=b.dataset.r;document.querySelectorAll('#trc .chip').forEach(x=>x.setAttribute('aria-pressed',x===b));
document.querySelectorAll('#trl .tr-card').forEach(c=>c.hidden=!!r&&!c.dataset.r.split(' ').includes(r));});
</script>"""
    page("trainers.html", "Trainers, docenten en dagvoorzitters – Bureau DFO",
         f"Met deze {len(mensen)} trainers, docenten en dagvoorzitters werkt Bureau DFO samen: DFO Opleidingen, DFO Compliance en NVHP-masterclasses. Boek een trainer via info@dfobv.nl.", body, scripts=js)
    return len(mensen)
