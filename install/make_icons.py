"""Generate the Polony Review icons (needs Pillow). Run: python install/make_icons.py

Writes install/assets/PolonyReview.png (512 px), PolonyReview.ico (multi-size) and PolonyReview.icns.
The design is the PoCo logo mark: a red and a green circle whose overlap is yellow, on a white rounded square.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

OUT = Path(__file__).resolve().parent / "assets"
RED, GREEN, YELLOW = (222, 72, 75, 255), (53, 155, 115, 255), (244, 201, 80, 255)
WHITE, EDGE = (255, 255, 255, 255), (222, 226, 232, 255)
S = 1024  # master size (supersampled, then downscaled)


def _disc(cx: float, cy: float, r: float) -> Image.Image:
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    return m


def master() -> Image.Image:
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((32, 32, S - 32, S - 32), radius=220, fill=WHITE, outline=EDGE, width=8)
    # logo mark: two circles of radius r, centres r apart (about); the overlap is a white-rimmed yellow lens
    r = 215.0
    dx = r * 1.01
    cy = S / 2
    lx, rx = S / 2 - dx / 2, S / 2 + dx / 2
    for cx, col in ((lx, RED), (rx, GREEN)):
        im.paste(col, (0, 0), _disc(cx, cy, r))
    im.paste(WHITE, (0, 0), ImageChops.multiply(_disc(lx, cy, r), _disc(rx, cy, r)))
    ri = r * 0.87
    im.paste(YELLOW, (0, 0), ImageChops.multiply(_disc(lx, cy, ri), _disc(rx, cy, ri)))
    return im


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    m = master()
    m.resize((512, 512), Image.LANCZOS).save(OUT / "PolonyReview.png")
    sizes = [16, 24, 32, 48, 64, 128, 256]
    m.save(OUT / "PolonyReview.ico", format="ICO", sizes=[(s, s) for s in sizes])
    m.save(OUT / "PolonyReview.icns", format="ICNS")
    for f in sorted(OUT.iterdir()):
        print(f"{f.name}: {f.stat().st_size} bytes")


if __name__ == "__main__":
    main()
