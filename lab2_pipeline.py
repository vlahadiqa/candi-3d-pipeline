"""Lab 2 evidence generator (numbers + images only; the diagnosis text is yours).

  python lab2_pipeline.py                      # everything
  python lab2_pipeline.py --section e          # E1-E4 numbers (A2)
  python lab2_pipeline.py --section frame      # raster vs ref vs raytrace, residual location (A2)
  python lab2_pipeline.py --section bugs       # 3 broken scenes: evidence + SSIM before/after (A3)
  python lab2_pipeline.py --section zfight     # depth-code histogram for z-fighting (A3)
  python lab2_pipeline.py --section persp      # naive vs perspective-correct u, floor renders (A5)
  python lab2_pipeline.py --section mip        # 4-level mip pyramid, with/without, shimmer (A5)
  python lab2_pipeline.py --section cull       # pitfall fix: back-face culling, measured (Lab 2 step 5)

Use YOUR model:  --model data/mymodel.obj --tex data/mytexture.ppm
Outputs go to out/lab2_*.ppm / .csv / .png.
"""
from __future__ import annotations

import argparse
import os
import time

import numpy as np

import raster3d
import raytrace
from lab_common import (print_env, load_scene, model_matrix, ensure_out,
                        residual_report, time_calls, time_stats)
from metrics import psnr, ssim
from ppm_io import read_ppm, write_ppm
from srgb import srgb_to_linear, linear_to_srgb
from transforms import (translate, rot_y, look_at, perspective, project, viewport,
                        perspective_divide_2d)

OUT = "out"


def hdr(t):
    print(f"\n{'=' * 8} {t} {'=' * 8}")


def fmt_db(p):
    return "inf" if np.isinf(p) else f"{p:.2f}"


# ===================================================================== E1-E4
def sec_e(a):
    hdr("A2: E1-E4 as numbers (not 'passed')")
    p = np.array([2.0, 3.0, 4.0, 1.0])
    T = translate((1, 0, -1)); R = rot_y(90)
    w1 = R @ T @ p
    w2 = T @ R @ p
    print(f"E1 p=(2,3,4): T then Ry(90) -> {np.round(w1[:3], 6)}   perspective divide d=2 -> "
          f"{np.round(perspective_divide_2d(w1[:3], 2), 6)}   (reverse order -> {np.round(w2[:3], 6)})")
    pt = np.array([5.0, 0, 0, 1])
    print(f"E2 duality: camera +1 on x: V@p = {(look_at((1, 0, 0), (1, 0, -1)) @ pt)[:3]}   "
          f"model -1 on x: M@p = {(translate((-1, 0, 0)) @ pt)[:3]}")
    n, f = 1.0, 9.0
    Pm = perspective(60, 1.0, n, f)
    for z in (-n, -3.0, -f):
        c = Pm @ np.array([0, 0, z, 1.0])
        print(f"E3 n={n:g} f={f:g}: eye z={z:+.1f} -> clip z={c[2]:+.4f} w={c[3]:.1f} -> ndc z={c[2]/c[3]:+.4f}")
    uL, uR, wL, wR, frac = 0.0, 1.0, 1.0, 9.0, 0.5
    naive = uL + frac * (uR - uL)
    num = (1 - frac) * uL / wL + frac * uR / wR
    den = (1 - frac) / wL + frac / wR
    print(f"E4 u at screen midpoint: naive {naive:.4f}   perspective-correct (u/w)/(1/w) = {num/den:.4f}")


