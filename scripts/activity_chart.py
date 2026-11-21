"""Render a real contribution calendar lifting into a three-dimensional terrain."""
from datetime import date, datetime
import math

from PIL import Image, ImageColor, ImageDraw

from art import ACCENT, ASSETS, BG, FG, GRID, MUTED, font, save_gif

WIDTH, HEIGHT, SCALE = 1280, 690, 2
GIF_NAME = "github-activity-full-wave-sage.gif"
PNG_NAME = "github-activity-full-wave-sage.png"


def summary(data):
    days = sorted((day for week in data["weeks"] for day in week["contributionDays"]),
                  key=lambda day: day["date"])
    if not days:
        raise ValueError("A calendar must contain at least one verified day")
    longest = streak = 0
    previous = None
    for day in days:
        current = date.fromisoformat(day["date"])
        consecutive = previous is not None and (current-previous).days == 1
        streak = (streak+1 if consecutive else 1) if day["contributionCount"] > 0 else 0
        longest = max(longest, streak)
        previous = current
    busiest = max(days, key=lambda day: day["contributionCount"])
    return {"total": sum(day["contributionCount"] for day in days),
            "busiest": busiest, "longest": longest, "current": streak,
            "first": days[0]["date"], "last": days[-1]["date"]}


def tone(color, multiplier):
    return tuple(round(channel*multiplier) for channel in ImageColor.getrgb(color))


def ease(value):
    value = max(0, min(1, value))
    return value*value*(3-2*value)


def surface_displacement(week, weekday, week_count, phase, strength):
    """A travelling wave deforms every floor tile and its attached pillar together."""
    position = week/max(1, week_count-1)
    angle = 2*math.pi*(1.4*position+weekday*0.035)-phase
    return 30*strength*math.sin(angle)


