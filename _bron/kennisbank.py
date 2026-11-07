"""Kennisbank: begrippenlijst per domein (schade, hypotheken, pensioenen, kredieten, inkomen).

Bron: _bron/kennisbank/<domein>.json  —  [{"term","afk","def","zie":[...],"volatiel":bool}]
"""
import json, re, html, unicodedata, datetime
from pathlib import Path

SRC = Path(__file__).resolve().parent / "kennisbank"
E = html.escape

DOMEINEN = [
    ("schade", "Schadeverzekeringen", "schade"),
    ("hypotheken", "Hypotheken", "hypotheken"),
    ("pensioenen", "Pensioenen", "leven"),
    ("kredieten", "Kredieten", "hypotheken"),
    ("inkomen", "Inkomensverzekeringen", "inkomen"),
    ("wetgeving", "Wet- en regelgeving", "compliance"),
]


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def load():
    items = []
    for key, naam, _ in DOMEINEN:
        f = SRC / f"{key}.json"
        if not f.exists():
            continue
        for it in json.loads(f.read_text()):
            it = dict(it)
            it["dom"], it["domnaam"] = key, naam
            it["id"] = f"{key}-{slug(it['term'])}"
            items.append(it)
    return items


def build_kennisbank(page, hero, callout, icon, cursussen=None, agenda=None):
    items = load()
    if not items:
        return 0
    byterm = {}
    for it in items:
        byterm.setdefault((it["dom"], it["term"].lower()), it)
        byterm.setdefault(("*", it["term"].lower()), it)
    counts = {k: sum(1 for i in items if i["dom"] == k) for k, _, _ in DOMEINEN}

    def zie_links(it):
        out = []
        for z in it.get("zie", []) or []:
            t = byterm.get((it["dom"], z.lower())) or byterm.get(("*", z.lower()))
            if t:
                out.append(f'<a href="#{t["id"]}" data-jump="{t["id"]}">{E(t["term"])}</a>')
        return " · ".join(out)

    items_sorted = sorted(items, key=lambda i: (slug(i["term"]), i["dom"]))
    letters = sorted({(slug(i["term"])[:1] or "#").upper() for i in items_sorted})
    cards, cur = [], None
    for it in items_sorted:
        L = (slug(it["term"])[:1] or "#").upper()
        if L != cur:
            cur = L
            cards.append(f'<h2 class="kb-letter" id="letter-{L}">{L}</h2>')
        afk = f' <span class="kb-afk">({E(it["afk"])})</span>' if it.get("afk") else ""
        vol = '<span class="tag alt" title="Bedragen of regels kunnen jaarlijks wijzigen">Kan jaarlijks wijzigen</span>' if it.get("volatiel") else ""
        zie = zie_links(it)
        cards.append(
            f'<article class="kb-item" id="{it["id"]}" data-d="{it["dom"]}" data-s="{E((it["term"] + " " + (it.get("afk") or "") + " " + it["def"]).lower())}">'
            f'<div class="kb-head"><h3>{E(it["term"])}{afk}</h3><span class="tag">{E(it["domnaam"])}</span>{vol}</div>'
            f'<p>{E(it["def"])}</p>'
            + (f'<p class="kb-zie"><a href="{E(it["link"])}"{" rel=noopener" if it["link"].startswith("http") else ""}>{"Bekijk het artikel" if it.get("bron") in ("Wft","BGfo","TRHK") else "Bekijk de wettekst"} →</a>{" · bron: " + E(it["bron"]) if it.get("bron") else ""}</p>' if it.get("link") else "")
            + (f'<p class="kb-zie"><strong>Zie ook:</strong> {zie}</p>' if zie else "")
            + "</article>")
    chips = f'<button class="chip" data-d="" aria-pressed="true">Alle ({len(items)})</button>' + "".join(
        f'<button class="chip" data-d="{k}" aria-pressed="false">{n} ({counts[k]})</button>' for k, n, _ in DOMEINEN if counts[k])
    az = "".join(f'<a href="#letter-{L}">{L}</a>' for L in letters)

    # opleidingen per domein (via related.py)
    opl = ""
    try:
        import related
        dfo, nv = related.dfo_items(cursussen or [], agenda or []), related.nvhp_items()
        blocks = []
        for k, n, topic in DOMEINEN:
            if not counts[k]:
                continue
            ptop = {topic: 8}
            ptok = related.tokens(n)
            if k == "kredieten":
                ptok |= {"krediet", "kredieten", "financieren", "zakelijk"}
            d = related.pick(dfo, ptop, ptok, 3, 6)
            nvh = related.pick(nv, ptop, ptok, 2, 6, nvhp=True) if k in ("hypotheken", "pensioenen") else []
            if d or nvh:
                blocks.append(f'<div class="kb-opl" data-d="{k}"><h3>{n}</h3><div class="grid" style="gap:12px">{"".join(related.card(x) for x in d + nvh)}</div></div>')
        if blocks:
            opl = (f'<section class="alt" id="opleidingen"><div class="wrap"><div class="sec-head"><span class="kicker" style="color:var(--blue)">Verdiep je kennis</span>'
                   f'<h2>Opleidingen per onderwerp</h2><p>Van begrip naar vakmanschap: trainingen van Bureau DFO en masterclasses van de NVHP (ook voor niet-leden).</p></div>'
                   f'<div class="grid g3" style="align-items:start">{"".join(blocks)}</div></div></section>')
    except Exception as ex:  # opleidingsblok is optioneel
        print("kennisbank opleidingen:", ex)

    vandaag = datetime.date.today()
    body = hero("Kennisbank", f"{len(items)} begrippen uit schadeverzekeringen, hypotheken, pensioenen, kredieten, inkomensverzekeringen en wet- en regelgeving, helder uitgelegd voor financieel adviseurs.",
                crumbs=["Kennisbank"],
                btns='<a class="btn btn-light arrow" href="#zoek">Zoek een begrip</a><a class="btn btn-ghost" href="#opleidingen">Opleidingen per onderwerp</a>')
    body += f"""
<section id="zoek"><div class="wrap kb">
  <div class="kb-tools">
    <div class="filters"><input type="search" id="kq" placeholder="Zoek een begrip of afkorting, bijv. NHG, WGA, eigen risico…" aria-label="Zoek begrip" autocomplete="off"></div>
    <div class="chips" id="kd" role="group" aria-label="Domein">{chips}</div>
    <nav class="kb-az" aria-label="Alfabet">{az}</nav>
    <div class="count" id="kc"></div>
  </div>
  <div id="kl">{''.join(cards)}</div>
  <div class="empty" id="ke" hidden><p><strong>Dit begrip staat nog niet in de kennisbank.</strong> Wil je dat we dit voor je maken?</p><a class="btn btn-primary arrow" id="kmail" href="mailto:info@dfobv.nl">Stuur een mail naar info@dfobv.nl</a><p class="muted" style="font-size:.82rem;margin:8px 0 0">Je mailprogramma opent met een concept dat je nog kunt aanvullen.</p></div>
  <div class="note" style="margin-top:30px"><strong>Let op:</strong> deze kennisbank is bedoeld als algemene uitleg en is geen advies. Wet- en regelgeving, fiscale grenzen en bedragen wijzigen regelmatig; begrippen met het label <em>Kan jaarlijks wijzigen</em> bevatten gegevens die per jaar kunnen verschillen. Peildatum: {vandaag.day}-{vandaag.month}-{vandaag.year}. Controleer actuele cijfers altijd bij de bron (Belastingdienst, AFM, UWV, NHG, BKR).</div>
</div></section>
{opl}
""" + callout("Begrip niet gevonden of een aanvulling?", "Laat het ons weten, dan nemen we het op in de kennisbank.",
              "mailto:info@dfobv.nl?subject=Kennisbank%20-%20aanvulling", "Mail een aanvulling")
    js = """<script>
const kq=document.getElementById('kq'),items=[...document.querySelectorAll('.kb-item')],letters=[...document.querySelectorAll('.kb-letter')];let kd='';
function f(){const t=kq.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);let n=0;
 items.forEach(a=>{const ok=(!kd||a.dataset.d===kd)&&t.every(w=>a.dataset.s.includes(w));a.hidden=!ok;if(ok)n++;});
 letters.forEach(h=>{let e=h.nextElementSibling,v=false;while(e&&!e.classList.contains('kb-letter')){if(!e.hidden)v=true;e=e.nextElementSibling;}h.hidden=!v;});
 document.querySelectorAll('.kb-opl').forEach(o=>o.hidden=!!kd&&o.dataset.d!==kd);
 document.getElementById('kc').textContent=n+(n===1?' begrip':' begrippen');document.getElementById('ke').hidden=n>0;
 if(!n){const t=kq.value.trim();document.getElementById('kmail').href='mailto:info@dfobv.nl?subject='+encodeURIComponent('Kennisbank: begrip toevoegen – '+t)+'&body='+encodeURIComponent('Beste Bureau DFO,\\n\\nIk zocht in de kennisbank naar: "'+t+'"\\nmaar dit begrip staat er nog niet in.\\n\\nKunnen jullie dit voor mij maken / toevoegen?\\n\\nToelichting:\\n\\n\\nMet vriendelijke groet,\\n\\nNaam:\\nKantoor:\\n');}}
document.querySelectorAll('#kd .chip').forEach(b=>b.onclick=()=>{kd=b.dataset.d;document.querySelectorAll('#kd .chip').forEach(x=>x.setAttribute('aria-pressed',x===b));history.replaceState(null,'',location.search+(kd?'#'+kd:''));f();});
kq.oninput=f;
document.addEventListener('click',e=>{const a=e.target.closest('a[data-jump]');if(!a)return;const el=document.getElementById(a.dataset.jump);if(el&&el.hidden){kq.value='';kd='';document.querySelectorAll('#kd .chip').forEach(x=>x.setAttribute('aria-pressed',x.dataset.d===''));f();}
 if(el){e.preventDefault();el.scrollIntoView({behavior:'smooth',block:'center'});el.classList.add('kb-hl');setTimeout(()=>el.classList.remove('kb-hl'),1800);history.replaceState(null,'','#'+el.id);}});
const p=new URLSearchParams(location.search).get('q');if(p){kq.value=p;}
const h=location.hash.slice(1);const dk=h?document.querySelector('#kd .chip[data-d="'+h+'"]'):null;if(dk)dk.click();
f();if(h&&document.getElementById(h)&&!dk){const el=document.getElementById(h);el.scrollIntoView({block:'center'});el.classList.add('kb-hl');}
</script>"""
    page("kennisbank.html", "Kennisbank begrippen – Bureau DFO",
         "Begrippenlijst schadeverzekeringen, hypotheken, pensioenen, kredieten en inkomensverzekeringen voor financieel adviseurs.", body, scripts=js)
    return len(items)
