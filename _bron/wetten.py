"""Wetteksten (Wft, BGfo, TRHK) uit de officiële BWB-XML renderen + wettenoverzicht van finrecht.nl.

Bron-XML: _bron/wetten/<BWB-id>.xml (repository.officiele-overheidspublicaties.nl).
Levert ook wettelijke definities voor de kennisbank: _bron/kennisbank/wetgeving.json
"""
import json, re, html, datetime
import xml.etree.ElementTree as ET
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
WDIR = SRC / "wetten"
E = html.escape

LAWS = {
    "BWBR0020368": {"kort": "Wft", "naam": "Wet op het financieel toezicht", "prefix": "wft"},
    "BWBR0020421": {"kort": "BGfo", "naam": "Besluit Gedragstoezicht financiële ondernemingen Wft", "prefix": "bgfo"},
    "BWBR0032503": {"kort": "TRHK", "naam": "Tijdelijke regeling hypothecair krediet", "prefix": "trhk"},
}
SKIP = {"meta-data", "jcis", "jci", "brondata", "opmerkingen-inhoud", "bwb-inputbestand", "bwb-wijzigingen",
        "redactionele-correcties", "colspec"}
STRUCT = {"titeldeel", "hoofdstuk", "afdeling", "paragraaf", "sub-paragraaf", "divisie", "titel"}

ART2PAGE = {}  # (bwb, artikelnr) -> pagina#anker


def aid(nr):
    return "artikel-" + re.sub(r"[^0-9a-zA-Z]+", "-", nr).strip("-").lower()


def kop_text(el):
    k = el.find("kop")
    if k is None:
        return "", "", ""
    lab = (k.findtext("label") or "").strip()
    nr = (k.findtext("nr") or "").strip()
    tit = "".join(k.find("titel").itertext()).strip() if k.find("titel") is not None else ""
    return lab, nr, re.sub(r"\s+", " ", tit)


def jci_target(doc):
    """jci1.3:c:BWBR0020368&artikel=1:1&... -> lokale of externe link."""
    m = re.search(r"(BWBR\d+)", doc or "")
    if not m:
        return None
    bwb = m.group(1)
    a = re.search(r"artikel=([^&]+)", doc)
    if bwb in LAWS and a and (bwb, a.group(1)) in ART2PAGE:
        return ART2PAGE[(bwb, a.group(1))]
    if bwb in LAWS and not a:
        return LAWS[bwb]["prefix"] + ".html"
    url = f"https://wetten.overheid.nl/{bwb}/"
    if a:
        url += f"#Artikel{a.group(1)}"
    return url


def inline(el):
    out = [E(el.text or "")]
    for c in el:
        t = c.tag
        if t in SKIP:
            out.append(E(c.tail or ""))
            continue
        inner = inline(c)
        if t in ("intref", "extref"):
            href = jci_target(c.get("doc") or "") or c.get("doc") or c.get("href")
            if href and (href.startswith("http") or href.endswith(".html") or "#" in href):
                ext = ' rel="noopener"' if href.startswith("http") else ""
                out.append(f'<a href="{E(href)}"{ext}>{inner}</a>')
            else:
                out.append(inner)
        elif t == "nadruk":
            ty = c.get("type", "")
            out.append(f"<strong>{inner}</strong>" if ty == "vet" else f"<em>{inner}</em>")
        elif t in ("sup", "inf", "sub"):
            out.append(f"<sup>{inner}</sup>" if t == "sup" else f"<sub>{inner}</sub>")
        elif t == "al":
            out.append(inner + " ")
        else:
            out.append(inner)
        out.append(E(c.tail or ""))
    return re.sub(r"\s+", " ", "".join(out))


