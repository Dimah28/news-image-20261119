# news-image-20261119

[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/Dimah28/news-image-20261119/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/Dimah28/news-image-20261119/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

Entry for the make.fun bounty **"Sum up 19 November's world news in one image"** ([news-image-20261119](https://make.fun/bounty/news-image-20261119), $250, ends Sat 21 Nov 2026 07:00 WIB).

## The image

`entry.png` — a 1024×1024 newspaper front page drawn entirely procedurally, in the style of a classic broadsheet:

- masthead: **THE DAY IN WORLD NEWS — THURSDAY, 19 NOVEMBER 2026** (35 stories · 6 continents · one page)
- lead story: **Trump, Xi and Putin meet** — the first trilateral summit in history opens at APEC in Shenzhen, with nuclear arms, Ukraine and Iran on the agenda, under a full-width **hero illustration** of the Shenzhen skyline at dusk with the three flags
- two feature cards: **US–Iran strikes widen across the Gulf** (Iran fires at US bases in Kuwait and Bahrain again; the US hits a Revolutionary Guard missile site on Qeshm Island) and **Anthropic's IPO at $79.4bn** (the biggest AI debut ever)
- nine stories in a **3×3 grid**, each with a dateline kicker, a short bold headline and a two-line summary: Gaza floods displacing 46,000 households, Herzog tapping Eisenkot to govern Israel, Estonia shutting its road border with Russia, Houthis seizing the Red Sea coast, GTA VI rolling out worldwide, the EU's €45bn Ukraine loan, Nvidia halting H-series chips to China, Bangladesh garment protests, and Cyclone Akvan nearing Odisha
- a **BY THE NUMBERS** strip ($79.4bn Anthropic IPO, 46,000 displaced in Gaza, €45bn EU loan for Ukraine, 150,000 tents awaiting entry)
- a **world map** ("WHERE THE NEWS HAPPENED") with numbered pins for stories 1–12, beside an **ALSO ON 19 NOVEMBER** list of 23 more stories (COP31, Voyager 1, Fed minutes, Myanmar, Parana floods, Ethiopia–Eritrea, the Siberian plane crash, France protests, Spain's general strike, Prague, India–Japan talks, Delhi schools, Liu Yunping, Venezuelan oil revenue, Canada–China ties, Goldman on India, Scotch duty, Microsoft–ByteDance, Abu Dhabi talks, German hybrid-threat warning, India–NZ Test, AI cyber threats, Saudi Arabia)
- a footer strip with the date and the source credit (AP, Reuters, AFP, BBC, Al Jazeera, UN News)

The stories are the ones that happened, or were first reported, on 19 November 2026. Nothing is invented beyond the reporting, and no other day's news is in the picture.

## The program

`main.py` (Python 3.13, standard library only) draws the whole page procedurally — Hershey vector fonts (public domain) for the masthead, headlines and body text, rasterised 2x-supersampled and alpha-blended so the type reads as clean lines, plus a hand-written 5×7 bitmap font, a small vector drawing layer, and a hand-encoded PNG (zlib). It runs with no network and no dependencies. It is fully deterministic: two runs write byte-identical files.

Run it with:

```sh
MAKEFUN_OUTPUT_DIR=/output python3 main.py
```

which writes `/output/entry.png` (1024×1024, under 1 MiB).
