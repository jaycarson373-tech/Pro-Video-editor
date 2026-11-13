# Optima promo video

A 30-second promo for Optima ([UseOptima.fun](https://www.useoptima.fun/), $OPTIMA) in two formats, both 24 fps:

- `optima-promo-9x16.mp4`: vertical, 1080×1920
- `optima-promo-16x9.mp4`: widescreen, 1920×1080

Everything is generated from code. The ring is a real 3D object (three.js, studio softbox lighting) rendered in headless Chromium. The soundtrack and every sound effect are synthesized in `music.py` at 120 BPM, and every cut sits on a beat with a bass hit. There is no voiceover; the cut is text only.

| Time | Scene |
| --- | --- |
| 0–4 | Hook: payment notifications stack up with dings and turn red. "You're overpaying for AI." |
| 4–8 | Switch: the red stack shatters, the ring drops in and lands. "OPTIMA", "The cheaper way to use AI." |
| 8–14 | Proof: "Them" flat-fee bar vs a tiny "Optima" pay-per-use bar, then a receipt prints out of the ring |
| 14–18 | How: one prompt goes into the ring, passes two doors that are overkill and takes the smallest that fits |
| 18–24 | Rewards: USE and HOLD coins orbit the ring, tokens burn into embers, fee split |
| 24–30 | End card: "Stop overpaying.", domain, ticker. The final frame is held for the last 2.5 s |

## Numbers

Every number on screen comes from `config.json`, and the values there match UseOptima.fun as of 13 November 2026:

- Cost planner defaults: $40.00 a month, 30 messages a day, break-even $0.0444 per message, $480.00 a year.
- Fee design: 75% holder and user rewards, 15% buyback and burn, 10% treasury.

The brief asked for a price per answer, a savings percentage and a contract address. The site publishes none of these yet: it says there is no rate card, that it does not claim Optima is cheaper, that rewards are not active, and that the token mint is awaiting verification. So Scene 3 uses the cost-planner math and "Pay per use." instead of "Up to X% less", Scene 5 says the rewards are a fee design that is not active yet, and the end card shows `$OPTIMA` instead of a contract address.

To switch to the brief's original lines once the numbers exist, fill these in `config.json` and rebuild:

- `savingsPercent`, `whatIsCompared`, `pricesCheckedDate`: Scene 3 becomes "Same question. Up to X% less." with the small print under it.
- `pricePerAnswer`: the receipt gains a "1 answer $X" line.
- `tokenMint`: the end card shows "CA: …".

The `-$20.00` charge in Scene 1 is the brief's own example of a subscription payment (`subscriptionCharge`); it is not an Optima number.

## Rebuild

Needs Python 3 with numpy and scipy, Node with Playwright (Chromium), and ffmpeg. Each format takes about 8 minutes to render.

```bash
./build.sh
```

`node render.js v --at 5.1 12.3` writes single preview frames to `out/preview/` (use `h` for widescreen).

- `scene.html`: all six scenes; `render(t)` draws the frame at time `t`, `?fmt=v|h` picks the layout
- `ring3d.js`: the 3D ring and coins
- `music.py`: soundtrack and sound effects
- `config.json`: every number, the domain, the ticker and the contract address
