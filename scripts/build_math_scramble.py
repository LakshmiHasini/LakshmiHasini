"""Render a README adaptation of the supplied Math Scramble by Louis Studios."""

from dataclasses import dataclass
from random import Random
from textwrap import wrap

from PIL import Image, ImageDraw

from art import ASSETS, font, save_gif


WIDTH = 1440
BACKGROUND = "#08080a"
RESTING = "#b9b6c0"
ACCENT = "#ff785f"
COLORS = ("#f16d90", "#ff9a55", "#e5c667", "#90d47f", "#6cd9cf", "#7caaff", "#c39aff")
SYMBOLS = "+−×÷±=≠≈≤≥∞√∑∏∫∂∆∈∪∩∧∨←→↑↓αβγλπφωΩ[]"
BIO = (
    "I'm **Batchu Lakshmi Hasini**, studying Computer Science at **PW Institute of Innovation · Medhavi Skills University**. "
    "I enjoy turning a complex problem into an interface that feels simple, responsive, and useful.",
    "I build across the frontend and backend, practise data structures and algorithms, and explore AI and blockchain "
    "through hands-on projects. Hackathons are where I get to bring those interests together with a team and ship an idea.",
    "- **I care about:** thoughtful interfaces, clear code, and software that helps people.",
    "- **I work with:** React, TypeScript, Node.js, and the fundamentals underneath them.",
    "- **I'm open to:** internships, collaborations, and interesting hackathon teams.",
)
FONT_SIZE = 50
LINE_PITCH = 64
MARGIN_X = 76
MARGIN_Y = 60


@dataclass(frozen=True)
class Glyph:
    char: str
    x: float
    y: float
    highlighted: bool
    symbol: str
    color: str
    boxed: bool
    start: float | None
    hold: float


def layout(typeface):
    """Wrap paragraphs and hang bullet continuations under their text."""
    random = Random(29)
    cell = typeface.getlength("M")
    max_columns = int((WIDTH - 2 * MARGIN_X) / cell)
    glyphs = []
    y = MARGIN_Y + LINE_PITCH / 2
    row = 0
    for block in BIO:
        bullet = block.startswith("- ")
        runs = block.removeprefix("- ").split("**")
        plain = "".join(runs)
        emphasis = [bool(i % 2) for i, run in enumerate(runs) for _ in run]
        indent = 2 if bullet else 0
        lines = wrap(plain, max_columns - indent, break_long_words=False, break_on_hyphens=False)
        offset = 0
        if bullet:
            glyphs.append(Glyph("•", MARGIN_X + cell / 2, y, True, "", ACCENT, False, None, 0))
        for line in lines:
            offset = plain.index(line, offset)
            origin = len(line) * (0.72 if row % 2 else 0.28)
            for col, char in enumerate(line):
                if char == " ":
                    continue
                highlighted = emphasis[offset + col]
                start = None
                if not highlighted and char.isalnum():
                    start = 0.7 + row * 0.55 + abs(col - origin) * 0.022
                glyphs.append(Glyph(
                    char, MARGIN_X + cell * (indent + col + 0.5), y, highlighted,
                    random.choice(SYMBOLS), random.choice(COLORS),
                    random.random() < 0.43, start, random.uniform(0.28, 0.45),
                ))
            offset += len(line)
            y += LINE_PITCH
            row += 1
        y += 14 if bullet else 28
    height = int(y - LINE_PITCH / 2 - 14 + MARGIN_Y)
    return glyphs, cell, height


def render_still(typeface, glyphs, height):
    image = Image.new("RGB", (WIDTH, height), BACKGROUND)
    draw = ImageDraw.Draw(image)
    for glyph in glyphs:
        color = ACCENT if glyph.highlighted else RESTING
        draw.text((glyph.x, glyph.y), glyph.char, font=typeface, fill=color, anchor="mm")
    return image


def render_wave(time, still, typeface, glyphs, cell):
    image = still.copy()
    draw = ImageDraw.Draw(image)
    for glyph in glyphs:
        if glyph.start is None or not (0 <= time - glyph.start < glyph.hold):
            continue
        half = cell * 0.47
        bounds = (glyph.x - half, glyph.y - 27, glyph.x + half, glyph.y + 27)
        draw.rectangle(bounds, fill=BACKGROUND)
        if glyph.boxed:
            draw.rounded_rectangle(bounds, radius=6, outline=glyph.color, width=2)
        draw.text((glyph.x, glyph.y), glyph.symbol, font=typeface, fill=glyph.color, anchor="mm")
    return image


def main():
    ASSETS.mkdir(exist_ok=True)
    typeface = font(FONT_SIZE, mono=True)
    glyphs, cell, height = layout(typeface)
    still = render_still(typeface, glyphs, height)
    still.save(ASSETS / "math-scramble.png", optimize=True)

    # Include every symbol color in the GIF palette even if a wave shows it briefly.
    palette_source = still.copy()
    palette_draw = ImageDraw.Draw(palette_source)
    for i, color in enumerate(COLORS):
        palette_draw.rectangle((i * 48, 0, i * 48 + 47, 47), fill=color)

    duration = 100
    end = max(glyph.start + glyph.hold for glyph in glyphs if glyph.start is not None)
    steps = int(end * 1000 / duration) + 2
    frames = (render_wave(step * duration / 1000, still, typeface, glyphs, cell) for step in range(steps))
    save_gif(frames, ASSETS / "math-scramble.gif", duration=duration, hold=2100,
             palette_source=palette_source)


if __name__ == "__main__":
    main()
