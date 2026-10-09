#!/usr/bin/env bash
# Builds the full video: purpose & scope intro (42s) -> 60s launch video -> customer feedback clip.
# Usage: ./assemble.sh <customer-clip.mp4>
set -euo pipefail
cd "$(dirname "$0")"
CLIP="$1"
OUT=../brag-full.mp4

# Frame 0 of the main video is the 60s cut's poster; use the original first frame inside the long cut.
mkdir -p main-frames
for f in frames/f*.jpg; do ln -sf "../$f" "main-frames/$(basename "$f")"; done
ln -sf ../frame0-orig.jpg main-frames/f0000.jpg

# Poster for the long cut: the settled problem statement, baked in as frame 0.
[ -f intro-frame0-orig.jpg ] || cp frames-intro/f0000.jpg intro-frame0-orig.jpg
cp frames-intro/f0150.jpg ../brag-full.jpg
cp ../brag-full.jpg frames-intro/f0000.jpg

ffmpeg -hide_banner -loglevel error -y \
  -framerate 30 -i frames-intro/f%04d.jpg \
  -framerate 30 -i main-frames/f%04d.jpg \
  -i intro.wav -i music.wav -i "$CLIP" \
  -filter_complex "\
[0:v]setsar=1,format=yuv420p[vi];\
[1:v]setsar=1,format=yuv420p[vm];\
[vi][vm]concat=n=2:v=1:a=0,fade=t=out:st=101.4:d=0.6:color=white[v0];\
[4:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:white,fps=30,setsar=1,fade=t=in:st=0:d=0.6:color=white,format=yuv420p[v1];\
[2:a]volume=-3.5dB[ia];[ia][3:a]concat=n=2:v=0:a=1,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,atrim=0:102[a0];\
[4:a]aresample=48000,pan=stereo|c0=c0|c1=c0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,afade=t=in:st=0:d=0.2[a1];\
[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart "$OUT"

ffprobe -v error -show_entries format=duration,size -of compact "$OUT"
