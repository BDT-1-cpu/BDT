// Re-captures the Dog Spots gallery list from the live site into dogspots.json.
// Run after adding photos in the Wix Media Manager (needs Node + Playwright):
//   node tools/refresh_dogspots.js
// (The page also picks up new photos by itself once Wix sends its list; this just
// keeps the instant first-load copy current.)
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  let data = null;
  await p.goto('https://www.bigdogstour.com/dog-spots', { waitUntil: 'domcontentloaded', timeout: 90000 });
  for (let i = 0; i < 160 && !data; i++) {
    const f = p.frames().find(f => /Dog%20Spots/.test(f.url()));
    if (f) {
      const s = await f.evaluate(() => { try { return localStorage.getItem('bdt-dogspots-v1'); } catch (e) { return null; } }).catch(() => null);
      if (s) data = JSON.parse(s);
    }
    await p.waitForTimeout(250);
  }
  await b.close();
  if (!data || !data.categories || !data.categories.length) { console.error('No gallery data received'); process.exit(1); }
  delete data.start;
  fs.writeFileSync('dogspots.json', JSON.stringify(data));
  console.log('dogspots.json:', data.categories.length, 'categories,', data.categories.reduce((n, c) => n + c.photos.length, 0), 'photos');
})();
