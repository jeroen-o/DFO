"""Deelafbeeldingen (Open Graph) per pagina voor LinkedIn, WhatsApp, Facebook en X.

1200x630 JPEG in DFO-huisstijl: logo, soort pagina, titel, korte omschrijving en waar mogelijk een foto
(trainerportret, productafbeelding of de afbeelding uit de paginakop). Alleen opnieuw gemaakt als de inhoud verandert.
"""
import hashlib, json, re, html
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
OUT = ROOT / "assets" / "og"
F = SRC / "fonts"
W, H = 1200, 630
VERSIE = "4"


def font(w, size):
    return ImageFont.truetype(str(F / f"Poppins-{w}.ttf"), size)


def wrap(draw, text, fnt, maxw, maxlines):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = wd
            if len(lines) == maxlines:
                break
    if cur and len(lines) < maxlines:
        lines.append(cur)
    if len(lines) == maxlines and " ".join(lines) != " ".join(words):
        last = lines[-1]
        while draw.textlength(last + "…", font=fnt) > maxw and " " in last:
            last = last.rsplit(" ", 1)[0]
        lines[-1] = last.rstrip(",.;:–-") + "…"
    return lines


def achtergrond():
    g = Image.new("RGB", (W, H))
    px = g.load()
    for x in range(W):
        t = x / W
        c = (int(9 + (0 - 9) * t), int(44 + (94 - 44) * t), int(84 + (169 - 84) * t))
        for y in range(H):
            px[x, y] = c
    # zachte lichtvlek rechtsboven
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((760, -260, 1400, 380), fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    g = Image.composite(Image.new("RGB", (W, H), (60, 140, 210)), g, glow)
    return g


_BG = None
_LOGO = None


def maak(pad, titel, kicker, sub, foto=None, rond=False):
    global _BG, _LOGO
    if _BG is None:
        _BG = achtergrond()
        lg = Image.open(ROOT / "assets/img/logo.png").convert("RGBA")
        lw = 300
        _LOGO = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
    im = _BG.copy()
    d = ImageDraw.Draw(im)
    # logo op wit label
    pad_ = 18
    box = (56, 48, 56 + _LOGO.width + 2 * pad_, 48 + _LOGO.height + 2 * pad_)
    d.rounded_rectangle(box, 16, fill=(255, 255, 255))
    im.paste(_LOGO, (56 + pad_, 48 + pad_), _LOGO)
    tekstbreedte = 1088
    if foto and Path(foto).exists():
        try:
            f = Image.open(foto).convert("RGB")
            if rond:
                s = 330
                f = f.resize((s, int(f.height * s / f.width)), Image.LANCZOS) if f.width != f.height else f.resize((s, s), Image.LANCZOS)
                f = f.crop((0, 0, s, s))
                m = Image.new("L", (s, s), 0)
                ImageDraw.Draw(m).ellipse((0, 0, s, s), fill=255)
                x, y = W - s - 70, (H - s) // 2 + 20
                d.ellipse((x - 8, y - 8, x + s + 8, y + s + 8), fill=(255, 255, 255))
                im.paste(f, (x, y), m)
                tekstbreedte = x - 56 - 50
            else:
                bw, bh = 420, 315
                r = max(bw / f.width, bh / f.height)
                f = f.resize((int(f.width * r + 1), int(f.height * r + 1)), Image.LANCZOS)
                f = f.crop(((f.width - bw) // 2, (f.height - bh) // 2, (f.width - bw) // 2 + bw, (f.height - bh) // 2 + bh))
                m = Image.new("L", (bw, bh), 0)
                ImageDraw.Draw(m).rounded_rectangle((0, 0, bw, bh), 22, fill=255)
                x, y = W - bw - 60, (H - bh) // 2 + 30
                im.paste(f, (x, y), m)
                tekstbreedte = x - 56 - 40
        except Exception:
            pass
    y = 200
    if kicker:
        d.text((56, y), kicker.upper(), font=font("bold", 24), fill=(147, 197, 253))
        y += 46
    tf = font("bold", 58 if len(titel) < 40 else 50 if len(titel) < 70 else 44)
    for ln in wrap(d, titel, tf, tekstbreedte, 3):
        d.text((56, y), ln, font=tf, fill=(255, 255, 255))
        y += int(tf.size * 1.22)
    if sub and y < 470:
        sf = font("regular", 25)
        for ln in wrap(d, sub, sf, tekstbreedte, 2 if y < 420 else 1):
            d.text((56, y + 10), ln, font=sf, fill=(219, 234, 254))
            y += 36
    d.text((56, H - 64), "Bureau DFO · dienstverlening voor financiële ondernemers", font=font("medium", 22), fill=(191, 219, 254))
    im.save(pad, "JPEG", quality=80, optimize=True, progressive=True)


def voor_pagina(fname, raw, titel, desc, producten):
    """Bepaalt inhoud van de deelafbeelding en maakt die (indien gewijzigd). Geeft het relatieve pad terug."""
    OUT.mkdir(parents=True, exist_ok=True)
    titel = re.sub(r"\s+–\s+(Bureau DFO|Webshop Bureau DFO|trainer en docent)$", "", titel).strip()
    titel = re.sub(r"\s+–\s+Bureau DFO$", "", titel)
    sub = re.sub(r"\s+", " ", desc or "")[:170]
    foto, rond, kicker = None, False, ""
    if fname.startswith("trainer-"):
        m = re.search(r'<img class="tr-foto tr-groot" src="([^"]+)"', raw)
        foto, rond = (ROOT / m.group(1)) if m else None, True
        tags = re.findall(r'<div class="tr-side">.*?</div>', raw, re.S)
        rollen = re.findall(r'<span class="tag[^"]*">(.*?)</span>', tags[0]) if tags else []
        kicker = " · ".join(html.unescape(r) for r in rollen[:2]) or "Trainer"
        h1 = re.search(r"<h1>(.*?)</h1>", raw, re.S)
        titel = html.unescape(h1.group(1)) if h1 else titel
        lead = re.search(r'<p class="lead">(.*?)</p>', raw, re.S)
        sub = html.unescape(lead.group(1)) if lead else sub
    elif fname.startswith("product-"):
        p = producten.get(fname[8:-5])
        kicker = "Webshop Bureau DFO"
        if p:
            titel = p["t"]
            if p.get("i"):
                foto = ROOT / p["i"]
            prijs = (p.get("p") or "") + (" " + p["x"] if p.get("x") and p.get("p") != "Gratis" else "")
            sub = (prijs + " · " if prijs.strip() else "") + sub
    else:
        if fname.startswith("artikel-"):
            kicker = "Artikel"
        elif fname.startswith(("wft", "bgfo", "trhk", "wetgeving", "fin-")):
            kicker = "Wet- en regelgeving"
        elif fname.startswith("info-"):
            kicker = "Bureau DFO"
        else:
            cr = re.search(r'<div class="crumbs">(.*?)</div>', raw, re.S)
            kicker = html.unescape(re.sub(r"<[^>]+>", "", cr.group(1)).split(" › ")[-1]) if cr else "Bureau DFO"
            if kicker.lower() == titel.lower():
                kicker = "Bureau DFO"
        m = re.search(r'<section class="hero[^"]*">.*?<div class="img"><img src="([^"]+)"', raw, re.S)
        if m and not m.group(1).startswith("http"):
            foto = ROOT / m.group(1)
        if fname == "index.html":
            titel, kicker = "Bureau DFO", "Sinds 1992 · Hoevelaken"
            sub = "Opleidingen, modeldocumenten, compliance, onderzoek en kennis voor financieel adviseurs en financiële ondernemers."
            foto = ROOT / "assets/img/pand.jpg"
    sub = sub.strip()
    if sub and not re.search(r"[.!?…)]$", sub):  # afgekapte omschrijving netjes afsluiten
        sub = sub.rsplit(" ", 1)[0].rstrip(",;:–-") + "…"
    rel = f"assets/og/{fname[:-5]}.jpg"
    key = hashlib.md5(json.dumps([VERSIE, titel, kicker, sub, str(foto), (foto.stat().st_mtime if foto and foto.exists() else 0)]).encode()).hexdigest()
    cache_f = SRC / "seo" / "og.json"
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    if cache.get(fname) != key or not (ROOT / rel).exists():
        maak(ROOT / rel, titel, kicker, sub, foto, rond)
        cache[fname] = key
        cache_f.write_text(json.dumps(cache, indent=0, sort_keys=True))
    return rel, titel
