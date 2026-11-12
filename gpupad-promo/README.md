# GPU Pad promo video

`gpupad-promo.mp4` is an 18-second, 1920×1080, 60 fps promo for GPU Pad ([gpupad.fun](https://gpupad.fun), [@GPUPad_](https://x.com/GPUPad_)), the AI agent launchpad on Solana. It's a clean, calm edit rather than a loud hype cut.

Everything is generated from code, including the soundtrack: an original 100 BPM track (F minor resolving to A♭ major) synthesized in `music.py`. Scene changes sit on the bar lines (1 bar = 2.4 s).

| Time | Section |
| --- | --- |
| 0.0–2.4 | Circuit traces draw in, the chip logo powers on, "GPU Pad" wordmark |
| 2.4–4.8 | "The AI agent launchpad." |
| 4.8–9.6 | Agent workspace: give it a mission (Plan), fund builds with creator fees (Build), track what it ships (Ship) |
| 9.6–12.0 | Where the creator fees go: 50% holder rewards, 30% agent AI credits, 20% GPU Pad buyback + burn |
| 12.0–18.0 | "Launch your agent.", GPUPad.fun, @GPUPad_ |

All copy, colors (`#090b09`, `#76b900`), fonts (Space Grotesk, DM Sans) and the fee split come from gpupad.fun. The workspace panel mirrors the site's own "Agent workspace" preview and uses its example brief and roadmap items. The fee scene carries the site's caveat that trading volume, funding and successful builds are not guaranteed.

## Rebuild

Needs Python 3 with numpy and scipy, Node with Playwright (Chromium), and ffmpeg.

```bash
./build.sh
```

`node render.js --at 0.8 7.9` writes single preview PNGs to `out/preview/`. Set `FPS=30` to render at 30 fps.
