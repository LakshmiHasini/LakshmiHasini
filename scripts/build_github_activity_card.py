"""Build the profile's flat contribution calendar from public GitHub data.

Run with --refresh to fetch a new snapshot. The default uses the saved snapshot.
"""

import argparse
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
import json
import re
import subprocess
from urllib.parse import quote

from PIL import Image, ImageColor, ImageDraw

from art import ASSETS, ROOT, font, save_gif


SNAPSHOT = ROOT / "data" / "github-activity-card.json"
WIDTH, HEIGHT = 1280, 429
BACKGROUND = "#0b0b0d"
TEXT = "#f3f9ed"
MUTED = "#c8d8c7"
LEVELS = ("#2a4132", "#5c794b", "#8aab5d", "#b4d876", "#dcf6a4")
MONOGRAMS = ("#accb8d", "#d4dab4", "#c6e98b")


class CalendarHTML(HTMLParser):
    """Read the dates, intensity levels, and matching day tooltips GitHub publishes."""

    def __init__(self):
        super().__init__()
        self.cells = {}
        self.counts = {}
        self.tooltip = None
        self.content = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and {"id", "data-date", "data-level"} <= attrs.keys():
            self.cells[attrs["id"]] = (attrs["data-date"], int(attrs["data-level"]))
        if tag == "tool-tip" and attrs.get("for") in self.cells:
            self.tooltip = attrs["for"]
            self.content = []

    def handle_data(self, text):
        if self.tooltip is not None:
            self.content.append(text)

    def handle_endtag(self, tag):
        if tag != "tool-tip" or self.tooltip is None:
            return
        label = "".join(self.content).strip()
        match = re.match(r"(No|[\d,]+) contributions? on ", label)
        if match:
            count = match[1]
            self.counts[self.tooltip] = 0 if count == "No" else int(count.replace(",", ""))
        self.tooltip = None


def get_public(url):
    return subprocess.check_output(["curl", "--fail", "--silent", "--show-error",
                                    "--max-time", "20", url], encoding="utf-8")


def refresh(username):
    login = quote(username, safe="")
    calendar = get_public(f"https://github.com/users/{login}/contributions")
    parser = CalendarHTML()
    parser.feed(calendar)
    if parser.cells.keys() != parser.counts.keys():
        raise ValueError("GitHub did not provide a count for every calendar cell")
    days = sorted((day, parser.counts[key], level) for key, (day, level) in parser.cells.items())
    total = sum(count for _, count, _ in days)
    heading = re.search(r"([\d,]+)\s+contributions?\s+in the last year", calendar)
    if not days or not heading or total != int(heading[1].replace(",", "")):
        raise ValueError("Daily counts did not match the GitHub calendar total")
    if any(not 0 <= level < len(LEVELS) for _, _, level in days):
        raise ValueError("GitHub returned an unknown activity level")
    if any(date.fromisoformat(b[0]) - date.fromisoformat(a[0]) != timedelta(days=1)
           for a, b in zip(days, days[1:])):
        raise ValueError("GitHub returned a calendar with missing or duplicate dates")

    events = json.loads(get_public(f"https://api.github.com/users/{login}/events/public?per_page=100"))
    pushes = Counter(event["repo"]["name"] for event in events if event["type"] == "PushEvent")
    event_dates = sorted(event["created_at"][:10] for event in events)
    return {
        "username": username,
        "verifiedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total": total,
        "days": days,
        "eventWindow": [event_dates[0], event_dates[-1]] if event_dates else [],
        "recentPushes": [{"repository": repo, "pushEvents": count} for repo, count in pushes.most_common(3)],
    }


def save_snapshot(snapshot):
    # One line per date makes data updates easy to review.
    header = {key: value for key, value in snapshot.items() if key != "days"}
    prefix = json.dumps(header, indent=2).removesuffix("\n}")
    days = ",\n".join("    " + json.dumps(day) for day in snapshot["days"])
    temporary = SNAPSHOT.with_suffix(".tmp")
    temporary.write_text(prefix + ',\n  "days": [\n' + days + "\n  ]\n}\n")
    temporary.replace(SNAPSHOT)


def display_date(iso):
    day = date.fromisoformat(iso)
    return f"{day:%b} {day.day}, {day.year}"


def blend(a, b, amount):
    return tuple(round(x + (y - x) * amount) for x, y in zip(a, b))


def card_surface():
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    start, end = map(ImageColor.getrgb, ("#344c39", "#13231b"))
    gradient = Image.new("RGB", (64, 32))
    gradient.putdata([blend(start, end, (x / 63 + y / 31) / 2)
                      for y in range(32) for x in range(64)])
    size = (WIDTH - 28, HEIGHT - 28)
    mask = Image.new("L", size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=40, fill=255)
    image.paste(gradient.resize(size, Image.Resampling.BICUBIC), (14, 14), mask)
    return image


