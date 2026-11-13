"""Original soundtrack and sound effects for the Optima promo, synthesized from scratch.

120 BPM (1 beat = 0.5 s, 1 bar = 2 s), G minor. A bass hit lands on every cut. Timeline shared with scene.html:
  0-4    the hook: payment dings stack up, riser, red hit at 3.0
  4-8    shatter at 4.0, whoosh, the ring lands at 5.0, beat starts on "OPTIMA" at 6.0
  8-14   full groove; receipt printer 11.0-12.4, counter ticks 12.0-12.45
  14-18  breakdown as the prompt goes in, two "nope" blips, a success ding at 16.3
  18-24  full groove; a coin clink every second as a coin passes the ring
  24-30  final hit, last dings, everything rings out; the last two seconds are quiet
Usage: python3 music.py out/music.wav
"""
import sys
import wave

import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 44100
BEAT = 0.5
BAR = 2.0
LENGTH = 30.0
N = int(LENGTH * SR)
rng = np.random.default_rng(21)

drums = np.zeros((N, 2))
music = np.zeros((N, 2))
sfx = np.zeros((N, 2))
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


# ---------------------------------------------------------------- drums and bass
def kick(d=0.4, punch=1.0):
    t = tt(d)
    f = 44 + 120 * np.exp(-t * 34) * punch
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8)
    click = rng.standard_normal(len(t)) * np.exp(-t * 500) * 0.25
    return np.tanh((body + click) * 1.5)


def boom(d=1.4):
    """Bass hit for cuts: a sub drop with a short thump on top."""
    t = tt(d)
    f = 36 + 70 * np.exp(-t * 9)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    th = lp(rng.standard_normal(len(t)), 900) * np.exp(-t * 30) * 0.5
    return np.tanh((s + th) * 1.6)


def clap(d=0.22):
    t = tt(d)
    n = bp(rng.standard_normal(len(t)), 1100, 5200)
    env = sum(np.where(t >= o, np.exp(-(t - o) * (70 if o < 0.02 else 20)), 0) for o in (0, 0.01, 0.021))
    return n * env * 0.9


def hat(d=0.05, open_=False):
    t = tt(0.2 if open_ else d)
    return hp(rng.standard_normal(len(t)), 8200) * np.exp(-t * (14 if open_ else 85)) * 0.5


def bass(freq, d):
    t = tt(d)
    s = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t * 6)
    env = np.minimum(1, t / 0.006) * np.exp(-t * 3.5) * np.clip((d - t) / 0.03, 0, 1)
    return np.tanh(s * 1.5) * env


def stab(notes, d=0.22):
    t = tt(d)
    out = np.zeros((len(t), 2))
    for n in notes:
        f = midi(n)
        for ch in range(2):
            ff = f * 2 ** ((ch * 8 - 4) / 1200)
            kmax = int(min(18, (SR / 2.2) / ff))
            for k in range(1, kmax + 1):
                out[:, ch] += np.sin(2 * np.pi * k * ff * t + k * 0.7) / k
    out = lp(out / len(notes), 2600)
    return out * (np.minimum(1, t / 0.003) * np.exp(-t * 16))[:, None]


# ---------------------------------------------------------------- sound effects
def ding(freq=1318.5, d=0.9, bright=1.0):
    """Card-payment style ding: a clean two-partial bell."""
    t = tt(d)
    s = np.sin(2 * np.pi * freq * t) + 0.5 * bright * np.sin(2 * np.pi * freq * 2.005 * t) * np.exp(-t * 7)
    s += 0.25 * bright * np.sin(2 * np.pi * freq * 3.01 * t) * np.exp(-t * 14)
    return s * np.minimum(1, t / 0.002) * np.exp(-t * 6.5) * np.clip((d - t) / 0.05, 0, 1) * 0.6


def whoosh(d, f0=400, f1=4000, peak=0.6):
    t = tt(d)
    n = rng.standard_normal((len(t), 2))
    m = (t / d)[:, None]
    s = lp(n, f0) * (1 - m) + bp(n, f1 * 0.5, f1) * m * 1.6
    env = np.sin(np.pi * np.clip(t / d, 0, 1) ** (np.log(0.5) / np.log(peak))) ** 2
    return hp(s, 180) * env[:, None]


def shatter(d=1.1):
    t = tt(d)
    out = hp(rng.standard_normal((len(t), 2)), 2500) * (np.exp(-t * 16) * 1.2)[:, None]
    for _ in range(26):
        f = rng.uniform(2200, 9500)
        o = rng.uniform(0, 0.28)
        m = t >= o
        ping = np.zeros(len(t))
        ping[m] = np.sin(2 * np.pi * f * (t[m] - o)) * np.exp(-(t[m] - o) * rng.uniform(14, 40))
        pan = rng.uniform(-0.8, 0.8)
        out[:, 0] += ping * (1 - pan) * 0.11
        out[:, 1] += ping * (1 + pan) * 0.11
    return out