def block(el):
    """Rendert inhoud van artikel/lid/li recursief."""
    out = []
    for c in el:
        t = c.tag
        if t in SKIP or t in ("kop", "lidnr", "li.nr"):
            continue
        if t == "al":
            out.append(f"<p>{inline(c).strip()}</p>")
        elif t == "lid":
            nr = (c.findtext("lidnr") or "").strip()
            out.append(f'<div class="lid"><span class="lidnr">{E(nr)}</span><div>{block(c)}</div></div>')
        elif t == "lijst":
            out.append('<ul class="wlijst">' + "".join(
                f'<li><span class="linr">{E((li.findtext("li.nr") or "").strip())}</span><div>{block(li)}</div></li>'
                for li in c.findall("li")) + "</ul>")
        elif t == "table":
            rows = []
            for row in c.iter("row"):
                cells = "".join(f"<td>{inline(e) if e.find('al') is None else ' '.join(inline(a) for a in e.findall('al'))}</td>" for e in row.findall("entry"))
                rows.append(f"<tr>{cells}</tr>")
            tit = c.findtext("title") or ""
            out.append(f'<div class="tablewrap">{f"<p><strong>{E(tit)}</strong></p>" if tit else ""}<table>{"".join(rows)}</table></div>')
        elif t == "redactie":
            out.append(f'<p class="redactie"><em>{inline(c).strip()}</em></p>')
        elif t in ("tussenkop", "subtitel"):
            out.append(f"<h4>{inline(c).strip()}</h4>")
        elif t in ("li",):
            out.append(block(c))
        else:
            sub = block(c)
            if sub:
                out.append(sub)
    return "".join(out)


def article_html(a, bwb):
    lab, nr, tit = kop_text(a)
    head = f"{lab} {nr}".strip() + (f" — {tit}" if tit else "")
    src = f"https://wetten.overheid.nl/{bwb}/#Artikel{nr}"
    return (f'<article class="wart" id="{aid(nr)}"><h3><a href="#{aid(nr)}" class="anchor">{E(head)}</a></h3>{block(a)}'
            f'<p class="wbron"><a href="{src}" rel="noopener">Bekijk op wetten.overheid.nl</a></p></article>')


def section_html(el, bwb, depth=2):
    """Structuurelement (hoofdstuk/afdeling/…) recursief."""
    out = []
    lab, nr, tit = kop_text(el)
    if lab or tit:
        h = min(depth, 4)
        sid = re.sub(r"[^0-9a-z]+", "-", f"{lab} {nr}".lower()).strip("-")
        out.append(f'<h{h} class="wkop" id="{sid}">{E((lab + " " + nr).strip())}{" — " + E(tit) if tit else ""}</h{h}>')
    for c in el:
        if c.tag == "artikel":
            out.append(article_html(c, bwb))
        elif c.tag in STRUCT:
            out.append(section_html(c, bwb, depth + 1))
        elif c.tag in ("al",):
            out.append(f"<p>{inline(c)}</p>")
    return "".join(out)


def toc(el, href_for, depth=0):
    items = []
    for c in el:
        if c.tag in STRUCT:
            lab, nr, tit = kop_text(c)
            sid = re.sub(r"[^0-9a-z]+", "-", f"{lab} {nr}".lower()).strip("-")
            sub = toc(c, href_for, depth + 1) if depth < 1 else ""
            items.append(f'<li><a href="{href_for(c, sid)}">{E((lab + " " + nr).strip())} — {E(tit)}</a>{sub}</li>')
    return f'<ul class="wtoc">{"".join(items)}</ul>' if items else ""


def load(bwb):
    return ET.parse(WDIR / f"{bwb}.xml").getroot()


def law_meta(root):
    t = root.find(".//citeertitel")
    titel = "".join(t.itertext()).strip() if t is not None else ""
    return titel, root.get("inwerkingtreding") or ""


def units(root):
    """Pagina-eenheden: Wft per hoofdstuk, BGfo per hoofdstuk, TRHK in één pagina."""
    wt = root.find(".//wettekst")
    if wt is None:
        wt = root.find(".//regeling-tekst")
    return wt


