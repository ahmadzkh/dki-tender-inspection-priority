# Development Task Tracker

## Sistem Prioritas Pemeriksaan Realisasi Tender DKI Jakarta

Dokumen ini menjadi **single source of truth** untuk urutan implementasi project. `PRD.md` menjelaskan produk, `CLAUDE.md` menjelaskan aturan teknis, sedangkan `TASKS.md` mencatat pekerjaan operasional.

## Status Marker

- `[ ]` belum selesai.
- `[x]` selesai dan sudah melewati seluruh Definition of Done.

Markdown tidak mencentang dirinya sendiri. Agent yang menyelesaikan task wajib mengubah `[ ]` menjadi `[x]` dalam perubahan yang sama setelah verifikasi dan code review lulus. Task parsial tetap `[ ]`.

## Aturan Eksekusi

1. Baca `AGENTS.md`, `PRD.md`, `CLAUDE.md`, dan `TASKS.md` sebelum bekerja.
2. Pilih task belum selesai dengan dependency yang seluruhnya sudah `[x]`.
3. Kerjakan satu task ID per perubahan logis. Jangan menggabungkan task berbeda.
4. Terapkan TDD untuk logika non-trivial: buat test gagal, implementasi minimal, lalu pastikan test lulus.
5. Jalankan pemeriksaan task-specific dan `verify-gate`.
6. Jalankan `software-development:requesting-code-review` untuk perubahan kode sebelum task dicentang.
7. Jalankan `ponytail-review` untuk mendeteksi over-engineering pada perubahan kode medium/besar.
8. Gunakan `github:github-code-review` jika perubahan diajukan melalui Pull Request.
9. Perbaiki seluruh temuan blocking, jalankan ulang verifikasi, baru ubah task menjadi `[x]`.
10. Update `README.md`, `PRD.md`, atau `CLAUDE.md` jika perilaku, scope, command, atau arsitektur berubah.
11. Commit/push hanya ketika diminta pengguna. Format commit tetap `type: subject`, maksimal 72 karakter.

## Definition of Done

Task hanya boleh dicentang jika seluruh kondisi berikut terpenuhi:

- Deliverable task tersedia pada path yang ditentukan.
- Acceptance criteria task terpenuhi.
- Test task-specific lulus.
- Build/type-check/lint yang relevan lulus atau belum tersedia dengan alasan yang sah.
- Tidak ada regression baru.
- Secret scan dan pemeriksaan raw-data integrity lulus jika relevan.
- Code review tidak memiliki security concern atau logic error blocking.
- Temuan `ponytail-review` blocking sudah diselesaikan.
- Dokumentasi terkait konsisten dengan implementasi aktual.
- Tidak ada server development yang tertinggal.
- Checkbox task diperbarui dalam perubahan yang sama.

## Code Review Skills

| Kebutuhan | Skill | Kapan digunakan |
|---|---|---|
| Machine verification | `verify-gate` | Setelah implementasi, sebelum review |
| Pre-commit code review | `software-development:requesting-code-review` | Semua task kode dengan perubahan non-trivial |
| Over-engineering review | `ponytail-review` | Perubahan kode medium/besar |
| GitHub Pull Request review | `github:github-code-review` | Hanya jika ada PR |

Pencarian `/find-skills` menemukan `obra/superpowers@requesting-code-review` sebagai skill eksternal paling populer. Hermes sudah memiliki `software-development:requesting-code-review` dengan workflow security scan, quality gate, independent reviewer, dan fix loop. Instalasi skill tambahan tidak diperlukan saat ini.

## Urutan Milestone

| Milestone | Task | Ketentuan |
|---|---|---|
| M1 - Data foundation | `TASK-ML-001` sampai `TASK-ML-006` | Harus selesai berurutan |
| M2 - Analysis and model | `TASK-ML-007` sampai `TASK-ML-014` | Backend tidak boleh memakai artefak sementara |
| M3 - API contract | `TASK-BE-001` sampai `TASK-BE-003` | `TASK-FE-001` dan `TASK-FE-002` boleh berjalan paralel |
| M4 - Product implementation | Sisa `TASK-BE-*` dan `TASK-FE-*` | FE mengikuti kontrak API terverifikasi |
| M5 - Deployment | `TASK-BE-010`, `TASK-BE-011`, `TASK-FE-012` | Hanya setelah test/build lulus |

