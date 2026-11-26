// Renders liquid-ponzi-hype.html to a 60 fps MP4 with its Web Audio soundtrack (rendered offline, sample-exact).
//   node export.js  ->  liquid-ponzi-hype.mp4
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const FPS = 60, WORKERS = 4, root = __dirname, out = path.join(root, 'out');
(async () => {
  const frames = path.join(out, 'frames');
  fs.rmSync(frames, { recursive: true, force: true }); fs.mkdirSync(frames, { recursive: true });
  const browser = await chromium.launch();
  const open = async () => {
    const p = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
    p.on('pageerror', e => { console.error('page error:', e.message); process.exit(1); });
    await p.goto('file://' + path.join(root, 'liquid-ponzi-hype.html'));
    await p.evaluate(() => window.ready);
    return p;
  };
  const p0 = await open();
  const wav = await p0.evaluate(() => window.renderAudioWav());
  fs.writeFileSync(path.join(out, 'audio.wav'), Buffer.from(wav, 'base64'));
  const dur = await p0.evaluate(() => window.DUR);
  await p0.close();
  const total = Math.round(dur * FPS);
  let next = 0;
  await Promise.all(Array.from({ length: WORKERS }, async () => {
    const p = await open();
    while (next < total) {
      const i = next++;
      const d = await p.evaluate(t => { window.render(t); return document.getElementById('c').toDataURL('image/jpeg', 0.95); }, i / FPS);
      fs.writeFileSync(path.join(frames, `f${String(i).padStart(5, '0')}.jpg`), Buffer.from(d.split(',')[1], 'base64'));
    }
  }));
  await browser.close();
  execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-framerate', String(FPS), '-i', path.join(frames, 'f%05d.jpg'), '-i', path.join(out, 'audio.wav'),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-af', 'volume=2.5dB,alimiter=limit=0.84:attack=1:release=50:level=false', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart',
    path.join(root, 'liquid-ponzi-hype.mp4')]);
  console.log(`exported ${total} frames`);
})();
