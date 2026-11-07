// Haalt dagelijks actueel nieuws op over hypotheken en verzekeringen bij toezichthouders en brancheorganisaties.
// Uitvoer: _bron/nieuws/nieuws.json (wordt samengevoegd met eerdere runs).
// Gebruik: node _bron/nieuws/fetch.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, 'nieuws.json');
const MAX_PER_SOURCE = 15;     // max. aantal nieuwe artikelpagina's per bron per run (voor datum/omschrijving)
const KEEP_DAYS = 180;

// Trefwoorden: hypotheken & verzekeringen (NL en EN voor ECB)
const KW = /hypothe|woning|huizen|huizenmarkt|woonlast|nhg|verzeker|polis|schade|assurantie|volmacht|krediet|lening|rente|pensioen|lijfrente|arbeidsongeschikt|aov|klimaatrisico|fundering|overstroming|adviseur|bemiddelaar|zorgplicht|provisie|mortgage|housing|house price|insur|interest rate|monetary policy decision|key ecb interest rates|real estate|residential/i;

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
  s = clean(s);
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
    let found = [];
    visits = 0;
    try {
      if (src.type === 'rss') {
        const r = await page.request.get(src.url, { timeout: 45000 });
        if (!r.ok()) throw new Error('HTTP ' + r.status());
        found = parseRss(await r.text());
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
        for (const [t, u] of links) {
          if (!src.pat.test(u) || seen.has(u)) continue;
          seen.add(u);
          found.push({ t: t.length > 15 ? t.split('\n')[0].replace(/^(nieuws|persbericht|blog)\s+/i, '').replace(/^\d{1,2}\s+\w+\s+20\d\d\s+/, '') : '', u, d: '', x: '' });
        }
        found = found.slice(0, 15);
      }
      let added = 0;
      for (let it of found) {
        if (!it.u) continue;
        if (byUrl.has(it.u)) continue;
        if (it.d && it.d < cutoffEarly) continue;
        if (src.prefilter && it.t && !KW.test(it.t)) continue;  // brede bron: eerst op titel filteren
        it.html = src.type === 'html';
        if (it.html || !it.x || !it.d || /is the central bank of the European Union/.test(it.x)) it = await enrich(it);
        delete it.html;
        if (!it.t || /one moment|just a moment|access denied|attention required|pagina niet gevonden|not found/i.test(it.t)) continue;
        if (src.filter && !KW.test(it.t + ' ' + it.x)) continue;
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
