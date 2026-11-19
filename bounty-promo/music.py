"""Original 150 BPM retro-trap track for the BOUNTY promo (F# minor), synthesized from scratch.

Timeline (1 beat = 0.4 s, 1 bar = 1.6 s) is shared with scene.html:
  0.0-3.2   siren + word hits (PULL IT OFF. / CLIP IT. / GET PAID.), sucked into the drop
  3.2-14.4  drop 1: logo, bounty #001, bounty #002 (siren layer), how it works; arp from 8.0
  14.4-15.6 build: classified bounties, snare roll, riser
  15.6-16.0 silence
  16.0-19.2 drop 2: 1.5 SOL up for grabs, cash hit
  19.2-23.0 outro: final impact + tail
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
LENGTH = 23.0
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


# chord progression F#m - D - A - E (F# minor)
PROG = [
    (54, [57, 61, 66, 69]),   # F#m
    (50, [57, 62, 66, 69]),   # D
    (45, [57, 61, 64, 69]),   # A
    (52, [56, 59, 64, 68]),   # E
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


# ---------------------------------------------------------------- sound effects
def siren(d, rate=0.9, lo=640, hi=980):
    """Police siren wail: a sine swept between two pitches, slightly distorted."""
    t = tt(d)
    f = lo + (hi - lo) * (0.5 - 0.5 * np.cos(2 * np.pi * rate * t))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    s = np.tanh(s * 2.2) * 0.5
    return bp(s, 400, 3500)


def clink(d=0.35):
    t = tt(d)
    out = np.zeros(len(t))
    for f, a, dec in ((2350, 1.0, 22), (3760, 0.7, 26), (5210, 0.5, 30), (7340, 0.35, 38)):
        out += a * np.sin(2 * np.pi * f * t) * np.exp(-t * dec)
    return out * 0.3


def blip(freq, d=0.12):
    t = tt(d)
    return np.sin(2 * np.pi * freq * t) * np.exp(-t * 30) * 0.5


def cash(d=0.9):
    """Register-style cha-ching: a bell chord over a noisy drawer clack."""
    t = tt(d)
    clack = bp(rng.standard_normal(len(t)), 800, 4000) * np.exp(-t * 40)
    bell = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 4) for f in (1568, 2093, 2637)) / 3
    ring = np.zeros(len(t))
    i0 = int(0.08 * SR)
    ring[i0:] = bell[:len(t) - i0]
    return clack * 0.6 + ring * 0.7


# ---------------------------------------------------------------- arrangement
# intro (0 - 3.2): siren rising, hits on 0.8 / 1.6 / 2.4
sv = siren(3.0)
sv *= (np.linspace(0.15, 1, len(sv)) ** 1.5)
place(fx, sv, 0.0, 0.32, pan=0.3)
pad(0.0, 2.8, [PROG[0], PROG[1]], gain=0.14, cutoff=(300, 2400))
place(music, bass808(midi(42), 2.8), 0.0, 0.3)
for bt in (0.8, 1.6, 2.4):
    place(drums, kick(0.35, hard=0.9), bt, 0.85)
    place(drums, impact(0.8), bt, 0.25)
    place(music, stab(PROG[0][1], 0.3), bt, 0.3)
riser(0.8, 2.2, gain=0.5)
snare_roll(1.6, 1.2, [(0.5, 2), (0.8, 4), (1.0, 8)], gain=0.5)
reverse_cymbal(3.2, 1.0, 0.45)

# drop 1: bars 2-8 (3.2 - 14.4), arp joins at bar 5 (8.0)
place(drums, impact(), 3.2, 0.9)
place(drums, crash(), 3.2, 0.6)
for bar in range(2, 9):
    drop_bar(bar, lead=bar >= 5)
    if bar in (3, 5, 7):
        place(drums, crash(1.6), bar * BAR, 0.35)
pad(3.2, 11.2, [PROG[b % 4] for b in range(2, 9)], gain=0.08, cutoff=(800, 4500))

# bounty #001: coin clinks as 1 SOL counts up, a blip per star, fast ticks on the timer
for i in range(6):
    place(fx, clink(), 4.8 + i * 0.06, 0.35, pan=(-0.3, 0.3)[i % 2])
for i in range(6):
    place(fx, blip(1200 + i * 120), 5.2 + i * 0.1, 0.35)
for i in range(25):
    place(fx, blip(2400, 0.03), 6.8 + i * 0.04, 0.2)
# bounty #002: siren layer under the police car, blips as the stars drain
place(fx, siren(3.0, rate=1.6, lo=700, hi=1050), 8.0, 0.16, pan=-0.4)
for i in range(3):
    place(fx, blip(1500, 0.1), 9.6 + i * 0.1, 0.3)
for i in range(3):
    place(fx, blip(900 - i * 150, 0.14), 10.2 + i * 0.2, 0.35)
# how it works: a blip per step
for t0 in (11.2, 12.0, 12.8, 13.6):
    place(fx, blip(1800, 0.08), t0, 0.3)

# build (14.4 - 16.0): hits on the classified bounties, snare roll, riser, silent beat
for bt in (14.4, 14.8, 15.2):
    place(drums, kick(0.3, hard=1.2), bt, 0.9)
    kick_times.append(bt)
    place(music, stab(PROG[3][1], 0.22), bt, 0.32)
snare_roll(14.4, 1.2, [(0.4, 4), (0.75, 8), (1.0, 16)], gain=0.8)
riser(14.0, 1.6, gain=0.9)
pad(14.4, 1.2, [PROG[3]], gain=0.2, cutoff=(500, 7000))
reverse_cymbal(16.0, 0.8, 0.55)

# drop 2: bars 10-11 (16.0 - 19.2)
place(drums, impact(), 16.0, 1.0)
place(drums, crash(), 16.0, 0.7)
place(fx, cash(), 16.0, 0.6)
for i in range(10):
    place(fx, clink(), 16.1 + i * 0.13, 0.2, pan=(-0.5, 0.5)[i % 2])
for bar in range(10, 12):
    drop_bar(bar, lead=True)
pad(16.0, 3.2, [PROG[b % 4] for b in range(10, 12)], gain=0.1, cutoff=(1200, 6000))
place(fx, siren(1.6, rate=1.6, lo=700, hi=1050), 17.6, 0.12, pan=0.4)

# outro: final hit 19.2 + tail
place(drums, impact(3.5), 19.2, 1.0)
place(drums, crash(3.5), 19.2, 0.6)
place(drums, kick(0.6), 19.2, 1.0)
place(music, stab(PROG[0][1], 1.2), 19.2, 0.4)
place(fx, cash(), 20.0, 0.35)
pad(19.2, 3.8, [PROG[0]], gain=0.14, cutoff=(3000, 400))
place(music, bass808(midi(42), 2.8), 19.2, 0.6)

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
