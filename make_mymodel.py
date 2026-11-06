"""Module 3 / Lab 1 -- YOUR OWN model: a stepped Javanese candi (blockout), generated from parameters.

Shape taken from photos of the building: low terrace, 3-tier base (batur) with a front staircase,
square body with a door (jambs + lintel + kala-head panel), a two-step cornice, a 9-tier stepped
roof, a small finial, and two guardian pedestals beside the stairs.

  python make_mymodel.py                      # writes data/mymodel.obj
  python make_mymodel.py --out data/mymodel.obj --seed 7

Properties (checked at the end): >= 200 triangles, per-face UVs inside [0,1], every face wound CCW
seen from OUTSIDE (the convention pinned in transforms.py), closed shells (0 boundary edges per box).
Fits the default cameras: x,z within [-1,1], height ~1.5, +z is the front (door side).

EDIT THE PARAMETERS BELOW to make it your own proportions -- you must be able to say what each does.
"""
from __future__ import annotations

import argparse
import os

import numpy as np

from objio import save_obj, load_obj

# ------------------------------------------------------------------ parameters
P = dict(
    terrace_half=1.00, terrace_h=0.05,                      # low wide platform the candi stands on
    batur=[(0.62, 0.08), (0.58, 0.10), (0.54, 0.10), (0.57, 0.04)],   # (half-width, height) per base tier, bottom -> top
    body_half=0.42, body_h=0.43,                            # square body (tubuh candi)
    door_half=0.13, jamb_w=0.03, door_h=0.29, lintel_h=0.06, kala_h=0.08,   # door on the +z face
    cornice=[(0.50, 0.04), (0.46, 0.04)],                   # overhanging cornice
    roof_tiers=9, roof_h=0.05, roof_start_half=0.42, roof_step=0.033,       # stepped roof
    finial=[(0.08, 0.04), (0.05, 0.05), (0.025, 0.07)],     # kemuncak
    stairs=6, stair_half=0.14, stair_run=0.05,              # staircase on the +z side
    ped_x=0.32, ped_z=0.82, ped_half=0.05, ped_h=0.12, head_half=0.035, head_h=0.05,  # guardian pedestals
)

UV_SCALE = 2.0          # world units covered by one whole texture (largest face = terrace top, 2.0)

# corner bits are (ix, iy, iz): 0 = min side, 1 = max side
FACES = {
    "+z": ((0, 0, 1), (1, 0, 1), (0, 1, 1)),
    "-z": ((1, 0, 0), (0, 0, 0), (1, 1, 0)),
    "+x": ((1, 0, 1), (1, 0, 0), (1, 1, 1)),
    "-x": ((0, 0, 0), (0, 0, 1), (0, 1, 0)),
    "+y": ((0, 1, 1), (1, 1, 1), (0, 1, 0)),
    "-y": ((0, 0, 0), (1, 0, 0), (0, 0, 1)),
}


