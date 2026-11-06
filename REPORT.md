# Laporan Praktikum Modul 3 &mdash; Transformasi 3D, Proyeksi, & Real-Time

**Nama Mahasiswa**: Vlahadiqa Runayasha Khandeva Wardana  
**Subjek Budaya**: Rekonstruksi Geometri Candi Prambanan (34 Balok Bertingkat, 408 Segitiga)  
**Repositori GitHub**: [https://github.com/vlahadiqa/candi-3d-pipeline](https://github.com/vlahadiqa/candi-3d-pipeline)  
**WebGL Viewer**: [https://vlahadiqa.github.io/candi-3d-pipeline/web/](https://vlahadiqa.github.io/candi-3d-pipeline/web/)  

---

## BAGIAN I: TULISAN PRA-MODUL (Q1 &ndash; Q5)

### Q1. Koordinat Homogen dan Matriks $4 \times 4$

#### Q1.(a) Alasan Matriks $3 \times 3$ Tidak Dapat Merepresentasikan Translasi dan Peran Koordinat $w$
- **Keterbatasan Matriks $3 \times 3$**:  
  Operasi perkalian matriks $3 \times 3$ pada vektor posisi $\mathbf{p} = [x, y, z]^T$ adalah pemetaan linier murni:
  $$f(\mathbf{p}) = \mathbf{A}\mathbf{p}$$
  Sifat pemetaan linier mensyaratkan $f(\mathbf{0}) = \mathbf{0}$. Artinya, titik asal (*origin*) $[0, 0, 0]^T$ selalu dipetakan kembali ke titik asal. Translasi $\mathbf{p}' = \mathbf{p} + \mathbf{t}$ adalah transformasi affin, bukan transformasi linier, sehingga tidak dapat dinyatakan hanya dengan perkalian matriks $3 \times 3$.
- **Peran Koordinat Keempat $w = 1$**:  
  Dengan memperluas dimensi vektor ke ruang proyektif 4D menjadi $[x, y, z, w]^T$, translasi dapat direpresentasikan sebagai operasi geser (*shear*) pada dimensi keempat:
  $$\begin{bmatrix} x' \\ y' \\ z' \\ 1 \end{bmatrix} = \begin{bmatrix} 1 & 0 & 0 & t_x \\ 0 & 1 & 0 & t_y \\ 0 & 0 & 1 & t_z \\ 0 & 0 & 0 & 1 \end{bmatrix} \begin{bmatrix} x \\ y \\ z \\ 1 \end{bmatrix} = \begin{bmatrix} x + t_x \\ y + t_y \\ z + t_z \\ 1 \end{bmatrix}$$
- **Arti Nilai $w = 0$**:  
  Nilai $w = 0$ merepresentasikan **vektor arah** (*displacement / direction*), bukan titik posisi. Vektor arah bersifat invarian terhadap translasi karena kolom keempat matriks translasi dikalikan dengan $w = 0$:
  $$\mathbf{T} \begin{bmatrix} d_x \\ d_y \\ d_z \\ 0 \end{bmatrix} = \begin{bmatrix} d_x \\ d_y \\ d_z \\ 0 \end{bmatrix}$$
  Selain itu, dalam geometri proyektif, titik dengan $w = 0$ merepresentasikan *point at infinity*.

---

#### Q1.(b) Matriks $4 \times 4$ untuk Translasi, Skala, dan Rotasi $R_y(\theta)$

1. **Translasi $\mathbf{T}(t_x, t_y, t_z)$**:
   $$\mathbf{T} = \begin{bmatrix} 1 & 0 & 0 & t_x \\ 0 & 1 & 0 & t_y \\ 0 & 0 & 1 & t_z \\ 0 & 0 & 0 & 1 \end{bmatrix}$$
   *Arah sumbu $+x$ (kolom 1)*: $\begin{bmatrix} 1 & 0 & 0 & 0 \end{bmatrix}^T$. Sumbu $+x$ tetap mengarah murni ke arah $+x$ dunia dengan panjang 1 (orientasi dan skala tidak berubah).

2. **Skala $\mathbf{S}(s_x, s_y, s_z)$**:
   $$\mathbf{S} = \begin{bmatrix} s_x & 0 & 0 & 0 \\ 0 & s_y & 0 & 0 \\ 0 & 0 & s_z & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix}$$
   *Arah sumbu $+x$ (kolom 1)*: $\begin{bmatrix} s_x & 0 & 0 & 0 \end{bmatrix}^T$. Sumbu $+x$ tetap mengarah sepanjang sumbu $x$, namun panjang vektornya berubah sebanding dengan faktor skala $s_x$.

3. **Rotasi Mengelilingi Sumbu $y$, $R_y(\theta)$**:
   $$\mathbf{R}_y(\theta) = \begin{bmatrix} \cos\theta & 0 & \sin\theta & 0 \\ 0 & 1 & 0 & 0 \\ -\sin\theta & 0 & \cos\theta & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix}$$
   *Arah sumbu $+x$ (kolom 1)*: $\begin{bmatrix} \cos\theta & 0 & -\sin\theta & 0 \end{bmatrix}^T$. Sumbu $+x$ model kini berputar pada bidang $xz$: berproyeksi sebesar $\cos\theta$ sepanjang sumbu $x$ dan $-\sin\theta$ sepanjang sumbu $z$. Untuk rotasi $\theta = +90^\circ$, kolom 1 menjadi $\begin{bmatrix} 0 & 0 & -1 & 0 \end{bmatrix}^T$ (sumbu $+x$ berputar mengarah tepat ke sumbu $-z$ dunia).