def printer(d=1.4, steps=12):
    """Receipt printer: a motor buzz with one burst of head chatter per paper step."""
    t = tt(d)
    motor = lp(np.sign(np.sin(2 * np.pi * 118 * t)), 700) * 0.12
    out = np.zeros(len(t))
    step = d / steps
    for i in range(steps):
        i0 = int(i * step * SR)
        L = int(step * 0.62 * SR)
        tb = np.arange(L) / SR
        chatter = bp(rng.standard_normal(L), 1800, 6500) * (0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 190 * tb)))
        out[i0:i0 + L] += chatter * np.minimum(1, tb / 0.004) * np.clip((L / SR - tb) / 0.01, 0, 1)
        out[i0:i0 + L] += motor[i0:i0 + L] * 3
    return out * 0.5


def clink(d=0.4):
    """Coin clink: inharmonic metal partials, struck twice in quick succession."""
    t = tt(d)
    out = np.zeros(len(t))
    for o, g in ((0, 1.0), (0.055, 0.6)):
        m = t >= o
        for f, a, dec in ((2350, 1.0, 22), (3760, 0.7, 26), (5210, 0.5, 30), (7340, 0.35, 38), (9120, 0.2, 45)):
            out[m] += g * a * np.sin(2 * np.pi * f * (1 + 0.012 * o * 10) * (t[m] - o)) * np.exp(-(t[m] - o) * dec)
    return out * 0.3


def blip(freq, d=0.16):
    t = tt(d)
    f = freq * (1 - 0.25 * t / d)
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * 2) * np.exp(-t * 16) * 0.5


def tick(d=0.03):
    t = tt(d)
    return np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 160) * 0.5


def riser(d, f0=250, f1=7000):
    t = tt(d)
    n = rng.standard_normal((len(t), 2))
    out = np.zeros_like(n)
    chunks = 30
    L = len(t) // chunks
    for c in range(chunks):
        sl = slice(c * L, (c + 1) * L if c < chunks - 1 else len(t))
        fc = f0 * (f1 / f0) ** (c / chunks)
        out[sl] = bp(n[sl], fc * 0.7, min(fc * 1.4, SR / 2.1))
    tone = np.sin(2 * np.pi * np.cumsum(120 * (5 ** (t / d))) / SR) * 0.3
    return (out + tone[:, None]) * ((t / d) ** 2.2)[:, None]


# ---------------------------------------------------------------- 0-4 the hook
NOTES = [0.5, 1.0, 1.5, 2.0, 2.25, 2.5, 2.75, 3.0, 3.083, 3.167, 3.25, 3.333, 3.417, 3.5, 3.583, 3.667, 3.75]
for i, t0 in enumerate(NOTES):
    f = midi(88 + min(i, 8))  # each ding a semitone higher: the charges pile up
    place(sfx, ding(f, 0.9 if i < 8 else 0.4, bright=1.0), t0, 0.75 if i < 8 else 0.4, pan=(-0.25, 0.25)[i % 2])
drone = lp(np.stack([np.sin(2 * np.pi * 49 * tt(4.0)), np.sin(2 * np.pi * 49.4 * tt(4.0))], axis=1), 200)
place(music, drone * np.clip(tt(4.0) / 1.0, 0, 1)[:, None], 0.0, 0.35)
place(sfx, riser(2.0), 2.0, 0.22)
place(drums, boom(1.2), 3.0, 0.9)                              # the screen turns red
place(music, stab([43, 44, 55], 0.7), 3.0, 0.5)               # a sour cluster under "You're overpaying"

# ---------------------------------------------------------------- 4-8 the switch
place(sfx, shatter(), 4.0, 0.8)
place(drums, boom(1.0), 4.0, 0.9)
place(sfx, whoosh(0.8, 500, 5000, peak=0.85), 4.22, 0.5)
place(drums, boom(1.6), 5.0, 1.0)                              # the ring lands: heavy stop
place(drums, kick(0.5, 1.3), 5.0, 1.0)
place(sfx, ding(midi(79), 1.4, bright=0.6), 5.02, 0.22)        # a low metallic ring-out from the ring itself

# ---------------------------------------------------------------- groove
ROOTS = [31, 31, 27, 29]                                       # G, G, Eb, F
CHORDS = [[58, 62, 65], [58, 62, 65], [58, 63, 67], [57, 60, 65]]
BASS_PAT = [(0, 0), (1.5, 0), (2.5, 12), (3.0, 0), (3.5, 7)]   # (beat, semitone offset)


def bar(b, kick_on=True, hats=True, claps=True, bass_on=True, stabs=True, level=1.0):
    t0 = b * BAR
    root = ROOTS[b % 4]
    for beat in range(4):
        if kick_on:
            place(drums, kick(), t0 + beat * BEAT, 0.95 * level)
            kick_times.append(t0 + beat * BEAT)
        if hats:
            place(drums, hat(), t0 + beat * BEAT + BEAT / 2, 0.42 * level, pan=0.2)
            place(drums, hat(0.03), t0 + beat * BEAT + BEAT * 0.75, 0.16 * level, pan=-0.25)
    if claps:
        place(drums, clap(), t0 + BEAT, 0.5 * level)
        place(drums, clap(), t0 + 3 * BEAT, 0.5 * level)
    if bass_on:
        for beat, off in BASS_PAT:
            place(music, bass(midi(root + off), 0.3), t0 + beat * BEAT, 0.7 * level)
    if stabs:
        for beat in (0.75, 2.25, 3.75):
            place(music, stab(CHORDS[b % 4]), t0 + beat * BEAT, 0.26 * level)


