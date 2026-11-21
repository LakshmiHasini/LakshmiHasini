"""Shared drawing primitives for the repository's self-contained images."""
from pathlib import Path

from PIL import Image, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
BG = "#111018"
FG = "#f4f0fa"
MUTED = "#aca5b9"
ACCENT = "#c7bbff"
GRID = ["#252130", "#443557", "#6c518c", "#9d7dc3", "#c7bbff"]


def font(size, bold=False, mono=False):
    if mono:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/System/Library/Fonts/Menlo.ttc",
            "C:/Windows/Fonts/consola.ttf",
        ]
    else:
        suffix = "-Bold" if bold else ""
        candidates = [
            f"/usr/share/fonts/truetype/dejavu/DejaVuSans{suffix}.ttf",
            f"/System/Library/Fonts/Supplemental/Arial{' Bold' if bold else ''}.ttf",
            f"C:/Windows/Fonts/arial{'bd' if bold else ''}.ttf",
        ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def save_gif(frames, path, duration=80, hold=2400):
    # One shared palette avoids flickering text and unnecessary GIF file size.
    palette = frames[-1].convert("RGB").quantize(colors=128)
    indexed = [f.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    durations = [duration] * len(indexed)
    durations[-1] = hold
    indexed[0].save(path, save_all=True, append_images=indexed[1:],
                    duration=durations, loop=0, optimize=True, disposal=1)