---

# TASK-ML - Machine Learning and Data Pipeline

## Data Foundation

### [x] TASK-ML-001 - Bootstrap Python environment and quality tools

- **Depends on:** none.
- **Goal:** menyediakan environment Python reproducible tanpa membangun boilerplate aplikasi.
- **Deliverables:** `pyproject.toml`, `uv.lock`, konfigurasi Ruff dan pytest, package/module minimum yang dibutuhkan task berikutnya.
- **Acceptance:** dependency runtime dan development dipisahkan; Python 3.11+ terkunci; `uv sync`, Ruff, dan pytest dapat dijalankan dari root.
- **Verification:** `uv sync`, `uv run ruff check .`, dan `uv run pytest` exit 0; test awal boleh berupa smoke test environment.

### [x] TASK-ML-002 - Establish immutable dataset layout and source manifest

- **Depends on:** `TASK-ML-001`.
- **Goal:** memisahkan raw, processed, manifest, dan report tanpa kehilangan file sumber.
- **Deliverables:** `datasets/raw/`, `datasets/processed/`, `datasets/manifests/source_manifest.json`, serta referensi path yang diperbarui.
- **Acceptance:** empat CSV saat ini dipindahkan atau disalin secara terverifikasi; SHA-256, byte size, row count, schema, source year, dan provenance tercatat; hash raw sebelum dan setelah migrasi sama.
- **Verification:** script/check manifest membandingkan seluruh hash dan row count; `git diff` memastikan tidak ada modifikasi isi raw yang tidak disengaja.

### [x] TASK-ML-003 - Build reproducible source-data audit pipeline

- **Depends on:** `TASK-ML-002`.
- **Goal:** mengganti audit manual dengan pipeline yang dapat dijalankan ulang.
- **Deliverables:** `pipelines/audit_source_data.py`, test unit, dan report audit pada `reports/data/source_audit.{json,md}`.
- **Acceptance:** validasi 14 kolom, identifier string, tahun, status `SELESAI`, sumber `Tender`, missing values, duplikasi, multi-provider, distribusi per tahun, penyedia, dan satuan kerja.
- **Verification:** fixture invalid wajib gagal dengan pesan spesifik; data aktual menghasilkan angka yang konsisten dengan audit awal atau perubahan dijelaskan.

### [x] TASK-ML-004 - Build resumable INAPROC enrichment pipeline

- **Depends on:** `TASK-ML-003`.
- **Goal:** mengambil detail paket tanpa mengulang request sukses atau kehilangan progres.
- **Deliverables:** `pipelines/enrich_tender_details.py`, cache/checkpoint raw terstruktur, konfigurasi timeout/retry/delay, test parser dan resume menggunakan respons fixture.
- **Acceptance:** request menggunakan `kode_paket`; timeout dan retry terbatas; paket sukses dilewati saat resume; HTTP error dan response invalid dicatat; tidak ada live network dalam unit test.
- **Verification:** simulasi interrupted run dilanjutkan tanpa duplicate request; parser diuji untuk sukses, null field, response malformed, 4xx, dan 5xx.

### [ ] TASK-ML-005 - Run full enrichment and publish coverage report

- **Depends on:** `TASK-ML-004`.
- **Goal:** mengukur ketersediaan HPS, pagu, metode, metadata, dan jadwal untuk seluruh kode paket unik.
- **Deliverables:** snapshot/cache enrichment lengkap dan `reports/data/enrichment_coverage.{json,md}`.
- **Acceptance:** total sukses, gagal, missing, HTTP status, serta coverage per field dan tahun dilaporkan; seluruh kegagalan dapat di-resume; klaim 10-sampel diganti dengan hasil penuh.
- **Verification:** jumlah paket attempted sama dengan jumlah kode paket unik yang eligible; rerun tidak mengulang request sukses; spot-check paket terhadap respons raw.

### [ ] TASK-ML-006 - Build canonical one-package-per-record dataset

