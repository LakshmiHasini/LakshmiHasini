"""Refresh public coding activity; keep the last verified snapshot on API failures.

Run with GH_TOKEN in the environment, or an authenticated gh CLI locally.
Only calendar counts and explicitly selected public statistics are saved.
"""
import argparse
from datetime import date, datetime, timezone
from html import escape
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

from PIL import Image, ImageDraw

from art import ACCENT, ASSETS, BG, FG, MUTED, ROOT, font
from activity_chart import GIF_NAME, PNG_NAME, render_activity

DATA_PATH = ROOT / "data" / "profile-stats.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PersonalProfileReadme/1.0)", "Accept": "application/json"}
GITHUB_QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date weekday } }
      }
    }
  }
}"""
LEETCODE_QUERY = """query($username: String!) {
  matchedUser(username: $username) {
    username
    submitStatsGlobal { acSubmissionNum { difficulty count } }
  }
}"""


def request_json(url, payload=None, headers=None):
    body = None if payload is None else json.dumps(payload).encode()
    merged = {**HEADERS, **(headers or {})}
    if body is not None:
        merged["Content-Type"] = "application/json"
    for attempt in range(3):
        req = urllib.request.Request(url, data=body, headers=merged)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.load(response)
            if isinstance(result, dict) and result.get("errors"):
                raise ValueError("The service returned GraphQL errors")
            return result
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def count(value):
    if type(value) is not int or value < 0:
        raise ValueError("Expected a non-negative integer statistic")
    return value


def fetch_github(username):
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        payload = {"query": GITHUB_QUERY, "variables": {"login": username}}
        response = request_json("https://api.github.com/graphql", payload,
                                {"Authorization": f"Bearer {token}"})
    else:
        # The token stays in gh's credential store and never enters command arguments.
        result = subprocess.run(["gh", "api", "graphql", "-f", f"query={GITHUB_QUERY}",
                                 "-f", f"login={username}"], capture_output=True, text=True, check=True)
        response = json.loads(result.stdout)
    calendar = response["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = []
    seen = set()
    for week in calendar["weeks"]:
        days = []
        for day in week["contributionDays"]:
            day_date = date.fromisoformat(day["date"]).isoformat()
            weekday = count(day["weekday"])
            if weekday > 6 or day_date in seen:
                raise ValueError("Invalid or repeated calendar day")
            seen.add(day_date)
            days.append({"date": day_date, "weekday": weekday,
                         "contributionCount": count(day["contributionCount"])})
        weeks.append({"contributionDays": days})
    total = count(calendar["totalContributions"])
    if not seen or sum(d["contributionCount"] for w in weeks for d in w["contributionDays"]) != total:
        raise ValueError("Incomplete contribution calendar")
    return {"totalContributions": total, "weeks": weeks}


def fetch_leetcode(username):
    data = request_json("https://leetcode.com/graphql/",
                        {"query": LEETCODE_QUERY, "variables": {"username": username}},
                        {"Referer": f"https://leetcode.com/u/{username}/"})
    user = data["data"]["matchedUser"]
    if not user or user["username"].lower() != username.lower():
        raise ValueError("LeetCode profile could not be verified")
    counts = {row["difficulty"]: count(row["count"])
              for row in user["submitStatsGlobal"]["acSubmissionNum"]}
    if not all(key in counts for key in ("All", "Easy", "Medium", "Hard")):
        raise ValueError("Incomplete LeetCode difficulty totals")
    if sum(counts[key] for key in ("Easy", "Medium", "Hard")) != counts["All"]:
        raise ValueError("LeetCode difficulty totals do not match")
    return {"solved": counts}


def fetch_hackerrank(username):
    base = f"https://www.hackerrank.com/rest/hackers/{username}"
    profile = request_json(f"https://www.hackerrank.com/rest/contests/master/hackers/{username}/profile")["model"]
    if profile.get("username", "").lower() != username.lower():
        raise ValueError("HackerRank profile could not be verified")
    history = request_json(base + "/submission_histories")
    if not isinstance(history, dict) or any(key in history for key in ("error", "errors", "status")):
        raise ValueError("HackerRank did not return a submission calendar")
    days = {date.fromisoformat(day).isoformat(): count(value) for day, value in history.items()}
    return {"submissions": sum(days.values()), "activeDays": sum(value > 0 for value in days.values()),
            "lastSubmission": max((d for d, value in days.items() if value > 0), default=None)}


def verified_label(data):
    return "Verified " + datetime.fromisoformat(data["verifiedAt"]).strftime("%d %b %Y")


def draw_activity(data):
    render_activity(data)


def svg_text(x, y, text, size=17, fill=FG, weight="400", anchor="start", mono=False):
    family = "ui-monospace,Consolas,monospace" if mono else "-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(str(text))}</text>')


def card(title, username, metric, caption, detail, verified, icon):
    title_xml = escape(f"{title} — {username}: {metric} {caption}")
    return "\n".join([
        '<svg xmlns="http://www.w3.org/2000/svg" width="620" height="286" viewBox="0 0 620 286" role="img">',
        f'<title>{title_xml}</title>',
        f'<rect x="1" y="1" width="618" height="284" rx="20" fill="{BG}" stroke="#314039" stroke-width="2"/>',
        f'<rect x="30" y="28" width="38" height="38" rx="10" fill="#22392b"/>',
        svg_text(49, 54, icon, 23, ACCENT, "700", "middle", True),
        svg_text(82, 54, title, 24, weight="600"),
        svg_text(30, 98, username, 16, MUTED, mono=True),
        svg_text(28, 165, metric, 58, ACCENT, "700"),
        svg_text(30, 195, caption, 18),
        '<path d="M30 216H590" stroke="#314039"/>',
        svg_text(30, 246, detail, 17, MUTED),
        svg_text(590, 269, verified, 12, MUTED, anchor="end"),
        '</svg>',
    ]) + "\n"


def draw_cards(state, config):
    if "leetcode" in state:
        d = state["leetcode"]
        c = d["solved"]
        detail = f"Easy {c['Easy']}   ·   Medium {c['Medium']}   ·   Hard {c['Hard']}"
        svg = card("LeetCode", config["leetcode"], c["All"], "unique questions solved", detail, verified_label(d), "<>")
        (ASSETS / "leetcode-sage.svg").write_text(svg)
    if "hackerrank" in state:
        d = state["hackerrank"]
        active = f"{d['activeDays']} active practice days"
        svg = card("HackerRank", config["hackerrank"], d["submissions"], "submissions across my practice history",
                   active, verified_label(d), "H")
        (ASSETS / "hackerrank-sage.svg").write_text(svg)
    for platform, title, icon in [("leetcode", "LeetCode", "<>"), ("hackerrank", "HackerRank", "H")]:
        if platform not in state:
            svg = card(title, config[platform], "—", "Statistics temporarily unavailable",
                       "Open my profile for current activity", "Awaiting a verified refresh", icon)
            (ASSETS / f"{platform}-sage.svg").write_text(svg)


def draw_unavailable_activity():
    image = Image.new("RGB", (1280, 350), BG)
    draw = ImageDraw.Draw(image)
    draw.text((38, 55), "Activity temporarily unavailable", font=font(32, bold=True), fill=FG)
    draw.text((38, 125), "Open my GitHub profile for the current contribution calendar.", font=font(24), fill=MUTED)
    image.save(ASSETS / PNG_NAME)
    image.save(ASSETS / GIF_NAME)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-only", action="store_true", help="Render previously verified data without network requests")
    parser.add_argument("--github-only", action="store_true", help="Refresh and render the GitHub chart without changing coding-platform cards")
    args = parser.parse_args()
    config = json.loads((ROOT / "profile.json").read_text())
    state = json.loads(DATA_PATH.read_text()) if DATA_PATH.exists() else {}
    failures = []
    if not args.render_only:
        providers = [("github", fetch_github)]
        if not args.github_only:
            providers += [("leetcode", fetch_leetcode), ("hackerrank", fetch_hackerrank)]
        for platform, fetch in providers:
            username = config[platform]
            # A changed handle must never display the previous person's cached statistics.
            if state.get(platform, {}).get("username") not in (None, username):
                state.pop(platform, None)
            try:
                value = fetch(username)
                state[platform] = {**value, "username": username,
                                   "verifiedAt": datetime.now(timezone.utc).isoformat(timespec="seconds")}
                print(f"Verified {platform} statistics for {username}.")
            except Exception as error:
                # Avoid logging request objects or authorization headers.
                failures.append(platform)
                print(f"::warning::{platform} refresh failed ({type(error).__name__}); retaining any last verified data.", file=sys.stderr)
        DATA_PATH.parent.mkdir(exist_ok=True)
        temporary = DATA_PATH.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, indent=2) + "\n")
        temporary.replace(DATA_PATH)
    ASSETS.mkdir(exist_ok=True)
    if "github" in state:
        draw_activity(state["github"])
    else:
        draw_unavailable_activity()
    if not args.github_only:
        draw_cards(state, config)
    required = ("github",) if args.github_only else ("github", "leetcode", "hackerrank")
    missing = [key for key in required if key not in state]
    if missing or failures:
        print("Refresh incomplete: " + ", ".join(sorted(set(missing + failures))), file=sys.stderr)
        return 1
    print("Rendered contribution animation and still image." if args.github_only else "Rendered contribution animation, still image, and both practice cards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

