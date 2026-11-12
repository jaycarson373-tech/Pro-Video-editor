"""Original soundtrack for the GPU Pad promo: clean 100 BPM electronic bed, synthesized from scratch.

Timeline (1 beat = 0.6 s, 1 bar = 2.4 s) is shared with scene.html:
  bar 0  0.0-2.4    pad swell, bell when the logo powers on (0.6 s)
  bar 1  2.4-4.8    headline: arp + soft kick enter
  bar 2-3 4.8-9.6   workspace: full groove (kick, rim, hats, sub)
  bar 4  9.6-12.0   fee split
  bar 5-6 12.0-18.0 outro: bell chord, drums drop out, ring out
Usage: python3 music.py out/music.wav
"""
import sys
import wave

import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 44100
BEAT = 0.6
BAR = BEAT * 4
LENGTH = 18.0
N = int(LENGTH * SR)
rng = np.random.default_rng(11)

drums = np.zeros((N, 2))
music = np.zeros((N, 2))
arp = np.zeros((N, 2))
kick_times = []


def place(buf, sig, t, gain=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= N or i < 0:
        return
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l * 1.414, sig * r * 1.414], axis=1)
    n = min(len(sig), N - i)
    buf[i:i + n] += sig[:n] * gain


def tt(d):
    return np.arange(int(d * SR)) / SR


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x, axis=0)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x, axis=0)


def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x, axis=0)


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---------------------------------------------------------------- instruments
def pluck(freq, d=0.7, bright=1.0):
    """Glassy FM pluck."""
    t = tt(d)
    idx = 2.2 * bright * np.exp(-t * 14)
    sig = np.sin(2 * np.pi * freq * t + idx * np.sin(2 * np.pi * freq * 2 * t))
    return sig * np.minimum(1, t / 0.003) * np.exp(-t * 6.5)


def bell(freq, d=3.5):
    t = tt(d)
    idx = 1.4 * np.exp(-t * 2.5)
    sig = np.sin(2 * np.pi * freq * t + idx * np.sin(2 * np.pi * freq * 3.5 * t))
    sig += 0.3 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t * 3)
    return sig * np.minimum(1, t / 0.004) * np.exp(-t * 1.5) * np.clip((d - t) / 0.3, 0, 1)


def pad(notes, d, cutoff=(500, 1600), attack=0.8, release=1.0):
    t = tt(d)
    out = np.zeros((len(t), 2))
    for n in notes:
        f = midi(n)
        for ch in range(2):
            for det in (-7, 0, 6):
                ff = f * 2 ** ((det + ch * 3) / 1200)
                ph = rng.uniform(0, 2 * np.pi)
                kmax = int(min(14, (SR / 2.2) / ff))
                for k in range(1, kmax + 1):
                    out[:, ch] += np.sin(2 * np.pi * k * ff * t + ph * k) / k
    out /= len(notes) * 3
    dark, bright = lp(out, cutoff[0]), lp(out, cutoff[1])
    mix = (0.5 - 0.5 * np.cos(np.pi * np.clip(t / d, 0, 1)))[:, None]
    out = dark * (1 - mix) + bright * mix
    env = np.clip(t / attack, 0, 1) * np.clip((d - t) / release, 0, 1)
    return out * env[:, None]


def sub(freq, d):
    t = tt(d)
    env = np.minimum(1, t / 0.015) * np.clip((d - t) / 0.12, 0, 1) * (0.75 + 0.25 * np.exp(-t * 3))
    return np.tanh(np.sin(2 * np.pi * freq * t) * 1.4) * env


def kick():
    t = tt(0.45)
    f = 46 + 80 * np.exp(-t * 30)
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5) * 1.3)


def rim():
    t = tt(0.12)
    tone = np.sin(2 * np.pi * 1750 * t) * np.exp(-t * 70)
    click = bp(rng.standard_normal(len(t)), 2000, 7000) * np.exp(-t * 90)
    return tone * 0.6 + click * 0.8


def hat(d=0.05):
    t = tt(d)
    return hp(rng.standard_normal(len(t)), 8000) * np.exp(-t * 80) * 0.5


def swell(d, f0=600, f1=5000):
    t = tt(d)
    n = rng.standard_normal((len(t), 2))
    lo, hi = lp(n, f0), lp(n, f1)
    m = (t / d)[:, None] ** 2
    return hp(lo * (1 - m) + hi * m, 300) * ((t / d) ** 2.5 * np.clip((d - t) / 0.05, 0, 1))[:, None]


# ---------------------------------------------------------------- harmony (F minor -> Ab major)
CH = {
    "Fm9": (41, [56, 60, 63, 67]),
    "Dbmaj7": (37, [56, 60, 61, 65]),
    "Abmaj7": (44, [55, 60, 63, 67]),
    "Eb": (39, [55, 58, 63, 65]),
}
BARS = ["Fm9", "Dbmaj7", "Abmaj7", "Eb", "Fm9", "Dbmaj7", "Abmaj7"]
ARP = [0, 1, 2, 3, 2, 1, 2, 3]

# pads
for b, name in enumerate(BARS[:6]):
    root, notes = CH[name]
    place(music, pad(notes, BAR + 0.9, cutoff=(450, 1300 + 250 * min(b, 4))), b * BAR - (0.0 if b == 0 else 0.25), 0.34)
