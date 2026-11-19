#!/usr/bin/env python3
"""news-image-20261119: The Day in World News, Thursday 19 November 2026.

A 1024x1024 newspaper front page drawn entirely procedurally with the
Python standard library only. No Pillow, no system fonts, no network.
All lettering is a hand-built vector stroke font (polylines, not pixels),
so every glyph stays crisp at any size. Output is deterministic: two runs
produce byte-identical entry.png. Writes only to MAKEFUN_OUTPUT_DIR.
"""
import math
import os
import struct
import zlib

W = 1024
H = 1024
PAPER = (246, 236, 212)
INK = (26, 26, 26)
RED = (176, 42, 32)
TEAL = (31, 111, 122)
NAVY = (22, 38, 74)
DARK = (20, 30, 55)
GOLD = (232, 178, 62)
CREAM = (250, 244, 228)


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray([bg[0], bg[1], bg[2]] * (w * h))

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, int(x))
        y0 = max(0, int(y))
        x1 = min(self.w, int(x + w))
        y1 = min(self.h, int(y + h))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + (x1 - x0) * 3] = row

    def disc(self, cx, cy, r, c):
        r = int(math.ceil(r))
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r + r:
                    self.put(cx + dx, cy + dy, c)

    def line(self, x0, y0, x1, y1, width, c):
        width = max(1, int(width))
        dx = x1 - x0
        dy = y1 - y0
        steps = int(max(abs(dx), abs(dy)) * 2) + 1
        r = width / 2.0
        for s in range(steps + 1):
            t = s / steps if steps else 0
            self.disc(int(round(x0 + dx * t)), int(round(y0 + dy * t)), r, c)

    def polyline(self, pts, width, c):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], width, c)

    def fill_circle(self, cx, cy, r, c):
        r = int(r)
        for dy in range(-r, r + 1):
            half = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill_rect(cx - half, cy + dy, half * 2 + 1, 1, c)

    def ring(self, cx, cy, r, width, c):
        for k in range(int(width)):
            rr = r - k
            for a in range(0, 360, 2):
                t = math.radians(a)
                self.put(int(cx + rr * math.cos(t)), int(cy + rr * math.sin(t)), c)

    def fill_poly(self, pts, c):
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0 = max(0, int(math.ceil(min(ys))))
        y1 = min(self.h - 1, int(math.floor(max(ys))))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x0, yy0 = pts[i]
                x1, yy1 = pts[(i + 1) % n]
                if (yy0 <= y < yy1) or (yy1 <= y < yy0):
                    if yy1 != yy0:
                        xs.append(x0 + (y - yy0) * (x1 - x0) / (yy1 - yy0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[j]), y, int(xs[j + 1]) - int(xs[j]) + 1, 1, c)

    def vgrad(self, x, y, w, h, top, bot):
        for yy in range(int(h)):
            t = yy / max(1, int(h) - 1)
            c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
            self.fill_rect(x, y + yy, w, 1, c)

    def outline(self, x, y, w, h, c, t=2):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)


# --- Vector stroke font: glyphs on a 9-wide x 14-tall grid, y down. ---
# Each glyph is a list of polylines. Lowercase renders as small caps
# (same glyph, 72% height, baseline-aligned).
G = {}
G['A'] = [[(0, 13), (4.5, 0), (9, 13)], [(2.2, 8), (6.8, 8)]]
G['B'] = [[(0, 0), (0, 13)], [(0, 0), (6, 0), (8, 2), (8, 5), (6, 7), (0, 7)],
          [(0, 7), (6, 7), (8, 9), (8, 11), (6, 13), (0, 13)]]
G['C'] = [[(8, 2), (6, 0), (2, 0), (0, 2), (0, 11), (2, 13), (6, 13), (8, 11)]]
G['D'] = [[(0, 0), (0, 13)], [(0, 0), (6, 0), (9, 3), (9, 10), (6, 13), (0, 13)]]
G['E'] = [[(0, 0), (0, 13)], [(0, 0), (8, 0)], [(0, 6.5), (6, 6.5)], [(0, 13), (8, 13)]]
G['F'] = [[(0, 0), (0, 13)], [(0, 0), (8, 0)], [(0, 6.5), (6, 6.5)]]
G['G'] = [[(8, 2), (6, 0), (2, 0), (0, 2), (0, 11), (2, 13), (6, 13), (8, 11),
           (8, 7), (5, 7)]]
