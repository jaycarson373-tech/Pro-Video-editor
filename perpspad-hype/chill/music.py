"""Chill cut soundtrack for the Perps Pad promo: original 96 BPM lo-fi house in D minor.

Timeline (1 bar = 2.5 s, 1 beat = 0.625 s) is shared with chill/scene.html:
  0.0-5.0   pad + keys + vinyl, no drums
  5.0-22.5  soft four-on-the-floor groove, swung hats, sub, keys, pluck
  17.5-22.5 burn section: filter opens, pluck melody
  22.5-25.0 groove continues under the builder shot
  25.0-31.0 drums out, keys ring out
Usage: python3 chill/music.py chill/out/music.wav
"""
import sys
import wave

import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 44100
BPM = 96
BEAT = 60 / BPM          # 0.4 s
BAR = BEAT * 4           # 1.6 s
LENGTH = 31.0
N = int(LENGTH * SR)
rng = np.random.default_rng(7)

drums = np.zeros((N, 2))
music = np.zeros((N, 2))
fx = np.zeros((N, 2))
kick_times = []


def place(buf, sig, t, gain=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= N:
        return
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l * 1.414, sig * r * 1.414], axis=1)
    n = min(len(sig), N - i)
    buf[i:i + n] += sig[:n] * gain


def tt(d):
    return np.arange(int(d * SR)) / SR


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


# ---------------------------------------------------------------- instruments
def kick(d=0.42, hard=1.0):
    t = tt(d)
    f = 46 + 170 * np.exp(-t * 32) * hard
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 6.5)
    click = rng.standard_normal(len(t)) * np.exp(-t * 400) * 0.35
    return np.tanh((body + click) * 1.6)


def clap(d=0.3):
    t = tt(d)
    n = rng.standard_normal(len(t))
    env = np.zeros_like(t)
    for o in (0, 0.009, 0.018):
        m = t >= o
        env[m] += np.exp(-(t[m] - o) * (60 if o < 0.018 else 14))
    return bp(n, 900, 5200) * env * 1.4


def snare(d=0.22):
    t = tt(d)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
    noise = bp(rng.standard_normal(len(t)), 1500, 9000) * np.exp(-t * 22)
    return tone * 0.5 + noise


def hat(d=0.06, open_=False):
    t = tt(0.28 if open_ else d)
    return hp(rng.standard_normal(len(t)), 7500) * np.exp(-t * (9 if open_ else 70)) * 0.5


def crash(d=2.6):
    t = tt(d)
    return hp(rng.standard_normal(len(t)), 4000) * np.exp(-t * 1.6) * 0.5


def impact(d=3.0):
    """Sub boom + noise burst for drops."""
    t = tt(d)
    f = 30 + 90 * np.exp(-t * 6)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.4)
    burst = lp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 5) * 0.6
    return np.tanh((boom + burst) * 1.8)


def saw(freq, d, voices=7, detune=0.18, maxh=None):
    """Band-limited supersaw via additive synthesis."""
    t = tt(d)
    out = np.zeros_like(t)
    for v in range(voices):
        cents = (v - (voices - 1) / 2) / ((voices - 1) / 2) * detune * 100
        f = freq * 2 ** (cents / 1200)
        ph0 = rng.uniform(0, 2 * np.pi)
        kmax = int(min(maxh or 99, (SR / 2.2) / f))
        for k in range(1, kmax + 1):
            out += np.sin(2 * np.pi * k * f * t + ph0 * k) / k
    return out / voices


def stereo_saw(freq, d, **kw):
    return np.stack([saw(freq, d, **kw), saw(freq, d, **kw)], axis=1)


def adsr(n, a=0.005, dcy=0.08, s=0.5, r=0.06):
    t = np.arange(n) / SR
    d = n / SR
    env = np.where(t < a, t / a, s + (1 - s) * np.exp(-(t - a) / max(dcy, 1e-4)))
    rel = np.clip((d - t) / r, 0, 1)
    return env * rel


def bass808(freq, d, glide_from=None):
    t = tt(d)
    f = np.full_like(t, freq)
    if glide_from:
        f = freq + (glide_from - freq) * np.exp(-t * 25)
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.exp(-t * 0.9) * np.clip((d - t) / 0.05, 0, 1)
    return np.tanh(np.sin(ph) * 2.2) * env


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


