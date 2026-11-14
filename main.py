#!/usr/bin/env python3
"""news-image-01 entry: one image summing up the world's news of Friday 13 November 2026.

The program reassembles base.png from the base.NN chunk files shipped in
this repository (the 1024x1024 editorial montage illustration, split only so
each file stays small), then composites crisp editorial labels over it with a
built-in 5x7 bitmap font:

  title   "FRIDAY 13 NOVEMBER 2026" / "THE WORLD IN ONE DAY"
  panels  SENATE SUMMONS HUANG & LUTNICK | ZELENSKY MEETS US ENVOYS
          DRONE HITS RUSSIAN WARSHIP    | IRAN CLAIMS BAHRAIN STRIKE
          FBI: N. KOREA $400M HEIST    | KANE BREAKS ENGLAND RECORD
  ticker  US REPORTS RECORD 483,200 DEPORTATIONS IN 2026

The seven stories are exactly the ones the competition kit names from the
BBC / Al Jazeera reports of 13 November 2026. The output is written to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png). Pure Python 3.13
standard library, no network, fully deterministic: two runs write identical
bytes. Output is a whole PNG of at most 1 MiB and 1024 by 1024 pixels.
"""

import os
import struct
import zlib
from pathlib import Path

# 5x7 bitmap font: each glyph is 7 rows of 5 bits ('1' = ink). Verified by
# rendering a test strip; every label below uses only these characters.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "10011", "10011"),
}


class Image:
    """A flat RGB bytearray, row-major."""

    def __init__(self, width, height, pixels=None):
        self.width = width
        self.height = height
        self.pixels = pixels if pixels is not None else bytearray(width * height * 3)

    def set(self, x, y, rgb):
        if 0 <= x < self.width and 0 <= y < self.height:
            o = (y * self.width + x) * 3
            self.pixels[o:o + 3] = bytes(rgb)

    def fill_rect(self, x, y, w, h, rgb):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.width, x + w), min(self.height, y + h)
        row = bytes(rgb) * (x1 - x0)
        for yy in range(y0, y1):
            o = (yy * self.width + x0) * 3
            self.pixels[o:o + len(row)] = row


def draw_text(img, x, y, text, scale, rgb):
    """Draw text with the 5x7 font; (x, y) is the top-left of the first glyph."""
    cx = x
    for ch in text:
        glyph = FONT.get(ch)
        if glyph is None:
            raise ValueError(f"no glyph for {ch!r}")
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "1":
                    img.fill_rect(cx + col * scale, y + row * scale,
                                  scale, scale, rgb)
        cx += (5 + 1) * scale
    return cx - x


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * (5 + 1) * scale - scale


