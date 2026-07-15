# Product Requirements Document

## Sistem Prioritas Pemeriksaan Realisasi Tender Pemerintah Provinsi DKI Jakarta

| Metadata | Nilai |
|---|---|
| Judul skripsi | Rancang Bangun Sistem Prioritas Pemeriksaan Realisasi Tender Pemerintah Provinsi DKI Jakarta Menggunakan Isolation Forest Berbasis Web |
| Versi PRD | 1.0-draft |
| Tanggal pembaruan | 12 Juli 2026 |
| Status produk | Perencanaan dan persiapan data |
| Metode penelitian | CRISP-DM untuk analisis Machine Learning; RAD untuk pengembangan website |
| Pemilik produk | Julius |
| Root project | `C:\Data Central\Documents\Code\julius\Skripsi\procurement_data` |

> Dokumen ini menjelaskan **apa** yang dibangun dan **mengapa** produk dibutuhkan. Keputusan implementasi teknis rinci mengikuti `CLAUDE.md`. PRD bersifat living document dan harus diperbarui ketika keputusan produk atau bukti data berubah.

## Prinsip Produk

1. Sistem menghasilkan **prioritas pemeriksaan**, bukan vonis fraud, korupsi, kolusi, atau pelanggaran hukum.
2. Skor tinggi berarti record lebih tidak lazim dibanding pola data pembanding, bukan bukti kecurangan.
3. Setiap skor harus dapat ditelusuri ke data sumber, fitur, versi model, dan alasan yang dapat dibaca pengguna.
4. Data mentah tidak boleh ditimpa. Seluruh transformasi harus reproducible dan menghasilkan artefak baru.
5. Cakupan v1.0 dibatasi pada DKI Jakarta agar baseline model lebih homogen dan sesuai kebutuhan pemeriksaan wilayah.
6. Top-N adalah mekanisme pengurutan beban pemeriksaan, bukan threshold label anomali absolut.

---

# SECTION 1 — Problem Statement

## 1.1 Masalah

Data realisasi tender pemerintah tersedia dalam bentuk tabel publik, tetapi jumlah record, variasi nilai paket, banyaknya satuan kerja, dan pola kemenangan penyedia membuat pemeriksaan manual sulit diprioritaskan secara konsisten. Auditor harus menentukan paket mana yang perlu dibaca lebih dahulu tanpa label fraud yang dapat dijadikan target supervised learning.

Spreadsheet dapat menyimpan dan memfilter data, tetapi tidak otomatis:

- membentuk baseline ketidaklaziman multivariat;
- menggabungkan data paket dengan HPS, pagu, dan jadwal tender;
- menghitung fitur konsentrasi penyedia pada konteks satuan kerja dan tahun;
- mengurutkan paket berdasarkan skor ketidaklaziman yang reproducible;
- menjelaskan faktor yang paling memengaruhi posisi prioritas setiap paket;
- menyajikan hasil yang mudah digunakan oleh pengguna non-teknis melalui web.

## 1.2 Bukti Data Awal

Audit file project pada 12 Juli 2026 menghasilkan kondisi berikut.

| Item | Hasil audit |
|---|---:|
| File sumber DKI Jakarta | 3 file, tahun 2024, 2025, dan 2026 |
| Baris sumber sebelum pembersihan penyedia kosong | 1.284 |
| Baris dataset gabungan | 1.279 |
| Kolom awal | 14 |
| Kode paket unik | 1.277 |
| Penyedia unik pada dataset gabungan | 684 |
| Satuan kerja unik pada dataset gabungan | 132 |
| Distribusi tahun | 2024: 312; 2025: 529; 2026: 438 |
| Status paket | 100% `SELESAI` |
| Sumber transaksi | 100% `Tender` |
| Kode paket berulang | `10060212000` muncul tiga kali dengan penyedia berbeda |
| Data penyedia kosong | 5 baris pada file mentah 2026, tidak masuk dataset gabungan |

Dataset utama saat ini berada di:

```text
datasets/raw/realisasi_dki_jakarta_2024_2026.csv
```

Tahun 2026 merupakan snapshot tahun berjalan pada waktu pengunduhan, bukan satu tahun kalender penuh. Statistik tahunan 2026 tidak boleh dibandingkan langsung dengan total tahunan 2024 atau 2025 tanpa penanda dan normalisasi yang sesuai.