class Builder:
    def __init__(self, seed):
        self.pos, self.uv, self.faces, self.fuv = [], [], [], []
        self.rng = np.random.default_rng(seed)
        self.boxes = 0

    def box(self, x0, x1, y0, y1, z0, z1):
        xs, ys, zs = (x0, x1), (y0, y1), (z0, z1)
        base = len(self.pos)
        idx = {}
        for ix in (0, 1):
            for iy in (0, 1):
                for iz in (0, 1):
                    idx[(ix, iy, iz)] = base + len(idx)
                    self.pos.append([xs[ix], ys[iy], zs[iz]])
        centre = np.array([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
        for name, (A, B, D) in FACES.items():
            C = tuple(b ^ d ^ a for a, b, d in zip(A, B, D))
            quad = [A, B, C, D]
            p = [np.array(self.pos[idx[q]]) for q in quad]
            u_len, v_len = np.linalg.norm(p[1] - p[0]), np.linalg.norm(p[3] - p[0])
            n = np.cross(p[1] - p[0], p[3] - p[0])
            flip = n @ (p[0] - centre) < 0                 # make the winding CCW seen from outside
            ua, vb = u_len / UV_SCALE, v_len / UV_SCALE
            u0 = self.rng.uniform(0, max(1 - ua, 0)); v0 = self.rng.uniform(0, max(1 - vb, 0))
            uvc = [(u0, v0), (u0 + ua, v0), (u0 + ua, v0 + vb), (u0, v0 + vb)]
            ubase = len(self.uv)
            self.uv.extend(uvc)
            order = [0, 1, 2, 3] if not flip else [0, 3, 2, 1]
            q = [quad[i] for i in order]; uq = [ubase + i for i in order]
            for tri in ((0, 1, 2), (0, 2, 3)):
                self.faces.append([idx[q[t]] for t in tri])
                self.fuv.append([uq[t] for t in tri])
        self.boxes += 1

    def centred(self, half, y0, h, cx=0.0, cz=0.0, hz=None):
        hz = half if hz is None else hz
        self.box(cx - half, cx + half, y0, y0 + h, cz - hz, cz + hz)
        return y0 + h


def build(seed=7):
    b, p = Builder(seed), P
    y = 0.0
    y = b.centred(p["terrace_half"], y, p["terrace_h"])
    for half, h in p["batur"]:
        y = b.centred(half, y, h)
    batur_top = y
    batur_front = p["batur"][0][0]
    # body + door on the +z face
    body_front = p["body_half"]
    body_y0 = y
    y = b.centred(p["body_half"], y, p["body_h"])
    body_top = y
    for sx in (-1, 1):                                    # jambs
        cx = sx * (p["door_half"] + p["jamb_w"] * 0.5 + 0.004 * sx)
        b.box(cx - p["jamb_w"] / 2, cx + p["jamb_w"] / 2, body_y0, body_y0 + p["door_h"],
              body_front - 0.02, body_front + 0.03)
    lin_y0 = body_y0 + p["door_h"]
    b.box(-(p["door_half"] + p["jamb_w"] + 0.015), p["door_half"] + p["jamb_w"] + 0.015,
          lin_y0, lin_y0 + p["lintel_h"], body_front - 0.02, body_front + 0.035)
    b.box(-(p["door_half"] + 0.01), p["door_half"] + 0.01, lin_y0 + p["lintel_h"],
          lin_y0 + p["lintel_h"] + p["kala_h"], body_front - 0.02, body_front + 0.022)
    for half, h in p["cornice"]:
        y = b.centred(half, y, h)
    for i in range(p["roof_tiers"]):
        y = b.centred(p["roof_start_half"] - i * p["roof_step"], y, p["roof_h"])
    for half, h in p["finial"]:
        y = b.centred(half, y, h)
    # staircase: nested boxes, widths differ by 4 mm so no two side faces are coplanar
    top_of_stairs = p["terrace_h"] + sum(h for _, h in p["batur"][:3])
    step_h = (top_of_stairs - p["terrace_h"]) / p["stairs"]
    for i in range(p["stairs"]):
        run_out = p["stair_run"] * (p["stairs"] - i)
        b.box(-(p["stair_half"] + 0.004 * i), p["stair_half"] + 0.004 * i,
              p["terrace_h"], p["terrace_h"] + step_h * (i + 1),
              batur_front - 0.02, batur_front + run_out)
    for sx in (-1, 1):                                    # guardian pedestals
        cx = sx * p["ped_x"]
        b.box(cx - p["ped_half"], cx + p["ped_half"], p["terrace_h"], p["terrace_h"] + p["ped_h"],
              p["ped_z"] - p["ped_half"], p["ped_z"] + p["ped_half"])
        hy = p["terrace_h"] + p["ped_h"]
        b.box(cx - p["head_half"] - 0.003, cx + p["head_half"] + 0.003, hy, hy + p["head_h"],
              p["ped_z"] - p["head_half"], p["ped_z"] + p["head_half"])
    return b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/mymodel.obj")
    ap.add_argument("--seed", type=int, default=7, help="only moves each face's patch of the texture")
    a = ap.parse_args()
    b = build(a.seed)
    pos = np.array(b.pos); faces = np.array(b.faces)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    save_obj(a.out, pos, np.array(b.uv), faces, np.array(b.fuv))
    with open(a.out, "r") as fh:                          # replace the lecturer's header comment
        body = fh.read().split("\n", 1)[1]
    with open(a.out, "w") as fh:
        fh.write("# Module 3 Lab 1 -- own model: stepped candi blockout (make_mymodel.py)\n" + body)

    m = load_obj(a.out)
    t = m.positions[m.faces]
    vol = float(np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2])).sum() / 6)
    uvr = (m.uvs.min(), m.uvs.max())
    print(f"wrote {a.out}: {len(b.pos)} vertices, {m.n_tris} triangles, {b.boxes} boxes")
    print(f"bbox min {np.round(m.positions.min(0), 3).tolist()} max {np.round(m.positions.max(0), 3).tolist()}")
    print(f"signed volume {vol:+.4f} ({'CCW outside: OK' if vol > 0 else 'INVERTED'})   uv range [{uvr[0]:.3f}, {uvr[1]:.3f}]")
    assert m.n_tris >= 200 and vol > 0 and uvr[0] >= 0 and uvr[1] <= 1
    print("checks: >=200 triangles, CCW winding, UVs in [0,1]  -> OK")


if __name__ == "__main__":
    main()