bar(3, hats=False, claps=False, stabs=False)                   # 6-8: beat comes in under "OPTIMA"
for b in (4, 5, 6):                                            # 8-14: the proof
    bar(b)
bar(7, kick_on=False, hats=False, claps=False, stabs=False, level=0.6)  # 14-16: breakdown, the prompt goes in
for beat in (2, 3):                                            # kick returns at 15.0 for the doors
    place(drums, kick(), 14 + beat * BEAT, 0.9)
    kick_times.append(14 + beat * BEAT)
bar(8, hats=False, claps=False, stabs=False)                   # 16-18
for b in (9, 10, 11):                                          # 18-24: the rewards
    bar(b)
bar(12, claps=False, stabs=False, level=0.8)                   # 24-26: end card, thinning out
for beat in (0, 1):
    place(drums, kick(), 26 + beat * BEAT, 0.6)
    kick_times.append(26 + beat * BEAT)

# a bass hit on every cut
for t0 in (8.0, 11.0, 14.0, 15.0, 17.0, 18.0, 24.0):
    place(drums, boom(1.1), t0, 0.75 if t0 != 24.0 else 1.0)
place(drums, boom(0.9), 6.0, 0.8)

# text hits
for t0 in (6.0, 7.0, 9.0, 12.5, 13.0, 18.5, 20.0, 21.5, 22.5, 24.5):
    place(music, stab([55, 62, 67, 70], 0.3), t0, 0.3)

# ---------------------------------------------------------------- scene sound effects
place(sfx, whoosh(0.35, 800, 6000), 8.0, 0.28)
place(sfx, np.stack([printer(1.4)] * 2, axis=1), 11.0, 0.5)
for i in range(11):
    place(sfx, tick(), 12.0 + i * 0.04, 0.3, pan=0.3)           # the number counts up
place(sfx, ding(midi(91), 0.9), 12.45, 0.4)
place(sfx, whoosh(0.7, 600, 5000, peak=0.8), 14.15, 0.4)       # prompt flies into the ring
place(sfx, blip(240), 14.85, 0.5)
place(sfx, blip(170), 15.4, 0.55)                              # "Overkill."
place(sfx, blip(150), 15.9, 0.55)                              # "Still overkill."
place(sfx, ding(midi(86), 0.9), 16.3, 0.45)                    # "Fits."
place(sfx, ding(midi(91), 1.0), 16.38, 0.4)
place(sfx, whoosh(0.3, 900, 6000), 17.0, 0.3)
for i, t0 in enumerate((19.0, 20.0, 21.0, 22.0, 23.0)):
    place(sfx, clink(), t0, 0.7, pan=(-0.3, 0.3)[i % 2])       # a coin passes the ring
place(sfx, ding(midi(86), 1.2), 25.5, 0.4)                     # domain
place(sfx, ding(midi(91), 1.6), 26.5, 0.36)                    # ticker / contract address

# outro chord at 24.0, held and released before the final two seconds
t = tt(4.6)
pad = np.zeros((len(t), 2))
for n in (43, 55, 62, 67, 70):
    for ch in range(2):
        ff = midi(n) * 2 ** ((ch * 10 - 5) / 1200)
        for k in range(1, 9):
            pad[:, ch] += np.sin(2 * np.pi * k * ff * t + k) / k
pad = lp(pad / 5, 1500) * (np.minimum(1, t / 0.02) * np.exp(-t * 0.7) * np.clip((4.6 - t) / 1.4, 0, 1))[:, None]
place(music, pad, 24.0, 0.45)

# ---------------------------------------------------------------- mix
duck = np.ones(N)
for kt in kick_times:
    i = int(kt * SR)
    n = min(int(0.26 * SR), N - i)
    duck[i:i + n] = np.minimum(duck[i:i + n], 1 - 0.5 * np.exp(-np.arange(n) / SR * 14))
music *= duck[:, None]

ir_t = tt(1.6)
ir = lp(np.stack([rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 4.0) for _ in range(2)], axis=1), 6000)
send = music * 0.25 + sfx * 0.5 + drums * 0.04
wet = np.stack([fftconvolve(send[:, c], ir[:, c])[:N] for c in range(2)], axis=1)
wet /= np.max(np.abs(wet)) + 1e-9

mix = drums * 0.5 + music * 0.75 + sfx * 0.85 + wet * 0.16
mix = hp(mix, 28)
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(mix * 2.6) / np.tanh(2.6)
t_all = np.arange(N) / SR
mix *= np.clip((28.6 - t_all) / 1.2, 0, 1)[:, None]           # quiet under the held final frame
mix /= np.max(np.abs(mix)) + 1e-9
mix = lp(mix, 16000, order=4)                                 # tame inter-sample peaks from the bright effects
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.78

out = sys.argv[1] if len(sys.argv) > 1 else "out/music.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("wrote", out, f"{LENGTH}s")