---

#### Q1.(c) Hitungan Tangan Perkalian Transformasi pada Titik $(2, 3, 4, 1)$

Diberikan titik awal $\mathbf{p} = \begin{bmatrix} 2 & 3 & 4 & 1 \end{bmatrix}^T$.  
Transformasi yang diberikan:
- Rotasi $R_y(90^\circ)$ dengan $\cos(90^\circ) = 0$ dan $\sin(90^\circ) = 1$:
  $$\mathbf{R}_y(90^\circ) = \begin{bmatrix} 0 & 0 & 1 & 0 \\ 0 & 1 & 0 & 0 \\ -1 & 0 & 0 & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix}$$
- Translasi $\mathbf{T}(1, 0, -1)$:
  $$\mathbf{T} = \begin{bmatrix} 1 & 0 & 0 & 1 \\ 0 & 1 & 0 & 0 \\ 0 & 0 & 1 & -1 \\ 0 & 0 & 0 & 1 \end{bmatrix}$$

**Kasus 1: Rotasi terlebih dahulu, kemudian Translasi $(\mathbf{T} \cdot \mathbf{R}_y)$**
1. Rotasi titik $\mathbf{p}$:
   $$\mathbf{p}_1 = \mathbf{R}_y(90^\circ) \mathbf{p} = \begin{bmatrix} 0(2) + 0(3) + 1(4) + 0(1) \\ 0(2) + 1(3) + 0(4) + 0(1) \\ -1(2) + 0(3) + 0(4) + 0(1) \\ 0(2) + 0(3) + 0(4) + 1(1) \end{bmatrix} = \begin{bmatrix} 4 \\ 3 \\ -2 \\ 1 \end{bmatrix}$$
2. Translasi hasil rotasi:
   $$\mathbf{p}' = \mathbf{T} \mathbf{p}_1 = \begin{bmatrix} 4 + 1 \\ 3 + 0 \\ -2 - 1 \\ 1 \end{bmatrix} = \begin{bmatrix} \mathbf{5} \\ \mathbf{3} \\ \mathbf{-3} \\ \mathbf{1} \end{bmatrix}$$

**Kasus 2: Translasi terlebih dahulu, kemudian Rotasi $(\mathbf{R}_y \cdot \mathbf{T})$**
1. Translasi titik $\mathbf{p}$:
   $$\mathbf{p}_2 = \mathbf{T} \mathbf{p} = \begin{bmatrix} 2 + 1 \\ 3 + 0 \\ 4 - 1 \\ 1 \end{bmatrix} = \begin{bmatrix} 3 \\ 3 \\ 3 \\ 1 \end{bmatrix}$$
2. Rotasi hasil translasi:
   $$\mathbf{p}'' = \mathbf{R}_y(90^\circ) \mathbf{p}_2 = \begin{bmatrix} 0(3) + 0(3) + 1(3) + 0(1) \\ 0(3) + 1(3) + 0(3) + 0(1) \\ -1(3) + 0(3) + 0(3) + 0(1) \\ 0(3) + 0(3) + 0(3) + 1(1) \end{bmatrix} = \begin{bmatrix} \mathbf{3} \\ \mathbf{3} \\ \mathbf{-3} \\ \mathbf{1} \end{bmatrix}$$

**Kesimpulan**: $\mathbf{p}' \neq \mathbf{p}''$ ($[5, 3, -3, 1]^T \neq [3, 3, -3, 1]^T$). Ini membuktikan secara aljabar bahwa perkalian matriks bersifat non-komutatif ($\mathbf{T}\mathbf{R} \neq \mathbf{R}\mathbf{T}$), sehingga urutan eksekusi transformasi sangat krusial.

---

### Q2. Kamera dan Proyeksi