- **Depends on:** `TASK-ML-005`.
- **Goal:** menghasilkan unit analisis satu `kode_paket` per record secara transparan.
- **Deliverables:** `pipelines/build_canonical_dataset.py`, `datasets/processed/tenders_canonical.csv`, data-quality report, dan test canonicalization.
- **Acceptance:** perlakuan lima supplier kosong dan paket `10060212000` terdokumentasi; source values dipertahankan; missing enrichment tetap null dengan availability flags; provenance tersedia.
- **Verification:** `kode_paket` unik; jumlah input/output dan seluruh exclusion/aggregation reconcile; tidak ada identifier berubah menjadi numerik.

## Analysis and Feature Engineering

### [ ] TASK-ML-007 - Produce reproducible EDA and data-quality analysis

- **Depends on:** `TASK-ML-006`.
- **Goal:** memahami distribusi dan menentukan fitur berdasarkan bukti, bukan asumsi.
- **Deliverables:** `pipelines/analyze_tender_data.py`, `reports/eda/summary.md`, tabel statistik, dan visualisasi relevan.
- **Acceptance:** analisis nilai, HPS/pagu, missingness, outlier univariat, kategori, supplier/work-unit concentration, tahun, dan dampak snapshot parsial 2026; chart tidak menduplikasi informasi tanpa alasan.
- **Verification:** report dapat diregenerasi dari canonical dataset dan menyebut row count serta versi dataset yang benar.

### [ ] TASK-ML-008 - Build leakage-safe model features

- **Depends on:** `TASK-ML-007`.
- **Goal:** membentuk fitur finansial, temporal, dan konsentrasi secara deterministik.
- **Deliverables:** `pipelines/build_model_features.py`, `datasets/processed/model_features.csv`, `artifacts/feature_schema.json`, dan unit test formula.
- **Acceptance:** log nilai, rasio kontrak/HPS, rasio HPS/pagu, savings ratio, PDN ratio, durasi, frekuensi, supplier share, dan HHI dihitung jika didukung data; zero/null division aman; kategori unseen dapat ditangani.
- **Verification:** test menggunakan contoh kecil dengan hasil manual; tidak ada infinite value; feature order eksplisit; aggregate features tidak memakai informasi masa depan.

### [ ] TASK-ML-009 - Define temporal evaluation protocol and model split

- **Depends on:** `TASK-ML-008`.
- **Goal:** menetapkan penggunaan 2024-2025 dan snapshot 2026 tanpa menganggap 2026 tahun penuh.
- **Deliverables:** `datasets/manifests/model_split.json`, konfigurasi eksperimen, dan catatan keputusan pada report model.
- **Acceptance:** training/evaluation windows, cut-off, eligible records, excluded records, dan leakage policy eksplisit; split dapat direproduksi dari manifest.
- **Verification:** assertion memastikan record tidak melintasi split secara salah dan fitur historis tidak memakai agregat masa depan.

### [ ] TASK-ML-010 - Implement transparent anomaly-ranking baseline

- **Depends on:** `TASK-ML-009`.
- **Goal:** menyediakan pembanding yang mudah dijelaskan untuk menilai manfaat Isolation Forest.
- **Deliverables:** baseline sederhana yang disetujui, ranking baseline, konfigurasi, dan test arah skor.
- **Acceptance:** baseline menggunakan feature matrix yang sama; ranking deterministik; keterbatasan dicatat; tidak menghasilkan label fraud.
- **Verification:** nilai ekstrem fixture berada di atas nilai normal; rerun menghasilkan ranking identik.

## Modeling and Evaluation

### [ ] TASK-ML-011 - Train reproducible Isolation Forest artifacts

- **Depends on:** `TASK-ML-010`.
- **Goal:** melatih model dan menyimpan seluruh metadata yang diperlukan untuk scoring ulang.
- **Deliverables:** `modeling/train_isolation_forest.py`, model/preprocessor artifact, config JSON, feature order, ranking CSV, dan test reproducibility.
- **Acceptance:** random seed, hyperparameters, library versions, dataset manifest, preprocessing, arah anomaly score, dan model version tersimpan; CPU-only.
- **Verification:** dua run dengan konfigurasi sama menghasilkan skor dalam toleransi dan ranking yang sama; seluruh eligible record memiliki finite score.

### [ ] TASK-ML-012 - Evaluate stability, sensitivity, temporal behavior, and baseline

