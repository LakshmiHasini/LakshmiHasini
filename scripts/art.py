"""Shared drawing primitives for the repository's self-contained images."""
from pathlib import Path

from PIL import Image, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
BG = "#0d1117"
FG = "#eef3ed"
MUTED = "#9aa79e"
ACCENT = "#b5efbd"
GRID = ["#1c2724", "#304c3a", "#527d56", "#80b37d", "#b5efbd"]


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


def save_gif(frames, path, duration=80, hold=2400, palette_source=None):
    # One shared palette avoids flickering text and unnecessary GIF file size.
    palette = (palette_source if palette_source is not None else frames[-1]).convert("RGB").quantize(colors=128)
    indexed = [f.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    durations = [duration] * len(indexed)
    durations[-1] = hold
    indexed[0].save(path, save_all=True, append_images=indexed[1:],
                    duration=durations, loop=0, optimize=True, disposal=1)

