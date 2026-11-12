// Renders scene.html frame by frame with headless Chromium.
//   node render.js                 -> out/frames/f00000.jpg ... (all frames, parallel)
//   node render.js --at 3.3 9.0    -> out/preview/t3.30.png ... (single frames for review)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const FPS = Number(process.env.FPS || 60);
const WORKERS = Number(process.env.WORKERS || 4);
const root = __dirname;
const url = 'file://' + path.join(root, 'scene.html');

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => { console.error('page error:', e.message); process.exit(1); });
  await page.goto(url);
  await page.evaluate(() => window.ready);
  return page;
}

async function grab(page, t, type) {
  const data = await page.evaluate(([t, type]) => {
    window.render(t);
    return document.getElementById('c').toDataURL(type, 0.95);
  }, [t, type]);
  return Buffer.from(data.split(',')[1], 'base64');
}

(async () => {
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const args = process.argv.slice(2);
  if (args[0] === '--at') {
    const dir = path.join(root, 'out/preview');
    fs.mkdirSync(dir, { recursive: true });
    const page = await openPage(browser);
    for (const a of args.slice(1)) {
      const t = Number(a);
      fs.writeFileSync(path.join(dir, `t${t.toFixed(2)}.png`), await grab(page, t, 'image/png'));
    }
    await browser.close();
    return;
  }
  const dir = path.join(root, 'out/frames');
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  const probe = await openPage(browser);
  const dur = await probe.evaluate(() => window.DUR);
  await probe.close();
  const total = Math.round(dur * FPS);
  let next = 0, done = 0;
  const t0 = Date.now();
  await Promise.all(Array.from({ length: WORKERS }, async () => {
    const page = await openPage(browser);
    while (next < total) {
      const i = next++;
      const buf = await grab(page, i / FPS, 'image/jpeg');
      fs.writeFileSync(path.join(dir, `f${String(i).padStart(5, '0')}.jpg`), buf);
      if (++done % 60 === 0) console.log(`${done}/${total} frames (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    }
  }));
  console.log(`rendered ${total} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  await browser.close();
})();