## 1.3 Kesenjangan Produk

Artefak enrichment, coverage report, dataset canonical satu-record-per-paket, EDA reproducible, feature matrix leakage-safe, dan split temporal sudah tersedia. Feature matrix berisi 1.276 record eligible dengan 20 fitur eksplisit dan schema versi di `artifacts/feature_schema.json`. Split temporal memakai 838 record 2024-2025 untuk training dan 438 record snapshot 2026 untuk evaluation, dengan satu record canonical tidak eligible tetap tercatat sebagai excluded. Baseline, model Isolation Forest, evaluasi model, backend API, frontend, laporan yang dapat diunduh, pengujian lanjutan, dan deployment belum tersedia.

## 1.4 Solusi yang Diusulkan

Membangun aplikasi web yang:

1. mengaudit dan memperkaya data tender selesai DKI Jakarta;
2. membentuk fitur finansial, temporal, dan konsentrasi penyedia;
3. melatih Isolation Forest secara reproducible;
4. mengurutkan paket berdasarkan anomaly score;
5. menampilkan Top-N paket untuk prioritas pemeriksaan;
6. menjelaskan faktor dominan setiap skor;
7. menyediakan filter, drill-down, dan ekspor laporan;
8. menampilkan disclaimer metodologis bahwa hasil bukan tuduhan fraud.

---

# SECTION 2 — Goals

## 2.1 Tujuan Produk dan Metrik Kesuksesan

| ID | Tujuan | Metrik kesuksesan |
|---|---|---|
| G-1 | Menyatukan data tender lintas tahun secara dapat ditelusuri | 100% record hasil transformasi memiliki `kode_paket`, tahun, provenance file sumber, dan status validasi |
| G-2 | Memperkaya paket dengan data detail INAPROC | Pipeline menghasilkan laporan coverage HPS, pagu, metadata tender, dan jadwal; tidak ada nilai enrichment yang diimputasi tanpa penanda |
| G-3 | Menghasilkan ranking prioritas yang reproducible | Konfigurasi, seed, fitur, dan versi dataset yang sama menghasilkan urutan dan skor yang sama dalam toleransi numerik |
| G-4 | Menyediakan penjelasan ranking | Setiap record Top-N menampilkan minimal tiga faktor yang paling memengaruhi ketidaklaziman atau deviasi fitur yang dapat diverifikasi |
| G-5 | Memudahkan eksplorasi hasil | Pengguna dapat memfilter tahun, satuan kerja, metode, jenis pengadaan, penyedia, dan rentang skor/nilai tanpa mengubah dataset sumber |
| G-6 | Mendukung pemeriksaan lanjutan | Pengguna dapat mengunduh daftar prioritas terfilter dalam CSV; laporan ringkas PDF menjadi P2 setelah data dan desain final stabil |
| G-7 | Menjaga batas interpretasi | Seluruh halaman ranking dan laporan memuat disclaimer bahwa skor bukan bukti fraud atau pelanggaran hukum |
| G-8 | Menghasilkan aplikasi skripsi yang dapat didemonstrasikan | Build frontend, backend, model, integrasi, dan pengujian utama lulus; frontend dan backend dapat diakses dari deployment yang ditetapkan |

## 2.2 Non-Goals

- Membuktikan fraud, korupsi, bid-rigging, suap, atau pelanggaran hukum.
- Menggantikan audit profesional atau keputusan aparat pengawasan.
- Menentukan kerugian negara.
- Memprediksi pemenang tender.
- Mendeteksi kolusi peserta karena data seluruh peserta dan penawaran kalah tidak tersedia.
- Memberikan skor real-time pada tender yang masih berlangsung.
- Membangun platform pengadaan baru.

---

# SECTION 3 — Target Users / Personas

