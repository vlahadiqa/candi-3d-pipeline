# Module 3 -- 3D Transforms, Projection, Texture & Real-Time (reference repo)

Course: *Grafika Komputer / Computer Graphics* (`25MP7716G030`), S1 Informatika
semester 5. Companion to `../../Module3_EN.tex`. **Feeds the UTS directly.**

**Rule:** the transform stack, the z-buffer rasteriser and the ray tracer are
**NumPy only**. Pillow is optional (reference cross-checks). The real-time
renderer (`web/`) is Three.js and is the GitHub Pages deliverable.

**Conventions** (pinned at the top of `transforms.py`, never mixed): column
vectors, pre-multiply (`p' = M @ p`), chains right-to-left; right-handed;
camera looks down `-z`; NDC `[-1,1]^3`, near at `z=-1`; viewport flips `y`.

## Quick start

```bash
cd code/Module3
python -m pip install -r requirements.txt
python make_model.py                 # data/pusaka_model.obj (180 tris) + data/relief.ppm
python tests.py                      # -> ALL CHECKS PASSED (9 ok)
python worked_example.py             # the running point through every space
python raster3d.py --model data/pusaka_model.obj --w 512 --h 512
python raytrace.py --model data/pusaka_model.obj --w 256 --h 256
python compare.py out/temple_raster.ppm out/temple_rt.ppm   # ~77 dB (byte-identical)
python broken_scene.py --all         # inside-out / zfight / stretched, with evidence
npx serve .   # open http://localhost:3000/web/  (Three.js, OrbitControls, Export PPM)
```

## Unit table

| File | Job | Reproduces |
|---|---|---|
| `transforms.py` | mat4 T/S/R, `perspective`, `look_at`, `project`, `viewport`, bare `perspective_divide_2d` | E1, E2, E3 |
| `objio.py` | minimal OBJ loader (`v`/`vt`/`f`, fan triangulation, `v` flip) + `save_obj` | Case Study input |
| `make_model.py` | deterministic 15-box temple OBJ + planar UVs + `relief.ppm` texture | Case Study |
| `raster3d.py` | MVP -> near clip -> w-divide -> viewport -> barycentric z-buffer -> perspective-correct texture -> Lambert; `--demo-triangle`, `--demo-overlap` | Fully Worked Example Steps 2-3 |
| `raytrace.py` | pinhole rays + Moller-Trumbore, nearest hit, same shading | Step 4 |
| `worked_example.py` | the running point (2,3,4) through object->world->view->clip->ndc->screen | Step 1 |
| `broken_scene.py` | 3 bugs (`inside-out`, `zfight`, `stretched`) each fixed by one change, with SSIM / depth evidence | Lab 2 diagnose-and-fix |
| `metrics.py` / `compare.py` | PSNR + global SSIM; frame diff + amplified difference image | Step 4, Case Study |
| `ppm_io.py` / `srgb.py` | P6 PPM r/w and sRGB<->linear (shared with Module 1) | -- |
| `tests.py` | E1-E5 + pipeline shapes + 1-triangle render + reference-frame match | MASTER 11.2 |
| `web/index.html`, `web/viewer.js` | Three.js textured temple, OrbitControls, camera/light/model matched to `raster3d.py`, PPM export | Lab 3 deliverable |

## What `python tests.py` asserts

- **E1** -- `(2,3,4)` translate `(1,0,-1)` then `Ry(90)` -> `(3,3,-3)`; bare
  perspective divide `d=2` -> `(2,2)`; the other multiply order -> `(5,3,-3)`.
- **E2** -- `look_at(eye=(1,0,0), ...) @ p == translate(-1,0,0) @ p` (the
  camera / model duality) for `p=(5,0,0)`.
- **E3** -- `perspective(.,.,n,f)` maps eye `z=-n -> ndc -1`, `z=-f -> +1`,
  `z=-3 -> 0.5` (the `1/z` crush).
- **E4** -- perspective-correct `u` at the screen midpoint of a floor edge
  with `w_L=1, w_R=9` is `0.1`, not the naive `0.5`.
- **E5** -- barycentric depth `0.20/0.50/0.90` at `(.25,.25,.5)` is `0.625`.
- **projection pipeline** -- `project` / `viewport` shapes and ranges.
- **one-triangle render** -- fills a plausible region at flat depth.
- **reference frame** -- re-rendering the committed temple is byte-identical
  to `ref/temple_ref.ppm` (generated on first run -- commit `ref/`).

## Notes on fixes applied while verifying

- **Barycentric-to-vertex mapping in `raster3d.py`** was a cyclic permutation
  (vertex A received weight lambda_B, etc.). With high-frequency textures this
  showed up as raster-vs-raytrace PSNR ~15 dB (same silhouette, wrong texels).
  Fixed to `lA = edge(B,C,P)/area`, `lB = edge(C,A,P)/area`, `lC = 1-lA-lB`
  mapped straight to vertices 0/1/2 -> **raster vs raytrace is now 76.9 dB,
  byte-identical bar ~10 edge pixels.**
- Shading made winding-independent in both renderers: orient the face normal
  toward the camera, then one-sided Lambert -- so the forward and backward
  renderers agree regardless of face winding.
- `broken_scene.py --bug zfight`: needed genuinely *crossing* quads + a
  low-precision (16-bit) depth buffer + per-face colours to make the fighting
  band visible and countable (2852 wrong pixels at `near=1e-3` vs ~180 after
  the fix).
- The committed fallback model is **180 triangles**, not the plan's ~800 (a
  light blockout; students' own models are >= 200) -- noted in the course plan
  deviations.

## Verified

| Item | Status | Date | Toolchain |
|---|---|---|---|
| `Module3_EN.tex` compiles | **yes** -- Tectonic 0.17.0, no overfull hbox > ~15 pt | 2026-09-04 | Windows 11 |
| `python tests.py` | **ALL CHECKS PASSED (9 ok)** | 2026-09-04 | Python 3.12.9, NumPy 2.4.6, Pillow 12.3.0 |
| `make_model` / `worked_example` / `raster3d` / `raytrace` / `broken_scene` / `compare` | **run green** -- transcripts in `Module3_EN.tex` are the actual output | 2026-09-04 | same |
| raster vs raytrace | **PSNR 76.9 dB, SSIM 1.000, max \|diff\| 10** (two independent renderers) | 2026-09-04 | same |
| `web/` Three.js viewer | **authored, not browser-verified on this host** (no display); loads `three@0.160.0` + OBJLoader/OrbitControls from jsdelivr, parses the P6 texture into a DataTexture, camera/light/model matched to `raster3d.py` | 2026-09-04 | -- |

Before the module fully meets the MASTER Definition of Done: open `web/` in a
browser (`npx serve .` -> `/web/`), orbit the textured temple, **Export PPM**
at the default camera, and run `python compare.py out/temple_raster.ppm
web/temple_three.ppm` -- expect ~30 dB with the residual on anti-aliased
silhouette edges. Record browser + version.
