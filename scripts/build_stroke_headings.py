"""Render the README headings as tracing outlines with a rising ink fill."""

from bisect import bisect_right
from dataclasses import dataclass, replace
from itertools import accumulate
from math import ceil, hypot, sin

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter

from art import ASSETS, font


HEADINGS = {
    "my-toolkit": "My toolkit",
    "things-ive-built": "Things I've built",
    "github-activity": "GitHub activity",
    "leetcode-progress": "LeetCode progress",
    "lets-connect": "Let's connect",
}
OUTPUT = ASSETS / "headings"
WIDTH, HEIGHT, SCALE = 1000, 104, 2
SIZE = (WIDTH * SCALE, HEIGHT * SCALE)
FONT_SIZE = 56
BASELINE = 73 * SCALE
BACKGROUND = "#0c1325"
GUIDE = "#577096"
STROKE = "#e2f5ff"
INK = "#85c9ff"
TIP = "#45edff"
TRACE_SECONDS, FILL_SECONDS, STAGGER = 0.92, 0.70, 0.058


class Contours(BasePen):
    """Flatten the font's actual quadratic or cubic outline to draw its length."""

    def __init__(self, glyphs):
        super().__init__(glyphs)
        self.paths = []

    def _moveTo(self, point):
        self.paths.append([point])

    def _lineTo(self, point):
        self.paths[-1].append(point)

    def _qCurveToOne(self, control, end):
        start = self.paths[-1][-1]
        for k in range(1, 11):
            t = k / 10
            s = 1 - t
            self._lineTo(tuple(s * s * a + 2 * s * t * b + t * t * c for a, b, c in zip(start, control, end)))

    def _curveToOne(self, control1, control2, end):
        start = self.paths[-1][-1]
        for k in range(1, 13):
            t = k / 12
            s = 1 - t
            self._lineTo(tuple(s**3 * a + 3 * s**2 * t * b + 3 * s * t**2 * c + t**3 * d
                               for a, b, c, d in zip(start, control1, control2, end)))

    def _closePath(self):
        self._lineTo(self.paths[-1][0])

    def _endPath(self):
        pass


@dataclass(frozen=True)
class Stroke:
    points: tuple
    distance: tuple

    @classmethod
    def from_points(cls, points):
        distance = tuple(accumulate((hypot(b[0] - a[0], b[1] - a[1])
                                     for a, b in zip(points, points[1:])), initial=0))
        return cls(tuple(points), distance)

    def visible(self, progress):
        if progress >= 1:
            return self.points
        end = self.distance[-1] * progress
        i = bisect_right(self.distance, end)
        fraction = (end - self.distance[i - 1]) / (self.distance[i] - self.distance[i - 1])
        a, b = self.points[i - 1], self.points[i]
        tip = tuple(start + (finish - start) * fraction for start, finish in zip(a, b))
        return (*self.points[:i], tip)


@dataclass(frozen=True)
class Letter:
    strokes: tuple[Stroke, ...]
    mask: Image.Image
    left: int
    top: int
    delay: float


def layout(text, typeface, outlines):
    cmap = outlines.getBestCmap()
    glyphs = outlines.getGlyphSet()
    metrics = outlines["hmtx"].metrics
    unit = FONT_SIZE * SCALE / outlines["head"].unitsPerEm
    advance = 0
    letters = []
    for char in text:
        name = cmap[ord(char)]
        if char != " ":
            x = round(advance)
            pen = Contours(glyphs)
            glyphs[name].draw(pen)
            strokes = tuple(Stroke.from_points([(x + a * unit, BASELINE - b * unit) for a, b in path])
                            for path in pen.paths if len(path) >= 2)
            x0, y0, x1, y1 = typeface.getbbox(char, anchor="ls")
            mask = Image.new("L", (x1 - x0 + 4, y1 - y0 + 4))
            ImageDraw.Draw(mask).text((2 - x0, 2 - y0), char, font=typeface, fill=255, anchor="ls")
            letters.append(Letter(strokes, mask, x + x0 - 2, BASELINE + y0 - 2, len(letters) * STAGGER))
        advance += metrics[name][0] * unit - 0.8 * SCALE
    points = [point for letter in letters for stroke in letter.strokes for point in stroke.points]
    xs, ys = zip(*points)
    dx = round((SIZE[0] - min(xs) - max(xs)) / 2)
    dy = round((SIZE[1] - min(ys) - max(ys)) / 2)
    return [replace(letter, left=letter.left + dx, top=letter.top + dy,
                    strokes=tuple(replace(stroke, points=tuple((x + dx, y + dy) for x, y in stroke.points))
                                  for stroke in letter.strokes))
            for letter in letters]


