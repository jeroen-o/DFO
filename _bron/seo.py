"""SEO en GEO (vindbaarheid in zoekmachines en AI-assistenten) voor alle gegenereerde pagina's.

Draait als laatste stap van build.py en voegt toe:
  - canonical, og:url, og:image, og:locale, twitter-card en robots-meta per pagina;
  - JSON-LD (schema.org): Organization + WebSite (zoekfunctie) + WebPage + BreadcrumbList op elke pagina,
    plus per paginasoort Product, Course, EducationEvent, Article, FAQPage, DefinedTermSet, Legislation en ItemList;
  - sitemap.xml (met lastmod die alleen verandert als de inhoud verandert), robots.txt, llms.txt en llms-full.txt.

BASE is het adres waarop de site draait. Pas dit aan bij de overstap naar het definitieve domein.
"""
import json, re, html, hashlib, datetime
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
BASE = "https://jeroen-o.github.io/DFO/"
E = html.escape
NOINDEX = {"404.html", "zoeken.html"}
MAAND = {m: i + 1 for i, m in enumerate(["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"])}

ORG = {
    "@type": ["Organization", "EducationalOrganization"], "@id": BASE + "#org", "name": "Bureau DFO", "legalName": "Bureau DFO B.V.",
    "description": "Dienstverlening voor financiële ondernemers: opleidingen, modeldocumenten, compliance, onderzoek en kennis voor financieel adviseurs.",
    "url": BASE, "logo": BASE + "assets/img/logo.png", "image": BASE + "assets/img/og-dfo.jpg",
    "telephone": "+31332580460", "email": "info@dfobv.nl",
    "address": {"@type": "PostalAddress", "streetAddress": "De Wel 14-16", "postalCode": "3871 MV", "addressLocality": "Hoevelaken", "addressCountry": "NL"},
    "sameAs": ["https://www.dfobv.nl/", "https://www.linkedin.com/company/bureaudfo", "https://twitter.com/BureauDFO", "https://www.dfosignalen.nl/",
               "https://sp.dfobv.nl/", "https://www.dfonazorg.nl/", "https://www.dfo-opleidingen.nl/", "https://pa-wft.nl/", "https://ai-permanent-actueel.nl/",
               "https://www.amersfoort-vergaderruimte.nl/"],
}
WEBSITE = {"@type": "WebSite", "@id": BASE + "#site", "url": BASE, "name": "Bureau DFO", "inLanguage": "nl-NL", "publisher": {"@id": BASE + "#org"},
           "potentialAction": {"@type": "SearchAction", "target": {"@type": "EntryPoint", "urlTemplate": BASE + "zoeken.html?q={search_term_string}"},
                               "query-input": "required name=search_term_string"}}


def euro(s):
    m = re.search(r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:,\d{2})?)", s or "")
    if not m:
        return None
    return round(float(m.group(1).replace(".", "").replace(",", ".")), 2)


def txt(s, n=300):
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


def meta(raw, name):
    m = re.search(rf'<meta (?:name|property)="{re.escape(name)}" content="([^"]*)"', raw)
    return html.unescape(m.group(1)) if m else ""


def crumbs(raw, fname, title):
    m = re.search(r'<div class="crumbs">(.*?)</div>', raw, re.S)
    items = []
    if m:
        parts = m.group(1).split(" › ")
        for p in parts:
            a = re.search(r'href="([^"]+)"[^>]*>(.*?)</a>', p)
            if a:
                items.append((txt(a.group(2), 80), BASE + ("" if a.group(1) == "index.html" else a.group(1))))
            else:
                items.append((txt(p, 80), BASE + fname))
    if not items:
        return None
    return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}


def nl_date(s):
    m = re.search(r"(\d{1,2}) (januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december) (\d{4})", s or "")
    return f"{m.group(3)}-{MAAND[m.group(2)]:02d}-{int(m.group(1)):02d}" if m else None


def place(loc):
    return {"@type": "Place", "name": loc or "Bureau DFO",
            "address": {"@type": "PostalAddress", "addressLocality": "Hoevelaken" if not loc or "hoevelaken" in loc.lower() else loc, "addressCountry": "NL",
                        **({"streetAddress": "De Wel 14-16", "postalCode": "3871 MV"} if not loc or "hoevelaken" in loc.lower() else {})}}


