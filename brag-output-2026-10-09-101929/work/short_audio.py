# Soundtrack for the under-a-minute cut: short-a.wav (purpose & scope + results, 38.5s) and short-outro.wav (3s).
# The feedback clip plays between them with its own voice only.
import numpy as np, wave

SR = 44100
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(5)

def hz(m): return 440 * 2 ** ((m - 69) / 12)

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

def swell_sig(length, gain):
    n = int(length * SR); x = rng.standard_normal(n)
    x = lowpass(x, 2200) - lowpass(x, 300)
    e = (np.arange(n) / n) ** 2.2; e[-int(0.04 * SR):] *= np.linspace(1, 0, int(0.04 * SR))
    return x * e * gain

def reverb(x, tau=1.1, mix=0.18):
    n = int(2.5 * SR); ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / (tau / 3))
    ir = lowpass(ir, 4000); ir /= np.sqrt(np.sum(ir ** 2))
    F = 1 << int(np.ceil(np.log2(len(x) + n)))
    return x + mix * np.fft.irfft(np.fft.rfft(x, F) * np.fft.rfft(ir, F), F)[: len(x)]

class Track:
    def __init__(self, dur):
        self.N = int(SR * dur); self.L = np.zeros(self.N); self.R = np.zeros(self.N)
    def add(self, sig, t0, gain=1.0, pan=0.0):
        i = int(t0 * SR)
        if i >= self.N: return
        sig = sig[: self.N - i] * gain
        self.L[i:i + len(sig)] += sig * np.sqrt((1 - pan) / 2); self.R[i:i + len(sig)] += sig * np.sqrt((1 + pan) / 2)
    def write(self, path, fade_in=0.02, fade_out=0.03, peak_to=0.89):
        L, R = reverb(self.L), reverb(self.R)
        fi, fo = int(fade_in * SR), int(fade_out * SR)
        for x in (L, R):
            x[:fi] *= np.linspace(0, 1, fi); x[-fo:] *= np.linspace(1, 0, fo) ** 1.5
        p = max(np.abs(L).max(), np.abs(R).max())
        data = (np.stack([L, R], 1) / p * peak_to * 32767).astype(np.int16)
        with wave.open(path, 'wb') as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())

D, Bm, G, A = [50, 54, 57, 62], [47, 50, 54, 59], [43, 50, 55, 59], [45, 49, 52, 57]
ROOT = {id(D): 38, id(Bm): 35, id(G): 31, id(A): 33}
HOOK, GROOVE, END = 12.5, 15.5, 38.5

def chord_at(t):
    b = int(t // BAR)
    return ([Bm, G, D, A] if t < HOOK else [D, Bm, G, A])[b % 4]

# ---- part A: purpose & scope (calm) -> hook -> results (groove)
a = Track(END)
for b in range(int(np.ceil(END / BAR))):
    t0 = b * BAR
    a.add(lowpass(pad(chord_at(t0 + 0.01), BAR + 0.6), 1500 if t0 < HOOK else 2400), t0, 0.17 if t0 < HOOK else 0.13)
for i, et in enumerate(np.arange(4.5, END, BEAT / 2)):
    if et < HOOK and i % 2: continue
    c = chord_at(et + 0.01)
    a.add(lowpass(pluck([c[0] + 12, c[2] + 12, c[1] + 12, c[3] + 12][i % 4], 0.8, 0.22, 0.4), 3400), et, 0.045 if et < HOOK else 0.065, pan=-0.35 if i % 2 else 0.35)
for bt in np.arange(GROOVE, END, BEAT):
    a.add(lowpass(pluck(ROOT[id(chord_at(bt + 0.01))], 0.9, 0.28, 0.15), 500), bt, 0.16)
    if int(round((bt - GROOVE) / BEAT)) % 2 == 0:
        t = np.arange(int(0.35 * SR)) / SR; f = 48 + 70 * np.exp(-t / 0.03)
        a.add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12), bt, 0.24)
    n = int(0.06 * SR); h = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / 0.015)
    a.add(h - lowpass(h, 6000), bt + BEAT / 2, 0.033, pan=0.2)
# swells into each cut; the hook gets a longer rise and a low impact
for c in (4.5, 8.5, 15.5, 19, 23.5, 27, 30.5, 34.5):
    a.add(swell_sig(0.5, 0.05), c - 0.5, pan=-0.2)
a.add(swell_sig(1.4, 0.08), HOOK - 1.4)
t = np.arange(int(1.6 * SR)) / SR
a.add(np.sin(2 * np.pi * hz(38) * t) * np.exp(-t / 0.5) + 0.4 * np.sin(2 * np.pi * hz(50) * t) * np.exp(-t / 0.4), HOOK + 0.05, 0.22)
# count-up ticks and callout bells
def ticks(t0, t1):
    k, tt, gap = 0, t0, 0.045
    while tt < t1:
        a.add(lowpass(pluck((74, 78, 81)[k % 3], 0.25, 0.05, 0.2), 5000), tt, 0.035, pan=0.15 * (-1) ** k); k += 1; gap *= 1.16; tt += gap
for t0, t1 in ((12.55, 13.4), (15.85, 16.8), (19.25, 20.0), (23.8, 24.5), (27.25, 28.0)):
    ticks(t0, t1)
for tb in (20.7, 32.1):
    for j, m in enumerate((74, 81)): a.add(pluck(m, 2.5, 0.9, 0.1), tb + j * 0.04, 0.06)
# music falls away under the last scene so the feedback voice enters clean
fade = np.ones(a.N); s0 = int(37.0 * SR); fade[s0:] = np.linspace(1, 0, a.N - s0) ** 1.4
a.L *= fade; a.R *= fade
a.write('short-a.wav', fade_in=0.4)

# ---- outro: resolving D chord with a bell
o = Track(3.0)
o.add(lowpass(pad([50, 54, 57, 62, 66], 3.2), 2600), 0.0, 0.15)
o.add(lowpass(pluck(38, 2.5, 0.8, 0.1), 500), 0.1, 0.18)
for j, m in enumerate((62, 69, 74)): o.add(pluck(m, 2.5, 0.9, 0.1), 0.15 + j * 0.04, 0.07)
o.write('short-outro.wav', fade_in=0.15, fade_out=0.9)
print('ok')
