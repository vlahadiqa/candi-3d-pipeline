"""Turn a photo (e.g. pusaka3d-main/bukti/kontak_foto.jpg) into the model's texture: data/mytex.ppm.

A contact sheet holds many thumbnails; pick ONE patch of stone/relief:

  python make_mytexture.py --img "C:/.../pusaka3d-main/bukti/kontak_foto.jpg" --info
        -> prints the image size (and writes out/mytex_sheet_grid.png with a numbered grid to read cell numbers)
  python make_mytexture.py --img "...kontak_foto.jpg" --grid 3 4 --cell 1 2
        -> grid of 3 rows x 4 columns, take the cell at row 1, column 2 (0-based)
  python make_mytexture.py --img "...kontak_foto.jpg" --crop 120 80 420 380
        -> explicit pixel box: left top right bottom
  (no selection: centre square of the whole image)

Output: data/mytex.ppm (256x256, power of two so the 4-level mipmap halves cleanly) and
out/mytex_preview.png -- LOOK at the preview before using it.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

from ppm_io import write_ppm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", required=True)
    ap.add_argument("--out", default="data/mytex.ppm")
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--crop", type=int, nargs=4, metavar=("L", "T", "R", "B"))
    ap.add_argument("--grid", type=int, nargs=2, metavar=("ROWS", "COLS"))
    ap.add_argument("--cell", type=int, nargs=2, metavar=("ROW", "COL"))
    ap.add_argument("--info", action="store_true")
    a = ap.parse_args()
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        sys.exit("needs Pillow: pip install pillow")
    if a.size & (a.size - 1):
        sys.exit("--size must be a power of two")
    im = Image.open(a.img).convert("RGB")
    W, H = im.size
    print(f"{a.img}: {W}x{H}")
    os.makedirs("out", exist_ok=True)
    if a.info or (a.grid and not a.cell):
        r, c = a.grid if a.grid else (3, 4)
        g = im.copy(); d = ImageDraw.Draw(g)
        for i in range(r):
            for j in range(c):
                x0, y0 = j * W // c, i * H // r
                d.rectangle([x0, y0, (j + 1) * W // c - 1, (i + 1) * H // r - 1], outline=(255, 0, 0), width=2)
                d.text((x0 + 6, y0 + 6), f"r{i} c{j}", fill=(255, 255, 0))
        g.save("out/mytex_sheet_grid.png")
        print(f"wrote out/mytex_sheet_grid.png ({r}x{c} grid, labels = row/col, 0-based). Open it, pick a cell, re-run with --grid {r} {c} --cell ROW COL")
        if a.info:
            return
    if a.crop:
        box = tuple(a.crop)
    elif a.grid and a.cell:
        r, c = a.grid; i, j = a.cell
        box = (j * W // c, i * H // r, (j + 1) * W // c, (i + 1) * H // r)
    else:
        s = min(W, H); box = ((W - s) // 2, (H - s) // 2, (W + s) // 2, (H + s) // 2)
    L, T, R, B = box
    side = min(R - L, B - T)                               # force a square patch (no stretching)
    cx, cy = (L + R) // 2, (T + B) // 2
    box = (cx - side // 2, cy - side // 2, cx - side // 2 + side, cy - side // 2 + side)
    print(f"cropped box {box} ({side}x{side}) -> {a.size}x{a.size}")
    t = im.crop(box).resize((a.size, a.size), Image.LANCZOS)
    arr = np.asarray(t, dtype=np.uint8)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    write_ppm(a.out, arr)
    t.save("out/mytex_preview.png")
    print(f"wrote {a.out} and out/mytex_preview.png   mean RGB {arr.reshape(-1,3).mean(0).round(1).tolist()}  "
          f"(very dark or very flat patches texture poorly; check the preview)")


if __name__ == "__main__":
    main()
