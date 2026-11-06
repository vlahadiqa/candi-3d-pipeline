"""Module 3 -- compare two rendered frames (PPM). Reports size, PSNR, SSIM,
mean |diff|; optionally writes an amplified difference image.

  python compare.py A.ppm B.ppm [--diff out/diff.ppm --scale 6]
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

from ppm_io import read_ppm, write_ppm
from metrics import psnr, ssim


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--diff"); ap.add_argument("--scale", type=float, default=6.0)
    args = ap.parse_args()
    A = read_ppm(args.a).astype(np.int32)
    B = read_ppm(args.b).astype(np.int32)
    if A.shape != B.shape:
        print(f"size mismatch: {A.shape} vs {B.shape} -- render both at the "
              f"same w/h and setPixelRatio(1)")
        sys.exit(2)
    d = np.abs(A - B)
    p = psnr(A.astype(np.uint8), B.astype(np.uint8))
    print(f"same size {A.shape[1]}x{A.shape[0]}   "
          f"PSNR: {'inf' if np.isinf(p) else f'{p:.1f}'} dB   "
          f"SSIM: {ssim(A.astype(np.uint8), B.astype(np.uint8)):.3f}   "
          f"mean |diff|: {d.mean():.1f}   max |diff|: {int(d.max())}")
    if args.diff:
        vis = np.clip(d * args.scale, 0, 255).astype(np.uint8)
        write_ppm(args.diff, vis)
        print(f"wrote {args.diff} (|A-B| x{args.scale:g})")


if __name__ == "__main__":
    main()
