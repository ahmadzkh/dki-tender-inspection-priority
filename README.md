# Sistem Prioritas Pemeriksaan Realisasi Tender DKI Jakarta

Sistem berbasis web untuk mengurutkan paket realisasi tender Pemerintah Provinsi DKI Jakarta berdasarkan tingkat ketidaklaziman menggunakan **Isolation Forest**. Sistem dirancang sebagai alat bantu prioritas pemeriksaan, bukan alat untuk menetapkan fraud, korupsi, kolusi, atau pelanggaran hukum.

## Status Project

> **Tahap saat ini: backend/frontend lokal dan Docker runtime terverifikasi; deployment publik durable masih pending.**

Dataset 2024-2026 telah dikumpulkan, diaudit, digabung, diperkaya, dicanonicalkan menjadi satu record per `kode_paket`, dianalisis melalui EDA reproducible, ditransformasi menjadi feature matrix leakage-safe, dibagi dengan split temporal, diberi baseline ranking transparan, dilatih dengan Isolation Forest, dan dievaluasi tanpa label ground truth. Empat CSV sumber disimpan pada layout raw yang immutable serta dicatat dalam manifest SHA-256 yang dapat diverifikasi. Pipeline audit dan enrichment menghasilkan report JSON/Markdown dari raw sources tanpa memodifikasinya. Full enrichment INAPROC sudah dijalankan untuk 1.277 kode paket unik dengan coverage 100%. Backend FastAPI read-only, frontend Next.js, Playwright E2E, integration contract, dan Docker runtime sudah tersedia untuk verifikasi lokal. Deployment publik durable masih menunggu Cloudflare named tunnel pada VPS/server target dan Vercel production smoke.

| Komponen | Status |
|---|---|
| Dataset raw 2024, 2025, 2026 | Selesai |
| Audit dan penggabungan awal | Selesai |
| Audit sumber data reproducible | Selesai |
| PRD dan engineering contract | Selesai |
| Python environment dan quality tools | Selesai |
| Next.js frontend scaffold | Selesai |
| Folder target terstruktur | Selesai |
| Enrichment HPS, pagu, dan jadwal | Selesai; coverage report 100% untuk 1.277 paket unik |
| Dataset canonical | Selesai; 1.277 paket unik, 1 multi-provider ditandai tidak eligible untuk model |
| EDA dan data-quality analysis | Selesai; report reproducible di `reports/eda/summary.md` |
| Feature engineering | Selesai; `datasets/processed/model_features.csv` berisi 1.276 baris dan 20 fitur |
| Split temporal model | Selesai; training 2024-2025 = 838 record, evaluation 2026 snapshot = 438 record |
| Baseline transparan | Selesai; robust z-score ranking di `artifacts/baseline_ranking.csv` |
| Training Isolation Forest | Selesai; `model_version=414f1691d2bccdd9`, ranking di `artifacts/isolation_forest_ranking.csv` |
| Evaluasi model | Selesai |
| Explanation model | Selesai; permutation sensitivity di `reports/model/explanation.md`, OD-5 dijawab |
| Freeze artifacts | Selesai; `artifacts/manifest.json`, 12 artifacts, integrity check |
| FastAPI backend scaffold | Selesai; `backend/app/main.py`, termasuk dalam suite 110 test Python |
| FastAPI backend API | Selesai; health/meta/summary/filters/ranking/detail/export/evaluation |
| Frontend product UI | Selesai lokal; landing, dashboard, detail, dataset, methodology, evaluation |
| Docker runtime | Selesai lokal; image healthy dan restart verified |
| Local quality gate | Selesai; 110 test Python, 24 Playwright lintas Chrome/Edge/Firefox, npm audit 0 vulnerability |
| Public deployment | Pending; butuh Cloudflare named tunnel dan Vercel smoke |

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

Lima baris pada file raw 2026 tidak memiliki nama penyedia dan tidak masuk ke dataset gabungan saat ini. Kode paket `10060212000` muncul tiga kali dengan penyedia berbeda. Pipeline canonical mempertahankan satu record untuk paket tersebut, menyimpan daftar penyedia/nilai sumber, dan menandainya `eligible_for_model=false` agar tidak diam-diam masuk fitur penyedia atau finansial.

