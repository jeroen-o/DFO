// Leest alle DFO-portalen uit via hun sitemap en schrijft per portaal _bron/portalen/<key>.json
// met per pagina: titel, omschrijving, datum, tussenkoppen en een tekstuittreksel.
// Wordt wekelijks gedraaid (zie .github/workflows/portalen.yml). Bij een fout of verdacht weinig
// pagina's blijft het vorige bestand van dat portaal staan.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ONLY = (process.env.PORTAAL || '').split(',').filter(Boolean);
const PORTALEN = [
  { key: 'signalen', naam: 'DFO Signalen', home: 'https://www.dfosignalen.nl/', sitemaps: ['https://www.dfosignalen.nl/sitemap.xml'],
    skip: /\/(privacy|cookie|inloggen|login|aanmelden)/i, min: 20 },
  { key: 'serviceproviders', naam: 'Serviceproviders (sp.dfobv.nl)', home: 'https://sp.dfobv.nl/', sitemaps: ['https://sp.dfobv.nl/wp-sitemap-posts-page-1.xml', 'https://sp.dfobv.nl/wp-sitemap-posts-ajde_events-1.xml'],
    skip: /\/(privacy|cookie|inloggen|login|hello-world|mijn-account|winkelwagen|afrekenen)/i, min: 15 },
  { key: 'nazorg', naam: 'Nazorg & Onderhoud Portal', home: 'https://www.dfonazorg.nl/', sitemaps: ['https://www.dfonazorg.nl/sitemap.xml'],
    skip: /\/(inloggen|login)/i, min: 1 },
  { key: 'aipa', naam: 'AI Permanent Actueel', home: 'https://ai-permanent-actueel.nl/', sitemaps: ['https://ai-permanent-actueel.nl/sitemap.xml'],
    skip: /\/(privacy|en)\b|\/en\//i, min: 5 },
  { key: 'pawft', naam: 'Wft Permanent Actueel', home: 'https://pa-wft.nl/', sitemaps: ['https://pa-wft.nl/sitemap.xml'],
    skip: /\/en\/|\/(privacy|gebruiksvoorwaarden|klachten)\.html/i, min: 20 },
  { key: 'vergaderruimte', naam: 'Vergaderruimte Amersfoort', home: 'https://www.amersfoort-vergaderruimte.nl/', sitemaps: ['https://www.amersfoort-vergaderruimte.nl/sitemap.xml'],
    skip: /\/(privacy|cookie)/i, min: 1 },
];
const MAX_PAGES = 250;
const UA = 'Mozilla/5.0 (compatible; DFO-sitebot/1.0; +https://jeroen-o.github.io/DFO/)';

async function getText(url) {
  const r = await fetch(url, { headers: { 'user-agent': UA }, redirect: 'follow' });
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.text();
}

async function sitemapUrls(url, depth = 0) {
  const xml = await getText(url);
  const locs = [...xml.matchAll(/<loc>\s*([^<\s]+)\s*<\/loc>/g)].map(m => m[1].replace(/&amp;/g, '&'));
  const lastmod = Object.fromEntries([...xml.matchAll(/<url>[\s\S]*?<loc>\s*([^<\s]+)\s*<\/loc>[\s\S]*?(?:<lastmod>([^<]+)<\/lastmod>)?[\s\S]*?<\/url>/g)].map(m => [m[1], (m[2] || '').slice(0, 10)]));
  if (/<sitemapindex/i.test(xml) && depth < 2) {
    let out = [];
    for (const l of locs) out = out.concat(await sitemapUrls(l, depth + 1).catch(() => []));
    return out;
  }
  return locs.map(u => ({ u, lastmod: lastmod[u] || '' }));
}

const MAAND = { januari: 1, februari: 2, maart: 3, april: 4, mei: 5, juni: 6, juli: 7, augustus: 8, september: 9, oktober: 10, november: 11, december: 12 };

// in de browser: inhoud van de pagina uitlezen
function extract() {
  const meta = n => (document.querySelector(`meta[name="${n}"],meta[property="${n}"]`) || {}).content || '';
  // grootste inhoudsblok kiezen (sommige sites hebben een leeg <article> naast de echte inhoud)
  const cands = [...document.querySelectorAll('main, article, .entry-content, #content, .content, body')];
  const bodyLen = document.body.innerText.length;
  let main = cands.sort((a, b) => b.innerText.length - a.innerText.length)
    .find(e => e.tagName !== 'BODY' && e.innerText.length > 400) || document.body;
  if (main.innerText.length < bodyLen * 0.5) main = document.body;  // inhoud verspreid over meerdere blokken
  const clone = main.cloneNode(true);
  clone.querySelectorAll('script,style,nav,header,footer,form,noscript,svg,[aria-hidden="true"]').forEach(e => e.remove());
  // cookiemeldingen: alleen kleine blokken weghalen (sommige sites zetten 'cookie' in de class van de hele pagina)
  clone.querySelectorAll('.cookie,#cookie-notice,[class*="cookie"],[id*="cookie"],[class*="consent"]').forEach(e => { if ((e.textContent || '').length < 1500) e.remove(); });
  const heads = [...clone.querySelectorAll('h2,h3,h4')].map(h => h.innerText.trim().replace(/\s+/g, ' ')).filter(t => t.length > 2 && t.length < 160);
  const h1 = (document.querySelector('h1') || {}).innerText || '';
  return {
    title: (meta('og:title') || document.title || h1).trim(),
    h1: h1.trim().replace(/\s+/g, ' '),
    desc: (meta('description') || meta('og:description')).trim(),
    date: meta('article:published_time') || meta('article:modified_time') || (document.querySelector('time[datetime]') || {}).dateTime || '',
    heads: [...new Set(heads)].slice(0, 25),
    text: clone.innerText.replace(/\s+/g, ' ').trim().slice(0, 6000),
    noindex: /noindex/i.test(meta('robots')),
  };
}

function isoDate(s, text) {
  if (s && /^\d{4}-\d{2}-\d{2}/.test(s)) return s.slice(0, 10);
  const m = (text || '').match(/\b(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(20\d\d)\b/i);
  if (m) return `${m[3]}-${String(MAAND[m[2].toLowerCase()]).padStart(2, '0')}-${m[1].padStart(2, '0')}`;
  return '';
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ userAgent: UA });
  const log = [];
  for (const P of PORTALEN.filter(p => !ONLY.length || ONLY.includes(p.key))) {
    const OUT = path.join(__dirname, `${P.key}.json`);
    try {
      let urls = [];
      for (const sm of P.sitemaps) urls = urls.concat(await sitemapUrls(sm).catch(e => (log.push(`${P.naam}: sitemap ${sm} niet leesbaar (${e.message})`), [])));
      const seen = new Set();
      urls = urls.filter(x => !P.skip.test(new URL(x.u).pathname) && !seen.has(x.u) && seen.add(x.u)).slice(0, MAX_PAGES);
      if (!urls.length) urls = [{ u: P.home, lastmod: '' }];
      const items = [];
      for (const { u, lastmod } of urls) {
        try {
          const r = await page.goto(u, { waitUntil: 'domcontentloaded', timeout: 45000 });
          if (!r || r.status() >= 400) { log.push(`${P.naam}: ${u} HTTP ${r && r.status()}`); continue; }
          await page.waitForTimeout(600);
          let x = await page.evaluate(extract);
          if (x.text.length < 200) { await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {}); x = await page.evaluate(extract); }
          const koek = /^(?:[^.]{0,220}\bcookies?\b[^.]*\.\s*){1,4}/i;  // cookiemelding vooraan weghalen
          x.text = x.text.replace(koek, ''); if (koek.test(x.desc)) x.desc = '';
          if (x.noindex && !/serviceprovider|nieuwsbrief/.test(u)) continue;
          const site = /DFO Signalen|Bureau DFO|AI Permanent Actueel|Wft Permanent Actueel|PA-Wft|DFO Portal|Serviceproviders|nieuwsbrief voor de financieel adviseur|^DFO$/i;
          const docT = x.title.split(/\s+[|–-]\s+/).filter(p => !site.test(p)).join(' – ').trim();
          const t = (x.h1 && x.h1.length < 90 && !/^alsjeblieft|^welkom op de website/i.test(x.h1) ? x.h1 : (docT || x.h1)).trim();
          if (!t || /^(pagina niet gevonden|404|not found)/i.test(t)) continue;
          items.push({ t, u, d: isoDate(x.date, x.text.slice(0, 600)) || lastmod, x: x.desc || x.text.slice(0, 300), h: x.heads, tekst: x.text.slice(0, 3000) });
        } catch (e) { log.push(`${P.naam}: ${u} niet gelezen (${e.message.split('\n')[0]})`); }
      }
      if (items.length < P.min) { log.push(`${P.naam}: maar ${items.length} pagina's gevonden (minimaal ${P.min}), ${P.key}.json niet aangepast`); continue; }
      items.sort((a, b) => (b.d || '').localeCompare(a.d || '') || a.t.localeCompare(b.t));
      fs.writeFileSync(OUT, JSON.stringify({ portaal: P.naam, home: P.home, bijgewerkt: new Date().toISOString(), items }, null, 1));
      log.push(`${P.naam}: ${items.length} pagina's`);
    } catch (e) {
      log.push(`${P.naam}: FOUT ${e.message.split('\n')[0]}`);
    }
  }
  await browser.close();
  console.log(log.join('\n'));
})();
