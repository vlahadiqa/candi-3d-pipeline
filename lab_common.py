"""Shared helpers for the lab analysis scripts (lab1_trace / lab2_pipeline /
lab3_bench / repro_clean). Put next to transforms.py in your Module3 folder.

Nothing here interprets results -- it only measures. Writing the diagnosis
and the reflection is YOUR job (the module is graded on that).
"""
from __future__ import annotations

import datetime
import os
import platform
import statistics
import subprocess
import sys
import time

import numpy as np

from metrics import psnr, ssim
from ppm_io import write_ppm


# ----------------------------------------------------------------- toolchain
def _cmd_version(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10, shell=(os.name == "nt"))
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except Exception:
        return "not found"


def env_info() -> dict:
    try:
        import PIL
        pil = PIL.__version__
    except Exception:
        pil = "not installed"
    return {
        "date": datetime.datetime.now().isoformat(timespec="seconds"),
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pillow": pil,
        "node": _cmd_version(["node", "--version"]),
        "three.js (from web/index.html)": "three@0.160.0 (check the importmap if you changed it)",
        "browser": "FILL IN BY HAND (name + version)",
    }


def print_env():
    print("== toolchain ==")
    for k, v in env_info().items():
        print(f"  {k:32s} {v}")


# -------------------------------------------------------------------- timing
def time_calls(fn, repeat=5, warmup=1):
    for _ in range(warmup):
        fn()
    ts = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t0)
    return ts


def time_stats(ts):
    q = np.percentile(ts, [25, 75])
    return {"median_s": statistics.median(ts), "min_s": min(ts), "max_s": max(ts),
            "iqr_s": float(q[1] - q[0]), "n": len(ts)}


# ----------------------------------------------------------- image residuals
def _dilate(m, r):
    p = np.pad(m, r, mode="constant", constant_values=False)
    out = np.zeros_like(m)
    h, w = m.shape
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1):
            out |= p[dy:dy + h, dx:dx + w]
    return out


def _erode(m, r):
    return ~_dilate(~m, r)


def residual_report(a, b, label="", mask=None, band=2, save_diff=None, amp=6.0):
    """Quantify where two same-size uint8 RGB frames disagree.

    mask: boolean object mask (default: pixels of `a` that are not pure black).
    Splits squared error into: silhouette band (+-band px around the object
    outline), interior (object eroded by band), background.
    """
    if a.shape != b.shape:
        raise ValueError(f"{label}: shape mismatch {a.shape} vs {b.shape}")
    af, bf = a.astype(float), b.astype(float)
    d = np.abs(af - bf)
    if mask is None:
        mask = (a.sum(axis=2) > 0) | (b.sum(axis=2) > 0)
    inner = _erode(mask, band)
    outline = _dilate(mask, band) & ~inner
    background = ~(inner | outline)
    se = ((af - bf) ** 2).sum(axis=2)
    tot = se.sum()

    def share(m):
        return float(se[m].sum() / tot) if tot > 0 else 0.0

    p = psnr(a, b)
    rep = {
        "label": label,
        "psnr_db": p, "ssim": ssim(a, b),
        "mean_abs_diff": float(d.mean()), "max_abs_diff": int(d.max()),
        "pct_pixels_diff_gt8": float((d.max(axis=2) > 8).mean() * 100),
        "err_share_outline": share(outline), "err_share_interior": share(inner),
        "err_share_background": share(background),
    }
    print(f"-- {label}")
    print(f"   PSNR {('inf' if np.isinf(p) else f'{p:.2f}')} dB   SSIM {rep['ssim']:.4f}   "
          f"mean|diff| {rep['mean_abs_diff']:.3f}   max|diff| {rep['max_abs_diff']}   "
          f"pixels>8: {rep['pct_pixels_diff_gt8']:.2f}%")
    print(f"   squared-error share: outline {rep['err_share_outline']*100:.1f}%   "
          f"interior {rep['err_share_interior']*100:.1f}%   background {rep['err_share_background']*100:.1f}%")
    if save_diff:
        os.makedirs(os.path.dirname(save_diff) or ".", exist_ok=True)
        write_ppm(save_diff, np.clip(d * amp, 0, 255).astype(np.uint8))
        print(f"   wrote {save_diff} (|diff| x{amp:g})")
    return rep


def ensure_out(path="out"):
    os.makedirs(path, exist_ok=True)
    return path


def model_matrix(yaw=35.0, s=1.4):
    from transforms import translate, rot_y, scale
    return translate((0, 0, 0)) @ rot_y(yaw) @ scale((s, s, s))


def load_scene(model_path, tex_path):
    from objio import load_obj
    from ppm_io import read_ppm
    mesh = load_obj(model_path)
    tex = read_ppm(tex_path) if tex_path and os.path.exists(tex_path) else None
    return mesh, tex


# ------------------------------------------------------------------ winding
def signed_volume(mesh):
    """(1/6) sum p0 . (p1 x p2) over all triangles. For a closed mesh wound CCW
    seen from OUTSIDE (the pinned convention) this is > 0; < 0 means every
    face is wound clockwise from outside (inside-out under back-face culling)."""
    t = mesh.positions[mesh.faces]
    return float(np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2])).sum() / 6.0)


def flip_winding(mesh):
    from objio import Mesh
    return Mesh(mesh.positions, mesh.uvs, mesh.faces[:, ::-1].copy(),
                None if mesh.face_uvs is None else mesh.face_uvs[:, ::-1].copy())


def winding_report(mesh, label="model"):
    v = signed_volume(mesh)
    kind = ("CCW from outside (matches the pinned convention)" if v > 0
            else "CLOCKWISE from outside (inverted vs the pinned CCW-front convention)")
    print(f"  winding check [{label}]: signed volume = {v:+.4f}  -> {kind}")
    return v
