"""Render a real contribution calendar lifting into a three-dimensional terrain."""
from datetime import date, datetime
import math

from PIL import Image, ImageColor, ImageDraw

from art import ACCENT, ASSETS, BG, FG, GRID, MUTED, font, save_gif

WIDTH, HEIGHT, SCALE = 1280, 660, 2
GIF_NAME = "github-activity-3d-wave-sage.gif"
PNG_NAME = "github-activity-3d-sage.png"


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


def wave_reveal(progress, week, weekday, week_count):
    """Sweep diagonally across the calendar, then settle at the exact data height."""
    position = (week+weekday*0.22)/max(1, week_count-1+6*0.22)
    local = (progress-position*0.56)/0.44
    if local <= 0:
        return 0
    if local >= 1:
        return 1
    # A soft overshoot gives the moving front a wave crest without changing the data.
    return 1-(1-local)**3*math.cos(1.5*math.pi*local)


def render_frame(data, stats, lift=1, orbit=0):
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

    # Both projections preserve weekday order; only the camera and height reveal change.
    p = ease(lift/0.3)
    wave_progress = max(0, min(1, (lift-0.18)/0.82))
    ux = 21+(19-21)*p
    uy = (1.4+0.4*math.sin(orbit))*p
    vx = (-9+0.65*math.sin(orbit))*p
    vy = 21+(9+0.25*math.sin(orbit)-21)*p
    origin_x = 83+(110-83)*p
    origin_y = 186+(280-186)*p

    def project(week, weekday, height=0):
        return (origin_x+week*ux+weekday*vx, origin_y+week*uy+weekday*vy-height)

    peak = max(1, stats["busiest"]["contributionCount"])
    blocks = []
    for week_index, week in enumerate(data["weeks"]):
        for day in week["contributionDays"]:
            blocks.append((week_index, day["weekday"], day["contributionCount"]))
    # Paint the farthest rows first so foreground pillars occlude them correctly.
    blocks.sort(key=lambda block: (project(block[0], block[1])[1], block[0]))
    for week, weekday, value in blocks:
        size = 0.78
        level = 0 if value == 0 else min(4, 1+int(math.log2(value)))
        reveal = wave_reveal(wave_progress, week, weekday, len(data["weeks"]))
        height = (4+value/peak*151)*reveal if value else 0
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
    for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        x, y = project(-1.5, row)
        text(x-7, y+3, label, 14, MUTED, anchor="rt")

    # Summary values remain fixed throughout the animation.
    text(36, 473, f"{stats['first']} — {stats['last']}", 14, MUTED, mono=True)
    text(1030, 472, "Less", 14, MUTED)
    for index, color in enumerate(GRID):
        x = 1074+index*22
        draw.rounded_rectangle((*xy((x, 474)), *xy((x+15, 489))), radius=3*SCALE, fill=color)
    text(1192, 472, "More", 14, MUTED)
    line([(36, 511), (1244, 511)], "#314039")
    busiest_date = date.fromisoformat(stats["busiest"]["date"]).strftime("%d %b")
    metrics = [
        (f"{stats['total']:,}", "contributions", "PAST YEAR"),
        (str(stats["busiest"]["contributionCount"]), f"contributions · {busiest_date}", "BUSIEST DAY"),
        (f"{stats['longest']} {'day' if stats['longest'] == 1 else 'days'}", "consecutive active days", "LONGEST STREAK"),
        (f"{stats['current']} {'day' if stats['current'] == 1 else 'days'}", "ending on latest calendar day", "CURRENT STREAK"),
    ]
    for index, (value, caption, label) in enumerate(metrics):
        x = 38+index*307
        text(x, 532, label, 13, MUTED, mono=True)
        text(x-1, 554, value, 34, ACCENT, bold=True)
        text(x, 598, caption, 14, MUTED)
    verified = datetime.fromisoformat(data["verifiedAt"]).strftime("%d %b %Y")
    text(1240, 638, "Verified "+verified, 12, MUTED, mono=True, anchor="rt")
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def render_activity(data):
    stats = summary(data)
    if stats["total"] != data["totalContributions"]:
        raise ValueError("Calendar total does not match the supplied daily counts")
    still = render_frame(data, stats)
    still.save(ASSETS / PNG_NAME, optimize=True)
    flat = render_frame(data, stats, lift=0)
    frames = [flat]*8
    frames += [render_frame(data, stats, lift=index/48) for index in range(1, 49)]
    frames += [render_frame(data, stats, orbit=index/24*2*math.pi) for index in range(1, 25)]
    frames += [still]*45
    frames += [render_frame(data, stats, lift=1-index/28) for index in range(1, 29)]
    frames.append(flat)
    save_gif(frames, ASSETS / GIF_NAME, duration=70, hold=1000, palette_source=still)

