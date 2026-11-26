// Renders scene.html frame by frame with headless Chromium (WebGL via SwiftShader for the 3D ring).
//   node render.js v                  -> out/frames-v/f00000.jpg ...   (9:16, 1080x1920)
//   node render.js h                  -> out/frames-h/f00000.jpg ...   (16:9, 1920x1080)
//   node render.js v --at 3.2 9.0     -> out/preview/v-t3.20.png ...   (single frames for review)
//   node render.js v --range 18 24    -> re-render only seconds 18-24 into the existing frames
const { chromium } = require('playwright');
const fs = require('fs');
const http = require('http');
const path = require('path');

const FPS = Number(process.env.FPS || 30);
const WORKERS = Number(process.env.WORKERS || 4);
const root = __dirname;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.ttf': 'font/ttf', '.woff2': 'font/woff2' };

function serve() {
  return new Promise(resolve => {
    const srv = http.createServer((req, res) => {
      const p = path.normalize(path.join(root, decodeURIComponent(req.url.split('?')[0])));
      if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
      res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
      fs.createReadStream(p).pipe(res);
    });
    srv.listen(0, '127.0.0.1', () => resolve(srv));
  });
}

async function openPage(browser, url, fmt) {
  const page = await browser.newPage({ viewport: fmt === 'h' ? { width: 1920, height: 1080 } : { width: 1080, height: 1920 } });
  page.on('pageerror', e => { console.error('page error:', e.message); });
  page.on('console', m => { if (m.type() === 'error') console.error('console:', m.text()); });
  await page.goto(url, { timeout: 180000 });
  // scene.html sets window.ready after its top-level awaits, so wait for it to exist before awaiting it
  await page.waitForFunction(() => window.ready, null, { timeout: 180000 });
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

// Software WebGL occasionally drops a page; reopen it and retry the frame instead of failing the render.
async function grabRetry(state, open, t, type) {
  for (let attempt = 0; ; attempt++) {
    try { return await grab(state.page, t, type); }
    catch (e) {
      if (attempt >= 3) throw e;
      console.error(`retrying frame at ${t.toFixed(3)}s: ${String(e.message).split('\n')[0]}`);
      try { await state.page.close(); } catch (_) {}
      state.page = await open();
    }
  }
}

(async () => {
  const args = process.argv.slice(2);
  const fmt = args[0] === 'h' ? 'h' : 'v';
  const page0 = args[1] === '--page' ? args[2] : 'scene.html';
  const srv = await serve();
  const url = `http://127.0.0.1:${srv.address().port}/${page0}?fmt=${fmt}`;
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const at = args.indexOf('--at');
  if (at >= 0) {
    const dir = path.join(root, 'out/preview');
    fs.mkdirSync(dir, { recursive: true });
    const open = () => openPage(browser, url, fmt);
    const state = { page: await open() };
    for (const a of args.slice(at + 1)) {
      const t = Number(a);
      fs.writeFileSync(path.join(dir, `${fmt}-t${t.toFixed(2)}.png`), await grabRetry(state, open, t, 'image/png'));
    }
  } else {
    const dir = path.join(root, `out/frames-${fmt}`);
    const rg = args.indexOf('--range'); // --range 18 24 re-renders only those seconds into the existing frames
    if (rg < 0) fs.rmSync(dir, { recursive: true, force: true });
    fs.mkdirSync(dir, { recursive: true });
    const probe = await openPage(browser, url, fmt);
    const dur = await probe.evaluate(() => window.DUR);
    await probe.close();
    const total = rg < 0 ? Math.round(dur * FPS) : Math.round(Number(args[rg + 2]) * FPS);
    let next = rg < 0 ? 0 : Math.round(Number(args[rg + 1]) * FPS), done = 0;
    const t0 = Date.now();
    await Promise.all(Array.from({ length: WORKERS }, async () => {
      const open = () => openPage(browser, url, fmt);
      const state = { page: await open() };
      while (next < total) {
        const i = next++;
        fs.writeFileSync(path.join(dir, `f${String(i).padStart(5, '0')}.jpg`), await grabRetry(state, open, i / FPS, 'image/jpeg'));
        if (++done % 120 === 0) console.log(`${fmt}: ${done}/${total} frames (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
      }
    }));
    console.log(`${fmt}: rendered ${total} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  await browser.close();
  srv.close();
})();
