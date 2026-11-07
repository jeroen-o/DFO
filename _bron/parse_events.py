"""Zet gedownloade EventON-agendapagina's van dfobv.nl om naar _bron/dfobv/events.json."""
import sys, re, json, glob, html
from bs4 import BeautifulSoup
src = sys.argv[1]
out = []
for f in sorted(glob.glob(src + "/events__*.html")):
    h = open(f, errors="ignore").read()
    s = BeautifulSoup(h, "html.parser")
    m = s.find(class_="eventon_single_event")
    if not m:
        continue
    t = m.find(class_="evcal_event_title")
    title = re.sub(r"\s+", " ", t.get_text(" ", strip=True)) if t else ""
    d = ""
    mm = re.search(r'data-time="(\d+)-', h)
    if mm:
        import datetime
        d = datetime.datetime.utcfromtimestamp(int(mm.group(1))).date().isoformat()
    else:
        mm = re.search(r"startDate'? content='(\d{4})-(\d{1,2})-(\d{1,2})", h)
        if mm:
            d = f"{mm.group(1)}-{int(mm.group(2)):02d}-{int(mm.group(3)):02d}"
    tm = m.find(class_="evo_time")
    tm = re.sub(r"\s+", " ", tm.get_text(" ", strip=True)).replace("Tijd ", "") if tm else ""
    loc = m.find(class_="evo_location_name")
    loc = re.sub(r"\s+", " ", loc.get_text(" ", strip=True)) if loc else ""
    addr = m.find(class_="evo_location_address")
    if addr:
        loc = (loc + ", " + re.sub(r"\s+", " ", addr.get_text(" ", strip=True))).strip(", ")
    de = m.find(class_="eventon_desc_in")
    paras = []
    if de:
        for p in de.find_all(["p", "li", "h2", "h3", "h4"]) or [de]:
            x = re.sub(r"\s+", " ", p.get_text(" ", strip=True))
            if x and x not in paras:
                paras.append(x)
        if not paras:
            paras = [re.sub(r"\s+", " ", de.get_text(" ", strip=True))]
    slug = f.split("events__")[-1][:-5]
    out.append({"t": title, "d": d, "tm": tm, "l": loc, "x": "\n".join(paras), "u": f"https://www.dfobv.nl/events/{slug}/"})
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=0)
print(len(out), "agenda-items;", sum(1 for e in out if e["x"]), "met omschrijving;", sum(1 for e in out if e["d"]), "met datum")