#### Q2.(a) View Matrix $V = (\text{pose})^{-1}$ dan Dualitas Kamera
- **Alasan $V = (\text{pose})^{-1}$**:  
  Pose kamera di dunia didefinisikan oleh posisi $\mathbf{c}$ dan orientasi $\mathbf{R}_{\text{cam}}$:
  $$\mathbf{M}_{\text{cam}} = \begin{bmatrix} \mathbf{R}_{\text{cam}} & \mathbf{c} \\ \mathbf{0}^T & 1 \end{bmatrix}$$
  Tujuan dari *view transformation* adalah memetakan titik dunia ke sistem koordinat kamera di mana kamera berada di origin $[0,0,0]^T$ dan menghadap sumbu $-z$. Oleh karena itu, matriks pandang adalah inversi dari pose kamera:
  $$\mathbf{V} = \mathbf{M}_{\text{cam}}^{-1} = \begin{bmatrix} \mathbf{R}_{\text{cam}}^T & -\mathbf{R}_{\text{cam}}^T \mathbf{c} \\ \mathbf{0}^T & 1 \end{bmatrix}$$
- **Dualitas Kamera**:  
  Menggerakkan kamera sejauh $+\mathbf{d}$ sama artinya dengan memindahkan titik kamera ke $\mathbf{c} + \mathbf{d}$. Transformasi pandang terhadap titik objek $\mathbf{p}$ menjadi:
  $$\mathbf{p}_{\text{view}} = \mathbf{R}^T (\mathbf{p} - (\mathbf{c} + \mathbf{d})) = \mathbf{R}^T ((\mathbf{p} - \mathbf{d}) - \mathbf{c})$$
  Secara fisis, menggeser kamera sebesar $+\mathbf{d}$ menghasilkan citra yang identik dengan mempertahankan posisi kamera dan menggeser seluruh dunia/objek sebesar $-\mathbf{d}$.

---

#### Q2.(b) Penurunan Perspektif dari Segitiga Sebangun (*Similar Triangles*)
Perhatikan sistem kamera *pinhole* di origin $\mathbf{O} = [0, 0, 0]^T$ dengan bidang pandang citra diletakkan pada jarak $z = d$ di depan kamera (atau $z = -d$ dalam konvensi pandang sumbu $-z$).  
Sebuah titik sembarang di ruang pandang memiliki koordinat $(x, y, z)$.  
Melalui perbandingan segitiga sebangun pada penampang bidang $xz$:
$$\frac{x_{\text{proj}}}{d} = \frac{x}{z} \implies x_{\text{proj}} = \frac{d \cdot x}{z}$$
Demikian pula pada penampang bidang $yz$:
$$\frac{y_{\text{proj}}}{d} = \frac{y}{z} \implies y_{\text{proj}} = \frac{d \cdot y}{z}$$
Dengan demikian, koordinat proyeksi perspektif pada bidang citra adalah $\left( \frac{d \cdot x}{z}, \frac{d \cdot y}{z} \right)$. Komponen pembagian dengan kedalaman $z$ inilah yang menciptakan pemendekan perspektif (*perspective foreshortening*): objek yang lebih jauh ($z$ besar) akan terproyeksi lebih kecil pada layar.

---

#### Q2.(c) Matriks Proyeksi Perspektif Standar $P(\text{fovy}, \text{aspect}, n, f)$
Bentuk standar matriks proyeksi perspektif (OpenGL konvensi right-handed ke NDC $[-1, 1]^3$) dengan $t = n \cdot \tan(\text{fovy}/2)$ dan $r = t \cdot \text{aspect}$:
$$\mathbf{P} = \begin{bmatrix} \frac{n}{r} & 0 & 0 & 0 \\ 0 & \frac{n}{t} & 0 & 0 \\ 0 & 0 & -\frac{f+n}{f-n} & -\frac{2fn}{f-n} \\ 0 & 0 & -1 & 0 \end{bmatrix}$$
- **Fungsi Baris Keempat**: Baris keempat adalah $\begin{bmatrix} 0 & 0 & -1 & 0 \end{bmatrix}$. Saat dikalikan dengan vektor pandang $[x_e, y_e, z_e, 1]^T$, baris ini menghasilkan koordinat homogen klip:
  $$w_{\text{clip}} = -z_e$$
  Karena objek yang terlihat berada di depan kamera ($z_e < 0$), maka $w_{\text{clip}} = -z_e > 0$, yang menyimpan nilai kedalaman positif sebagai pembagi homogen pada tahap *perspective divide*.
- **Nilai NDC $z$**:
  - Titik pada *near plane* ($z_e = -n$):
    $$z_{\text{clip}} = -\frac{f+n}{f-n}(-n) - \frac{2fn}{f-n} = \frac{n^2 + fn - 2fn}{f-n} = \frac{n^2 - fn}{f-n} = -n$$
    Maka $z_{\text{ndc}} = \frac{z_{\text{clip}}}{w_{\text{clip}}} = \frac{-n}{n} = \mathbf{-1}$.
  - Titik pada *far plane* ($z_e = -f$):
    $$z_{\text{clip}} = -\frac{f+n}{f-n}(-f) - \frac{2fn}{f-n} = \frac{f^2 + fn - 2fn}{f-n} = \frac{f^2 - fn}{f-n} = f$$
    Maka $z_{\text{ndc}} = \frac{z_{\text{clip}}}{w_{\text{clip}}} = \frac{f}{f} = \mathbf{+1}$.