# ============================================================== frame match
def sec_frame(a):
    hdr("A2: your frame vs ref/ and vs the ray tracer")
    mesh, tex = load_scene(a.model, a.tex)
    M = model_matrix()
    ref_path = a.ref
    if os.path.exists(ref_path):
        # tests.py always builds ref/temple_ref.ppm from the LECTURER's model (data/pusaka_model.obj + relief.ppm),
        # so the reference check re-renders THAT model, whatever --model is.
        rmesh, rtex = load_scene("data/pusaka_model.obj", "data/relief.ppm")
        ref = read_ppm(ref_path)
        h, w = ref.shape[:2]
        col, dep, _ = raster3d.render(rmesh, w=w, h=h, tex_u8=rtex, model=M)
        write_ppm(f"{OUT}/lab2_frame_raster.ppm", col)
        residual_report(col, ref, f"raster {w}x{h} (data/pusaka_model.obj) vs {ref_path}",
                        save_diff=f"{OUT}/lab2_diff_vs_ref.ppm")
    else:
        print(f"   {ref_path} not found -- run tests.py once (it creates it) and commit ref/.")
    w = h = a.size
    col, dep, filled = raster3d.render(mesh, w=w, h=h, tex_u8=tex, model=M)
    rt, t = raytrace.render(mesh, w=w, h=h, tex_u8=tex, model=M)
    write_ppm(f"{OUT}/lab2_raster_{w}.ppm", col)
    write_ppm(f"{OUT}/lab2_rt_{w}.ppm", rt)
    mask = np.isfinite(t)
    print(f"raster vs raytrace at {w}x{h}: pixels hit by rays {int(mask.sum())}, "
          f"pixels covered by raster {int(np.isfinite(dep).sum())}")
    residual_report(col, rt, "raster vs raytrace", mask=mask, save_diff=f"{OUT}/lab2_diff_raster_rt.ppm")
    a_only = np.isfinite(dep) & ~mask
    b_only = ~np.isfinite(dep) & mask
    print(f"   coverage disagreements: raster-only {int(a_only.sum())}   ray-only {int(b_only.sum())}   (expected: silhouette pixels only)")


# ===================================================================== bugs
def sec_bugs(a):
    hdr("A3: three broken scenes -- evidence first, then SSIM before/after")
    import broken_scene as bs
    mesh, tex = load_scene(a.model, a.tex)
    for name, fn in bs.BUGS.items():
        bad, good, ev = fn(mesh, tex)
        write_ppm(f"{OUT}/lab2_bug_{name}_bad.ppm", bad)
        write_ppm(f"{OUT}/lab2_bug_{name}_fixed.ppm", good)
        s, p = ssim(bad, good), psnr(bad, good)
        print(f"\n[{name}]  <- write YOUR diagnosis from this evidence BEFORE reading broken_scene.py's comments")
        print("  evidence:", ev.replace("\n", "\n  "))
        print(f"  SSIM(bad, fixed) = {s:.4f}   PSNR = {fmt_db(p)} dB   (pixels differing >8: "
              f"{(np.abs(bad.astype(int) - good.astype(int)).max(2) > 8).mean() * 100:.1f}%)")
        print(f"  images: {OUT}/lab2_bug_{name}_bad.ppm  {OUT}/lab2_bug_{name}_fixed.ppm")