G['H'] = [[(0, 0), (0, 13)], [(9, 0), (9, 13)], [(0, 6.5), (9, 6.5)]]
G['I'] = [[(4.5, 0), (4.5, 13)], [(1, 0), (8, 0)], [(1, 13), (8, 13)]]
G['J'] = [[(9, 0), (9, 11), (7, 13), (3, 13), (1, 11)]]
G['K'] = [[(0, 0), (0, 13)], [(9, 0), (1, 7)], [(4, 9), (9, 13)]]
G['L'] = [[(0, 0), (0, 13)], [(0, 13), (8, 13)]]
G['M'] = [[(0, 13), (0, 0), (4.5, 7), (9, 0), (9, 13)]]
G['N'] = [[(0, 13), (0, 0), (9, 13), (9, 0)]]
G['O'] = [[(2, 0), (7, 0), (9, 3), (9, 10), (7, 13), (2, 13), (0, 10), (0, 3), (2, 0)]]
G['P'] = [[(0, 0), (0, 13)], [(0, 0), (6, 0), (9, 2), (9, 5), (6, 7), (0, 7)]]
G['Q'] = [[(2, 0), (7, 0), (9, 3), (9, 10), (7, 13), (2, 13), (0, 10), (0, 3), (2, 0)],
          [(6, 10), (9, 13)]]
G['R'] = [[(0, 0), (0, 13)], [(0, 0), (6, 0), (9, 2), (9, 5), (6, 7), (0, 7)],
          [(5, 7), (9, 13)]]
G['S'] = [[(8, 2), (6, 0), (3, 0), (1, 2), (1, 5), (3, 7), (6, 7), (8, 9),
           (8, 11), (6, 13), (3, 13), (1, 11)]]
G['T'] = [[(0, 0), (9, 0)], [(4.5, 0), (4.5, 13)]]
G['U'] = [[(0, 0), (0, 11), (2, 13), (7, 13), (9, 11), (9, 0)]]
G['V'] = [[(0, 0), (4.5, 13), (9, 0)]]
G['W'] = [[(0, 0), (2.2, 13), (4.5, 6), (6.8, 13), (9, 0)]]
G['X'] = [[(0, 0), (9, 13)], [(9, 0), (0, 13)]]
G['Y'] = [[(0, 0), (4.5, 6.5)], [(9, 0), (4.5, 6.5)], [(4.5, 6.5), (4.5, 13)]]
G['Z'] = [[(0, 0), (9, 0), (0, 13), (9, 13)]]
G['0'] = G['O']
G['1'] = [[(5, 0), (5, 13)], [(2, 3), (5, 0)], [(1, 13), (8, 13)]]
G['2'] = [[(1, 2), (3, 0), (6, 0), (8, 2), (8, 5), (1, 13), (8, 13)]]
G['3'] = [[(1, 1), (3, 0), (7, 0), (9, 2), (9, 5), (7, 7), (4, 7)],
          [(7, 7), (9, 9), (9, 11), (7, 13), (2, 13)]]
G['4'] = [[(7, 0), (7, 13)], [(0, 8), (7, 8)], [(7, 0), (0, 8)]]
G['5'] = [[(8, 0), (1, 0), (1, 6), (7, 6), (9, 8), (9, 11), (7, 13), (2, 13)]]
G['6'] = [[(8, 1), (6, 0), (2, 0), (0, 3), (0, 10), (2, 13), (6, 13), (8, 11),
           (8, 8), (6, 6), (2, 6), (0, 8)]]
G['7'] = [[(0, 0), (9, 0), (4, 13)]]
G['8'] = [[(3, 0), (6, 0), (8, 2), (8, 5), (6, 7), (3, 7), (1, 5), (1, 2), (3, 0)],
          [(3, 7), (6, 7), (8, 9), (8, 11), (6, 13), (3, 13), (1, 11), (1, 9), (3, 7)]]
