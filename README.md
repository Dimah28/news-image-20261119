# news-image-20261119

[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/Dimah28/news-image-20261119/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/Dimah28/news-image-20261119/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

Entry for the make.fun bounty **"Sum up 19 November's world news in one image"** ([news-image-20261119](https://make.fun/bounty/news-image-20261119), $250, ends Sat 21 Nov 2026 07:00 WIB).

## The image

`entry.png` — a 1024×1024 newspaper front page drawn entirely procedurally, in the style of a classic broadsheet:

- masthead: **THE DAY IN WORLD NEWS — THURSDAY, 19 NOVEMBER 2026** (35 stories · 6 continents · one page)
- lead story: **Trump, Xi and Putin meet** — the first trilateral summit in history opens at APEC in Shenzhen, with nuclear arms, Ukraine and Iran on the agenda, under a full-width **hero illustration** of the Shenzhen skyline at dusk with the three flags
- two feature cards: **US–Iran strikes widen across the Gulf** (Iran hits US bases again; the US hits back) and **Anthropic's IPO at $79.4bn** (a record AI debut, with a rising bar chart)
- nine stories in a **3×3 grid**, each with a dateline kicker, a short bold headline and a two-line summary: Gaza floods displacing 46,000 households, Herzog tapping Eisenkot to govern Israel, Estonia shutting its road border with Russia, Houthis seizing the Red Sea coast, GTA VI rolling out worldwide, the EU's €45bn Ukraine loan, Nvidia halting H-series chips to China, Bangladesh garment protests, and Cyclone Akvan nearing Odisha
- a **BY THE NUMBERS** band ($79.4bn Anthropic IPO value · 46,000 displaced in Gaza · €45bn EU loan for Ukraine · 150,000 tents awaiting entry)
- a **world map** with numbered dots marking stories 1–12, and **ALSO ON 19 NOVEMBER — 23 MORE STORIES** (stories 13–35, one line each)
- footer: sources AP · Reuters · AFP · BBC · Al Jazeera · UN News, "Original drawings."

## How it is drawn

`main.py` is standard library only (`math`, `os`, `struct`, `zlib`) — no Pillow, no system fonts, no network. All lettering uses a hand-built vector stroke font (polylines on a grid, with true lowercase glyphs), so text stays crisp at any size and never looks pixelated. Buildings, flags, the tanker, the bar chart and the world map are all drawn with the same small canvas primitives (rectangles, gradients, polygons, circles, thick lines).

## Run it

```sh
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
# writes /tmp/out/entry.png — 1024×1024, deterministic (two runs are byte-identical)
```

The grader runs it the same way, read-only, with no network, in under 60 seconds.
