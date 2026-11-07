// Haalt dagelijks actueel nieuws op over hypotheken en verzekeringen bij toezichthouders en brancheorganisaties.
// Uitvoer: _bron/nieuws/nieuws.json (wordt samengevoegd met eerdere runs).
// Gebruik: node _bron/nieuws/fetch.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, 'nieuws.json');
const ONLY = (process.env.NIEUWS_ONLY || '').split(',').filter(Boolean);
const MAX_PER_SOURCE = 15;     // max. aantal nieuwe artikelpagina's per bron per run (voor datum/omschrijving)
const KEEP_DAYS = 180;

// Trefwoorden: hypotheken & verzekeringen (NL en EN voor ECB)
const KW = /hypothe|eigen woning|eigenwoning|box ?3|schenk|erfbelast|overdrachtsbelasting|woningmarkt|koopwoning|woning|huizen|huizenmarkt|woonlast|nhg|verzeker|polis|schade|assurantie|volmacht|krediet|lening|rente|pensioen|lijfrente|arbeidsongeschikt|aov|klimaatrisico|fundering|overstroming|adviseur|bemiddelaar|zorgplicht|provisie|mortgage|housing|house price|insur|interest rate|monetary policy decision|key ecb interest rates|real estate|residential/i;

// strenger filter voor brede politieke bronnen
const KW_STRICT = /hypothe|woning|huizen|koopwoning|verzeker|pensioen|lijfrente|belastingplan|box ?3|krediet|afm|dnb|financiële sector|financieel advies|arbeidsongeschikt|aov|nhg/i;