G['9'] = [[(0, 12), (0, 9), (1, 6), (3, 5), (7, 5), (9, 7), (9, 10), (7, 13),
           (3, 13), (1, 11)], [(1, 5), (1, 2), (3, 0), (6, 0), (8, 2), (9, 5)]]
G['.'] = [[(4.5, 12.5), (4.5, 12.5)]]
G[','] = [[(4.5, 11), (4.5, 13), (3, 15)]]
G[':'] = [[(4.5, 4), (4.5, 4)], [(4.5, 11), (4.5, 11)]]
G[';'] = [[(4.5, 4), (4.5, 4)], [(4.5, 11), (4.5, 13), (3, 15)]]
G['-'] = [[(1, 6.5), (8, 6.5)]]
G['\u2013'] = [[(1, 6.5), (8, 6.5)]]
G['\u2014'] = [[(0, 6.5), (9, 6.5)]]
G["'"] = [[(4.5, 0), (4, 3)]]
G['\u2019'] = G["'"]
G['"'] = [[(2.5, 0), (2, 3)], [(6.5, 0), (6, 3)]]
G['!'] = [[(4.5, 0), (4.5, 9)], [(4.5, 12.5), (4.5, 12.5)]]
G['?'] = [[(2, 2), (4, 0), (7, 0), (8, 2), (8, 4), (6, 6), (4.5, 8), (4.5, 10)],
          [(4.5, 12.5), (4.5, 12.5)]]
G['/'] = [[(8, 0), (1, 13)]]
G['('] = [[(7, 0), (4, 3), (4, 10), (7, 13)]]
G[')'] = [[(2, 0), (5, 3), (5, 10), (2, 13)]]
G['+'] = [[(1, 6.5), (8, 6.5)], [(4.5, 2), (4.5, 11)]]
G['%'] = [[(8, 0), (0, 13)],
          [(1, 1), (3, 1), (4, 2), (4, 4), (3, 5), (1, 5), (0, 4), (0, 2), (1, 1)],
          [(5, 8), (7, 8), (8, 9), (8, 11), (7, 12), (5, 12), (4, 11), (4, 9), (5, 8)]]
G['$'] = [[(8, 2), (6, 0), (3, 0), (1, 2), (1, 5), (3, 7), (6, 7), (8, 9),
           (8, 11), (6, 13), (3, 13), (1, 11)], [(4.5, -1), (4.5, 14)]]
G['\u20ac'] = [[(8, 2), (6, 0), (2, 0), (0, 2), (0, 11), (2, 13), (6, 13), (8, 11)],
               [(0, 5), (7, 5)], [(0, 8), (7, 8)]]
G['\u00b7'] = [[(4.5, 6), (4.5, 6)]]
G['\u2022'] = [[(4.5, 6), (4.5, 6)]]
G['&'] = [[(7, 2), (5, 0), (2, 0), (1, 2), (1, 4), (3, 6), (8, 12), (8, 13)],
          [(3, 6), (1, 8), (1, 11), (3, 13), (6, 13), (8, 11)]]
G['='] = [[(1, 4), (8, 4)], [(1, 9), (8, 9)]]
G['*'] = [[(4.5, 1), (4.5, 12)], [(1, 3.5), (8, 9.5)], [(8, 3.5), (1, 9.5)]]

# True lowercase glyphs: x-height top y=5, baseline y=13, descenders to y=17.
GL = {}
GL['a'] = [[(8, 4), (8, 13)], [(8, 5), (6, 5), (3, 5), (1, 7), (1, 10), (3, 13), (6, 13), (8, 11)]]
GL['b'] = [[(1, 0), (1, 13)], [(1, 5), (4, 5), (7, 6), (8, 8), (8, 11), (6, 13), (3, 13), (1, 11)]]
GL['c'] = [[(8, 6), (6, 5), (3, 5), (1, 7), (1, 11), (3, 13), (6, 13), (8, 12)]]
GL['d'] = [[(8, 0), (8, 13)], [(8, 5), (5, 5), (2, 6), (1, 8), (1, 11), (3, 13), (6, 13), (8, 11)]]
GL['e'] = [[(8, 7), (6, 5), (3, 5), (1, 7), (1, 10), (3, 13), (6, 13), (8, 11)], [(1, 8), (8, 8)]]
GL['f'] = [[(6, 0), (4, 1), (3, 3), (3, 13)], [(1, 4), (7, 4)]]
GL['g'] = [[(2, 6), (5, 5), (7, 5), (8, 7), (8, 11), (6, 13), (3, 13), (1, 11), (1, 8), (2, 6)],
           [(8, 5), (8, 13), (6, 16), (3, 16), (1, 14)]]
