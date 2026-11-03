"""Draw the app icons (the amber ring on navy) for 'install to home screen'.

Run once from the project folder:   python tools/make_icons.py
Writes PNG files into items/static/items/icons/
"""
from pathlib import Path

from PIL import Image, ImageDraw

NAVY = (20, 33, 61, 255)       # #14213D
AMBER = (242, 169, 0, 255)     # #F2A900
OUT = Path(__file__).resolve().parent.parent / "items" / "static" / "items" / "icons"
SCALE = 4                      # draw big, then shrink, for smooth edges


def draw_icon(size, rounded):
    """Navy square with an amber ring. `rounded` leaves transparent corners."""
    big = size * SCALE
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if rounded:
        d.rounded_rectangle([0, 0, big - 1, big - 1], radius=big * 0.22, fill=NAVY)
    else:
        d.rectangle([0, 0, big, big], fill=NAVY)   # full-bleed: the phone crops the shape

    # The ring stays inside the middle 60% so cropping never cuts it.
    cx = cy = big / 2
    outer = big * 0.27
    inner = big * 0.145
    d.ellipse([cx - outer, cy - outer, cx + outer, cy + outer], fill=AMBER)
    d.ellipse([cx - inner, cy - inner, cx + inner, cy + inner], fill=NAVY)

    return img.resize((size, size), Image.Resampling.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "icon-192.png": (192, True),
        "icon-512.png": (512, True),
        "icon-maskable-512.png": (512, False),
        "apple-touch-icon.png": (180, False),   # iPhones round the corners themselves
    }
    for name, (size, rounded) in files.items():
        draw_icon(size, rounded).save(OUT / name, optimize=True)
        print("wrote", OUT / name)


if __name__ == "__main__":
    main()