def specifiek(fname, raw, ctx, page_url):
    """Extra schema.org-objecten per paginasoort."""
    out = []
    P = ctx["producten"]
    if fname.startswith("product-"):
        p = P.get(fname[8:-5])
        if p:
            prijs = euro(p["p"])
            prod = {"@type": "Product", "@id": page_url + "#product", "name": p["t"], "description": txt(p.get("k"), 500) or txt(meta(raw, "description")),
                    "sku": p.get("sku") or p["s"], "brand": {"@id": BASE + "#org"}, "category": ", ".join(p.get("c", [])),
                    "url": page_url}
            if p.get("i"):
                prod["image"] = BASE + p["i"]
            order = re.search(r'href="(https://www\.dfobv\.nl/product/[^"]+)"[^>]*>Bestellen in de webshop', raw)
            if prijs is not None:
                prod["offers"] = {"@type": "Offer", "price": f"{prijs:.2f}", "priceCurrency": "EUR", "availability": "https://schema.org/InStock",
                                  "url": order.group(1) if order else page_url, "seller": {"@id": BASE + "#org"},
                                  "priceSpecification": {"@type": "UnitPriceSpecification", "price": f"{prijs:.2f}", "priceCurrency": "EUR",
                                                         "valueAddedTaxIncluded": "excl" not in (p.get("x") or "").lower()}}
            elif (p.get("p") or "").lower().startswith("gratis"):
                prod["offers"] = {"@type": "Offer", "price": "0", "priceCurrency": "EUR", "availability": "https://schema.org/InStock", "url": page_url}
            out.append(prod)
    elif fname == "opleidingen.html":
        courses = []
        for c in ctx["cursussen"]:
            co = {"@type": "Course", "name": c["t"], "description": txt(c["s"] or f'{c["type"]} {c["wg"]}', 400) or c["t"], "url": c["u"],
                  "provider": {"@id": BASE + "#org"}, "inLanguage": "nl", "educationalLevel": "Professioneel", "about": c["wg"] or c["cat"]}
            pr = euro(c["prijs"])
            if pr is not None:
                co["offers"] = {"@type": "Offer", "price": f"{pr:.2f}", "priceCurrency": "EUR", "category": "Paid", "url": c["u"]}
            co["hasCourseInstance"] = [{"@type": "CourseInstance", "courseMode": "Onsite", "startDate": a["d"], "location": place(a["loc"])}
                                       for a in ctx["agenda"] if a["u"] == c["u"]][:5] or [{"@type": "CourseInstance", "courseMode": "Blended", "courseWorkload": c["type"] or "Training"}]
            courses.append(co)
        out.append({"@type": "ItemList", "name": "Opleidingen van Bureau DFO", "numberOfItems": len(courses),
                    "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": c} for i, c in enumerate(courses)]})
        today = datetime.date.today().isoformat()
        for a in ctx["agenda"]:
            if a["d"] >= today:
                ev = {"@type": "EducationEvent", "name": a["t"], "startDate": a["d"], "eventStatus": "https://schema.org/EventScheduled",
                      "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode", "location": place(a["loc"]), "organizer": {"@id": BASE + "#org"}, "url": a["u"]}
                pr = euro(a.get("prijs"))
                if pr is not None:
                    ev["offers"] = {"@type": "Offer", "price": f"{pr:.2f}", "priceCurrency": "EUR", "url": a["u"], "availability": "https://schema.org/InStock"}
                if a.get("doc"):
                    ev["performer"] = {"@type": "Person", "name": a["doc"]}
                out.append(ev)
        for x in ctx["nvhp"]:
            nd = x.get("next")
            if nd:
                out.append({"@type": "EducationEvent", "name": "NVHP-masterclass: " + x["t"], "startDate": nd["d"], "eventStatus": "https://schema.org/EventScheduled",
                            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode", "location": place(nd.get("loc")),
                            "organizer": {"@type": "Organization", "name": "NVHP – Nederlandse Vereniging van Hypothecair Planners", "url": "https://www.hypothecairplanner.nl/"},
                            "url": x["u"], **({"offers": {"@type": "Offer", "price": f"{euro(x['prijs']):.2f}", "priceCurrency": "EUR", "url": x["u"]}} if euro(x["prijs"]) is not None else {})})
    elif fname.startswith("artikel-") or fname.startswith("column"):
        h1 = re.search(r"<h1>(.*?)</h1>", raw, re.S)
        k = re.search(r'<span class="kicker"[^>]*>(.*?)</span>', raw, re.S)
        art = {"@type": "Article", "headline": txt(h1.group(1) if h1 else "", 110), "description": meta(raw, "description"), "inLanguage": "nl-NL",
               "publisher": {"@id": BASE + "#org"}, "mainEntityOfPage": page_url, "image": BASE + "assets/img/og-dfo.jpg",
               "author": {"@type": "Person", "name": "Jurjen Oosterbaan"} if "column" in fname or "jurjen" in fname else {"@id": BASE + "#org"}}
        d = nl_date(txt(k.group(1)) if k else "") or nl_date(raw[:20000])
        if d:
            art["datePublished"] = d
        out.append(art)
    elif fname == "wft-bieb.html":
        faq = re.findall(r'<details class="wb-det"><summary>(.*?)</summary><p>(.*?)</p></details>', raw[raw.find('id="faq"'):], re.S)
        if faq:
            out.append({"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": txt(q), "acceptedAnswer": {"@type": "Answer", "text": txt(a, 1000)}} for q, a in faq]})
        wet = re.findall(r'<article class="wb-card"[^>]*>.*?<h3>(.*?)</h3><p>(.*?)</p><p class="wb-links">(?:<a class="more arrow" href="([^"]+)")?', raw, re.S)
        out.append({"@type": "ItemList", "name": "Wet- en regelgeving voor financiële dienstverleners", "numberOfItems": len(wet),
                    "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@type": "Legislation", "name": txt(t), "description": txt(d),
                                         "legislationJurisdiction": "NL", **({"url": u if u.startswith("http") else BASE + u} if u else {})}} for i, (t, d, u) in enumerate(wet)]})
    elif fname == "kennisbank.html":
        terms = re.findall(r'<article class="kb-item" id="([^"]+)"[^>]*><div class="kb-head"><h3>(.*?)</h3>.*?</div><p>(.*?)</p>', raw, re.S)
        out.append({"@type": "DefinedTermSet", "@id": page_url + "#begrippen", "name": "Kennisbank Bureau DFO", "inLanguage": "nl-NL",
                    "hasDefinedTerm": [{"@type": "DefinedTerm", "@id": page_url + "#" + i, "name": txt(re.sub(r'<span class="kb-afk">.*?</span>', "", h)),
                                        **({"termCode": txt(re.search(r'kb-afk">\((.*?)\)', h).group(1))} if 'kb-afk' in h else {}),
                                        "description": txt(d, 220), "inDefinedTermSet": page_url + "#begrippen"} for i, h, d in terms]})
    elif fname.startswith("trainer-"):
        h1 = re.search(r"<h1>(.*?)</h1>", raw, re.S)
        img = re.search(r'<img class="tr-foto[^"]*" src="([^"]+)"', raw)
        bio = re.search(r'<div class="tr-main">\s*<p>(.*?)</p>', raw, re.S)
        rollen = re.findall(r'<div class="tr-side">.*?</div>', raw, re.S)
        out.append({"@type": "Person", "@id": page_url + "#persoon", "name": txt(h1.group(1)) if h1 else "",
                    "jobTitle": txt(re.search(r'<p class="lead">(.*?)</p>', raw, re.S).group(1)) if '<p class="lead">' in raw else "Trainer",
                    **({"image": BASE + img.group(1)} if img else {}), **({"description": txt(bio.group(1), 400)} if bio else {}),
                    "url": page_url, "affiliation": {"@id": BASE + "#org"},
                    "knowsAbout": [txt(t) for t in re.findall(r'<span class="tag[^"]*">(.*?)</span>', rollen[0] if rollen else "")]})
    elif fname == "trainers.html":
        ppl = re.findall(r'<a class="card tr-card" href="(trainer-[^"]+)"[^>]*>.*?<h3>(.*?)</h3>', raw, re.S)
        seen = []
        for u, n in ppl:
            if u not in [x[0] for x in seen]:
                seen.append((u, n))
        out.append({"@type": "ItemList", "name": "Trainers, docenten en dagvoorzitters", "numberOfItems": len(seen),
                    "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@type": "Person", "name": txt(n), "url": BASE + u}} for i, (u, n) in enumerate(seen)]})
    elif fname == "congressen.html":
        today = datetime.date.today().isoformat()
        for c in json.loads((SRC / "congressen.json").read_text()):
            for d in c["data"]:
                if d["d"] >= today:
                    out.append({"@type": "Event", "name": d["t"], "startDate": d["d"], "eventStatus": "https://schema.org/EventScheduled",
                                "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode" if d["loc"].lower() == "online" else "https://schema.org/OfflineEventAttendanceMode",
                                "location": {"@type": "VirtualLocation", "url": c["url"]} if d["loc"].lower() == "online" else {"@type": "Place", "name": d["loc"], "address": {"@type": "PostalAddress", "addressLocality": d["loc"].split(",")[-1].strip(), "addressCountry": "NL"}},
                                "description": txt(c["tekst"], 300), "url": c["url"], "image": BASE + c["img"], "organizer": {"@id": BASE + "#org"}})
    elif fname == "kennistoets.html":
        out.append({"@type": "Quiz", "name": "Wft-kennistoets", "about": "Wet op het financieel toezicht", "educationalLevel": "Professioneel",
                    "inLanguage": "nl-NL", "provider": {"@id": BASE + "#org"}, "url": page_url})
    elif fname in ("nieuws.html", "portalen.html", "artikelen.html", "webshop.html", "signalen.html"):
        links = re.findall(r'<(?:h3|li)[^>]*><a href="([^"]+)"[^>]*>(.*?)</a>', raw)[:60]
        if fname == "webshop.html":
            links = [(f'product-{p["s"]}.html', p["t"]) for p in list(P.values())[:100]]
        if links:
            out.append({"@type": "ItemList", "numberOfItems": len(links), "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": txt(t, 150), "url": u if u.startswith("http") else BASE + u} for i, (u, t) in enumerate(links)]})
    elif fname == "contact.html":
        out.append({"@type": "LocalBusiness", "@id": BASE + "#vestiging", "name": "Bureau DFO", "parentOrganization": {"@id": BASE + "#org"},
                    "address": ORG["address"], "telephone": ORG["telephone"], "email": ORG["email"], "image": BASE + "assets/img/pand.jpg",
                    "geo": {"@type": "GeoCoordinates", "latitude": 52.1668573, "longitude": 5.4656206}, "url": page_url})
    elif fname in ("vergadercentrum.html", "zalencentrum.html"):
        out.append({"@type": "EventVenue", "name": "DFO Vergadercentrum", "address": ORG["address"], "telephone": ORG["telephone"], "url": page_url,
                    "sameAs": ["https://www.amersfoort-vergaderruimte.nl/"], "image": BASE + "assets/img/grote-zaal.jpg"})
    return out