GL['h'] = [[(1, 0), (1, 13)], [(1, 5), (4, 5), (7, 6), (8, 8), (8, 13)]]
GL['i'] = [[(4.5, 5), (4.5, 13)], [(4.5, 1), (4.5, 1)]]
GL['j'] = [[(7, 5), (7, 13), (5, 16), (2, 16), (1, 14)], [(7, 1), (7, 1)]]
GL['k'] = [[(1, 0), (1, 13)], [(8, 5), (2, 9)], [(4, 10), (8, 13)]]
GL['l'] = [[(4.5, 0), (4.5, 13)]]
GL['m'] = [[(1, 13), (1, 5), (4, 5), (5, 8), (5, 13)], [(5, 5), (8, 5), (9, 7), (9, 13)]]
GL['n'] = [[(1, 13), (1, 5), (4, 5), (7, 6), (8, 8), (8, 13)]]
GL['o'] = [[(2, 5), (5, 5), (7, 6), (8, 8), (8, 11), (6, 13), (3, 13), (1, 11), (1, 8), (2, 5)]]
GL['p'] = [[(1, 5), (1, 16)], [(1, 5), (4, 5), (7, 6), (8, 8), (8, 11), (6, 13), (3, 13), (1, 11)]]
GL['q'] = [[(8, 5), (8, 16)], [(8, 5), (5, 5), (2, 6), (1, 8), (1, 11), (3, 13), (6, 13), (8, 11)]]
GL['r'] = [[(1, 13), (1, 5)], [(1, 5), (5, 5), (7, 7), (8, 9)]]
GL['s'] = [[(7, 6), (5, 5), (2, 5), (1, 7), (1, 9), (2, 11), (5, 11), (7, 13), (8, 12)]]
GL['t'] = [[(5, 0), (5, 13)], [(2, 4), (7, 4)], [(5, 13), (7, 12)]]
GL['u'] = [[(1, 5), (1, 11), (3, 13), (6, 13), (8, 11), (8, 5)]]
GL['v'] = [[(1, 5), (4.5, 13), (8, 5)]]
GL['w'] = [[(1, 5), (2.5, 13), (4.5, 8), (6.5, 13), (8, 5)]]
GL['x'] = [[(1, 5), (8, 13)], [(8, 5), (1, 13)]]
GL['y'] = [[(1, 5), (4.5, 12), (8, 5)], [(4.5, 12), (4.5, 16), (2, 17)]]
GL['z'] = [[(1, 5), (8, 5), (1, 13), (8, 13)]]

NARROW = set(".,:;!'")
MEDIUM = set("I1()/[]")
WIDE = set("MW%@&")


def _advance(ch, size, bold):
    if ch == ' ':
        return size * 0.38
    if ch in NARROW:
        f = 0.36
    elif ch in MEDIUM:
        f = 0.55
    elif ch in WIDE:
        f = 0.86
    elif ch.islower():
        if ch in "ilj":
            f = 0.32
        elif ch in "ft":
            f = 0.42
        elif ch in "mw":
            f = 0.72
        else:
            f = 0.52
    else:
        f = 0.62
    return size * f + (size * 0.06 if bold else size * 0.03)


def text_width(s, size, bold=False):
    return sum(_advance(ch, size, bold) for ch in s)