| Persona | Profil | Kebutuhan | Masalah saat ini |
|---|---|---|---|
| Auditor/Inspektorat | Pengguna utama yang menyeleksi paket untuk pemeriksaan awal | Ranking yang dapat difilter, alasan prioritas, detail nilai dan jadwal, ekspor daftar kerja | Volume data tinggi; pemeriksaan spreadsheet memerlukan banyak langkah manual |
| Analis pengadaan | Pengguna yang memahami konteks satuan kerja, metode, dan penyedia | Statistik distribusi, konsentrasi penyedia, tren, dan drill-down paket | Data tersebar antara CSV dan detail portal |
| Dosen/penguji | Pengguna evaluasi akademik | Alur data yang dapat ditelusuri, metode yang tepat, evaluasi tanpa klaim berlebihan | Sulit menilai validitas jika skor tidak dijelaskan atau pipeline tidak reproducible |
| Peneliti/mahasiswa | Pengguna sekunder | Dokumentasi dataset, fitur, konfigurasi eksperimen, dan hasil evaluasi | Eksperimen sering tidak memiliki provenance dan batas interpretasi yang jelas |

## 3.1 Konteks Penggunaan

- Desktop/laptop menjadi target utama karena tabel prioritas memuat banyak kolom.
- Mobile harus tetap dapat membuka ringkasan dan detail, tetapi bukan target utama analisis tabel lebar.
- Pengguna v1.0 hanya membaca dan mengekspor hasil. Tidak ada akun, role, atau modifikasi data melalui UI.

---

# SECTION 4 — User Stories

Prioritas: **P1** wajib untuk v1.0, **P2** penting setelah P1 stabil, **P3** nice-to-have.

| ID | Pri | User story |
|---|---|---|
| US-1 | P1 | Sebagai auditor, saya ingin melihat paket diurutkan berdasarkan skor prioritas agar dapat menentukan pemeriksaan awal secara efisien. |
| US-2 | P1 | Sebagai auditor, saya ingin memilih Top-N agar jumlah paket dapat disesuaikan dengan kapasitas pemeriksaan. |
| US-3 | P1 | Sebagai auditor, saya ingin memfilter hasil berdasarkan tahun, satuan kerja, metode, jenis pengadaan, dan penyedia agar analisis sesuai ruang lingkup tugas. |
| US-4 | P1 | Sebagai auditor, saya ingin membuka detail paket agar dapat melihat nilai kontrak, HPS, pagu, jadwal, penyedia, dan fitur yang memengaruhi skor. |
| US-5 | P1 | Sebagai auditor, saya ingin melihat alasan skor dalam bahasa yang netral agar ranking tidak disalahartikan sebagai tuduhan fraud. |
| US-6 | P1 | Sebagai analis, saya ingin melihat statistik distribusi dan konsentrasi penyedia agar pola data dapat dipahami sebelum membaca ranking. |
| US-7 | P1 | Sebagai pengguna, saya ingin mengunduh hasil terfilter dalam CSV agar dapat melakukan pemeriksaan lanjutan. |
| US-8 | P1 | Sebagai dosen/penguji, saya ingin melihat sumber data, transformasi, fitur, versi model, dan batasan agar hasil dapat diaudit secara akademik. |
| US-9 | P1 | Sebagai peneliti, saya ingin menjalankan ulang pipeline dengan konfigurasi yang sama agar hasil penelitian reproducible. |
| US-10 | P2 | Sebagai auditor, saya ingin mengunduh laporan ringkas PDF agar hasil dapat dibagikan tanpa membuka aplikasi. |
| US-11 | P2 | Sebagai analis, saya ingin membandingkan distribusi antar tahun secara ternormalisasi agar snapshot parsial 2026 tidak menyesatkan. |
| US-12 | P2 | Sebagai dosen/penguji, saya ingin melihat analisis sensitivitas parameter agar pemilihan konfigurasi Isolation Forest dapat dipertanggungjawabkan. |
| US-13 | P3 | Sebagai pengguna, saya ingin menyimpan kombinasi filter sebagai tautan agar tampilan dapat dibagikan. |

---

# SECTION 5 — Functional Requirements

## 5.1 Data Acquisition, Audit, and Provenance