def og_image():
    f = ROOT / "assets/img/og-dfo.jpg"
    if f.exists():
        return
    from PIL import Image
    im = Image.open(ROOT / "assets/img/pand.jpg").convert("RGB")
    W, H = 1200, 630
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s + 1), int(im.height * s + 1)))
    im = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
    logo = Image.open(ROOT / "assets/img/logo.png").convert("RGBA")
    lw = 520; logo = logo.resize((lw, int(logo.height * lw / logo.width)))
    pad = 28
    band = Image.new("RGBA", (lw + 2 * pad, logo.height + 2 * pad), (255, 255, 255, 235))
    im.paste(band, (40, H - band.height - 40), band)
    im.paste(logo, (40 + pad, H - band.height - 40 + pad), logo)
    im.save(f, quality=85, optimize=True)


def run(ctx):
    og_image()
    lmf = SRC / "seo" / "lastmod.json"
    lmf.parent.mkdir(exist_ok=True)
    lastmod = json.loads(lmf.read_text()) if lmf.exists() else {}
    today = datetime.date.today().isoformat()
    pages = []
    for f in sorted(ROOT.glob("*.html")):
        raw = f.read_text()
        if "<head>" not in raw or 'http-equiv="refresh"' in raw:
            continue
        fname = f.name
        url = BASE + ("" if fname == "index.html" else fname)
        raw = re.sub(r'\n?<!-- seo -->.*?<!-- /seo -->', "", raw, flags=re.S)  # idempotent
        title = html.unescape(re.search(r"<title>(.*?)</title>", raw, re.S).group(1))
        if len(title) > 65 and title.endswith(" – Bureau DFO"):  # lange titel: merknaam weglaten zodat Google niet afkapt
            title = title[: -len(" – Bureau DFO")]
            raw = re.sub(r"<title>.*?</title>", "<title>" + E(title) + "</title>", raw, count=1, flags=re.S)
            raw = re.sub(r'(<meta property="og:title" content=")[^"]*(")', lambda m: m.group(1) + E(title) + m.group(2), raw, count=1)
        desc = meta(raw, "description")
        if len(desc) < 50:  # te korte of ontbrekende omschrijving aanvullen met de eerste alinea
            main = re.search(r"<main.*?</main>", raw, re.S)
            ps = [txt(x, 158) for x in re.findall(r"<p[^>]*>(.*?)</p>", main.group(0) if main else "", re.S)]
            nd = next((x for x in ps if len(x) >= 80), max(ps, key=len, default=""))
            if len(nd) > len(desc):
                raw = re.sub(r'(<meta (?:name|property)="(?:description|og:description)" content=")[^"]*(")', lambda m: m.group(1) + E(nd) + m.group(2), raw)
                desc = nd
        node_page = {"@type": "WebPage", "@id": url + "#webpage", "url": url, "name": title, "description": desc, "inLanguage": "nl-NL",
                     "isPartOf": {"@id": BASE + "#site"}, "publisher": {"@id": BASE + "#org"}}
        bc = crumbs(raw, fname, title)
        if bc:
            bc["@id"] = url + "#breadcrumb"
            node_page["breadcrumb"] = {"@id": bc["@id"]}
        graph = [ORG, WEBSITE, node_page] + ([bc] if bc else []) + specifiek(fname, raw, ctx, url)
        ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        import og
        ogimg, ogtitel = og.voor_pagina(fname, raw, title, desc, ctx["producten"])
        ogtype = "article" if fname.startswith(("artikel-", "column")) else ("profile" if fname.startswith("trainer-") else "website")
        raw = raw.replace('<meta property="og:type" content="website">', f'<meta property="og:type" content="{ogtype}">', 1)
        robots = "noindex, follow" if fname in NOINDEX else "index, follow, max-image-preview:large, max-snippet:-1"
        head = (f'\n<!-- seo --><link rel="canonical" href="{url}">\n<meta name="robots" content="{robots}">\n'
                f'<meta property="og:url" content="{url}">\n<meta property="og:site_name" content="Bureau DFO">\n<meta property="og:locale" content="nl_NL">\n'
                f'<meta property="og:image" content="{BASE}{ogimg}">\n<meta property="og:image:secure_url" content="{BASE}{ogimg}">\n<meta property="og:image:type" content="image/jpeg">\n'
                f'<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n<meta property="og:image:alt" content="{E(ogtitel)}">\n'
                f'<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:site" content="@BureauDFO">\n'
                f'<meta name="twitter:title" content="{E(title)}">\n<meta name="twitter:description" content="{E(desc)}">\n<meta name="twitter:image" content="{BASE}{ogimg}">\n'
                f'<link rel="alternate" type="text/plain" title="llms.txt" href="llms.txt">\n'
                f'<script type="application/ld+json">{ld}</script><!-- /seo -->')
        raw = raw.replace("</head>", head + "\n</head>", 1)
        f.write_text(raw)
        if fname in NOINDEX:
            continue
        main = re.search(r"<main.*?</main>", raw, re.S)
        h = hashlib.md5(re.sub(r"\s+", " ", main.group(0) if main else raw).encode()).hexdigest()
        if lastmod.get(fname, {}).get("h") != h:
            lastmod[fname] = {"h": h, "d": today}
        pages.append((fname, url, title, desc, lastmod[fname]["d"]))
    lmf.write_text(json.dumps(lastmod, indent=0, sort_keys=True))

    def prio(fn):
        if fn == "index.html":
            return "1.0"
        if fn in ("opleidingen.html", "documenten.html", "kennisbank.html", "wft-bieb.html", "compliance.html", "nieuws.html", "webshop.html", "portalen.html"):
            return "0.9"
        if fn.startswith(("product-", "artikel-", "info-")):
            return "0.5"
        return "0.7"
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for fn, url, *_, d in pages:
        sm.append(f"<url><loc>{url}</loc><lastmod>{d}</lastmod><priority>{prio(fn)}</priority></url>")
    sm.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(sm) + "\n")
    (ROOT / "robots.txt").write_text(
        "# Bureau DFO – alle zoekmachines en AI-assistenten zijn welkom\nUser-agent: *\nAllow: /\nDisallow: /_bron/\n\n"
        "# AI-crawlers expliciet toegestaan (GEO)\n" + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in
        ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "Claude-SearchBot", "PerplexityBot", "Google-Extended", "Applebot-Extended", "CCBot"])
        + f"Sitemap: {BASE}sitemap.xml\n")
    llms(pages, ctx)
    return len(pages)