def build_law_pages(page, hero, callout):
    stats = {}
    defs = []
    intro = json.loads((SRC / "finrecht.json").read_text())
    for bwb, info in LAWS.items():
        root = load(bwb)
        wt = units(root)
        pre = info["prefix"]
        geldig = root.get("inwerkingtreding") or ""
        # eenheden bepalen
        pages = []
        if bwb == "BWBR0020368":
            for deel in wt.findall("titeldeel"):
                hs = deel.findall("hoofdstuk")
                if hs:
                    for h in hs:
                        pages.append((deel, h))
                else:
                    pages.append((deel, deel))
        elif bwb == "BWBR0020421":
            for h in wt.findall("hoofdstuk"):
                pages.append((None, h))
        else:
            pages.append((None, wt))
        # artikel -> pagina
        fname = {}
        for parent, unit in pages:
            lab, nr, _ = kop_text(unit)
            fn = f"{pre}.html" if unit is wt else f"{pre}-{re.sub(r'[^0-9a-z]+', '-', (lab + ' ' + nr).lower()).strip('-')}.html"
            fname[id(unit)] = fn
            for a in unit.iter("artikel"):
                _, anr, _ = kop_text(a)
                ART2PAGE[(bwb, anr)] = f"{fn}#{aid(anr)}"
        stats[info["kort"]] = sum(1 for _ in wt.iter("artikel"))
    # tweede ronde: renderen (alle ankers bekend voor kruisverwijzingen)
    for bwb, info in LAWS.items():
        root = load(bwb)
        wt = units(root)
        pre = info["prefix"]
        geldig = root.get("inwerkingtreding") or ""
        if bwb == "BWBR0020368":
            pages = [(d, h) for d in wt.findall("titeldeel") for h in (d.findall("hoofdstuk") or [d])]
        elif bwb == "BWBR0020421":
            pages = [(None, h) for h in wt.findall("hoofdstuk")]
        else:
            pages = [(None, wt)]
        geldig_txt = f"Geldend vanaf {geldig}" if geldig else ""
        src_url = f"https://wetten.overheid.nl/{bwb}/" + (f"{geldig}/0" if geldig else "")
        def href_for(c, sid, pre=pre, bwb=bwb):
            a = next(c.iter("artikel"), None)
            if a is None:
                return f"{pre}.html"
            _, anr, _ = kop_text(a)
            p = ART2PAGE.get((bwb, anr), f"{pre}.html")
            # hoofdstukken zonder label (sid '1', '3a') hebben geen eigen anker op de pagina: naar de paginatop
            return p.split("#")[0] + ("" if re.fullmatch(r"\d+[a-z]?", sid or "") else f"#{sid}")
        nav_index = f'<a href="{pre}.html">{info["kort"]} – inhoudsopgave</a>'
        if len(pages) > 1:
            for i, (parent, unit) in enumerate(pages):
                lab, nr, tit = kop_text(unit)
                fn = ART2PAGE[(bwb, kop_text(next(unit.iter("artikel")))[1])].split("#")[0] if next(unit.iter("artikel"), None) is not None else None
                if not fn:
                    continue
                plab, pnr, ptit = kop_text(parent) if parent is not None and parent is not unit else ("", "", "")
                prev_fn = next_fn = None
                if i > 0 and next(pages[i - 1][1].iter("artikel"), None) is not None:
                    prev_fn = ART2PAGE[(bwb, kop_text(next(pages[i - 1][1].iter("artikel")))[1])].split("#")[0]
                if i + 1 < len(pages) and next(pages[i + 1][1].iter("artikel"), None) is not None:
                    next_fn = ART2PAGE[(bwb, kop_text(next(pages[i + 1][1].iter("artikel")))[1])].split("#")[0]
                pn = '<div class="btns" style="justify-content:space-between">' + \
                     (f'<a class="btn btn-ghost" href="{prev_fn}">← Vorige</a>' if prev_fn else "<span></span>") + \
                     f'<a class="btn btn-ghost" href="{pre}.html">Inhoudsopgave</a>' + \
                     (f'<a class="btn btn-ghost" href="{next_fn}">Volgende →</a>' if next_fn else "<span></span>") + "</div>"
                body = hero(E(f"{lab} {nr} {tit}".strip()), E(f"{info['naam']} ({info['kort']})" + (f" · {plab} {pnr} {ptit}" if plab else "")),
                            crumbs=['<a href="wetgeving.html">Wet- en regelgeving</a>', f'<a href="{pre}.html">{info["kort"]}</a>', E(f"{lab} {nr}")])
                body += f'''<section><div class="wrap wet">{pn}
<p class="muted" style="font-size:.85rem">{E(geldig_txt)} · Bron: <a href="{src_url}" rel="noopener">wetten.overheid.nl</a> (officiële tekst)</p>
{section_html(unit, bwb)}{pn}</div></section>'''
                page(fn, f"{info['kort']} {lab} {nr} {tit} – Wet- en regelgeving".strip(), f"{info['naam']}: {lab} {nr} {tit}"[:155], body)
            # inhoudsopgave
            intro_html = ""
            key = {"wft": None, "bgfo": "bgfo-p.html", "trhk": "trhk-p.html"}[pre]
            if key:
                intro_html = render_intro(intro[key])
            body = hero(E(info["naam"]), E(f"{info['kort']} · {stats[info['kort']]} artikelen · {geldig_txt}"),
                        crumbs=['<a href="wetgeving.html">Wet- en regelgeving</a>', info["kort"]])
            body += f'''<section><div class="wrap wet">{intro_html}
<h2>Inhoudsopgave</h2>{toc(wt, href_for)}
<p class="muted" style="margin-top:24px;font-size:.85rem">De wettekst is overgenomen uit de officiële bron (wetten.overheid.nl, BWB {bwb}). Aan deze weergave kunnen geen rechten worden ontleend; de officiële publicatie is leidend.</p>
</div></section>'''
            page(f"{pre}.html", f"{info['naam']} ({info['kort']}) – Wet- en regelgeving", f"Volledige tekst {info['naam']} met inhoudsopgave.", body)
        else:
            intro_html = render_intro(intro["trhk-p.html"]) if pre == "trhk" else ""
            body = hero(E(info["naam"]), E(f"{info['kort']} · {stats[info['kort']]} artikelen · {geldig_txt}"),
                        crumbs=['<a href="wetgeving.html">Wet- en regelgeving</a>', info["kort"]])
            body += f'''<section><div class="wrap wet">{intro_html}<h2>Volledige tekst</h2>
<p class="muted" style="font-size:.85rem">{E(geldig_txt)} · Bron: <a href="{src_url}" rel="noopener">wetten.overheid.nl</a></p>
{section_html(wt, bwb)}
{bijlagen(root, bwb)}</div></section>'''
            page(f"{pre}.html", f"{info['naam']} ({info['kort']}) – Wet- en regelgeving", f"Volledige tekst {info['naam']}.", body)
        defs += definitions(root, bwb, info)
    # definities naar kennisbank
    (SRC / "kennisbank").mkdir(exist_ok=True)
    defs += afkortingen(intro)
    seen, uniq = set(), []
    for d in defs:
        k = d["term"].lower()
        if k in seen:
            continue
        seen.add(k); uniq.append(d)
    uniq.sort(key=lambda d: d["term"].lower())
    (SRC / "kennisbank" / "wetgeving.json").write_text(json.dumps(uniq, ensure_ascii=False, indent=1))
    build_overview(page, hero, callout, intro, stats)
    return stats, len(uniq)


