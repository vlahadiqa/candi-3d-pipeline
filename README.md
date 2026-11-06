# Candi 3D Rendering Pipeline (Pusaka3D &mdash; Modul 3)

Repositori ini berisi implementasi pipeline grafika komputer 3D dari nol (*scratch*) serta visualisasi interaktif *real-time* berbasis WebGL (Three.js) untuk model warisan budaya Candi Prambanan. Modul ini mencakup transformasi koordinat 6-ruang, proyeksi perspektif, interpolasi tekstur terkoreksi perspektif, z-buffering, mipmapping, back-face culling, pengujian ray tracing CPU berbasis Möller–Trumbore, serta perbandingan kuantitatif terhadap rasterisasi perangkat keras GPU.

**Mahasiswa**: Vlahadiqa Runayasha Khandeva Wardana  
**Mata Kuliah**: Praktikum Grafika Komputer (Modul 3 &mdash; Transformasi 3D, Proyeksi, & Real-Time)

---

## 1. Geometri Candi & Tekstur Mandiri

Berbeda dari model uji bawaan dasar (180 segitiga), proyek ini menggunakan rekonstruksi candi mandiri berorientasi budaya lokal:

- **Model Candi (`data/mymodel.obj`)**:
  - Dihasilkan melalui skrip prosedural [`make_mymodel.py`](make_mymodel.py).
  - Geometri tersusun dari 34 balok bertingkat (*tiered blockout*) yang merepresentasikan struktur Candi Prambanan: batur/kaki candi berundak, selasar keliling, tubuh candi dengan relung pintu masuk (*entrance portal niche*), atap bertingkat tiga undak, serta kemuncak ratna.
  - Total **272 verteks** dan **408 segitiga** (memenuhi batas minimum $\ge 200$ segitiga).
  - *Bounding box*: `min [-1.0, 0.0, -1.0]`, `max [1.0, 1.49, 1.0]`.
  - Konsistensi *winding counter-clockwise* (CCW) dari luar dengan **signed volume $+1.2186$** (tanpa poligon terbalik / *inside-out*).
  - Rentang koordinat UV seragam $[0.0, 1.0]$ pada seluruh permukaan kubus pembentuk.

- **Tekstur Relief Batu (`data/mytex.ppm`)**:
  - Diekstraksi langsung dari foto autentik relief batu candi ([`kontak_foto.jpg`](kontak_foto.jpg)) menggunakan skrip pemotong [`make_mytexture.py`](make_mytexture.py) dengan parameter *bounding box* `--crop 350 670 600 920`.
  - Berdimensi 256&times;256 piksel dengan rata-rata intensitas RGB `[111.0, 112.9, 112.7]`, bebas dari elemen langit atau vegetasi untuk menjaga konsistensi material batu andesit candi.

---

## 2. Arsitektur Pipeline & Komponen

Pipeline ini dibangun secara modular dan mengeksplorasi dua paradigma rendering:

1. **Transformasi & Proyeksi Koordinat ([`transforms.py`](transforms.py))**:
   - Menggunakan konvensi vektor kolom OpenGL ($p' = M \cdot p$).
   - Menelusuri verteks melalui 6 ruang koordinat:
     $$\text{Object} \xrightarrow{M} \text{World} \xrightarrow{V} \text{View/Camera} \xrightarrow{P} \text{Clip} \xrightarrow{/w} \text{NDC} \xrightarrow{\text{Viewport}} \text{Screen}$$
   - Matriks kamera *look-at* dibangun ortonormal ($R \cdot R^T = I, \det(R) = 1$).
   - Matriks proyeksi perspektif standar memetakan volume frustum ke ruang kanonik $[-1, 1]^3$.

2. **Software Rasterizer Berbasis CPU ([`raster3d.py`](raster3d.py))**:
   - Rasterisasi segitiga berbasis *bounding box* dengan koordinat barisentrik $(\alpha, \beta, \gamma)$.
   - *Depth buffering* ($z$-buffer) untuk resolusi visibilitas permukaan tersembunyi.
   - Interpolasi parameter tekstur terkoreksi perspektif via pembagian koordinat homogen ($u/w, v/w, 1/w$).
   - *Mipmapping* piramidal 4 tingkat untuk meredam *aliasing* frekuensi tinggi dan kelap-kelip (*shimmer*).
   - Optimasi *back-face culling* untuk memangkas poligon yang membelakangi kamera sebelum tahap fragmentasi.

3. **CPU Ray Tracer Möller–Trumbore ([`raytrace.py`](raytrace.py))**:
   - Pinhole camera ray generation.
   - Pengujian interseksi sinar-segitiga Möller–Trumbore secara analitik.
   - Pencarian tabrakan terdekat (*nearest hit*) untuk *primary rays*.
   - Evaluasi bayangan keras (*hard shadows*) melalui penembakan *secondary shadow rays* ke arah sumber cahaya directional $(0.4, 0.9, 0.6)$.

4. **Interactive WebGL Viewer ([`web/`](web/))**:
   - Menggunakan library Three.js (r160) dengan kanvas render $512 \times 512$.
   - Dilengkapi *OrbitControls* interaktif untuk rotasi kamera bebas.
   - Material `MeshStandardMaterial` dengan tekstur batu lokal dan pencahayaan terkalibrasi ($\pi$-scaled illuminance).
   - Tombol **Export PPM** yang secara otomatis mengunci posisi kamera ke `(2.6, 2.0, 3.4)` dan target `(0, 0.7, 0)` agar orientasi citra bit-identik dengan renderer CPU.

---

## 3. Petunjuk Menjalankan (*Quickstart*)

### Prasyarat
- Python 3.12+ (disertai NumPy $\ge 1.24$ dan Pillow $\ge 10.0$).
- Node.js (untuk menjalankan server lokal WebGL via `npx serve`).

### Langkah Eksekusi

1. **Instalasi Dependensi**:
   ```powershell
   pip install -r requirements.txt
   ```

2. **Generate Model Candi & Tekstur**:
   ```powershell
   python make_mymodel.py
   python make_mytexture.py --img kontak_foto.jpg --crop 350 670 600 920
   ```

3. **Verifikasi Unit Test Dasar**:
   ```powershell
   python make_model.py
   python tests.py
   ```

4. **Lab 1: Penelusuran Transformasi 6-Ruang**:
   ```powershell
   python lab1_trace.py --model data/mymodel.obj --tex data/mytex.ppm --vertex 0
   ```
   *Keluaran tersimpan di `out/lab1_trace.txt`.*

5. **Lab 2: Pipeline Rasterisasi, Analisis Bug, Mipmapping, & Culling**:
   ```powershell
   python lab2_pipeline.py --model data/mymodel.obj --tex data/mytex.ppm
   ```

6. **Lab 3: Viewer WebGL & Perbandingan Citra**:
   - Jalankan server lokal:
     ```powershell
     npx serve .
     ```
   - Buka alamat browser (misalnya `http://localhost:3000/web/` atau port yang dialokasikan).
   - Klik tombol **Export PPM** untuk mengunduh `mymodel_three.ppm`, lalu letakkan file tersebut ke dalam folder `web/mymodel_three.ppm`.
   - Jalankan perbandingan WebGL vs software raster:
     ```powershell
     python lab3_bench.py webcompare --web web/mymodel_three.ppm --model data/mymodel.obj --tex data/mytex.ppm
     ```

7. **Lab 3: Prediksi & Pengukuran Kinerja (*Benchmark*)**:
   - Catat hipotesis prediksi terlebih dahulu:
     ```powershell
     python lab3_bench.py predict --ratio 6.8 --shadow raytrace --reflection raytrace --note "Estimasi rasio waktu ray tracer vs rasteriser meningkat dari ~5.4x (model 180 segitiga) ke ~6.8x pada candi 408 segitiga karena ray tracer menguji seluruh segitiga secara brute-force O(N) per piksel tanpa akselerasi BVH, sedangkan rasteriser memproyeksikan segitiga ke layar dan memangkas poligon luar frustum serta back-face culling sebelum tahap fragmentasi. Ray tracing diprediksi lebih unggul untuk bayangan tajam dan pantulan sekunder karena menggunakan secondary shadow ray dan hukum pantulan terarah."
     ```
   - Lakukan pengukuran empiris (10 repetisi):
     ```powershell
     python lab3_bench.py measure --model data/mymodel.obj --tex data/mytex.ppm --repeat 10
     ```

8. **Uji Reproduksibilitas Lingkungan Bersih**:
   ```powershell
   python repro_clean.py
   ```

---

## 4. Hasil Verifikasi Empiris

Seluruh item pengujian di bawah ini telah diverifikasi langsung pada lingkungan eksekusi lokal:

| Item Pengujian | Status | Tanggal Verifikasi | Hasil Kuantitatif & Spesifikasi Toolchain |
|---|---|---|---|
| `python tests.py` | **ALL CHECKS PASSED (8 ok)** | 2026-11-06 | Windows 11 (build 26300), Python 3.12.6, NumPy 2.4.3, Pillow 12.1.1 |
| Raster vs Raytrace (256&times;256) | **PSNR inf dB, SSIM 1.0000, max \|diff\| 0** | 2026-11-06 | Python 3.12.6, NumPy 2.4.3 (`data/mymodel.obj`, 408 segitiga) |
| Lab 1 (`lab1_trace.py`) | **run green** | 2026-11-06 | Telusur verteks #0 pada 6 ruang koordinat, verifikasi ortonormalitas $V$, volume $+1.2186$ |
| Lab 2: 3 Kasus Bug Pipeline | **run green** | 2026-11-06 | Inside-out SSIM 0.7053, Z-fight SSIM 0.7787 (2852 piksel salah), Stretched SSIM 0.4758 |
| Lab 2: Mipmapping | **run green** | 2026-11-06 | 4 tingkat energi terjaga (0.21684), PSNR naik 30.44 $\to$ 32.57 dB, shimmer turun 1.576 $\to$ 0.692 |
| Lab 2: Back-face Culling | **run green** | 2026-11-06 | 256/408 segitiga terpotong (62.7%), penulisan fragmen turun 13.5% (74.037 $\to$ 64.024), citra identik (SSIM 1.0000) |
| WebGL Viewer (`webcompare`) | **PSNR 30.03 dB, SSIM 0.9887** | 2026-11-06 | Brave Browser (Chromium engine), Three.js r160, kanvas 512&times;512, mean \|diff\| 3.145 |
| Lab 3: Prediksi vs Pengukuran | **run green** | 2026-11-06 | Prediksi rasio 6.8&times;, terukur 9.49&times; (faktor deviasi 1.40&times;), *hard shadow* 4.6% (687/14.821 piksel) |
| `repro_clean.py` | **ALL STEPS GREEN** | 2026-11-06 | *Clean-room isolated virtual environment*, fresh pip install, make_model, tests green |

---

## 5. Analisis & Keterbatasan Teknis

### Rekonsiliasi Prediksi vs Pengukuran Lab 3
- **Deviasi Rasio (Prediksi 6.8&times; vs Terukur 9.49&times;)**:
  Prediksi awal 6.8&times; dibuat dengan asumsi bahwa peningkatan kompleksitas waktu ray tracing akan berbanding lurus secara moderat terhadap peningkatan poligon dari 180 ke 408 segitiga ($2.27\times$). Namun secara empiris terukur rasio $9.49\times$ (deviasi faktor $1.40\times$).
  Penyebabnya adalah ketiadaan struktur akselerasi spasial (BVH/kd-tree) pada ray tracer: untuk resolusi $192 \times 192$, ray tracer CPU melakukan pengujian Möller–Trumbore secara *brute-force* sebanyak $192 \times 192 \times 408 \approx 1.50 \times 10^7$ kali. Sebaliknya, software rasterizer melakukan proyeksi geometri terlebih dahulu dan langsung mengeliminasi 62.7% segitiga tampak belakang via *back-face culling*, menyisakan hanya 152 segitiga yang diproses ke tahap fragmentasi barisentrik.

### Keterbatasan Sistem
1. **Skalabilitas Poligon pada CPU Ray Tracer**: Tanpa BVH (*Bounding Volume Hierarchy*), kompleksitas ray tracer berordo $O(N_{\text{tri}} \cdot N_{\text{pixels}})$, sehingga penambahan kompleksitas model menjadi ribuan segitiga akan menurunkan *frame rate* secara drastis.
2. **Ketiadaan Akselerasi Perangkat Keras pada Software Rasterizer**: Renderer `raster3d.py` dieksekusi secara sekuensial pada CPU dengan interpreter Python, sehingga waktu render berada pada kisaran ratusan milidetik, jauh tertinggal dibanding WebGL GPU yang mengeksekusi jutaan fragmen secara paralel masif.
3. **Penyederhanaan Model Pencahayaan**: Rasterizer software saat ini belum mengimplementasikan *shadow map* atau *environment reflection probe*, sehingga efek bayangan diri (*self-shadowing*) dan pantulan spekular hanya dapat dihasilkan melalui ray tracing.