# chord progression Dm - Bb - F - C (D minor)
PROG = [
    (50, [57, 62, 65, 69]),   # Dm
    (46, [58, 62, 65, 70]),   # Bb
    (41, [57, 60, 65, 69]),   # F
    (48, [55, 60, 64, 67]),   # C
]
STAB_16THS = [0, 3, 6, 10, 12, 14]
ARP = [0, 2, 1, 3, 2, 1, 3, 2]

stab_cache = {}


def stab(notes, d):
    key = (tuple(notes), round(d, 3))
    if key not in stab_cache:
        s = sum(stereo_saw(midi(n), d, voices=5, maxh=40) for n in notes) / len(notes)
        env = adsr(len(s), a=0.003, dcy=0.09, s=0.35, r=0.04)[:, None]
        s = np.stack([lp(s[:, 0], 5200), lp(s[:, 1], 5200)], axis=1)
        stab_cache[key] = s * env
    return stab_cache[key]


def drop_bar(bar, lead=False, kick_on=True):
    t0 = bar * BAR
    root, chord = PROG[bar % 4]
    for b in range(4):
        if kick_on:
            place(drums, kick(), t0 + b * BEAT, 1.0)
            kick_times.append(t0 + b * BEAT)
        place(drums, hat(), t0 + b * BEAT + BEAT / 2, 0.55, pan=0.25)
        place(drums, hat(0.03), t0 + b * BEAT + BEAT * 0.75, 0.25, pan=-0.3)
    place(drums, clap(), t0 + BEAT, 0.8)
    place(drums, clap(), t0 + 3 * BEAT, 0.8)
    place(drums, hat(open_=True), t0 + 3.5 * BEAT, 0.3, pan=0.4)
    # 808: root on 1, octave hop on the "and" of 3
    place(music, bass808(midi(root - 12), BEAT * 2.5, glide_from=midi(root)), t0, 0.75)
    place(music, bass808(midi(root), BEAT * 1.4, glide_from=midi(root - 12)), t0 + BEAT * 2.5, 0.55)
    for s in STAB_16THS:
        place(music, stab(chord, BEAT / 4 * 1.6), t0 + s * BEAT / 4, 0.32)
    if lead:
        for i in range(16):
            n = chord[ARP[i % 8]] + 12
            sig = saw(midi(n), BEAT / 4 * 0.9, voices=3, maxh=25)
            sig = sig * adsr(len(sig), a=0.002, dcy=0.05, s=0.3, r=0.02)
            place(music, sig, t0 + i * BEAT / 4, 0.16, pan=(-0.5 if i % 2 else 0.5))


def pad(start, d, chord_seq, gain=0.18, cutoff=(400, 3000)):
    """Sustained supersaw pad with opening filter."""
    total = np.zeros((int(d * SR), 2))
    seg = d / len(chord_seq)
    for i, (_, chord) in enumerate(chord_seq):
        s = sum(stereo_saw(midi(n), seg + 0.05, voices=7, maxh=30) for n in chord) / len(chord)
        i0 = int(i * seg * SR)
        n = min(len(s), len(total) - i0)
        total[i0:i0 + n] += s[:n]
    # filter sweep by blending a dark and bright version
    dark = np.stack([lp(total[:, c], cutoff[0]) for c in range(2)], axis=1)
    bright = np.stack([lp(total[:, c], cutoff[1]) for c in range(2)], axis=1)
    mix = np.linspace(0, 1, len(total))[:, None] ** 1.5
    out = dark * (1 - mix) + bright * mix
    fade = np.minimum(1, np.arange(len(out)) / (0.3 * SR))[:, None]
    place(music, out * fade, start, gain)


def riser(start, d, gain=0.5, f0=300, f1=9000):
    t = tt(d)
    n = rng.standard_normal((len(t), 2))
    # chunked bandpass with rising center
    out = np.zeros_like(n)
    chunks = 40
    L = len(t) // chunks
    for c in range(chunks):
        sl = slice(c * L, (c + 1) * L if c < chunks - 1 else len(t))
        fc = f0 * (f1 / f0) ** (c / chunks)
        for ch in range(2):
            out[sl, ch] = bp(n[sl, ch], fc * 0.7, min(fc * 1.4, SR / 2.1))
    env = (t / d) ** 2
    # pitched sweep tone
    f = 200 * (8 ** (t / d))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * env * 0.25
    place(fx, out * env[:, None] + tone[:, None], start, gain)