- **Depends on:** `TASK-ML-011`.
- **Goal:** memilih konfigurasi model menggunakan evaluasi yang sesuai untuk data tanpa label.
- **Deliverables:** `modeling/evaluate_anomaly_ranking.py`, `reports/model/evaluation.{json,md}`, tabel/plot sensitivity, dan keputusan konfigurasi final.
- **Acceptance:** evaluasi antar seed, Top-N overlap, contamination/estimator/subsample sensitivity, score distribution, temporal behavior, dan baseline comparison; accuracy/F1 tidak diklaim.
- **Verification:** report dapat diregenerasi; semua angka ditelusuri ke config dan artifact version; keputusan final menjawab `OD-1`, `OD-2`, dan sebagian `OD-4`.

### [ ] TASK-ML-013 - Validate model explanations

- **Depends on:** `TASK-ML-012`.
- **Goal:** menghasilkan alasan ranking yang konsisten dengan anomaly score.
- **Deliverables:** permutation sensitivity, eksperimen SHAP bila kompatibel, `artifacts/ranking_explanations.json`, dan `reports/model/explanation_validation.md`.
- **Acceptance:** setiap Top-N memiliki minimal tiga faktor dengan nilai asli dan konteks; hubungan explanation-score diuji; fallback transparan dipakai jika SHAP tidak valid.
- **Verification:** perturbasi fitur fixture mengubah skor/penjelasan pada arah yang dapat dijelaskan; keputusan menjawab `OD-5`.

### [ ] TASK-ML-014 - Freeze versioned backend-ready artifacts

- **Depends on:** `TASK-ML-013`.
- **Goal:** menyediakan kontrak artefak read-only yang stabil untuk backend.
- **Deliverables:** `artifacts/manifest.json`, ranking final, explanation artifact, summary/filter artifact, schema/version docs, dan integrity checks.
- **Acceptance:** manifest berisi checksum, dataset version, model version, generated time, schema version, row count, dan path relatif; tidak ada runtime retraining.
- **Verification:** loader ad-hoc membaca seluruh artifact, memvalidasi hash/schema, menemukan package detail, dan menghasilkan Top-N sesuai ranking final.

---

# TASK-BE - FastAPI Backend

## Foundation and Contracts

### [ ] TASK-BE-001 - Scaffold minimal FastAPI backend

- **Depends on:** `TASK-ML-001`.
- **Goal:** menyediakan satu aplikasi FastAPI tanpa database, auth, atau service tambahan.
- **Deliverables:** `backend/app/main.py`, konfigurasi minimum, package structure, test startup, dan command yang benar pada `CLAUDE.md`.
- **Acceptance:** aplikasi start, OpenAPI tersedia, tidak ada hardcoded machine path, dan dependency hanya yang diperlukan.
- **Verification:** `uv run fastapi dev backend/app/main.py` start; smoke request berhasil; process dihentikan setelah test.

### [ ] TASK-BE-002 - Implement artifact loader and typed API contracts

- **Depends on:** `TASK-BE-001`, `TASK-ML-014`.
- **Goal:** memvalidasi artifact sekali saat startup dan menetapkan kontrak response stabil.
- **Deliverables:** Pydantic schemas, `backend/app/services/artifact_store.py`, config paths, version metadata, dan unit test.
- **Acceptance:** checksum/schema/version incompatibility gagal jelas; null tidak diubah menjadi nol; score direction dan disclaimer tersedia pada contract.
- **Verification:** valid artifact load sekali; missing/corrupt/incompatible artifact menghasilkan failure terkontrol.

### [ ] TASK-BE-003 - Add health and metadata endpoints

- **Depends on:** `TASK-BE-002`.
- **Goal:** menyediakan readiness serta versi dataset/model untuk deployment dan frontend.
- **Deliverables:** `GET /api/v1/health` dan `GET /api/v1/meta` beserta test.
- **Acceptance:** health membedakan process alive dan artifact ready; metadata tidak membocorkan local path.
- **Verification:** TestClient menguji kondisi ready dan artifact failure.

## Read-only Product API

### [ ] TASK-BE-004 - Add summary and filter-option endpoints

