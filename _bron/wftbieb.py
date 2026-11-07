"""WFT Bieb (jeroen-o.github.io/dfo-wft-bieb) geïntegreerd in de DFO-site.

Bron: _bron/wftbieb/bieb.json (WETTEN, THEMAS, FLAGLABEL, KENNIS), secties.json (actueel, toezicht, rekenen, faq)
en vragen.json (kennistoets). Bouwt:
  - wft-bieb.html     : overzicht wet- en regelgeving per thema, praktijkthema's, toezicht, rekenhulpen, FAQ
  - kennistoets.html  : Wft-kennistoets (7 vragen per ronde)
  - kennisbank/wetten.json en kennisbank/praktijk.json : begrippen voor de kennisbank
"""
import json, re, html
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
D = SRC / "wftbieb"
E = html.escape

# wetten die ook als volledige tekst op deze site staan
LOKAAL = {"BWBR0020368": "wft.html", "BWBR0020421": "bgfo.html", "BWBR0032503": "trhk.html"}


def load():
    b = json.loads((D / "bieb.json").read_text())
    return b, json.loads((D / "secties.json").read_text()), json.loads((D / "vragen.json").read_text())


def wet_url(w):
    if w.get("url"):
        return w["url"]
    if w.get("b"):
        return f"https://wetten.overheid.nl/{w['b']}"
    return ""


def local(u):
    """Links naar dfobv.nl omzetten naar pagina's op deze site waar mogelijk."""
    m = re.match(r"https?://(?:www\.)?dfobv\.nl/product/([^/]+)/?", u)
    if m and (ROOT / f"product-{m.group(1)}.html").exists():
        return f"product-{m.group(1)}.html"
    if "www2.dfobv.nl/documenten-contracten" in u:
        return "documenten.html"
    if re.match(r"https?://(?:www\.)?dfobv\.nl/agenda", u):
        return "opleidingen.html"
    return u


def ext(u):
    return ' rel="noopener"' if u.startswith("http") else ""


def kennisbank_json(b):
    themas = b["THEMAS"]
    wetten = []
    for w in b["WETTEN"]:
        u = wet_url(w)
        wetten.append({"term": w["t"], "afk": w.get("a") or "", "def": w["d"] + f" Thema: {themas.get(w['c'], w['c'])}.",
                       "volatiel": w.get("flag") == "jaarlijks", "link": LOKAAL.get(w.get("b"), u),
                       "bron": "wetten.overheid.nl" if "wetten.overheid" in u else ("EUR-Lex" if "eur-lex" in u else "")})
    praktijk = []
    for k in b["KENNIS"]:
        if k.get("bron") == "dfo":
            continue
        for it in k["items"]:
            praktijk.append({"term": it["t"], "afk": "", "def": it["d"] + f" ({it.get('g', '')})",
                             "link": LOKAAL.get(it["u"].rsplit("/", 1)[-1], it["u"]), "bron": ""})
    (SRC / "kennisbank" / "wetten.json").write_text(json.dumps(wetten, ensure_ascii=False, indent=1))
    (SRC / "kennisbank" / "praktijk.json").write_text(json.dumps(praktijk, ensure_ascii=False, indent=1))
    return len(wetten), len(praktijk)