def snare_roll(start, d, rates, gain=0.5):
    """rates: list of (fraction_of_duration, hits_per_beat)."""
    t = start
    end = start + d
    while t < end - 1e-6:
        prog = (t - start) / d
        rate = rates[-1][1]
        for frac, r in rates:
            if prog < frac:
                rate = r
                break
        place(drums, snare(), t, gain * (0.4 + 0.6 * prog))
        t += BEAT / rate


def reverse_cymbal(end, d=1.2, gain=0.5):
    c = crash(d)[::-1]
    place(fx, c, end - d, gain)



# ---------------------------------------------------------------- chill instruments
def keys(freq, d, bright=1.0):
    """Electric-piano-ish FM voice."""
    t = tt(d)
    idx = 1.6 * bright * np.exp(-t * 3.5)
    mod = np.sin(2 * np.pi * freq * t) * idx
    car = np.sin(2 * np.pi * freq * t + mod)
    bell = np.sin(2 * np.pi * freq * 4 * t) * 0.08 * np.exp(-t * 9)
    env = np.minimum(1, t / 0.004) * np.exp(-t * 1.1) * np.clip((d - t) / 0.08, 0, 1)
    trem = 1 + 0.12 * np.sin(2 * np.pi * 4.5 * t)
    sig = (car + bell) * env
    return np.stack([sig * trem, sig * (2 - trem)], axis=1) * 0.5


def chord(notes, d, gain=1.0, strum=0.012, bright=1.0):
    out = np.zeros((int((d + strum * len(notes)) * SR), 2))
    for i, n in enumerate(notes):
        k = keys(midi(n), d, bright)
        i0 = int(i * strum * SR)
        out[i0:i0 + len(k)] += k
    return out * gain / np.sqrt(len(notes))


def soft_kick():
    t = tt(0.5)
    f = 48 + 70 * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    return np.tanh(body * 1.3)


def snap():
    t = tt(0.2)
    n = bp(rng.standard_normal(len(t)), 1200, 6000) * np.exp(-t * 38)
    return n * 0.9


def sub(freq, d):
    t = tt(d)
    env = np.minimum(1, t / 0.02) * np.clip((d - t) / 0.1, 0, 1) * (0.7 + 0.3 * np.exp(-t * 3))
    return np.sin(2 * np.pi * freq * t) * env


def pluck(freq, d=0.5):
    t = tt(d)
    s = saw(freq, d, voices=2, detune=0.08, maxh=12)
    s = lp(s, 2800) * np.exp(-t * 7) * np.minimum(1, t / 0.003)
    return s


def vinyl(d):
    n = rng.standard_normal(int(d * SR)) * 0.02
    n = lp(n, 3500)
    pops = np.zeros_like(n)
    for _ in range(int(d * 7)):
        i = rng.integers(0, len(n) - 200)
        pops[i:i + 60] += rng.standard_normal(60) * np.exp(-np.arange(60) / 10) * rng.uniform(0.05, 0.25)
    return n + hp(pops, 1500)


# Dm9 - Bbmaj7 - Fmaj7 - C6/9 voicings + roots
CPROG = [
    (38, [53, 57, 60, 64, 69]),   # Dm9  (F A C E A)
    (34, [53, 57, 58, 62, 65]),   # Bbmaj7 (F A Bb D F)
    (41, [52, 57, 60, 64, 69]),   # Fmaj7 (E A C E A)
    (36, [52, 55, 57, 62, 64]),   # C6/9 (E G A D E)
]
MELODY = [  # (16th offset within 2-bar phrase, midi)
    (0, 76), (3, 74), (6, 72), (8, 69), (12, 72), (14, 74),
    (16, 77), (19, 76), (22, 74), (24, 72), (28, 69),
]