def draw_text(cv, x, y, s, size, color, bold=False, align='l'):
    """Draw string s with top at y. align l/c/r relative to x."""
    if align == 'c':
        x -= text_width(s, size, bold) / 2
    elif align == 'r':
        x -= text_width(s, size, bold)
    if bold:
        w = max(1, int(size * 0.11))
    elif size < 16:
        w = 1
    else:
        w = max(1, int(size * 0.075))
    cx = float(x)
    for ch in s:
        if ch == ' ':
            cx += _advance(ch, size, bold)
            continue
        up = ch.upper()
        strokes = GL.get(ch) if ch.islower() else G.get(ch) or G.get(up)
        if not strokes:
            strokes = G.get(up)
        if not strokes:
            cx += _advance(ch, size, bold)
            continue
        fs = size
        top = y
        gw = _advance(ch, size, bold) * 0.92
        for stroke in strokes:
            pts = [(cx + px / 9.0 * gw, top + py / 13.0 * fs) for px, py in stroke]
            if len(pts) == 1:
                cv.disc(int(round(pts[0][0])), int(round(pts[0][1])), max(1, w / 2.0), color)
            else:
                cv.polyline(pts, w, color)
        cx += _advance(ch, size, bold)
    return cx


def wrap(s, size, max_w, bold=False):
    words = s.split(' ')
    lines, cur = [], ''
    for wd in words:
        trial = wd if not cur else cur + ' ' + wd
        if text_width(trial, size, bold) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, s, size, max_w, color, bold=False, lh=None, max_lines=None):
    lines = wrap(s, size, max_w, bold)
    if max_lines:
        lines = lines[:max_lines]
    lh = lh or int(size * 1.32)
    for i, ln in enumerate(lines):
        draw_text(cv, x, y + i * lh, ln, size, color, bold=bold)
    return y + len(lines) * lh


# --- Story data: 35 real stories from Thursday 19 November 2026. ---
LEAD = ("TRUMP, XI AND PUTIN MEET",
        "Trump, Xi and Putin open the first trilateral summit in history "
        "at APEC in Shenzhen, with nuclear arms, Ukraine and Iran on the agenda.")
CAPTION = ("Illustration \u2014 Trump, Xi and Putin open the first trilateral "
           "summit in history at APEC in Shenzhen, with nuclear arms, "
           "Ukraine and Iran on the agenda.")
FEATURES = [
    (2, "GULF \u00b7 CONFLICT", "US\u2013IRAN STRIKES WIDEN",
     "Iran hits US bases again; US hits back.", "gulf"),
    (3, "MARKETS \u00b7 IPO", "ANTHROPIC IPO AT $79.4BN",
     "Anthropic lists in a record AI debut.", "chart"),
]
GRID = [
    (4, "GAZA \u00b7 AID CRISIS", "FLOODS SWAMP GAZA CAMPS",
     "Storms displace 46,000 households; aid waits.", 34.5, 31.5),
    (5, "ISRAEL \u00b7 POLITICS", "HERZOG TAPS EISENKOT TO GOVERN",
     "Herzog bypasses Netanyahu; Kahana is speaker.", 35.2, 31.8),
    (6, "EUROPE \u00b7 SECURITY", "ESTONIA TO SHUT BORDER WITH RUSSIA",
     "Tallinn shuts road crossings from 1 December.", 27.5, 59.0),
    (7, "YEMEN \u00b7 WAR", "HOUTHIS SEIZE RED SEA COAST",
     "Rebels take coast posts as troops withdraw.", 43.3, 12.6),
    (8, "TECH \u00b7 GAMES", "GTA VI ROLLS OUT WORLDWIDE",
     "Rockstar's Vice City return launches worldwide.", -80.2, 25.8),
    (9, "EUROPE \u00b7 UKRAINE", "EU PROPOSES \u20ac45BN UKRAINE LOAN",
     "Brussels tables a loan repaid after reparations.", 4.4, 50.8),
    (10, "ASIA \u00b7 CHIPS", "NVIDIA HALTS H-SERIES CHIPS TO CHINA",
     "H-series shipments stop; Kress promises raises.", 116.4, 39.9),
    (11, "ASIA \u00b7 LABOUR", "BANGLADESH GARMENT PROTESTS",
     "Workers demand a 30,000-taka minimum wage.", 90.4, 23.8),
    (12, "ASIA \u00b7 WEATHER", "CYCLONE AKVAN NEARS ODISHA",
     "Schools close as the storm bears down.", 85.8, 20.3),
]
NUMBERS = [("$79.4BN", "ANTHROPIC IPO VALUE"), ("46,000", "DISPLACED IN GAZA"),
           ("\u20ac45BN", "EU LOAN FOR UKRAINE"), ("150,000", "TENTS AWAITING ENTRY")]
