"""Lab 1 evidence: trace ONE vertex of YOUR model through every space, read the
columns of M and V, and put numbers on the 1/z depth squeeze.

Run (from the Module3 folder):
  python lab1_trace.py --model data/mymodel.obj --vertex 0
  python lab1_trace.py --model data/mymodel.obj --vertex 17 --hand 3.0 3.0 -3.0   # check your hand result of M@p
  python lab1_trace.py --near 0.01 --far 1000 --vertex 5                        # depth-precision numbers for other planes

Prints numbers only. The by-hand work (first two steps) and every interpretation
sentence is yours to write. Output is also saved to out/lab1_trace.txt.
"""
from __future__ import annotations

import argparse
import io
import os
import sys
from contextlib import redirect_stdout

import numpy as np

from lab_common import print_env, load_scene, model_matrix, ensure_out, winding_report
from transforms import perspective, look_at, project, viewport

np.set_printoptions(precision=6, suppress=True, linewidth=120)


def vec(v):
    return np.array2string(np.asarray(v, float), precision=6, suppress_small=True)


def trace(args):
    print_env()
    mesh, tex = load_scene(args.model, args.tex)
    P0 = mesh.positions
    print("\n== model ==")
    print(f"  file: {args.model}")
    print(f"  vertices {len(P0)}   triangles {mesh.n_tris}   uvs {len(mesh.uvs)}   "
          f"textured: {mesh.face_uvs is not None and tex is not None}")
    print(f"  bbox min {vec(P0.min(0))}  max {vec(P0.max(0))}")
    winding_report(mesh, "your model")
    if mesh.n_tris < 200:
        print("  NOTE: Lab 1 asks for >= 200 triangles for YOUR own model.")

    M = model_matrix(args.yaw, args.scale)
    V = look_at(args.eye, args.center)
    P = perspective(args.fovy, args.w / args.h, args.near, args.far)
    print("\n== matrices (column-vector convention, p' = M @ p) ==")
    print(f"model M = T(0) @ Ry({args.yaw:g}) @ S({args.scale:g})\n{M}")
    print(f"view V = look_at(eye={tuple(args.eye)}, center={tuple(args.center)})\n{V}")
    print(f"proj P = perspective(fovy={args.fovy:g}, aspect={args.w}/{args.h}, near={args.near:g}, far={args.far:g})\n{P}")

    i = args.vertex % len(P0)
    p = np.r_[P0[i], 1.0]
    world = M @ p
    eye_s = V @ world
    clip = P @ eye_s
    ndc = clip[:3] / clip[3]
    scr = viewport(ndc[None, :], args.w, args.h)[0]
    print(f"\n== vertex #{i} through the six spaces ==")
    print(f"  object  p      = {vec(p)}")
    print(f"  world   M p    = {vec(world)}")
    print(f"  view    V M p  = {vec(eye_s)}    (z<0 means in front of the camera; distance = {-eye_s[2]:.6f})")
    print(f"  clip    P V M p= {vec(clip)}    (w = -z_eye = {clip[3]:.6f})")
    print(f"  ndc     clip/w = {vec(ndc)}    (inside [-1,1]^3: {bool(np.all(np.abs(ndc) <= 1))})")
    print(f"  screen  {args.w}x{args.h}      = x {scr[0]:.3f}  y {scr[1]:.3f} (y down)  depth(ndc z) {scr[2]:.6f}   depth01 {(scr[2]+1)/2:.6f}")

    # cross-check: the one-MVP route and transforms.project/viewport must agree
    clip2, ndc2 = project(P, V, M, P0[i:i + 1])
    mvp = P @ V @ M
    assert np.allclose(clip2[0], clip) and np.allclose(mvp @ p, clip) and np.allclose(ndc2[0], ndc)
    print("  cross-check: P@V@M@p == step-by-step == transforms.project()  -> OK")

    print("\n== read the columns (where do the model's axes go?) ==")
    names = ["+x", "+y", "+z", "origin"]
    for k in range(4):
        print(f"  M col {k} ({names[k]:6s}) -> world {vec(M[:3, k])}   |col| = {np.linalg.norm(M[:3, k]):.6f}")
    for k in range(4):
        print(f"  V col {k} (world {names[k]:6s}) -> camera space {vec(V[:3, k])}")
    print(f"  det(upper-left 3x3 of M) = {np.linalg.det(M[:3,:3]):.6f}   (scale^3 = {args.scale**3:.6f}; sign + = right-handed kept)")
    R = V[:3, :3]
    print(f"  V rotation orthonormal? R R^T = I: {np.allclose(R @ R.T, np.eye(3))}   det R = {np.linalg.det(R):.6f}")
    print(f"  camera position recovered from V: {vec(-R.T @ V[:3, 3])}   (should equal eye {tuple(args.eye)})")

    if args.hand is not None:
        h = np.array(args.hand, float)
        d = np.abs(h - world[:3])
        print(f"\n== your hand result for M p vs the tool ==")
        print(f"  yours {vec(h)}   tool {vec(world[:3])}   max |diff| {d.max():.6f}   "
              f"{'MATCH to 3 decimals' if d.max() < 5e-4 else 'MISMATCH -- recheck your arithmetic'}")