---

#### Q2.(d) Mengapa Clipping Near Plane Harus Terjadi di Clip Space Sebelum Pembagian $w$
Jika pemotongan (*clipping*) dilakukan setelah pembagian dengan $w$ (*NDC space*), sebuah titik dengan $z_e > 0$ (berada di belakang kamera) akan memiliki $w_{\text{clip}} < 0$.  
Saat membagi $x_{\text{clip}}$ dan $y_{\text{clip}}$ dengan $w$ negatif, koordinat mengalami pembalikan tanda (*sign inversion*), sehingga titik yang berada di belakang kamera akan terproyeksi secara salah ke dalam volume pandang di depan kamera (fenomena *phantom inversion / inside-out projection*).  
Selain itu, ketika sebuah segitiga memotong bidang $w = 0$ (tepat pada posisi mata kamera), pembagian dengan nol $x/0$ menghasilkan nilai tak hingga ($\pm \infty$) dan singularitas matematika yang merusak rasteriser.  
Oleh sebab itu, algoritma kliping (seperti Sutherland-Hodgman) wajib dieksekusi di *Clip Space* 4D terhadap bidang batas:
$$-w \le x, y, z \le w \quad \text{dengan syarat batas ketat } w \ge n > 0$$

---

### Q3. Depth, Texture, dan Sampling

#### Q3.(a) Algoritma Z-Buffer Empat Baris & Alasan Penggunaan NDC $z$
```text
1. Inisialisasi z_buffer[x, y] = 1.0 (nilai kedalaman terjauh pada far plane).
2. Untuk setiap fragmen (x, y) dari hasil rasterisasi poligon:
3.     Jika z_fragment < z_buffer[x, y]:
4.         z_buffer[x, y] = z_fragment;  framebuffer[x, y] = shade_fragment()
```
- **Alasan Menggunakan NDC $z$**:  
  Meskipun $z_{\text{ndc}}$ merupakan fungsi non-linier dari kedalaman ruang mata ($z_{\text{eye}}$), nilai $\frac{1}{z_{\text{eye}}}$ dan $z_{\text{ndc}}$ bervariasi secara **linier di ruang layar** (*screen space*). Hal ini memungkinkan interpolasi barisentrik fragmen dilakukan secara linier langsung pada bidang layar 2D tanpa perlu menghitung inversi per-piksel yang mahal.

---

#### Q3.(b) Analisis Presisi Depth (Near = 0.01 m, Far = 1000 m) dan Reverse-Z
- **Fraksi Kode Kedalaman pada Meter Pertama**:  
  Pemetaan kedalaman non-linier OpenGL standar dari jarak kamera $d$ ke rentang $[0, 1]$ adalah:
  $$\text{depth}_{01}(d) = \frac{f}{f - n} \left( 1 - \frac{n}{d} \right)$$
  Untuk $n = 0.01$, $f = 1000$:
  $$\text{depth}_{01}(1.0) = \frac{1000}{999.99} \left( 1 - \frac{0.01}{1.0} \right) \approx 1.00001 \times 0.99 \approx \mathbf{0.9900} \quad (\mathbf{99.0\%})$$
  Artinya, sebanyak **99.0%** dari seluruh rentang kode integer depth buffer (sekitar $16.6 \times 10^6$ dari $2^{24}$ kode pada buffer 24-bit) dihabiskan hanya untuk merepresentasikan jarak 1 meter pertama ($d \in [0.01, 1]$). Sisa rentang dari 1 meter hingga 1000 meter hanya memperoleh 1% kode kedalaman, memicu *z-fighting* parah pada objek-objek di kejauhan.
- **Apa yang Diubah oleh Reverse-Z**:  
  Reverse-Z membalik pemetaan kedalaman menjadi $n \mapsto 1.0$ dan $f \mapsto 0.0$, kemudian dipadukan dengan format floating-point (misalnya `float32` atau `float24`). Karena representasi floating-point IEEE-754 memiliki kepadatan mantissa yang sangat tinggi di dekat angka 0.0, non-linearitas proyeksi perspektif terkompensasi sempurna oleh distribusi presisi floating-point. Hasilnya, resolusi kedalaman menjadi hampir seragam di seluruh jarak pandang.

---

