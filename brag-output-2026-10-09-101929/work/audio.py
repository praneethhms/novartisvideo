# Synthesises the 60s soundtrack: restrained D-major bed arranged in sections + in-key sound effects.
import numpy as np, wave

SR = 44100
DUR = 60.0
N = int(SR * DUR)
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(7)

CUTS = [4, 8.5, 15.5, 20, 25.5, 30, 34.5, 39.5, 45, 52, 56.5]
OUTRO = 56.5

L = np.zeros(N); R = np.zeros(N)
fx_L = np.zeros(N); fx_R = np.zeros(N)

def hz(m): return 440 * 2 ** ((m - 69) / 12)
def within(t, ranges): return any(a - 1e-3 <= t < b for a, b in ranges)

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

def env(n, att, tau):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(att, 1e-4)) * np.exp(-t / tau)

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

D, Bm, G, A = [50, 54, 57, 62], [47, 50, 54, 59], [43, 50, 55, 59], [45, 49, 52, 57]
ROOTS = {id(D): 38, id(Bm): 35, id(G): 31, id(A): 33}
PROG_A = [D, Bm, G, A]          # verse
PROG_B = [G, A, Bm, A]          # lift, used under the breakdown
PROG_C = [Bm, G, D, A]          # middle section variety

def chord_at(t):
    b = int(t // BAR)
    if t >= OUTRO: return D
    if 45 <= t < 52: return PROG_B[b % 4]
    if 25.5 <= t < 39.5: return PROG_C[b % 4]
    return PROG_A[b % 4]

# sections
DRUMS = [(4, 45), (52, OUTRO)]
HATS = [(15.5, 45), (52, OUTRO)]
ARP = [(4, OUTRO)]
BASS = [(4, OUTRO)]

# --- pad, per bar
nbars = int(np.ceil(DUR / BAR))
for b in range(nbars):
    t0 = b * BAR
    if t0 >= OUTRO: break
    g = 0.17 if t0 < 4 else (0.15 if 45 <= t0 < 52 else 0.13)
    fc = 1400 if t0 < 4 else 2400
    add(L, R, lowpass(pad(chord_at(t0 + 0.01), BAR + 0.6), fc), t0, g)

# final sustained D chord for the outro
add(L, R, lowpass(pad([50, 54, 57, 62, 66], DUR - OUTRO + 0.2), 2600), OUTRO, 0.15)

# --- bass + kick
for bt in np.arange(0, DUR, BEAT):
    if within(bt, BASS):
        root = ROOTS[id(chord_at(bt + 0.01))]
        add(L, R, lowpass(pluck(root, 0.9, 0.28, 0.15), 500), bt, 0.16 if not (45 <= bt < 52) else 0.11)
    if within(bt, DRUMS) and int(round(bt / BEAT)) % 2 == 0:
        t = np.arange(int(0.35 * SR)) / SR
        f = 48 + 70 * np.exp(-t / 0.03)
        add(L, R, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12), bt, 0.24)

# --- arp
eighth = BEAT / 2
for i, et in enumerate(np.arange(4, OUTRO, eighth)):
    c = chord_at(et + 0.01)
    m = [c[0] + 12, c[2] + 12, c[1] + 12, c[3] + 12][i % 4]
    g = 0.055 if et < 15.5 else (0.05 if 45 <= et < 52 else 0.07)
    add(L, R, lowpass(pluck(m, 0.8, 0.22, 0.4), 3500), et, g, pan=-0.35 if i % 2 else 0.35)

# --- hats
for et in np.arange(eighth, DUR, BEAT):
    if not within(et, HATS): continue
    n = int(0.06 * SR); h = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / 0.015)
    add(L, R, h - lowpass(h, 6000), et, 0.035, pan=0.2)

# --- sound effects
def swell(t_end, length=0.55, gain=0.05):
    n = int(length * SR); x = rng.standard_normal(n)
    x = lowpass(x, 2200) - lowpass(x, 300)
    e = (np.arange(n) / n) ** 2.2; e[-int(0.04 * SR):] *= np.linspace(1, 0, int(0.04 * SR))
    add(fx_L, fx_R, x * e, t_end - length, gain, pan=-0.2)
    add(fx_L, fx_R, x * e, t_end - length + 0.01, gain * 0.7, pan=0.2)

for c in CUTS: swell(c)

def ticks(t0, t1, gain=0.035, notes=(74, 78, 81)):
    k = 0; t = t0; gap = 0.045
    while t < t1:
        add(fx_L, fx_R, lowpass(pluck(notes[k % len(notes)], 0.25, 0.05, 0.2), 5000), t, gain, pan=0.15 * (-1) ** k)
        k += 1; gap *= 1.16; t += gap

# count-ups: hook, glance, risk, phone, scores, divisions
for a, b in ((0.1, 1.4), (15.95, 17.2), (20.35, 21.3), (25.85, 26.8), (30.35, 31.4), (34.9, 35.9)):
    ticks(a, b)

# hook: soft low impact under the first number
t = np.arange(int(1.6 * SR)) / SR
add(fx_L, fx_R, np.sin(2 * np.pi * hz(38) * t) * np.exp(-t / 0.5) + 0.4 * np.sin(2 * np.pi * hz(50) * t) * np.exp(-t / 0.4), 0.1, 0.22)

# bells: 76% callout, 15x callout, final line
for tb, ms, g in ((22.3, [74, 81], 0.06), (41.9, [74, 81], 0.06), (56.65, [62, 69, 74], 0.07)):
    for j, m in enumerate(ms):
        add(fx_L, fx_R, pluck(m, 2.5, 0.9, 0.1), tb + j * 0.04, g, pan=0.1 * (j - 1))

# soft plucks as each priority / check appears
for tp in (45.5, 46.4, 47.3):
    add(fx_L, fx_R, pluck(69, 1.2, 0.4, 0.15), tp, 0.045)
for k, tp in enumerate((52.4, 52.7, 53.0, 53.3)):
    add(fx_L, fx_R, pluck([74, 78, 81, 86][k], 0.6, 0.15, 0.2), tp, 0.03)

# --- shared space
def reverb(x, tau=1.1, mix=0.18):
    n = int(2.5 * SR); ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / (tau / 3))
    ir = lowpass(ir, 4000); ir /= np.sqrt(np.sum(ir ** 2))
    F = 1 << int(np.ceil(np.log2(len(x) + n)))
    return x + mix * np.fft.irfft(np.fft.rfft(x, F) * np.fft.rfft(ir, F), F)[: len(x)]

ML = reverb(L + 0.8 * fx_L); MR = reverb(R + 0.8 * fx_R)
fo = int(1.6 * SR); ML[-fo:] *= np.linspace(1, 0, fo) ** 1.5; MR[-fo:] *= np.linspace(1, 0, fo) ** 1.5
fi = int(0.02 * SR); ML[:fi] *= np.linspace(0, 1, fi); MR[:fi] *= np.linspace(0, 1, fi)

peak = max(np.abs(ML).max(), np.abs(MR).max())
data = (np.stack([ML, MR], 1) / peak * 0.89 * 32767).astype(np.int16)
with wave.open('music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
print('ok', DUR)