def bijlagen(root, bwb):
    out = []
    for b in root.iter("bijlage"):
        lab, nr, tit = kop_text(b)
        out.append(f'<h2 class="wkop">{E((lab + " " + nr).strip())}{" — " + E(tit) if tit else ""}</h2>{block(b)}')
    return "".join(out)


def render_intro(blocks):
    out = []
    for b in blocks:
        t = b["t"]
        if re.match(r"^(Bekijk|TRHK ondersteuning|BGFO ondersteuning|Hypothecairplanner|Fastlane|DRAAGPLICHT|RekenTOOLS|BLINQX|www\.|verzekeringhypotheek|Google Sites|Report abuse|Page )", t, re.I):
            continue
        if b["tag"] == "li":
            out.append(f"<li>{E(t)}</li>")
        else:
            out.append(f"<p>{E(t)}</p>")
    s = "".join(out)
    s = re.sub(r"((?:<li>.*?</li>)+)", r'<ul class="check">\1</ul>', s)
    return f'<div class="prose" style="margin-bottom:28px">{s}</div>'


def definitions(root, bwb, info):
    """Wettelijke definities uit het definitie-artikel (Wft 1:1, BGfo 1, TRHK 1): <al><nadruk>term:</nadruk> definitie</al>."""
    want = {"BWBR0020368": "1:1", "BWBR0020421": "1", "BWBR0032503": "1"}[bwb]
    art = next((a for a in root.iter("artikel") if kop_text(a)[1] == want), None)
    if art is None:
        return []
    clean = lambda h: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", h))).strip()
    out = []
    # kandidaten: al-elementen direct in het artikel, in leden of in lijst-items (TRHK)
    cands = []
    def collect(el):
        kids = list(el)
        for i, c in enumerate(kids):
            if c.tag == "al":
                cands.append((c, kids[i + 1] if i + 1 < len(kids) else None))
            elif c.tag in ("lid", "lijst", "li"):
                collect(c)
    collect(art)
    for al, nxt in cands:
        n = al.find("nadruk")
        if n is None or (al.text or "").strip():
            continue
        term = clean("".join(n.itertext())).rstrip(":").strip()
        rest = clean((n.tail or "") + "".join(inline(x) + (x.tail or "") for x in list(al)[list(al).index(n) + 1:]))
        rest = rest.lstrip(":").strip()
        if not rest and nxt is not None and nxt.tag == "lijst":
            parts = []
            for li in nxt.findall("li"):
                nr = (li.findtext("li.nr") or "").strip()
                txt = clean(" ".join(inline(x) for x in li.iter("al")))
                parts.append(f"{nr} {txt}".strip())
            rest = " ".join(parts)
        rest = rest.rstrip(";").rstrip(",").strip().rstrip(".")
        if not term or not rest or len(term) > 80:
            continue
        d = rest if re.match(r"^[a-z0-9]{1,3}[.°]", rest) else rest[0].upper() + rest[1:]
        out.append({"term": term[0].upper() + term[1:], "afk": "", "def": f"{d}. (Wettelijke definitie, art. {want} {info['kort']}.)",
                    "zie": [], "volatiel": False, "link": ART2PAGE.get((bwb, want), ""), "bron": info["kort"]})
    return out


