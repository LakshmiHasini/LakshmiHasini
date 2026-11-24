# Maintaining this profile

The profile itself is `README.md`. All its images are committed to `assets/`; visitors do not depend on a third-party stats-card service.

The generated image names include `-sage` so the restored palette uses different URLs from the earlier violet images. Keep the README links and generator filenames in sync when changing themes, since GitHub and browsers can cache images at an unchanged URL.

## Practice chart updates

`.github/workflows/refresh-leetcode-matrix.yml` checks the chart's two public sources every 15 minutes and commits updated assets when the data changes. It also supports **Actions → Refresh LeetCode chart → Run workflow**. The workflow must be on the default branch with Actions enabled. GitHub can delay scheduled runs and cache profile images, so this is a periodic refresh.

The amber LED chart uses [LeetCode's public profile totals](https://leetcode.com/u/Lakshmihasini_13/) for unique solves by difficulty. The GitHub row separately counts C solution files and shows examples from the [HackerRank repository](https://github.com/LakshmiHasini/HackerRank). Change the sources in `profile.json`. The card dates refer to when the snapshot last changed. A failed request preserves previously verified data for that source.

Run `python scripts/build_leetcode_matrix.py --refresh` to check both sources locally. Run it without `--refresh` to rebuild the GIF and PNG from `data/leetcode-matrix.json` without a network request. The workflow uses GitHub's built-in token to save its generated changes.

## Original practice cards and contribution chart

GitHub uses the actual contribution calendar, including its actual dates and counts. A travelling wave bends the entire 3D calendar surface, including empty tiles, and the pillars move with their bases. Column heights are measured from that moving surface and reflect daily counts. Headings and summary numbers stay fixed while the complete grid ripples. The PNG is a still of the settled 3D view. LeetCode uses the public profile's unique accepted-question totals. HackerRank's public submission history counts attempts rather than distinct solved questions, so the card explicitly says **submissions**. Hackos points are not used as a solved-question count.

The 3D chart is rendered by `scripts/activity_chart.py`. Its summary shows the total contributions, busiest day, longest consecutive streak, and streak ending on the latest day present in the calendar. Zero-contribution or missing days break a streak. To update only this chart, run `python scripts/refresh_profile.py --github-only`. The README plays a GIF, so the 3D camera movement is pre-rendered rather than controlled by the viewer.

Each provider has its own verification timestamp in `data/profile-stats.json`. A failed request preserves that provider's previous verified numbers and date. The legacy refresh script reports an incomplete refresh so it can be rerun.

## Editorial portrait

The README displays an editorial portrait adapted from the supplied Elias React component, with warm paper, orange display lettering, a portrait arch, a SevaRecover project book, and a self-writing note.

GitHub READMEs cannot run React, pointer effects, or JavaScript. The entrance, gently moving book, and typed note are pre-rendered into `assets/editorial-hero.gif`. Readers who prefer reduced motion receive `assets/editorial-hero.png`. The image links to the portfolio.

Regenerate the hero after changing `assets/portrait.png` or the content in `scripts/build_editorial_hero.py`:

```sh
python scripts/build_editorial_hero.py
```

This uses the repository's existing Pillow dependency.

## Math Scramble

The second panel adapts the supplied Math Scramble component by Louis Studios to display the full bio. A timed wave turns the letters into colored math symbols and back while the highlighted text stays steady. The GIF plays automatically, and the PNG shows the settled bio for readers who prefer reduced motion.

Edit `BIO` in `scripts/build_math_scramble.py` and run `python scripts/build_math_scramble.py` to regenerate both images. Update the alternative text in `README.md` if the words change.

## Project reel

The project reel adapts the supplied Tilted Grid Hero. Screenshots bend around a curved track and pass through the center. A still grid shows all four screenshots for readers who prefer reduced motion.

The images in `assets/project-screenshots/` are captures of [SevaRecover](https://frontend-pink-two-8nh56blhuw.vercel.app/), [Recall](https://recall-incident-memory.lakshmihasini8.chatgpt.site/landing/), [ChainMatrix](https://chain-matrix.vercel.app/), and [JobFit Lab's local demo overview](https://github.com/LakshmiHasini/JobFit-Lab) from commit `6725088`. To change a screenshot, replace its source image and run `python scripts/build_project_reel.py` to rebuild the GIF and PNG. Edit `PROJECTS` in that script and the alternative text in `README.md` when changing the project list.

## GitHub activity card

The card uses the dates, counts, and intensity levels from GitHub's public contribution calendar. The initials in the card represent repositories with the most public push events in the available event response. The card links to GitHub for the live calendar.

Run `python scripts/build_github_activity_card.py` to rebuild the GIF and still PNG from `data/github-activity-card.json`. Add `--refresh` to fetch a new snapshot using `curl`. After refreshing, use the snapshot to update the calendar's alternative text.

## Crowd footer

The closing banner adapts [Skiper UI's Canvas Crowd](https://skiper-ui.com/v1/skiper39) and uses the supplied sprite sheet of [Open Peeps illustrations](https://www.openpeeps.com/). It renders looping layers of walking characters and a still fallback with the same message.

Run `python scripts/build_crowd_footer.py` to regenerate both images from `assets/crowd-sprites.png`. Edit the closing message in the script and its alternative text in `README.md`. The banner's LinkedIn link is edited directly in the README.

## Original dither banner

The original dither banner uses the GitHub profile photo downloaded from `https://avatars.githubusercontent.com/u/229450114?v=4`. It applies the 8×8 Bayer matrix from the previously supplied React component. A moving band changes the pixel size before the image settles.

Replace `assets/portrait.png` with another photograph, then regenerate:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build_banner.py
```

You can also pass a photo path to `python scripts/build_banner.py path/to/photo.jpg`. The script changes the banner only; it does not overwrite the source photograph. No additional React app or npm installation is required.

## Change handles or refresh locally

Edit `profile.json` to change the platform handles. To refresh, use an authenticated `gh` CLI or set a GitHub token in `GH_TOKEN` in your environment:

```sh
python scripts/refresh_profile.py
```

To regenerate images from the last verified snapshot without network requests:

```sh
python scripts/refresh_profile.py --render-only
```

The scripts look for common system fonts on Linux, macOS, and Windows and fall back to Pillow's default font. Slight typography differences between operating systems are expected.

## Edit the content

Update `README.md` to change the portfolio link or alternative text. Edit `scripts/build_editorial_hero.py` to change the words shown inside the editorial portrait.

The five section headings use the supplied Stroke Draw Type effect. Each heading remains an HTML `h2` with alternative text and a section anchor. To change a title, edit `HEADINGS` in `scripts/build_stroke_headings.py` and the heading image's alternative text in `README.md`. Install `fonttools` in the same environment as Pillow and run `python scripts/build_stroke_headings.py` to regenerate the GIFs and still PNGs.

The toolkit scrolls across five full-width ribbons, one per category. Green ribbons move left and purple ribbons move right. To change the skills, edit `TOOLKIT` in `scripts/build_toolkit_marquee.py`, then run `python scripts/build_toolkit_marquee.py` to regenerate the GIF and still PNG. Update the alternative text in `README.md` to match.

The initial bio, education, skills, and project summaries came from your public GitHub profile, public project READMEs, and the source of [your portfolio](https://github.com/LakshmiHasini/portfolio-website). Project links preserve team attribution where applicable. Review the bio whenever your internship availability or education changes.

