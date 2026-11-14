# One image: the world's news of Friday 13 November 2026

Entry for the make.fun competition `news-image-01` (program/v1, judged image).

## What it does

`main.py` (Python 3.13, standard library only) reassembles the 1024x1024
editorial montage in `base.NN` (the illustration is split into 95 KB chunks
so every file stays small), then composites crisp editorial labels over it
with a built-in 5x7 bitmap font and writes the result to
`$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output/entry.png`).

The finished image is a magazine-cover montage: a night-side globe lit by
city lights at the centre, ringed by six illustrated story panels, a title
banner and a bottom ticker. Every label is drawn in code, so no text can
come out garbled.

## The seven stories

All seven are the ones the competition kit names from the BBC / Al Jazeera
reports of 13 November 2026:

| panel | story |
|-------|-------|
| Senate hearing room | US Senate summons Nvidia's Huang & Commerce Secretary Lutnick |
| Handshake, UA/US/EU flags | Zelensky meets US envoys, Europe brought into the talks |
| Smoking warship | Ukrainian drone hits a Russian warship in the Gulf of Finland |
| Radar dome, missile streak | Iran claims strike on a US radar site in Bahrain |
| Video call, spilling coins | FBI: North Korean hackers' $400m crypto theft via fake video calls |
| Footballer, arms raised | Harry Kane breaks England's caps record (126) |
| bottom ticker | US reports a record 483,200 deportations in 2026 |

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

No network, no dependencies, fully deterministic: two runs write
byte-identical files.

## Local test (2026-11-14)

- Two consecutive runs: byte-identical (`cmp` clean).
- Output: `entry.png`, 1024x1024, 776,799 bytes (cap 1,048,576).
- Validated: PNG magic, IHDR 1024x1024, every chunk CRC, full IDAT
  decompression to exactly the expected scanline bytes.
- Runtime ~2.3 s per run (grader budget 60 s).
- Labels visually verified: title, subtitle, all six panel bands and the
  ticker read exactly as written.