def render_frame(data, stats, lift=1, orbit=0, wave_phase=0, wave_strength=0):
    image = Image.new("RGB", (WIDTH*SCALE, HEIGHT*SCALE), BG)
    draw = ImageDraw.Draw(image)

    def xy(point):
        return tuple(round(v*SCALE) for v in point)

    def line(points, fill, width=1):
        draw.line([xy(point) for point in points], fill=fill, width=width*SCALE)

    def text(x, y, value, size=20, color=FG, bold=False, mono=False, anchor=None):
        draw.text(xy((x, y)), str(value), fill=color,
                  font=font(size*SCALE, bold=bold, mono=mono), anchor=anchor)

    def polygon(points, fill):
        draw.polygon([xy(point) for point in points], fill=fill)

    draw.rounded_rectangle((1, 1, WIDTH*SCALE-2, HEIGHT*SCALE-2),
                           radius=20*SCALE, outline="#314039", width=2*SCALE)
    text(36, 26, "MY CONTRIBUTION TERRAIN", 16, ACCENT, mono=True)
    text(34, 58, "Small steps. Another dimension.", 34, bold=True)
    text(1240, 32, "@"+data.get("username", "LakshmiHasini"), 18, MUTED, mono=True, anchor="rt")
    text(1240, 68, "REAL DAYS. REAL PROGRESS.", 13, MUTED, mono=True, anchor="rt")

    # Calendar heights remain measured from the moving surface, including empty days.
    p = ease(lift/0.3)
    rise = ease((lift-0.12)/0.88)
    wave_strength = max(0, min(1, wave_strength))
    ux = 21+(19-21)*p
    uy = (1.4+0.4*math.sin(orbit))*p
    vx = (-9+0.65*math.sin(orbit))*p
    vy = 21+(9+0.25*math.sin(orbit)-21)*p
    origin_x = 83+(110-83)*p
    origin_y = 186+(280-186)*p+8*wave_strength

    def project(week, weekday, height=0):
        surface = surface_displacement(week, weekday, len(data["weeks"]), wave_phase, wave_strength)
        return (origin_x+week*ux+weekday*vx, origin_y+week*uy+weekday*vy-height-surface)

    peak = max(1, stats["busiest"]["contributionCount"])
    blocks = []
    for week_index, week in enumerate(data["weeks"]):
        for day in week["contributionDays"]:
            blocks.append((week_index, day["weekday"], day["contributionCount"]))
    # Paint the farthest rows first so foreground pillars occlude them correctly.
    blocks.sort(key=lambda block: (block[0]*uy+block[1]*vy, block[0]))
    for week, weekday, value in blocks:
        size = 0.78
        level = 0 if value == 0 else min(4, 1+int(math.log2(value)))
        height = (4+value/peak*151)*rise if value else 0
        base = [project(week, weekday), project(week+size, weekday),
                project(week+size, weekday+size), project(week, weekday+size)]
        top = [(x, y-height) for x, y in base]
        color = GRID[level]
        if height > 0:
            polygon([base[1], base[2], top[2], top[1]], tone(color, 0.48))
            polygon([base[2], base[3], top[3], top[2]], tone(color, 0.70))
        polygon(top, color)
        if value and p > 0:
            line([top[0], top[1], top[2]], tone(color, 1), 1)

    last_month = None
    for column, week in enumerate(data["weeks"]):
        dates = [date.fromisoformat(day["date"]) for day in week["contributionDays"]]
        month = next((day for day in dates if day.day <= 7), dates[0] if column == 0 and dates else None)
        if month and month.month != last_month:
            x, y = project(column, 7.6)
            text(x, y+12, month.strftime("%b"), 15, MUTED)
            last_month = month.month
    # The weekday labels follow the sheet as a group so they never bunch together.
    label_surface = surface_displacement(-1.5, 3, len(data["weeks"]), wave_phase, wave_strength)
    for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        x = origin_x-1.5*ux+row*vx
        y = origin_y-1.5*uy+row*vy-label_surface
        text(x-7, y+3, label, 14, MUTED, anchor="rt")

    # Summary values remain fixed throughout the animation.
    text(36, 503, f"{stats['first']} — {stats['last']}", 14, MUTED, mono=True)
    text(1030, 502, "Less", 14, MUTED)
    for index, color in enumerate(GRID):
        x = 1074+index*22
        draw.rounded_rectangle((*xy((x, 504)), *xy((x+15, 519))), radius=3*SCALE, fill=color)
    text(1192, 502, "More", 14, MUTED)
    line([(36, 541), (1244, 541)], "#314039")
    busiest_date = date.fromisoformat(stats["busiest"]["date"]).strftime("%d %b")
    metrics = [
        (f"{stats['total']:,}", "contributions", "PAST YEAR"),
        (str(stats["busiest"]["contributionCount"]), f"contributions · {busiest_date}", "BUSIEST DAY"),
        (f"{stats['longest']} {'day' if stats['longest'] == 1 else 'days'}", "consecutive active days", "LONGEST STREAK"),
        (f"{stats['current']} {'day' if stats['current'] == 1 else 'days'}", "ending on latest calendar day", "CURRENT STREAK"),
    ]
    for index, (value, caption, label) in enumerate(metrics):
        x = 38+index*307
        text(x, 562, label, 13, MUTED, mono=True)
        text(x-1, 584, value, 34, ACCENT, bold=True)
        text(x, 628, caption, 14, MUTED)
    verified = datetime.fromisoformat(data["verifiedAt"]).strftime("%d %b %Y")
    text(1240, 668, "Verified "+verified, 12, MUTED, mono=True, anchor="rt")
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def render_activity(data):
    stats = summary(data)
    if stats["total"] != data["totalContributions"]:
        raise ValueError("Calendar total does not match the supplied daily counts")
    still = render_frame(data, stats)
    still.save(ASSETS / PNG_NAME, optimize=True)
    flat = render_frame(data, stats, lift=0)
    frames = [flat]*8
    tick = 0
    for index in range(1, 37):
        tick += 1
        lift = index/36
        frames.append(render_frame(data, stats, lift=lift,
                                   wave_phase=tick/32*2*math.pi, wave_strength=ease(lift)))
    for index in range(1, 61):
        tick += 1
        frames.append(render_frame(data, stats, orbit=index/60*2*math.pi,
                                   wave_phase=tick/32*2*math.pi, wave_strength=1))
    for index in range(1, 25):
        tick += 1
        lift = 1-index/24
        frames.append(render_frame(data, stats, lift=lift,
                                   wave_phase=tick/32*2*math.pi, wave_strength=ease(lift)))
    frames.append(flat)
    save_gif(frames, ASSETS / GIF_NAME, duration=80, hold=1000, palette_source=still)