- **Depends on:** `TASK-BE-003`.
- **Goal:** menyediakan statistik dashboard dan pilihan filter dari artifact aktual.
- **Deliverables:** `GET /api/v1/summary`, `GET /api/v1/filters`, schemas, service logic, dan test.
- **Acceptance:** statistik paket, nilai, supplier, satker, tahun, score distribution, serta filter options konsisten dengan artifact; 2026 berlabel snapshot parsial.
- **Verification:** nilai endpoint dibandingkan dengan artifact fixture dan production artifact.

### [ ] TASK-BE-005 - Add ranking endpoint with filters and pagination

- **Depends on:** `TASK-BE-004`.
- **Goal:** menyediakan ranking yang dapat difilter, diurutkan, dipaginasi, dan dibatasi Top-N.
- **Deliverables:** `GET /api/v1/rankings`, validated query parameters, service logic, dan integration test.
- **Acceptance:** filter tahun/satker/metode/jenis/supplier/nilai/skor dapat digabung; default urut skor tertinggi; pagination metadata benar; invalid query menghasilkan 4xx.
- **Verification:** fixture 52-row menguji page terakhir, filter combinations, stable ordering, Top-N, empty result, dan boundary values.

### [ ] TASK-BE-006 - Add package-detail endpoint

- **Depends on:** `TASK-BE-005`.
- **Goal:** mengembalikan source, enrichment, feature, score, explanation, provenance, dan source link satu paket.
- **Deliverables:** `GET /api/v1/packages/{package_id}`, typed detail schema, dan test.
- **Acceptance:** package tidak ditemukan menghasilkan 404; missing data tetap null; penjelasan memakai bahasa netral dan menyertakan disclaimer.
- **Verification:** paket normal, Top-N, missing enrichment, dan unknown ID diuji.

### [ ] TASK-BE-007 - Add filter-consistent CSV export

- **Depends on:** `TASK-BE-005`.
- **Goal:** mengunduh ranking sesuai filter dan urutan aktif.
- **Deliverables:** `GET /api/v1/export.csv`, filename/headers, disclaimer metadata yang sesuai format, dan test.
- **Acceptance:** jumlah, urutan, filter, field, encoding UTF-8, dan nilai null konsisten dengan ranking API.
- **Verification:** hasil CSV diparse ulang dan dibandingkan record-per-record dengan response ranking untuk query sama.

### [ ] TASK-BE-008 - Harden API errors, CORS, logging, and security boundaries

- **Depends on:** `TASK-BE-003` sampai `TASK-BE-007`.
- **Goal:** memastikan API aman untuk publikasi read-only.
- **Deliverables:** CORS allowlist, centralized safe errors, structured logging, request validation, dan security tests.
- **Acceptance:** tidak ada stack trace/local path/secret pada response; unexpected error menjadi safe 500; allowed origin configurable; logs memuat artifact version tanpa payload sensitif.
- **Verification:** test invalid origin/parameter/artifact/error; secret scan lulus.

### [ ] TASK-BE-009 - Complete backend integration, performance, and OpenAPI verification

- **Depends on:** `TASK-BE-008`.
- **Goal:** membekukan kontrak backend yang siap dipakai frontend dan deployment.
- **Deliverables:** integration suite, OpenAPI snapshot/schema validation, performance probe, dan dokumentasi endpoint.
- **Acceptance:** seluruh endpoint P1 lulus; p95 summary/ranking <1 detik setelah warm-up pada dataset v1; contract sesuai `PRD.md`.
- **Verification:** pytest backend/integration, Ruff, OpenAPI validation, dan local HTTP smoke test lulus.

## Deployment

### [ ] TASK-BE-010 - Containerize backend with health check

- **Depends on:** `TASK-BE-009`.
- **Goal:** menjalankan FastAPI dan artifact read-only melalui Docker.
- **Deliverables:** minimal `Dockerfile`, `docker-compose.yml`, `.dockerignore`, environment example, dan health check.
- **Acceptance:** image tidak memuat secret/raw cache yang tidak diperlukan; non-root bila praktis; artifact path configurable; container healthy.
- **Verification:** `docker compose build`, `up -d`, health request, restart test, logs check, lalu `down` lulus.

### [ ] TASK-BE-011 - Deploy backend through Cloudflare Tunnel