Audit yang dapat dijalankan ulang tersedia pada [`reports/data/source_audit.md`](reports/data/source_audit.md) dan [`reports/data/source_audit.json`](reports/data/source_audit.json). Report membedakan 1.284 baris annual raw dari 1.279 baris merged input agar lima supplier kosong tetap terlihat dalam data-quality trail.

Dataset canonical tersedia pada `datasets/processed/tenders_canonical.csv`. Report kualitasnya tersedia pada [`reports/data/canonical_data_quality.md`](reports/data/canonical_data_quality.md) dan [`reports/data/canonical_data_quality.json`](reports/data/canonical_data_quality.json).

EDA reproducible tersedia pada [`reports/eda/summary.md`](reports/eda/summary.md) dengan tabel statistik di `reports/eda/tables/` dan visualisasi SVG di `reports/eda/figures/`. Report menyebut row count, checksum canonical dataset, missingness, outlier univariat, distribusi kategori, konsentrasi penyedia/satuan kerja, dan batas interpretasi snapshot parsial 2026.

Feature matrix tersedia pada `datasets/processed/model_features.csv` dengan schema eksplisit di `artifacts/feature_schema.json`. Pipeline `pipelines/build_model_features.py` membentuk 20 fitur finansial, temporal, kategori, dan agregat prior-year/prior-observation untuk 1.276 record eligible. Fitur agregat penyedia/satuan kerja hanya memakai record sebelumnya dalam tahun yang sama setelah sorting jadwal dan `package_id`, sehingga tidak memakai informasi masa depan.

Split temporal tersedia pada `datasets/manifests/model_split.json` dengan konfigurasi eksperimen di `artifacts/model_experiment_config.json` dan catatan keputusan di [`reports/model/split_decision.md`](reports/model/split_decision.md). Training memakai 838 record eligible dari 2024-2025. Evaluation memakai 438 record eligible dari snapshot 2026 dan tidak diperlakukan sebagai tahun kalender penuh.

Baseline transparan tersedia pada `artifacts/baseline_ranking.csv` dengan konfigurasi di `artifacts/baseline_config.json` dan report di [`reports/model/baseline.md`](reports/model/baseline.md). Baseline memakai median dan skala robust dari train split 2024-2025, lalu memberi skor deviasi fitur. Skor ini adalah pembanding prioritas pemeriksaan, bukan label pelanggaran.

Model Isolation Forest tersedia pada `artifacts/isolation_forest_model.joblib` dengan konfigurasi di `artifacts/isolation_forest_config.json` dan ranking di `artifacts/isolation_forest_ranking.csv`. Model memakai `StandardScaler`, `n_estimators=200`, `random_seed=42`, `n_jobs=1`, dan dilatih hanya pada train split 2024-2025. Skor semakin tinggi berarti paket semakin diprioritaskan untuk pemeriksaan, bukan bukti pelanggaran.

Evaluasi model tersedia pada [`reports/model/evaluation.md`](reports/model/evaluation.md) dan `reports/model/evaluation.json`. Pipeline `modeling/evaluate_anomaly_ranking.py` membandingkan stabilitas antar seed, sensitivitas `contamination`, jumlah estimator, dan subsampling, overlap Top-N dengan baseline transparan, distribusi skor, serta perilaku temporal train/evaluation. Keputusan saat ini mempertahankan konfigurasi Isolation Forest `414f1691d2bccdd9`, memakai Top-20 sebagai default tampilan kapasitas pemeriksaan, dan mempertahankan 20 fitur sampai validasi explanation selesai.

Explanation model tersedia pada [`reports/model/explanation.md`](reports/model/explanation.md) dan `artifacts/ranking_explanations.json`. Pipeline `modeling/explain_anomaly_ranking.py` menggunakan permutation sensitivity sebagai metode primer karena SHAP tidak terinstal. Setiap record Top-20 dan Top-50 memiliki minimal tiga faktor dengan nilai asli, persentil, dan dampak perubahan. Keputusan `OD-5` ditetapkan: permutation sensitivity menjadi fallback transparan jika SHAP tidak tersedia.

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

### Enrichment INAPROC

Data paket diperkaya melalui detail paket INAPROC menggunakan `kode_paket`. Pipeline `pipelines/enrich_tender_details.py` menyimpan respons per paket, checkpoint, failure log, dan ringkasan run agar proses yang terputus dapat dilanjutkan tanpa mengulang paket yang sudah sukses.