def depth_precision(near, far):
    print(f"\n== depth precision for near={near:g}, far={far:g} (OpenGL-style, depth01 = (ndc_z+1)/2) ==")
    print("  depth01(d) = far/(far-near) * (1 - near/d) ;  resolvable step in metres at distance d = (far-near) d^2 / (far near) / 2^bits")
    print(f"  {'d (m)':>10s} {'ndc z':>12s} {'depth01':>12s} {'step@16bit (m)':>16s} {'step@24bit (m)':>16s}")
    ds = sorted(set([near, near + 1.0, 2 * near, 5 * near, 10 * near, 0.1 * far, 0.5 * far, far]))
    for d in ds:
        if d < near or d > far:
            continue
        z01 = far / (far - near) * (1 - near / d)
        st = lambda bits: (far - near) * d * d / (far * near) / 2 ** bits
        print(f"  {d:10.4f} {2*z01-1:12.6f} {z01:12.6f} {st(16):16.6g} {st(24):16.6g}")
    d1 = near + 1.0
    z01 = far / (far - near) * (1 - near / d1)
    print(f"  first metre (d from {near:g} to {d1:g}) uses {z01*100:.4f}% of the depth range"
          f" = ~{z01 * 2**24:,.0f} of 2^24 codes ({z01 * 2**16:,.0f} of 2^16)")
    z_half = far / (far - near) * (1 - near / (far / 2))
    print(f"  half the far distance ({far/2:g} m) is already at depth01 {z_half:.6f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="data/pusaka_model.obj")
    ap.add_argument("--tex", default="data/relief.ppm")
    ap.add_argument("--vertex", type=int, default=0)
    ap.add_argument("--hand", type=float, nargs=3, metavar=("X", "Y", "Z"), help="your hand-computed world position M@p")
    ap.add_argument("--w", type=int, default=512)
    ap.add_argument("--h", type=int, default=512)
    ap.add_argument("--yaw", type=float, default=35.0)
    ap.add_argument("--scale", type=float, default=1.4)
    ap.add_argument("--eye", type=float, nargs=3, default=(2.6, 2.0, 3.4))
    ap.add_argument("--center", type=float, nargs=3, default=(0, 0.7, 0))
    ap.add_argument("--fovy", type=float, default=45.0)
    ap.add_argument("--near", type=float, default=1.0)
    ap.add_argument("--far", type=float, default=14.0)
    ap.add_argument("--out", default="out/lab1_trace.txt")
    args = ap.parse_args()

    buf = io.StringIO()

    class Tee:
        def write(self, s):
            sys.__stdout__.write(s); buf.write(s)
        def flush(self):
            sys.__stdout__.flush()

    with redirect_stdout(Tee()):
        trace(args)
        depth_precision(args.near, args.far)
        if (args.near, args.far) != (0.01, 1000.0):
            depth_precision(0.01, 1000.0)       # the module's own example
    ensure_out(os.path.dirname(args.out) or ".")
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(buf.getvalue())
    print(f"\nsaved {args.out}")


if __name__ == "__main__":
    main()