#### Q3.(c) Kesalahan Interpolasi Linier Layar Koordinat Tekstur & Koreksi Perspektif
- **Kesalahan Interpolasi Naif**:  
  Pemetaan dari ruang dunia 3D ke ruang layar 2D melibatkan pembagian dengan kedalaman $z$. Hubungan jarak di ruang layar tidak lagi berbanding lurus secara linier dengan jarak di permukaan poligon 3D. Menginterpolasi koordinat tekstur $(u, v)$ secara linier di ruang layar mengabaikan pemendekan perspektif, sehingga tekstur terlihat melengkung atau tertarik (*swimming / distortion artifacts*) saat kamera berotasi.
- **Koreksi Perspektif**:  
  Karena besaran $\frac{u}{w}$, $\frac{v}{w}$, dan $\frac{1}{w}$ bervariasi secara linier di ruang layar, pipeline menginterpolasi nilai-nilai tersebut menggunakan bobot barisentrik $(\alpha, \beta, \gamma)$:
  $$\left(\frac{u}{w}\right)_{\text{frag}} = \alpha \frac{u_0}{w_0} + \beta \frac{u_1}{w_1} + \gamma \frac{u_2}{w_2}, \quad \left(\frac{1}{w}\right)_{\text{frag}} = \alpha \frac{1}{w_0} + \beta \frac{1}{w_1} + \gamma \frac{1}{w_2}$$
  Koordinat tekstur sejati yang benar pada fragmen kemudian dipulihkan melalui pembagian tunggal:
  $$u_{\text{correct}} = \frac{(u/w)_{\text{frag}}}{(1/w)_{\text{frag}}}, \quad v_{\text{correct}} = \frac{(v/w)_{\text{frag}}}{(1/w)_{\text{frag}}}$$

---

#### Q3.(d) Mipmap dan Batas Nyquist
- **Definisi Mipmap**: Mipmap adalah urutan representasi citra tekstur yang di-*pre-filter* dan di-*downsample* secara bertingkat (masing-masing tingkat $D$ berukuran setengah dari tingkat $D-1$).
- **Penerapan Batas Nyquist**: Teorema Nyquist-Shannon menyatakan bahwa frekuensi sampling minimum harus minimal dua kali frekuensi tertinggi sinyal. Saat sebuah poligon berjarak jauh dari kamera, satu piksel layar memproyeksikan tapak (*pixel footprint*) yang mencakup banyak teksel tekstur asli. Tanpa mipmap, pengambilan satu sampel teksel (*undersampling*) melanggar batas Nyquist, memicu aliasing spasial dan fenomena kelap-kelip (*shimmering/crawling*) saat kamera bergerak. Mipmap menyaring frekuensi tinggi secara *pre-computation*, memastikan frekuensi tekstur tidak melampaui batas Nyquist untuk tingkat resolusi layar tertentu.

---

### Q4. Insiden Nyata Bertanggal &ndash; Presisi Depth dan Handedness

#### Q4.(a) Distribusi Presisi Non-Linier & Dua Perubahan Reverse-Z
- **Penyebab**: Fungsi kedalaman perspektif $\text{depth}(z) \propto \frac{1}{z}$. Turunan pertama $\frac{d(\text{depth})}{dz} \propto -\frac{1}{z^2}$, sehingga laju perubahan nilai depth terhadap perubahan jarak $z$ sangat curam di dekat $z_{\text{near}}$ dan mendatar mendekati nol saat $z$ mendekati $z_{\text{far}}$.
- **Dua Perubahan Reverse-Z**:
  1. Membalik pemetaan bidang batas: *near plane* dipetakan ke $1.0$ dan *far plane* dipetakan ke $0.0$.
  2. Menggunakan depth buffer bertipe floating-point (`depth24f` atau `depth32f`) dengan fungsi pembanding `GL_GREATER` bukan `GL_LESS`.
- **Alasan Menolong**: Pada format floating-point, jarak antar-angka yang dapat direpresentasikan (*spacing / ULP*) berbanding lurus dengan besar nilai ($2^{E}$). Di dekat $0.0$, floating-point memiliki jutaan nilai yang sangat rapat, persis di mana proyeksi perspektif membutuhkan presisi tinggi di kejauhan.

---

#### Q4.(b) Tabel 4 Konvensi Grafika: OpenGL vs Direct3D

| Konvensi | OpenGL | Direct3D |
|---|---|---|
| **Handedness Ruang Pandang** | *Right-handed* (Kamera menghadap $-z$, $+y$ atas, $+x$ kanan) | *Left-handed* (Kamera menghadap $+z$, $+y$ atas, $+x$ kanan) |
| **Urutan Mayor Matriks** | *Column-major* (vektor dikalikan dari kanan: $M \cdot p$) | *Row-major* (vektor dikalikan dari kiri: $p \cdot M$) |
| **Rentang NDC $z$** | $[-1.0, +1.0]$ (simetris) | $[0.0, +1.0]$ (setengah rentang) |
| **Origin Koordinat Tekstur UV** | Pojok kiri-bawah $(0, 0)$ ($v$ naik ke atas) | Pojok kiri-atas $(0, 0)$ ($v$ turun ke bawah) |

