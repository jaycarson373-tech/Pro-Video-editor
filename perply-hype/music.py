"""Original 150 BPM hype track for the Perply promo, synthesized from scratch.

Timeline (1 bar = 1.6 s, 1 beat = 0.4 s) is shared with scene.html:
  bars  0-2   intro hits + riser, silent beat before the drop
  bars  2-10  drop 1 (four-on-the-floor, 808, supersaw stabs)
  bars 10-12  drop 1 continues, terminal section
  bars 12-14  build: snare roll, riser, kick out
  bar  14     silence beat before drop 2 (21.6-22.4 handled as build tail)
  bars 14-18  drop 2 (adds lead arp)
  bars 18-20  outro: final impact + tail
Usage: python3 music.py out/music.wav
"""
import sys
import wave

import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 44100
BPM = 150
BEAT = 60 / BPM          # 0.4 s
BAR = BEAT * 4           # 1.6 s
LENGTH = 33.5
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


# chord progression Am - F - C - G (A minor)
PROG = [
    (45, [57, 60, 64, 69]),   # Am
    (41, [53, 57, 60, 65]),   # F
    (48, [55, 60, 64, 67]),   # C
    (43, [55, 59, 62, 67]),   # G
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


# ---------------------------------------------------------------- arrangement
# intro (0 - 3.2): pad swell + word hits on beats 2,4,5,5.5,6
pad(0.0, 2.8, [PROG[0], PROG[1]], gain=0.16, cutoff=(300, 2400))
place(music, bass808(midi(33), 2.8), 0.0, 0.35)
for bt in (2, 4, 5, 5.5, 6):
    place(drums, kick(0.35, hard=0.8), bt * BEAT, 0.8)
    place(music, stab(PROG[0][1], 0.25), bt * BEAT, 0.28)
place(drums, impact(1.6), 0.0, 0.35)
riser(0.4, 2.4, gain=0.45)
snare_roll(1.6, 1.2, [(0.5, 2), (0.8, 4), (1.0, 8)], gain=0.45)
reverse_cymbal(3.2, 1.0, 0.45)

# drop 1: bars 2-12 (3.2 - 19.2)
place(drums, impact(), 3.2, 0.9)
place(drums, crash(), 3.2, 0.6)
for bar in range(2, 12):
    drop_bar(bar)
    if bar in (6, 10):
        place(drums, crash(1.8), bar * BAR, 0.4)
pad(3.2, 16.0, [PROG[b % 4] for b in range(2, 12)], gain=0.09, cutoff=(800, 4000))

# button press accent at 14.4 + section accents
place(fx, impact(1.2), 14.4, 0.35)

# build (19.2 - 22.0): kick out, snare roll accelerating, riser, word hits
for b in range(4):  # driving kicks + claps under the first half of the build
    place(drums, kick(), 19.2 + b * BEAT, 0.85)
    kick_times.append(19.2 + b * BEAT)
    place(drums, hat(), 19.2 + b * BEAT + BEAT / 2, 0.5, pan=0.25)
    place(music, bass808(midi(36), BEAT * 0.9), 19.2 + b * BEAT, 0.5)
snare_roll(19.2, 2.4, [(0.33, 2), (0.66, 4), (0.9, 8), (1.0, 16)], gain=0.8)
riser(19.2, 2.8, gain=0.9)
pad(19.2, 2.8, [PROG[2], PROG[3]], gain=0.22, cutoff=(500, 6000))
for bt in (20.8, 21.2, 21.6):
    place(drums, kick(0.3, hard=1.2), bt, 0.9)
    place(music, stab(PROG[3][1], 0.3), bt, 0.32)
reverse_cymbal(22.4, 1.0, 0.5)

# drop 2: bars 14-18 (22.4 - 28.8)
place(drums, impact(), 22.4, 1.0)
place(drums, crash(), 22.4, 0.7)
for bar in range(14, 18):
    drop_bar(bar, lead=True)
pad(22.4, 6.4, [PROG[b % 4] for b in range(14, 18)], gain=0.1, cutoff=(1200, 6000))

# outro: final hit 28.8 + tail
place(drums, impact(4.0), 28.8, 1.0)
place(drums, crash(4.0), 28.8, 0.6)
place(drums, kick(0.6), 28.8, 1.0)
place(music, stab(PROG[0][1], 1.2), 28.8, 0.4)
pad(28.8, 4.4, [PROG[0]], gain=0.14, cutoff=(3000, 400))
place(music, bass808(midi(33), 3.0), 28.8, 0.6)

# ---------------------------------------------------------------- mix
# sidechain the music bus to kicks
duck = np.ones(N)
for kt in kick_times:
    i = int(kt * SR)
    L = int(0.3 * SR)
    n = min(L, N - i)
    curve = 1 - 0.65 * np.exp(-np.arange(n) / SR * 14)
    duck[i:i + n] = np.minimum(duck[i:i + n], curve)
music *= duck[:, None]

# reverb send
ir_t = tt(2.2)
ir = np.stack([rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 2.6) for _ in range(2)], axis=1)
ir[:, 0] = lp(ir[:, 0], 6000)
ir[:, 1] = lp(ir[:, 1], 6000)
send = music * 0.35 + fx * 0.3 + drums * 0.06
wet = np.stack([fftconvolve(send[:, c], ir[:, c])[:N] for c in range(2)], axis=1)
wet /= np.max(np.abs(wet)) + 1e-9

mix = drums * 0.45 + music * 0.8 + fx * 0.55 + wet * 0.2
mix = hp(mix.T, 25).T
# master: normalize, then gentle soft clip on peaks only
mix /= np.max(np.abs(mix)) + 1e-9
DRIVE = 1.8
mix = np.tanh(mix * DRIVE) / np.tanh(DRIVE)
fade_out = np.clip((LENGTH - np.arange(N) / SR) / 1.5, 0, 1)
mix *= fade_out[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.93

out = sys.argv[1] if len(sys.argv) > 1 else "out/music.wav"
pcm = (mix * 32767).astype(np.int16)
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("wrote", out, f"{LENGTH}s")
