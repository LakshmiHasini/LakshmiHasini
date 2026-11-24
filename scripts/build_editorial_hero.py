"""Render the supplied Elias hero's editorial style for a GitHub README.

Run: python scripts/build_editorial_hero.py
Uses the existing portrait unchanged inside a rounded photo frame. No network calls.
"""
from functools import lru_cache
from math import sin, pi
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from art import ASSETS, font

W, H = 1440, 920
PAGE = "#f6f4f0"
INK = "#171412"
ORANGE = "#ff4829"
MUTED = "#77716e"
RULE = "#d9d3ca"
NOTE = "Build something useful.\nMake it feel simple.\nKeep learning, every day."


@lru_cache(maxsize=32)
def face(size, heavy=False, mono=False):
    if heavy:
        for path in ["/System/Library/Fonts/Supplemental/Arial Black.ttf",
                     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                     "C:/Windows/Fonts/arialbd.ttf"]:
            if Path(path).exists():
                return ImageFont.truetype(path, size)
    return font(size, mono=mono)


def text(draw, xy, value, size=22, fill=INK, heavy=False, mono=False):
    for i, line in enumerate(value.split("\n")):
        draw.text((xy[0], xy[1]+i*(size+10)), line,
                  font=face(size, heavy, mono), fill=fill, anchor="lt")


def word(value, width, height, color):
    f = face(260, heavy=True)
    box = f.getbbox(value)
    layer = Image.new("RGBA", (box[2] - box[0] + 4, box[3] - box[1] + 4))
    ImageDraw.Draw(layer).text((-box[0] + 2, -box[1] + 2), value, font=f, fill=color)
    return layer.resize((width, height), Image.Resampling.LANCZOS)


def arrow(draw, x, y, color=INK):
    draw.line((x, y+14, x+14, y), fill=color, width=2)
    draw.line((x+1, y, x+14, y, x+14, y+13), fill=color, width=2)


def ease(value):
    return 1 - (1 - min(1, max(0, value))) ** 3


def book(angle=0):
    """A project presented as a hardcover, echoing the reference's book card."""
    image = Image.new("RGBA", (240, 265))
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((29, 18, 216, 253), 5, fill="#c8aa95")
    d.rounded_rectangle((24, 13, 211, 248), 4, fill="#f8dccb", outline="#d6b39c", width=1)
    d.rectangle((24, 13, 35, 248), fill="#e8ac87")
    d.line((39, 20, 39, 242), fill="#e4bca4", width=1)
    text(d, (51, 30), "PROJECT / 01", 12, mono=True)
    text(d, (49, 59), "Seva", 37, heavy=True)
    text(d, (49, 99), "Recover", 31, heavy=True)
    d.ellipse((75, 149, 179, 253), fill="#ff9f80")
    d.rectangle((40, 201, 210, 247), fill="#f3c7ae")
    for y, inset in [(211, 0), (223, 14), (235, 29)]:
        d.line((63+inset, y, 191-inset, y), fill="#dfa582", width=3)
    return image.rotate(angle, Image.Resampling.BICUBIC)


def prepare():
    with Image.open(ASSETS / "portrait.png") as source:
        photo = ImageOps.fit(ImageOps.exif_transpose(source).convert("RGB"), (466, 504), centering=(.5, .45))
    mask = Image.new("L", photo.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 465, 503), radius=215, fill=255)
    # Square the bottom half, leaving an architectural arch across the top.
    ImageDraw.Draw(mask).rectangle((0, 235, 465, 503), fill=255)
    photo.putalpha(mask)
    return photo, word("LAKSHMI", 1002, 181, ORANGE), word("HASINI", 447, 136, INK)


