# Builds the 60s timeline from the voice-over lengths, then renders the phone track:
# pieces of the two screen recordings, sped to fit each step, with the SOS contact blurred.
# Writes timeline.json and phone.mp4 (996x2160, 30fps). Usage: python3 build_phone.py
import json, subprocess, wave

FPS, TOTAL, GAP, LEAD = 30, 60.0, 0.85, 0.3
A, B = 'src/recA_blur.mp4', 'src/recB.mp4'  # recA_blur: contact blurred by blur_sos.py

# (source, in, out) pieces per step, in seconds of the original recordings
PIECES = {
    'intro':   [(A, 0.0, 1.4)],
    'home':    [(B, 0.0, 3.6)],
    'modes':   [(B, 4.0, 8.2), (B, 26.0, 33.6)],
    'scores':  [(B, 36.0, 51.0)],
    'improve': [(B, 51.0, 60.0)],
    'trips':   [(B, 69.0, 77.0)],
    'trip':    [(B, 78.0, 95.0)],
    'reports': [(B, 95.5, 100.0), (B, 105.5, 110.5)],
    'sos':     [(A, 1.3, 7.6)],
    'more':    [(B, 119.6, 122.4), (B, 125.0, 128.5)],
    'outro':   [(B, 33.6, 35.0)],
}

script = json.load(open('script.json'))
def wav_len(p):
    w = wave.open(p); return w.getnframes() / w.getframerate()

steps, t = [], 0.0
for i, line in enumerate(script):
    vo = wav_len(f"vo/{line['id']}.wav")
    dur = vo + GAP if i < len(script) - 1 else TOTAL - t
    steps.append(dict(id=line['id'], title=line['title'], caption=line['caption'],
                      start=round(t, 3), end=round(t + dur, 3), vo_start=round(t + LEAD, 3), vo_len=round(vo, 3)))
    t += dur
assert abs(t - TOTAL) < 1e-6 and steps[-1]['end'] - steps[-1]['start'] > steps[-1]['vo_len'] + LEAD
json.dump(steps, open('timeline.json', 'w'), indent=1)

parts, labels = ["[0:v]null[A]"], []
n = 0
for s in steps:
    pieces = PIECES[s['id']]
    src_len = sum(o - i for _, i, o in pieces)
    seg_frames = round(s['end'] * FPS) - round(s['start'] * FPS)
    speed = src_len / (seg_frames / FPS)
    acc = 0.0
    for k, (src, i, o) in enumerate(pieces):
        acc += o - i
        want = round(acc / src_len * seg_frames) - round((acc - (o - i)) / src_len * seg_frames)
        lab = f'p{n}'; n += 1
        src_lab = 'A' if src == A else '1:v'
        parts.append(f"[{'s' + lab}]trim={i}:{o},setpts=(PTS-STARTPTS)/{speed:.5f},fps={FPS},"
                     f"scale=996:2160:flags=lanczos,setsar=1,tpad=stop_mode=clone:stop_duration=2,trim=end_frame={want},setpts=PTS-STARTPTS[{lab}]")
        labels.append((src_lab, lab))
    s['speed'] = round(speed, 2)

# fan out each source to as many trims as it feeds
fan = []
for src_lab in ('A', '1:v'):
    labs = [lab for s_, lab in labels if s_ == src_lab]
    fan.append(f"[{src_lab}]split={len(labs)}" + ''.join(f'[s{l}]' for l in labs))
graph = ';'.join([parts[0]] + fan + parts[1:] + [''.join(f'[{l}]' for _, l in labels) + f'concat=n={len(labels)}:v=1:a=0[v]'])

subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', A, '-i', B,
                '-filter_complex', graph, '-map', '[v]', '-an', '-c:v', 'libx264', '-crf', '14', '-preset', 'fast',
                '-pix_fmt', 'yuv420p', 'phone.mp4'], check=True)
json.dump(steps, open('timeline.json', 'w'), indent=1)
for s in steps:
    print(f"{s['id']:8s} {s['start']:6.2f}-{s['end']:6.2f}  vo {s['vo_len']:.2f}  speed {s['speed']}x")
