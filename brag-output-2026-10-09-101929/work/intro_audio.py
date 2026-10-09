# Synthesises the 42s purpose & scope intro bed: calm D-major pad and arp that build into the "7,716" hook.
import numpy as np, wave

SR = 44100
DUR = 42.0
N = int(SR * DUR)
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(11)

CUTS = [5.5, 12, 19, 25.5, 31]

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

def pluck(m, dur=1.2, tau=0.35, bright=0.35):
    t = np.arange(int(dur * SR)) / SR; f = hz(m)
    s = np.sin(2 * np.pi * f * t) + bright * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.08) + 0.12 * np.sin(6 * np.pi * f * t) * np.exp(-t / 0.05)
    return s * np.minimum(1, t / 0.004) * np.exp(-t / tau)

def pad(notes, dur):
    t = np.arange(int(dur * SR)) / SR; s = np.zeros_like(t)
    for m in notes:
        for d in (-0.06, 0.0, 0.07):
            f = hz(m + d)
            s += np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    return s * np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.5) / (3 * len(notes))

D, Bm, G, A = [50, 54, 57, 62], [47, 50, 54, 59], [43, 50, 55, 59], [45, 49, 52, 57]
ROOT = {id(D): 38, id(Bm): 35, id(G): 31, id(A): 33}
# problem (I1-I2) sits on the minor side; opportunity onward lifts to the verse progression
def chord_at(t):
    b = int(t // BAR)
    if t < 12: return [Bm, G, D, A][b % 4]
    return [D, Bm, G, A][b % 4]

nbars = int(np.ceil(DUR / BAR))
for b in range(nbars):
    t0 = b * BAR
    add(L, R, lowpass(pad(chord_at(t0 + 0.01), BAR + 0.6), 1500 if t0 < 12 else 2200), t0, 0.17)

# soft bass from the opportunity scene
for bt in np.arange(12, DUR, BEAT):
    add(L, R, lowpass(pluck(ROOT[id(chord_at(bt + 0.01))], 0.9, 0.3, 0.1), 450), bt, 0.12)

# arp: sparse quarters during the problem, eighths from the opportunity
for i, et in enumerate(np.arange(5.5, DUR, BEAT / 2)):
    if et < 12 and i % 2: continue
    c = chord_at(et + 0.01)
    m = [c[0] + 12, c[2] + 12, c[1] + 12, c[3] + 12][i % 4]
    add(L, R, lowpass(pluck(m, 0.8, 0.22, 0.4), 3200), et, 0.045 if et < 19 else 0.06, pan=-0.35 if i % 2 else 0.35)

# swells into each cut, and a longer rise into the hook
def swell(t_end, length=0.55, gain=0.05):
    n = int(length * SR); x = rng.standard_normal(n)
    x = lowpass(x, 2200) - lowpass(x, 300)
    e = (np.arange(n) / n) ** 2.2; e[-int(0.04 * SR):] *= np.linspace(1, 0, int(0.04 * SR))
    add(fx_L, fx_R, x * e, t_end - length, gain, pan=-0.2)
    add(fx_L, fx_R, x * e, t_end - length + 0.01, gain * 0.7, pan=0.2)

for c in CUTS: swell(c)
swell(DUR, 1.6, 0.08)

# soft plucks as cards land
for tp, m in ((12.5, 69), (13.3, 71), (14.1, 74), (19.5, 69), (20.2, 74)):
    add(fx_L, fx_R, pluck(m, 1.2, 0.4, 0.15), tp, 0.04)
for k in range(6):
    add(fx_L, fx_R, pluck([74, 76, 78, 81, 83, 86][k], 0.5, 0.12, 0.2), 25.95 + k * 0.22, 0.025)
    add(fx_L, fx_R, pluck([62, 66, 69, 74, 78, 81][k], 0.8, 0.25, 0.2), 31.5 + k * 0.6, 0.03)

def reverb(x, tau=1.1, mix=0.18):
    n = int(2.5 * SR); ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / (tau / 3))
    ir = lowpass(ir, 4000); ir /= np.sqrt(np.sum(ir ** 2))
    F = 1 << int(np.ceil(np.log2(len(x) + n)))
    return x + mix * np.fft.irfft(np.fft.rfft(x, F) * np.fft.rfft(ir, F), F)[: len(x)]

ML = reverb(L + 0.8 * fx_L); MR = reverb(R + 0.8 * fx_R)
fi = int(0.5 * SR); ML[:fi] *= np.linspace(0, 1, fi); MR[:fi] *= np.linspace(0, 1, fi)
fo = int(0.03 * SR); ML[-fo:] *= np.linspace(1, 0, fo); MR[-fo:] *= np.linspace(1, 0, fo)

peak = max(np.abs(ML).max(), np.abs(MR).max())
data = (np.stack([ML, MR], 1) / peak * 0.89 * 32767).astype(np.int16)
with wave.open('intro.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
print('ok', DUR)
