#!/usr/bin/env bash
# Rebuild perpspad-chill.mp4 (chill cut): soundtrack -> frames -> encode.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p chill/out
python3 chill/music.py chill/out/music.wav
node chill/render.js
ffmpeg -hide_banner -loglevel error -y -framerate 60 -i chill/out/frames/f%05d.jpg -i chill/out/music.wav \
  -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p -c:a aac -b:a 320k -shortest -movflags +faststart \
  perpspad-chill.mp4
echo "done: perpspad-chill.mp4"
