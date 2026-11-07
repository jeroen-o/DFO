"""Zet een pagina van de oude www2-site woordelijk om naar blokken voor de nieuwe opmaak."""
import re, html
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

BRON = Path(__file__).resolve().parent / "bron-www2"

# oude interne paden -> nieuwe pagina's
LINKMAP = {
    "over-dfo/contact": "contact.html", "studio/contact": "contact.html",
    "over-dfo/ons-team": "over-dfo.html#team", "over-dfo/bureau-dfo": "over-dfo.html",
    "over-dfo/werken-bij": "over-dfo.html#werken-bij",
    "documenten-contracten": "documenten.html", "diensten/compliance": "compliance.html",
    "diensten/onze-abonnementen": "abonnementen.html", "diensten/dfo-zalencentrum": "vergadercentrum.html",
    "studio/webinar-producties": "studio-webinar.html", "studio/podcastproducties": "studio-podcast.html",
    "studio/videoproductie": "studio-video.html",
    "studio/studio-verhuur-met-technische-ondersteuning-professionele-producties-zorgeloos-geregeld": "studio-verhuur.html",
    "studio/contentmarketing-social-media-productie": "studio-contentmarketing.html",
    "studio/training-en-e-learning-modules-doelgericht-leren": "studio-elearning.html",
    "studio": "studio.html", "congressen": "congressen.html", "themas": "themas.html",
    "abonnement-dashboard/toelichting-calculator-onderhoud-en-nazorg": "nazorg-calculator.html",
    "abonnement-dashboard": "https://www2.dfobv.nl/abonnement-dashboard/",
    "zoeken": "zoeken.html", "": "index.html",
}
SKIP_TXT = {"Bureau DFO", "Jouw partner voor een beheerste en integere bedrijfsvoering", "DFO Compliance"}
FOOTER = {"Extra informatie", "Op de hoogte blijven?", "Contact"}


def maplink(href, page_rel):
    if not href:
        return "#"
    if href.startswith(("http", "mailto:", "tel:")):
        return href.replace("tel:033 258 04 60", "tel:+31332580460")
    base = Path(page_rel).parent
    anchor = ""
    if "#" in href:
        href, anchor = href.split("#", 1)
    p = (base / href).as_posix() if href else page_rel
    p = re.sub(r"(^|/)index\.html$", "", p)
    parts = []
    for seg in p.split("/"):
        if seg == "..":
            parts and parts.pop()
        elif seg and seg != ".":
            parts.append(seg)
    key = "/".join(parts)
    # documenten-subcategorie
    m = re.match(r"documenten-contracten/(.+)", key)
    if m:
        return "documenten.html#" + m.group(1)
    if key.startswith("assets/files/"):
        name = key.split("/")[-1]
        return {"vacature-secretaresse-bestuur.pdf": "assets/pdf/vacature-secretaresse-bestuur.pdf",
                "vacature-secretaresse-allround.pdf": "assets/pdf/vacature-secretaresse-allround.pdf",
                "persbericht-bureau-dfo-meedenken-met-kantoor-bepaalt-waardering-serviceproviders.pdf": "assets/pdf/persbericht-bureau-dfo-meedenken-met-kantoor-bepaalt-waardering-serviceproviders.pdf"}.get(
            name, "https://www2.dfobv.nl/" + key)
    if key.startswith("columns-jurjen-oosterbaan/"):
        return "columns.html#" + key.split("/")[-1].replace("column-jurjen-oosterbaan-", "")
    new = LINKMAP.get(key, "https://www2.dfobv.nl/" + key + "/")
    if anchor == "abonneren":
        anchor = "aanvragen"
    return new + ("#" + anchor if anchor and "#" not in new else "")


def inline(el, page_rel):
    """Inline-inhoud van een element als veilige HTML (a/strong/em/br behouden)."""
    out = []
    for c in el.children:
        if isinstance(c, NavigableString):
            out.append(html.escape(str(c)))
        elif isinstance(c, Tag):
            if c.name in ("script", "style", "img", "iframe", "ul", "ol"):
                continue
            inner = inline(c, page_rel)
            if c.name == "a":
                h = maplink(c.get("href"), page_rel)
                ext = ' rel="noopener"' if h.startswith("http") else ""
                out.append(f'<a href="{html.escape(h)}"{ext}>{inner}</a>' if inner.strip() else "")
            elif c.name in ("strong", "b"):
                out.append(f"<strong>{inner}</strong>" if inner.strip() else inner)
            elif c.name in ("em", "i"):
                out.append(f"<em>{inner}</em>" if inner.strip() else inner)
            elif c.name == "br":
                out.append("<br>")
            elif c.name == "sup":
                out.append(f"<sup>{inner}</sup>")
            else:
                out.append(inner)
    s = "".join(out).replace("\xad", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def blocks(page_rel):
    """Lijst van (soort, inhoud) in documentvolgorde. soort: h1,h2,h3,p,ul,ol,btn,img,yt"""
    s = BeautifulSoup((BRON / page_rel).read_text(), "html.parser")
    for t in s(["header", "nav", "footer", "script", "style", "noscript", "form"]):
        t.decompose()
    res, done = [], set()

    def handled(el):
        return any(id(p) in done for p in el.parents)

    for el in s.body.find_all(True):
        if handled(el):
            continue
        cls = " ".join(el.get("class") or [])
        txt = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).replace("\xad", "")
        hm = re.search(r"heading-(\d)", cls)
        if el.name in ("h1", "h2", "h3", "h4") or (el.name == "div" and hm):
            if txt in FOOTER:
                break
            done.add(id(el))
            if txt in SKIP_TXT or not txt:
                continue
            lvl = int(hm.group(1)) if hm else int(el.name[1])
            res.append(("h1" if lvl == 1 else "h2" if lvl == 2 else "h3", txt))
        elif el.name == "div" and "handler" in cls:
            done.add(id(el))
            res.append(("h3", txt))
        elif el.name == "a" and "button" in cls:
            done.add(id(el))
            if txt:
                res.append(("btn", (txt, maplink(el.get("href"), page_rel))))
        elif el.name in ("ul", "ol"):
            done.add(id(el))
            items = [inline(li, page_rel) for li in el.find_all("li", recursive=False)]
            items = [i for i in items if i]
            if items:
                res.append((el.name, items))
        elif el.name == "p":
            done.add(id(el))
            h = inline(el, page_rel)
            if h and re.sub(r"<[^>]+>", "", h).strip() not in SKIP_TXT:
                res.append(("p", h))
            for im in el.find_all("img"):
                res.append(("img", im.get("src", "")))
        elif el.name == "iframe":
            done.add(id(el))
            m = re.search(r"youtube\.com/embed/([\w-]+)", el.get("src", ""))
            if m:
                res.append(("yt", m.group(1)))
        elif el.name == "img":
            done.add(id(el))
            res.append(("img", el.get("src", "")))
    # rommel: losse "Bureau DFO"-strong koppen in p
    return res


def li_html(item):
    # "<strong>Label:</strong> tekst" of "tekst<strong>Label</strong>" -> label vooraan
    return f"<li>{item}</li>"