| ID | Pri | Kebutuhan yang dapat diuji | Kriteria penerimaan |
|---|---|---|---|
| FR-1 | P1 | Sistem pipeline membaca file raw 2024-2026 tanpa mengubahnya | Hash dan jumlah baris sumber dicatat; file raw tidak ditimpa |
| FR-2 | P1 | Pipeline memvalidasi skema 14 kolom awal, tipe, nilai kosong, status, tahun, sumber transaksi, dan duplikasi | Eksekusi gagal dengan pesan jelas jika skema wajib berubah atau kolom wajib hilang |
| FR-3 | P1 | Setiap record processed menyimpan provenance | Minimal tersedia nama file sumber, tahun sumber, dan waktu proses |
| FR-4 | P1 | Baris tanpa penyedia dan kode paket berulang ditangani secara eksplisit | Laporan kualitas data menunjukkan jumlah dikeluarkan, dipertahankan, atau diagregasi beserta alasan |
| FR-5 | P1 | Dataset model memiliki unit analisis paket yang jelas | Satu `kode_paket` tidak menghasilkan skor ganda kecuali desain multi-record dibuktikan dan didokumentasikan |

## 5.2 Data Enrichment

| ID | Pri | Kebutuhan yang dapat diuji | Kriteria penerimaan |
|---|---|---|---|
| FR-6 | P1 | Pipeline mengambil detail paket INAPROC berdasarkan `kode_paket` | HPS, pagu, metode evaluasi, metadata tender, dan jadwal disimpan jika tersedia |
| FR-7 | P1 | Enrichment mendukung cache, retry terbatas, checkpoint, dan resume | Proses yang terputus dapat dilanjutkan tanpa mengulang request sukses |
| FR-8 | P1 | Pipeline menghasilkan coverage report | Jumlah sukses, gagal, HTTP error, data kosong, dan persentase coverage per field tersedia |
| FR-9 | P1 | Missing enrichment tidak disamarkan | Nilai kosong tetap null dan memiliki flag ketersediaan; imputasi hanya boleh digunakan jika dibuktikan serta dicatat |
| FR-10 | P1 | Respons API mentah atau snapshot terstruktur dapat diaudit | Paket dapat ditelusuri kembali ke respons detail yang digunakan pada saat enrichment |

> Full enrichment terhadap 1.277 kode paket unik menghasilkan 1.277 respons sukses. Coverage HPS, pagu, metode evaluasi, metadata tender, dan jadwal tercatat 100% pada `reports/data/enrichment_coverage.md`; angka ini menjadi dasar task canonicalization berikutnya.

## 5.3 Feature Engineering

| ID | Pri | Kebutuhan yang dapat diuji | Kriteria penerimaan |
|---|---|---|---|
| FR-11 | P1 | Pipeline membentuk fitur finansial | Minimal: log nilai kontrak, rasio kontrak terhadap HPS, rasio HPS terhadap pagu, penghematan terhadap HPS, dan rasio PDN; pembagian nol/null aman |
| FR-12 | P1 | Pipeline membentuk fitur temporal | Minimal: durasi tender total dan durasi tahapan yang tersedia; timestamp invalid dilaporkan |
| FR-13 | P1 | Pipeline membentuk fitur konsentrasi | Minimal: frekuensi kemenangan penyedia, pangsa nilai penyedia, dan HHI pada konteks satuan kerja-tahun yang didefinisikan |
| FR-14 | P1 | Fitur tahun berjalan tidak menyesatkan | Fitur frekuensi/konsentrasi 2026 dihitung pada konteks periode observasi dan diberi penanda snapshot parsial |
| FR-15 | P1 | Transformasi kategori ditentukan dari data training | Kategori baru saat scoring ditangani tanpa crash atau perubahan diam-diam pada urutan fitur |
| FR-16 | P1 | Data leakage dicegah pada fitur agregat | Fitur paket tidak boleh menggunakan informasi masa depan yang tidak tersedia pada skenario evaluasi temporal |

> Pipeline `pipelines/build_model_features.py` menghasilkan `datasets/processed/model_features.csv` dan `artifacts/feature_schema.json`. Fitur agregat penyedia/satuan kerja memakai record sebelumnya dalam tahun yang sama setelah sorting jadwal dan `package_id`. Split temporal final dicatat pada `datasets/manifests/model_split.json`, `artifacts/model_experiment_config.json`, dan `reports/model/split_decision.md`: training 2024-2025, evaluation snapshot 2026, tanpa menganggap 2026 sebagai tahun penuh.

## 5.4 Modeling and Evaluation

