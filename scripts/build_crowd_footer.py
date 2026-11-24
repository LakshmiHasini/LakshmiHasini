"""Render the Skiper UI Canvas Crowd as a closing banner for a GitHub README."""

from dataclasses import dataclass
from math import sin, tau
from random import Random

from PIL import Image, ImageDraw, ImageOps

from art import ASSETS, font, save_gif


WIDTH, HEIGHT = 1280, 494
GIF_SIZE = (840, 324)
PAPER = "#f6f4f0"
INK = "#181614"
CORAL = "#ee573b"
SPRITE_COLUMNS = 15
SPRITE_ROWS = 7


@dataclass(frozen=True)
class Lane:
    count: int
    step: int
    bottom: int
    heights: tuple[int, int]
    direction: int
    ink: str
    bounce: int


LANES = (
    Lane(12, 84, 372, (119, 142), -1, "#a0958a", 2),
    Lane(13, 96, 439, (145, 175), 1, "#64584e", 3),
    Lane(11, 124, 512, (185, 225), -1, "#211d1a", 5),
)


@dataclass(frozen=True)
class Person:
    sprite: Image.Image
    x: int
    bottom: int
    beat: float


def load_sprites():
    with Image.open(ASSETS / "crowd-sprites.png") as source:
        sheet = source.convert("RGBA")
    cell_width = sheet.width // SPRITE_COLUMNS
    cell_height = sheet.height // SPRITE_ROWS
    sprites = []
    for row in range(SPRITE_ROWS):
        for col in range(SPRITE_COLUMNS):
            x, y = col * cell_width, row * cell_height
            cell = sheet.crop((x, y, x + cell_width, y + cell_height))
            box = cell.getbbox()
            if box:
                sprites.append(cell.crop(box))
    return sprites


def prepare_crowd(sprites):
    random = Random(713)
    samples = iter(random.sample(sprites, sum(lane.count for lane in LANES)))
    crowd = []
    for row, lane in enumerate(LANES):
        people = []
        for i in range(lane.count):
            source = next(samples)
            shade = "#aa3d2c" if row == 2 and i in (2, 8) else lane.ink
            tinted = ImageOps.colorize(source.convert("L"), shade, PAPER)
            tinted.putalpha(source.getchannel("A"))
            height = random.randint(*lane.heights)
            width = round(tinted.width * height / tinted.height)
            sprite = tinted.resize((width, height), Image.Resampling.LANCZOS)
            if lane.direction < 0:
                sprite = ImageOps.mirror(sprite)
            people.append(Person(sprite, i * lane.step + random.randint(-12, 12),
                                 lane.bottom + random.randint(-13, 13), random.random()))
        crowd.append(people)
    return crowd


def background():
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)
    draw.line((44, 28, WIDTH - 44, 28), fill="#d7cdc2", width=1)
    draw.text((WIDTH / 2, 57), "LAKSHMI HASINI", font=font(17, mono=True), fill="#6f6055", anchor="mt")
    draw.text((WIDTH / 2, 90), "Let's build something useful.", font=font(63, bold=True), fill=INK, anchor="mt")
    draw.text((WIDTH / 2, 166), "Open to internships, collaborations, and hackathons.",
              font=font(26), fill="#594d44", anchor="mt")
    draw.line((WIDTH / 2 - 23, 216, WIDTH / 2 + 23, 216), fill=CORAL, width=3)
    return image


def render(base, crowd, phase):
    image = base.copy()
    phase = phase % 1
    for lane, people in zip(LANES, crowd):
        period = lane.count * lane.step
        for person in people:
            sprite = person.sprite
            first = round((person.x + lane.direction * phase * period) % period) - period
            bob = round(lane.bounce * sin(tau * (12 * phase + person.beat)))
            for x in range(first, WIDTH, period):
                if x + sprite.width > 0:
                    image.paste(sprite, (x, person.bottom - sprite.height + bob), sprite)
    return image


def main():
    base = background()
    crowd = prepare_crowd(load_sprites())
    start = 0.18
    still = render(base, crowd, start)
    still.save(ASSETS / "crowd-footer.png", optimize=True)

    frame_count = 80
    frames = (render(base, crowd, start + step / frame_count).resize(GIF_SIZE, Image.Resampling.LANCZOS)
              for step in range(frame_count))
    save_gif(frames, ASSETS / "crowd-footer.gif", duration=120, hold=120, palette_source=still)


if __name__ == "__main__":
    main()