ALSO = [
    (13, "COP31", "Talks near finale"), (14, "Voyager", "A light-day out"),
    (15, "Fed", "Minutes point to rises"), (16, "Myanmar", "Rethinks ASEAN ties"),
    (17, "Argentina", "Parana floods"), (18, "Ethiopia", "Troops at border"),
    (19, "Siberia", "Crash kills 19"), (20, "France", "Protests, week four"),
    (21, "Spain", "General strike"), (22, "Prague", "Media freedom march"),
    (23, "India", "Japan 2+2 talks"), (24, "Delhi", "Schools reopen"),
    (25, "US", "Liu to chair House Dems"), (26, "Venezuela", "$12bn oil revenue"),
    (27, "Canada", "China ties adjusted"), (28, "Markets", "Goldman lifts India"),
    (29, "India", "162.5% Scotch duty"), (30, "Microsoft", "ByteDance talks"),
    (31, "Abu Dhabi", "Drone strikes"), (32, "Germany", "Hybrid threats"),
    (33, "Cricket", "India\u2013NZ Test"), (34, "Senate", "AI cyber threats grow"),
    (35, "Saudi", "Danger passed"),
]
PINS = [(114.1, 22.5), (47.5, 29.3), (-122.4, 37.8)] + [
    (lon, lat) for _, _, _, _, lon, lat in GRID]


def circ_num(cv, x, y, n, r=7):
    cv.fill_circle(x + r, y + r, r, RED)
    draw_text(cv, x + r, y + r - 5, str(n), 10, (255, 255, 255), bold=True, align='c')


