"""Build the practice LED chart and refresh its public data when requested."""

import argparse
from datetime import datetime, timezone
import json
import os
import re
from urllib.error import HTTPError
from urllib.parse import quote

from PIL import Image, ImageColor, ImageDraw

from art import ASSETS, ROOT, font, save_gif
from refresh_profile import fetch_leetcode, request_json


SNAPSHOT = ROOT / "data" / "leetcode-matrix.json"
STILL_NAME, GIF_NAME = "leetcode-matrix.png", "leetcode-matrix.gif"
WIDTH, HEIGHT = 1280, 556
ROWS, DOT_COLUMNS = 9, 13
DIFFICULTIES = ("Easy", "Medium", "Hard")
HIGHLIGHT = ("#ffc45b", "#ffac62", "#ff8664")
PAPER = "#f7ead8"
MUTED = "#d4bb9b"
AMBER = "#ffb547"
OFF = "#493424"
EXAMPLE_FILES = (
    ("Sum-of-two-numbers.c", "Sum of two numbers"),
    ("If-Else_Leap Year.c", "Leap Year"),
    ("Swap Two Numbers.c", "Swap Two Numbers"),
)


def fetch_practice(repository):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Expected an owner/repository GitHub path")
    token = os.environ.get("GH_TOKEN")
    url = f"https://api.github.com/repos/{quote(repository)}/git/trees/HEAD?recursive=1"
    try:
        tree = request_json(url, headers={"Authorization": f"Bearer {token}"} if token else None)
    except HTTPError as error:
        # The workflow token may be scoped to the profile repository only.
        if not token or error.code not in (401, 403, 404):
            raise
        tree = request_json(url)
    if tree.get("truncated") is not False:
        raise ValueError("GitHub returned an incomplete repository tree")
    files = {entry["path"] for entry in tree["tree"]
             if entry["type"] == "blob" and entry["path"].lower().endswith(".c")}
    examples = [{"path": path, "title": title} for path, title in EXAMPLE_FILES if path in files]
    return {"solutionFiles": len(files), "examples": examples}


def refresh(previous):
    config = json.loads((ROOT / "profile.json").read_text())
    sources = (
        ("leetcode", "username", config["leetcode"], fetch_leetcode),
        ("github", "repository", config["github_practice_repo"], fetch_practice),
    )
    today = datetime.now(timezone.utc).date().isoformat()
    updated = {}
    successes = 0
    for key, identity_key, identity, fetch in sources:
        cached = previous.get(key, {})
        try:
            value = {identity_key: identity, **fetch(identity)}
        except (ValueError, OSError, KeyError, TypeError) as error:
            if cached.get(identity_key) != identity:
                raise RuntimeError(f"No verified {key} data for {identity}") from error
            print(f"::warning::{key} refresh failed ({type(error).__name__}); keeping the previous snapshot.")
            updated[key] = cached
        else:
            successes += 1
            # A successful check with unchanged data does not create a bot commit.
            saved_value = {k: v for k, v in cached.items() if k != "updatedOn"}
            updated[key] = cached if value == saved_value else {**value, "updatedOn": today}
    if not successes:
        raise RuntimeError("Neither public practice source could be refreshed")
    return updated


def chart_levels(counts):
    peak = max(counts, default=0)
    return [max(1, round(count / peak * ROWS)) if count else 0 for count in counts]


def surface():
    image = Image.new("RGB", (WIDTH, HEIGHT), "#0c0907")
    colors = [ImageColor.getrgb(value) for value in ("#18110c", "#4a2e18")]
    wash = Image.new("RGB", (64, 32))
    wash.putdata([
        tuple(round(a + (b - a) * min(1, (x / 63) ** 2 * (1 - y / 31) ** 2))
              for a, b in zip(*colors))
        for y in range(32) for x in range(64)
    ])
    size = (WIDTH - 24, HEIGHT - 24)
    mask = Image.new("L", size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=34, fill=255)
    image.paste(wash.resize(size, Image.Resampling.BICUBIC), (12, 12), mask)
    return image


