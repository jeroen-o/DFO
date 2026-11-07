"""Integratie van www.dfobv.nl (WordPress): pagina's, artikelen, webshopcatalogus en agenda-archief.

Bron: _bron/dfobv/*.json (WordPress REST API + WooCommerce Store API) en _bron/dfobv/events.json.
Wordt aangeroepen vanuit build.py via build_dfobv(ctx).
"""
import json, re, html, hashlib, os, datetime
from pathlib import Path
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup, NavigableString, Tag

SRC = Path(__file__).resolve().parent / "dfobv"
ROOT = Path(__file__).resolve().parent.parent
IMGDIR = ROOT / "assets" / "dfobv" / "img"
PDFDIR = ROOT / "assets" / "dfobv" / "pdf"
E = html.escape

PAGES = json.loads((SRC / "pages.json").read_text())
POSTS = json.loads((SRC / "posts.json").read_text())
PRODUCTS = [p for f in sorted(SRC.glob("prod*.json")) for p in json.loads(f.read_text())]
CATS = json.loads((SRC / "cats.json").read_text())
EVENTS = json.loads((SRC / "events.json").read_text()) if (SRC / "events.json").exists() else []

# pagina's die alleen techniek/winkelfunctie zijn of al elders op de site staan
SKIP_PAGES = {"blogpagina", "opleidingen", "mijn-reservaties", "tags", "categorieen", "locaties", "evenementen",
              "mijn-account", "afrekenen", "winkelwagen", "winkel", "agenda"}
PAGE_SLUGS = {p["slug"] for p in PAGES if p["slug"] not in SKIP_PAGES}
POST_SLUGS = {p["slug"] for p in POSTS}
PROD_SLUGS = {p["slug"] for p in PRODUCTS}

IMGQ = {}  # bron-url -> lokaal pad


def u(s):
    return html.unescape(s or "")


def local_img(url, maxw=900):
    url = url.split("?")[0]
    if "dfobv.nl/wp-content/uploads" not in url:
        return url
    name = unquote(url.split("/uploads/")[-1]).replace("/", "-")
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", name.rsplit(".", 1)[0])[:90]
    rel = f"assets/dfobv/img/{base}.jpg"
    IMGQ[url] = (rel, maxw)
    return rel


def page_name(slug):
    return f"info-{slug}.html"


def rewrite(href):
    """dfobv.nl-links naar lokale pagina's waar mogelijk."""
    if not href:
        return "#"
    h = href.strip()
    if h.startswith(("mailto:", "tel:", "#")):
        return h.replace("tel:033 258 04 60", "tel:+31332580460")
    p = urlparse(h)
    host = (p.netloc or "").lower()
    if host in ("www.dfobv.nl", "dfobv.nl"):
        path = unquote(p.path)
        if "/wp-content/uploads/" in path and path.lower().endswith(".mp4"):
            f = path.split("/uploads/")[-1].replace("/", "-")
            if (ROOT / "assets/dfobv/video" / f).exists():
                return f"assets/dfobv/video/{f}"
            return h.split("?")[0]
        if "/wp-content/uploads/" in path and path.lower().endswith(".pdf"):
            f = path.split("/uploads/")[-1].replace("/", "-")
            if (PDFDIR / f).exists():
                return f"assets/dfobv/pdf/{f}"
            return h
        if "/wp-content/uploads/" in path and re.search(r"\.(jpe?g|png|gif|webp)$", path, re.I):
            return local_img(h, 1400)
        seg = [s for s in path.split("/") if s]
        if not seg:
            return "index.html"
        if seg[0] == "product" and len(seg) > 1 and seg[1] in PROD_SLUGS:
            return f"product-{seg[1]}.html"
        if seg[0] == "product-categorie" and len(seg) > 1:
            return f"webshop.html#{seg[-1]}"
        if seg[0] in ("winkel", "shop"):
            return "webshop.html"
        if seg[0] in ("events", "evenementen", "agenda"):
            return "agenda-archief.html"
        if seg[0] == "ons-team":
            return "over-dfo.html#team"
        if seg[0] == "contact":
            return "contact.html"
        if seg[0] == "secretariaten":
            return "secretariaten.html"
        if seg[0] in ("opinie", "blog", "category"):
            return "artikelen.html"
        if seg[0] in PAGE_SLUGS:
            return page_name(seg[0])
        if seg[0] in POST_SLUGS:
            return f"artikel-{seg[0]}.html"
    if host in ("www.dfosignalen.nl", "dfosignalen.nl") and p.path in ("", "/"):
        return "signalen.html"
    return h