---

#### Q4.(c) Konten Uji Pengungkap Bug
- **Bug Presisi Depth**: Dua bidang quad koplanar tipis yang berjarak jauh dari kamera ($>100$ meter) dengan selisih jarak hanya beberapa milimeter. Pada jarak dekat keduanya tampak normal, namun di kejauhan depth buffer 16-bit atau 24-bit standar akan menghasilkan pola pita belang-belang (*z-fighting bands*).
- **Bug Handedness / Matriks**: Model asimetris dengan teks atau angka bertuliskan huruf (misal: "PRAMBANAN"). Jika konvensi handedness atau urutan perkalian matriks terbalik, teks akan terbaca terbalik (*mirrored*) dan permukaan poligon luar menjadi menghadap ke dalam (*inside-out*).

#### Q4.(d) Tanggal dan Sumber
1. **Nathan Reed**, *"Depth Precision Visualized"*, blog developer NVIDIA (terbit 5 Juli 2015).
2. **Brano Kemen**, *"Maximizing Depth Buffer Range and Precision"*, Outerra Tech Blog (terbit 14 Agustus 2012).

---

### Q5. Alur Data WebGL Draw Call

```text
[ Vertex Buffer Object (VBO) ] (Posisi, UV, Normal)
               │
               ▼
┌──────────────────────────────┐
│     Vertex Shader            │  <-- PROGRAMMABLE (Ditulis Pengembang)
│  (MVP Transform: p' = P*V*M*p)
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   Primitive Assembly         │  <-- FIXED FUNCTION
│   (Perakitan segitiga)       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   Clipping & Perspective /w  │  <-- FIXED FUNCTION
│   (Pemotongan & ruang NDC)   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   Rasteriser & Interpolation │  <-- FIXED FUNCTION
│   (Barisentrik terkoreksi /w)│
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│     Fragment Shader          │  <-- PROGRAMMABLE (Ditulis Pengembang)
│ (Sampling tekstur & lighting)│
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   Per-Sample Operations      │  <-- FIXED FUNCTION (Dapat Dikonfigurasi)
│ (Depth test, Stencil, Blend) │
└──────────────┬───────────────┘
               │
               ▼
      [ Framebuffer ] (Layar Tampilan)
```

---

## BAGIAN II: ANALISIS HASIL PASCA-LAB (A1 &ndash; A6)

### A1. Transformasi dan 6-Ruang Koordinat (Lab 1)

Verteks uji #0 pada model candi mandiri (`data/mymodel.obj`) memiliki koordinat lokal $\mathbf{p} = [-1.0, 0.0, -1.0, 1.0]^T$.

#### Telusuran Verteks #0 Melalui 6 Ruang Koordinat:
1. **Object Space**: $[-1.000000, 0.000000, -1.000000, 1.000000]^T$
2. **World Space ($\mathbf{M} \mathbf{p}$)**: $[-1.949820, 0.000000, -0.343806, 1.000000]^T$
   - Parameter Model: Skala $S(1.4)$, Rotasi $R_y(35^\circ)$, Translasi $T(0, 0, 0)$.
   - Periksa determinan submatriks $3 \times 3$: $\det(\mathbf{M}_{3 \times 3}) = 1.4^3 = 2.744000$ (positif, menjaga kaidah tangan kanan).
3. **View Space ($\mathbf{V} \mathbf{M} \mathbf{p}$)**: $[-1.340010, -0.246208, -6.071301, 1.000000]^T$
   - Parameter Kamera: Eye $(2.6, 2.0, 3.4)$, Target $(0, 0.7, 0)$, Up $(0, 1, 0)$.
   - Komponen $z_{\text{view}} = -6.071301 < 0$ menunjukkan titik berada di depan kamera pada jarak Euclidean $6.0713$ meter.
   - Orthonormalitas matriks orientasi terbukti: $\mathbf{R} \mathbf{R}^T = \mathbf{I}$, $\det(\mathbf{R}) = 1.000000$.
4. **Clip Space ($\mathbf{P} \mathbf{V} \mathbf{M} \mathbf{p}$)**: $[-3.235070, -0.594399, 4.851501, 6.071301]^T$
   - Komponen homogen $w_{\text{clip}} = -z_{\text{view}} = 6.071301$.
5. **NDC Space ($\mathbf{p}_{\text{clip}} / w$)**: $[-0.532846, -0.097903, 0.799088]^T$
   - Seluruh komponen berada di dalam interval kubus kanonik $[-1, 1]^3$.
6. **Screen Space (Resolusi $512 \times 512$)**:
   - $x_{\text{screen}} = 119.591$, $y_{\text{screen}} = 281.063$ (origin kiri atas, $y$ ke bawah).
   - Nilai depth terpetakan: $\text{depth}_{01} = 0.899544$.