def groove_bar(bar, hats=True, melody=False, filt=1.0):
    t0 = bar * BAR
    root, ch = CPROG[bar % 4]
    for b in range(4):
        place(drums, soft_kick(), t0 + b * BEAT, 0.9)
        kick_times.append(t0 + b * BEAT)
        if hats:
            for s16 in (1, 2, 3):
                sw = 0.08 * BEAT if s16 == 2 else 0
                place(drums, hat(0.04), t0 + b * BEAT + s16 * BEAT / 4 + sw, (0.22 if s16 == 2 else 0.1), pan=0.3 if s16 == 2 else -0.25)
    place(drums, snap(), t0 + BEAT, 0.55)
    place(drums, snap(), t0 + 3 * BEAT, 0.55)
    place(drums, hat(open_=True), t0 + 3.5 * BEAT, 0.16, pan=0.4)
    place(music, sub(midi(root), BEAT * 2.9), t0, 0.55)
    place(music, sub(midi(root), BEAT * 0.9), t0 + BEAT * 3, 0.4)
    place(music, chord(ch, BAR * 0.95, bright=filt), t0, 0.5)
    place(music, chord(ch[2:], BEAT * 0.8, bright=filt), t0 + BEAT * 2.5, 0.28)
    if melody:
        half = bar % 2
        for off, n in MELODY:
            if (off >= 16) == bool(half):
                place(music, pluck(midi(n)), t0 + (off % 16) * BEAT / 4, 0.22, pan=0.15)


# ---------------------------------------------------------------- arrangement
place(fx, vinyl(LENGTH), 0.0, 1.0)
# intro: keys + pad, no drums
place(music, chord(CPROG[0][1], 2.4), 0.0, 0.5)
place(music, chord(CPROG[1][1], 2.4), BAR, 0.5)
pad(0.0, 5.0, [CPROG[0], CPROG[1]], gain=0.07, cutoff=(250, 1800))
place(music, sub(midi(38), 2.4), 0.0, 0.3)
place(music, sub(midi(34), 2.4), BAR, 0.3)
riser(3.0, 2.0, gain=0.12, f0=400, f1=5000)
reverse_cymbal(5.0, 1.2, 0.25)

# groove: bars 2-9 (5.0 - 25.0); melody in burn section bars 7-8
for bar in range(2, 10):
    groove_bar(bar, hats=bar >= 2, melody=bar in (7, 8, 9), filt=1.4 if bar in (7, 8) else 1.0)
pad(5.0, 20.0, [CPROG[b % 4] for b in range(2, 10)], gain=0.05, cutoff=(600, 2600))
place(drums, crash(2.0), 5.0, 0.25)
place(drums, crash(2.0), 17.5, 0.3)
riser(15.5, 2.0, gain=0.15, f0=500, f1=6000)

# outro: keys ring out, sub, soft hit
place(drums, crash(3.0), 25.0, 0.25)
place(drums, soft_kick(), 25.0, 0.9)
place(music, chord(CPROG[0][1], 4.5), 25.0, 0.6)
place(music, sub(midi(38), 3.5), 25.0, 0.45)
pad(25.0, 6.0, [CPROG[0]], gain=0.08, cutoff=(1800, 300))
place(music, pluck(midi(81), 1.2), 25.0 + BEAT * 2, 0.15)
place(music, pluck(midi(76), 1.2), 25.0 + BEAT * 3, 0.12)

# ---------------------------------------------------------------- mix
duck = np.ones(N)
for kt in kick_times:
    i = int(kt * SR)
    n = min(int(0.35 * SR), N - i)
    curve = 1 - 0.35 * np.exp(-np.arange(n) / SR * 10)
    duck[i:i + n] = np.minimum(duck[i:i + n], curve)
music *= duck[:, None]

ir_t = tt(3.0)
ir = np.stack([rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 1.8) for _ in range(2)], axis=1)
ir[:, 0] = lp(ir[:, 0], 4500)
ir[:, 1] = lp(ir[:, 1], 4500)
send = music * 0.5 + drums * 0.12
wet = np.stack([fftconvolve(send[:, c], ir[:, c])[:N] for c in range(2)], axis=1)
wet /= np.max(np.abs(wet)) + 1e-9

mix = drums * 0.5 + music * 0.9 + fx * 0.6 + wet * 0.3
mix = hp(mix.T, 25).T
mix = np.stack([lp(mix[:, c], 12000) for c in range(2)], axis=1)  # warm top end
mix /= np.max(np.abs(mix)) + 1e-9
DRIVE = 1.4
mix = np.tanh(mix * DRIVE) / np.tanh(DRIVE)
fade_in = np.clip(np.arange(N) / SR / 0.8, 0, 1)
fade_out = np.clip((LENGTH - np.arange(N) / SR) / 2.5, 0, 1)
mix *= (fade_in * fade_out)[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.6  # chill: leave headroom (~-13 LUFS)

out = sys.argv[1] if len(sys.argv) > 1 else "chill/out/music.wav"
pcm = (mix * 32767).astype(np.int16)
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("wrote", out, f"{LENGTH}s")