const SOURCES = [
  { naam: 'DNB', type: 'rss', url: 'https://www.dnb.nl/nl/rss/16451/6882', filter: true, home: 'https://www.dnb.nl/' },
  { naam: 'DNB', type: 'rss', url: 'https://www.dnb.nl/nl/rss/16453/6892', filter: true, home: 'https://www.dnb.nl/' },
  { naam: 'DNB', type: 'rss', url: 'https://www.dnb.nl/nl/rss/16452/6893', filter: true, home: 'https://www.dnb.nl/' },
  { naam: 'ECB', type: 'rss', url: 'https://www.ecb.europa.eu/rss/press.html', filter: true, home: 'https://www.ecb.europa.eu/' },
  { naam: 'AFM', type: 'rss', url: 'https://www.afm.nl/rss', filter: true, home: 'https://www.afm.nl/' },
  { naam: 'HDN', type: 'rss', url: 'https://www.hdn.nl/feed/', filter: false, home: 'https://www.hdn.nl/' },
  { naam: 'Verbond van Verzekeraars', type: 'html', raw: true, url: 'https://www.verzekeraars.nl/', pat: /\/publicaties\/actueel\/[a-z0-9-]{8,}$/, filter: false, home: 'https://www.verzekeraars.nl/' },
  { naam: 'NVB', type: 'html', url: 'https://www.nvb.nl/nieuws-en-verhalen', pat: /\/nieuws-en-verhalen\/[a-z0-9-]{8,}$/, filter: true, home: 'https://www.nvb.nl/' },
  { naam: 'SIVI', type: 'html', url: 'https://www.sivi.org/actueel/', pat: /\/actueel\/[a-z0-9-]{6,}\/?$/, filter: false, home: 'https://www.sivi.org/' },
  { naam: 'NHG', type: 'html', url: 'https://www.nhg.nl/nhg-actueel/', pat: /\/nhg-actueel\/[a-z0-9-]{6,}\/?$/, filter: false, home: 'https://www.nhg.nl/' },
  { naam: 'Rijksoverheid', type: 'html', url: 'https://www.rijksoverheid.nl/actueel/nieuws', pat: /\/actueel\/nieuws\/20\d\d\/\d\d\/\d\d\/[a-z0-9-]{6,}$/, filter: true, prefilter: true, home: 'https://www.rijksoverheid.nl/' },
  // --- toegevoegd: geschillen, normen, belangenorganisaties, cijfers, Europa, politiek, DFO
  { naam: 'Kifid', type: 'html', url: 'https://www.kifid.nl/nieuws/', pat: /kifid\.nl\/nieuws\/[a-z0-9-]{8,}\/?$/, filter: true, home: 'https://www.kifid.nl/' },
  { naam: 'Nibud', type: 'rss', url: 'https://www.nibud.nl/feed/', filter: true, home: 'https://www.nibud.nl/' },
  { naam: 'Belastingdienst', type: 'html', url: 'https://www.belastingdienst.nl/', pat: /\/berichten\/nieuws\/[a-z0-9-]{8,}$/, filter: true, strict: true, home: 'https://www.belastingdienst.nl/' },
  { naam: 'Ministerie van Financiën', type: 'html', url: 'https://www.rijksoverheid.nl/actueel/nieuws?size=n_20_n&filters%5B0%5D%5Bfield%5D=ministry&filters%5B0%5D%5Bvalues%5D%5B0%5D=Ministerie%20van%20Financi%C3%ABn&filters%5B0%5D%5Btype%5D=all', pat: /\/actueel\/nieuws\/20\d\d\/\d\d\/\d\d\/[a-z0-9-]{6,}$/, filter: true, strict: true, home: 'https://www.rijksoverheid.nl/ministeries/ministerie-van-financien' },
  { naam: 'Adfiz', type: 'html', url: 'https://www.adfiz.nl/nieuws/', pat: /adfiz\.nl\/nieuws\/[a-z0-9-]{8,}\/?$/, filter: false, home: 'https://www.adfiz.nl/' },
  { naam: 'OvFD', type: 'rss', url: 'https://www.ovfd.nl/feed/', filter: false, home: 'https://www.ovfd.nl/' },
  { naam: 'NVHP', type: 'rss', url: 'https://www.hypothecairplanner.nl/rss.xml', filter: false, home: 'https://www.hypothecairplanner.nl/' },
  { naam: 'CBS', type: 'rss', url: 'https://www.cbs.nl/nl-nl/rss-feeds/bouwen-en-wonen', filter: true, home: 'https://www.cbs.nl/' },
  { naam: 'Kadaster', type: 'html', url: 'https://www.kadaster.nl/over-ons/nieuws', pat: /kadaster\.nl\/-\/[a-z0-9-]{8,}/, filter: true, home: 'https://www.kadaster.nl/' },
  { naam: 'NVM', type: 'html', url: 'https://www.nvm.nl/nieuws/', pat: /nvm\.nl\/nieuws\/20\d\d\/[a-z0-9-]{8,}\/?$/, filter: false, home: 'https://www.nvm.nl/' },
  { naam: 'EIOPA', type: 'html', url: 'https://www.eiopa.europa.eu/media/news_en', pat: /eiopa\.europa\.eu\/[a-z0-9-]{20,}_en$/, filter: false, home: 'https://www.eiopa.europa.eu/' },
  { naam: 'Pensioenfederatie', type: 'html', url: 'https://www.pensioenfederatie.nl/', pat: /pensioenfederatie\.nl\/[a-z0-9-]{15,}\/?$/, textRe: /^Nieuws\b/, filter: false, home: 'https://www.pensioenfederatie.nl/' },
  { naam: 'Tweede Kamer', type: 'html', url: 'https://www.tweedekamer.nl/nieuws/kamernieuws', pat: /\/nieuws\/kamernieuws\/[a-z0-9-]{8,}$/, filter: true, strict: true, prefilter: true, home: 'https://www.tweedekamer.nl/' },
  { naam: 'BKR', type: 'html', url: 'https://www.bkr.nl/nl/inzichtelijk', pat: /bkr\.nl\/nl\/inzichtelijk\/[a-z0-9-]{8,}$/, filter: false, home: 'https://www.bkr.nl/' },
  { naam: 'BKR', type: 'html', url: 'https://www.bkr.nl/nl/persberichten', pat: /bkr\.nl\/nl\/persberichten\/[a-z0-9-]{8,}$/, filter: false, home: 'https://www.bkr.nl/' },
  { naam: 'SVn', type: 'html', url: 'https://www.svn.nl/over-svn/nieuws/', pat: /svn\.nl\/over-svn\/nieuws\/[a-z0-9-]{8,}\/?$/, filter: true, home: 'https://www.svn.nl/' },
  { naam: 'DFO Signalen', type: 'html', raw: true, titleFromUrl: u => { const m = u.match(/week-(\d+)-(20\d\d)/); return m ? `DFO Signalen week ${m[1]} – ${m[2]}` : ''; }, url: 'https://www.dfosignalen.nl/', pat: /\/nieuwsbrief-dfo-signalen\/nieuwsbrief-dfo-signalen-week-\d+-20\d\d\/?$/, filter: false, home: 'https://www.dfosignalen.nl/' },
  { naam: 'Wft Permanent Actueel', type: 'pawft', url: 'https://pa-wft.nl/nieuws.html', filter: false, home: 'https://pa-wft.nl/' },
  { naam: 'AI Permanent Actueel', type: 'aipa', url: 'https://ai-permanent-actueel.nl/nieuw/', filter: false, home: 'https://ai-permanent-actueel.nl/' },
];

