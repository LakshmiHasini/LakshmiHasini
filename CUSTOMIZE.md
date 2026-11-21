# Maintaining this profile

The profile itself is `README.md`. All its images are committed to `assets/`; visitors do not depend on a third-party stats-card service.

The generated image names include `-sage` so the restored palette uses different URLs from the earlier violet images. Keep the README links and generator filenames in sync when changing themes, since GitHub and browsers can cache images at an unchanged URL.

## Daily updates

`.github/workflows/refresh-profile.yml` refreshes the GitHub calendar, LeetCode solved totals, and HackerRank submission activity every day around **06:17 IST**. It also supports **Actions → Refresh profile activity → Run workflow**. Scheduled runs can be delayed by GitHub and may be disabled after extended repository inactivity.

The workflow uses the automatically supplied `GITHUB_TOKEN`, with `contents: write` permission to commit generated images. No personal access token needs to be stored in the repository. The workflow must be present on the default `main` branch and Actions must be enabled for the schedule to run.

GitHub uses the actual contribution calendar, including its actual dates and counts. A travelling wave bends the entire 3D calendar surface, including empty tiles, and the pillars move with their bases. Column heights are measured from that moving surface and reflect daily counts. Headings and summary numbers stay fixed while the complete grid ripples. The PNG is a still of the settled 3D view. LeetCode uses the public profile's unique accepted-question totals. HackerRank's public submission history counts attempts rather than distinct solved questions, so the card explicitly says **submissions**. Hackos points are not used as a solved-question count.

The 3D chart is rendered by `scripts/activity_chart.py`. Its summary shows the total contributions, busiest day, longest consecutive streak, and streak ending on the latest day present in the calendar. Zero-contribution or missing days break a streak. To update only this chart, run `python scripts/refresh_profile.py --github-only`. The README plays a GIF, so the 3D camera movement is pre-rendered rather than controlled by the viewer.

Each provider has its own verification timestamp in `data/profile-stats.json`. A failed request preserves that provider's previous verified numbers and date; successful providers still update. The workflow reports the incomplete refresh so it can be rerun. Source websites can change their public endpoints, so their availability is not guaranteed. GitHub image caching may briefly delay the visible refresh.

## Change the portrait

The banner uses your current GitHub profile photo, downloaded from `https://avatars.githubusercontent.com/u/229450114?v=4`. It applies the 8×8 Bayer matrix from your supplied React component. A moving band changes the pixel size before the image settles. The GIF runs directly in a GitHub README; React and browser JavaScript cannot run inside the README.

Replace `assets/portrait.png` with another photograph, then regenerate:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build_banner.py
```

You can also pass a photo path to `python scripts/build_banner.py path/to/photo.jpg`. The script changes the banner only; it does not overwrite the source photograph. No additional React app or npm installation is required.

The README selects still PNGs for readers who prefer reduced motion and includes an expandable still version of the activity chart.

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

Update `README.md` directly for your bio, education, skills, projects, and links. The refresh workflow only commits the activity assets and data, so it preserves your text and portrait banner.

The initial bio, education, skills, and project summaries came from your public GitHub profile, public project READMEs, and the source of [your portfolio](https://github.com/LakshmiHasini/portfolio-website). Project links preserve team attribution where applicable. Review the bio whenever your internship availability or education changes.