def draw_text_centered(img, cx, y, text, scale, rgb):
    draw_text(img, cx - text_width(text, scale) // 2, y, text, scale, rgb)


# --- PNG decoding (8-bit RGB / RGBA, non-interlaced) ------------------------
def decode_png(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos = 8
    width = height = bitdepth = ctype = interlace = None
    idat = bytearray()
    while pos < len(data):
        (ln, typ) = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            width, height, bitdepth, ctype, _, _, interlace = struct.unpack(
                ">IIBBBBB", chunk[:13])
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if bitdepth != 8 or ctype not in (2, 6) or interlace != 0:
        raise ValueError(f"unsupported PNG: bitdepth={bitdepth} ctype={ctype} "
                         f"interlace={interlace}")
    channels = 3 if ctype == 2 else 4
    stride = width * channels
    raw = zlib.decompress(bytes(idat))
    img = Image(width, height)
    prev = bytearray(stride)
    for y in range(height):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if f == 1:
            for i in range(channels, len(line)):
                line[i] = (line[i] + line[i - channels]) & 255
        elif f == 2:
            for i in range(len(line)):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(len(line)):
                a = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(len(line)):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        elif f != 0:
            raise ValueError(f"unknown PNG filter {f}")
        dst = y * width * 3
        if channels == 3:
            img.pixels[dst:dst + stride] = line
        else:
            for x in range(width):
                s = x * 4
                img.pixels[dst + x * 3:dst + x * 3 + 3] = line[s:s + 3]
        prev = line
    return img


# --- PNG encoding (8-bit RGB, best of None/Sub/Up per row, zlib level 9) ----
def _filter_row(kind, line, prev, channels=3):
    out = bytearray(len(line))
    if kind == 0:
        out[:] = line
    elif kind == 1:
        for i in range(len(line)):
            a = line[i - channels] if i >= channels else 0
            out[i] = (line[i] - a) & 255
    elif kind == 2:
        for i in range(len(line)):
            out[i] = (line[i] - prev[i]) & 255
    return out


def _signed_size(filt):
    return sum(b if b < 128 else 256 - b for b in filt)


def _chunk(typ, payload):
    out = struct.pack(">I", len(payload)) + typ + payload
    out += struct.pack(">I", zlib.crc32(typ + payload) & 0xFFFFFFFF)
    return out


def encode_png(img):
    w, h = img.width, img.height
    stride = w * 3
    prev = bytearray(stride)
    body = bytearray()
    for y in range(h):
        line = img.pixels[y * stride:(y + 1) * stride]
        best_kind, best_score, best_filt = 0, None, None
        for kind in (0, 1, 2):
            filt = _filter_row(kind, line, prev)
            score = _signed_size(filt)
            if best_score is None or score < best_score:
                best_kind, best_score, best_filt = kind, score, filt
        body.append(best_kind)
        body += best_filt
        prev = line
    out = b"\x89PNG\r\n\x1a\n"
    out += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    out += _chunk(b"IDAT", zlib.compress(bytes(body), 9))
    out += _chunk(b"IEND", b"")
    return out


# --- layout (final image is 1024x1024; all coordinates in that space) -------
NAVY = (10, 18, 38)
GOLD = (212, 175, 55)
WHITE = (255, 255, 255)
TITLE = "FRIDAY 13 NOVEMBER 2026"
SUBTITLE = "THE WORLD IN ONE DAY"
TICKER = "US REPORTS RECORD 483,200 DEPORTATIONS IN 2026"
# (x, y, width, line 1, line 2) — bands sit on the bottom edge of each panel
BANDS = [
    (38, 307, 359, "SENATE SUMMONS", "HUANG & LUTNICK"),
    (38, 576, 359, "ZELENSKY MEETS", "US ENVOYS"),
    (38, 844, 359, "DRONE HITS", "RUSSIAN WARSHIP"),
    (690, 307, 280, "IRAN CLAIMS", "BAHRAIN STRIKE"),
    (690, 576, 280, "FBI: N. KOREA", "$400M CRYPTO HACK"),
    (690, 844, 280, "KANE BREAKS", "ENGLAND RECORD"),
]
BAND_H = 58


def compose(img):
    # title block (top empty sky)
    draw_text_centered(img, 512, 22, TITLE, 6, WHITE)
    draw_text_centered(img, 512, 78, SUBTITLE, 3, GOLD)
    # lower-third label bands on each story panel
    for (x, y, w, line1, line2) in BANDS:
        img.fill_rect(x, y, w, BAND_H, NAVY)
        img.fill_rect(x, y, w, 3, GOLD)
        draw_text_centered(img, x + w // 2, y + 9, line1, 3, WHITE)
        draw_text_centered(img, x + w // 2, y + 34, line2, 3, WHITE)
    # bottom ticker (the seventh story, in the empty strip)
    img.fill_rect(0, 910, 1024, 3, GOLD)
    draw_text_centered(img, 512, 940, TICKER, 3, WHITE)


def load_base(here):
    """Reassemble base.png from the base.NN chunk files in order."""
    parts = sorted(here.glob("base.*"))
    if not parts:
        raise SystemExit("no base.NN chunk files found beside main.py")
    data = bytearray()
    for p in parts:
        data += p.read_bytes()
    return bytes(data)


def main():
    here = Path(__file__).resolve().parent
    img = decode_png(load_base(here))
    if (img.width, img.height) != (1024, 1024):
        raise SystemExit(f"unexpected base size {img.width}x{img.height}")
    compose(img)
    out = encode_png(img)
    if len(out) > 1048576:
        raise SystemExit(f"output too large: {len(out)} bytes (cap 1048576)")
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "entry.png").write_bytes(out)
    print(f"wrote {out_dir / 'entry.png'} ({len(out)} bytes, "
          f"{img.width}x{img.height})")


if __name__ == "__main__":
    main()
