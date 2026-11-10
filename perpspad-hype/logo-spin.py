"""Perps Pad logo GIF: fast 3D spin with motion blur and glitches, then the logo locks in and holds still.

Usage: python3 logo-spin.py [assets/brand/perps-pad-podium.png] [out-prefix]
Writes <prefix>.gif and <prefix>.mp4.
"""
import subprocess
import sys

import numpy as np
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "assets/brand/perps-pad-podium.png"
OUT = sys.argv[2] if len(sys.argv) > 2 else "perpspad-logo-spin"
S = 720           # render size (MP4 is upscaled to 1080, GIF saved at GIF_S)
GIF_S = 480
FPS = 25          # GIF-friendly (40 ms frames)
SPIN_END = 1.45   # seconds of spinning
TURNS = 6
HOLD = 2.2        # seconds standing still at the end
rng = np.random.default_rng(3)

img = np.asarray(Image.open(SRC).convert("RGB").resize((S, S), Image.LANCZOS)).astype(np.float32)
H, W, _ = img.shape

# background gradient sampled from the left edge (no logo there)
grad = np.repeat(img[:, 4:14].mean(axis=1, keepdims=True), W, axis=1)
yy, xx = np.mgrid[0:H, 0:W]

# logo matte: how much brighter than the background each pixel is (keeps the glow halo)
m = np.clip((img[..., 1] - grad[..., 1] - 8) / 95, 0, 1)
m[(yy > 0.765 * H) & (xx > 0.27 * W)] = 0        # leave the podium ring in the background
m[yy > 0.80 * H] = 0
premul = np.clip(img - grad * (1 - m[..., None]), 0, 255)
plate = img * (1 - m[..., None]) + grad * m[..., None]

cols = np.where(m.max(axis=0) > 0.5)[0]
cx = (cols.min() + cols.max()) / 2


def squash(sx):
    """Scale the logo horizontally about its center (sx<0 shows the mirrored back)."""
    if abs(sx) < 1e-3:
        return np.zeros_like(premul), np.zeros_like(m)
    src = cx + (np.arange(W) - cx) / sx
    valid = (src >= 0) & (src <= W - 1)
    s0 = np.clip(np.floor(src).astype(int), 0, W - 1)
    s1 = np.clip(s0 + 1, 0, W - 1)
    f = (src - np.floor(src))[None, :]
    p = premul[:, s0] * (1 - f[..., None]) + premul[:, s1] * f[..., None]
    a = m[:, s0] * (1 - f) + m[:, s1] * f
    p[:, ~valid] = 0
    a[:, ~valid] = 0
    if sx < 0:
        p = p * 0.62  # darker back face
    return p, a


def angle(t):
    p = min(1, t / SPIN_END)
    return 2 * np.pi * TURNS * (1 - (1 - p) ** 2.6)


def glitch(fr, g, seed):
    r = np.random.default_rng(seed)
    out = fr.copy()
    d = int(2 + 14 * g)
    out[..., 0] = np.roll(fr[..., 0], d, axis=1)
    out[..., 2] = np.roll(fr[..., 2], -d, axis=1)
    for _ in range(int(3 + 10 * g)):
        y = r.integers(0, H - 8)
        h = int(r.integers(3, 8 + int(40 * g)))
        out[y:y + h] = np.roll(out[y:y + h], int(r.normal(0, 70 * g)), axis=1)
    if r.random() < 0.6 * g:
        y, x = r.integers(0, H - 60), r.integers(0, W - 160)
        hh, ww = r.integers(10, 60), r.integers(60, 160)
        out[y:y + hh, x:x + ww] = out[y:y + hh, x:x + ww][..., [1, 2, 0]]
    out[::2] *= 1 - 0.18 * g
    return out


frames, durations = [], []
n = int(round((SPIN_END + 0.45) * FPS))
for i in range(n):
    t = i / FPS
    # motion blur: average sub-frame angles while spinning
    subs = 5 if t < SPIN_END else 1
    acc_p = np.zeros_like(premul)
    acc_a = np.zeros_like(m)
    for s in range(subs):
        p, a = squash(np.cos(angle(t + s / (subs * FPS))))
        acc_p += p
        acc_a += a
    p, a = acc_p / subs, acc_a / subs
    fr = p + plate * (1 - a[..., None])
    # spin glow behind the logo
    spin_speed = 1 - min(1, t / SPIN_END)
    if t < SPIN_END:
        glow = np.exp(-(((xx - cx) / (W * 0.35)) ** 2 + ((yy - H * 0.47) / (H * 0.33)) ** 2)) * 60 * spin_speed
        fr += glow[..., None] * np.array([0.15, 1.0, 0.9])
    # glitch envelope: busy while spinning, a burst at the lock-in, a couple of aftershocks
    land = SPIN_END
    g = 0.0
    if t < land:
        g = 0.35 + 0.35 * abs(np.sin(t * 23)) + (0.5 if land - t < 0.25 else 0)
    elif t < land + 0.12:
        g = 0.9
    elif abs(t - (land + 0.28)) < 0.021:
        g = 0.4
    if g > 0:
        fr = glitch(fr, min(1, g), i)
    # flash on lock-in
    k = t - land
    if k >= 0:
        fr = fr + (255 - fr) * 0.55 * np.exp(-k * 14)
    frames.append(Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)))
    durations.append(int(1000 / FPS))

# standing still: the clean logo, held
frames.append(Image.fromarray(img.astype(np.uint8)))
durations.append(int(HOLD * 1000))

pal = [f.resize((GIF_S, GIF_S), Image.LANCZOS).quantize(colors=160, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG) for f in frames]
pal[0].save(f"{OUT}.gif", save_all=True, append_images=pal[1:], duration=durations, loop=0, optimize=False, disposal=1)

# MP4 version (for X / Telegram), same timing at 50 fps
tmp = f"{OUT}-frames"
subprocess.run(["rm", "-rf", tmp])
subprocess.run(["mkdir", "-p", tmp])
idx = 0
for f, d in zip(frames, durations):
    for _ in range(max(1, round(d / 20))):
        f.resize((1080, 1080), Image.LANCZOS).save(f"{tmp}/f{idx:05d}.png")
        idx += 1
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", "50", "-i", f"{tmp}/f%05d.png",
                "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", f"{OUT}.mp4"], check=True)
subprocess.run(["rm", "-rf", tmp])
print("wrote", f"{OUT}.gif", f"{OUT}.mp4", len(frames), "gif frames")