# ==================================================================== zfight
def sec_zfight(a):
    hdr("A3: z-fighting -- depth-code histogram, before vs after")
    import broken_scene as bs
    m = bs._zfight_scene()
    cam = dict(eye=(0, 1, 6), center=(0, 1, -1), cull_back=False, far=200,
               tri_colors=bs.TRI_COLS, light_dir=(0, 0.2, 1))
    BITS, W, H = 16, 192, 192
    res = {}
    for label, near in (("near=1e-3 (bug)", 1e-3), ("near=1.0 (fix)", 1.0)):
        col, dep, _ = raster3d.render(m, w=W, h=H, near=near, depth_bits=BITS, **cam)
        res[label] = (col, dep, near)
    ref, _, _ = raster3d.render(m, w=W, h=H, near=1.0, depth_bits=None, **cam)
    rows = []
    for label, (col, dep, near) in res.items():
        fin = np.isfinite(dep)
        codes = np.round((dep[fin] * 0.5 + 0.5) * 2 ** BITS).astype(np.int64)
        u, c = np.unique(codes, return_counts=True)
        wrong = int(np.sum(np.abs(col.astype(int) - ref.astype(int)).max(2) > 60))
        print(f"\n{label}: covered pixels {int(fin.sum())}   distinct {BITS}-bit depth codes used: {len(u)}   "
              f"code range [{u.min()}, {u.max()}] (span {u.max() - u.min()})   "
              f"pixels wrong vs float-depth reference: {wrong}")
        # reference in metres: eye-space depth of the contested quads is ~15 m (eye z=6, quads at z=-9)
        top = np.argsort(-c)[:3]
        print("  most-shared codes (code: pixels):", ", ".join(f"{int(u[i])}: {int(c[i])}" for i in top))
        print(f"  largest single-code share: {c.max() / c.sum() * 100:.1f}% of covered pixels")
        if len(u) <= 40:
            print(f"  depth codes actually used (code: pixels) -- {len(u)} distinct:")
            peak = int(c.max())
            for code, cnt in zip(u, c):
                print(f"   {int(code):7d}  {int(cnt):7d}  " + "#" * int(40 * cnt / peak))
                rows.append((label, float(code), float(code), int(cnt)))
        else:
            hist, edges = np.histogram(codes, bins=24)
            peak = max(hist.max(), 1)
            print("  histogram of depth codes (24 bins):")
            for i in range(24):
                print(f"   [{edges[i]:9.0f},{edges[i + 1]:9.0f})  {hist[i]:7d}  " + "#" * int(40 * hist[i] / peak))
                rows.append((label, float(edges[i]), float(edges[i + 1]), int(hist[i])))
        write_ppm(f"{OUT}/lab2_zfight_{'bug' if near < 0.5 else 'fix'}.ppm", col)
    write_ppm(f"{OUT}/lab2_zfight_reference.ppm", ref)
    with open(f"{OUT}/lab2_zfight_hist.csv", "w") as fh:
        fh.write("scene,bin_lo,bin_hi,count\n")
        for r in rows:
            fh.write(f"{r[0]},{r[1]:.1f},{r[2]:.1f},{r[3]}\n")
    print(f"\nwrote {OUT}/lab2_zfight_hist.csv, lab2_zfight_{{bug,fix,reference}}.ppm")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(1, 2, figsize=(9, 3))
        for ax, (label, (col, dep, near)) in zip(axs, res.items()):
            fin = np.isfinite(dep)
            codes = np.round((dep[fin] * 0.5 + 0.5) * 2 ** BITS)
            ax.hist(codes, bins=40)
            ax.set_title(label); ax.set_xlabel(f"{BITS}-bit depth code"); ax.set_ylabel("pixels")
        fig.tight_layout(); fig.savefig(f"{OUT}/lab2_zfight_hist.png", dpi=150)
        print(f"wrote {OUT}/lab2_zfight_hist.png")
    except Exception as e:  # matplotlib is optional
        print(f"(matplotlib not available -> no PNG; the CSV has the same data) [{e.__class__.__name__}]")