- **Depends on:** `TASK-BE-010`, `TASK-FE-011`.
- **Goal:** menyediakan public API HTTPS untuk frontend.
- **Deliverables:** deployment config non-secret, CORS production config, public URL environment setup, dan smoke-test report.
- **Acceptance:** health/meta/summary/ranking/detail/export dapat diakses; secret tidak masuk Git; tunnel hanya mengarah ke backend yang disetujui.
- **Verification:** source service dan public path mengembalikan version/count yang sama; error/CORS behavior diuji.

---

# TASK-FE - Next.js Frontend

## Foundation

### [x] TASK-FE-001 - Scaffold minimal Next.js application

- **Depends on:** none.
- **Goal:** menyediakan Next.js App Router dengan TypeScript strict dan Tailwind tanpa dependency UI yang belum diperlukan.
- **Deliverables:** `frontend/`, `package.json`, lockfile, lint/build config, root layout, dan smoke test.
- **Acceptance:** npm menjadi satu-satunya package manager frontend; tidak ada `any`; tidak ada auth/state manager/database client.
- **Verification:** `npm --prefix frontend run lint` dan `npm --prefix frontend run build` exit 0.

### [ ] TASK-FE-002 - Build application shell and visual foundation

- **Depends on:** `TASK-FE-001`.
- **Goal:** menetapkan navigation, typography, color tokens, content width, footer, dan disclaimer global.
- **Deliverables:** app shell, responsive navigation, CSS variables, reusable page header/disclaimer components.
- **Acceptance:** semantic layout, keyboard focus, neutral analytical colors, mobile navigation, tanpa accusatory language.
- **Verification:** component test minimum, responsive visual inspection, dan accessibility smoke check.

### [ ] TASK-FE-003 - Implement typed backend client and URL filter model

- **Depends on:** `TASK-FE-002`, `TASK-BE-003`.
- **Goal:** menyediakan satu trust boundary untuk API dan shareable state lewat URL.
- **Deliverables:** `frontend/lib/` API client, response types/validation, formatter Indonesia, URL query parser, dan tests.
- **Acceptance:** base URL dari environment; no direct fetch di presentation component; network/error/null state typed; tidak memakai Axios/React Query tanpa kebutuhan.
- **Verification:** tests untuk valid/invalid response, URL round-trip, currency/date/null formatting.

## Pages and Interactions

### [ ] TASK-FE-004 - Build landing page

- **Depends on:** `TASK-FE-002`.
- **Goal:** menjelaskan tujuan, data, cara kerja, batas klaim, dan akses ke dashboard.
- **Deliverables:** `/` dengan project overview, workflow singkat, dataset scope, dan disclaimer.
- **Acceptance:** tidak mengklaim fraud detection; 2026 disebut snapshot parsial; CTA jelas; konten ringkas dan tidak menduplikasi metodologi penuh.
- **Verification:** semantic heading/link tests, mobile/desktop inspection, no broken internal links.

### [ ] TASK-FE-005 - Build dashboard summary and charts

- **Depends on:** `TASK-FE-003`, `TASK-BE-004`.
- **Goal:** menampilkan statistik utama dan visualisasi yang tidak redundan.
- **Deliverables:** `/dashboard` summary cards, score/year/category charts yang dipilih, loading/empty/error states.
- **Acceptance:** nilai berasal dari API; label satuan dan periode jelas; 2026 ditandai parsial; satu chart library saja; chart di atas tabel full-width.
- **Verification:** API-to-UI mapping test, representative values match backend, browser console bersih.

### [ ] TASK-FE-006 - Build ranking table, combined filters, Top-N, and pagination

- **Depends on:** `TASK-FE-005`, `TASK-BE-005`.
- **Goal:** menyediakan alur utama pemilihan paket prioritas.
- **Deliverables:** full-width ranking table, URL filters, sort, pagination, Top-N control, reset, loading/empty/error states.
- **Acceptance:** score direction jelas; filter dapat digabung; URL shareable; tabel tidak ditempatkan dalam half-width grid; mobile tidak menyembunyikan package ID/score.
- **Verification:** tests filter/query/pagination/Top-N; E2E dashboard-to-page navigation; values match API.

### [ ] TASK-FE-007 - Build package-detail page