root, notes = CH["Abmaj7"]
place(music, pad(notes, 3.9, cutoff=(1700, 500), attack=0.5, release=2.6), 6 * BAR - 0.25, 0.36)

# logo power-on (beat 2 of bar 0) and pickup into the headline
place(music, bell(midi(72), 3.0), 0.6, 0.28, pan=-0.15)
place(music, bell(midi(79), 3.0), 0.6, 0.16, pan=0.2)
place(music, sub(midi(41), 1.6), 0.6, 0.4)
for i, n in enumerate([63, 67, 72]):
    place(arp, pluck(midi(n + 12)), 1.5 + i * 0.3, 0.2 + 0.05 * i, pan=(-0.3, 0.3, 0)[i])
place(music, swell(1.2), 1.2, 0.05)

# arp: bars 1-5
for b in range(1, 6):
    root, notes = CH[BARS[b]]
    level = 0.3 if b < 5 else 0.2
    for i in range(8):
        n = notes[ARP[i]] + 12
        accent = 1.25 if i in (0, 3, 6) else 1.0
        place(arp, pluck(midi(n), bright=1.0 if b < 5 else 0.7), b * BAR + i * BEAT / 2, level * accent, pan=-0.35 if i % 2 else 0.35)

# bass
for b in range(1, 5):
    root, _ = CH[BARS[b]]
    place(music, sub(midi(root), BEAT * 1.9), b * BAR, 0.5)
    place(music, sub(midi(root), BEAT * 1.4), b * BAR + BEAT * 2.5, 0.42)
place(music, sub(midi(37), BAR * 0.95), 5 * BAR, 0.5)
place(music, sub(midi(32), 3.0), 6 * BAR, 0.5)

# drums: soft kick from bar 1, rim + hats from bar 2, out at bar 5
for b in range(1, 5):
    for beat in (0, 2):
        place(drums, kick(), b * BAR + beat * BEAT, 0.9)
        kick_times.append(b * BAR + beat * BEAT)
    if b >= 2:
        place(drums, kick(), b * BAR + 3.5 * BEAT, 0.55)
        kick_times.append(b * BAR + 3.5 * BEAT)
        for beat in (1, 3):
            place(drums, rim(), b * BAR + beat * BEAT, 0.5, pan=0.1)
        for i in range(8):
            place(drums, hat(), b * BAR + i * BEAT / 2 + BEAT / 4, 0.16 if i % 2 else 0.1, pan=-0.3 if i % 2 else 0.3)
place(music, swell(1.2), 4 * BAR - 1.2, 0.045)
place(music, swell(1.6), 5 * BAR - 1.6, 0.07)

# outro: bell chord on bar 5, resolution on bar 6
place(drums, kick(), 5 * BAR, 0.9)
kick_times.append(5 * BAR)
for n, g, p in ((68, 0.2, -0.3), (72, 0.24, 0.0), (77, 0.16, 0.3)):
    place(music, bell(midi(n), 4.0), 5 * BAR, g, pan=p)
for n, g, p in ((67, 0.18, 0.3), (72, 0.2, -0.2), (75, 0.18, 0.1), (84, 0.08, 0.0)):
    place(music, bell(midi(n), 3.6), 6 * BAR, g, pan=p)
for i, n in enumerate([75, 72, 79]):
    place(arp, pluck(midi(n + 12), d=1.0, bright=0.7), 6 * BAR + 0.6 + i * 0.6, 0.14, pan=(0.3, -0.3, 0)[i])

# ---------------------------------------------------------------- mix
duck = np.ones(N)
for kt in kick_times:
    i = int(kt * SR)
    n = min(int(0.3 * SR), N - i)
    duck[i:i + n] = np.minimum(duck[i:i + n], 1 - 0.3 * np.exp(-np.arange(n) / SR * 11))
music *= duck[:, None]

# ping-pong dotted-eighth delay on the arp
dly = np.zeros_like(arp)
for k in range(1, 6):
    off = int(k * 0.45 * SR)
    g = 0.42 ** k
    src = arp[:N - off]
    if k % 2:
        dly[off:, 0] += src[:, 1] * g
        dly[off:, 1] += src[:, 0] * g * 0.5
    else:
        dly[off:, 1] += src[:, 0] * g
        dly[off:, 0] += src[:, 1] * g * 0.5
arp_bus = arp + lp(dly, 3500)

ir_t = tt(2.8)
ir = np.stack([rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 2.0) for _ in range(2)], axis=1)
ir = lp(ir, 5000)
send = music * 0.4 + arp_bus * 0.5 + drums * 0.08
wet = np.stack([fftconvolve(send[:, c], ir[:, c])[:N] for c in range(2)], axis=1)
wet /= np.max(np.abs(wet)) + 1e-9

mix = drums * 0.55 + music * 0.9 + arp_bus * 0.8 + wet * 0.3
mix = hp(mix, 28)
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(mix * 1.3) / np.tanh(1.3)
t_all = np.arange(N) / SR
mix *= (np.clip(t_all / 0.3, 0, 1) * np.clip((LENGTH - t_all) / 2.2, 0, 1))[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.62  # clean, not loud: about -14 LUFS

out = sys.argv[1] if len(sys.argv) > 1 else "out/music.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("wrote", out, f"{LENGTH}s")
