"""Lab 3 evidence: predict -> measure -> reconcile for rasterisation vs ray tracing.

Step 1 -- record YOUR prediction BEFORE measuring (it is time-stamped):
  python lab3_bench.py predict --ratio 5 --shadow raytrace --reflection raytrace --note "why, in your words"
      --ratio   your guess of (raytrace frame time / raster frame time) on your model
      --shadow / --reflection   which renderer you predict gives better result: raster | raytrace

Step 2 -- measure (frame time, scaling with triangles and resolution, hard shadows):
  python lab3_bench.py measure --model data/mymodel.obj --tex data/mytexture.ppm --size 256 --repeat 5

Step 3 -- reconcile the WebGL export with your NumPy frame (same camera, 512x512):
  python lab3_bench.py webcompare --web web/mymodel_three.ppm --model data/mymodel.obj --tex data/mytexture.ppm

Numbers only. Deciding "real-time viewer vs beauty shot" and why is yours to write.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import os

import numpy as np

import raster3d
import raytrace
from lab_common import (print_env, load_scene, model_matrix, ensure_out, time_calls,
                        time_stats, residual_report)
from objio import Mesh
from ppm_io import read_ppm, write_ppm
from srgb import linear_to_srgb

OUT = "out"
PRED = f"{OUT}/lab3_prediction.json"


def replicate(mesh, k):
    """k copies of the same geometry in place (timing only: triangle count x k)."""
    if k == 1:
        return mesh
    n = len(mesh.positions)
    faces = np.vstack([mesh.faces + i * n for i in range(k)])
    pos = np.vstack([mesh.positions] * k)
    uv = mesh.uvs
    fuv = None if mesh.face_uvs is None else np.vstack([mesh.face_uvs] * k)
    return Mesh(pos, uv, faces, fuv if fuv is not None else [])


def cmd_predict(a):
    ensure_out(OUT)
    d = {"time": datetime.datetime.now().isoformat(timespec="seconds"),
         "predicted_ratio_rt_over_raster": a.ratio, "predicted_better_shadows": a.shadow,
         "predicted_better_reflections": a.reflection, "note": a.note}
    if os.path.exists(PRED) and not a.overwrite:
        raise SystemExit(f"{PRED} already exists (your earlier prediction). Use --overwrite only if you have NOT measured yet.")
    json.dump(d, open(PRED, "w"), indent=2)
    print("saved prediction:", json.dumps(d, indent=2))


def hard_shadow_mask(mesh, M, w, h, eye, center, fovy, light_dir, tex=None):
    """Primary rays (same camera as raytrace.render) + one shadow ray per hit toward the light.
    Returns (hit_mask, shadowed_mask)."""
    tris = (M @ np.c_[mesh.positions, np.ones(len(mesh.positions))].T).T[:, :3][mesh.faces]
    img, t = raytrace.render(mesh, w=w, h=h, tex_u8=tex, model=M, eye=eye, center=center, fovy=fovy)
    eye = np.asarray(eye, float)
    fwd = np.asarray(center, float) - eye; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, (0, 1, 0)); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    th = np.tan(np.radians(fovy) / 2)
    ii, jj = np.mgrid[0:h, 0:w]
    nx = (jj + 0.5) / w * 2 - 1
    ny = 1 - (ii + 0.5) / h * 2
    dirs = nx[..., None] * right * th * (w / h) + ny[..., None] * up * th + fwd
    dirs /= np.linalg.norm(dirs, axis=-1, keepdims=True)
    hit = np.isfinite(t)
    pts = eye + dirs * np.where(hit, t, 0)[..., None]
    pts = pts.reshape(-1, 3)
    L = np.asarray(light_dir, float); L /= np.linalg.norm(L)
    # offset along the face normal toward the light to avoid self-hits
    nrm = np.zeros_like(pts)
    # nearest-triangle normals: recompute by brute force on hit pixels (cheap enough at <=256^2)
    idx = np.where(hit.reshape(-1))[0]
    best = np.full(len(pts), np.inf); bn = np.zeros_like(pts)
    for tri in tris:
        n = np.cross(tri[1] - tri[0], tri[2] - tri[0]); n /= np.linalg.norm(n) + 1e-12
        dist = np.abs((pts[idx] - tri[0]) @ n)
        # barycentric inside test of the projected point
        e0, e1 = tri[1] - tri[0], tri[2] - tri[0]
        d = pts[idx] - tri[0]
        d00, d01, d11 = e0 @ e0, e0 @ e1, e1 @ e1
        d20, d21 = d @ e0, d @ e1
        den = d00 * d11 - d01 * d01
        v = (d11 * d20 - d01 * d21) / den
        u = (d00 * d21 - d01 * d20) / den
        ok = (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6) & (dist < best[idx])
        best[idx[ok]] = dist[ok]; bn[idx[ok]] = n
    flip = (bn @ L) < 0
    bn[flip] = -bn[flip]
    orig = pts + bn * 1e-4
    shadow = np.zeros(len(pts), bool)
    for tri in tris:
        e1, e2 = tri[1] - tri[0], tri[2] - tri[0]
        pvec = np.cross(L, e2)
        det = pvec @ e1
        if abs(det) < 1e-12:
            continue
        tvec = orig[idx] - tri[0]
        u = (tvec @ pvec) / det
        q = np.cross(tvec, e1)
        v = (q @ L) / det
        tt = (q @ e2) / det
        shadow[idx] |= (u >= 0) & (v >= 0) & (u + v <= 1) & (tt > 1e-6)
    return hit, shadow.reshape(h, w)


def cmd_measure(a):
    ensure_out(OUT)
    print_env()
    mesh, tex = load_scene(a.model, a.tex)
    M = model_matrix()
    w = h = a.size
    cam = dict(eye=(2.6, 2.0, 3.4), center=(0, 0.7, 0), fovy=45.0)
    print(f"\nmodel {a.model}: {mesh.n_tris} triangles   frame {w}x{h}   repeats {a.repeat} (1 warm-up)")

    rows = []
    print("\n== frame time vs triangle count (geometry replicated in place; timing only) ==")
    print(f"  {'tris':>8s} {'raster ms':>11s} {'raytrace ms':>12s} {'rt/raster':>10s}")
    for k in a.copies:
        m = replicate(mesh, k)
        tr = time_stats(time_calls(lambda: raster3d.render(m, w=w, h=h, tex_u8=tex, model=M, **{**cam, 'eye': cam['eye']}), a.repeat))
        tt = time_stats(time_calls(lambda: raytrace.render(m, w=w, h=h, tex_u8=tex, model=M, **cam), max(2, a.repeat // 2)))
        r = tt["median_s"] / tr["median_s"]
        print(f"  {m.n_tris:8d} {tr['median_s'] * 1e3:11.1f} {tt['median_s'] * 1e3:12.1f} {r:10.2f}")
        rows.append(dict(kind="tris", tris=m.n_tris, size=w, raster_ms=tr["median_s"] * 1e3,
                         raytrace_ms=tt["median_s"] * 1e3, ratio=r))

    print("\n== frame time vs resolution (your model, as loaded) ==")
    print(f"  {'size':>8s} {'raster ms':>11s} {'raytrace ms':>12s} {'rt/raster':>10s}")
    for s in a.sizes:
        tr = time_stats(time_calls(lambda: raster3d.render(mesh, w=s, h=s, tex_u8=tex, model=M, **cam), a.repeat))
        tt = time_stats(time_calls(lambda: raytrace.render(mesh, w=s, h=s, tex_u8=tex, model=M, **cam), max(2, a.repeat // 2)))
        r = tt["median_s"] / tr["median_s"]
        print(f"  {s:8d} {tr['median_s'] * 1e3:11.1f} {tt['median_s'] * 1e3:12.1f} {r:10.2f}")
        rows.append(dict(kind="res", tris=mesh.n_tris, size=s, raster_ms=tr["median_s"] * 1e3,
                         raytrace_ms=tt["median_s"] * 1e3, ratio=r))

    base = [r for r in rows if r["kind"] == "res" and r["size"] == w]
    measured_ratio = base[0]["ratio"] if base else rows[0]["ratio"]
    print(f"\nmeasured rt/raster at {w}x{w}, {mesh.n_tris} tris: {measured_ratio:.2f}x")
    print("  NOTE: both renderers are Python/NumPy on the CPU. The ratio says nothing about a GPU rasteriser or RT cores.")

    print("\n== hard shadows (ray tracer only: one shadow ray per primary hit) ==")
    light = tuple(a.light)
    hit, sh = hard_shadow_mask(mesh, M, min(w, 192), min(h, 192), cam["eye"], cam["center"], cam["fovy"], light, tex)
    print(f"  light dir {light}: {int(sh.sum())} of {int(hit.sum())} hit pixels are in shadow ({sh.sum() / max(hit.sum(), 1) * 100:.1f}%)")
    sm = np.zeros(sh.shape + (3,), np.uint8)
    sm[hit] = (90, 90, 90); sm[sh] = (20, 40, 120)
    write_ppm(f"{OUT}/lab3_shadow_mask.ppm", sm)
    print(f"  wrote {OUT}/lab3_shadow_mask.ppm  (grey = lit, blue = shadowed)")
    print("  raster3d.py has no shadows or reflections (would need a shadow map / environment probe) -> "
          "nothing to measure on that side; state that in your reconciliation.")

    with open(f"{OUT}/lab3_bench.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
    json.dump({"rows": rows, "shadow_pct": float(sh.sum() / max(hit.sum(), 1) * 100)}, open(f"{OUT}/lab3_bench.json", "w"), indent=2)
    print(f"  wrote {OUT}/lab3_bench.csv, {OUT}/lab3_bench.json")

    if os.path.exists(PRED):
        p = json.load(open(PRED))
        pr = p["predicted_ratio_rt_over_raster"]
        print("\n== your prediction vs the measurement ==")
        print(f"  predicted at {p['time']}: ratio {pr:g}x   shadows -> {p['predicted_better_shadows']}   reflections -> {p['predicted_better_reflections']}")
        print(f"  measured: ratio {measured_ratio:.2f}x   => off by a factor of {max(pr / measured_ratio, measured_ratio / pr):.2f}   "
              f"({'over' if pr > measured_ratio else 'under'}-estimated)")
        print("  (explaining the gap is the 'reconcile' step -- yours to write)")
    else:
        print("\n(no prediction file found: run `python lab3_bench.py predict ...` BEFORE measuring next time; "
              "the module requires the prediction to come first.)")


def cmd_webcompare(a):
    ensure_out(OUT)
    web = read_ppm(a.web)
    h, w = web.shape[:2]
    print(f"web export {a.web}: {w}x{h}")
    if (w, h) != (512, 512):
        print("  WARNING: Lab 3 asks for 512x512 with setPixelRatio(1); a different size usually means devicePixelRatio crept in.")
    mesh, tex = load_scene(a.model, a.tex)
    col, dep, _ = raster3d.render(mesh, w=w, h=h, tex_u8=tex, model=model_matrix())
    write_ppm(f"{OUT}/lab3_raster_{w}.ppm", col)
    mask = np.isfinite(dep)
    residual_report(col, web, "NumPy raster vs WebGL export", mask=mask, band=3, save_diff=f"{OUT}/lab3_diff_raster_web.ppm")
    # where is the largest error? report block hot-spots so you can name the region
    d = np.abs(col.astype(float) - web.astype(float)).sum(2)
    B = 64
    blocks = d[:h // B * B, :w // B * B].reshape(h // B, B, w // B, B).sum((1, 3))
    top = np.dstack(np.unravel_index(np.argsort(-blocks.ravel())[:5], blocks.shape))[0]
    print("  5 worst 64x64 blocks (row, col -> share of total abs error):")
    for r, c in top:
        print(f"    block ({r},{c}) pixels x {c * B}-{(c + 1) * B}, y {r * B}-{(r + 1) * B}: {blocks[r, c] / blocks.sum() * 100:.1f}%")
    if os.path.exists(a.rt):
        rt = read_ppm(a.rt)
        if rt.shape == col.shape:
            residual_report(rt, web, "ray trace vs WebGL export", mask=np.isfinite(dep), band=3)
        else:
            print(f"  ({a.rt} is {rt.shape[1]}x{rt.shape[0]}; re-run raytrace.py at {w}x{h} to compare it with the web frame)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("predict")
    p.add_argument("--ratio", type=float, required=True)
    p.add_argument("--shadow", choices=["raster", "raytrace"], required=True)
    p.add_argument("--reflection", choices=["raster", "raytrace"], required=True)
    p.add_argument("--note", default="")
    p.add_argument("--overwrite", action="store_true")
    p.set_defaults(fn=cmd_predict)
    m = sub.add_parser("measure")
    m.add_argument("--model", default="data/pusaka_model.obj")
    m.add_argument("--tex", default="data/relief.ppm")
    m.add_argument("--size", type=int, default=192)
    m.add_argument("--repeat", type=int, default=5)
    m.add_argument("--copies", type=int, nargs="+", default=[1, 2, 4])
    m.add_argument("--sizes", type=int, nargs="+", default=[96, 192, 288])
    m.add_argument("--light", type=float, nargs=3, default=(0.4, 0.9, 0.6), help="light direction for the shadow test (default = the renderers' light)")
    m.set_defaults(fn=cmd_measure)
    c = sub.add_parser("webcompare")
    c.add_argument("--web", default="web/temple_three.ppm")
    c.add_argument("--model", default="data/pusaka_model.obj")
    c.add_argument("--tex", default="data/relief.ppm")
    c.add_argument("--rt", default="out/temple_rt.ppm")
    c.set_defaults(fn=cmd_webcompare)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
