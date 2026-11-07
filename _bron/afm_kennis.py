"""AFM-informatie voor de kennisbank: leidraden/beleidsdocumenten + AFM-onderwerpen voor adviseurs en bemiddelaars.

Bron: _bron/afm/afm-crawl.json (sector 'Adviseurs, bemiddelaars & gevolmachtigden' op afm.nl).
Per onderwerp wordt een kort citaat van de AFM-tekst opgenomen met een link naar de bron.
"""
import json, re
from pathlib import Path

SRC = Path(__file__).resolve().parent
AFM = "https://www.afm.nl"

LEIDRADEN = [
    ("Leidraad hypotheekadvisering (herzien 2026)", "Geactualiseerde leidraad van de AFM, gepubliceerd op 9 april 2026, die hypotheekadviseurs handvatten geeft om consumenten passend te adviseren over hypothecair krediet. Deze leidraad vervangt de oude leidraden, die bestonden uit zeven individuele afleveringen. Bij de herziening is ook een feedback statement gepubliceerd.",
     AFM + "/~/profmedia/files/wet-regelgeving/beleidsuitingen/leidraden/leidraad-hypotheekadvisering-herzien-2026.pdf"),
    ("Feedback statement herziene leidraad hypotheekadvisering 2026", "Reactie van de AFM op de consultatie van de herziene leidraad hypotheekadvisering; licht toe welke keuzes de AFM heeft gemaakt naar aanleiding van de ontvangen reacties.",
     AFM + "/~/profmedia/files/wet-regelgeving/beleidsuitingen/leidraden/feedback-statement-hypotheekadvies-bij-herziene-leidraad-2026.pdf"),
    ("Leidraad tweedepijler pensioenadvies (2023)", "Leidraad die richting en duidelijkheid geeft over de normen van artikel 4:23 Wft voor de advisering over tweedepijler pensioenproducten door de pensioenadviseur aan werkgevers, specifiek voor de fases inventariseren, analyseren en adviseren.",
     AFM + "/~/profmedia/files/wet-regelgeving/beleidsuitingen/leidraden/leidraad-tweedepijler-pensioenadvies-2023.pdf"),
    ("Pensioenadvies tijdens de pensioentransitie", "Publicatie van de AFM over aandachtspunten bij pensioenadvies in de periode van de overgang naar het nieuwe pensioenstelsel (Wtp).",
     AFM + "/~/profmedia/files/doelgroepen/pensioenuitvoerders/2024/pensioenadvies-tijdens-pensioentransitie.pdf"),
    ("Leidraad informatieverstrekking bij collectieve waardeoverdracht", "Leidraad over de informatie die deelnemers moeten krijgen bij een collectieve waardeoverdracht van pensioen.",
     AFM + "/~/profmedia/files/wet-regelgeving/beleidsuitingen/leidraden/leidraad-informatieverstrekking-cwo.pdf"),
    ("Leidraad advies en vermogensbeheerdienstverlening", "Geconsolideerde leidraad van de AFM over advies en vermogensbeheer, waarin eerdere leidraden over onder meer advies over vermogensopbouw, klantgericht advies en het klantprofiel zijn samengevoegd.",
     AFM + "/~/profmedia/files/wet-regelgeving/beleidsuitingen/leidraden/leidraad-advies-en-vermogensbeheerdienstverlening.pdf"),
    ("Leidraad zorgplicht bij (semi-)automatisch vermogensbeheer", "Leidraad (2018) over de invulling van de zorgplicht bij (semi-)automatisch vermogensbeheer en roboadvies, met een overzicht van de belangrijkste zorgplichtregels in de klantreis.",
     AFM + "/~/profmedia/files/onderwerpen/roboadvies-sav/leidraad-zorgplicht-semiautomatisch-vermogensbeheer.pdf"),
    ("Kwalificatie innovatieve dienstverlening", "Uitleg (2016) van de AFM over hoe innovatieve en online vormen van dienstverlening worden gekwalificeerd, zoals de vraag of sprake is van advies.",
     AFM + "/~/profmedia/files/wet-regelgeving/beleidsuitingen/leidraden/kwalificatie-innovatieve-dienstverlening.pdf"),
    ("Dienstverlening op maat (online bedieningsconcepten)", "Publicatie van de AFM over dienstverlening op maat en online bedieningsconcepten in de financiële dienstverlening.",
     AFM + "/~/profmedia/files/onderwerpen/online-dienstverlening/dom-financiele-dienstverlening.pdf"),
    ("Interpretatie informeren en adviseren", "Interpretatie (2021) van de AFM over de grens tussen informeren en adviseren.",
     AFM + "/~/profmedia/files/nieuws/2021/interpretatie-informeren-en-adviseren.pdf"),
    ("Stappenplan adviseren of bemiddelen", "Stappenplan van de AFM om te bepalen of een activiteit kwalificeert als adviseren of bemiddelen, en welke vakbekwaamheidseisen daarbij horen.",
     AFM + "/~/profmedia/files/doelgroepen/adviseurs-bemiddelaars/2016/advies-vakbekwaamheid.pdf"),
    ("Beleidsregel informatieverstrekking", "Beleidsregel van de AFM over de informatieverstrekking aan cliënten door financiële dienstverleners.",
     "https://wetten.overheid.nl/BWBR0041773/2018-12-31"),
    ("Interpretatie passende volmachtbeloning", "Interpretatie van de AFM over de norm voor een passende beloning van gevolmachtigd agenten.",
     AFM + "/~/profmedia/files/wet-regelgeving/beleidsuitingen/interpretaties/interpretatie-passende-volmachtbeloning1.pdf"),
    ("Interpretatie ontheffingsmogelijkheid serviceorganisaties (provisieverbod)", "Interpretatie van de AFM over de mogelijkheid van ontheffing van het provisieverbod voor serviceorganisaties.",
     AFM + "/~/profmedia/files/wet-regelgeving/beloningsbeleid/provisieverbod-ontheffing-serviceorganisaties.pdf"),
    ("Ontheffingsbeleid diplomaplicht", "Beleid van de AFM over ontheffing van de diplomaplicht voor medewerkers van financiële dienstverleners.",
     AFM + "/~/profmedia/files/doelgroepen/adviseurs-bemiddelaars/2024/ontheffingbeleid-diplomaplicht.pdf"),
    ("Brochure Wwft- en Sanctiewetverplichtingen", "Brochure van de AFM: voldoet u aan de verplichtingen uit de Wwft en de Sanctiewet?",
     AFM + "/~/profmedia/files/onderwerpen/wwft/brochure-wwft-sw-verplichtingen.pdf"),
    ("Handvatten als u niet meer adviseert", "Handreiking van de AFM voor financieel dienstverleners die stoppen met (een deel van) hun advies- of bemiddelingsactiviteiten.",
     AFM + "/~/profmedia/files/doelgroepen/adviseurs-bemiddelaars/2016/handvatten-als-u-niet-meer-adviseert.pdf"),
    ("Rapport hypotheekadviessoftware", "Bevindingen van de AFM uit het onderzoek naar hypotheekadviessoftware, met aandachtspunten bij het gebruik van adviessoftware bij hypotheekadvisering.",
     AFM + "/~/profmedia/files/rapporten/2011/adviessoftware.pdf"),
    ("Begrippenlijst Marktmonitor 2026", "Begrippenlijst bij de Marktmonitor 2026 die adviseurs, bemiddelaars en gevolmachtigden jaarlijks invullen.",
     AFM + "/~/profmedia/files/doelgroepen/adviseurs-bemiddelaars/2026/mmab-2026-begrippenlijst.pdf"),
]