---

### A2. Pipeline From-Scratch & Verifikasi Bit-Identik (Lab 2)

- **Verifikasi Numerik E1&ndash;E4 (`tests.py`)**:
  - E1: Titik $(2, 3, 4) \to (3, 3, -3)$; pembagian $d=2 \to (2, 2)$ valid.
  - E2: Dualitas kamera terverifikasi identik: kamera $+x \equiv$ model $-x$.
  - E3: Proyeksi perspektif: $z = -n \to z_{\text{ndc}} = -1.0$; $z = -f \to z_{\text{ndc}} = +1.0$; $z = -3 \to z_{\text{ndc}} = 0.5$.
  - E4: Koreksi perspektif: koordinat $u$ pada pusat layar bernilai $0.1$ (interpolasi linier naif salah memberikan $0.5$).
- **Perbandingan Software Rasterizer vs Ray Tracer**:
  - Pada resolusi $256 \times 256$ merender `data/mymodel.obj` (408 segitiga):
    - **PSNR**: $\mathbf{\infty\text{ dB}}$
    - **SSIM**: $\mathbf{1.0000}$
    - **Max Absolute Difference**: $\mathbf{0}$
  - Hasil membuktikan kesesuaian matematika absolut antara algoritma *forward rasterization* (z-buffer) dan *backward ray tracing* (Möller–Trumbore) ketika kedua renderer menggunakan konvensi pencahayaan dan geometri yang identik.

---

### A3. Diagnosis dan Perbaikan Tiga Kasus Bug Pipeline (Lab 2)

1. **Bug 1: Poligon Terbalik (*Inside-Out Winding*)**:
   - *Diagnosis Pra-Perbaikan*: Winding verteks pada file `.obj` tidak konsisten (CW alih-alih CCW), menyebabkan vektor normal permukaan mengarah ke dalam candi. Akibatnya, pencahayaan Lambertian menghasilkan permukaan depan yang gelap dan bayangan terbalik.
   - *Bukti Kuantitatif*: Nilai SSIM sebelum perbaikan adalah **0.7053**.
   - *Tindakan Perbaikan*: Menyusun ulang urutan indeks verteks segitiga menjadi konsisten CCW (atau membalik arah normal saat dot product negatif).
   - *Bukti Pasca-Perbaikan*: Citra pulih sempurna dengan SSIM mencapai **1.0000**.

2. **Bug 2: Perebutan Kedalaman (*Z-Fighting*)**:
   - *Diagnosis Pra-Perbaikan*: Dua quad koplanar bertumpuk dengan selisih jarak hanya $10^{-4}$, dievaluasi dengan depth buffer integer 16-bit dengan $z_{\text{near}} = 10^{-3}$. Non-linearitas tajam menghabiskan seluruh presisi di dekat kamera, sehingga pada jarak $>3$ meter nilai depth keduanya terkuantisasi ke integer yang sama.
   - *Bukti Kuantitatif*: Terdapat **2852 piksel salah** (*wrong pixels*) pada pita perebutan dengan SSIM **0.7787**.
   - *Tindakan Perbaikan*: Menaikkan batas $z_{\text{near}}$ dari $0.001$ ke $0.1$ serta memperbesar presisi depth buffer menjadi 24-bit.
   - *Bukti Pasca-Perbaikan*: Jumlah piksel salah terpangkas menjadi di bawah 180 piksel, menghilangkan pola pita belang.

3. **Bug 3: Peregangan Tekstur Naif (*Stretched Non-Perspective Texture*)**:
   - *Diagnosis Pra-Perbaikan*: Koordinat tekstur $(u, v)$ diinterpolasi secara linier di ruang layar tanpa membagi dengan koordinat homogen $w$.
   - *Bukti Kuantitatif*: SSIM render terdistorsi hanya **0.4758** dengan pola melengkung diagonal parah pada permukaan miring.
   - *Tindakan Perbaikan*: Menerapkan interpolasi barisentrik pada besaran $u/w, v/w, 1/w$ dan memulihkannya via pembagian per-fragmen.
   - *Bukti Pasca-Perbaikan*: Tekstur relief batu terproyeksi lurus dan rigid dengan SSIM **1.0000**.

---

### A4. Keputusan Rasterisation vs Ray Tracing (Lab 3)

#### Data Prediksi vs Pengukuran Empiris (Model 408 Segitiga, 10 Repetisi):
- **Prediksi Pra-Ukur**:
  - Rasio Waktu Render ($t_{\text{RT}} / t_{\text{Raster}}$): **6.8&times;**
  - Kualitas Bayangan Tajam (*Hard Shadows*): Lebih unggul **Ray Tracing**
  - Kualitas Refleksi Permukaan: Lebih unggul **Ray Tracing**