def prepare(snapshot):
    days = snapshot["days"]
    first, last = (date.fromisoformat(days[i][0]) for i in (0, -1))
    sunday = first - timedelta(days=(first.weekday() + 1) % 7)
    columns = (last - sunday).days // 7 + 1
    x0, y0 = 100, 176
    pitch = (WIDTH - 48 - x0) / columns
    tile = int(pitch) - 4
    row_pitch = 23

    base = card_surface()
    draw = ImageDraw.Draw(base)
    draw.text((44, 42), "GITHUB ACTIVITY", font=font(17, mono=True), fill="#cfe5bc", anchor="lt")
    noun = "contribution" if snapshot["total"] == 1 else "contributions"
    draw.text((42, 75), f'{snapshot["total"]:,} {noun}', font=font(47, bold=True), fill=TEXT, anchor="lt")
    draw.text((WIDTH - 47, 45), "@" + snapshot["username"], font=font(21, bold=True), fill=TEXT, anchor="rt")
    dates = f"{display_date(days[0][0])} – {display_date(days[-1][0])}"
    draw.text((WIDTH - 47, 83), dates, font=font(16, mono=True), fill=MUTED, anchor="rt")
    draw.line((44, 132, WIDTH - 45, 132), fill="#4b5d49", width=1)

    months = defaultdict(list)
    tiles = []
    for day, _, level in days:
        current = date.fromisoformat(day)
        week, weekday = divmod((current - sunday).days, 7)
        months[(current.year, current.month)].append(week)
        x, y = round(x0 + week * pitch), y0 + weekday * row_pitch
        tiles.append((week, (x, y, x + tile - 1, y + tile - 1), level))
    for (year, month), weeks in months.items():
        if max(weeks) - min(weeks) >= 2:
            x = round(x0 + min(weeks) * pitch)
            draw.text((x, 150), date(year, month, 1).strftime("%b"), font=font(14), fill=MUTED, anchor="lt")
    for weekday, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        draw.text((88, y0 + weekday * row_pitch + tile / 2), label, font=font(15), fill=MUTED, anchor="rm")

    draw.rounded_rectangle((37, 351, WIDTH - 37, 396), radius=17, fill="#16271c", outline="#52674c")
    repo_label = "Recent public pushes" if snapshot["recentPushes"] else "Public contribution calendar"
    draw.text((54, 373), repo_label, font=font(18, bold=True), fill=TEXT, anchor="lm")
    for i, repo in reversed(list(enumerate(snapshot["recentPushes"]))):
        x = 259 + i * 26
        draw.ellipse((x - 15, 358, x + 15, 388), fill=MONOGRAMS[i], outline="#16271c", width=2)
        initial = repo["repository"].split("/", 1)[-1][:1].upper()
        draw.text((x, 373), initial, font=font(14, bold=True), fill="#18291d", anchor="mm")

    draw.text((1054, 373), "Less", font=font(15), fill=MUTED, anchor="rm")
    for index, color in enumerate(LEVELS):
        x = 1063 + index * 22
        draw.rounded_rectangle((x, 365, x + 15, 380), radius=4, fill=color)
    draw.text((1176, 373), "More", font=font(15), fill=MUTED, anchor="lm")
    return base, tiles, columns


def render(prepared, reveal):
    base, tiles, columns = prepared
    image = base.copy()
    draw = ImageDraw.Draw(image)
    palette = [ImageColor.getrgb(color) for color in LEVELS]
    for week, bounds, level in tiles:
        progress = max(0, min(1, (reveal - week / max(1, columns - 1) * 0.75) / 0.25))
        color = blend(palette[0], palette[level], 1 - (1 - progress) ** 3)
        draw.rounded_rectangle(bounds, radius=4, fill=color)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Fetch the public calendar and recent push events")
    args = parser.parse_args()
    if args.refresh:
        username = json.loads((ROOT / "profile.json").read_text())["github"]
        snapshot = refresh(username)
        save_snapshot(snapshot)
    else:
        snapshot = json.loads(SNAPSHOT.read_text())

    ASSETS.mkdir(exist_ok=True)
    prepared = prepare(snapshot)
    still = render(prepared, 1)
    still.save(ASSETS / "github-activity-card.png", optimize=True)
    frames = (render(prepared, step / 24) for step in range(25))
    save_gif(frames, ASSETS / "github-activity-card.gif", duration=70, hold=4000, palette_source=still)
    print(f'{snapshot["total"]} contributions through {snapshot["days"][-1][0]}')
    for repo in snapshot["recentPushes"]:
        print(f'{repo["repository"]}: {repo["pushEvents"]} public push events')


if __name__ == "__main__":
    main()