def prepare(state):
    leetcode, github = state["leetcode"], state["github"]
    base = surface()
    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle((46, 42, 104, 100), radius=15, fill=AMBER)
    for i, icon_height in enumerate((11, 22, 33)):
        x = 61 + i * 9
        draw.rounded_rectangle((x, 88 - icon_height, x + 5, 88), radius=2, fill="#3a2212")
    draw.text((122, 47), "LeetCode progress", font=font(31, bold=True), fill=PAPER, anchor="lt")
    draw.text((124, 86), "@" + leetcode["username"], font=font(19, mono=True), fill=MUTED, anchor="lt")
    draw.text((WIDTH - 48, 104), "UNIQUE PROBLEMS SOLVED", font=font(17, mono=True), fill=MUTED, anchor="rt")
    draw.line((45, 133, WIDTH - 45, 133), fill="#604329", width=1)

    counts = [leetcode["solved"][name] for name in DIFFICULTIES]
    levels = chart_levels(counts)
    columns = []
    for index, (name, count, level, lit) in enumerate(zip(DIFFICULTIES, counts, levels, HIGHLIGHT)):
        left = 70 + 402 * index
        for col in range(DOT_COLUMNS):
            columns.append((left + col * 27, level, lit))
        draw.text((left, 377), name, font=font(25, bold=True), fill=PAPER, anchor="lt")
        draw.text((left + 324, 377), str(count), font=font(25, mono=True), fill=lit, anchor="rt")
    draw.line((45, 419, WIDTH - 45, 419), fill="#604329", width=1)

    draw.text((47, 441), "GITHUB PRACTICE", font=font(17, mono=True), fill=AMBER, anchor="lt")
    examples = "  ·  ".join(row["title"] for row in github["examples"])
    draw.text((47, 477), examples or github["repository"], font=font(21), fill=PAPER, anchor="lt")
    draw.text((WIDTH - 48, 445), f'{github["solutionFiles"]:,} C solution files', font=font(24, bold=True),
              fill=PAPER, anchor="rt")
    stamp = datetime.fromisoformat(leetcode["updatedOn"]).strftime("%d %b %Y").upper()
    draw.text((WIDTH - 48, 485), "LEETCODE SNAPSHOT  " + stamp, font=font(14, mono=True), fill=MUTED, anchor="rt")
    return base, columns, leetcode["solved"]["All"]


def render(prepared, progress):
    base, columns, total = prepared
    image = base.copy()
    draw = ImageDraw.Draw(image)
    draw.text((WIDTH - 45, 37), f"{round(total * progress):,}", font=font(64, mono=True), fill=PAPER, anchor="rt")
    for index, (x, level, color) in enumerate(columns):
        fill_level = min(level, max(0, round((progress * (len(columns) + ROWS) - index) * 1.4)))
        for row in range(ROWS):
            y = 347 - row * 22
            fill = OFF if row >= fill_level else color
            if fill_level and row == fill_level - 1 and fill_level == level:
                fill = "#ffe9b7"
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=fill)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Check LeetCode and GitHub for current public stats")
    args = parser.parse_args()
    saved = json.loads(SNAPSHOT.read_text()) if SNAPSHOT.exists() else {}
    state = refresh(saved) if args.refresh else saved
    if not state:
        parser.error("No cached snapshot. Run with --refresh first.")
    if args.refresh and state == saved and all((ASSETS / name).is_file() for name in (STILL_NAME, GIF_NAME)):
        print("Practice stats unchanged. Keeping the current chart.")
        return

    ASSETS.mkdir(exist_ok=True)
    prepared = prepare(state)
    still = render(prepared, 1)
    still.save(ASSETS / STILL_NAME, optimize=True)
    frames = (render(prepared, i / 26) for i in range(27))
    save_gif(frames, ASSETS / GIF_NAME, duration=65, hold=4300, palette_source=still)

    if state != saved:
        temporary = SNAPSHOT.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, indent=2) + "\n")
        temporary.replace(SNAPSHOT)
    print(f'{state["leetcode"]["solved"]["All"]} unique LeetCode solves; '
          f'{state["github"]["solutionFiles"]} GitHub solution files.')


if __name__ == "__main__":
    main()