| ID | Pri | Kebutuhan yang dapat diuji | Kriteria penerimaan |
|---|---|---|---|
| FR-17 | P1 | Isolation Forest dilatih dengan konfigurasi tersimpan | Seed, daftar fitur, preprocessing, hyperparameter, versi dataset, dan versi library tersimpan bersama artefak |
| FR-18 | P1 | Sistem menghasilkan skor kontinu dan ranking | Seluruh record layak-scoring memiliki skor; arah skor konsisten: semakin tinggi berarti semakin diprioritaskan |
| FR-19 | P1 | Top-N bersifat configurable | Pengguna dapat memilih N; Top-N tidak diubah menjadi label fraud |
| FR-20 | P1 | Evaluasi sesuai model tanpa label | Minimal mencakup stabilitas antar-seed, sensitivitas hyperparameter/Top-N, inspeksi distribusi skor, dan validasi contoh kasus terhadap fitur sumber |
| FR-21 | P1 | Evaluasi temporal dilakukan tanpa menyatakan 2026 sebagai tahun penuh | Eksperimen membandingkan penggunaan data historis 2024-2025 dengan snapshot 2026 dan menjelaskan keterbatasannya |
| FR-22 | P1 | Pengaruh fitur dianalisis | Permutation sensitivity menjadi baseline; SHAP digunakan jika hasilnya tervalidasi terhadap output Isolation Forest |
| FR-23 | P1 | Setiap ranking dapat dijelaskan | Detail Top-N menampilkan kontribusi/penyimpangan fitur, nilai asli, dan konteks pembanding |
| FR-24 | P2 | Konfigurasi final dibandingkan dengan baseline sederhana | Ranking Isolation Forest dibandingkan dengan minimal satu baseline transparan, misalnya robust z-score multivariat/fitur utama |

## 5.5 Web Dashboard

| ID | Pri | Kebutuhan yang dapat diuji | Kriteria penerimaan |
|---|---|---|---|
| FR-25 | P1 | Landing page menjelaskan tujuan, sumber data, dan disclaimer | Pengguna memahami bahwa sistem memprioritaskan pemeriksaan, bukan menuduh kecurangan |
| FR-26 | P1 | Dashboard menampilkan statistik utama | Minimal jumlah paket, nilai total, penyedia, satuan kerja, distribusi tahun, dan ringkasan skor |
| FR-27 | P1 | Dashboard menampilkan visualisasi relevan | Chart tidak menduplikasi tabel; label, satuan, sumber, dan periode observasi jelas |
| FR-28 | P1 | Tabel ranking diurutkan dari prioritas tertinggi | Pagination, sorting, filter, state kosong, loading, dan error tersedia |
| FR-29 | P1 | Detail paket tersedia | Menampilkan identitas paket, nilai, HPS/pagu, penyedia, satker, jadwal, fitur model, alasan ranking, dan tautan sumber bila tersedia |
| FR-30 | P1 | Filter dapat digabungkan | Tahun, satker, metode, jenis, penyedia, skor, dan nilai dapat diterapkan bersama dan dapat di-reset |
| FR-31 | P1 | Pengguna dapat mengunduh CSV sesuai filter | Jumlah dan urutan record ekspor sama dengan tampilan/filter aktif |
| FR-32 | P2 | Pengguna dapat mengunduh PDF ringkas | PDF memuat periode, filter, waktu pembuatan, disclaimer, ringkasan, dan daftar Top-N |
| FR-33 | P1 | Halaman metodologi/data tersedia | Menjelaskan provenance, coverage enrichment, fitur, model, evaluasi, keterbatasan, dan versi artefak |

## 5.6 API and Error Handling

| ID | Pri | Kebutuhan yang dapat diuji | Kriteria penerimaan |
|---|---|---|---|
| FR-34 | P1 | Backend menyediakan data ringkasan, ranking, filter options, detail, dan export | Kontrak respons tervalidasi; parameter invalid menghasilkan 4xx, bukan 500 |
| FR-35 | P1 | Respons mencantumkan metadata versi | Dataset version, model version, waktu pemrosesan, dan filter aktif tersedia |
| FR-36 | P1 | Missing data ditampilkan jujur | UI/API menampilkan `tidak tersedia`, bukan nol palsu |
| FR-37 | P1 | Kegagalan backend ditangani | Pengguna menerima pesan ringkas dan retry yang aman; detail internal tidak diekspos |
| FR-38 | P1 | Disclaimer ikut pada ranking dan export | Tidak ada daftar prioritas yang dapat dipisahkan dari konteks interpretasinya tanpa disclaimer |

