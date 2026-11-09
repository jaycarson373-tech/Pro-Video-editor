#!/usr/bin/env bash
# Rebuild perply-hype.mp4 from source: soundtrack -> frames -> encode.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out
python3 music.py out/music.wav
node render.js
ffmpeg -hide_banner -loglevel error -y -framerate 30 -i out/frames/f%05d.jpg -i out/music.wav \
  -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -c:a aac -b:a 256k -shortest -movflags +faststart \
  perply-hype.mp4
echo "done: perply-hype.mp4"
