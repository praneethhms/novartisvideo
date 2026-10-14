#!/usr/bin/env bash
# Encodes the portrait walkthrough: frames-walk (from walk.html) + walk.wav -> ../walkthrough.mp4
# Frame 0 is replaced by the settled intro card so thumbnails show it.
set -euo pipefail
cd "$(dirname "$0")"
[ -f walk-frame0-orig.jpg ] || cp frames-walk/f0000.jpg walk-frame0-orig.jpg
cp frames-walk/f0075.jpg ../walkthrough.jpg
cp ../walkthrough.jpg frames-walk/f0000.jpg
ffmpeg -hide_banner -loglevel error -y -framerate 30 -i frames-walk/f%04d.jpg -i walk.wav \
  -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart ../walkthrough.mp4
ffprobe -v error -show_entries format=duration,size:stream=width,height -of compact ../walkthrough.mp4