def flag_us(cv, x, y, w, h):
    for i in range(7):
        cv.fill_rect(x, y + i * h // 7, w, h // 7 + 1, (178, 34, 52) if i % 2 == 0 else (255, 255, 255))
    cv.fill_rect(x, y, w * 0.45, h * 0.55, (30, 50, 110))
    for r in range(3):
        for c in range(3):
            cv.fill_circle(x + 3 + c * 5, y + 3 + r * 4, 1, (255, 255, 255))


def flag_cn(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (222, 41, 16))
    cv.fill_circle(x + 7, y + 6, 3, GOLD)
    for dx, dy in [(14, 3), (17, 6), (16, 10), (12, 11)]:
        cv.fill_circle(x + dx, y + dy, 1, GOLD)


def flag_ru(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h // 3 + 1, (255, 255, 255))
    cv.fill_rect(x, y + h // 3, w, h // 3 + 1, (0, 57, 166))
    cv.fill_rect(x, y + 2 * h // 3, w, h // 3 + 1, (213, 0, 50))


def hero(cv, x, y, w, h):
    sky_h = int(h * 0.58)
    for yy in range(sky_h):
        t = yy / max(1, sky_h - 1)
        if t < 0.55:
            a, b = (62, 48, 98), (214, 110, 62)
            tt = t / 0.55
        else:
            a, b = (214, 110, 62), (244, 196, 90)
            tt = (t - 0.55) / 0.45
        c = tuple(int(a[i] + (b[i] - a[i]) * tt) for i in range(3))
        cv.fill_rect(x, y + yy, w, 1, c)
    cv.fill_circle(x + int(w * 0.64), y + sky_h - 6, 17, (244, 205, 115))
    cv.fill_rect(x, y + sky_h, w, h - sky_h, NAVY)
    heights = [62, 40, 78, 52, 88, 46, 70, 58, 84, 44, 66, 50, 76, 42]
    bw = w // len(heights)
    for i, bh in enumerate(heights):
        bx = x + i * bw
        cv.fill_rect(bx + 2, y + sky_h - bh, bw - 4, bh, DARK)
        for wy in range(8, bh - 6, 10):
            for wx in range(6, bw - 8, 9):
                if (i * 13 + wy * 7 + wx) % 5 == 0:
                    cv.fill_rect(bx + wx, y + sky_h - bh + wy, 2, 2, GOLD)
    for k, lw in enumerate([120, 90, 64, 42, 26]):
        cv.fill_rect(x + int(w * 0.64) - lw // 2, y + sky_h + 10 + k * 9, lw, 2, GOLD)
    for fx, fn in [(x + 108, flag_us), (x + 178, flag_cn), (x + 308, flag_ru)]:
        cv.line(fx + 17, y + sky_h - 44, fx + 17, y + sky_h + 2, 2, INK)
        fn(cv, fx, y + sky_h - 44, 34, 21)


def gulf_art(cv, x, y, w, h):
    cv.vgrad(x, y, w, int(h * 0.55), (214, 120, 60), (120, 60, 40))
    cv.fill_circle(x + int(w * 0.68), y + 22, 12, (244, 180, 90))
    for cx, cy, r in [(30, 18, 14), (48, 12, 16), (66, 22, 12), (90, 14, 13)]:
        cv.fill_circle(x + cx, y + cy, r, (70, 60, 58))
    cv.fill_rect(x, y + int(h * 0.55), w, h - int(h * 0.55), (18, 60, 80))
    cv.fill_rect(x + 12, y + int(h * 0.62), w - 24, 12, (20, 20, 20))
    cv.fill_rect(x + 12, y + int(h * 0.62) + 12, w - 24, 4, (150, 40, 30))
    cv.fill_rect(x + int(w * 0.62), y + int(h * 0.42), 16, 14, (240, 240, 240))
    cv.fill_rect(x + 30, y + int(h * 0.72), 34, 3, GOLD)
    cv.fill_rect(x + 90, y + int(h * 0.78), 26, 3, GOLD)


def chart_art(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, NAVY)
    for gy in range(4):
        yy = y + 12 + gy * (h - 24) // 3
        cv.fill_rect(x + 6, yy, w - 12, 1, (90, 110, 150))
    bars = [26, 40, 54, 70]
    cols = [(44, 160, 170), (232, 178, 62), (214, 110, 62), (120, 190, 220)]
    bw = (w - 20) // 4
    tops = []
    for i, bh in enumerate(bars):
        bx = x + 10 + i * bw
        cv.fill_rect(bx, y + h - 8 - bh, bw - 6, bh, cols[i])
        tops.append((bx + (bw - 6) // 2, y + h - 8 - bh))
    cv.polyline(tops, 2, GOLD)
    draw_text(cv, tops[-1][0] + 2, tops[-1][1] - 16, "*", 18, GOLD, bold=True)


def world_map(cv, x, y, w, h):
    blobs = [
        [(0.02, 0.25), (0.10, 0.12), (0.20, 0.10), (0.24, 0.22), (0.18, 0.32), (0.10, 0.38), (0.04, 0.32)],
        [(0.20, 0.45), (0.26, 0.42), (0.30, 0.50), (0.27, 0.68), (0.22, 0.62)],
        [(0.44, 0.18), (0.50, 0.12), (0.56, 0.16), (0.54, 0.26), (0.47, 0.28)],
        [(0.45, 0.32), (0.52, 0.30), (0.58, 0.38), (0.56, 0.55), (0.50, 0.62), (0.46, 0.48)],
        [(0.58, 0.12), (0.70, 0.08), (0.85, 0.12), (0.92, 0.22), (0.85, 0.32), (0.72, 0.34), (0.60, 0.26)],
        [(0.80, 0.62), (0.88, 0.58), (0.94, 0.64), (0.88, 0.72), (0.81, 0.68)],
    ]
    for blob in blobs:
        cv.fill_poly([(x + px * w, y + py * h) for px, py in blob], TEAL)
    for i, (lon, lat) in enumerate(PINS, start=1):
        px = x + (lon + 180) / 360.0 * w
        py = y + (75 - lat) / 130.0 * h
        cv.fill_circle(int(px), int(py), 6, RED)
        cv.ring(int(px), int(py), 6, 1, (255, 255, 255))
        draw_text(cv, px, py - 4, str(i), 8, (255, 255, 255), bold=True, align='c')


def write_png(cv, path):
    raw = bytearray()
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.px[yy * cv.w * 3:(yy + 1) * cv.w * 3]

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack(
            '>I', zlib.crc32(kind + data) & 0xffffffff)

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)


def build():
    cv = Canvas(W, H, PAPER)
    # Masthead + dateline
    draw_text(cv, W // 2, 14, "THE DAY IN WORLD NEWS", 52, INK, bold=True, align='c')
    cv.fill_rect(28, 84, 968, 3, INK)
    cv.fill_rect(28, 90, 968, 1, INK)
    draw_text(cv, 28, 98, "THURSDAY, 19 NOVEMBER 2026", 15, INK, bold=True)
    draw_text(cv, 996, 98, "35 STORIES \u00b7 6 CONTINENTS \u00b7 ONE PAGE", 15, INK,
              bold=True, align='r')
    cv.fill_rect(28, 122, 968, 2, INK)
    # Lead
    circ_num(cv, 28, 132, 1)
    draw_text(cv, 50, 132, "SUMMIT \u00b7 SHENZHEN", 15, RED, bold=True)
    draw_text(cv, 28, 152, LEAD[0], 42, INK, bold=True)
    hero(cv, 28, 202, 968, 148)
    draw_para(cv, 28, 358, CAPTION, 13, 968, INK, lh=17, max_lines=2)
    cv.fill_rect(28, 398, 968, 2, INK)
    # Features
    for k, (num, kicker, head, summ, kind) in enumerate(FEATURES):
        bx = 28 + k * 492
        cv.outline(bx, 406, 476, 104, INK, 2)
        if kind == 'gulf':
            gulf_art(cv, bx + 6, 412, 148, 92)
        else:
            chart_art(cv, bx + 6, 412, 148, 92)
        tx = bx + 164
        circ_num(cv, tx, 412, num)
        draw_text(cv, tx + 22, 412, kicker, 13, RED, bold=True)
        draw_para(cv, tx, 432, head, 17, 476 - 170, INK, bold=True, lh=20, max_lines=2)
        draw_para(cv, tx, 474, summ, 12, 476 - 170, INK, lh=15, max_lines=2)
    # Grid 3x3
    for i, (num, kicker, head, summ, lon, lat) in enumerate(GRID):
        col, row = i % 3, i // 3
        gx = 28 + col * 320
        gy = 518 + row * 81
        circ_num(cv, gx, gy, num, r=6)
        draw_text(cv, gx + 18, gy, kicker, 11, RED, bold=True)
        draw_para(cv, gx, gy + 16, head, 15, 304, INK, bold=True, lh=18, max_lines=2)
        draw_para(cv, gx, gy + 52, summ, 11, 304, INK, lh=14, max_lines=2)
    for sx in (340, 660):
        cv.fill_rect(sx, 518, 1, 243, (200, 180, 140))
    # By the numbers
    cv.outline(28, 770, 968, 48, INK, 2)
    draw_para(cv, 36, 780, "BY THE NUMBERS", 11, 100, RED, bold=True, lh=14, max_lines=2)
    for i, (big, label) in enumerate(NUMBERS):
        cx = 138 + i * 215
        draw_text(cv, cx + 107, 776, big, 21, INK, bold=True, align='c')
        draw_text(cv, cx + 107, 803, label, 10, INK, align='c')
        if i:
            cv.fill_rect(cx, 776, 1, 36, INK)
    # Map + Also
    cv.outline(28, 826, 476, 148, INK, 2)
    draw_text(cv, 36, 832, "WHERE THE NEWS HAPPENED", 12, INK, bold=True)
    draw_text(cv, 36, 848, "Dots mark stories 1-12.", 10, INK)
    world_map(cv, 36, 864, 460, 102)
    cv.outline(520, 826, 476, 148, INK, 2)
    draw_text(cv, 528, 832, "ALSO ON 19 NOVEMBER \u2014 23 MORE STORIES", 12, INK, bold=True)
    for j, (num, place, short) in enumerate(ALSO):
        col = j // 12
        lx = 528 + col * 236
        ly = 848 + (j % 12) * 10.5
        draw_text(cv, lx, ly, "%d. %s \u2014 %s" % (num, place, short), 9, INK)
    # Footer
    cv.fill_rect(28, 982, 968, 2, INK)
    draw_text(cv, 28, 988, "Sources: AP \u00b7 Reuters \u00b7 AFP \u00b7 BBC \u00b7 Al Jazeera \u00b7 UN News. Original drawings.", 11, INK)
    draw_text(cv, 28, 1004, "The world in one picture \u2014 35 stories from Thursday 19 November 2026.", 11, INK)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "."
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(build(), path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