def afkortingen(intro):
    out = []
    for b in intro["fin-afkortingen.html"]:
        m = re.match(r"^([A-Za-z0-9.\- /tm]+?)\s*[–-]\s*(.+?):?\s*(https?://\S+)?$", b["t"])
        if not m or b["t"].startswith("Afkortingen"):
            continue
        afk, naam = m.group(1).strip(), m.group(2).strip().rstrip(":").strip()
        link = next((h for _, h in b["l"] if h.startswith("http")), "")
        bw = re.search(r"(BWBR\d+)", link or "")
        local = LAWS.get(bw.group(1), {}).get("prefix") + ".html" if bw and bw.group(1) in LAWS else ""
        out.append({"term": naam.split(":")[0].strip(), "afk": afk, "def": f"{naam.split(':')[0].strip()} ({afk})." + (" " + naam.split(':', 1)[1].strip() if ':' in naam else ""),
                    "zie": [], "volatiel": False, "link": local or link, "bron": "finrecht.nl"})
    return out


def build_overview(page, hero, callout, intro, stats):
    blocks = intro["fin-home.html"]
    out, cur = [], None
    for b in blocks:
        t = b["t"]
        if b["tag"] in ("h3", "h2") or (b["tag"] == "p" and t.isupper() and len(t) < 60):
            title = re.sub(r"\s+", " ", t.replace("W FT", "WFT").replace("Kif id", "Kifid"))
            cur = {"t": title.title() if title.isupper() else title, "items": []}
            out.append(cur)
            continue
        if b["tag"] == "li" and cur is not None:
            href = next((h for _, h in b["l"] if h.startswith("http")), "")
            href = href.replace("https://www.google.com/search?q=", "")
            bw = re.search(r"(BWBR\d+)", href)
            local = LAWS[bw.group(1)]["prefix"] + ".html" if bw and bw.group(1) in LAWS else ""
            cur["items"].append((t, local or href, bool(local)))
    secs = ""
    for s in out:
        if not s["items"]:
            continue
        lis = "".join(f'<li><a href="{E(h)}"{"" if loc else " rel=noopener"}>{icon_doc()}<span>{E(t)}{" <strong>(volledige tekst op deze site)</strong>" if loc else ""}</span></a></li>' for t, h, loc in s["items"])
        secs += f'<div class="doc-group"><h3>{E(s["t"])}</h3><ul class="doc-list">{lis}</ul></div>'
    afk = "".join(f'<tr><td><strong>{E(d["afk"])}</strong></td><td>{E(d["term"])}</td><td>{f"<a href={chr(34)}{E(d["link"])}{chr(34)} rel=noopener>wettekst</a>" if d["link"] else ""}</td></tr>' for d in afkortingen(intro))
    alf = []
    for b in intro["fin-alfabet.html"]:
        m = re.match(r"^(\S.+?)\s+-\s+(.+)$", b["t"])
        if m:
            href = next((h for _, h in b["l"] if h.startswith("http")), "")
            alf.append((m.group(1), m.group(2), href))
    alf_html = " · ".join(f'<a href="{E(h or "#")}" rel="noopener">{E(w)}</a>' for w, _, h in alf)
    body = hero("Wet- en regelgeving", "Wetten voor de financiële dienstverlening: de volledige teksten van de Wft, het BGfo en de TRHK op deze site, plus een overzicht van alle relevante wetten.",
                crumbs=["Wet- en regelgeving"],
                btns='<a class="btn btn-light arrow" href="wft.html">Wft</a><a class="btn btn-ghost" href="bgfo.html">BGfo</a><a class="btn btn-ghost" href="trhk.html">TRHK</a>')
    body += f"""
<section><div class="wrap">
  <div class="grid g3">
    <a class="card" href="wft.html"><span class="tag">Wft</span><h3>Wet op het financieel toezicht</h3><p>{stats.get('Wft', 0)} artikelen, per hoofdstuk, met kruisverwijzingen.</p><span class="more arrow">Naar de Wft </span></a>
    <a class="card" href="bgfo.html"><span class="tag">BGfo</span><h3>Besluit Gedragstoezicht financiële ondernemingen Wft</h3><p>{stats.get('BGfo', 0)} artikelen: vakbekwaamheid, informatieverstrekking, zorgvuldige dienstverlening.</p><span class="more arrow">Naar het BGfo </span></a>
    <a class="card" href="trhk.html"><span class="tag">TRHK</span><h3>Tijdelijke regeling hypothecair krediet</h3><p>De leennormen: LTI, LTV en de financieringslasttabellen.</p><span class="more arrow">Naar de TRHK </span></a>
  </div>
  <p style="margin-top:18px"><a href="kennisbank.html#wetgeving">Wettelijke definities en afkortingen in de kennisbank →</a></p>
</div></section>
<section class="alt"><div class="wrap"><div class="sec-head"><h2>Financiële wetgeving</h2><p>Overzicht van wetten en regelingen voor de financiële dienstverlening (bron: FINrecht.nl).</p></div>{secs}</div></section>
<section><div class="wrap"><div class="sec-head"><h2>Afkortingen wet- en regelgeving</h2></div><div class="tablewrap"><table><tbody>{afk}</tbody></table></div></div></section>
<section class="alt"><div class="wrap"><div class="sec-head"><h2>Alfabet</h2><p>Omdat veel van deze woorden in meerdere titels voorkomen, zijn ze gekoppeld aan de meest relevante wet.</p></div><p style="line-height:2">{alf_html}</p></div></section>
<section class="tight"><div class="wrap"><div class="note"><strong>Disclaimer.</strong> De informatie op deze pagina's is uitsluitend bedoeld voor algemene informatieve doeleinden; er kunnen geen rechten aan worden ontleend. Dit is geen financieel, juridisch of fiscaal advies. Wetteksten zijn overgenomen uit de officiële bron; de publicatie op wetten.overheid.nl is leidend.</div></div></section>
"""
    page("wetgeving.html", "Wet- en regelgeving – Bureau DFO", "Wft, BGfo en TRHK volledig, plus een overzicht van alle wetten voor de financiële dienstverlening.", body)


def icon_doc():
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M8 13h8M8 17h6"/></svg>')