---

# SECTION 6 — Non-Functional Requirements

| ID | Pri | Kebutuhan | Target/verifikasi |
|---|---|---|---|
| NFR-1 | P1 | Performa API | Respons ringkasan/ranking p95 <1 detik setelah warm-up pada dataset v1.0 di VPS target |
| NFR-2 | P1 | Performa frontend | LCP <2,5 detik pada koneksi normal; interaksi filter terasa responsif dan tidak memblokir UI |
| NFR-3 | P1 | Reproducibility | Pipeline dapat dijalankan dari environment bersih menggunakan lockfile dan satu konfigurasi eksperimen |
| NFR-4 | P1 | Integritas data | Raw data immutable; artefak processed/model memiliki checksum atau manifest versi |
| NFR-5 | P1 | Reliability | Error enrichment per paket tidak menggagalkan seluruh batch; proses dapat resume |
| NFR-6 | P1 | Security | HTTPS pada akses publik, CORS allowlist, input tervalidasi, tidak ada secret di repository/client |
| NFR-7 | P1 | Privacy | Hanya data pengadaan publik yang diproses; tidak menambah data pribadi nonpublik |
| NFR-8 | P1 | Interpretability | Skor Top-N selalu disertai fitur penjelas dan disclaimer |
| NFR-9 | P1 | Accessibility | Navigasi keyboard, semantic HTML, kontras memadai, label chart/tabel, target WCAG 2.1 AA untuk jalur utama |
| NFR-10 | P1 | Responsive design | Jalur utama berfungsi pada desktop dan mobile; tabel lebar memakai pola responsif yang tidak menyembunyikan data |
| NFR-11 | P1 | Maintainability | Struktur sederhana, typed boundaries, fungsi transformasi dapat diuji, tidak ada microservice yang tidak diperlukan |
| NFR-12 | P1 | Observability | Backend mencatat request error dan versi artefak tanpa menyimpan secret atau payload sensitif |
| NFR-13 | P1 | Portability | Backend dan pipeline dapat dijalankan melalui Docker pada VPS; frontend dapat dibangun di Vercel |
| NFR-14 | P2 | Availability | Target demo 99% di luar maintenance, tanpa klaim SLA produksi pemerintah |
| NFR-15 | P1 | Browser compatibility | Dua versi terbaru Chrome, Edge, dan Firefox |

---

# SECTION 7 — Scope (In/Out)

## 7.1 In Scope v1.0

- Data realisasi tender selesai Pemerintah Provinsi DKI Jakarta 2024-2026.
- Tahun 2026 diperlakukan sebagai snapshot parsial sesuai tanggal ekstraksi.
- Audit schema, missing values, duplikasi, provenance, dan coverage enrichment.
- Enrichment detail INAPROC untuk HPS, pagu, metode evaluasi, metadata, dan jadwal yang tersedia.
- Dataset canonical pada unit analisis paket.
- Feature engineering finansial, temporal, dan konsentrasi penyedia.
- Isolation Forest, ranking kontinu, Top-N configurable, dan evaluasi tanpa label.
- Analisis pengaruh fitur menggunakan permutation sensitivity dan SHAP bila tervalidasi.
- Dashboard statistik, ranking, filter, detail paket, halaman metodologi/data.
- Download laporan CSV.
- PDF report sebagai P2 setelah output final stabil.
- Next.js di Vercel, FastAPI dalam Docker pada VPS/server, dipublikasikan melalui Cloudflare Tunnel.
- Unit test, integration test, black-box test, dan verifikasi deployment utama.

## 7.2 Out of Scope v1.0

