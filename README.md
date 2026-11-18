[![make.fun](https://make.fun/badge/news-image-20261117.svg)](https://make.fun/bounty/news-image-20261117?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)
[![rank](https://make.fun/badge/news-image-20261117/Emjee22/news-image-20261117-entry-v4/rank.svg)](https://make.fun/bounty/news-image-20261117/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)
[![reward](https://make.fun/badge/news-image-20261117/Emjee22/news-image-20261117-entry-v4/reward.svg)](https://make.fun/bounty/news-image-20261117?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)

# Tuesday 17 November 2026 — The World's News in One Image (v4, map-hero)

Entry for the make.fun bounty `news-image-20261117`: a program that draws one
image summing up the world's news of Tuesday 17 November 2026 — 20 stories,
6 continents, one day. This is the second entry for the same competition
(v4, map-hero poster); it replaces the earlier newspaper front-page entry
if submitted last before the deadline.

## How it works

`main.py` (Python 3.13, standard library only) draws a 1024x1024 PNG entirely
from scratch: its own PNG encoder, its own 5x7 bitmap font, a dot-grid world
map with numbered pins for the 10 biggest stories, short ALL-CAPS headlines
(legible at ~300 px), a numbered one-liner list for 10 more stories, a
BY THE NUMBERS strip, a DATE CHECK box and a sources footer. No network, no
image files, no fonts on disk. Two runs write byte-identical output.

Run it:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## Files

- `main.py` — the whole entry
- `README.md` — this file
- `LICENSE` — MIT
