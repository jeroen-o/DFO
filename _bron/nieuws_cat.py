"""Indeling nieuwsberichten in Hypotheken, Verzekeringen, Pensioenen, Kredieten, Overig (op trefwoorden)."""
import re

CATS = ["Hypotheken", "Verzekeringen", "Pensioenen", "Kredieten", "Overig"]
KW = {
    "Hypotheken": r"hypothe|mortgage|nhg|woning|huizen|huizenprijs|koopwoning|huur|huurder|vastgoed|eigen woning|overdrachtsbelasting|starter|leencapaciteit|financieringslast|ltv|loan-to-value|taxat|kadaster|bouwen|nieuwbouw|woonlasten|hdn|housing|residential|real estate|makelaar|verduurzam|energielabel|aflossing",
    "Verzekeringen": r"verzeker|insur|schade|polis|premie|aov|arbeidsongeschikt|woonlasten ?bescherm|overlijdensrisico|uitvaart|zorgverzeker|aansprakelijk|brand|storm|klimaatschade|verzekerbaar|sivi|risicodekking|reinsur|solvency|solvabiliteit|eiopa|cyber",
    "Pensioenen": r"pensioen|pension|lijfrente|wtp|wet toekomst pensioenen|aow|oudedag|annuïteit|annuity|iorp|uitkeringsfase|premieregeling|beschikbare premie|pensioenfonds",
    "Kredieten": r"krediet|\bcredit|\bgeldlening|\w*leningen\b|\blening\b|\bconsumptie|\bbkr\b|\bccd|rood staan|buy now|\bbnpl|betalingsachterstand|\bschulden|\bschuldhulp|\blending|\bloans?\b|financial lease|private lease|klarna",
}
DEFAULT = {"NHG": "Hypotheken", "HDN": "Hypotheken", "NVM": "Hypotheken", "Kadaster": "Hypotheken", "CBS": "Hypotheken", "NVHP": "Hypotheken",
           "Verbond van Verzekeraars": "Verzekeringen", "SIVI": "Verzekeringen", "Adfiz": "Verzekeringen", "EIOPA": "Verzekeringen",
           "Pensioenfederatie": "Pensioenen", "BKR": "Kredieten", "SVn": "Hypotheken", "Volkshuisvesting Nederland": "Hypotheken"}
DEFAULT_W = {"Pensioenfederatie": 3}
RX = {k: re.compile(v, re.I) for k, v in KW.items()}


def cat(item):
    t, x = item.get("t", ""), item.get("x", "") or ""
    score = {k: 3 * len(r.findall(t)) + len(r.findall(x)) for k, r in RX.items()}
    d = DEFAULT.get(item.get("bron"))
    if d:
        score[d] += DEFAULT_W.get(item.get("bron"), 1.5)
    best = max(score, key=score.get)
    return best if score[best] >= 1.5 else "Overig"


# Vaste achtergrondinformatie per categorie (bovenaan zichtbaar als de categorie gekozen is).
# Omschrijvingen in eigen woorden; alleen links, geen overgenomen tekst.
ACHTERGROND = {
    "Hypotheken": [
        {"t": "Leennormen voor hypotheken (Tijdelijke regeling hypothecair krediet)",
         "u": "https://www.volkshuisvestingnederland.nl/onderwerpen/huren-en-wonen/tijdelijke-regeling-hypothecair-krediet",
         "bron": "Volkshuisvesting Nederland",
         "x": "Hoe de maximale hypotheek wordt bepaald op basis van inkomen, woningwaarde en energielabel, het jaarlijkse Nibud-advies en wanneer maatwerk mogelijk is."},
    ],
    "Kredieten": [
        {"t": "Wat zijn de regels voor geldleningen (consumentenkrediet)?",
         "u": "https://www.rijksoverheid.nl/documenten/vraag-en-antwoord/bescherming-van-consumenten/wat-zijn-de-regels-rond-het-consumentenkrediet",
         "bron": "Rijksoverheid",
         "x": "Informatieplicht vooraf, 14 dagen bedenktijd, beperkte kosten bij vervroegd aflossen en de verplichting om in reclame de hoogste rente te noemen."},
        {"t": "Consumentenkrediet: waarom vernieuwde EU-regels nodig zijn",
         "u": "https://www.europarl.europa.eu/topics/nl/article/20220713STO35303/consumentenkrediet-waarom-vernieuwde-eu-regels-nodig-zijn",
         "bron": "Europees Parlement",
         "x": "Achtergrond bij de herziening van de Europese richtlijn consumentenkrediet (CCD II) en de extra bescherming voor consumenten."},
        {"t": "Leningen aanvragen in de EU veiliger na vaststelling herziene richtlijn consumentenkrediet",
         "u": "https://ecer.minbuza.nl/-/leningen-aanvragen-in-de-eu-veiliger-na-definitieve-vaststelling-van-herziene-eu-richtlijn-consumentenkrediet",
         "bron": "Expertisecentrum Europees Recht",
         "x": "Richtlijn (EU) 2023/2225: duidelijkere kredietinformatie en een verplichte kredietwaardigheidsbeoordeling door de kredietverstrekker."},
        {"t": "Toepassing van het rekenmodel maximale kredietverstrekking (Caribisch Nederland)",
         "u": "https://www.afm.nl/nl-nl/sector/caribisch-nederland/kredietverstrekking/toepassing-van-het-rekenmodel-maximale-kredietverstrekking",
         "bron": "AFM",
         "x": "Uitleg van de AFM bij het rekenmodel voor de kredietwaardigheidstoets in Caribisch Nederland: normbedragen, overwerk, woonlasten en creditcards."},
        {"t": "Nederlandse Vereniging van Financieringsadviseurs en -bemiddelaars",
         "u": "https://www.nvf.nl/",
         "bron": "NVF",
         "x": "Brancheorganisatie van financieringsadviseurs en kredietbemiddelaars, met gedragscode, ledenoverzicht en klachtenprocedure."},
    ],
}