- Tuduhan atau klasifikasi fraud/korupsi terbukti.
- Deteksi bid-rigging atau kolusi peserta.
- Data seluruh Indonesia atau pelatihan lintas provinsi.
- Tender berstatus berlangsung.
- Data peserta kalah, nilai penawaran pesaing, bukti suap, atau dokumen investigasi nonpublik.
- Login, role-based access control, komentar auditor, workflow kasus, atau kolaborasi multi-user.
- Upload data bebas oleh pengguna.
- Real-time streaming dan retraining otomatis.
- Mobile app native.
- Database operasional jika artefak read-only sudah memenuhi kebutuhan.
- Arsitektur microservices lebih dari kebutuhan frontend + satu backend API.
- Integrasi langsung ke sistem internal pemerintah.

## 7.3 Future Scope

- Validasi ranking oleh ahli/auditor melalui protokol penelitian terpisah.
- Data lintas provinsi dengan model per wilayah atau hierarchical baseline.
- Audit workflow, catatan tindak lanjut, dan akses berbasis role.
- Scheduled data refresh dan model monitoring.
- Perbandingan algoritma anomaly detection tambahan jika dibutuhkan penelitian lanjutan.

---

# 8. Information Architecture

| Halaman | Tujuan | Prioritas |
|---|---|---|
| Landing | Menjelaskan masalah, fungsi sistem, cakupan, dan disclaimer | P1 |
| Dashboard | Menampilkan statistik, chart utama, filter, dan tabel ranking | P1 |
| Detail Paket | Menampilkan data sumber, enrichment, fitur, skor, dan alasan | P1 |
| Dataset | Menampilkan provenance, kualitas, distribusi, dan coverage enrichment | P1 |
| Metodologi | Menjelaskan CRISP-DM, Isolation Forest, evaluasi, interpretasi, dan keterbatasan | P1 |
| Laporan | Mengatur Top-N/filter dan mengunduh CSV/PDF | P1 CSV; P2 PDF |

# 9. Data and Modeling Decisions

## 9.1 Unit Analisis

Unit target adalah satu paket tender (`kode_paket`). Kasus `10060212000` yang memiliki tiga penyedia tidak boleh diam-diam menjadi tiga skor paket. Pipeline canonical mempertahankan satu record untuk paket tersebut, menyimpan daftar penyedia dan nilai sumber, serta menandainya `eligible_for_model=false` sampai feature engineering menetapkan aturan eksplisit untuk paket multi-provider.

## 9.2 Interpretasi Fitur HPS

`total_nilai / nilai_hps` mengukur kedekatan nilai realisasi terhadap HPS. Nilai mendekati 1 berarti diskon terhadap HPS kecil, bukan otomatis mark-up atau fraud. Nilai di atas 1, null, atau ekstrem harus diverifikasi terhadap definisi field dan data sumber sebelum ditafsirkan.

## 9.3 Protokol Tahun

- 2024 dan 2025 adalah kandidat baseline historis penuh.
- 2026 adalah snapshot tahun berjalan pada 12 Juli 2026.
- Evaluasi temporal harus mencegah informasi masa depan masuk ke fitur record masa lalu.
- Model final untuk demo dipilih setelah eksperimen, bukan ditetapkan hanya dari jumlah baris.

## 9.4 Evaluasi Tanpa Ground Truth

Accuracy, precision, recall, F1-score, dan confusion matrix tidak dapat menjadi metrik utama karena tidak tersedia label fraud/anomali tervalidasi. Evaluasi utama menggunakan:

1. stabilitas ranking antar random seed;
2. overlap Top-N antar konfigurasi;
3. sensitivitas terhadap `contamination`, jumlah estimator, dan subsampling;
4. inspeksi distribusi skor;
5. sanity check nilai fitur pada record prioritas;
6. evaluasi temporal 2024-2025 terhadap snapshot 2026;
7. perbandingan dengan baseline transparan;
8. validasi ahli hanya jika responden dan protokol benar-benar tersedia.

# 10. Release Acceptance Criteria

v1.0 dinyatakan siap untuk penulisan BAB 4 apabila:

- [ ] Audit dan enrichment selesai dengan coverage report.
- [ ] Dataset canonical dan feature matrix memiliki manifest versi.
- [ ] Eksperimen model final dan baseline dapat dijalankan ulang.
- [ ] Ranking, Top-N, dan penjelasan fitur tervalidasi.
- [ ] Backend API, frontend, export CSV, dan seluruh halaman P1 selesai.
- [ ] Unit, integration, black-box, build, dan smoke test deployment lulus.
- [ ] Tidak ada secret dalam repository.
- [ ] Disclaimer tampil pada dashboard, detail, dan hasil ekspor.
- [ ] Dokumentasi metode konsisten dengan kode dan output aktual.
- [ ] Frontend Vercel dan backend Docker melalui Cloudflare Tunnel dapat diakses.