def build(page, hero, callout):
    b, sec, vragen = load()
    nw, npk = kennisbank_json(b)
    themas, flags = b["THEMAS"], b["FLAGLABEL"]
    cnt = {k: sum(1 for w in b["WETTEN"] if w["c"] == k) for k in themas}

    # --- wet- en regelgeving
    cards = ""
    for w in sorted(b["WETTEN"], key=lambda w: list(themas).index(w["c"])):  # stabiel: volgorde van de bieb binnen een thema
        u = wet_url(w)
        href = LOKAAL.get(w.get("b"), u)
        fl = f'<span class="tag alt">{E(flags[w["flag"]])}</span>' if w.get("flag") else ""
        loc = ' <span class="muted" style="font-size:.8rem">(volledige tekst op deze site)</span>' if w.get("b") in LOKAAL else ""
        links = (f'<a class="more arrow" href="{E(href)}"{ext(href)}>{"Lees de wettekst" if "wetten.overheid" in href or href in LOKAAL.values() else ("Bekijk bij EUR-Lex" if "eur-lex" in href else "Naar de bron")} </a>{loc}' if href else '<span class="muted" style="font-size:.85rem">Directe link volgt</span>')
        if w.get("extra"):
            links += f' · <a href="{E(w["extra"]["href"])}" rel="noopener">{E(w["extra"]["label"])}</a>'
        zoek = " ".join([w["t"], w.get("a", ""), w["d"], themas.get(w["c"], "")]).lower()
        cards += (f'<article class="wb-card" data-c="{w["c"]}" data-f="{w.get("flag", "")}" data-s="{E(zoek)}">'
                  f'<div class="wb-meta"><span class="tag">{E(themas[w["c"]])}</span>{fl}</div>'
                  f'<h3>{E(w["t"])}{f" <span class=kb-afk>({E(w[chr(97)])})</span>" if w.get("a") else ""}</h3>'
                  f'<p>{E(w["d"])}</p><p class="wb-links">{links}</p></article>')
    chips = f'<button class="chip" data-c="" aria-pressed="true">Alle thema\'s ({len(b["WETTEN"])})</button>' + "".join(
        f'<button class="chip" data-c="{k}" aria-pressed="false">{E(n)} ({cnt[k]})</button>' for k, n in themas.items() if cnt[k])

    # --- wat verandert er
    act = "".join(f'<li><strong>{E(a["k"])}.</strong> {E(a["t"])}</li>' for a in sec["actueel"])

    # --- praktijkthema's (gegroepeerd)
    pk = [k for k in b["KENNIS"] if k.get("bron") != "dfo"][0]
    groepen = {}
    for it in pk["items"]:
        groepen.setdefault(it.get("g", "Overig"), []).append(it)
    prak = "".join(
        f'<div class="wb-groep"><h3>{E(g)}</h3>' + "".join(
            f'<details class="wb-det"><summary>{E(it["t"])}</summary><p>{E(it["d"])}</p>'
            f'<p><a class="more arrow" href="{E(LOKAAL.get(it["u"].rsplit("/", 1)[-1], it["u"]))}"{ext(it["u"])}>Bekijk de onderliggende regel </a></p></details>'
            for it in items) + "</div>" for g, items in groepen.items())

    # --- kennis en praktijk Bureau DFO
    dfo = [k for k in b["KENNIS"] if k.get("bron") == "dfo"][0]
    dg = {}
    for it in dfo["items"]:
        dg.setdefault(it.get("g", "Overig"), []).append(it)
    dfoh = "".join(
        f'<div class="wb-groep"><h3>{E(g)}</h3><ul class="wb-list">' + "".join(
            f'<li><a href="{E(local(it["u"]))}"{ext(local(it["u"]))}>{E(it["t"])}</a><br><span class="muted">{E(it["d"])}</span></li>' for it in items)
        + "</ul></div>" for g, items in dg.items())

    def blok(items):
        return "".join(
            f'<div class="card"><h3 style="font-size:1.02rem">{E(x["h"])}</h3>' + "".join(f"<p>{E(p)}</p>" for p in x["p"])
            + '<div style="margin-top:auto">' + " · ".join(f'<a class="more arrow" href="{E(local(u))}"{ext(local(u))}>{E(t)} </a>' for t, u in x["links"]) + "</div></div>"
            for x in items)

    faq = "".join(f'<details class="wb-det"><summary>{E(f["q"])}</summary><p>{E(f["a"])}</p></details>' for f in sec["faq"])

    body = hero("WFT Bieb", "Alle wet- en regelgeving voor de financiële dienstverlening op één plek: van Wft en Wwft tot fiscaal, pensioen en sociale zekerheid. Zoek op naam, afkorting of thema.",
                crumbs=['<a href="kennisbank.html">Kennisbank</a>', "WFT Bieb"],
                btns='<a class="btn btn-light arrow" href="#regelgeving">Naar de regelgeving</a><a class="btn btn-ghost" href="kennistoets.html">Doe de kennistoets</a>')
    body += f"""
<section class="tight"><div class="wrap">
  <div class="wb-nav"><a href="#actueel">Wat verandert er</a><a href="#regelgeving">Wet- en regelgeving</a><a href="#praktijk">Praktijkthema's</a><a href="#dfo-kennis">Modeldocumenten &amp; kennis</a><a href="#toezicht">Toezicht</a><a href="#rekenen">Rekenen</a><a href="#faq">Veelgestelde vragen</a><a href="kennistoets.html">Kennistoets</a></div>
  <p class="muted" style="font-size:.88rem;margin:10px 0 0">Peildatum: {E(sec["peildatum"])}. Nationale regelingen verwijzen naar wetten.overheid.nl (altijd de geldende tekst), Europese regels naar EUR-Lex. De Wft, het BGfo en de TRHK staan ook volledig op <a href="wetgeving.html">deze site</a>.</p>
</div></section>
<section class="alt" id="actueel"><div class="wrap" style="max-width:980px">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Actueel</span><h2>Wat er dit jaar verandert</h2></div>
  <ul class="wb-act">{act}</ul>
  <p style="margin-top:14px"><a class="more arrow" href="nieuws.html#kredieten">Volg het actuele nieuws </a></p>
</div></section>
<section id="regelgeving"><div class="wrap kb">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">{len(b["WETTEN"])} wetten en regelingen</span><h2>Wet- en regelgeving per thema</h2></div>
  <div class="kb-tools">
    <div class="filters"><input type="search" id="wq" placeholder="Zoek op naam, afkorting of onderwerp, bijv. Wwft, box 3, AOW…" aria-label="Zoek in de regelgeving" autocomplete="off"></div>
    <div class="chips" id="wc" role="group" aria-label="Thema">{chips}</div>
    <div class="chips" id="wf" role="group" aria-label="Aandachtspunten"><button class="chip" data-f="" aria-pressed="true">Alles</button><button class="chip" data-f="jaarlijks" aria-pressed="false">Wijzigt per 1 januari</button><button class="chip" data-f="nieuw" aria-pressed="false">Nieuw of op komst</button></div>
    <div class="count" id="wn"></div>
  </div>
  <div class="wb-grid" id="wl">{cards}</div>
  <div class="empty" id="we" hidden><p><strong>Niets gevonden.</strong> Mist u een regeling? <a href="mailto:info@dfobv.nl?subject=WFT%20Bieb%3A%20aanvulling">Laat het ons weten</a>.</p></div>
</div></section>
<section class="alt" id="praktijk"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Praktijkthema's Wft</span><h2>Korte toelichtingen voor de advies- en compliancepraktijk</h2><p>{E(pk.get("intro", ""))} <a href="{E(pk["meer"]["href"])}" rel="noopener">{E(pk["meer"]["label"])}</a></p></div>
  <div class="wb-cols">{prak}</div>
</div></section>
<section id="dfo-kennis"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Bureau DFO</span><h2>Modeldocumenten en kennis</h2><p>{E(dfo.get("intro", ""))} Een deel van de DFO-inhoud is alleen toegankelijk met een abonnement.</p></div>
  <div class="wb-cols">{dfoh}</div>
</div></section>
<section class="alt" id="toezicht"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Toezicht, geschillen en signalen</span><h2>Hoe een norm in de praktijk uitpakt</h2><p>Naast de wettekst zelf bepalen toezichthouder en geschilleninstantie hoe een norm in de praktijk uitpakt.</p></div>
  <div class="grid g3">{blok(sec["toezicht"])}</div>
</div></section>
<section id="rekenen"><div class="wrap">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Rekenen en opzoeken</span><h2>Hulpmiddelen voor het adviesgesprek</h2></div>
  <div class="grid g3">{blok(sec["rekenen"])}</div>
</div></section>
<section class="alt" id="faq"><div class="wrap" style="max-width:980px">
  <div class="sec-head"><span class="kicker" style="color:var(--blue)">Veelgestelde vragen</span><h2>Vragen over Wft, Wwft en regelgeving</h2></div>
  {faq}
  <div class="btns" style="margin-top:22px"><a class="btn btn-primary arrow" href="kennistoets.html">Doe de Wft-kennistoets: 7 vragen, elke keer anders</a></div>
  <div class="note" style="margin-top:26px"><strong>Disclaimer.</strong> De informatie in de WFT Bieb is met zorg samengesteld, maar Bureau DFO is niet verantwoordelijk voor de juistheid, volledigheid of actualiteit van alle informatie op deze pagina en de pagina's waarnaar wordt verwezen. Aan de inhoud kunnen geen rechten worden ontleend. Wilt u het zeker weten? Neem dan contact op met <a href="contact.html">Bureau DFO</a>.</div>
</div></section>
""" + callout("Twijfelt u over de toepassing van een regel?", "Bureau DFO helpt bij vergunningaanvragen, Wft- en Wwft-vragen en de verplichte vastleggingen.",
              "compliance.html", "Naar DFO Compliance")
    js = """<script>
const wq=document.getElementById('wq'),wc=[...document.querySelectorAll('.wb-card')];let fc='',ff='';
function wf(){const t=wq.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);let n=0;
 wc.forEach(a=>{const ok=(!fc||a.dataset.c===fc)&&(!ff||a.dataset.f===ff)&&t.every(w=>a.dataset.s.includes(w));a.hidden=!ok;if(ok)n++;});
 document.getElementById('wn').textContent=n+(n===1?' regeling':' regelingen');document.getElementById('we').hidden=n>0;}
function grp(id,k,set){document.querySelectorAll('#'+id+' .chip').forEach(b=>b.onclick=()=>{set(b.dataset[k]);document.querySelectorAll('#'+id+' .chip').forEach(x=>x.setAttribute('aria-pressed',x===b));wf();});}
grp('wc','c',v=>fc=v);grp('wf','f',v=>ff=v);wq.oninput=wf;
const q=new URLSearchParams(location.search).get('q');if(q)wq.value=q;wf();
</script>"""
    page("wft-bieb.html", "WFT Bieb – wet- en regelgeving voor financieel adviseurs – Bureau DFO",
         f"{len(b['WETTEN'])} wetten en regelingen voor financiële dienstverleners per thema: Wft, Wwft, krediet, pensioen, fiscaal, sociale zekerheid en meer.", body, scripts=js)

    # --- kennistoets
    tq = {"wft": "Wft & toezicht", "eu": "Europese regels", "wwft": "Wwft & integriteit", "privacy": "Privacy", "krediet": "Krediet & hypotheek",
          "fiscaal": "Fiscaal", "pensioen": "Pensioen", "sociaal": "Sociale zekerheid", "toeslagen": "Toeslagen", "familie": "Familie & relatie",
          "erfrecht": "Erfrecht", "burgerlijk": "Burgerlijk recht", "wonen": "Wonen & huur"}
    tcnt = {k: sum(1 for v in vragen if v[0] == k) for k in tq}
    opts = '<option value="">Alle thema\'s (' + str(len(vragen)) + ' vragen)</option>' + "".join(
        f'<option value="{k}">{E(n)} ({tcnt[k]})</option>' for k, n in tq.items() if tcnt[k])
    body = hero("Wft-kennistoets", "Test je kennis van Wft, Wwft en aanpalende regelgeving in 7 vragen. Elke ronde andere vragen, met uitleg bij elk antwoord.",
                crumbs=['<a href="kennisbank.html">Kennisbank</a>', "Kennistoets"])
    body += f"""
<section><div class="wrap" style="max-width:820px">
  <div class="kt-start" id="kts">
    <label for="ktt"><strong>Kies een thema</strong></label>
    <select id="ktt" class="kt-sel">{opts}</select>
    <div class="btns"><button class="btn btn-primary arrow" id="ktgo" type="button">Start de toets</button></div>
  </div>
  <div id="ktp" hidden></div>
  <div class="note" style="margin-top:28px"><strong>Let op.</strong> Deze toets is bedoeld als kennischeck en geldt niet als Wft-examen of PE-bewijs. Bureau DFO is niet verantwoordelijk voor de juistheid en volledigheid van alle vragen en antwoorden; regels wijzigen. Wilt u het zeker weten? Neem contact op met Bureau DFO via 033 258 04 60 of <a href="mailto:info@dfobv.nl">info@dfobv.nl</a>.</div>
</div></section>
""" + callout("Meer weten over de Wft?", "In de WFT Bieb vind je alle wet- en regelgeving per thema, met praktijkthema's en veelgestelde vragen.", "wft-bieb.html", "Naar de WFT Bieb")
    js = """<script>
const V=__V__,TH=__T__,N=7;let set=[],i=0,goed=0;
const p=document.getElementById('ktp'),s=document.getElementById('kts');
const esc=x=>String(x).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const mix=a=>{a=a.slice();for(let k=a.length-1;k>0;k--){const j=Math.floor(Math.random()*(k+1));[a[k],a[j]]=[a[j],a[k]];}return a;};
function start(){const t=document.getElementById('ktt').value;set=mix(V.filter(v=>!t||v[0]===t)).slice(0,N).map(v=>({th:v[0],q:v[1],a:mix(v[2].map((x,k)=>({t:x[0],w:x[1],ok:k===0})))}));i=0;goed=0;s.hidden=true;p.hidden=false;vraag();}
function vraag(){const v=set[i];p.innerHTML=`<div class="kt-kop"><span class="tag">${esc(TH[v.th]||v.th)}</span><span class="muted">Vraag ${i+1} van ${set.length}</span></div><h2 class="kt-q">${esc(v.q)}</h2><div class="kt-opts">`+v.a.map((x,k)=>`<button type="button" class="kt-opt" data-k="${k}">${esc(x.t)}</button>`).join('')+`</div><div id="ktf"></div>`;
 p.querySelectorAll('.kt-opt').forEach(b=>b.onclick=()=>kies(+b.dataset.k));p.querySelector('.kt-opt').focus();}
function kies(k){const v=set[i];const x=v.a[k];if(x.ok)goed++;
 p.querySelectorAll('.kt-opt').forEach((b,j)=>{b.disabled=true;if(v.a[j].ok)b.classList.add('ok');else if(j===k)b.classList.add('fout');});
 const juist=v.a.find(a=>a.ok);document.getElementById('ktf').innerHTML=`<div class="kt-fb ${x.ok?'ok':'fout'}"><strong>${x.ok?'Goed!':'Helaas, niet goed.'}</strong> ${esc(x.w)}${x.ok?'':'<br><span class="muted">Juist antwoord: '+esc(juist.t)+'. '+esc(juist.w)+'</span>'}</div><div class="btns"><button type="button" class="btn btn-primary arrow" id="ktn">${i+1<set.length?'Volgende vraag':'Bekijk je score'}</button></div>`;
 document.getElementById('ktn').onclick=()=>{i++;i<set.length?vraag():einde();};document.getElementById('ktn').focus();}
function einde(){const pct=Math.round(goed/set.length*100);p.innerHTML=`<div class="kt-score"><div class="kt-pct">${goed} / ${set.length}</div><p>${pct>=80?'Uitstekend! Je kennis is goed op orde.':pct>=55?'Voldoende, maar er zijn nog aandachtspunten.':'Er valt nog wat te leren. Kijk eens in de WFT Bieb of volg een opleiding.'}</p><div class="btns"><button type="button" class="btn btn-primary arrow" id="ktr">Nieuwe ronde</button><a class="btn btn-ghost" href="wft-bieb.html">Naar de WFT Bieb</a><a class="btn btn-ghost" href="opleidingen.html">Opleidingen</a></div></div>`;
 document.getElementById('ktr').onclick=()=>{p.hidden=true;s.hidden=false;};}
document.getElementById('ktgo').onclick=start;
</script>""".replace("__V__", json.dumps(vragen, ensure_ascii=False)).replace("__T__", json.dumps(tq, ensure_ascii=False))
    page("kennistoets.html", "Wft-kennistoets – test je kennis in 7 vragen – Bureau DFO",
         "Gratis Wft-kennistoets: 7 wisselende vragen over Wft, Wwft, krediet, pensioen, fiscaal en meer, met uitleg bij elk antwoord.", body, scripts=js)
    return f"{len(b['WETTEN'])} regelingen, {npk} praktijkthema's, {len(vragen)} toetsvragen; kennisbank +{nw}+{npk}"