- **Depends on:** `TASK-FE-006`, `TASK-BE-006`.
- **Goal:** menjelaskan alasan prioritas tanpa menuduh kecurangan.
- **Deliverables:** `/packages/[packageId]` dengan identity, nilai, HPS/pagu, supplier, satker, jadwal, features, explanation, provenance, dan source link.
- **Acceptance:** missing data tampil `Tidak tersedia`; minimal tiga faktor untuk Top-N jika artifact tersedia; disclaimer terlihat; 404 state jelas.
- **Verification:** tests normal/missing/404; representative detail matches backend; keyboard and mobile inspection.

### [ ] TASK-FE-008 - Build dataset transparency page

- **Depends on:** `TASK-FE-003`, `TASK-BE-004`.
- **Goal:** menampilkan provenance, distribusi, kualitas, enrichment coverage, dan snapshot note.
- **Deliverables:** `/dataset` dengan source links, row counts, schema, missing/duplicate summary, coverage, dan version metadata.
- **Acceptance:** angka tidak di-hardcode jika API/artifact menyediakannya; raw limitation dijelaskan; no fake coverage.
- **Verification:** values match metadata/summary endpoint; links valid; static/revalidation behavior diuji.

### [ ] TASK-FE-009 - Build methodology and evaluation page

- **Depends on:** `TASK-FE-003`, `TASK-ML-013`.
- **Goal:** menjelaskan CRISP-DM, RAD, features, Isolation Forest, evaluation, explanation, dan batasan.
- **Deliverables:** `/methodology` dengan content terstruktur dan version references.
- **Acceptance:** tidak memakai accuracy/F1 tanpa label; Top-N bukan fraud label; SHAP hanya diklaim sesuai hasil validasi aktual.
- **Verification:** documentation consistency check terhadap report model dan PRD; internal links valid.

### [ ] TASK-FE-010 - Add CSV export and complete UI feedback states

- **Depends on:** `TASK-FE-006`, `TASK-BE-007`.
- **Goal:** mengunduh hasil aktif dan memastikan seluruh state pengguna selesai.
- **Deliverables:** export action, filename handling, retry, disabled/loading feedback, empty/error/unavailable states lintas halaman.
- **Acceptance:** export mempertahankan filter/order; double-submit dicegah; error aman; disclaimer tetap tersedia pada konteks download.
- **Verification:** E2E export memparse CSV dan membandingkan dengan tabel aktif; error simulation dan empty state lulus.

## Quality and Deployment

### [ ] TASK-FE-011 - Complete responsive, accessibility, integration, and build gates

- **Depends on:** `TASK-FE-004` sampai `TASK-FE-010`, `TASK-BE-009`.
- **Goal:** membekukan frontend P1 sebelum deployment.
- **Deliverables:** component/integration/E2E tests, accessibility fixes, responsive audit, performance report, dan final build.
- **Acceptance:** primary flow keyboard-accessible; WCAG 2.1 AA target; Chrome/Edge/Firefox current; LCP target <2,5 detik pada kondisi uji; no hydration/console errors.
- **Verification:** lint, tests, production build, Playwright primary flow, accessibility scan, dan browser console inspection lulus; dev server dihentikan.

### [ ] TASK-FE-012 - Deploy Vercel and run public end-to-end smoke tests

- **Depends on:** `TASK-FE-011`, `TASK-BE-011`.
- **Goal:** menghubungkan frontend public dengan backend public yang benar.
- **Deliverables:** Vercel deployment, production environment, deployment notes, dan smoke-test report.
- **Acceptance:** landing/dashboard/detail/dataset/methodology/export dapat diakses; API version/count sama dengan backend source; no hardcoded tunnel URL; secret tidak masuk client bundle.
- **Verification:** public E2E primary flow, representative values, CORS, CSV export, mobile viewport, and console/network checks lulus.

---

# Release Gate v1.0

Seluruh task berikut wajib `[x]` sebelum project dinyatakan siap untuk dokumentasi BAB 4:

- Semua `TASK-ML-*` P1.
- Semua `TASK-BE-*`.
- Semua `TASK-FE-*`.
- Seluruh checklist Release Acceptance Criteria pada `PRD.md` telah diverifikasi.
- Local dan public deployment menggunakan dataset/model version yang sama.
- Tidak ada secret, placeholder palsu, dummy metric, atau klaim fraud.
- README, PRD, CLAUDE, TASKS, command, screenshot, dan hasil uji konsisten dengan implementasi aktual.