def frame(t, prepared):
    photo, first, last = prepared
    image = Image.new("RGB", (W, H), PAGE)
    d = ImageDraw.Draw(image)
    # Masthead, deliberately quiet against the oversized name.
    text(d, (50, 33), "LH.", 28, heavy=True)
    text(d, (146, 41), "A DEVELOPER'S NOTEBOOK", 15, mono=True)
    text(d, (908, 41), "BENGALURU, INDIA", 15, mono=True)
    d.ellipse((1204, 44, 1212, 52), fill=ORANGE)
    text(d, (1226, 41), "LET'S BUILD", 15, mono=True)
    d.line((50, 87, 1390, 87), fill=RULE)

    # Name layers rise into place, then settle for most of the loop.
    for layer, x, y, delay in [(first, 41, 129, .05), (last, 943, 380, .18)]:
        p = ease((t-delay)/.8)
        image.paste(layer, (x, y+int((1-p)*40)), layer)

    # The project card occupies the same position as the book in the source design.
    d.rounded_rectangle((1101, 123, 1390, 307), radius=12, fill="#eae4da")
    d.ellipse((1171, 277, 1332, 294), fill="#d8cfc1")
    b = book(sin(t*1.2)*2 if t < 4.3 else 0).resize((180, 199), Image.Resampling.LANCZOS)
    image.paste(b, (1157, 106), b)
    text(d, (1102, 324), "SELECTED BUILD", 14, mono=True)
    arrow(d, 1370, 322)

    # Photo uses the repository owner's actual portrait, framed rather than replaced.
    py = 355
    d.rounded_rectangle((440, py-9, 924, py+513), radius=225, fill="#e9dfd1")
    d.rectangle((440, py+235, 924, py+513), fill="#e9dfd1")
    image.paste(photo, (449, py), photo)
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((471, py+450, 702, py+484), radius=17, fill=PAGE)
    text(d, (485, py+461), "BATCHU LAKSHMI HASINI", 13, mono=True)

    # Personal introduction in the reference's narrow editorial column.
    text(d, (53, 379), "STUDENT / DEVELOPER", 16, mono=True)
    text(d, (53, 408), "HACKATHON BUILDER", 16, mono=True)
    text(d, (50, 463), "Where logic", 40)
    text(d, (50, 511), "meets design.", 40)
    d.line((53, 580, 111, 580), fill=ORANGE, width=3)
    text(d, (53, 610), "Turning complex problems", 23, MUTED)
    text(d, (53, 643), "into thoughtful interfaces.", 23, MUTED)
    text(d, (53, 676), "Building, learning, repeating.", 23, MUTED)
    text(d, (53, 782), "REACT / TYPESCRIPT", 15, mono=True)
    text(d, (53, 810), "FULL STACK / AI / WEB3", 15, mono=True)

    # A writing pad, personalized from the original letter-to-tomorrow motif.
    d.rounded_rectangle((987, 574, 1390, 845), radius=4, fill="#eee8de")
    d.rounded_rectangle((1001, 560, 1376, 831), radius=4, fill="#fffdf8")
    text(d, (1023, 584), "A NOTE TO TOMORROW", 14, mono=True, fill=MUTED)
    d.line((1023, 616, 1354, 616), fill=RULE)
    text(d, (1023, 639), "Dear tomorrow,", 25)
    count = int(min(1, max(0, (t-1.1)/2.8))*len(NOTE))
    text(d, (1023, 686), NOTE[:count], 23)
    if count < len(NOTE):
        lines = NOTE[:count].split("\n")
        x = 1023 + d.textlength(lines[-1], font=face(23))
        y = 686 + (len(lines)-1)*33
        d.line((x+3, y, x+3, y+23), fill=ORANGE, width=2)
    else:
        d.ellipse((1310, 771, 1354, 815), fill=ORANGE)
        text(d, (1321, 787), "LH", 13, fill=PAGE, heavy=True)

    d.line((50, 871, 1390, 871), fill=RULE)
    text(d, (53, 893), "CURIOUS MIND. THOUGHTFUL CODE.", 14, mono=True)
    text(d, (1104, 893), "lakshmihasini.in", 16)
    arrow(d, 1372, 890)
    return image


def main():
    ASSETS.mkdir(exist_ok=True)
    prepared = prepare()
    still = frame(6, prepared)
    still.save(ASSETS / "editorial-hero.png", optimize=True)
    # Palette includes the final page and the entrance. The photograph stays fixed.
    palette = still.quantize(colors=192)
    times = [i*.1 for i in range(43)] + [6]
    frames = [frame(t, prepared).quantize(palette=palette, dither=Image.Dither.NONE) for t in times]
    frames[0].save(ASSETS / "editorial-hero.gif", save_all=True,
                   append_images=frames[1:], duration=[100]*43+[4200],
                   loop=0, optimize=True, disposal=1)
    print("Built assets/editorial-hero.gif and assets/editorial-hero.png")


if __name__ == "__main__":
    main()
