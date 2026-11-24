"""Render a full-width scrolling ribbon for each toolkit category."""

from PIL import Image, ImageDraw

from art import ASSETS, font, save_gif


WIDTH = 1280
BAND_HEIGHT = 74
GAP = 16
MARGIN = 34
BACKGROUND = "#0b0b0d"
WHITE = "#ffffff"
COLORS = ("#16974b", "#9841ec")

TOOLKIT = (
    ("Languages", ("C", "C++", "Java", "JavaScript", "TypeScript", "Python")),
    ("Frontend", ("React", "HTML", "CSS", "Tailwind CSS", "Vite", "Responsive design")),
    ("Backend & data", ("Node.js", "Express", "MongoDB", "MySQL", "Supabase")),
    ("Exploring through projects", ("AWS", "AI agents", "Blockchain", "Algorand", "Smart contracts")),
    ("Foundations", ("Data structures", "Algorithms", "Operating systems", "Git & GitHub")),
)
HEIGHT = 2 * MARGIN + len(TOOLKIT) * BAND_HEIGHT + (len(TOOLKIT) - 1) * GAP


def make_strip(category, skills, color, typeface):
    text = f"{category}:    {'  •  '.join(skills)}".upper()
    period = round(typeface.getlength(text)) + 96
    strip = Image.new("RGB", (period, BAND_HEIGHT), color)
    ImageDraw.Draw(strip).text((0, BAND_HEIGHT / 2), text, font=typeface,
                               fill=WHITE, anchor="lm")
    return strip


def render_frame(strips, phase):
    frame = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    for index, strip in enumerate(strips):
        direction = -1 if index % 2 == 0 else 1
        start = (27 + direction * round(phase * strip.width)) % strip.width - strip.width
        y = MARGIN + index * (BAND_HEIGHT + GAP)
        for x in range(start, WIDTH, strip.width):
            frame.paste(strip, (x, y))
    return frame


def render_still():
    """Keep every skill readable within its colored band in reduced motion."""
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    label_font = font(19, bold=True)
    pad_x = 28
    skills_by_row = ["   •   ".join(skills).upper() for _, skills in TOOLKIT]
    for size in range(34, 18, -1):
        skill_font = font(size, bold=True)
        if max(map(skill_font.getlength, skills_by_row)) <= WIDTH - 2 * pad_x:
            break
    else:
        raise ValueError("The toolkit skills do not fit in the still image")

    for index, ((label, _), skills) in enumerate(zip(TOOLKIT, skills_by_row)):
        y = MARGIN + index * (BAND_HEIGHT + GAP)
        draw.rectangle((0, y, WIDTH - 1, y + BAND_HEIGHT - 1), fill=COLORS[index % len(COLORS)])
        draw.text((pad_x, y + 12), label.upper(), font=label_font, fill=WHITE, anchor="lt")
        draw.text((pad_x, y + 36), skills, font=skill_font, fill=WHITE, anchor="lt")
    return image


def main():
    ASSETS.mkdir(exist_ok=True)
    typeface = font(51, bold=True)
    strips = [make_strip(label, skills, COLORS[index % len(COLORS)], typeface)
              for index, (label, skills) in enumerate(TOOLKIT)]
    render_still().save(ASSETS / "toolkit-marquee.png", optimize=True)

    # A complete strip per loop, alternating the direction between adjacent bands.
    frame_count = 144
    frames = (render_frame(strips, i / frame_count) for i in range(frame_count))
    save_gif(frames, ASSETS / "toolkit-marquee.gif", duration=100, hold=100,
             palette_source=render_frame(strips, 0))


if __name__ == "__main__":
    main()