const MAANDEN = { januari: 1, februari: 2, maart: 3, april: 4, mei: 5, juni: 6, juli: 7, augustus: 8, september: 9, oktober: 10, november: 11, december: 12,
  jan: 1, feb: 2, mrt: 3, apr: 4, jun: 6, jul: 7, aug: 8, sep: 9, okt: 10, nov: 11, dec: 12 };

const clean = s => decode(decode((s || '').replace(/<!\[CDATA\[|\]\]>/g, ''))).replace(/<[^>]+>/g, ' ').replace(/The post .*? appeared first on .*$/i, '').replace(/&nbsp;/g, ' ')
  .replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#x27;|&#39;|&#8217;/g, '’').replace(/&#x26;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  .replace(/&#(\d+);/g, (m, n) => String.fromCharCode(+n)).replace(/\s+/g, ' ').trim();

function decode(s) {
  return s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#x27;|&#39;|&#8217;/g, '’').replace(/&#x26;|&amp;/g, '&').replace(/&#(\d+);/g, (m, n) => String.fromCharCode(+n));
}

function kort(s, n = 280) {
  s = clean(s)
    .replace(/^.*?\b\d{1,2}\/\d{1,2}\/20\d\d\s*-\s*\d{1,2}:\d{2}\s*/, '')   // NVHP: titel, auteur, datum vooraan
    .replace(/\S+@\S*/g, '').replace(/\s{2,}/g, ' ').trim();
  if (s.length < 30) return '';
  if (s.length <= n) return s;
  const cut = s.slice(0, n);
  const i = Math.max(cut.lastIndexOf('. '), cut.lastIndexOf('! '), cut.lastIndexOf('? '));
  return (i > n * 0.5 ? cut.slice(0, i + 1) : cut.replace(/\s+\S*$/, '') + '…');
}

function isoDate(s) {
  if (!s) return '';
  const d = new Date(s);
  if (!isNaN(d)) return d.toISOString().slice(0, 10);
  const m = String(s).toLowerCase().match(/(\d{1,2})\s+([a-z]+)\s+(\d{4})/);
  if (m && MAANDEN[m[2]]) return `${m[3]}-${String(MAANDEN[m[2]]).padStart(2, '0')}-${m[1].padStart(2, '0')}`;
  const n = String(s).match(/(\d{1,2})-(\d{1,2})-(\d{4})/);
  if (n) return `${n[3]}-${n[2].padStart(2, '0')}-${n[1].padStart(2, '0')}`;
  return '';
}

