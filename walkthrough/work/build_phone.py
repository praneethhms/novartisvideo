# Builds the 60s timeline from the voice-over lengths, then renders the phone track:
# pieces of the two screen recordings, sped to fit each step, with the SOS contact blurred.
# Writes timeline.json and phone.mp4 (996x2160, 30fps). Usage: python3 build_phone.py
import json, subprocess, wave

FPS, TOTAL, GAP, LEAD = 30, 60.0, 0.85, 0.3
A, B, C = 'src/recA_blur.mp4', 'src/recB.mp4', 'src/recC.mp4'  # recA_blur: contact blurred by blur_sos.py; recC: working hours

# (source, in, out) pieces per step, in seconds of the original recordings (true PTS; recB is VFR)
PIECES = {
    'intro':     [(A, 0.0, 1.4)],
    'home':      [(B, 0.0, 4.4)],
    'passenger': [(B, 5.0, 9.0), (B, 21.0, 25.9)],     # vehicle menu with Passenger Mode; passenger timer
    'hours':     [(C, 2.4, 13.4), (B, 27.0, 32.9)],    # working hours (recC 0-2s is the profile screen); personal mode
    'scores':    [(B, 45.0, 50.5)],                    # smoothness tooltip
    'improve':   [(B, 53.0, 60.0)],                    # improvement suggestion, news feed
    'trips':     [(B, 72.0, 78.0)],                    # trip list once loaded
    'trip':      [(B, 80.0, 82.5), (B, 88.0, 93.0)],   # trip summary, map with events
    'reports':   [(B, 97.0, 100.0), (B, 106.0, 108.5)],# weekly, monthly
    'sos':       [(A, 1.3, 7.6)],
    'more':      [(B, 119.6, 122.6), (B, 127.2, 128.4)],# documents, languages (stops short of the profile screen)
    'outro':     [(B, 35.0, 36.6)],
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
        src_lab = {A: 'A', B: '1:v', C: '2:v'}[src]
        parts.append(f"[{'s' + lab}]trim={i}:{o},setpts=(PTS-STARTPTS)/{speed:.5f},fps={FPS},"
                     f"scale=996:2160:flags=lanczos,setsar=1,tpad=stop_mode=clone:stop_duration=2,trim=end_frame={want},setpts=PTS-STARTPTS[{lab}]")
        labels.append((src_lab, lab))
    s['speed'] = round(speed, 2)

# fan out each source to as many trims as it feeds
fan = []
for src_lab in ('A', '1:v', '2:v'):
    labs = [lab for s_, lab in labels if s_ == src_lab]
    fan.append(f"[{src_lab}]split={len(labs)}" + ''.join(f'[s{l}]' for l in labs))
graph = ';'.join([parts[0]] + fan + parts[1:] + [''.join(f'[{l}]' for _, l in labels) + f'concat=n={len(labels)}:v=1:a=0[v]'])

subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', A, '-i', B, '-i', C,
                '-filter_complex', graph, '-map', '[v]', '-an', '-c:v', 'libx264', '-crf', '14', '-preset', 'fast',
                '-pix_fmt', 'yuv420p', 'phone.mp4'], check=True)
json.dump(steps, open('timeline.json', 'w'), indent=1)
for s in steps:
    print(f"{s['id']:8s} {s['start']:6.2f}-{s['end']:6.2f}  vo {s['vo_len']:.2f}  speed {s['speed']}x")
