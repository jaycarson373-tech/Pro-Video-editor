#!/usr/bin/env bash
# Rebuild gpupad-promo.mp4 from source: soundtrack -> frames -> encode.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out
python3 music.py out/music.wav
node render.js
ffmpeg -hide_banner -loglevel error -y -framerate 60 -i out/frames/f%05d.jpg -i out/music.wav \
  -c:v libx264 -preset slow -crf 17 -profile:v high -pix_fmt yuv420p -c:a aac -b:a 320k -shortest -movflags +faststart \
  gpupad-promo.mp4
echo "done: gpupad-promo.mp4"