NAV = {"Voor de Sector", "Adviseurs, bemiddelaars & gevolmachtigden", "Heb ik een vergunning nodig?", "Vergunning aanvragen of wijzigen",
       "Doorlopende eisen en bedrijfsvoering", "Marktmonitor", "Beloning", "Informatie voor gevolmachtigd agenten", "Specifieke dienstverlening",
       "Nazorg beleggingsverzekeringen", "Nationaal regime", "Consumptief krediet", "Hypothecair krediet", "Pensioenverzekeringen", "Vermogen",
       "Leidraden", "Thema's", "Toezicht", "Onderzoek"}


def intro(page):
    lines = [l.strip() for l in page["txt"].split("\n") if l.strip()]
    h1 = page["h1"].strip()
    idx = [i for i, l in enumerate(lines) if l == h1]
    start = idx[-1] + 1 if idx else 0
    out = []
    for l in lines[start:]:
        if l in NAV or l.startswith(("Relevante links", "(opens", "Meer over", "Lees ")):
            if out:
                break
            continue
        if len(l) < 40:
            if out:
                break
            continue
        out.append(l)
        if sum(len(x) for x in out) > 380:
            break
    txt = " ".join(out)
    if len(txt) > 520:
        cut = txt[:520].rsplit(". ", 1)[0]
        txt = cut + "."
    return txt


def build():
    crawl = json.loads((SRC / "afm" / "afm-crawl.json").read_text())
    items = []
    for t, d, u in LEIDRADEN:
        items.append({"term": t, "afk": "", "def": d, "zie": [], "volatiel": False, "link": u, "bron": "AFM"})
    for p in crawl:
        h1 = (p.get("h1") or "").strip()
        if not h1 or "niet gevonden" in h1.lower() or p["u"].rstrip("/").endswith("gevolmachtigde-agenten"):
            continue
        txt = intro(p)
        if len(txt) < 60:
            continue
        items.append({"term": f"AFM: {h1}", "afk": "", "def": f"“{txt}” (AFM)", "zie": [], "volatiel": True, "link": p["u"], "bron": "AFM"})
    seen, uniq = set(), []
    for it in items:
        if it["term"].lower() in seen:
            continue
        seen.add(it["term"].lower()); uniq.append(it)
    uniq.sort(key=lambda x: x["term"].lower())
    (SRC / "kennisbank" / "afm.json").write_text(json.dumps(uniq, ensure_ascii=False, indent=1))
    return len(uniq)


if __name__ == "__main__":
    print(build())