# ================================================================ perspective
def _checker(n=256, cells=8):
    y, x = np.mgrid[0:n, 0:n]
    c = (((x * cells // n) + (y * cells // n)) % 2).astype(np.uint8)
    img = np.where(c[..., None] == 1, [235, 235, 235], [40, 40, 40]).astype(np.uint8)
    return img


def _raster_quad(P, V, quad, uv, tex_lin, w, h, correct):
    """Tiny textured-quad rasteriser: naive screen-linear UV vs perspective-correct."""
    clip, ndc = project(P, V, np.eye(4), quad)
    scr = viewport(ndc, w, h)
    iw = 1.0 / clip[:, 3]
    img = np.zeros((h, w, 3))
    depth = np.full((h, w), np.inf)
    for tri in ((0, 1, 2), (0, 2, 3)):
        s = scr[list(tri)]; q = uv[list(tri)]; ww = iw[list(tri)]
        x0, x1 = int(max(0, np.floor(s[:, 0].min()))), int(min(w - 1, np.ceil(s[:, 0].max())))
        y0, y1 = int(max(0, np.floor(s[:, 1].min()))), int(min(h - 1, np.ceil(s[:, 1].max())))
        ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        px, py = xs + 0.5, ys + 0.5
        (ax, ay), (bx, by), (cx, cy) = s[0, :2], s[1, :2], s[2, :2]
        area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
        lA = ((cx - bx) * (py - by) - (cy - by) * (px - bx)) / area
        lB = ((ax - cx) * (py - cy) - (ay - cy) * (px - cx)) / area
        lC = 1 - lA - lB
        ins = (lA >= 0) & (lB >= 0) & (lC >= 0)
        z = lA * s[0, 2] + lB * s[1, 2] + lC * s[2, 2]
        if correct:
            den = lA * ww[0] + lB * ww[1] + lC * ww[2]
            u = (lA * q[0, 0] * ww[0] + lB * q[1, 0] * ww[1] + lC * q[2, 0] * ww[2]) / den
            v = (lA * q[0, 1] * ww[0] + lB * q[1, 1] * ww[1] + lC * q[2, 1] * ww[2]) / den
        else:
            u = lA * q[0, 0] + lB * q[1, 0] + lC * q[2, 0]
            v = lA * q[0, 1] + lB * q[1, 1] + lC * q[2, 1]
        rgb = raster3d.sample_bilinear(tex_lin, u, v)
        reg_d = depth[y0:y1 + 1, x0:x1 + 1]; reg_c = img[y0:y1 + 1, x0:x1 + 1]
        win = ins & (z < reg_d)
        reg_d[win] = z[win]; reg_c[win] = rgb[win]
    return (linear_to_srgb(img) * 255).astype(np.uint8), np.isfinite(depth)


def sec_persp(a):
    hdr("A5: perspective-correct vs naive texture coordinates")
    wL, wR = 1.0, 9.0
    print(f"E4 numbers: floor edge L (w={wL:g}, u=0) to R (w={wR:g}, u=1), screen midpoint -> "
          f"naive u = 0.5000, perspective-correct u = {((0.5*0/wL + 0.5*1/wR) / (0.5/wL + 0.5/wR)):.4f}")
    W = H = 256
    P = perspective(60, 1.0, 0.1, 100.0)
    V = look_at((0, 1.0, 3.0), (0, 0.0, -10.0))
    quad = np.array([[-3, 0, 0], [3, 0, 0], [3, 0, -40], [-3, 0, -40]], float)
    uv = np.array([[0, 0], [1, 0], [1, 8], [0, 8]], float)       # 8 tiles down the floor
    tex_lin = srgb_to_linear(_checker().astype(float) / 255)
    naive, cov = _raster_quad(P, V, quad, uv, tex_lin, W, H, correct=False)
    right, _ = _raster_quad(P, V, quad, uv, tex_lin, W, H, correct=True)
    write_ppm(f"{OUT}/lab2_persp_naive.ppm", naive)
    write_ppm(f"{OUT}/lab2_persp_correct.ppm", right)
    d = np.abs(naive.astype(int) - right.astype(int)).max(2)
    print(f"floor quad {W}x{H}: covered pixels {int(cov.sum())}   pixels where naive != correct (>32 levels): "
          f"{int(((d > 32) & cov).sum())} ({((d > 32) & cov).sum() / cov.sum() * 100:.1f}% of the quad)")
    print(f"SSIM(naive, correct) = {ssim(naive, right):.4f}   PSNR = {fmt_db(psnr(naive, right))} dB")
    # a swimming measure: how fast does the texture row boundary move with distance (rows where colour flips along centre column)
    for nm, im in (("naive", naive), ("correct", right)):
        col = im[:, W // 2, 0].astype(int)
        flips = np.where(np.abs(np.diff(col)) > 100)[0]
        print(f"  {nm:8s} checker row boundaries (screen y) down the centre column: {flips.tolist()}")
    print(f"wrote {OUT}/lab2_persp_naive.ppm, {OUT}/lab2_persp_correct.ppm")


# ======================================================================= mip
def build_mips(tex_lin, levels=4):
    """Gamma-correct (linear-light) 2x2 box pyramid. tex_lin is already linear."""
    pyr = [tex_lin]
    for _ in range(levels - 1):
        t = pyr[-1]
        h, w = (t.shape[0] // 2) * 2, (t.shape[1] // 2) * 2
        t = t[:h, :w]
        pyr.append(0.25 * (t[0::2, 0::2] + t[1::2, 0::2] + t[0::2, 1::2] + t[1::2, 1::2]))
    return pyr


class MipSampler:
    """Drop-in replacement for raster3d.sample_bilinear that picks a mip level
    per pixel from finite-difference UV derivatives, and blends the two nearest
    levels (trilinear, expressed as tent weights over the levels)."""

    def __init__(self, levels=4):
        self.levels, self.cache, self.base = levels, {}, raster3d.sample_bilinear
        self.last_lod_hist = np.zeros(levels)

    def __call__(self, tex_lin, u, v):
        pyr = self.cache.get(id(tex_lin))
        if pyr is None:
            pyr = self.cache[id(tex_lin)] = build_mips(tex_lin, self.levels)
        if u.ndim < 2 or min(u.shape) < 2:
            return self.base(pyr[0], u, v)
        H, W = tex_lin.shape[:2]
        dudx, dudy = np.gradient(u, axis=1), np.gradient(u, axis=0)
        dvdx, dvdy = np.gradient(v, axis=1), np.gradient(v, axis=0)
        rho = np.maximum(np.hypot(dudx * W, dvdx * H), np.hypot(dudy * W, dvdy * H))
        lod = np.clip(np.log2(np.maximum(rho, 1e-9)), 0, self.levels - 1)
        out = np.zeros(u.shape + (3,))
        for k in range(self.levels):
            wk = np.clip(1.0 - np.abs(lod - k), 0.0, 1.0)
            if wk.any():
                out += wk[..., None] * self.base(pyr[k], u, v)
        return out


def _hf_energy(img, mask):
    g = img.astype(float).mean(2)
    lap = (-4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:])
    m = mask[1:-1, 1:-1]
    return float((lap[m] ** 2).mean()) if m.any() else 0.0


def sec_mip(a):
    hdr("A5: mipmap before/after (4-level, gamma-correct box, trilinear)")
    mesh, tex = load_scene(a.model, a.tex)
    if tex is None:
        print("   needs a texture (--tex)"); return
    M = model_matrix()
    S, W = 4, a.mip_size
    far_eye = np.array([2.6, 2.0, 3.4]) * a.mip_dist
    cam = dict(center=(0, 0.7, 0), far=200.0)
    print(f"far view: eye = {np.round(far_eye, 2).tolist()} ({a.mip_dist:g}x the default distance), frame {W}x{W}")
    pyr = build_mips(srgb_to_linear(tex.astype(float) / 255), 4)
    print("pyramid sizes:", [p.shape[:2] for p in pyr],
          " mean linear value per level:", [round(float(p.mean()), 5) for p in pyr], "(equal means = energy preserved)")

    base = raster3d.sample_bilinear

    def frame(eye, size, sampler):
        raster3d.sample_bilinear = sampler
        try:
            c, d, _ = raster3d.render(mesh, w=size, h=size, tex_u8=tex, model=M, eye=tuple(eye), **cam)
        finally:
            raster3d.sample_bilinear = base
        return c, np.isfinite(d)

    mip = MipSampler(4)
    nomip, mask = frame(far_eye, W, base)
    withmip, _ = frame(far_eye, W, mip)
    # ground truth: render at 4x resolution (4x less minification), box-filter down in LINEAR light
    big, _ = frame(far_eye, W * S, base)
    gt_lin = srgb_to_linear(big.astype(float) / 255).reshape(W, S, W, S, 3).mean((1, 3))
    gt = (linear_to_srgb(gt_lin) * 255).astype(np.uint8)
    write_ppm(f"{OUT}/lab2_mip_without.ppm", nomip)
    write_ppm(f"{OUT}/lab2_mip_with.ppm", withmip)
    write_ppm(f"{OUT}/lab2_mip_groundtruth.ppm", gt)
    write_ppm(f"{OUT}/lab2_mip_diff_without.ppm", np.clip(np.abs(nomip.astype(int) - gt) * 6, 0, 255).astype(np.uint8))
    write_ppm(f"{OUT}/lab2_mip_diff_with.ppm", np.clip(np.abs(withmip.astype(int) - gt) * 6, 0, 255).astype(np.uint8))
    for nm, im in (("without mipmap", nomip), ("with mipmap   ", withmip)):
        print(f"{nm}: PSNR vs 4x-supersampled truth {fmt_db(psnr(im, gt))} dB   SSIM {ssim(im, gt):.4f}   "
              f"high-frequency energy (mean Laplacian^2 on object) {_hf_energy(im, mask):.2f}")
    print(f"ground truth       : high-frequency energy {_hf_energy(gt, mask):.2f}")

    # shimmer: tiny camera moves, how much does the texture flicker frame to frame?
    steps = [np.array([0.0, 0, 0]), np.array([0.01, 0, 0]), np.array([0.02, 0.005, 0]), np.array([0.03, 0.005, 0.01])]
    for nm, smp in (("without mipmap", base), ("with mipmap   ", mip)):
        fr = [frame(far_eye + s, W, smp)[0].astype(float) for s in steps]
        diffs = [np.abs(fr[i + 1] - fr[i])[mask].mean() for i in range(len(fr) - 1)]
        print(f"shimmer {nm}: mean |frame(t+1) - frame(t)| on object over {len(diffs)} tiny camera steps = {np.mean(diffs):.3f}")
    print(f"wrote {OUT}/lab2_mip_{{without,with,groundtruth,diff_without,diff_with}}.ppm")


# ============================================================== back-face cull
def sec_cull(a):
    hdr("Lab 2 step 5: pitfall fix = back-face culling, measured (+ winding check)")
    from lab_common import winding_report, flip_winding, signed_volume
    mesh0, tex = load_scene(a.model, a.tex)
    M = model_matrix()
    w = h = a.size
    eye, center = (2.6, 2.0, 3.4), (0, 0.7, 0)
    P = perspective(45, w / h, 1.0, 14.0)
    V = look_at(eye, center)
    v0 = winding_report(mesh0, "as loaded")
    variants = [("as loaded", mesh0)]
    if v0 < 0:
        variants.append(("winding corrected (faces flipped)", flip_winding(mesh0)))
        print("  -> adding a second run with the winding corrected, so you can compare")
    for name, mesh in variants:
        print(f"\n--- variant: {name} ---")
        clip, ndc = project(P, V, M, mesh.positions)
        scr = viewport(ndc, w, h)
        tri = scr[mesh.faces][:, :, :2]
        area = ((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1])
                - (tri[:, 1, 1] - tri[:, 0, 1]) * (tri[:, 2, 0] - tri[:, 0, 0]))
        back = area > 0       # raster3d rule (screen y-down): front faces have area < 0
        print(f"  {mesh.n_tris} triangles; culled by the rule (area>0): {int(back.sum())} ({back.mean() * 100:.1f}%)   "
              f"kept: {int((area < 0).sum())}   degenerate: {int((area == 0).sum())}")
        res = {}
        for cull in (False, True):
            fn = lambda: raster3d.render(mesh, w=w, h=h, tex_u8=tex, model=M, cull_back=cull)
            st = time_stats(time_calls(fn, repeat=a.repeat))
            col, dep, filled = fn()
            tag = name.split()[0] + ("_cull" if cull else "_nocull")
            write_ppm(f"{OUT}/lab2_{tag}.ppm", col)
            res[cull] = (col, filled)
            print(f"  cull_back={str(cull):5s}: depth-passing fragment writes {filled:6d}   frame time median "
                  f"{st['median_s'] * 1e3:.1f} ms (min {st['min_s'] * 1e3:.1f}, iqr {st['iqr_s'] * 1e3:.1f}, n={st['n']})")
        (c_off, f_off), (c_on, f_on) = res[False], res[True]
        print(f"  fragment writes {f_off} -> {f_on}  ({(1 - f_on / f_off) * 100:.1f}% fewer)")
        print(f"  culled image == un-culled image?  {np.array_equal(c_off, c_on)}   max|diff| "
              f"{int(np.abs(c_off.astype(int) - c_on).max())}   SSIM {ssim(c_off, c_on):.4f}")


SECTIONS = {"e": sec_e, "frame": sec_frame, "bugs": sec_bugs, "zfight": sec_zfight,
            "persp": sec_persp, "mip": sec_mip, "cull": sec_cull}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--section", choices=["all"] + list(SECTIONS), default="all")
    ap.add_argument("--model", default="data/pusaka_model.obj")
    ap.add_argument("--tex", default="data/relief.ppm")
    ap.add_argument("--ref", default="ref/temple_ref.ppm")
    ap.add_argument("--size", type=int, default=256, help="frame size for frame/cull sections")
    ap.add_argument("--mip-size", type=int, default=96)
    ap.add_argument("--mip-dist", type=float, default=3.0, help="camera distance multiplier for the far view")
    ap.add_argument("--repeat", type=int, default=5)
    a = ap.parse_args()
    ensure_out(OUT)
    print_env()
    for k, fn in SECTIONS.items():
        if a.section in ("all", k):
            t0 = time.time()
            fn(a)
            print(f"   [{k} took {time.time() - t0:.1f}s]")


if __name__ == "__main__":
    main()
