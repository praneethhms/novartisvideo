#!/usr/bin/env bash
# Builds the under-a-minute cut: purpose & scope + results (frames-short 0-38.5s)
# -> feedback soundbite (clip 0:34.25-0:50.10, with the lower third) -> outro card (frames-short 38.5-41.5s).
# Usage: ./assemble-short.sh <customer-clip.mp4>
set -euo pipefail
cd "$(dirname "$0")"
CLIP="$1"
OUT=../brag-short.mp4
CLIP_IN=34.25
CLIP_OUT=50.10
CLIP_LEN=$(python3 -c "print(round($CLIP_OUT - $CLIP_IN, 3))")

# Poster: the settled 15x chart, baked in as frame 0.
[ -f short-frame0-orig.jpg ] || cp frames-short/f0000.jpg short-frame0-orig.jpg
cp frames-short/f1020.jpg ../brag-short.jpg
cp ../brag-short.jpg frames-short/f0000.jpg

ffmpeg -hide_banner -loglevel error -y \
  -framerate 30 -i frames-short/f%04d.jpg \
  -framerate 30 -start_number 1155 -i frames-short/f%04d.jpg \
  -i short-a.wav -i short-outro.wav \
  -ss "$CLIP_IN" -to "$CLIP_OUT" -i "$CLIP" \
  -framerate 30 -i frames-lowerthird/f%04d.png \
  -filter_complex "\
[0:v]trim=end_frame=1155,setpts=PTS-STARTPTS,setsar=1,format=yuv420p[va];\
[1:v]trim=end_frame=90,setpts=PTS-STARTPTS,setsar=1,format=yuv420p[vo];\
[4:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:white,fps=30,setsar=1,setpts=PTS-STARTPTS[vc];\
[vc][5:v]overlay=0:0:eof_action=repeat:shortest=1,fade=t=in:st=0:d=0.5:color=white,fade=t=out:st=$(python3 -c "print($CLIP_LEN - 0.5)"):d=0.5:color=white,format=yuv420p[vf];\
[2:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,atrim=0:38.5[aa];\
[4:a]asetpts=PTS-STARTPTS,aresample=48000,pan=stereo|c0=c0|c1=c0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,afade=t=in:st=0:d=0.15,afade=t=out:st=$(python3 -c "print($CLIP_LEN - 0.35)"):d=0.35,apad,atrim=0:$CLIP_LEN[af];\
[3:a]volume=-6dB,aresample=48000,aformat=channel_layouts=stereo[ao];\
[va][aa][vf][af][vo][ao]concat=n=3:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart "$OUT"

ffprobe -v error -show_entries format=duration,size -of compact "$OUT"
