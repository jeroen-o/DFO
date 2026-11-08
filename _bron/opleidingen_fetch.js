// Haalt cursussen en geplande data op van het DFO-opleidingsportaal (www.dfo-opleidingen.nl, AFAS)
// en schrijft _bron/opleidingen.json. Bij een fout of verdacht weinig gegevens blijft het oude bestand staan.
//
// Bronnen:
//  - /cursussen/cursussen               volledig cursusoverzicht (alle cursussen in één lijst, geen paginering)
//  - /alle-cursus-evenementen/overzicht alle geplande data
// AFAS zet de rijen van elke lijst als JS-object ("data":[{"uniqueId":...}]) in de pagina; daaruit lezen we
// de kolommen plus de samenvatting (veld "Summary"). Als dat niet lukt vallen we terug op de zichtbare tabel.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const OUT = path.join(__dirname, 'opleidingen.json');
const BASE = 'https://www.dfo-opleidingen.nl';

// Zoek alle "data":[{"uniqueId"...}]-arrays in de HTML en parse ze.
function viewData(html) {
  const out = [];
  let k = 0;
  while ((k = html.indexOf('"data":[{"uniqueId"', k)) >= 0) {
    const start = k + 7;
    let d = 0, s = false, e = false, i = start;
    for (; i < html.length; i++) {
      const c = html[i];
      if (s) { if (e) e = false; else if (c === '\\') e = true; else if (c === '"') s = false; continue; }
      if (c === '"') s = true;
      else if (c === '{' || c === '[') d++;
      else if (c === '}' || c === ']') { if (--d === 0) break; }
    }
    const lit = html.slice(start, i + 1).replace(/\\\\|\\'/g, m => (m === "\\'" ? "'" : m)); // JS-escape \' -> '
    try { out.push(JSON.parse(lit)); } catch (err) { /* overslaan */ }
    k = i;
  }
  return out;
}

const v = (r, key) => ((r.columns[key] || {}).value || '').trim();

async function open(p, url) {
  await p.goto(url, { waitUntil: 'networkidle', timeout: 90000 });
  await p.waitForTimeout(2500);
  // Mocht AFAS ooit een "Meer"-knop tonen: doorklikken tot alles geladen is.
  for (let n = 0; n < 30; n++) {
    const meer = p.locator('button:has-text("Meer"), a:has-text("Meer tonen")').first();
    if (!(await meer.count()) || !(await meer.isVisible())) break;
    await meer.click();
    await p.waitForLoadState('networkidle');
    await p.waitForTimeout(1000);
  }
}

// Zichtbare tabelrijen (eerste grid): [href, [kolomteksten]]
const domRows = p => p.evaluate(() => {
  const grid = [...document.querySelectorAll('.viewdata')].find(g => g.querySelector('a.dataRow'));
  if (!grid) return [];
  return [...grid.querySelectorAll('a.dataRow')].map(a => [a.getAttribute('href'),
    [...a.querySelectorAll(':scope > .dataColumn')].map(c => c.innerText.trim())]);
});

(async () => {
  const t0 = Date.now();
  const b = await chromium.launch();
  const p = await b.newPage();

  // ---- cursussen
  await open(p, BASE + '/cursussen/cursussen');
  const cursussen = [], seen = new Set();
  for (const arr of viewData(await p.content())) {
    for (const r of arr) {
      if (!r.link || !r.columns || seen.has(r.link)) continue;
      seen.add(r.link);
      cursussen.push({ href: r.link, cols: [v(r, 'U001'), v(r, 'U003'), v(r, 'U004'), v(r, 'U005')], summary: v(r, 'Summary') });
    }
  }
  for (const [href, cols] of await domRows(p)) {  // aanvullen met rijen die (nog) niet in de data zaten
    if (!href || seen.has(href) || cols.length < 4) continue;
    seen.add(href);
    cursussen.push({ href, cols: cols.slice(0, 4), summary: '' });
  }

  // ---- geplande data
  await open(p, BASE + '/alle-cursus-evenementen/overzicht');
  const evenementen = [], seenE = new Set();
  const datum = s => { const m = s.match(/^(\d{4})-(\d{2})-(\d{2})/); return m ? `${m[3]}-${m[2]}-${m[1]}` : s; };
  for (const arr of viewData(await p.content())) {
    for (const r of arr) {
      if (!r.columns || !('U002' in r.columns)) continue;
      const cols = [v(r, 'U001'), datum(v(r, 'U002')), v(r, 'U003'), v(r, 'U004'), v(r, 'SeRe'), v(r, 'U007')];
      const key = v(r, 'KnCreId') || cols.join('|');
      if (seenE.has(key)) continue;   // AFAS zet dezelfde lijst soms meerdere keren in de pagina
      seenE.add(key);
      evenementen.push({ href: r.link || null, cols, summary: '' });
    }
  }
  if (!evenementen.length) {
    for (const [href, cols] of await domRows(p)) {
      if (cols.length >= 6 && /^\d{2}-\d{2}-\d{4}$/.test(cols[1])) evenementen.push({ href: href || null, cols: cols.slice(0, 6), summary: '' });
    }
  }
  await b.close();

  console.log(`Opleidingen: ${cursussen.length} cursussen, ${evenementen.length} data (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
  if (cursussen.length < 50 || evenementen.length < 5) {
    console.log('Opleidingen: te weinig gegevens gevonden, opleidingen.json niet aangepast');
    process.exit(0);
  }
  fs.writeFileSync(OUT, JSON.stringify({ cursussen, evenementen }, null, 1));
})().catch(e => { console.log('Opleidingen: FOUT ' + e.message.split('\n')[0] + ' (opleidingen.json niet aangepast)'); process.exit(0); });
