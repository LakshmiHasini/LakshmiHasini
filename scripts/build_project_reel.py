"""Render a curved, looping strip of project screenshots for the GitHub README."""

from dataclasses import dataclass
from math import ceil, cos, floor, radians, sin

from PIL import Image, ImageDraw, ImageOps

from art import ASSETS, font


WIDTH, HEIGHT = 1280, 455
GIF_SIZE = (900, 320)
CARD_WIDTH, CARD_HEIGHT = 436, 267
CAMERA = 1.6
EDGE = radians(68)
RADIUS = WIDTH * (CAMERA - 1 + cos(EDGE)) / (2 * CAMERA * sin(EDGE))
PITCH = (CARD_WIDTH + 22) / RADIUS
BACKGROUND = "#0b0b0d"
SCREENSHOTS = ASSETS / "project-screenshots"


@dataclass(frozen=True)
class Project:
    name: str
    screenshot: str
    label: str
    accent: str


PROJECTS = (
    Project("SevaRecover", "sevarecover.png", "CIVIC TECH", "#88b6ff"),
    Project("Recall", "recall.png", "INCIDENT INTELLIGENCE", "#d4cfff"),
    Project("JobFit Lab", "jobfit-lab.png", "LOCAL DEMO", "#c1a8ff"),
    Project("ChainMatrix", "chainmatrix.png", "TEAM PROJECT", "#75eac1"),
)


def project_card(project):
    image = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), "#14161c")
    with Image.open(SCREENSHOTS / project.screenshot) as source:
        screenshot = ImageOps.fit(source.convert("RGB"), (CARD_WIDTH - 12, 218),
                                  Image.Resampling.LANCZOS, centering=(0.5, 0))
    thumbnail_mask = Image.new("L", screenshot.size)
    ImageDraw.Draw(thumbnail_mask).rounded_rectangle((0, 0, screenshot.width - 1, screenshot.height - 1),
                                                     radius=10, fill=255)
    image.paste(screenshot, (6, 6), thumbnail_mask)
    draw = ImageDraw.Draw(image)
    draw.ellipse((15, 242, 22, 249), fill=project.accent)
    draw.text((31, 246), project.name, font=font(23, bold=True), fill="#fcf7f2", anchor="lm")
    draw.text((CARD_WIDTH - 16, 246), project.label, font=font(12, mono=True),
              fill=project.accent, anchor="rm")
    draw.rounded_rectangle((1, 1, CARD_WIDTH - 2, CARD_HEIGHT - 2), radius=17,
                           outline=project.accent, width=1)
    alpha = Image.new("L", image.size)
    ImageDraw.Draw(alpha).rounded_rectangle((0, 0, CARD_WIDTH - 1, CARD_HEIGHT - 1), radius=17, fill=255)
    image.putalpha(alpha)
    return image


def project_point(angle):
    scale = CAMERA / (CAMERA - 1 + cos(angle))
    return WIDTH / 2 + RADIUS * sin(angle) * scale, scale


def draw_curved_card(image, card, center):
    """Draw adjoining vertical facets of one card on the cylinder."""
    facet = 6
    first = max(0, floor((CARD_WIDTH / 2 + (-EDGE - center) * RADIUS) / facet) * facet)
    last = min(CARD_WIDTH, ceil((CARD_WIDTH / 2 + (EDGE - center) * RADIUS) / facet) * facet)
    x0, scale0 = project_point(center + (first - CARD_WIDTH / 2) / RADIUS)
    for sx in range(first, last, facet):
        next_sx = min(sx + facet, last)
        x1, scale1 = project_point(center + (next_sx - CARD_WIDTH / 2) / RADIUS)
        left, right = round(x0), round(x1)
        if right > 0 and left < WIDTH and right > left:
            height = round(CARD_HEIGHT * (scale0 + scale1) / 2)
            strip = card.crop((sx, 0, next_sx, CARD_HEIGHT))
            strip = strip.resize((right - left, height), Image.Resampling.BILINEAR)
            image.paste(strip, (left, (HEIGHT - height) // 2), strip)
        x0, scale0 = x1, scale1


def edge_fade():
    ramp = Image.new("L", (WIDTH, 1))
    ramp.putdata([round(255 * min(1, x / 126, (WIDTH - 1 - x) / 126)) for x in range(WIDTH)])
    return ramp.resize((WIDTH, HEIGHT))


def render(cards, dark, fade, phase):
    image = dark.copy()
    position = (phase % 1) * len(cards)
    visible = EDGE + CARD_WIDTH / (2 * RADIUS)
    for i in range(floor(position - visible / PITCH), ceil(position + visible / PITCH) + 1):
        angle = (i - position) * PITCH
        if abs(angle) <= visible:
            draw_curved_card(image, cards[i % len(cards)], angle)
    return Image.composite(image, dark, fade)


def render_still(cards):
    """Show all the screenshot cards together for reduced motion."""
    gap, padding = 24, 32
    rows = ceil(len(cards) / 2)
    height = rows * CARD_HEIGHT + (rows - 1) * gap + 2 * padding
    image = Image.new("RGB", (WIDTH, height), BACKGROUND)
    for start in range(0, len(cards), 2):
        row = cards[start:start + 2]
        left = (WIDTH - len(row) * CARD_WIDTH - (len(row) - 1) * gap) // 2
        top = padding + start // 2 * (CARD_HEIGHT + gap)
        for index, card in enumerate(row):
            image.paste(card, (left + index * (CARD_WIDTH + gap), top), card)
    return image


def main():
    ASSETS.mkdir(exist_ok=True)
    cards = [project_card(project) for project in PROJECTS]
    dark = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    fade = edge_fade()
    render_still(cards).save(ASSETS / "project-reel.png", optimize=True)

    samples = Image.new("RGB", (CARD_WIDTH * len(cards), CARD_HEIGHT + 106), BACKGROUND)
    for i, card in enumerate(cards):
        samples.paste(card, (i * CARD_WIDTH, 0), card)
        contact = render(cards, dark, fade, i / len(cards)).resize((320, 106), Image.Resampling.LANCZOS)
        samples.paste(contact, (i * CARD_WIDTH, CARD_HEIGHT))
    palette = samples.quantize(colors=176)
    frame_count = 112
    frames = (
        render(cards, dark, fade, i / frame_count)
        .resize(GIF_SIZE, Image.Resampling.LANCZOS)
        .quantize(palette=palette, dither=Image.Dither.NONE)
        for i in range(frame_count)
    )
    first = next(frames)
    first.save(ASSETS / "project-reel.gif", save_all=True, append_images=frames,
               duration=110, loop=0, optimize=True, disposal=1)


if __name__ == "__main__":
    main()
