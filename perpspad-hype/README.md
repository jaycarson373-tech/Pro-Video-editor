# Perps Pad hype video

`perpspad-hype.mp4` is a 23-second, 1920×1080, 60 fps promo for Perps Pad ($PERPS, [perpspad.live](https://perpspad.live), [@Perpspad_live](https://x.com/Perpspad_live)). It's built from the live site at perps-pad-seven.vercel.app.

Everything is generated from code, including the soundtrack: an original 150 BPM track in D minor (Dm–B♭–F–C) synthesized in `music.py`. Every cut, flash and shake sits on the same beat grid (1 beat = 0.4 s).

| Time | Section |
| --- | --- |
| 0.0–3.2 | LAUNCH / A COIN. / GIVE / IT / A STRATEGY. |
| 3.2 | Drop 1: app-icon slam, `perpspad` wordmark, `$PERPS` chip |
| 4.8–9.6 | LONG HYPE. / SHORT BTC. / OR BUILD YOUR OWN MIX. (HYPE, ETH, SOL tiles) |
| 9.6–12.8 | The Perps Pad engine: fees in, positions open, profits routed back to coin buybacks |
| 12.8–14.4 | Strobe: MULTI-PAIR. / LONG & SHORT. / FEE ROUTING. / RISK LIMITS. |
| 14.4–16.0 | Build: $P-$PE-$PER-$PERP-$PERPS stutter, then a silent beat |
| 16.0 | Drop 2: giant $PERPS, "Coins with a strategy." |
| 17.6–19.2 | Strategy builder on perpspad.live/launch, typing "Perps Pad" / "PERPS" |
| 19.2–23.0 | Lockup, "Build your coin →", perpspad.live, $PERPS, @Perpspad_live, risk line |

All copy, colors (`#061b1e`, `#98f4ce`, `#19d6bd`, `#f1b3b7`), the DM Sans font and the logo come from the site. The engine diagram uses the site's own labeled example strategy (60% HYPE long 3×, 40% BTC short 2×). The closing line matches the site's status: the strategy builder is live and execution is coming next.

## Rebuild

```bash
./build.sh
```

`node render.js --at 3.4 16.3` writes single preview PNGs to `out/preview/`. Set `FPS=30` to render at 30 fps.

## Chill cut

`perpspad-chill.mp4` runs 31 s at 1080p60. It's a calmer edit set to an original 96 BPM lo-fi house track (Dm9–B♭maj7–Fmaj7–C6/9, with electric-piano keys, vinyl texture and soft drums). It uses slow eases, cross-dissolves and sentence-case site typography, with no strobes or glitches. It adds a burn section: "20% of fees from coins launched on Perps Pad burn $PERPS."

Note: the site's guide page currently says "No $PERPS buyback percentage or token contract is configured." Update it so the site matches the burn claim.

```bash
chill/build.sh
```

`node chill/render.js --at 20.6` writes preview frames to `chill/out/preview/`.

## Logo spin GIF

`perpspad-logo-spin.gif` (480px, loops) and `perpspad-logo-spin.mp4` (1080×1080) show the logo spinning fast in 3D with motion blur and RGB-split/slice glitches. It locks in with a flash and holds still for 2.2 s.

```bash
python3 logo-spin.py assets/brand/perps-pad-podium.png perpspad-logo-spin
```
