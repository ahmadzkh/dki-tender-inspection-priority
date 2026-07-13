# Sistem Prioritas Pemeriksaan Realisasi Tender DKI Jakarta

Sistem berbasis web untuk mengurutkan paket realisasi tender Pemerintah Provinsi DKI Jakarta berdasarkan tingkat ketidaklaziman menggunakan **Isolation Forest**. Sistem dirancang sebagai alat bantu prioritas pemeriksaan, bukan alat untuk menetapkan fraud, korupsi, kolusi, atau pelanggaran hukum.

## Status Project

> **Tahap saat ini: fondasi pengembangan selesai; integritas dan audit sumber data sudah reproducible.**

Dataset 2024-2026 telah dikumpulkan, diaudit, dan digabung. Empat CSV sumber disimpan pada layout raw yang immutable serta dicatat dalam manifest SHA-256 yang dapat diverifikasi. Pipeline audit menghasilkan report JSON dan Markdown dari raw sources tanpa memodifikasinya. Enrichment, feature engineering, model Machine Learning, backend API, antarmuka pengguna, pengujian tambahan, dan deployment belum dibangun.

| Komponen | Status |
|---|---|
| Dataset raw 2024, 2025, 2026 | Selesai |
| Audit dan penggabungan awal | Selesai |
| Audit sumber data reproducible | Selesai |
| PRD dan engineering contract | Selesai |
| Python environment dan quality tools | Selesai |
| Next.js frontend scaffold | Selesai |
| Folder target terstruktur | Selesai |
| Enrichment HPS, pagu, dan jadwal | Belum dimulai |
| Dataset canonical | Belum dimulai |
| Feature engineering | Belum dimulai |
| Isolation Forest dan evaluasi | Belum dimulai |
| FastAPI backend | Belum dimulai |
| Docker dan deployment | Belum dimulai |

## Judul Penelitian

**Rancang Bangun Sistem Prioritas Pemeriksaan Realisasi Tender Pemerintah Provinsi DKI Jakarta Menggunakan Isolation Forest Berbasis Web**

## Latar Belakang

Data realisasi tender pemerintah tersedia melalui portal resmi INAPROC. Jumlah paket, variasi nilai kontrak, banyaknya satuan kerja, dan pola kemenangan penyedia membuat pemeriksaan manual sulit diprioritaskan secara konsisten. Spreadsheet dapat menyimpan dan memfilter data, tetapi tidak otomatis membentuk baseline ketidaklaziman multivariat, menghitung konsentrasi penyedia, atau menjelaskan alasan sebuah paket ditempatkan pada urutan pemeriksaan tertentu.

Project ini mengolah data tender selesai menjadi fitur finansial, temporal, dan konsentrasi penyedia. Isolation Forest menghasilkan skor ketidaklaziman untuk mengurutkan record. Dashboard web menerjemahkan hasil model ke dalam statistik, filter, detail paket, penjelasan faktor, dan laporan yang dapat diunduh.

## Tujuan

1. Menggabungkan data realisasi tender DKI Jakarta secara dapat ditelusuri.
2. Memperkaya data paket menggunakan HPS, pagu, metode evaluasi, metadata, dan jadwal tender dari INAPROC.
3. Membentuk fitur finansial, temporal, dan konsentrasi penyedia.
4. Menghasilkan ranking prioritas pemeriksaan menggunakan Isolation Forest.
5. Menjelaskan faktor yang memengaruhi posisi prioritas setiap paket.
6. Menyediakan dashboard yang dapat digunakan pengguna non-teknis.
7. Menjaga interpretasi hasil agar tidak berubah menjadi tuduhan fraud.

## Batas Interpretasi

Skor model menunjukkan ketidaklaziman relatif terhadap pola data pembanding. Skor tinggi berarti sebuah paket layak ditinjau lebih dahulu, bukan berarti paket tersebut terbukti bermasalah.

Sistem tidak dapat membuktikan:

- korupsi atau fraud;
- suap atau gratifikasi;
- bid-rigging;
- kolusi antar peserta;
- manipulasi dokumen;
- kerugian negara.

Data seluruh peserta dan nilai penawaran pesaing tidak tersedia pada dataset utama. Pemeriksaan profesional tetap diperlukan untuk menarik kesimpulan hukum atau administratif.

## Dataset

### Sumber

Data diperoleh dari portal resmi INAPROC/LKPP:

- [INAPROC](https://inaproc.id/)
- [Data INAPROC](https://data.inaproc.id/)
- [Realisasi Pengadaan](https://data.inaproc.id/realisasi)

Filter pengunduhan:

| Filter | Nilai |
|---|---|
| Jenis instansi | Provinsi |
| Instansi | Provinsi DKI Jakarta |
| Tahun anggaran | 2024, 2025, 2026 |
| Sumber transaksi | Tender |
| Status paket | Selesai |
| Format | CSV |

### Audit Dataset Gabungan

Dataset utama:

```text
datasets/raw/realisasi_dki_jakarta_2024_2026.csv
```

| Item | Nilai |
|---|---:|
| Baris sumber sebelum pembersihan | 1.284 |
| Baris dataset gabungan | 1.279 |
| Kolom awal | 14 |
| Kode paket unik | 1.277 |
| Penyedia unik | 684 |
| Satuan kerja unik | 132 |
| Tahun 2024 | 312 baris |
| Tahun 2025 | 529 baris |
| Tahun 2026 | 438 baris |
| Status paket | 100% selesai |
| Sumber transaksi | 100% tender |

Tahun 2026 merupakan snapshot tahun berjalan per Juli 2026, bukan satu tahun kalender penuh. Total tahun 2026 tidak boleh dibandingkan langsung dengan total tahunan 2024 atau 2025 tanpa penanda dan normalisasi.

Lima baris pada file raw 2026 tidak memiliki nama penyedia dan tidak masuk ke dataset gabungan saat ini. Kode paket `10060212000` muncul tiga kali dengan penyedia berbeda. Perlakuan canonical untuk kasus tersebut harus ditetapkan sebelum feature engineering.

Audit yang dapat dijalankan ulang tersedia pada [`reports/data/source_audit.md`](reports/data/source_audit.md) dan [`reports/data/source_audit.json`](reports/data/source_audit.json). Report membedakan 1.284 baris annual raw dari 1.279 baris merged input agar lima supplier kosong tetap terlihat dalam data-quality trail.

### Kolom Awal

```text
nama_instansi
nama_satuan_kerja
kode_paket
kode_rup
tahun_anggaran
sumber_transaksi
sumber_dana
nama_penyedia
metode_pengadaan
jenis_pengadaan
nama_paket
status_paket
total_nilai
nilai_pdn
```

### Enrichment yang Direncanakan

Data paket akan diperkaya melalui detail paket INAPROC menggunakan `kode_paket`.

| Field | Fungsi analitik |
|---|---|
| HPS | Pembanding nilai realisasi |
| Pagu | Batas anggaran paket |
| Metode evaluasi | Konteks proses pemilihan |
| Metode tender | Konteks mekanisme pengadaan |
| Jadwal tahapan | Pembentukan fitur durasi |
| Lokasi pekerjaan | Konteks geografis |
| Cara pembayaran | Konteks kontrak |

Sampel awal 10 paket berhasil mengembalikan HPS dan pagu. Coverage seluruh paket belum diukur dan tidak boleh diasumsikan 100% sebelum pipeline enrichment selesai.

## Fitur Machine Learning

Daftar berikut merupakan kandidat. Fitur final ditetapkan setelah enrichment dan Exploratory Data Analysis (EDA).

### Fitur Finansial

- log nilai realisasi;
- rasio nilai realisasi terhadap HPS;
- rasio HPS terhadap pagu;
- penghematan terhadap HPS;
- rasio PDN terhadap nilai realisasi.

### Fitur Temporal

- durasi tender keseluruhan;
- durasi tahapan penawaran;
- durasi evaluasi;
- durasi masa sanggah;
- penanda snapshot tahun berjalan.

### Fitur Konsentrasi Penyedia

- frekuensi kemenangan penyedia;
- frekuensi kemenangan pada satuan kerja yang sama;
- pangsa nilai penyedia per satuan kerja dan tahun;
- Herfindahl-Hirschman Index (HHI) per satuan kerja dan tahun.

Rasio nilai realisasi terhadap HPS tidak diperlakukan sebagai bukti mark-up. Nilai yang dekat dengan satu hanya menunjukkan selisih kecil terhadap estimasi HPS dan tetap memerlukan pemeriksaan konteks.

## Metode

### CRISP-DM untuk Machine Learning

1. **Business Understanding**: menetapkan kebutuhan prioritas pemeriksaan dan batas klaim.
2. **Data Understanding**: mengaudit skema, distribusi, missing values, duplikasi, dan coverage enrichment.
3. **Data Preparation**: membentuk dataset canonical, melakukan enrichment, dan membangun feature matrix.
4. **Modeling**: melatih Isolation Forest dengan konfigurasi dan random seed yang tersimpan.
5. **Evaluation**: menguji stabilitas ranking, sensitivitas parameter, distribusi skor, temporal behavior, dan baseline transparan.
6. **Deployment**: menyajikan artefak model melalui FastAPI dan dashboard Next.js.

### RAD untuk Website

1. **Requirements Planning**: menyusun kebutuhan fungsional, nonfungsional, halaman, dan batas sistem.
2. **User Design**: merancang navigasi, Activity Diagram, Sequence Diagram, dan antarmuka.
3. **Construction**: membangun backend, frontend, integrasi, serta pengujian.
4. **Cutover**: menjalankan build final, deployment, smoke test, dan dokumentasi.

## Model dan Evaluasi

Isolation Forest dipilih karena bekerja tanpa label dan ringan untuk dataset tabular. Training berjalan pada CPU dan tidak membutuhkan GPU.

Project tidak memiliki ground-truth fraud/anomali tervalidasi. Accuracy, precision, recall, F1-score, dan confusion matrix tidak digunakan sebagai metrik utama. Evaluasi direncanakan melalui:

- stabilitas ranking antar random seed;
- overlap Top-N antar konfigurasi;
- sensitivitas `contamination`, jumlah estimator, dan subsampling;
- pemeriksaan distribusi skor;
- sanity check nilai fitur pada record prioritas;
- evaluasi temporal 2024-2025 terhadap snapshot 2026;
- perbandingan dengan baseline yang transparan;
- permutation sensitivity;
- SHAP jika hubungan explanation terhadap anomaly score telah tervalidasi.

Top-N menjadi mekanisme untuk menyesuaikan jumlah record dengan kapasitas pemeriksaan, bukan threshold label fraud.

## Fitur Aplikasi v1.0

- landing page dan penjelasan metodologi;
- dashboard statistik tender;
- ranking prioritas berdasarkan anomaly score;
- Top-N yang dapat diatur;
- filter tahun, satuan kerja, metode, jenis pengadaan, penyedia, nilai, dan skor;
- detail paket dan jadwal tender;
- penjelasan faktor yang memengaruhi skor;
- halaman dataset dan coverage enrichment;
- download hasil terfilter dalam CSV;
- disclaimer pada ranking, detail, dan laporan.

PDF report menjadi prioritas kedua setelah dashboard dan CSV stabil.

## Arsitektur yang Direncanakan

```text
Data INAPROC
      │
      ▼
Audit dan Enrichment Pipeline
      │
      ▼
Canonical Dataset dan Feature Matrix
      │
      ▼
Isolation Forest dan Explanation Artifacts
      │
      ▼
FastAPI Backend ──────► Next.js Frontend
      │                       │
      ▼                       ▼
Docker + VPS           Vercel
      │
      ▼
Cloudflare Tunnel
```

Prinsip arsitektur:

- satu backend FastAPI;
- satu frontend Next.js;
- artefak data dan model bersifat read-only pada runtime;
- tidak ada database, authentication, queue, atau microservices tambahan pada v1.0 tanpa kebutuhan yang terbukti;
- ranking dan explanation diprekomputasi jika memungkinkan.

## Tech Stack

| Layer | Teknologi |
|---|---|
| Data dan ML | Python, pandas, NumPy, scikit-learn |
| Interpretasi | Permutation sensitivity, SHAP setelah validasi |
| Backend | FastAPI, Pydantic |
| Frontend | Next.js App Router, TypeScript, Tailwind CSS |
| Testing Python | pytest |
| Testing frontend | Vitest/Testing Library setelah frontend tersedia |
| End-to-end | Playwright setelah alur utama stabil |
| Container | Docker Compose |
| Frontend hosting | Vercel |
| Backend hosting | VPS/server melalui Cloudflare Tunnel |
| Package manager | uv untuk Python, npm untuk frontend |

## Struktur Repository Saat Ini

```text
.
├── AGENTS.md
├── CLAUDE.md
├── PRD.md
├── README.md
├── TASKS.md
├── .gitignore
├── pipelines/
│   └── verify_source_manifest.py
└── datasets/
    ├── manifests/
    │   └── source_manifest.json
    ├── processed/
    └── raw/
        ├── inaproc_realisasi_tender_dki_jakarta_2024.csv
        ├── inaproc_realisasi_tender_dki_jakarta_2025.csv
        ├── inaproc_realisasi_tender_dki_jakarta_2026.csv
        └── realisasi_dki_jakarta_2024_2026.csv
```

Struktur aplikasi akan dibuat bertahap saat file pertamanya diperlukan. Rancangan target tercantum dalam [`CLAUDE.md`](CLAUDE.md).

## Menjalankan Project

Python environment, source-manifest verifier, source-data audit, dan scaffold frontend sudah tersedia. Backend dan pipeline pemodelan belum tersedia.

```bash
git clone https://github.com/ahmadzkh/dki-tender-inspection-priority.git
cd dki-tender-inspection-priority
uv sync
uv run python pipelines/verify_source_manifest.py
uv run python pipelines/audit_source_data.py
uv run pytest
npm --prefix frontend install
npm --prefix frontend run lint
npm --prefix frontend run build
```

Command enrichment pipeline, model, dan backend akan ditambahkan setelah implementasinya tersedia dan sudah diverifikasi.

## Roadmap

- [x] Menetapkan topik, ruang lingkup, dan batas interpretasi.
- [x] Mengunduh dataset DKI Jakarta 2024-2026.
- [x] Mengaudit dan menggabungkan dataset awal.
- [x] Menyusun PRD dan engineering contract.
- [x] Membuat layout raw immutable dan source manifest terverifikasi.
- [x] Membangun audit data reproducible.
- [ ] Membangun enrichment pipeline INAPROC yang resumable.
- [ ] Mengukur coverage HPS, pagu, dan jadwal.
- [ ] Membentuk dataset canonical satu paket per record.
- [ ] Menjalankan EDA dan feature engineering.
- [ ] Melatih dan mengevaluasi Isolation Forest.
- [ ] Memvalidasi feature influence dan explanation.
- [ ] Membangun FastAPI backend.
- [ ] Membangun Next.js frontend.
- [ ] Menambahkan CSV export dan pengujian.
- [ ] Membuat Docker runtime.
- [ ] Deploy backend dan frontend.
- [ ] Menyelesaikan release acceptance criteria sebelum penulisan BAB 4.

## Dokumentasi

- [`PRD.md`](PRD.md): masalah, tujuan, persona, user stories, requirements, scope, risiko, dan acceptance criteria.
- [`CLAUDE.md`](CLAUDE.md): tech stack, struktur, commands, coding rules, testing, security, dan agent contract.
- [`AGENTS.md`](AGENTS.md): instruksi wajib untuk agent yang bekerja di repository.
- [`TASKS.md`](TASKS.md): urutan `TASK-ML`, `TASK-BE`, dan `TASK-FE`, dependency, acceptance criteria, verification, serta status checklist.
- [`reports/data/source_audit.md`](reports/data/source_audit.md): ringkasan audit sumber data yang dapat diregenerasi.

`TASKS.md` menjadi single source of truth status implementasi. Agent hanya boleh mengubah task menjadi `[x]` setelah test, `verify-gate`, dan code review yang diwajibkan lulus.

## Prinsip Pengembangan

Project menerapkan pendekatan YAGNI melalui skill `ponytail`:

- membangun hanya kebutuhan yang sudah terbukti;
- menggunakan standard library atau dependency yang sudah tersedia sebelum menambah package;
- menghindari database, authentication, state manager, dan microservices tanpa kebutuhan;
- menulis perubahan kecil yang dapat diuji;
- menyimpan raw data tanpa modifikasi;
- memverifikasi hasil sebelum menyatakan task selesai.

## Reproducibility dan Integritas Data

Implementasi pipeline wajib:

- mempertahankan file raw;
- mencatat checksum, jumlah baris, skema, dan provenance;
- menyimpan konfigurasi, random seed, feature order, versi dataset, dan versi library;
- membedakan null dari nol;
- mencatat record yang dikeluarkan atau diagregasi;
- mencegah temporal leakage;
- menghasilkan artefak versioned yang dapat dilacak.

## Etika dan Disclaimer

Repository ini merupakan project penelitian. Hasil sistem hanya digunakan untuk menentukan urutan peninjauan data. Ranking tidak boleh dipublikasikan sebagai daftar pelaku fraud atau korupsi. Interpretasi akhir memerlukan dokumen pendukung, konteks pengadaan, dan pemeriksaan oleh pihak berwenang.

## Kontribusi

Project masih berada pada tahap awal dan belum membuka alur kontribusi publik formal. Perubahan harus mengikuti `PRD.md`, `CLAUDE.md`, dan `AGENTS.md`. Satu task logis menggunakan satu commit dengan format:

```text
type: subject
```

Subject maksimal 72 karakter. Jangan commit file `.env`, credential, token, private host, atau data nonpublik.

## Lisensi

Lisensi source code belum ditetapkan. Dataset berasal dari portal publik INAPROC dan tetap mengikuti ketentuan sumber aslinya. Jangan menganggap keberadaan dataset di repository sebagai pemindahan kepemilikan atau perubahan lisensi data.

## Tautan Repository

[github.com/ahmadzkh/dki-tender-inspection-priority](https://github.com/ahmadzkh/dki-tender-inspection-priority)