# 11. Risks and Mitigations

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Coverage HPS/jadwal tidak penuh | Sebagian fitur tidak tersedia | Coverage report, missing flag, pemilihan fitur berdasarkan coverage aktual |
| API INAPROC berubah/down | Enrichment gagal | Cache, checkpoint, retry terbatas, snapshot respons, jangan bergantung pada live API saat demo |
| 2026 belum satu tahun penuh | Perbandingan tahunan bias | Label snapshot, normalisasi, evaluasi temporal yang eksplisit |
| Tidak ada ground truth | Tidak dapat mengklaim akurasi fraud | Evaluasi unsupervised, baseline, stability, expert validation opsional |
| Nama penyedia tidak konsisten | Konsentrasi penyedia bias | Normalisasi konservatif, simpan nilai asli, audit perubahan nama |
| Duplikasi/multi-provider | Skor dan frekuensi ganda | Canonical package rule dan audit exclusion/aggregation |
| SHAP tidak konsisten dengan anomaly score | Penjelasan menyesatkan | Validasi terhadap skor, fallback ke permutation sensitivity dan deviasi fitur |
| Scope berkembang menjadi sistem audit penuh | Implementasi membesar | Patuhi In/Out Scope dan ponytail/YAGNI |
| Bahasa UI menuduh kecurangan | Risiko etis dan akademik | Gunakan “prioritas”, “ketidaklaziman”, “perlu ditinjau”; hindari “terbukti fraud” |

# 12. Open Decisions

| ID | Keputusan yang masih perlu dibuktikan | Waktu keputusan |
|---|---|---|
| OD-1 | Konfigurasi Isolation Forest final, termasuk `contamination` | Setelah eksperimen sensitivitas |
| OD-2 | Nilai default Top-N | Setelah melihat distribusi skor dan kebutuhan demo |
| OD-3 | Perlakuan final paket multi-provider: satu record canonical dengan daftar nilai sumber dan `eligible_for_model=false` | Diputuskan pada canonicalization, sebelum feature engineering |
| OD-4 | Fitur final berdasarkan coverage enrichment, EDA, multikolinearitas, dan leakage policy | Setelah feature engineering awal |
| OD-5 | SHAP dipakai sebagai penjelasan utama atau sekunder | Setelah validasi konsistensi explanation-score |
| OD-6 | PDF export masuk v1.0 final | Setelah P1 dashboard dan CSV stabil |

# 13. Traceability to Research Method

| Tahap penelitian | Keluaran produk |
|---|---|
| CRISP-DM Business Understanding | Problem statement, goals, batas klaim, target pengguna |
| CRISP-DM Data Understanding | Audit data, provenance, distribusi, kualitas, coverage |
| CRISP-DM Data Preparation | Canonical dataset, enrichment, feature matrix |
| CRISP-DM Modeling | Isolation Forest, baseline, konfigurasi, artefak |
| CRISP-DM Evaluation | Stability, sensitivity, temporal evaluation, explanation validation |
| CRISP-DM Deployment | FastAPI, Next.js, Docker, Vercel, Cloudflare Tunnel |
| RAD Requirements Planning | PRD, kebutuhan fungsional/nonfungsional, daftar halaman |
| RAD User Design | Navigasi, Activity Diagram, Sequence Diagram, rancangan UI |
| RAD Construction | Implementasi pipeline, model, backend, frontend, pengujian |
| RAD Cutover | Build final, deployment, smoke test, dokumentasi |

# 14. Change Log

| Versi | Tanggal | Perubahan |
|---|---|---|
| 1.0-draft | 12 Juli 2026 | Menulis ulang PRD memakai tujuh section inti: Problem Statement, Goals, Personas, User Stories, Functional Requirements, Non-Functional Requirements, dan Scope; menambahkan audit data, acceptance criteria, risiko, open decisions, dan traceability. |
