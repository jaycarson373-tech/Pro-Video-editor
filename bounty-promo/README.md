# BOUNTY promo video

`bounty-promo.mp4` is a 23-second vertical (1080×1920, 30 fps) promo for BOUNTY ([GTA6Bounties.xyz](https://www.gta6bounties.xyz/), $BOUNTY), a community site of player-made GTA VI challenges.

Everything is generated from code. The city, palms, helicopter, police car and banknotes are original drawings made in `scene.html`; no game footage or Rockstar artwork is used. The soundtrack (an original 150 BPM retro-trap track with a siren, coin and register effects) is synthesized in `music.py`.

| Time | Scene |
| --- | --- |
| 0–3.2 | Sirens: "PULL IT OFF. CLIP IT. GET PAID." |
| 3.2–4.8 | Logo slam, "PLAYER-MADE GTA VI CHALLENGES", $BOUNTY |
| 4.8–8.0 | Bounty #001: 1 SOL, six stars pop, "SIX STARS. FIVE MINUTES.", survival clock to 5:00 |
| 8.0–11.2 | Bounty #002: 0.5 SOL, police car, "LOSE THE HEAT.", wanted level drains to zero |
| 11.2–14.4 | How it works: hold 2.5M+ $BOUNTY, clip it, get paid; fees fill the pool, no team supply |
| 14.4–16.0 | Next bounties #003 and #004: classified, drop when the pool fills |
| 16.0–19.2 | "2 BOUNTIES LIVE · 1.5 SOL UP FOR GRABS", cash rain, "No entry fees. No wagers." |
| 19.2–23.0 | Logo, GTA6BOUNTIES.XYZ, "Submit a clip", disclaimer |

All rewards, rules and wording come from the site. The end card carries the site's own disclaimers: an independent community project, not affiliated with Rockstar Games or Take-Two, and payouts are not live yet.

## Rebuild

```bash
python3 music.py out/music.wav
node render.js
ffmpeg -framerate 30 -i out/frames/f%05d.jpg -i out/music.wav -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 320k -shortest -movflags +faststart bounty-promo.mp4
```

`node render.js --at 5.5 16.2` writes single preview frames to `out/preview/`.