def llms(pages, ctx):
    """llms.txt (kort overzicht) en llms-full.txt (alle pagina's met omschrijving) voor AI-assistenten."""
    byfn = {fn: (url, t, d) for fn, url, t, d, _ in pages}

    def ln(fn, label=None):
        if fn not in byfn:
            return ""
        url, t, d = byfn[fn]
        return f"- [{label or t.split(' – ')[0]}]({url}): {d}\n"
    kern = ["index.html", "opleidingen.html", "trainers.html", "documenten.html", "webshop.html", "compliance.html", "abonnementen.html", "kennisbank.html", "wft-bieb.html",
            "kennistoets.html", "wetgeving.html", "nieuws.html", "portalen.html", "signalen.html", "serviceproviders.html", "nazorg.html", "onderzoek.html",
            "performance.html", "vergadercentrum.html", "studio.html", "congressen.html", "secretariaten.html", "over-dfo.html", "contact.html"]
    s = (f"# Bureau DFO\n\n> Bureau DFO (Hoevelaken) ondersteunt financieel adviseurs en financiële ondernemers met opleidingen, modeldocumenten en contracten, "
         f"compliance-ondersteuning (Wft, Wwft, AVG), onderzoek, nieuwsbrieven, een kennisbank met {ctx.get('kb', 1000)}+ begrippen en de volledige Wft-, BGfo- en TRHK-teksten. "
         "Bureau DFO voert ook het secretariaat van de NVHP. Adres: De Wel 14-16, 3871 MV Hoevelaken · 033 258 04 60 · info@dfobv.nl.\n\n"
         "Informatie op deze site is algemene uitleg en geen advies; bedragen en regels wijzigen jaarlijks. Raadpleeg bij twijfel de bron (wetten.overheid.nl, AFM, Belastingdienst).\n\n"
         "## Belangrijkste pagina's\n\n" + "".join(ln(f) for f in kern) +
         "\n## Portalen van Bureau DFO\n\n- [DFO Signalen](https://www.dfosignalen.nl/): wekelijkse nieuwsbrief voor onafhankelijk financieel adviseurs\n"
         "- [Serviceproviders](https://sp.dfobv.nl/): serviceproviders vergelijken\n- [Opleidingsportaal](https://www.dfo-opleidingen.nl/): inschrijven voor opleidingen\n"
         "- [Wft Permanent Actueel](https://pa-wft.nl/): permanente educatie per Wft-module\n- [AI Permanent Actueel](https://ai-permanent-actueel.nl/): AI-geletterdheid\n"
         "- [Nazorg & Onderhoud](https://www.dfonazorg.nl/): documentatie nazorg\n- [Vergaderruimte Amersfoort](https://www.amersfoort-vergaderruimte.nl/)\n"
         f"\n## Meer\n\n- [Alle pagina's met omschrijving]({BASE}llms-full.txt)\n- [Sitemap]({BASE}sitemap.xml)\n")
    (ROOT / "llms.txt").write_text(s)
    groepen = [("Opleidingen en agenda", lambda f: f.startswith("opleiding")), ("Webshop: modeldocumenten, contracten en opleidingen", lambda f: f.startswith("product-")),
               ("Wet- en regelgeving", lambda f: f.startswith(("wft", "bgfo", "trhk", "wetgeving", "fin-"))), ("Artikelen en columns", lambda f: f.startswith(("artikel-", "column"))),
               ("Informatie", lambda f: f.startswith("info-")), ("Overige pagina's", lambda f: True)]
    done, full = set(), s.split("## Meer")[0]
    for naam, test in groepen:
        rows = [fn for fn, *_ in pages if fn not in done and test(fn)]
        if not rows:
            continue
        full += f"\n## {naam}\n\n" + "".join(ln(fn) for fn in rows)
        done |= set(rows)
    (ROOT / "llms-full.txt").write_text(full)
