"""Apply the supplied component's Bayer kernel to the real portrait and animate it.

Usage: python scripts/build_banner.py [path/to/a/replacement/photo.jpg]
"""
import argparse

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from art import ACCENT, ASSETS, BG, FG, MUTED, font, save_gif

BAYER = [
    0, 32, 8, 40, 2, 34, 10, 42, 48, 16, 56, 24, 50, 18, 58, 26,
    12, 44, 4, 36, 14, 46, 6, 38, 60, 28, 52, 20, 62, 30, 54, 22,
    3, 35, 11, 43, 1, 33, 9, 41, 51, 19, 59, 27, 49, 17, 57, 25,
    15, 47, 7, 39, 13, 45, 5, 37, 63, 31, 55, 23, 61, 29, 53, 21,
]
WIDTH, HEIGHT = 1280, 480
PORTRAIT_WIDTH = 600
PORTRAIT_X = WIDTH - PORTRAIT_WIDTH
DARK = (17, 16, 24)
LIGHT = (221, 214, 244)


def dither(image, pixel_size=3):
    """The component's 8x8 Bayer threshold, two tones, with nearest-neighbour pixels."""
    grid = image.resize((image.width // pixel_size, image.height // pixel_size), Image.Resampling.LANCZOS)
    values = ImageOps.grayscale(grid)
    out = Image.new("RGB", grid.size)
    pixels = []
    for y in range(grid.height):
        for x in range(grid.width):
            value = values.getpixel((x, y)) / 255
            value += (BAYER[(y % 8) * 8 + x % 8] + 0.5) / 64 - 0.5
            pixels.append(LIGHT if value >= 0.5 else DARK)
    out.putdata(pixels)
    return out.resize(image.size, Image.Resampling.NEAREST)


def compose(portrait):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), BG)
    canvas.paste(portrait, (PORTRAIT_X, 0))
    # Feather only the left edge; the face remains visible on the right.
    fade = Image.new("L", (PORTRAIT_WIDTH, HEIGHT))
    fd = ImageDraw.Draw(fade)
    for x in range(PORTRAIT_WIDTH):
        alpha = int(255 * (1 - min(1, x / 180)) ** 1.8)
        fd.line((x, 0, x, HEIGHT), fill=alpha)
    canvas.paste(Image.new("RGB", portrait.size, BG), (PORTRAIT_X, 0), fade)
    draw = ImageDraw.Draw(canvas)
    draw.text((54, 35), "BATCHU LAKSHMI HASINI", font=font(15, mono=True), fill=ACCENT)
    draw.line((54, 75, 617, 75), fill="#40364f", width=1)
    draw.text((48, 109), "Lakshmi", font=font(100, bold=True), fill=FG)
    draw.text((48, 208), "Hasini.", font=font(100, bold=True), fill=FG)
    draw.text((55, 339), "Where logic meets design.", font=font(25), fill=FG)
    draw.text((55, 389), "FRONTEND  /  FULL STACK  /  WEB3", font=font(16, mono=True), fill=MUTED)
    draw.text((55, 437), "BENGALURU, INDIA", font=font(13, mono=True), fill=MUTED)
    draw.text((1006, 440), "@LakshmiHasini", font=font(16, mono=True), fill=FG,
              stroke_width=2, stroke_fill=BG)
    return canvas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("photo", nargs="?", default=str(ASSETS / "portrait.png"))
    args = parser.parse_args()
    ASSETS.mkdir(exist_ok=True)
    with Image.open(args.photo) as source:
        source = ImageOps.exif_transpose(source).convert("RGB")
        # Move the face into the right half of the banner, preserving the original photo.
        portrait = ImageOps.fit(source, (PORTRAIT_WIDTH, HEIGHT), centering=(0.5, 0.42))
    portrait = ImageEnhance.Contrast(portrait).enhance(1.15)
    still = dither(portrait)
    composed = compose(still)
    composed.save(ASSETS / "dither-banner.png", optimize=True)
    # A travelling band shifts between two pixel sizes, then settles on the portrait.
    # This keeps the original face visible throughout the entire loop.
    alternate = dither(portrait, pixel_size=5)
    frames = []
    for i in range(34):
        t = i / 33
        center = -160 + t * (PORTRAIT_WIDTH + 320)
        mask = Image.new("L", still.size)
        md = ImageDraw.Draw(mask)
        md.rectangle((center - 70, 0, center + 70, HEIGHT), fill=220)
        mask = mask.filter(ImageFilter.GaussianBlur(22))
        frames.append(compose(Image.composite(alternate, still, mask)))
    frames.append(composed)
    save_gif(frames, ASSETS / "dither-banner.gif", duration=70, hold=2700)
    print("Built dither-banner.gif and its still-image alternative from the supplied photo.")


if __name__ == "__main__":
    main()

