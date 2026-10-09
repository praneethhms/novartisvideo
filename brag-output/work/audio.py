# Synthesises the soundtrack: restrained D-major corporate bed + in-key sound effects.
import numpy as np, wave

SR = 44100
DUR = 22.4
N = int(SR * DUR)
BPM = 100
BEAT = 60 / BPM
rng = np.random.default_rng(7)

L = np.zeros(N); R = np.zeros(N)
fx_L = np.zeros(N); fx_R = np.zeros(N)

def hz(m): return 440 * 2 ** ((m - 69) / 12)

def add(buf_l, buf_r, sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N: return
    sig = sig[: N - i] * gain
    buf_l[i:i + len(sig)] += sig * np.sqrt((1 - pan) / 2)
    buf_r[i:i + len(sig)] += sig * np.sqrt((1 + pan) / 2)

def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s; y[i] = s
    return y

def env(n, att, rel_tau):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(att, 1e-4)) * np.exp(-t / rel_tau)

def pluck(m, dur=1.2, tau=0.35, bright=0.35):
    t = np.arange(int(dur * SR)) / SR; f = hz(m)
    s = np.sin(2 * np.pi * f * t) + bright * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.08) + 0.12 * np.sin(6 * np.pi * f * t) * np.exp(-t / 0.05)
    return s * env(len(t), 0.004, tau)

def pad(notes, dur):
    t = np.arange(int(dur * SR)) / SR; s = np.zeros_like(t)
    for m in notes:
        for d in (-0.06, 0.0, 0.07):
            f = hz(m + d)
            s += np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    a = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.5)
    return s * a / (3 * len(notes))

# progression: D  Bm  G  A, one bar (4 beats) each
CH = [[50, 54, 57, 62], [47, 50, 54, 59], [43, 50, 55, 59], [45, 49, 52, 57]]
ROOT = [38, 35, 31, 33]
BAR = 4 * BEAT
nbars = int(np.ceil(DUR / BAR))

# --- pad (whole piece), opens up after the hook
for b in range(nbars):
    t0 = b * BAR; c = CH[b % 4]
    if t0 >= 18.8: c = CH[0]
    g = 0.17 if t0 < 3.6 else 0.13
    add(L, R, lowpass(pad(c, BAR + 0.6), 1400 if t0 < 3.6 else 2400), t0, g)

# final sustained D chord for the outro
add(L, R, lowpass(pad([50, 54, 57, 62, 66], DUR - 18.8 + 0.2), 2600), 18.8, 0.15)

# --- bass + kick + arp from the reveal until the outro
beat_times = np.arange(0, DUR, BEAT)
for bt in beat_times:
    if not (3.6 - 1e-3 <= bt < 18.8): continue
    b = int(bt // BAR); root = ROOT[b % 4]
    bl = pluck(root, 0.9, 0.28, 0.15); add(L, R, lowpass(bl, 500), bt, 0.16)
    # soft kick on 1 and 3
    if int(round(bt / BEAT)) % 2 == 0:
        t = np.arange(int(0.35 * SR)) / SR
        f = 48 + 70 * np.exp(-t / 0.03)
        k = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)
        add(L, R, k, bt, 0.24)

eighth = BEAT / 2
for i, et in enumerate(np.arange(3.6, 18.8, eighth)):
    b = int(et // BAR); c = CH[b % 4]
    seq = [c[0] + 12, c[2] + 12, c[1] + 12, c[3] + 12]
    m = seq[i % 4]
    g = 0.055 if et < 7.6 else 0.07
    add(L, R, lowpass(pluck(m, 0.8, 0.22, 0.4), 3500), et, g, pan=-0.35 if i % 2 else 0.35)

# light hat on the off-beats after the glance scene
for et in np.arange(7.6 + eighth, 18.8, BEAT):
    n = int(0.06 * SR); h = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / 0.015)
    h = h - lowpass(h, 6000)
    add(L, R, h, et, 0.035, pan=0.2)

# --- sound effects (same key, mixed under the music)
def swell(t_end, length=0.55, gain=0.05):
    n = int(length * SR); x = rng.standard_normal(n)
    x = lowpass(x, 2200) - lowpass(x, 300)
    e = (np.arange(n) / n) ** 2.2; e[-int(0.04 * SR):] *= np.linspace(1, 0, int(0.04 * SR))
    add(fx_L, fx_R, x * e, t_end - length, gain, pan=-0.2)
    add(fx_L, fx_R, x * e, t_end - length + 0.01, gain * 0.7, pan=0.2)

for c in (3.6, 7.6, 11.4, 15.6, 18.8):
    swell(c)

def ticks(t0, t1, notes, gain=0.035):
    # decelerating ticks that follow an ease-out counter
    k = 0; t = t0; gap = 0.045
    while t < t1:
        add(fx_L, fx_R, lowpass(pluck(notes[k % len(notes)], 0.25, 0.05, 0.2), 5000), t, gain, pan=0.15 * (-1) ** k)
        k += 1; gap *= 1.16; t += gap

ticks(0.1, 1.3, [74, 78, 81])
ticks(8.1, 9.4, [74, 78, 81])
ticks(11.75, 12.7, [74, 78, 81])
ticks(16.25, 17.1, [74, 78, 81])

# hook: soft low impact under the first number
t = np.arange(int(1.6 * SR)) / SR
boom = np.sin(2 * np.pi * hz(38) * t) * np.exp(-t / 0.5) + 0.4 * np.sin(2 * np.pi * hz(50) * t) * np.exp(-t / 0.4)
add(fx_L, fx_R, boom, 0.1, 0.22)

# bell accents: 76% callout, final line
for tb, ms, g in ((13.4, [74, 81], 0.06), (20.25, [62, 69, 74], 0.07)):
    for j, m in enumerate(ms):
        add(fx_L, fx_R, pluck(m, 2.5, 0.9, 0.1), tb + j * 0.04, g, pan=0.1 * (j - 1))

# --- shared space: one reverb for music + fx so it sits together
def reverb(x, tau=1.1, mix=0.18):
    n = int(2.5 * SR); ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / (tau / 3))
    ir = lowpass(ir, 4000); ir /= np.sqrt(np.sum(ir ** 2))
    m = len(x) + n; F = 1 << int(np.ceil(np.log2(m)))
    wet = np.fft.irfft(np.fft.rfft(x, F) * np.fft.rfft(ir, F), F)[: len(x)]
    return x + mix * wet

ML = reverb(L + 0.8 * fx_L); MR = reverb(R + 0.8 * fx_R)

# fade out ending
fo = int(1.2 * SR); ML[-fo:] *= np.linspace(1, 0, fo) ** 1.5; MR[-fo:] *= np.linspace(1, 0, fo) ** 1.5
fi = int(0.02 * SR); ML[:fi] *= np.linspace(0, 1, fi); MR[:fi] *= np.linspace(0, 1, fi)

peak = max(np.abs(ML).max(), np.abs(MR).max())
ML, MR = ML / peak * 0.89, MR / peak * 0.89
data = (np.stack([ML, MR], 1) * 32767).astype(np.int16)
with wave.open('music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
print('ok', DUR)