function parseRss(xml) {
  const items = [];
  const blocks = xml.match(/<item[\s>][\s\S]*?<\/item>|<entry[\s>][\s\S]*?<\/entry>/g) || [];
  for (const b of blocks) {
    const get = tag => { const m = b.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`)); return m ? m[1] : ''; };
    let link = clean(get('link'));
    if (!link) { const m = b.match(/<link[^>]*href="([^"]+)"/); if (m) link = m[1]; }
    items.push({ t: clean(get('title')), u: link.trim(), d: isoDate(clean(get('pubDate') || get('published') || get('updated') || get('dc:date'))),
      x: kort(get('description') || get('summary') || get('content:encoded') || '') });
  }
  return items;
}

(async () => {
  const old = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : { items: [] };
  const byUrl = new Map(old.items.map(i => [i.u, i]));
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ userAgent: 'Mozilla/5.0 (DFO nieuwsoverzicht; +https://jeroen-o.github.io/DFO/)' });
  const page = await ctx.newPage();
  const log = [];
  let visits = 0;
  const cutoffEarly = new Date(Date.now() - KEEP_DAYS * 864e5).toISOString().slice(0, 10);

  async function enrich(it) {
    if (visits >= MAX_PER_SOURCE) return it;
    visits++;
    try {
      await page.goto(it.u, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.waitForTimeout(800);
      const meta = await page.evaluate(() => {
        const q = s => (document.querySelector(s) || {}).content || '';
        let ld = '';
        document.querySelectorAll('script[type="application/ld+json"]').forEach(s => { const m = s.textContent.match(/"datePublished"\s*:\s*"([^"]+)"/); if (m && !ld) ld = m[1]; });
        const t = document.querySelector('time[datetime]');
        const p = [...document.querySelectorAll('main p, article p, .content p, p')].map(x => x.innerText.trim()).find(x => x.length > 80) || '';
        const body = (document.querySelector('main') || document.body).innerText.slice(0, 1500);
        return { title: (document.querySelector('h1') || {}).innerText || document.title, desc: q('meta[name="description"]') || q('meta[property="og:description"]'),
          date: q('meta[property="article:published_time"]') || ld || (t ? t.getAttribute('datetime') : '') || '', p, body };
      });
      const h1 = (meta.title || '').trim().replace(/\s*[|–-]\s*(SIVI|NHG|NVB|HDN|Verbond van Verzekeraars)\s*$/i, '');
      if (!it.t || it.html || /^(lees|meer|bekijk)/i.test(it.t)) it.t = h1 || it.t;
      const generic = d => !d || d.length < 60 || /cookie|provider|gegevens die door|is the central bank of the European Union|Insights into our work|JavaScript/i.test(d);
      if (generic(meta.desc)) meta.desc = '';
      if (generic(meta.p)) meta.p = '';
      if (!it.d) it.d = isoDate(meta.date) || isoDate((meta.body.match(/\d{1,2}\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+20\d\d/i) || [''])[0]);
      if (!it.x || it.x.length < 60 || generic(it.x)) it.x = kort(meta.desc || meta.p || '');
    } catch (e) { /* artikel overslaan */ }
    return it;
  }

  for (const src of SOURCES) {
    if (ONLY.length && !ONLY.includes(src.naam)) continue;
    let found = [];
    visits = 0;
    try {
      if (src.type === 'rss') {
        const r = await page.request.get(src.url, { timeout: 45000 });
        if (!r.ok()) throw new Error('HTTP ' + r.status());
        found = parseRss(await r.text());
      } else if (src.type === 'pawft') {
        // maandpagina's met artikelen (id = datum-slug)
        await page.goto(src.url, { waitUntil: 'domcontentloaded', timeout: 45000 });
        const months = (await page.evaluate(() => [...document.querySelectorAll('a[href]')].map(a => a.href).filter(h => /nieuws-20\d\d-\d\d\.html$/.test(h)))).filter((v, i, a) => a.indexOf(v) === i).slice(0, 2);
        for (const m of months) {
          await page.goto(m, { waitUntil: 'domcontentloaded', timeout: 45000 });
          const arts = await page.evaluate(() => [...document.querySelectorAll('article[id]')].filter(a => /^20\d\d-\d\d-\d\d/.test(a.id)).map(a => ({
            id: a.id, t: ((a.querySelector('h2,h3') || {}).innerText || '').trim(),
            x: ([...a.querySelectorAll('p')].map(p => p.innerText.trim()).find(p => p.length > 60) || '') })));
          for (const a of arts) found.push({ t: a.t, u: m + '#' + a.id, d: a.id.slice(0, 10), x: kort(a.x) });
        }
      } else if (src.type === 'aipa') {
        await page.goto(src.url, { waitUntil: 'domcontentloaded', timeout: 45000 });
        const r = await page.evaluate(() => { const h = [...document.querySelectorAll('h2')].find(x => /^Update/i.test(x.innerText.trim())); if (!h) return null;
          let p = h.nextElementSibling, x = ''; while (p && !x) { if (p.innerText && p.innerText.trim().length > 60) x = p.innerText.trim(); p = p.nextElementSibling; }
          return { t: h.innerText.trim(), x }; });
        if (r) { const m = r.t.toLowerCase().match(/(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(20\d\d)/);
          const d = m ? `${m[2]}-${String(MAANDEN[m[1]]).padStart(2, '0')}-01` : '';
          found.push({ t: r.t, u: src.url + (m ? '#' + m[1] + '-' + m[2] : ''), d, x: kort(r.x) }); }
      } else if (src.raw) {
        const r = await page.request.get(src.url, { timeout: 45000 });
        const h = await r.text();
        const base = new URL(src.url).origin;
        const seen = new Set();
        for (const m of h.matchAll(/href="([^"#?]+)"[^>]*>([\s\S]{0,400}?)<\/a>/g)) {
          const u = m[1].startsWith('http') ? m[1] : base + m[1];
          if (!src.pat.test(u) || seen.has(u)) continue;
          seen.add(u);
          const t = clean(m[2]);
          found.push({ t: t.length > 15 ? t : '', u, d: '', x: '' });
        }
        found = found.slice(0, 15);
      } else {
        await page.goto(src.url, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
        await page.waitForTimeout(2000);
        const links = await page.evaluate(() => [...document.querySelectorAll('a[href]')].map(a => [a.innerText.trim().replace(/\s+/g, ' '), a.href.split('#')[0].split('?')[0]]));
        const seen = new Set();
        for (const [t0, u] of links) {
          if (!src.pat.test(u) || seen.has(u)) continue;
          if (src.textRe && !src.textRe.test(t0)) continue;
          const t = t0.replace(/^Nieuws\s+/, '').replace(/\s+\d{1,2}-\d{1,2}-20\d\d$/, '').replace(/^\d{1,2}\s+[a-z]+\s+20\d\d\s+/i, '');
          seen.add(u);
          const dm = t0.match(/^(\d{1,2})-(\d{1,2})-(20\d\d)\b/);
          found.push({ d: dm ? `${dm[3]}-${dm[2].padStart(2, '0')}-${dm[1].padStart(2, '0')}` : '', t: t.length > 15 ? t.split('\n')[0].replace(/^(nieuws|persbericht|blog)\s+/i, '').replace(/^\d{1,2}\s+\w+\s+20\d\d\s+/, '') : '', u, x: '' });
        }
        found = found.slice(0, 15);
      }
      let added = 0;
      for (let it of found) {
        if (!it.u) continue;
        if (byUrl.has(it.u)) continue;
        if (it.d && it.d < cutoffEarly) continue;
        const kw = src.strict ? KW_STRICT : KW;
        if (src.prefilter && it.t && !kw.test(it.t)) continue;  // brede bron: eerst op titel filteren
        it.html = src.type === 'html';
        if (it.html || !it.x || !it.d || /is the central bank of the European Union/.test(it.x)) it = await enrich(it);
        delete it.html;
        if (src.titleFromUrl) it.t = src.titleFromUrl(it.u) || it.t;
        if (!it.t || /^(inloggen|login|nieuws)$/i.test(it.t.trim()) || /one moment|just a moment|access denied|attention required|pagina niet gevonden|not found/i.test(it.t)) continue;
        if (src.filter && !kw.test(it.t + ' ' + it.x)) continue;
        byUrl.set(it.u, { ...it, bron: src.naam, home: src.home, opgehaald: new Date().toISOString().slice(0, 10) });
        added++;
      }
      log.push(`${src.naam}: ${found.length} gevonden, ${added} nieuw (${src.url})`);
    } catch (e) {
      log.push(`${src.naam}: FOUT ${e.message.split('\n')[0]} (${src.url})`);
    }
  }
  await browser.close();

  const cutoff = new Date(Date.now() - KEEP_DAYS * 864e5).toISOString().slice(0, 10);
  let items = [...byUrl.values()].map(i => ({ ...i, d: i.d || i.opgehaald }))
    .filter(i => i.d >= cutoff && i.d <= new Date(Date.now() + 864e5).toISOString().slice(0, 10));
  items.sort((a, b) => (b.d || '').localeCompare(a.d || '') || a.bron.localeCompare(b.bron));
  items = items.slice(0, 400);
  fs.writeFileSync(OUT, JSON.stringify({ bijgewerkt: new Date().toISOString(), items }, null, 1));
  console.log(log.join('\n'));
  console.log(`Totaal ${items.length} berichten in ${OUT}`);
})();
