#!/usr/bin/env python3
"""news-image-20261119 — "The world in one picture: Thursday 19 November 2026".

A newspaper front page drawn entirely procedurally with the Python 3.13
standard library only: Hershey vector fonts (public domain) for the
masthead and headlines — smooth strokes, rasterised 2x-supersampled and
alpha-blended, so the big type reads as clean lines, not square pixels —
plus a hand-written 5x7 bitmap font for the smallest labels, a small
vector drawing layer, and a hand-encoded PNG (zlib). No network, no
files read, no randomness, no clock — two runs write byte-identical
files.

Layout (1024x1024), 35 stories, 6 continents:
  masthead -> lead story (Trump, Xi and Putin meet in Shenzhen) with a
  full-width hero illustration -> two feature cards (Gulf strikes,
  Anthropic's record IPO) -> nine stories in a 3x3 grid -> "BY THE
  NUMBERS" strip -> dotted world map with numbered pins beside an
  "ALSO ON" list of 23 more stories -> sources footer.
Every story below happened, or was first reported, on Thursday
19 November 2026; disputed claims are labelled as claims.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 231)     # warm newsprint
INK = (28, 26, 22)          # near-black text and rules
NAVY = (22, 32, 63)         # masthead band
NAVY_DK = (14, 20, 42)
GOLD = (200, 134, 26)
GOLD_LT = (232, 196, 110)
BRICK = (166, 58, 42)       # kickers, number badges
BRICK_DK = (130, 44, 30)
CREAM = (250, 246, 236)
CARD = (255, 253, 247)
LINE = (28, 26, 22)
MUTED = (96, 90, 78)
SEA = (46, 92, 110)
SKY = (126, 170, 196)
SAND = (214, 186, 140)
SAGE = (122, 140, 110)
RUST = (178, 92, 52)
SLATE = (84, 98, 110)
MAPDOT = (90, 104, 96)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
EU_BLUE = (16, 48, 120)
TEAL_DK = (14, 58, 66)
TEAL = (40, 128, 128)       # chart bars
RED = BRICK                 # kickers (alias of brick red)
RULE = (196, 188, 172)      # light divider rules

# ---------------------------------------------------------------- PNG writer
def encode_png(width, height, rgb):
    """rgb: bytes of RGB rows, top to bottom. Returns whole PNG bytes."""
    body = b"".join(
        b"\x00" + rgb[y * width * 3:(y + 1) * width * 3]
        for y in range(height)
    )

    def pack(kind, payload):
        head = struct.pack(">I", len(payload)) + kind + payload
        return head + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + pack(b"IHDR", header)
            + pack(b"IDAT", zlib.compress(body, 9)) + pack(b"IEND", b""))

# ---------------------------------------------------------------- drawing surface
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill(0, 0, w, h, bg)

    def _off(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._off(x, y)
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        stripe = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = self._off(x0, yy)
            self.px[i:i + len(stripe)] = stripe

    def hline(self, x, y, w, c):
        self.fill(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.fill(x, y, 1, h, c)

    def rect(self, x, y, w, h, c, lw=1):
        """Filled rectangle (lw kept for call compatibility)."""
        self.fill(x, y, w, h, c)

    def outline(self, x, y, w, h, c, lw=1):
        """Rectangle outline (border only)."""
        self.fill(x, y, w, lw, c)
        self.fill(x, y + h - lw, w, lw, c)
        self.fill(x, y, lw, h, c)
        self.fill(x + w - lw, y, lw, h, c)

    def blend(self, x, y, c, alpha):
        """Alpha-blend one pixel towards colour c (alpha in [0, 1])."""
        if 0 <= x < self.w and 0 <= y < self.h and alpha > 0.0:
            i = self._off(x, y)
            self.px[i] = int(round(self.px[i] + (c[0] - self.px[i]) * alpha))
            self.px[i + 1] = int(round(self.px[i + 1] + (c[1] - self.px[i + 1]) * alpha))
            self.px[i + 2] = int(round(self.px[i + 2] + (c[2] - self.px[i + 2]) * alpha))

    def png_bytes(self):
        return encode_png(self.w, self.h, bytes(self.px))

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, filled=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if filled:
                    if d <= r * r:
                        self.set(xx, yy, c)
                elif r * r - 2 * r <= d <= r * r:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        """Scanline fill of a simple polygon."""
        if not pts:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                xa, xb = int(xs[j]), int(xs[j + 1])
                self.fill(xa, y, xb - xa + 1, 1, c)

    def disc(self, cx, cy, r, c):
        """Filled disc (used for soft dots in art)."""
        self.circle(cx, cy, r, c, filled=True)


# ---------------------------------------------------------------- bitmap font
# 5x7 bitmap font: each glyph is 7 rows of 5 cells, '1' = ink. Glyphs are
# drawn as FILLED rectangles (solid pixels), never as strokes, so the
# letterforms stay solid and legible at every size. The euro, degree,
# curly-quote and arrow glyphs were added for this page.
# No files read, no network.
BITMAP = {
'A': ("01110","10001","10001","11111","10001","10001","10001"),
'B': ("11110","10001","10001","11110","10001","10001","11110"),
'C': ("01110","10001","10000","10000","10000","10001","01110"),
'D': ("11110","10001","10001","10001","10001","10001","11110"),
'E': ("11111","10000","10000","11110","10000","10000","11111"),
'F': ("11111","10000","10000","11110","10000","10000","10000"),
'G': ("01110","10001","10000","10111","10001","10001","01111"),
'H': ("10001","10001","10001","11111","10001","10001","10001"),
'I': ("01110","00100","00100","00100","00100","00100","01110"),
'J': ("00111","00010","00010","00010","00010","10010","01100"),
'K': ("10001","10010","10100","11000","10100","10010","10001"),
'L': ("10000","10000","10000","10000","10000","10000","11111"),
'M': ("10001","11011","10101","10101","10001","10001","10001"),
'N': ("10001","11001","10101","10011","10001","10001","10001"),
'O': ("01110","10001","10001","10001","10001","10001","01110"),
'P': ("11110","10001","10001","11110","10000","10000","10000"),
'Q': ("01110","10001","10001","10001","10101","10010","01101"),
'R': ("11110","10001","10001","11110","10100","10010","10001"),
'S': ("01111","10000","10000","01110","00001","00001","11110"),
'T': ("11111","00100","00100","00100","00100","00100","00100"),
'U': ("10001","10001","10001","10001","10001","10001","01110"),
'V': ("10001","10001","10001","10001","10001","01010","00100"),
'W': ("10001","10001","10001","10101","10101","11011","10001"),
'X': ("10001","10001","01010","00100","01010","10001","10001"),
'Y': ("10001","10001","01010","00100","00100","00100","00100"),
'Z': ("11111","00001","00010","00100","01000","10000","11111"),
'0': ("01110","10001","10011","10101","11001","10001","01110"),
'1': ("00100","01100","00100","00100","00100","00100","01110"),
'2': ("01110","10001","00001","00110","01000","10000","11111"),
'3': ("11111","00010","00100","00010","00001","10001","01110"),
'4': ("00010","00110","01010","10010","11111","00010","00010"),
'5': ("11111","10000","11110","00001","00001","10001","01110"),
'6': ("00110","01000","10000","11110","10001","10001","01110"),
'7': ("11111","00001","00010","00100","01000","01000","01000"),
'8': ("01110","10001","10001","01110","10001","10001","01110"),
'9': ("01110","10001","10001","01111","00001","00010","01100"),
'a': ("00000","00000","01110","00001","01111","10001","01111"),
'b': ("10000","10000","11110","10001","10001","10001","11110"),
'c': ("00000","00000","01110","10001","10000","10001","01110"),
'd': ("00001","00001","01111","10001","10001","10001","01111"),
'e': ("00000","00000","01110","10001","11111","10000","01110"),
'f': ("00110","01001","01000","11110","01000","01000","01000"),
'g': ("00000","00000","01111","10001","10001","01111","01110"),
'h': ("10000","10000","11110","10001","10001","10001","10001"),
'i': ("00100","00000","01100","00100","00100","00100","01110"),
'j': ("00010","00000","00110","00010","00010","10010","01100"),
'k': ("10000","10000","10010","10100","11000","10100","10010"),
'l': ("01100","00100","00100","00100","00100","00100","01110"),
'm': ("00000","00000","11010","10101","10101","10101","10101"),
'n': ("00000","00000","11110","10001","10001","10001","10001"),
'o': ("00000","00000","01110","10001","10001","10001","01110"),
'p': ("00000","00000","11110","10001","10001","11110","10000"),
'q': ("00000","00000","01111","10001","10001","01111","00001"),
'r': ("00000","00000","10110","11001","10000","10000","10000"),
's': ("00000","00000","01111","10000","01110","00001","11110"),
't': ("01000","01000","11110","01000","01000","01000","00110"),
'u': ("00000","00000","10001","10001","10001","10001","01111"),
'v': ("00000","00000","10001","10001","10001","01010","00100"),
'w': ("00000","00000","10001","10101","10101","10101","01010"),
'x': ("00000","00000","10001","01010","00100","01010","10001"),
'y': ("00000","00000","10001","10001","10001","01111","01110"),
'z': ("00000","00000","11111","00010","00100","01000","11111"),
' ': ("00000","00000","00000","00000","00000","00000","00000"),
'.': ("00000","00000","00000","00000","00000","01100","01100"),
',': ("00000","00000","00000","00000","01100","00100","01000"),
':': ("00000","01100","01100","00000","01100","01100","00000"),
';': ("00000","01100","01100","00000","01100","00100","01000"),
'!': ("00100","00100","00100","00100","00100","00000","00100"),
'?': ("01110","10001","00001","00110","00100","00000","00100"),
'-': ("00000","00000","00000","01110","00000","00000","00000"),
'\u2013': ("00000","00000","00000","01110","00000","00000","00000"),
'\u2014': ("00000","00000","00000","11111","00000","00000","00000"),
"'": ("00100","00100","01000","00000","00000","00000","00000"),
'\u2018': ("00100","00100","00010","00000","00000","00000","00000"),
'\u2019': ("00100","00100","01000","00000","00000","00000","00000"),
'"': ("01010","01010","01010","00000","00000","00000","00000"),
'(': ("00010","00100","01000","01000","01000","00100","00010"),
')': ("01000","00100","00010","00010","00010","00100","01000"),
'/': ("00001","00010","00010","00100","01000","01000","10000"),
'%': ("11001","11010","00010","00100","01000","01011","10011"),
'$': ("00100","01111","10100","01110","00101","11110","00100"),
'&': ("01100","10010","10100","01000","10101","10010","01101"),
'\u00b7': ("00000","00000","00000","01100","01100","00000","00000"),
'\u2022': ("00000","01110","11111","11111","01110","00000","00000"),
'+': ("00000","00100","00100","11111","00100","00100","00000"),
'\u00d7': ("00000","10001","01010","00100","01010","10001","00000"),
'=': ("00000","00000","11111","00000","11111","00000","00000"),
'*': ("00000","00100","10101","01110","10101","00100","00000"),
'>': ("10000","01000","00100","00010","00100","01000","10000"),
'<': ("00001","00010","00100","01000","00100","00010","00001"),
'#': ("01010","01010","11111","01010","11111","01010","01010"),
'\u20ac': ("01110","10001","10000","11111","10000","10001","01110"),
'\u00b0': ("01100","10010","10010","01100","00000","00000","00000"),
'\u201c': ("01010","01010","01010","00000","00000","00000","00000"),
'\u201d': ("01010","01010","01010","00000","00000","00000","00000"),
'\u2192': ("00000","00100","00010","11111","00010","00100","00000"),
}


# Hershey vector fonts (public domain, A.V. Hershey, US NBS).
# Extracted from Paul Bourke's hershey JHF file; only the glyphs used here.
# Each glyph: (left bearing, right bearing, stroke data).
# Stroke data: char pairs, coords relative to ord("R"); a pair " R" = pen up.
SIMPLEX = {
    '!': (-2, 3, 'RMRR RSMSR RRURVSVSURU'),
    '"': (-4, 4, 'PMPQ RTMTQ'),
    '#': (-5, 6, 'RLPW RULSW ROPVP ROSVS'),
    '$': (-5, 5, 'UNSMQMONOPQQTRUSUUSVQVOU RRLRW'),
    '&': (-6, 6, 'VRURTSSURVOVNUNSORRQSPSNRMPMONOPQSSUUVVV'),
    "'": (-2, 2, 'RMRQ'),
    '(': (-3, 4, 'TLRNQPQSRUTW'),
    ')': (-4, 3, 'PLRNSPSSRUPW'),
    '*': (-5, 5, 'RORU ROPUT RUPOT'),
    '+': (-6, 6, 'RNRV RNRVR'),
    ',': (-2, 3, 'SVRVRUSUSWRY'),
    '-': (-6, 6, 'NRVR'),
    '.': (-2, 3, 'RURVSVSURU'),
    '/': (-5, 5, 'VLNW'),
    '0': (-5, 5, 'RMPNOPOSPURVTUUSUPTNRM'),
    '1': (-5, 5, 'PORMRV'),
    '2': (-5, 5, 'ONQMSMUNUPTROVUV'),
    '3': (-5, 5, 'ONQMSMUNUPSQ RRQSQURUUSVQVOU'),
    '4': (-5, 5, 'SMSV RSMNSVS'),
    '5': (-5, 5, 'PMOQQPRPTQUSTURVQVOU RPMTM'),
    '6': (-5, 5, 'TMRMPNOPOSPURVTUUSTQRPPQOS'),
    '7': (-5, 5, 'UMQV ROMUM'),
    '8': (-5, 5, 'QMONOPQQSQUPUNSMQM RQQOROUQVSVUUURSQ'),
    '9': (-5, 5, 'UPTRRSPROPPNRMTNUPUSTURVPV'),
    ':': (-2, 3, 'RPRQSQSPRP RRURVSVSURU'),
    ';': (-2, 3, 'RPRQSQSPRP RSVRVRUSUSWRY'),
    '=': (-6, 6, 'NPVP RNTVT'),
    '?': (-4, 5, 'PNRMSMUNUPRQRRSRSQUP RRURVSVSURU'),
    'A': (-5, 5, 'RMNV RRMVV RPSTS'),
    'B': (-5, 5, 'OMOV ROMSMUNUPSQ ROQSQURUUSVOV'),
    'C': (-5, 6, 'VNTMRMPNOPOSPURVTVVU'),
    'D': (-5, 5, 'OMOV ROMRMTNUPUSTURVOV'),
    'E': (-5, 5, 'OMOV ROMUM ROQSQ ROVUV'),
    'F': (-5, 4, 'OMOV ROMUM ROQSQ'),
    'G': (-5, 6, 'VNTMRMPNOPOSPURVTVVUVR RSRVR'),
    'H': (-5, 5, 'OMOV RUMUV ROQUQ'),
    'I': (-2, 2, 'RMRV'),
    'J': (-4, 3, 'SMSTRVPVOTOS'),
    'K': (-5, 5, 'OMOV RUMOS RQQUV'),
    'L': (-5, 4, 'OMOV ROVUV'),
    'M': (-6, 6, 'NMNV RNMRV RVMRV RVMVV'),
    'N': (-5, 5, 'OMOV ROMUV RUMUV'),
    'O': (-5, 6, 'RMPNOPOSPURVSVUUVSVPUNSMRM'),
    'P': (-5, 5, 'OMOV ROMSMUNUQSROR'),
    'Q': (-5, 6, 'RMPNOPOSPURVSVUUVSVPUNSMRM RSTVW'),
    'R': (-5, 5, 'OMOV ROMSMUNUQSROR RRRUV'),
    'S': (-5, 5, 'UNSMQMONOOPPTRUSUUSVQVOU'),
    'T': (-5, 5, 'RMRV RNMVM'),
    'U': (-5, 6, 'OMOSPURVSVUUVSVM'),
    'V': (-5, 5, 'NMRV RVMRV'),
    'W': (-6, 6, 'NMPV RRMPV RRMTV RVMTV'),
    'X': (-5, 5, 'OMUV RUMOV'),
    'Y': (-5, 5, 'NMRQRV RVMRQ'),
    'Z': (-5, 5, 'UMOV ROMUM ROVUV'),
    'a': (-9, 10, 'XMX[ RXPVNTMQMONMPLSLUMXOZQ[T[VZXX'),
    'b': (-10, 9, 'LFL[ RLPNNPMSMUNWPXSXUWXUZS[P[NZLX'),
    'c': (-9, 9, 'XPVNTMQMONMPLSLUMXOZQ[T[VZXX'),
    'd': (-9, 10, 'XFX[ RXPVNTMQMONMPLSLUMXOZQ[T[VZXX'),
    'e': (-9, 9, 'LSXSXQWOVNTMQMONMPLSLUMXOZQ[T[VZXX'),
    'f': (-5, 7, 'WFUFSGRJR[ ROMVM'),
    'g': (-9, 10, 'XMX]W`VaTbQbOa RXPVNTMQMONMPLSLUMXOZQ[T[VZXX'),
    'h': (-9, 10, 'MFM[ RMQPNRMUMWNXQX['),
    'i': (-4, 4, 'QFRGSFREQF RRMR['),
    'j': (-5, 5, 'RFSGTFSERF RSMS^RaPbNb'),
    'k': (-9, 8, 'MFM[ RWMMW RQSX['),
    'l': (-4, 4, 'RFR['),
    'm': (-15, 15, 'GMG[ RGQJNLMOMQNRQR[ RRQUNWMZM\\N]Q]['),
    'n': (-9, 10, 'MMM[ RMQPNRMUMWNXQX['),
    'o': (-9, 10, 'QMONMPLSLUMXOZQ[T[VZXXYUYSXPVNTMQM'),
    'p': (-10, 9, 'LMLb RLPNNPMSMUNWPXSXUWXUZS[P[NZLX'),
    'q': (-9, 10, 'XMXb RXPVNTMQMONMPLSLUMXOZQ[T[VZXX'),
    'r': (-7, 6, 'OMO[ ROSPPRNTMWM'),
    's': (-8, 9, 'XPWNTMQMNNMPNRPSUTWUXWXXWZT[Q[NZMX'),
    't': (-5, 7, 'RFRWSZU[W[ ROMVM'),
    'u': (-9, 10, 'MMMWNZP[S[UZXW RXMX['),
    'v': (-8, 8, 'LMR[ RXMR['),
    'w': (-11, 11, 'JMN[ RRMN[ RRMV[ RZMV['),
    'x': (-8, 9, 'MMX[ RXMM['),
    'y': (-8, 8, 'LMR[ RXMR[P_NaLbKb'),
    'z': (-8, 9, 'XMM[ RMMXM RM[X['),
    '|': (-2, 2, 'RLRW'),
    '°': (-4, 4, 'QMPNPPQQSQTPTNSMQM'),
    '·': (-2, 3, 'RQRRSRSQRQ'),
    '×': (-5, 5, 'OOUU RUOOU'),
    '‘': (-2, 2, 'RMRQ'),
    '’': (-2, 2, 'RMRQ'),
    '“': (-4, 4, 'PMPQ RTMTQ'),
    '”': (-4, 4, 'PMPQ RTMTQ'),
    '•': (-2, 3, 'RQRRSRSQRQ'),
    '→': (-6, 6, 'SOVRSU RNRVR'),
    "€": (-6, 7, 'VNTMRMPNOPOSPURVTVVU RLPYP RLSYS'),
    '–': (-4, 4, 'ORUR'),
    '—': (-6, 6, 'MRWR'),
}


COMPLEX = {
    '!': (-4, 4, 'RKQLRSSLRK RRLRO RRVQWRXSWRV'),
    '"': (-6, 6, 'OKOP RPKOP RUKUP RVKUP'),
    '#': (-7, 7, 'RKN\\ RVKR\\ RNQWQ RMVVV'),
    '$': (-7, 8, 'QHQ\\ RTHT\\ RWLVLVMWMWLUKPKNLNNOPVSWT RNNOOVRWTWVVWTXQXOWNVNUOUOVNV'),
    '%': (-8, 8, 'XKLX ROKPLPNOOMOLNLLMKOKSLVLXK RUTTUTWUXWXXWXUWTUT'),
    '&': (-8, 9, 'YPXPXQYQYPXOWOVPUTTVSWQXOXMWLVLTMSORRPSNSLRKPKOLONPQUWWXXXYW ROXMVMTOR RONPPVWWX'),
    "'": (-3, 4, 'RKRP RSKRP'),
    '(': (-5, 5, 'UHSJQMPPPTQWSZU\\ RSJRLQPQTRXSZ'),
    ')': (-5, 5, 'OHQJSMTPTTSWQZO\\ RQJRLSPSTRXQZ'),
    '*': (-5, 5, 'RJRP ROKUO RUKOO'),
    '+': (-9, 9, 'RLRX RLRXR'),
    ',': (-4, 4, 'SWRXQWRVSWSYQ['),
    '-': (-9, 9, 'LRXR'),
    '.': (-4, 4, 'RVQWRXSWRV'),
    '/': (-7, 8, 'XHM\\'),
    '0': (-6, 7, 'QKOLNONTOWQXTXVWWTWOVLTKQK RQKPLOOOTPWQX RTXUWVTVOULTK'),
    '1': (-6, 7, 'PNSKSX RRLRX ROXVX'),
    '2': (-6, 7, 'OMONNNNMOLQKTKVLWNVPTQQROSNUNX RTKULVNUPTQ RNWOVPVSWVWWV RPVSXVXWVWU'),
    '3': (-6, 7, 'OMONNNNMOLQKTKVLWNVPTQ RTKULVNUPTQ RRQTQVRWTWUVWTXQXOWNVNUOUOV RTQURVTVUUWTX'),
    '4': (-6, 7, 'SMSX RTKTX RTKMTXT RQXVX'),
    '5': (-6, 7, 'OKNQ ROKVK ROLSLVK RNQOPQOTOVPWRWUVWTXQXOWNVNUOUOV RTOUPVRVUUWTX'),
    '6': (-6, 7, 'VMVNWNWMVLTKRKPLOMNPNUOWQXTXVWWUWSVQTPQPNR RRKPMOPOUPWQX RTXUWVUVSUQTP'),
    '7': (-6, 7, 'NKNO RVMRTPX RWKTQQX RNMPKRKUM RNMPLRLUMVM'),
    '8': (-6, 7, 'QKOLNNOPQQTQVPWNVLTKQK RQKPLONPPQQ RTQUPVNULTK RQQORNTNUOWQXTXVWWUWTVRTQ RQQPROTOUPWQX RTXUWVUVTURTQ'),
    '9': (-6, 7, 'OVOUNUNVOWQXSXUWVVWSWNVLTKQKOLNNNPORQSTSWQ RSXUVVSVNULTK RQKPLONOPPRQS'),
    ':': (-4, 4, 'ROQPRQSPRO RRVQWRXSWRV'),
    ';': (-4, 4, 'ROQPRQSPRO RSWRXQWRVSWSYQ['),
    '<': (-5, 5, 'THPRT\\'),
    '=': (-9, 9, 'LPXP RLTXT'),
    '>': (-5, 5, 'PHTRP\\'),
    '?': (-6, 7, 'NNONOONONNOLQKTKVLWNWOVQSRRSRTST RTKVMVPUQSR RRWRXSXSWRW'),
    '@': (-8, 9, 'UPSOQOPQPRQTSTUS RUOUSVTXTYRYQXNVLSKRKOLMNLQLRMUOWRXSXVW'),
    'A': (-7, 7, 'RKMX RRNVX RRKWX ROTTT RKXPX RTXYX'),
    'B': (-8, 8, 'NKNX ROKOX RLKSKVLWNVPSQ RSKULVNUPSQ ROQSQVRWTWUVWSXLX RSQURVTVUUWSX'),
    'C': (-7, 7, 'VLWKWOVLTKQKOLNMMPMSNVOWQXTXVWWU RQKOMNPNSOVQX'),
    'D': (-8, 8, 'NKNX ROKOX RLKSKVLWMXPXSWVVWSXLX RSKULVMWPWSVVUWSX'),
    'E': (-8, 7, 'NKNX ROKOX RSOSS RLKVKVOUK ROQSQ RLXVXVTUX'),
    'F': (-8, 6, 'NKNX ROKOX RSOSS RLKVKVOUK ROQSQ RLXQX'),
    'G': (-7, 9, 'VLWKWOVLTKQKOLNMMPMSNVOWQXTXVW RQKOMNPNSOVQX RTXUWVU RVSVX RWSWX RTSYS'),
    'H': (-8, 9, 'NKNX ROKOX RVKVX RWKWX RLKQK RTKYK ROQVQ RLXQX RTXYX'),
    'I': (-4, 5, 'RKRX RSKSX RPKUK RPXUX'),
    'J': (-6, 6, 'SKSURWQX RTKTUSWQXPXNWMUNTOUNV RQKVK'),
    'K': (-8, 8, 'NKNX ROKOX RWKOS RQQVX RRQWX RLKQK RTKYK RLXQX RTXYX'),
    'L': (-7, 6, 'OKOX RPKPX RMKRK RMXWXWTVX'),
    'M': (-9, 10, 'MKMX RNNRX RNKRU RWKRX RWKWX RXKXX RKKNK RWKZK RKXOX RUXZX'),
    'N': (-8, 8, 'NKNX ROMVX ROKVV RVKVX RLKOK RTKXK RLXPX'),
    'O': (-7, 8, 'QKOLNMMPMSNVOWQXTXVWWVXSXPWMVLTKQK RQKOMNPNSOVQX RTXVVWSWPVMTK'),
    'P': (-8, 7, 'NKNX ROKOX RLKSKVLWNWOVQSROR RSKULVNVOUQSR RLXQX'),
    'Q': (-7, 8, 'QKOLNMMPMSNVOWQXTXVWWVXSXPWMVLTKQK RQKOMNPNSOVQX RTXVVWSWPVMTK RPWPUQTSTTUUZV[W[XZ RTUUXVZW['),
    'R': (-8, 8, 'NKNX ROKOX RLKSKVLWNWOVQSROR RSKULVNVOUQSR RLXQX RSRTSUWVXWXXW RSRUSVWWX'),
    'S': (-7, 8, 'VMWKWOVMULSKQKOLNMNOOPQQTRVSWT RNNOOQPTQVRWSWVVWTXRXPWOVNTNXOV'),
    'T': (-7, 8, 'RKRX RSKSX RNKMOMKXKXOWK RPXUX'),
    'U': (-8, 9, 'NKNUOWQXTXVWWUWK ROKOUPWQX RLKQK RUKYK'),
    'V': (-7, 7, 'MKRX RNKRU RWKRX RKKPK RTKYK'),
    'W': (-9, 9, 'LKOX RMKOT RRKOX RRKUX RSKUT RXKUX RJKOK RVKZK'),
    'X': (-7, 8, 'NKVX ROKWX RWKNX RLKQK RTKYK RLXQX RTXYX'),
    'Y': (-6, 7, 'NKRRRX ROKSR RWKSRSX RLKQK RTKYK RPXUX'),
    'Z': (-6, 7, 'VKNX RWKOX ROKNONKWK RNXWXWTVX'),
    '[': (-5, 5, 'PHP\\ RQHQ\\ RPHUH RP\\U\\'),
    ']': (-5, 5, 'SHS\\ RTHT\\ ROHTH RO\\T\\'),
    'a': (-6, 8, 'QOPPPQOQOPQOTOVQVWWXXX RTOUQUWWX RURRSPTOUOWPXSXTWUU RRSPUPWQX'),
    'b': (-8, 7, 'NKNX ROKOX RORPPROTOVPWRWUVWTXRXPWOU RTOUPVRVUUWTX RLKOK'),
    'c': (-6, 6, 'VQUQURVRVQUPSOQOOPNRNUOWQXSXUWVV RQOPPOROUPWQX'),
    'd': (-6, 9, 'VKVX RWKWX RVRUPSOQOOPNRNUOWQXSXUWVU RQOPPOROUPWQX RTKWK RVXYX'),
    'e': (-6, 6, 'OSVSVRUPSOQOOPNRNUOWQXSXUWVV RUSUQSO RQOPPOROUPWQX'),
    'f': (-6, 5, 'TKULUMVMVLTKRKPMPX RRKQMQX RNOSO RNXSX'),
    'g': (-6, 7, 'QOOQOSQUSUUSUQSOQO RQOPQPSQU RSUTSTQSO RTPUOVO RPTOUOXPYTYVZ ROWPXTXVYV[T\\P\\N[NYPX'),
    'h': (-8, 9, 'NKNX ROKOX RORPPROTOVPWRWX RTOUPVRVX RLKOK RLXQX RTXYX'),
    'i': (-4, 5, 'RKRLSLSKRK RRORX RSOSX RPOSO RPXUX'),
    'j': (-4, 5, 'SKSLTLTKSK RSOSZR\\ RTOTZR\\P\\O[OZPZP[O[ RQOTO'),
    'k': (-8, 8, 'NKNX ROKOX RWOOU RRSVX RSSWX RLKOK RTOYO RLXQX RTXYX'),
    'l': (-4, 5, 'RKRX RSKSX RPKSK RPXUX'),
    'm': (-12, 13, 'JOJX RKOKX RKRLPNOPORPSRSX RPOQPRRRX RSRTPVOXOZP[R[X RXOYPZRZX RHOKO RHXMX RPXUX RXX]X'),
    'n': (-8, 9, 'NONX ROOOX RORPPROTOVPWRWX RTOUPVRVX RLOOO RLXQX RTXYX'),
    'o': (-6, 7, 'QOOPNRNUOWQXTXVWWUWRVPTOQO RQOPPOROUPWQX RTXUWVUVRUPTO'),
    'p': (-8, 7, 'NON\\ ROOO\\ RORPPROTOVPWRWUVWTXRXPWOU RTOUPVRVUUWTX RLOOO RL\\Q\\'),
    'q': (-7, 7, 'UOU\\ RVOV\\ RURTPROPONPMRMUNWPXRXTWUU RPOOPNRNUOWPX RS\\X\\'),
    'r': (-7, 6, 'OOOX RPOPX RPRQPSOUOVPVQUQUPVP RMOPO RMXRX'),
    's': (-6, 7, 'TOUPUQVQVPTOQOOPORQSTTVU ROQQRTSVTVWTXQXOWOVPVPWQX'),
    't': (-6, 5, 'PKPVRXTXUWUV RQKQVRX RNOTO'),
    'u': (-8, 9, 'NONUOWQXSXUWVU ROOOUPWQX RVOVX RWOWX RLOOO RTOWO RVXYX'),
    'v': (-7, 7, 'NORX ROORV RVORX RLOQO RTOXO'),
    'w': (-9, 9, 'LOOX RMOOU RROOX RROUX RSOUU RXOUX RJOOO RVOZO'),
    'x': (-7, 7, 'NOUX ROOVX RVONX RLOQO RTOXO RLXPX RSXXX'),
    'y': (-7, 7, 'NORX ROORV RVORXP[N\\M\\L[LZMZM[L[ RLOQO RTOXO'),
    'z': (-6, 6, 'UONX RVOOX ROONQNOVO RNXVXVVUX'),
    '{': (-6, 5, 'SHQIPJPLRNSP RQIPL RSNRQ RPJQLSNSPRQPRRSSTSVQXPZ RRSSV RPXQ[ RSTRVPXPZQ[S\\'),
    '|': (-3, 3, 'RHR\\'),
    '}': (-5, 6, 'QHSITJTLRNQP RSITL RQNRQ RTJSLQNQPRQTRRSQTQVSXTZ RRSQV RTXS[ RQTRVTXTZS[Q\\'),
    '°': (-5, 5, 'QKPLPNQOSOTNTLSKQK'),
    '·': (-4, 4, 'RQQRRSSRRQ'),
    '×': (-8, 8, 'MMWW RWMMW'),
    '‘': (-3, 4, 'RKRP RSKRP'),
    '’': (-3, 4, 'RKRP RSKRP'),
    '“': (-6, 6, 'OKOP RPKOP RUKUP RVKUP'),
    '”': (-6, 6, 'OKOP RPKOP RUKUP RVKUP'),
    '•': (-4, 4, 'RQQRRSSRRQ'),
    "€": (-8, 8, 'VLWKWOVLTKQKOLNMMPMSNVOWQXTXVWWU RQKOMNPNSOVQX RJQZQ RJTZT'),
    '–': (-4, 4, 'OSUS'),
    '—': (-6, 6, 'MSWS'),
}

METRICS = {"S": {'cap_top': -5, 'cap_bot': 5, 'low_top': -13, 'low_bot': 16}, "C": {'cap_top': -7, 'cap_bot': 9, 'low_top': -7, 'low_bot': 10}}


# ------------------------------------------------------------------ font core
def _disc_offsets(radius):
    """Cells of a filled disc of the given radius, offsets sorted by x,y."""
    cells = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                cells.append((dx, dy))
    return cells


def _glyph_segments(data, left, right):
    """Convert Hershey stroke data into (x1, y1, x2, y2) segments."""
    segments = []
    pen = None
    i = 0
    while i + 1 < len(data):
        a, b = data[i], data[i + 1]
        i += 2
        if a == ' ':
            pen = None
            continue
        x, y = ord(a) - ord('R'), ord(b) - ord('R')
        if pen is None:
            pen = (x, y)
            continue
        segments.append((pen[0], pen[1], x, y))
        pen = (x, y)
    return segments


class VecFont:
    """Hershey stroke font rendered as a 2x-supersampled coverage bitmap."""

    def __init__(self, glyphs, metrics, fallback=None):
        self.glyphs = glyphs
        self.metrics = metrics
        self.fallback = fallback
        self._seg_cache = {}
        self._glyph_cache = {}

    def _segments(self, ch):
        if ch not in self._seg_cache:
            data = self.glyphs.get(ch)
            if data is None:
                self._seg_cache[ch] = ()
            else:
                left, right, strokes = data
                self._seg_cache[ch] = (left, right, _glyph_segments(strokes, left, right))
        return self._seg_cache[ch]

    def glyph(self, ch, scale, thickness):
        """A glyph as a list of (dx, dy, coverage) over its own canvas."""
        key = (ch, scale, thickness)
        hit = self._glyph_cache.get(key)
        if hit is not None:
            return hit
        segs = self._segments(ch)
        if not segs:
            if self.fallback is not None:
                return self.fallback.glyph(ch, scale, thickness)
            return (0, 0, ())
        left, right, strokes = segs
        m = self.metrics
        top = m['cap_top'] if ch.isupper() or ch in '0123456789!?:;()[]{}&%+*=<>#|/' else m['low_top']
        bot = m['cap_bot'] if ch.isupper() or ch in '0123456789!?:;()[]{}&%+*=<>#|/' else m['low_bot']
        width = int(round((right - left) * scale)) + 2 * thickness + 1
        height = int(round((bot - top) * scale)) + 2 * thickness + 1
        sup = 2
        w = width * sup
        h = height * sup
        cover = [0.0] * (w * h)
        radius = max(1, int(round(thickness * sup)))
        disc = _disc_offsets(radius)
        for x1, y1, x2, y2 in strokes:
            steps = int(max(abs(x2 - x1), abs(y2 - y1)) * scale * sup) + 1
            for s in range(steps + 1):
                t = s / steps if steps else 0.0
                fx = (x1 + (x2 - x1) * t) * scale
                fy = (y1 + (y2 - y1) * t) * scale
                px = int(round((fx - left * scale) * sup)) + thickness * sup
                py = int(round((fy - top * scale) * sup)) + thickness * sup
                for dx, dy in disc:
                    qx, qy = px + dx, py + dy
                    if 0 <= qx < w and 0 <= qy < h:
                        cover[qy * w + qx] = 1.0
        pixels = []
        for y in range(height):
            for x in range(width):
                acc = 0.0
                for sy in range(sup):
                    for sx in range(sup):
                        acc += cover[(y * sup + sy) * w + x * sup + sx]
                cov = acc / (sup * sup) if disc else 0.0
                if cov > 0.02:
                    pixels.append((x, y, min(1.0, cov)))
        result = (width, height, tuple(pixels))
        self._glyph_cache[key] = result
        return result

    def text_width(self, text, scale, thickness=1):
        """Advance width of a string in output pixels."""
        width = 0
        for ch in text:
            if ch == ' ':
                width += int(round(9 * scale)) + 2 * thickness
                continue
            segs = self._segments(ch)
            if not segs:
                if self.fallback is not None:
                    width += self.fallback.text_width(ch, scale, thickness)
                continue
            left, right, _ = segs
            width += int(round((right - left) * scale)) + 2 * thickness + 1
        return width

    def draw(self, canvas, x, y, text, scale, color, thickness=1):
        """Draw text at top-left (x, y). Returns the advance width."""
        cx = x
        for ch in text:
            if ch == ' ':
                cx += int(round(9 * scale)) + 2 * thickness
                continue
            w, h, pixels = self.glyph(ch, scale, thickness)
            for dx, dy, cov in pixels:
                canvas.blend(cx + dx, y + dy, color, cov)
            cx += w
        return cx - x


class BitmapFont:
    """5x7 bitmap font, filled solid rectangles per inked cell."""

    def __init__(self, glyphs):
        self.glyphs = glyphs

    def text_width(self, text, scale, thickness=1):
        return len(text) * (5 * scale + scale)

    def draw(self, canvas, x, y, text, scale, color, thickness=1):
        cx = x
        for ch in text:
            rows = self.glyphs.get(ch)
            if rows:
                for ry, row in enumerate(rows):
                    for rx, cell in enumerate(row):
                        if cell == '1':
                            canvas.rect(cx + rx * scale, y + ry * scale, scale, scale, color)
            cx += 5 * scale + scale
        return cx - x


# Font instances: two Hershey vector faces; the sans face falls back to
# the serif face (which covers every sans glyph, so its fallback is None
# and the chain can never recurse). Plus a bitmap face for tiny labels.
VEC = VecFont(COMPLEX, METRICS["C"], None)
VEC_SANS = VecFont(SIMPLEX, METRICS["S"], VEC)
BMP = BitmapFont(BITMAP)


def draw_text(canvas, x, y, text, font, scale, color, thickness=1):
    return font.draw(canvas, x, y, text, scale, color, thickness)


def draw_text_c(canvas, cx, y, text, font, scale, color, thickness=1):
    w = font.text_width(text, scale, thickness)
    return font.draw(canvas, cx - w // 2, y, text, scale, color, thickness)


def wrap(text, font, scale, max_width, thickness=1):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines = []
    for para in text.split('\n'):
        words = para.split(' ')
        cur = ''
        for word in words:
            trial = (cur + ' ' + word) if cur else word
            if font.text_width(trial, scale, thickness) <= max_width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


def draw_para(canvas, x, y, text, font, scale, color, max_width, line_gap=0, thickness=1):
    """Draw wrapped paragraph at (x, y). Returns the y after the last line.

    Line height is the glyph box height (low_bot - low_top, so ascenders
    and descenders clear) plus line_gap — never less, or lines collide.
    """
    lines = wrap(text, font, scale, max_width, thickness)
    span = getattr(font, 'metrics', None)
    if span is not None:
        line_h = int(round((span['low_bot'] - span['low_top']) * scale)) + 2 * thickness + 1 + line_gap
    else:
        line_h = int(round(7 * scale)) + line_gap
    for line in lines:
        font.draw(canvas, x, y, line, scale, color, thickness)
        y += line_h
    return y


# ------------------------------------------------------------------- world map
# Continents as ellipses on a 46 x 29 cell grid (equirectangular:
# lon -180..180 across, lat 75..-60 down). Each tuple is
# (centre_col, centre_row, radius_x, radius_y). Rasterised into a land
# set by _land(); pins use the same linear lon/lat mapping, so they
# always land on the right continent.
LAND = [
    (8.5, 5.5, 7.5, 4.5),    # North America
    (17.5, 1.5, 2.5, 1.5),   # Greenland
    (10.5, 11.5, 2.0, 2.0),  # Central America
    (15.0, 19.0, 3.0, 6.5),  # South America
    (24.5, 4.5, 3.0, 2.5),   # Europe
    (25.5, 14.5, 4.0, 6.0),  # Africa
    (31.0, 7.0, 4.0, 3.0),   # Middle East / western Asia
    (37.0, 5.5, 8.0, 5.0),   # Asia (mainland)
    (33.5, 12.5, 1.8, 2.5),  # India
    (38.5, 13.5, 2.5, 1.8),  # South-East Asia
    (39.0, 16.5, 3.0, 1.0),  # Indonesia
    (39.5, 21.0, 3.0, 2.5),  # Australia
]


def _land(ellipses):
    """Rasterise continent ellipses into a set of (col, row) land cells."""
    cells = set()
    for cx, cy, rx, ry in ellipses:
        for r in range(max(0, int(cy - ry)), min(29, int(cy + ry) + 1)):
            for c in range(max(0, int(cx - rx)), min(46, int(cx + rx) + 1)):
                if ((c - cx) / rx) ** 2 + ((r - cy) / ry) ** 2 <= 1.0:
                    cells.add((c, r))
    return cells


def _rx(lon, x0, x1):
    """Longitude to x inside the map frame."""
    return int(round(x0 + (lon + 180.0) / 360.0 * (x1 - x0)))


def _ry(lat, y0, y1):
    """Latitude to y inside the map frame (north at top).

    Same range as the ellipse grid: lat 75 at the top row, -60 at the
    bottom row, so pins land on the land they belong to.
    """
    return int(round(y0 + (75.0 - lat) / 135.0 * (y1 - y0)))


def draw_map(canvas, x0, y0, x1, y1):
    """Paint the land mask as a solid sea-free outline."""
    cells = _land(LAND)
    cols = max(c for c, _ in cells) + 1
    rows = max(r for _, r in cells) + 1
    cw = (x1 - x0) / cols
    ch = (y1 - y0) / rows
    for c, r in cells:
        canvas.rect(int(round(x0 + c * cw)), int(round(y0 + r * ch)),
                    int(round(cw)) + 1, int(round(ch)) + 1, SEA)


def pin_xy(lon, lat, x0, y0, x1, y1):
    return _rx(lon, x0, x1), _ry(lat, y0, y1)


def draw_pin(canvas, x, y, n=None, color=RED):
    """A numbered pin: small filled disc with the story number in white."""
    canvas.disc(x, y, 6, color)
    if n is not None:
        label = str(n)
        w = VEC_SANS.text_width(label, 0.45, 1)
        VEC_SANS.draw(canvas, x - w // 2, y - 4, label, 0.45, PAPER, 1)


# ------------------------------------------------------------- illustrations
def art_hero_shenzhen(c, x, y, w, h):
    """Dusk over Shenzhen: sky gradient, gold sun, skyline, water reflection."""
    # Sky: warm amber band at the horizon fading to deep blue at the top.
    for i in range(h // 2):
        t = i / max(1, h // 2 - 1)
        col = _lerp_color((70, 60, 110), (245, 180, 90), t)
        c.hline(x, y + i, w, col)
    # Sun disc, low and gold, half-sunk into the skyline.
    cx, cy = x + w // 2, y + h // 2 - 8
    c.disc(cx, cy, 26, (255, 205, 90))
    c.circle(cx, cy, 30, (255, 220, 140))
    # Skyline silhouettes: Ping An Finance Centre (needle tower) centre,
    # flanked by stepped office blocks and a crane or two.
    base = y + h // 2
    towers = [
        (0.02, 0.30, 0.10, 0.55), (0.13, 0.42, 0.08, 0.62),
        (0.22, 0.55, 0.09, 0.55), (0.33, 0.70, 0.07, 0.62),
        (0.42, 0.52, 0.06, 0.55), (0.50, 0.88, 0.05, 0.30),
        (0.56, 0.48, 0.06, 0.58), (0.63, 0.60, 0.08, 0.52),
        (0.72, 0.40, 0.07, 0.66), (0.80, 0.52, 0.08, 0.55),
        (0.89, 0.38, 0.07, 0.60), (0.95, 0.30, 0.04, 0.55),
    ]
    for fx, fh, fw, _ in towers:
        tx = x + int(fx * w)
        tw = max(4, int(fw * w))
        th = int(fh * (h // 2))
        c.rect(tx, base - th, tw, th, (38, 34, 66))
    # Needle spire on the tallest tower.
    px = x + int(0.50 * w) + 2
    c.line(px, base - int(0.88 * (h // 2)), px, base - int(1.05 * (h // 2)), (38, 34, 66))
    # Windows: tiny lit dots scattered across the towers.
    for i, (fx, fh, fw, _) in enumerate(towers):
        tx = x + int(fx * w)
        tw = max(4, int(fw * w))
        th = int(fh * (h // 2))
        for wy in range(4, th - 4, 9):
            for wx in range(3, tw - 3, 7):
                if (i * 7 + wy * 3 + wx) % 5 == 0:
                    c.rect(tx + wx, base - wy, 2, 2, (255, 210, 120))
    # Water: dark blue with horizontal shimmer bands and a mirrored sun.
    for i in range(h // 2):
        t = i / max(1, h // 2 - 1)
        col = _lerp_color((30, 40, 90), (16, 22, 52), t)
        c.hline(x, base + i, w, col)
    for k in range(7):
        yy = base + 6 + k * 6
        ww = 60 - k * 6
        c.hline(cx - ww // 2, yy, ww, (255, 190, 100))
    # Three flags on poles above the waterline, left to right.
    flag_y = base + 6
    poles = [x + int(0.08 * w), x + int(0.20 * w), x + int(0.32 * w)]
    for p in poles:
        c.vline(p, flag_y - 26, 26, (220, 220, 220))
    # United States: red/white stripes, blue canton, white stars.
    fx, fy = poles[0] + 2, flag_y - 26
    for s in range(7):
        c.rect(fx, fy + s * 3, 34, 3, (178, 34, 52) if s % 2 == 0 else PAPER)
    c.rect(fx, fy, 15, 12, (30, 50, 110))
    for sy in range(3):
        for sx in range(4):
            c.rect(fx + 2 + sx * 3, fy + 2 + sy * 3, 1, 1, PAPER)
    # China: red field, one large gold star and four small ones.
    fx, fy = poles[1] + 2, flag_y - 26
    c.rect(fx, fy, 34, 21, (222, 41, 16))
    _star(c, fx + 7, fy + 6, 4, (255, 222, 0))
    for sx, sy in ((16, 3), (20, 6), (20, 11), (16, 14)):
        _star(c, fx + sx, fy + sy, 2, (255, 222, 0))
    # Russia: white-blue-red horizontal tricolour.
    fx, fy = poles[2] + 2, flag_y - 26
    c.rect(fx, fy, 34, 7, PAPER)
    c.rect(fx, fy + 7, 34, 7, (0, 57, 166))
    c.rect(fx, fy + 14, 34, 7, (213, 0, 50))


def art_gulf(c, x, y, w, h):
    """Strait of Hormuz: smoke columns over a dark sea, tanker silhouette."""
    # Sky: smoky grey-brown gradient, darker at the top.
    for i in range(h // 2):
        t = i / max(1, h // 2 - 1)
        col = _lerp_color((52, 48, 44), (150, 110, 80), t)
        c.hline(x, y + i, w, col)
    # Smoke columns rising from the horizon.
    for sx, sw in ((0.18, 14), (0.55, 18), (0.78, 12)):
        px = x + int(sx * w)
        for k in range(5):
            c.disc(px + (k % 2) * 6 - 3, y + h // 2 - 8 - k * 9, sw - k, (90, 84, 78))
    # Sun, dimmed behind the smoke.
    c.disc(x + int(0.42 * w), y + int(0.22 * h), 12, (230, 170, 110))
    # Sea: dark teal with lighter wave strokes.
    base = y + h // 2
    for i in range(h - h // 2):
        t = i / max(1, h - h // 2 - 1)
        col = _lerp_color((24, 52, 66), (12, 28, 40), t)
        c.hline(x, base + i, w, col)
    for k in range(4):
        yy = base + 6 + k * 8
        for wx in range(0, w, 26):
            c.hline(x + wx, yy, 14, (70, 110, 130))
    # Tanker: long dark hull, red waterline, white superstructure, funnel.
    hx, hy = x + int(0.10 * w), base + int(0.18 * h)
    hw, hh = int(0.80 * w), 16
    c.rect(hx, hy, hw, hh, (40, 34, 30))
    c.rect(hx, hy + hh - 4, hw, 4, (150, 50, 40))
    c.rect(hx + hw - int(0.18 * w), hy - 14, int(0.14 * w), 14, (210, 205, 195))
    c.rect(hx + hw - int(0.10 * w), hy - 26, int(0.05 * w), 12, (150, 50, 40))
    # Small flame licking from the deck amidships.
    c.disc(hx + int(0.45 * w), hy - 6, 6, (255, 150, 40))
    c.disc(hx + int(0.45 * w), hy - 3, 3, (255, 220, 90))


def art_ai(c, x, y, w, h):
    """Anthropic IPO: a rising bar chart under a gold arrow on deep blue."""
    c.rect(x, y, w, h, (18, 28, 66))
    # Faint grid lines.
    for k in range(1, 4):
        gy = y + k * h // 4
        for gx in range(x, x + w, 10):
            c.hline(gx, gy, 5, (60, 80, 130))
    # Rising bars: teal, gold, rust.
    bars = [(0.12, 0.30, TEAL), (0.30, 0.45, GOLD), (0.48, 0.58, RUST),
            (0.66, 0.74, (90, 170, 210))]
    base = y + h - 8
    for fx, fh, col in bars:
        bx = x + int(fx * w)
        bw = int(0.12 * w)
        bh = int(fh * (h - 16))
        c.rect(bx, base - bh, bw, bh, col)
        c.rect(bx, base - bh, bw, 3, PAPER)
    # Gold arrow sweeping up over the bars.
    ax0, ay0 = x + int(0.10 * w), base - int(0.20 * h)
    ax1, ay1 = x + int(0.88 * w), y + int(0.18 * h)
    c.line(ax0, ay0, ax1, ay1, GOLD)
    c.line(ax1, ay1, ax1 - 12, ay1 + 2, GOLD)
    c.line(ax1, ay1, ax1 - 2, ay1 + 12, GOLD)
    # Small gold star at the arrow tip.
    _star(c, ax1, ay1, 6, (255, 220, 120))


# ------------------------------------------------------------------- content
# 19 November 2026 — 35 stories, 6 continents. Sourced from live news
# reporting on the day; every figure below was reported that day.
# Stories are numbered 1-12 (lead + features + grid); the map pins carry
# the same numbers. ALSO items are 13-35. Bodies are short on purpose:
# the page is a newspaper front, headlines carry the news and bodies
# are one- or two-line elaborations (two lines max at the sizes used).
HERO = [
    {"n": 1, "kicker": "SUMMIT \u00b7 SHENZHEN",
     "headline": "TRUMP, XI AND PUTIN MEET",
     "body": "Trump, Xi and Putin open the first trilateral summit in history "
             "at APEC in Shenzhen, with nuclear arms, Ukraine and Iran on "
             "the agenda.",
     "art": "shenzhen", "pin": (114.1, 22.5)},
    {"n": 2, "kicker": "GULF \u00b7 CONFLICT",
     "headline": "US\u2013IRAN STRIKES WIDEN",
     "body": "Iran hits US bases again; US hits back.",
     "art": "gulf", "pin": (47.5, 29.3)},
    {"n": 3, "kicker": "MARKETS \u00b7 IPO",
     "headline": "ANTHROPIC IPO AT $79.4BN",
     "body": "Anthropic lists in a record AI debut.",
     "art": "ai", "pin": (-122.4, 37.8)},
]

SMALL = [
    {"n": 4, "kicker": "GAZA \u00b7 AID CRISIS",
     "headline": "FLOODS SWAMP GAZA CAMPS",
     "body": "Storms displace 46,000 households; aid waits.",
     "pin": (34.5, 31.5)},
    {"n": 5, "kicker": "ISRAEL \u00b7 POLITICS",
     "headline": "HERZOG TAPS EISENKOT TO GOVERN",
     "body": "Herzog bypasses Netanyahu; Kahana is speaker.",
     "pin": (35.2, 31.8)},
    {"n": 6, "kicker": "EUROPE \u00b7 SECURITY",
     "headline": "ESTONIA TO SHUT BORDER WITH RUSSIA",
     "body": "Tallinn shuts road crossings from 1 December.",
     "pin": (27.5, 59.0)},
    {"n": 7, "kicker": "YEMEN \u00b7 WAR",
     "headline": "HOUTHIS SEIZE RED SEA COAST",
     "body": "Rebels take coast posts as troops withdraw.",
     "pin": (43.3, 12.6)},
    {"n": 8, "kicker": "TECH \u00b7 GAMES",
     "headline": "GTA VI ROLLS OUT WORLDWIDE",
     "body": "Rockstar's Vice City return launches worldwide.",
     "pin": (-80.2, 25.8)},
    {"n": 9, "kicker": "EUROPE \u00b7 UKRAINE",
     "headline": "EU PROPOSES \u20ac45BN UKRAINE LOAN",
     "body": "Brussels tables a loan repaid after reparations.",
     "pin": (4.4, 50.8)},
    {"n": 10, "kicker": "ASIA \u00b7 CHIPS",
     "headline": "NVIDIA HALTS H-SERIES CHIPS TO CHINA",
     "body": "H-series shipments stop; Kress promises raises.",
     "pin": (116.4, 39.9)},
    {"n": 11, "kicker": "ASIA \u00b7 LABOUR",
     "headline": "BANGLADESH GARMENT PROTESTS",
     "body": "Workers demand a 30,000-taka minimum wage.",
     "pin": (90.4, 23.8)},
    {"n": 12, "kicker": "ASIA \u00b7 WEATHER",
     "headline": "CYCLONE AKVAN NEARS ODISHA",
     "body": "Schools close as the storm bears down.",
     "pin": (85.8, 20.3)},
]

# NUMBERS: (big figure, label) — the day in four numbers.
NUMBERS = [
    ("$79.4BN", "ANTHROPIC IPO VALUE"),
    ("46,000", "DISPLACED IN GAZA"),
    ("\u20ac45BN", "EU LOAN FOR UKRAINE"),
    ("150,000", "TENTS AWAITING ENTRY"),
]

# ALSO: (number, place, short text) — 23 more stories, one line each.
ALSO = [
    (13, "COP31", "Talks near finale"),
    (14, "Voyager", "A light-day out"),
    (15, "Fed", "Minutes point to rises"),
    (16, "Myanmar", "Rethinks ASEAN ties"),
    (17, "Argentina", "Parana floods"),
    (18, "Ethiopia", "Troops at border"),
    (19, "Siberia", "Crash kills 19"),
    (20, "France", "Protests, week four"),
    (21, "Spain", "General strike"),
    (22, "Prague", "Media freedom march"),
    (23, "India", "Japan 2+2 talks"),
    (24, "Delhi", "Schools reopen"),
    (25, "US", "Liu to chair House Dems"),
    (26, "Venezuela", "$12bn oil revenue"),
    (27, "Canada", "China ties adjusted"),
    (28, "Markets", "Goldman lifts India"),
    (29, "India", "162.5% Scotch duty"),
    (30, "Microsoft", "ByteDance talks"),
    (31, "Abu Dhabi", "Drone strikes"),
    (32, "Germany", "Hybrid threats"),
    (33, "Cricket", "India\u2013NZ Test"),
    (34, "Senate", "AI cyber threats grow"),
    (35, "Saudi", "Danger passed"),
]

# ------------------------------------------------------------------ helpers
def _lerp_color(c1, c2, t):
    """Linear blend between two RGB colours; t in [0, 1]."""
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def _star(c, cx, cy, r, color):
    """Five-point star outline, drawn as five lines."""
    pts = []
    for k in range(5):
        ang = -math.pi / 2 + k * 2 * math.pi / 5
        pts.append((cx + int(round(r * math.cos(ang))),
                    cy + int(round(r * math.sin(ang)))))
    order = (0, 2, 4, 1, 3, 0)
    for a, b in zip(order, order[1:]):
        c.line(pts[a][0], pts[a][1], pts[b][0], pts[b][1], color)


def _fit_scale(text, font, start, max_w, thickness=1, floor=0.8):
    """Largest scale <= start (step 0.05) whose width fits max_w."""
    scale = start
    while scale > floor and font.text_width(text, scale, thickness) > max_w:
        scale = round(scale - 0.05, 2)
    return scale


# -------------------------------------------------------------------- build
def build():
    c = Canvas(W, H, PAPER)

    # Masthead (auto-fit from cap 46) and rules.
    ms = _fit_scale("THE DAY IN WORLD NEWS", VEC, 46.0 / 17.0, 976, 2)
    draw_text_c(c, W // 2, 10, "THE DAY IN WORLD NEWS", VEC, ms, INK, 2)
    c.fill(24, 68, 976, 3, INK)
    c.fill(24, 75, 976, 1, INK)
    # Dateline row.
    draw_text(c, 24, 85, "THURSDAY, 19 NOVEMBER 2026", VEC_SANS, 1.1, INK, 1)
    right = "35 STORIES \u00b7 6 CONTINENTS \u00b7 ONE PAGE"
    rw = VEC_SANS.text_width(right, 1.1, 1)
    draw_text(c, 1000 - rw, 85, right, VEC_SANS, 1.1, INK, 1)
    c.fill(24, 106, 976, 1, INK)

    # Lead story: number disc, kicker, giant one-line headline.
    lead = HERO[0]
    c.disc(34, 126, 10, BRICK)
    nw = VEC_SANS.text_width("1", 1.1, 1)
    VEC_SANS.draw(c, 34 - nw // 2, 120, "1", 1.1, PAPER, 1)
    draw_text(c, 50, 118, lead["kicker"], VEC_SANS, 1.2, RED, 1)
    hs = _fit_scale(lead["headline"], VEC, 36.0 / 17.0, 976, 2)
    draw_text_c(c, W // 2, 138, lead["headline"], VEC, hs, INK, 2)

    # Hero illustration, full width, with the lead body as its caption.
    hero_y = 178
    art_hero_shenzhen(c, 24, hero_y, 976, 170)
    c.outline(24, hero_y, 976, 170, INK)
    cap = "Illustration \u2014 " + lead["body"]
    draw_para(c, 24, 355, cap, VEC, 11.0 / 17.0, MUTED, 976, 0, 1)
    c.fill(24, 390, 976, 3, INK)

    # Two feature cards, stories 2 and 3.
    fy = 398
    card_h = 116
    for i, cx in enumerate((24, 518)):
        s = HERO[1 + i]
        c.fill(cx, fy, 482, card_h, CARD)
        c.outline(cx, fy, 482, card_h, INK)
        if s["art"] == "gulf":
            art_gulf(c, cx + 8, fy + 8, 176, card_h - 16)
        else:
            art_ai(c, cx + 8, fy + 8, 176, card_h - 16)
        c.vline(cx + 192, fy + 8, card_h - 16, MUTED)
        tx = cx + 204
        tw = 482 - 204 - 10
        c.disc(tx + 9, fy + 19, 9, BRICK)
        nw = VEC_SANS.text_width(str(s["n"]), 1.0, 1)
        VEC_SANS.draw(c, tx + 9 - nw // 2, fy + 14, str(s["n"]), 1.0, PAPER, 1)
        draw_text(c, tx + 24, fy + 14, s["kicker"], VEC_SANS, 1.0, RED, 1)
        hlines = wrap(s["headline"], VEC, 17.0 / 17.0, tw, 1)[:2]
        hy = draw_para(c, tx, fy + 29, "\n".join(hlines), VEC, 17.0 / 17.0, INK, tw, 0, 1)
        blines = wrap(s["body"], VEC, 12.0 / 17.0, tw, 1)[:2]
        draw_para(c, tx, hy + 4, "\n".join(blines), VEC, 12.0 / 17.0, INK, tw, 0, 1)

    # Dense columns, stories 4 to 12, three rows of three.
    dy = fy + card_h + 12
    row_h = 80
    for r in range(3):
        for col in range(3):
            s = SMALL[r * 3 + col]
            x = 24 + col * 329
            yy = dy + r * row_h
            c.disc(x + 8, yy + 11, 8, BRICK)
            nscale = 0.9 if s["n"] < 10 else 0.7
            nw = VEC_SANS.text_width(str(s["n"]), nscale, 1)
            VEC_SANS.draw(c, x + 8 - nw // 2, yy + 7, str(s["n"]), nscale, PAPER, 1)
            draw_text(c, x + 22, yy + 5, s["kicker"], VEC_SANS, 0.9, RED, 1)
            hlines = wrap(s["headline"], VEC, 13.0 / 17.0, 309, 1)[:2]
            hy = draw_para(c, x, yy + 19, "\n".join(hlines), VEC, 13.0 / 17.0, INK, 309, 0, 1)
            blines = wrap(s["body"], VEC, 11.0 / 17.0, 309, 1)[:2]
            draw_para(c, x, hy + 4, "\n".join(blines), VEC, 11.0 / 17.0, INK, 309, 0, 1)
    c.vline(345, dy, 3 * row_h, MUTED)
    c.vline(674, dy, 3 * row_h, MUTED)

    # BY THE NUMBERS strip.
    ny = dy + 3 * row_h + 10
    c.fill(24, ny, 976, 36, CREAM)
    c.outline(24, ny, 976, 36, INK)
    draw_text(c, 36, ny + 5, "BY THE", VEC_SANS, 1.0, RED, 1)
    draw_text(c, 36, ny + 19, "NUMBERS", VEC_SANS, 1.0, RED, 1)
    c.vline(112, ny + 5, 26, MUTED)
    for i, (fig, lab) in enumerate(NUMBERS):
        cx = 124 + i * 219 + 109
        draw_text_c(c, cx, ny + 2, fig, VEC, 17.0 / 17.0, INK, 1)
        draw_text_c(c, cx, ny + 22, lab, VEC, 9.0 / 17.0, MUTED, 1)
        if i:
            c.vline(124 + i * 219, ny + 5, 26, MUTED)

    # Bottom band: map card on the left, ALSO list on the right.
    by = ny + 36 + 10
    bh = 156
    c.fill(24, by, 300, bh, CARD)
    c.outline(24, by, 300, bh, INK)
    draw_text(c, 36, by + 7, "WHERE THE NEWS HAPPENED", VEC_SANS, 0.85, INK, 1)
    draw_text(c, 36, by + 23, "Dots mark stories 1\u201312.", VEC, 10.0 / 17.0, MUTED, 1)
    mx0, my0, mx1, my1 = 40, by + 42, 270, by + 129
    draw_map(c, mx0, my0, mx1, my1)
    for s in HERO + SMALL:
        px, py = pin_xy(s["pin"][0], s["pin"][1], mx0, my0, mx1, my1)
        if s["n"] == 5:  # Jerusalem sits on Gaza's pin; nudge it clear.
            px += 9
            py -= 6
        draw_pin(c, px, py, s["n"])
    c.fill(336, by, 664, bh, CARD)
    c.outline(336, by, 664, bh, INK)
    draw_text(c, 348, by + 7, "ALSO ON 19 NOVEMBER \u2014 23 MORE STORIES", VEC_SANS, 1.1, INK, 1)
    for i, (n, place, text) in enumerate(ALSO):
        col = 0 if i < 12 else 1
        row = i if i < 12 else i - 12
        ix = 348 + col * 332
        iy = by + 21 + row * 11
        draw_text(c, ix, iy, "%d. %s \u2013 %s" % (n, place, text), VEC, 8.0 / 17.0, INK, 1)

    # Footer.
    fy2 = by + bh + 8
    c.fill(24, fy2, 976, 3, INK)
    draw_text(c, 24, fy2 + 7, "Sources: AP \u00b7 Reuters \u00b7 AFP \u00b7 BBC \u00b7 Al Jazeera \u00b7 UN News. Original drawings.", VEC, 10.0 / 17.0, MUTED, 1)
    draw_text(c, 24, fy2 + 20, "The world in one picture \u2013 35 stories from Thursday 19 November 2026.", VEC, 10.0 / 17.0, MUTED, 1)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", ".")
    os.makedirs(out_dir, exist_ok=True)
    canvas = build()
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(canvas.png_bytes())


if __name__ == "__main__":
    main()