BLOCK = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "blockquote", "table", "img", "iframe", "video", "figure"}


def inline(el):
    out = []
    for c in el.children:
        if isinstance(c, NavigableString):
            out.append(E(str(c)))
        elif isinstance(c, Tag):
            n = c.name
            if n in ("script", "style", "form", "button", "input", "svg", "noscript", "textarea", "select", "label"):
                continue
            if n == "img":
                src = c.get("src") or c.get("data-src") or ""
                if src:
                    out.append(f'<img src="{E(local_img(src))}" alt="{E(c.get("alt", ""))}" loading="lazy">')
                continue
            inner = inline(c)
            if n == "a":
                h = rewrite(c.get("href"))
                ext = ' rel="noopener"' if h.startswith("http") else ""
                out.append(f'<a href="{E(h)}"{ext}>{inner}</a>' if inner.strip() else "")
            elif n in ("strong", "b"):
                out.append(f"<strong>{inner}</strong>" if inner.strip() else inner)
            elif n in ("em", "i"):
                out.append(f"<em>{inner}</em>" if inner.strip() else inner)
            elif n == "br":
                out.append("<br>")
            elif n in ("sup", "sub"):
                out.append(f"<{n}>{inner}</{n}>")
            else:
                out.append(inner)
    s = re.sub(r"[ \t\r\n]+", " ", "".join(out))
    s = re.sub(r"(<br>\s*){3,}", "<br><br>", s)
    return s.strip()


def clean(raw):
    """WordPress/Elementor-HTML -> schone, woordelijke HTML-blokken."""
    raw = re.sub(r"\[/?[a-z_]+[^\]]*\]", "", raw or "")  # shortcodes
    s = BeautifulSoup(raw, "html.parser")
    for t in s(["script", "style", "form", "button", "input", "svg", "noscript", "textarea", "select"]):
        t.decompose()
    out, done = [], set()

    def handled(el):
        return any(id(p) in done for p in el.parents)

    for el in s.find_all(True):
        if handled(el):
            continue
        n = el.name
        if n in ("h1", "h2", "h3", "h4", "h5", "h6"):
            done.add(id(el))
            t = inline(el)
            if re.sub(r"<[^>]+>", "", t).strip():
                lvl = "h2" if n in ("h1", "h2") else "h3"
                out.append(f"<{lvl}>{t}</{lvl}>")
        elif n == "p":
            done.add(id(el))
            t = inline(el)
            if re.sub(r"<[^>]+>|&nbsp;|\s", "", t) or "<img" in t:
                out.append(f"<p>{t}</p>")
        elif n in ("ul", "ol"):
            done.add(id(el))
            items = [inline(li) for li in el.find_all("li", recursive=False)]
            items = [i for i in items if re.sub(r"<[^>]+>|\s", "", i)]
            if items:
                out.append(f"<{n}>" + "".join(f"<li>{i}</li>" for i in items) + f"</{n}>")
        elif n == "blockquote":
            done.add(id(el))
            out.append(f"<blockquote>{inline(el)}</blockquote>")
        elif n == "table":
            done.add(id(el))
            rows = []
            for tr in el.find_all("tr"):
                cells = "".join(f"<{c.name}>{inline(c)}</{c.name}>" for c in tr.find_all(["td", "th"]))
                rows.append(f"<tr>{cells}</tr>")
            out.append('<div class="tablewrap"><table>' + "".join(rows) + "</table></div>")
        elif n == "img":
            done.add(id(el))
            src = el.get("src") or el.get("data-src") or ""
            if src and not src.startswith("data:"):
                a = el.find_parent("a")
                im = f'<img src="{E(local_img(src))}" alt="{E(el.get("alt", ""))}" loading="lazy">'
                if a and a.get("href"):
                    h = rewrite(a["href"])
                    im = f'<a href="{E(h)}"{" rel=noopener" if h.startswith("http") else ""}>{im}</a>'
                out.append(f'<p class="wpimg">{im}</p>')
        elif n == "iframe":
            done.add(id(el))
            m = re.search(r"youtube(?:-nocookie)?\.com/embed/([\w-]+)", el.get("src", ""))
            if m:
                out.append(f'<div class="yt"><iframe src="https://www.youtube-nocookie.com/embed/{m.group(1)}?rel=0" loading="lazy" title="Video" allowfullscreen></iframe></div>')
            elif el.get("src", "").startswith("http"):
                out.append(f'<p><a href="{E(el["src"])}" rel="noopener">Bekijk de ingesloten inhoud</a></p>')
        elif n == "video":
            done.add(id(el))
            src = (el.find("source") or {}).get("src") if el.find("source") else el.get("src")
            if src:
                src = rewrite(src.split("?")[0])
                if src.startswith("assets/"):
                    out.append(f'<div class="vid"><video controls preload="metadata" playsinline src="{E(src)}"></video></div>')
                else:
                    out.append(f'<p><a class="btn btn-ghost arrow" href="{E(src)}" rel="noopener">Bekijk de video (mp4)</a></p>')
        elif n in ("div", "span", "section", "li") and el.find(True) is None:
            # losse tekst in Elementor-widgets
            t = re.sub(r"\s+", " ", el.get_text(" ", strip=True))
            if t and len(t) > 1 and n != "li":
                done.add(id(el))
                out.append(f"<p>{E(t)}</p>")
    # dubbele opeenvolgende blokken weghalen
    res = []
    for b in out:
        if not res or res[-1] != b:
            res.append(b)
    return "\n".join(res)