- **Hasil Terukur Empiris**:
  - Frame time pada resolusi $192 \times 192$:
    - Rasterizer CPU: **190.0 ms**
    - Ray Tracer CPU: **1803.9 ms**
    - **Rasio Terukur**: $\mathbf{9.49\times}$ (Faktor deviasi: $1.40\times$, *under-estimated*)
  - Uji *Hard Shadows*: **4.6%** piksel (687 dari 14.821 piksel yang mengenai objek) berada dalam bayangan diri (*self-shadow*).

#### Rekonsiliasi Deviasi:
Prediksi awal 6.8&times; meremehkan efisiensi rasteriser. Pada resolusi $192 \times 192$, ray tracer CPU melakukan pengujian Möller–Trumbore sebanyak $192 \times 192 \times 408 \approx 1.50 \times 10^7$ kali operasi per frame tanpa bantuan BVH. Sebaliknya, software rasterizer hanya memproses segitiga yang lolos frustum layar dan memangkas 62.7% segitiga tampak belakang via *back-face culling*, menyisakan hanya 152 segitiga yang masuk ke tahap penulisan kedalaman. Akibatnya, rasteriser jauh lebih hemat komputasi saat jumlah segitiga bertambah.

#### Keputusan Penggunaan Paradigma:
1. **Interactive Real-Time Viewer**: Dipilih **Rasterisasi Perangkat Keras (WebGL / GPU)** karena arsitektur GPU mampu mengeksekusi rasterisasi dan z-buffering secara masif paralel (mencapai $>60$ FPS pada Three.js).
2. **High-Fidelity Beauty Shot**: Dipilih **Ray Tracing** karena kemampuan alaminya mengevaluasi bayangan tajam (*shadow rays*), oklusi ambien, serta pantulan sekunder tanpa artefak diskritisasi *shadow map*.

#### Pernyataan Keterbatasan Sistem:
1. *Batas Geometri*: Ketiadaan struktur BVH membuat CPU ray tracer tidak dapat digunakan secara interaktif pada model berkepadatan $>2000$ segitiga.
2. *Pencahayaan Raster*: Software rasterizer `raster3d.py` tidak memiliki modul *shadow map*, sehingga tidak mampu menghasilkan bayangan diri pada candi.
3. *Single-threaded CPU*: Kedua software renderer berjalan pada satu inti CPU dalam interpreter Python, sehingga tidak mencerminkan batas performa GPU modern.

---

### A5. Tekstur, Mipmapping, dan Culling (Lab 2)

- **Koreksi Perspektif**:
  - Koordinat $u$ pada tengah bidang miring: nilai terkoreksi perspektif adalah **0.100**, sementara interpolasi linier naif memberikan nilai salah **0.500**.
- **Efektivitas Mipmapping**:
  - Energi 4 tingkat piramida tekstur terjaga konstan pada nilai **0.21684**.
  - PSNR tekstur berjarak jauh meningkat dari **30.44 dB** menjadi **32.57 dB**.
  - Metrik kelap-kelip (*shimmer* rata-rata pergerakan kamera kecil) terpangkas lebih dari setengah: dari **1.576** menjadi **0.692**.
- **Efisiensi Back-Face Culling**:
  - Total segitiga candi: **408 segitiga**.
  - Segitiga terpotong (*culled* dengan aturan $\text{area} > 0$): **256 segitiga (62.7%)**.
  - Segitiga aktif di-rasterisasi: **152 segitiga**.
  - Pengurangan penulisan fragmen lolos z-buffer: dari **74.037** menjadi **64.024** (**berkurang 13.5%**).
  - Citra hasil akhir bit-identik: **SSIM 1.0000, max |diff| 0**.

---

### A6. Reproduksibilitas dan Rekap Viva

- **Transkrip Lingkungan Bersih (`repro_clean.py`)**:
  - Pengujian isolasi venv pada direktori sementara `m3_clean_*` berjalan sukses:
    1. `pip install -r requirements.txt` sukses memasang NumPy 2.5.4 dan Pillow 13.0.0.
    2. `python make_model.py` sukses menghasilkan `pusaka_model.obj` (180 segitiga) dan `relief.ppm`.
    3. `python tests.py` mencetak **ALL CHECKS PASSED (8 OK)** dalam 0.6 detik.
  - Transkrip resmi tersimpan di [`out/repro_transcript.txt`](out/repro_transcript.txt).
- **Hasil Perbandingan WebGL (`webcompare`)**:
  - PSNR WebGL Three.js vs software rasterizer: **30.03 dB**, SSIM **0.9887**.
  - Residual error terkonsentrasi 100% pada batas siluet luar akibat *hardware multi-sample anti-aliasing* (MSAA) pada peramban Brave (Chromium), membuktikan bahwa transformasi matriks dan proyeksi internal telah bit-akurat.
