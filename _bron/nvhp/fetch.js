// Haalt cursussen en geplande data op van het NVHP-opleidingsportaal (mc.hypothecairplanner.nl)
// en schrijft _bron/nvhp.json. Bij een fout of verdacht weinig gegevens blijft het oude bestand staan.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const OUT = path.join(__dirname, '..', 'nvhp.json');

const euro = s => {
  const n = parseFloat(s.replace(/\.(?=\d{3}\b)/g, '').replace(',', '.'));
  return isNaN(n) ? s : '€ ' + n.toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('https://mc.hypothecairplanner.nl/', { waitUntil: 'networkidle', timeout: 90000 });
  await p.waitForTimeout(4000);
  const cards = await p.evaluate(() => [...document.querySelectorAll('a[href*="/cursus-nvhp/"]')]
    .map(a => [a.href.split('?')[0], a.innerText.trim().replace(/\s+/g, ' ')]));
  const seen = new Set(), cursussen = [];
  for (const [u, t] of cards) {
    if (seen.has(u)) continue;
    const m = t.match(/^(.*?)\s+\d+\s+€\s*([\d.,]+)\s*(.*)$/);
    if (!m) continue;
    seen.add(u);
    cursussen.push({ t: m[1].trim(), prijs: euro(m[2]), pe: m[3].trim(), u });
  }

  // per cursuspagina de tabel 'Geplande data': Datum, Begintijd, Eindtijd, Omschrijving, Docent, Locatie, Beschikbare plaatsen, Prijs
  const data = [];
  for (const c of cursussen) {
    try {
      await p.goto(c.u, { waitUntil: 'networkidle', timeout: 60000 });
      await p.waitForTimeout(1500);
      const txt = await p.innerText('body');
      const k = txt.indexOf('Geplande data');
      if (k < 0) continue;
      const L = txt.slice(k).split('\n').map(s => s.trim()).filter(Boolean);
      const h = L.indexOf('Prijs');
      for (let i = h + 1; i + 7 < L.length + 1; ) {
        const dm = (L[i] || '').match(/^(\d{1,2})-(\d{1,2})-(20\d\d)$/);
        if (!dm) break;
        const [, van, tot, oms, doc, loc, pl] = L.slice(i, i + 7);
        data.push({ t: c.t, d: `${dm[3]}-${dm[2].padStart(2, '0')}-${dm[1].padStart(2, '0')}`, tijd: `${van}–${tot}`, loc, doc,
          plaatsen: /^\d+$/.test(pl) ? +pl : null });
        i += 7;
        if (/^€/.test(L[i] || '')) i++;  // prijskolom
      }
    } catch (e) { console.log('NVHP: kon ' + c.u + ' niet lezen'); }
  }
  await b.close();
  data.sort((a, b) => a.d.localeCompare(b.d) || a.tijd.localeCompare(b.tijd));
  console.log(`NVHP: ${cursussen.length} cursussen, ${data.length} geplande data (${data.filter(d => /hoevelaken/i.test(d.loc)).length} in Hoevelaken)`);
  if (cursussen.length < 10 || data.length < 3) {
    console.log('NVHP: te weinig gegevens gevonden, nvhp.json niet aangepast');
    process.exit(0);
  }
  fs.writeFileSync(OUT, JSON.stringify({ bijgewerkt: new Date().toISOString(), cursussen, data }, null, 1));
})().catch(e => { console.log('NVHP: FOUT ' + e.message.split('\n')[0] + ' (nvhp.json niet aangepast)'); process.exit(0); });
