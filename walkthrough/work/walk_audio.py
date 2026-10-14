# Soundtrack for the walkthrough: voice-over lines placed per timeline.json over a soft music bed
# that ducks under speech and resolves on the outro. Writes walk.wav (48 kHz stereo).
import json, wave
import numpy as np

SR = 48000
steps = json.load(open('timeline.json'))
DUR = steps[-1]['end']
N = int(SR * DUR)
BEAT = 60 / 96
BAR = 4 * BEAT
rng = np.random.default_rng(3)

def hz(m): return 440 * 2 ** ((m - 69) / 12)

def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s; y[i] = s
    return y

def pluck(m, dur=1.0, tau=0.3, bright=0.3):
    t = np.arange(int(dur * SR)) / SR; f = hz(m)
    s = np.sin(2 * np.pi * f * t) + bright * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.08)
    return s * np.minimum(1, t / 0.004) * np.exp(-t / tau)

def pad(notes, dur):
    t = np.arange(int(dur * SR)) / SR; s = np.zeros_like(t)
    for m in notes:
        for d in (-0.05, 0.0, 0.06):
            f = hz(m + d); s += np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    return s * np.minimum(1, t / 0.8) * np.minimum(1, (dur - t) / 0.6) / (3 * len(notes))

L = np.zeros(N); R = np.zeros(N)
def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N: return
    sig = sig[: N - i] * gain
    L[i:i + len(sig)] += sig * np.sqrt((1 - pan) / 2); R[i:i + len(sig)] += sig * np.sqrt((1 + pan) / 2)

# music: G - D - Em - C, soft pad + gentle arp + light pulse
CH = [[43, 50, 55, 59], [38, 50, 54, 57], [40, 52, 55, 59], [36, 48, 52, 55]]
for b in range(int(np.ceil(DUR / BAR))):
    add(lowpass(pad(CH[b % 4], BAR + 0.8), 1800), b * BAR, 0.16)
    add(lowpass(pluck(CH[b % 4][0], 1.6, 0.5, 0.1), 400), b * BAR, 0.16)
for i, t in enumerate(np.arange(0, DUR, BEAT / 2)):
    c = CH[int(t // BAR) % 4]
    add(lowpass(pluck([c[1] + 12, c[2] + 12, c[3] + 12, c[2] + 12][i % 4], 0.6, 0.18), 3000), t, 0.05, pan=-0.3 if i % 2 else 0.3)
outro = steps[-1]['start']
for j, m in enumerate((67, 74, 79)):
    add(pluck(m, 2.5, 0.9, 0.1), outro + 0.1 + j * 0.05, 0.06)

# voice-over
vo = np.zeros(N)
for s in steps:
    w = wave.open(f"vo/{s['id']}.wav"); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    x = np.interp(np.arange(int(len(x) * SR / sr)) * sr / SR, np.arange(len(x)), x)   # resample to 48k
    i = int(s['vo_start'] * SR); vo[i:i + len(x)] += x[: N - i]

# duck the music under speech (smoothed envelope), fade the ends
env = np.convolve(np.abs(vo) > 0.01, np.ones(int(0.25 * SR)) / int(0.25 * SR), mode='same')
duck = 1 - 0.55 * np.clip(env * 3, 0, 1)
music_gain = 0.55
L, R = L * duck * music_gain, R * duck * music_gain
fi, fo = int(0.6 * SR), int(1.2 * SR)
for x in (L, R):
    x[:fi] *= np.linspace(0, 1, fi); x[-fo:] *= np.linspace(1, 0, fo) ** 1.5

vo_n = vo / (np.abs(vo).max() + 1e-9) * 0.8
mL, mR = L / (max(np.abs(L).max(), np.abs(R).max()) + 1e-9) * 0.35, R / (max(np.abs(L).max(), np.abs(R).max()) + 1e-9) * 0.35
outL, outR = vo_n + mL, vo_n + mR
p = max(np.abs(outL).max(), np.abs(outR).max())
data = (np.stack([outL, outR], 1) / p * 0.9 * 32767).astype(np.int16)
with wave.open('walk.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
print('ok', DUR)