| Field | Fungsi analitik |
|---|---|
| HPS | Pembanding nilai realisasi |
| Pagu | Batas anggaran paket |
| Metode evaluasi | Konteks proses pemilihan |
| Metode tender | Konteks mekanisme pengadaan |
| Jadwal tahapan | Pembentukan fitur durasi |
| Lokasi pekerjaan | Konteks geografis |
| Cara pembayaran | Konteks kontrak |

Full enrichment menghasilkan 1.277 respons sukses dari 1.277 paket unik. Coverage HPS, pagu, metode evaluasi, metadata, dan jadwal tercatat 100% pada `reports/data/enrichment_coverage.md`.

## Fitur Machine Learning

Daftar berikut sudah dibentuk oleh `pipelines/build_model_features.py` untuk record yang `eligible_for_model=true`. Urutan fitur dan encoder kategori disimpan pada `artifacts/feature_schema.json` agar training dan scoring memakai kontrak yang sama.

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
| Testing frontend | ESLint, TypeScript, dan Next.js production build |
| End-to-end | Playwright pada Chrome, Edge, dan Firefox |
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
├── artifacts/
│   ├── baseline_config.json
│   ├── baseline_ranking.csv
│   ├── feature_schema.json
│   ├── isolation_forest_config.json
│   ├── isolation_forest_model.joblib
│   ├── isolation_forest_ranking.csv
│   └── model_experiment_config.json
├── modeling/
│   ├── build_baseline_ranking.py
│   ├── evaluate_anomaly_ranking.py
│   └── train_isolation_forest.py
├── pipelines/
│   ├── audit_source_data.py
│   ├── analyze_tender_data.py
│   ├── build_canonical_dataset.py
│   ├── build_model_features.py
│   ├── define_model_split.py
│   ├── enrich_tender_details.py
│   ├── report_enrichment_coverage.py
│   └── verify_source_manifest.py
├── tests/
│   ├── test_analyze_tender_data.py
│   ├── test_build_canonical_dataset.py
│   ├── test_build_model_features.py
│   ├── test_build_baseline_ranking.py
│   ├── test_define_model_split.py
│   ├── test_evaluate_anomaly_ranking.py
│   ├── test_train_isolation_forest.py
│   └── ...
├── reports/
│   ├── data/
│   ├── eda/
│   └── model/
├── frontend/
└── datasets/
    ├── manifests/
    │   ├── model_split.json
    │   └── source_manifest.json
    ├── processed/
    │   ├── model_features.csv
    │   └── tenders_canonical.csv
    └── raw/
        ├── inaproc_realisasi_tender_dki_jakarta_2024.csv
        ├── inaproc_realisasi_tender_dki_jakarta_2025.csv
        ├── inaproc_realisasi_tender_dki_jakarta_2026.csv
        └── realisasi_dki_jakarta_2024_2026.csv
```

Struktur utama aplikasi sudah tersedia. Kontrak engineering dan batas deployment tercantum dalam [`CLAUDE.md`](CLAUDE.md).

## Menjalankan Project

Python environment, source-manifest verifier, source-data audit, enrichment runner, canonical dataset builder, EDA generator, training Isolation Forest, evaluasi model, FastAPI backend, Next.js frontend, Playwright E2E, dan Docker runtime sudah tersedia.

```bash
git clone https://github.com/ahmadzkh/dki-tender-inspection-priority.git
cd dki-tender-inspection-priority
uv sync
uv run python pipelines/verify_source_manifest.py
uv run python pipelines/audit_source_data.py
INAPROC_DETAIL_API_BASE_URL="<detail-api-base-url>" uv run python pipelines/enrich_tender_details.py --limit 10
uv run python pipelines/report_enrichment_coverage.py
uv run python pipelines/build_canonical_dataset.py
uv run python pipelines/analyze_tender_data.py
uv run python pipelines/build_model_features.py
uv run python pipelines/define_model_split.py
uv run python modeling/build_baseline_ranking.py
uv run python modeling/train_isolation_forest.py
uv run python modeling/evaluate_anomaly_ranking.py
uv run python modeling/explain_anomaly_ranking.py
uv run python modeling/freeze_artifacts.py
uv run pytest
npm --prefix frontend install
npm --prefix frontend run lint
npm --prefix frontend run build

# Backend API
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# Frontend E2E
cd frontend && npm exec playwright test