def smooth(value):
    value = min(1.0, max(0.0, value))
    return value * value * (3 - 2 * value)


def ink_fill(image, letter, level, time):
    mask = letter.mask
    if level < 1:
        height = mask.height * (1 - level)
        wave = [(x, height + 2.7 * SCALE * sin(x / 13 + time * 9)) for x in range(0, mask.width, 3)]
        liquid = Image.new("L", mask.size)
        ImageDraw.Draw(liquid).polygon([*wave, (mask.width, mask.height), (0, mask.height)], fill=255)
        mask = Image.composite(mask, Image.new("L", mask.size), liquid)
    color = Image.new("RGB", mask.size, INK)
    image.paste(color, (letter.left, letter.top), mask)


def render(base, letters, time):
    image = base.copy()
    glow = Image.new("L", SIZE)
    tips = ImageDraw.Draw(glow)
    draw = ImageDraw.Draw(image)
    for letter in letters:
        elapsed = time - letter.delay
        filled = smooth((elapsed - TRACE_SECONDS) / FILL_SECONDS)
        if filled:
            ink_fill(image, letter, filled, time)
        traced = smooth(elapsed / TRACE_SECONDS)
        if traced:
            for path in letter.strokes:
                points = path.visible(traced)
                draw.line(points, fill=STROKE, width=3, joint="curve")
                if traced < 1:
                    x, y = points[-1]
                    tips.ellipse((x - 4, y - 4, x + 4, y + 4), fill=235)
    halo = glow.filter(ImageFilter.GaussianBlur(4))
    color = Image.new("RGB", SIZE, TIP)
    image.paste(color, (0, 0), halo)
    image.paste(color, (0, 0), glow)
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def build(name, text, typeface, outlines):
    letters = layout(text, typeface, outlines)
    base = Image.new("RGB", SIZE, BACKGROUND)
    guide = ImageDraw.Draw(base)
    for letter in letters:
        for path in letter.strokes:
            guide.line(path.points, fill=GUIDE, width=3, joint="curve")

    end = letters[-1].delay + TRACE_SECONDS + FILL_SECONDS + 0.01
    frame_count = ceil(end / 0.070)
    rising = [render(base, letters, i / frame_count * end) for i in range(frame_count + 1)]
    still = rising[-1]
    still.save(OUTPUT / f"{name}.png", optimize=True)
    samples = Image.new("RGB", (WIDTH, HEIGHT * 3))
    for i, frame in enumerate((rising[len(rising) // 3], rising[len(rising) * 2 // 3], still)):
        samples.paste(frame, (0, HEIGHT * i))
    palette = samples.quantize(colors=96)
    draining = rising[-2:0:-3]
    frames = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in rising + draining]
    duration = [70] * (len(rising) - 1) + [4700] + [60] * len(draining)
    frames[0].save(OUTPUT / f"{name}.gif", save_all=True, append_images=frames[1:],
                   duration=duration, loop=0, optimize=True, disposal=1)


def main():
    typeface = font(FONT_SIZE * SCALE, bold=True)
    if not getattr(typeface, "path", None):
        raise RuntimeError("Install a system TrueType font used by scripts/art.py")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with TTFont(typeface.path) as outlines:
        for name, title in HEADINGS.items():
            build(name, title, typeface, outlines)


if __name__ == "__main__":
    main()