def text_of(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h or ""))).strip()


def euro(cents, minor=2):
    v = int(cents) / (10 ** minor)
    if v == 0:
        return "Gratis"
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€ {s}"


def date_nl(iso):
    M = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]
    d = datetime.date.fromisoformat(iso[:10])
    return f"{d.day} {M[d.month - 1]} {d.year}"


def terms(p):
    return [html.unescape(t["name"]) for g in p.get("_embedded", {}).get("wp:term", []) for t in g if t.get("taxonomy") == "category"]


def featured(p):
    fm = p.get("_embedded", {}).get("wp:featuredmedia", [{}])
    return fm[0].get("source_url") if fm and isinstance(fm[0], dict) else None


def build_dfobv(ctx):
    page, hero, callout, icon = ctx["page"], ctx["hero"], ctx["callout"], ctx["icon"]
    PAGE_SLUGS.discard("secretariaten")  # eigen pagina bestaat al
    # ---------------- informatiepagina's
    for p in PAGES:
        slug = p["slug"]
        if slug in SKIP_PAGES or slug == "secretariaten":
            continue
        title = u(p["title"]["rendered"]) or slug.replace("-", " ").capitalize()
        body_html = clean(p["content"]["rendered"])
        if not text_of(body_html) and "<img" not in body_html and "<a" not in body_html:
            continue
        body = hero(E(title), "", crumbs=["www.dfobv.nl", E(title)])
        body += f'<section><div class="wrap"><div class="prose wp">{body_html}</div>' \
                f'<p class="muted" style="font-size:.82rem;margin-top:28px">Overgenomen van www.dfobv.nl/{E(slug)}/ · laatst gewijzigd {date_nl(p["modified"])}</p></div></section>'
        page(page_name(slug), f"{title} – Bureau DFO", text_of(body_html)[:155] or title, body)

    # overzicht van de overgenomen pagina's
    lst = "".join(f'<a class="card" href="{page_name(p["slug"])}"><span class="tag">dfobv.nl/{E(p["slug"])}</span><h3>{E(u(p["title"]["rendered"]) or p["slug"])}</h3><span class="more arrow">Bekijken </span></a>'
                  for p in PAGES if (ROOT / page_name(p["slug"])).exists())
    page("info.html", "Pagina’s van www.dfobv.nl – Bureau DFO", "Alle informatiepagina’s van www.dfobv.nl.",
         hero("Pagina’s van www.dfobv.nl", "Alle informatiepagina’s die van www.dfobv.nl zijn overgenomen.", crumbs=["dfobv.nl"]) +
         f'<section><div class="wrap"><div class="grid g3">{lst}</div><p class="muted" style="margin-top:20px">Zie ook: <a href="artikelen.html">artikelen</a>, <a href="webshop.html">webshop</a> en <a href="agenda-archief.html">agenda-archief</a>.</p></div></section>')

    # ---------------- artikelen
    posts = sorted(POSTS, key=lambda p: p["date"], reverse=True)
    cards = []
    for p in posts:
        slug, title = p["slug"], u(p["title"]["rendered"])
        cats = terms(p) or ["Artikel"]
        img = featured(p)
        body_html = clean(p["content"]["rendered"])
        # de 'De mening van'-berichten bestaan uit een quote + afbeelding met pdf
        body = hero(E(title), E(text_of(p["excerpt"]["rendered"])[:220]), crumbs=['<a href="artikelen.html">Artikelen</a>', E(title)])
        body += f'''<section><div class="wrap"><article class="article wp">
<span class="kicker" style="color:var(--blue)">{E(" · ".join(cats))} · {date_nl(p["date"])}</span>
{body_html}
<div class="btns" style="margin-top:28px"><a class="btn btn-ghost arrow" href="artikelen.html">Alle artikelen</a></div>
</article></div></section>'''
        page(f"artikel-{slug}.html", f"{title} – Bureau DFO", text_of(p["excerpt"]["rendered"])[:155] or title, body)
        cards.append({"u": f"artikel-{slug}.html", "t": title, "d": p["date"][:10], "dn": date_nl(p["date"]),
                      "c": cats, "x": text_of(p["excerpt"]["rendered"])[:220], "i": local_img(img, 600) if img else ""})
    allcats = sorted({c for x in cards for c in x["c"]})
    chips = '<button class="chip" data-c="" aria-pressed="true">Alle</button>' + "".join(
        f'<button class="chip" data-c="{E(c)}" aria-pressed="false">{E(c)}</button>' for c in allcats)
    body = hero("Artikelen &amp; opinie", f"{len(cards)} columns, opiniestukken en nieuwsberichten van Bureau DFO, overgenomen van www.dfobv.nl.",
                crumbs=["Artikelen"])
    body += f'''<section><div class="wrap">
<div class="chips" id="ac">{chips}</div>
<div class="filters"><input type="search" id="aq" placeholder="Zoek in artikelen…" aria-label="Zoek artikel"></div>
<div class="count" id="acnt"></div><div class="grid g3" id="alist"></div>
<p class="muted" style="margin-top:22px">Zie ook de <a href="columns.html">columns van Jurjen Oosterbaan</a> en <a href="de-mening-van.html">De mening van</a>.</p>
</div></section>'''
    js = """<script>
const A=__A__;let ac='';const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function r(){const q=document.getElementById('aq').value.toLowerCase().split(/\\s+/).filter(Boolean);
const x=A.filter(a=>(!ac||a.c.includes(ac))&&q.every(w=>(a.t+' '+a.x).toLowerCase().includes(w)));
document.getElementById('acnt').textContent=x.length+' artikelen';
document.getElementById('alist').innerHTML=x.map(a=>`<a class="card${a.i?' img':''}" href="${a.u}">${a.i?`<div class="ph"><img src="${a.i}" alt="" loading="lazy"></div><div class="body">`:''}<span class="tag">${esc(a.c.join(' · '))}</span><h3>${esc(a.t)}</h3><p class="muted" style="font-size:.85rem">${a.dn}</p><p>${esc(a.x)}</p><span class="more arrow">Lees meer </span>${a.i?'</div>':''}</a>`).join('');}
document.querySelectorAll('#ac .chip').forEach(b=>b.onclick=()=>{ac=b.dataset.c;document.querySelectorAll('#ac .chip').forEach(y=>y.setAttribute('aria-pressed',y===b));r();});
document.getElementById('aq').oninput=r;r();
</script>""".replace("__A__", json.dumps(cards, ensure_ascii=False))
    page("artikelen.html", "Artikelen & opinie – Bureau DFO", "Columns, opiniestukken en nieuws van Bureau DFO.", body, scripts=js)

    # ---------------- webshop-catalogus
    catmap = {c["id"]: c for c in CATS}
    prods = []
    for p in PRODUCTS:
        slug, name = p["slug"], u(p["name"])
        pr = p["prices"]
        minor = int(pr.get("currency_minor_unit", 2))
        price = euro(pr["price"], minor) if pr.get("price") not in (None, "") else ""
        regular = euro(pr["regular_price"], minor) if pr.get("regular_price") and pr.get("regular_price") != pr.get("price") else ""
        suffix = "excl. btw" if "excl" in (p.get("price_html") or "") else ("incl. btw" if "incl" in (p.get("price_html") or "") else "")
        cats = [u(c["name"]) for c in p.get("categories", [])]
        cslugs = [c["slug"] for c in p.get("categories", [])]
        # ook de bovenliggende categorieën, zodat filteren op bijv. 'hypotheken' alle subcategorieën meeneemt
        bysl = {c["slug"]: c for c in CATS}
        extra = []
        for cs in cslugs:
            par = bysl.get(cs, {}).get("parent")
            while par:
                pc = catmap.get(par)
                if not pc:
                    break
                extra.append(pc["slug"]); par = pc.get("parent")
        allslugs = cslugs + [x for x in extra if x not in cslugs]
        img = p["images"][0] if p.get("images") else None
        thumb = local_img(img["thumbnail"], 500) if img else ""
        big = local_img(img["src"], 900) if img else ""
        short = clean(p.get("short_description", ""))
        desc = clean(p.get("description", ""))
        prods.append({"s": slug, "t": name, "p": price, "r": regular, "x": suffix, "c": cats, "cs": allslugs, "i": thumb,
                      "k": text_of(p.get("short_description", ""))[:200], "sku": p.get("sku", "")})
        catlinks = " ".join(f'<a class="tag" href="webshop.html#{E(cs)}">{E(c)}</a>' for c, cs in zip(cats, cslugs))
        pricehtml = (f'<div class="amount">{E(price)} <small>{E(suffix)}</small></div>' if price else "") + \
                    (f'<p class="fine">Normale prijs {E(regular)}</p>' if regular else "")
        body = hero(E(name), "", crumbs=['<a href="webshop.html">Webshop</a>', E(name)])
        body += f'''<section><div class="wrap split" style="align-items:start">
<div>{f'<div class="media"><img src="{E(big)}" alt="" loading="lazy"></div>' if big else ''}</div>
<div class="card price"><div>{catlinks}</div><h2 style="font-size:1.4rem;margin-top:10px">{E(name)}</h2>{pricehtml}
<div class="prose wp">{short}</div>
<div class="btns"><a class="btn btn-primary arrow" href="{E(p["permalink"])}" rel="noopener">Bestellen in de webshop</a></div>
<p class="fine" style="font-size:.8rem;color:var(--muted)">Artikelnummer {E(p.get("sku",""))}. Bestellen en betalen gaat via de webshop op dfobv.nl.</p></div>
</div></section>
{f'<section class="alt"><div class="wrap"><div class="prose wp"><h2>Omschrijving</h2>{desc}</div></div></section>' if text_of(desc) else ''}'''
        page(f"product-{slug}.html", f"{name} – Webshop Bureau DFO", (text_of(p.get("short_description", "")) or name)[:155], body)
    used = {}
    for x in prods:
        for cs in x["cs"]:
            c = next((u(cc["name"]) for cc in CATS if cc["slug"] == cs), cs)
            used[cs] = c
    used.pop("geen-categorie", None)
    chips = '<button class="chip" data-c="" aria-pressed="true">Alle</button>' + "".join(
        f'<button class="chip" data-c="{E(cs)}" aria-pressed="false">{E(c)}</button>' for cs, c in sorted(used.items(), key=lambda kv: kv[1].lower()))
    body = hero("Webshop", f"{len(prods)} producten van Bureau DFO: modeldocumenten, opleidingen, rapporten en abonnementen. Bestellen gaat via de webshop op dfobv.nl.",
                crumbs=["Webshop"], btns='<a class="btn btn-light arrow" href="https://www.dfobv.nl/winkelwagen/" rel="noopener">Winkelwagen</a><a class="btn btn-ghost" href="https://www.dfobv.nl/mijn-account/" rel="noopener">Mijn account</a>')
    body += f'''<section><div class="wrap">
<div class="filters"><input type="search" id="wq" placeholder="Zoek product, bijv. ‘dienstenwijzer’ of ‘AOV’…" aria-label="Zoek product">
<select id="ws" aria-label="Sorteren"><option value="t">Naam A–Z</option><option value="pa">Prijs laag–hoog</option><option value="pd">Prijs hoog–laag</option></select></div>
<details class="card" style="padding:14px 18px;margin-bottom:18px"><summary style="font-weight:600;cursor:pointer">Categorieën</summary><div class="chips" id="wc" style="margin:12px 0 0">{chips}</div></details>
<div class="count" id="wcnt"></div><div class="grid g4" id="wlist"></div>
</div></section>'''
    js = """<script>
const P=__P__;let wc=location.hash.slice(1);const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const num=p=>parseFloat((p.p||'0').replace(/[^0-9,]/g,'').replace(',','.'))||0;
function r(){const q=document.getElementById('wq').value.toLowerCase().split(/\\s+/).filter(Boolean),so=document.getElementById('ws').value;
let x=P.filter(p=>(!wc||p.cs.includes(wc))&&q.every(w=>(p.t+' '+p.k+' '+p.c.join(' ')+' '+p.sku).toLowerCase().includes(w)));
x.sort(so==='t'?(a,b)=>a.t.localeCompare(b.t,'nl'):so==='pa'?(a,b)=>num(a)-num(b):(a,b)=>num(b)-num(a));
document.getElementById('wcnt').textContent=x.length+' producten';
document.getElementById('wlist').innerHTML=x.map(p=>`<a class="card img" href="product-${p.s}.html"><div class="ph">${p.i?`<img src="${p.i}" alt="" loading="lazy">`:''}</div><div class="body"><span class="tag">${esc(p.c[0]||'')}</span><h3 style="font-size:1rem">${esc(p.t)}</h3><p style="font-size:.85rem">${esc(p.k)}</p><div style="margin-top:auto;font-weight:700">${esc(p.p)} <small class="muted" style="font-weight:400">${esc(p.x)}</small></div></div></a>`).join('');
document.querySelectorAll('#wc .chip').forEach(y=>y.setAttribute('aria-pressed',y.dataset.c===wc));}
document.querySelectorAll('#wc .chip').forEach(b=>b.onclick=()=>{wc=b.dataset.c;history.replaceState(null,'',wc?'#'+wc:location.pathname);r();});
document.getElementById('wq').oninput=r;document.getElementById('ws').onchange=r;r();
</script>""".replace("__P__", json.dumps(prods, ensure_ascii=False))
    page("webshop.html", "Webshop – Bureau DFO", "Alle producten van Bureau DFO: modeldocumenten, opleidingen, rapporten en abonnementen.", body, scripts=js)

    # ---------------- agenda-archief
    evs = sorted(EVENTS, key=lambda e: e.get("d", ""), reverse=True)
    (ROOT / "assets" / "dfobv").mkdir(parents=True, exist_ok=True)
    (ROOT / "assets/dfobv/agenda-archief.json").write_text(json.dumps(evs, ensure_ascii=False))
    years = sorted({e["d"][:4] for e in evs if e.get("d")}, reverse=True)
    yopts = '<option value="">Alle jaren</option>' + "".join(f"<option>{y}</option>" for y in years)
    body = hero("Agenda-archief", f"Alle {len(evs)} bijeenkomsten, opleidingen en evenementen uit de agenda van www.dfobv.nl. Voor actuele data: zie de <a href=\"opleidingen.html#agenda\" style=\"color:#fff\">agenda opleidingen</a>.",
                crumbs=["Agenda-archief"])
    body += f'''<section><div class="wrap" style="max-width:960px">
<div class="filters"><input type="search" id="eq" placeholder="Zoek op titel, plaats of onderwerp…" aria-label="Zoek in agenda-archief"><select id="ey" aria-label="Jaar">{yopts}</select></div>
<div class="count" id="ecnt"></div><div class="list" id="elist"></div>
<div class="btns" style="justify-content:center;margin-top:18px"><button class="btn btn-ghost" id="emore" type="button">Meer tonen</button></div>
</div></section>'''
    js = """<script>
let EV=[],lim=60;const M=['jan','feb','mrt','apr','mei','jun','jul','aug','sep','okt','nov','dec'];
const esc=s=>String(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function r(){const q=document.getElementById('eq').value.toLowerCase().split(/\\s+/).filter(Boolean),y=document.getElementById('ey').value;
const x=EV.filter(e=>(!y||(e.d||'').startsWith(y))&&q.every(w=>(e.t+' '+(e.l||'')+' '+(e.x||'')).toLowerCase().includes(w)));
document.getElementById('ecnt').textContent=x.length+' bijeenkomsten';document.getElementById('emore').hidden=x.length<=lim;
document.getElementById('elist').innerHTML=x.slice(0,lim).map(e=>{const d=e.d?new Date(e.d+'T12:00'):null;
return `<details class="date" style="display:block"><summary style="display:grid;grid-template-columns:76px 1fr;gap:18px;align-items:center;cursor:pointer;list-style:none">
<div class="d">${d?`<b>${d.getDate()}</b><span>${M[d.getMonth()]} ${d.getFullYear()}</span>`:'<span>–</span>'}</div>
<div><div class="t">${esc(e.t)}</div><div class="m">${esc([e.tm,e.l].filter(Boolean).join(' · '))}</div></div></summary>
<div class="prose" style="padding:12px 0 6px 94px;font-size:.93rem">${(e.x||'').split('\\n').filter(Boolean).map(p=>`<p>${esc(p)}</p>`).join('')}<p><a href="${esc(e.u)}" rel="noopener">Originele agendapagina</a></p></div></details>`}).join('')||'<div class="empty">Niets gevonden.</div>';}
fetch('assets/dfobv/agenda-archief.json').then(r=>r.json()).then(d=>{EV=d;r();});
document.getElementById('eq').oninput=()=>{lim=60;r()};document.getElementById('ey').onchange=()=>{lim=60;r()};
document.getElementById('emore').onclick=()=>{lim+=120;r()};
</script>"""
    page("agenda-archief.html", "Agenda-archief – Bureau DFO", "Archief van alle bijeenkomsten en evenementen van Bureau DFO.", body, scripts=js)
    return {"pages": len(PAGE_SLUGS), "posts": len(cards), "products": len(prods), "events": len(evs)}


def download_images():
    from PIL import Image
    import io, urllib.request
    IMGDIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for url, (rel, maxw) in IMGQ.items():
        dst = ROOT / rel
        if dst.exists():
            continue
        try:
            from urllib.parse import quote
            req = urllib.request.Request(quote(url, safe=":/%?=&#"), headers={"User-Agent": "Mozilla/5.0 (DFO site migratie)"})
            data = urllib.request.urlopen(req, timeout=40).read()
            im = Image.open(io.BytesIO(data))
            if im.mode in ("RGBA", "P", "LA"):
                im = im.convert("RGBA")
                bg = Image.new("RGB", im.size, (255, 255, 255))
                bg.paste(im, mask=im.split()[3])
                im = bg
            im = im.convert("RGB")
            if im.width > maxw:
                im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
            im.save(dst, "JPEG", quality=78, optimize=True, progressive=True)
            n += 1
        except Exception as ex:
            print("img fout", url, ex)
    return n