# Docker backend runtime
docker compose build
docker compose up -d
docker compose down
```

## Roadmap

- [x] Menetapkan topik, ruang lingkup, dan batas interpretasi.
- [x] Mengunduh dataset DKI Jakarta 2024-2026.
- [x] Mengaudit dan menggabungkan dataset awal.
- [x] Menyusun PRD dan engineering contract.
- [x] Membuat layout raw immutable dan source manifest terverifikasi.
- [x] Membangun audit data reproducible.
- [x] Membangun enrichment pipeline INAPROC yang resumable.
- [x] Mengukur coverage HPS, pagu, dan jadwal.
- [x] Membentuk dataset canonical satu paket per record.
- [x] Menjalankan EDA dan data-quality analysis.
- [x] Membangun feature engineering leakage-safe.
- [x] Menetapkan split temporal training/evaluation.
- [x] Membangun baseline ranking transparan.
- [x] Melatih Isolation Forest reproducible.
- [x] Mengevaluasi stabilitas, sensitivitas, perilaku temporal, dan baseline.
- [x] Memvalidasi feature influence dan explanation (permutation sensitivity, OD-5).
- [x] Membekukan artefak backend-ready dengan manifest integrity check.
- [x] Scaffold dan finalisasi FastAPI backend (main.py, CORS, OpenAPI, bagian dari 110 test Python).
- [x] Implementasi artifact loader dan typed API contracts.
- [x] Membangun Next.js frontend.
- [x] Menambahkan CSV export dan pengujian.
- [x] Membuat Docker runtime.
- [ ] Deploy backend dan frontend.
- [x] Menyelesaikan local release acceptance criteria untuk penulisan implementasi dan pengujian BAB 4.
- [ ] Menyelesaikan public deployment acceptance sebelum finalisasi subsection cutover/deployment.

## Dokumentasi

- [`PRD.md`](PRD.md): masalah, tujuan, persona, user stories, requirements, scope, risiko, dan acceptance criteria.
- [`CLAUDE.md`](CLAUDE.md): tech stack, struktur, commands, coding rules, testing, security, dan agent contract.
- [`AGENTS.md`](AGENTS.md): instruksi wajib untuk agent yang bekerja di repository.
- [`TASKS.md`](TASKS.md): urutan `TASK-ML`, `TASK-BE`, dan `TASK-FE`, dependency, acceptance criteria, verification, serta status checklist.
- [`reports/data/source_audit.md`](reports/data/source_audit.md): ringkasan audit sumber data yang dapat diregenerasi.
- `reports/data/enrichment_coverage.md`: ringkasan coverage enrichment yang dapat diregenerasi setelah full enrichment.
- `reports/data/canonical_data_quality.md`: ringkasan kualitas dataset canonical yang dapat diregenerasi.
- `reports/eda/summary.md`: ringkasan EDA, tabel statistik, dan visualisasi yang dapat diregenerasi dari canonical dataset.
- `artifacts/feature_schema.json`: urutan fitur, encoder kategori, checksum canonical dataset, dan leakage policy feature matrix.
- `datasets/manifests/model_split.json`: manifest split temporal 2024-2025 ke snapshot 2026.
- `reports/model/split_decision.md`: catatan keputusan split temporal dan leakage policy modeling.
- `artifacts/baseline_ranking.csv`: ranking baseline transparan yang deterministik.
- `reports/model/baseline.md`: metode, keterbatasan, dan batas interpretasi baseline.
- `artifacts/isolation_forest_config.json`: konfigurasi, versi dataset, preprocessing, hyperparameter, dan versi library model.
- `artifacts/isolation_forest_ranking.csv`: ranking Isolation Forest untuk 1.276 record eligible.
- `artifacts/isolation_forest_model.joblib`: artefak model dan preprocessor untuk scoring ulang.
- `reports/model/evaluation.md`: evaluasi stabilitas, sensitivitas, distribusi skor, perilaku temporal, baseline comparison, dan keputusan Top-N.
- `reports/model/tables/`: tabel seed stability, hyperparameter sensitivity, dan baseline comparison.
- `reports/model/figures/`: visualisasi distribusi skor dan sensitivitas hyperparameter.
- `reports/model/explanation.md`: penjelasan fitur permutation sensitivity untuk model Isolation Forest.
- `artifacts/ranking_explanations.json`: faktor per record (Top-20, Top-50, all).
- `artifacts/manifest.json`: manifest integritas artefak yang berisi checksum SHA-256, versi, jumlah baris, dan metadata file penting untuk kebutuhan backend.

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
