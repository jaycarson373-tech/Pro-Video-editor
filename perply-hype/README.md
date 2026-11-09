# Perply hype video

`perply-hype.mp4` is a 33-second, 1920×1080, 30 fps promo for [perply.live](https://www.perply.live/), the memecoin perpetual exchange on Elysium.

Everything is generated from code. That includes the soundtrack, an original 150 BPM track in A minor synthesized in `music.py`. Every cut, flash and shake lands on the same beat grid (1 beat = 0.4 s).

| Time | Section |
| --- | --- |
| 0.0–3.2 | Intro hits: ELYSIUM / MEMECOINS / JUST GOT / PERPS. |
| 3.2 | Drop 1: emblem slam, shockwave, `perply` wordmark |
| 4.8–9.6 | LONG. / SHORT. / HYPE MARGIN. |
| 9.6–16.0 | ONE TERMINAL.: walkthrough of the trade ticket (market → direction → leverage → review) |
| 16.0–19.2 | Strobe montage, one word per beat |
| 19.2–22.4 | Build: P-logo tunnel, PERPLY stutter, LONG / OR / SHORT?, silent beat |
| 22.4 | Drop 2: spinning emblem plus hero copy |
| 25.6–28.8 | Live site in a browser frame, then DISCOVER. / TRADE. / MANAGE. |
| 28.8–33.5 | Logo lockup, "Explore markets →", perply.live, risk line |

All on-screen copy, colors (`#04181c`, `#6fe6d3`, `#ff9eaf`, …), fonts (DM Sans) and logos come from perply.live. The trade UI is a labeled "Interface preview" mock that only uses the site's own options (1× / 1.5× / 2×, HYPE margin). It shows no invented prices or stats.

## Rebuild

Needs Python 3 with numpy and scipy, Node with Playwright (Chromium), and ffmpeg.

```bash
./build.sh
```

- `music.py`: soundtrack synth, writes `out/music.wav`
- `scene.html`: canvas scene; `render(t)` draws the frame at time `t`
- `render.js`: drives headless Chromium. `node render.js --at 3.3 22.5` writes single preview PNGs.
- `assets/`: brand files pulled from perply.live
