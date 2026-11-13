#!/usr/bin/env bash
# Rebuild both Optima promo videos from source: soundtrack -> frames -> encode.
# Edit config.json first if a number, the domain or the contract address changes.
set -euo pipefail
cd "$(dirname "$0")"
[ -d node_modules/three ] || npm install --no-audit --no-fund
mkdir -p out
python3 music.py out/music.wav
AF="volume=3.0dB,alimiter=limit=0.76:attack=2:release=40:level=false"
for fmt in v h; do
  node render.js "$fmt"
  name=$([ "$fmt" = v ] && echo optima-promo-9x16.mp4 || echo optima-promo-16x9.mp4)
  ffmpeg -hide_banner -loglevel error -y -framerate 24 -i "out/frames-$fmt/f%05d.jpg" -i out/music.wav -af "$AF" \
    -c:v libx264 -preset slow -crf 16 -profile:v high -pix_fmt yuv420p -r 24 -c:a aac -b:a 320k -shortest -movflags +faststart "$name"
  echo "done: $name"
done
