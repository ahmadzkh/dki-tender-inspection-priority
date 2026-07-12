# AGENTS.md - Project Procurement Data

## Project Root

```text
C:\Data Central\Documents\Code\julius\Skripsi\procurement_data
```

Instruksi ini berlaku untuk semua agent yang bekerja dari project root atau subfoldernya.

## Mandatory Startup

Sebelum mengerjakan task apa pun, agent WAJIB:

1. Baca `AGENTS.md`.
2. Baca `PRD.md` untuk scope, requirements, batas klaim, risiko, dan acceptance criteria.
3. Baca `CLAUDE.md` untuk tech stack, struktur, commands, coding rules, testing, dan security.
4. Baca `TASKS.md` untuk urutan task, dependency, deliverable, verification, dan status checklist.
5. Load skill `ponytail` dan terapkan YAGNI-first minimal implementation.
6. Load skill `caveman/caveman` untuk progress report singkat dan faktual.
7. Periksa `git status`, branch, recent commits, serta file yang relevan sebelum mengubah apa pun.

## Task Tracker

`TASKS.md` adalah **single source of truth** status pengembangan.

- Pilih task `[ ]` paling awal yang seluruh dependency-nya sudah `[x]`.
- Kerjakan satu task ID per perubahan logis.
- Jangan mencentang task yang baru sebagian selesai.
- Markdown tidak mencentang task secara otomatis. Agent yang menyelesaikan task wajib mengubah `[ ]` menjadi `[x]` setelah seluruh Definition of Done lulus.
- Update checkbox dilakukan dalam perubahan yang sama dengan implementasi task.
- Jangan menduplikasi checklist operasional ke `AGENTS.md`, `PRD.md`, atau `CLAUDE.md`.
- Jika implementasi mengubah scope, perbarui `PRD.md` lebih dahulu.
- Jika implementasi mengubah command, dependency, struktur, atau aturan teknis, perbarui `CLAUDE.md`.

## Mandatory Quality Gates

Untuk setiap task kode non-trivial:

1. Terapkan TDD untuk logika yang dapat diuji.
2. Jalankan test task-specific.
3. Load dan jalankan `verify-gate` untuk build/type-check, tests, lint, dan runtime/data-path verification yang relevan.
4. Load dan jalankan `software-development:requesting-code-review` sebelum task dicentang atau perubahan di-commit.
5. Reviewer harus independen dari implementer untuk task dengan perubahan kode pada dua file atau lebih.
6. Load `ponytail-review` untuk task medium/besar dan hapus over-engineering yang terbukti.
7. Gunakan `github:github-code-review` hanya ketika mereview Pull Request GitHub.
8. Perbaiki seluruh security concern, logic error, regression, dan finding blocking; ulangi gate sampai lulus.
9. Format commit tetap mengikuti project: `type: subject`, maksimal 72 karakter. Jangan memakai prefix non-conventional seperti `[verified]`.

Task dokumentasi-only tidak memerlukan full independent code review, tetapi wajib menjalani structural/link/consistency validation dan secret scan.

## Completion Rules

Agent dilarang menyatakan task selesai jika:

- deliverable belum dijalankan;
- test/build/lint relevan gagal;
- code review belum lulus;
- raw dataset berubah tanpa rencana migrasi dan verifikasi hash;
- output dibuat dari dummy/fallback yang terlihat seperti data nyata;
- dokumentasi tidak sesuai implementasi aktual;
- development server masih berjalan;
- checkbox `TASKS.md` belum diperbarui.

Commit dan push hanya dilakukan ketika diminta pengguna. Verifikasi remote setelah push sebelum melaporkan keberhasilan.

## Dataset Guardrails

- Merged input saat ini: `datasets/realisasi_dki_jakarta_2024_2026.csv` dengan 1.279 baris dan 14 kolom.
- Raw per tahun: `datasets/inaproc_realisasi_tender_dki_jakarta_{tahun}.csv`.
- Jangan menimpa atau membersihkan raw data secara in-place.
- `kode_paket` wajib diperlakukan sebagai string.
- Tahun 2026 adalah snapshot parsial per Juli 2026, bukan tahun penuh.
- Lima record supplier kosong dan paket multi-provider `10060212000` harus tetap tercatat dalam data-quality trail.
- Missing HPS/pagu bukan nol.
- Enrichment live API harus memakai timeout, retry terbatas, cache, checkpoint, dan coverage report.

## Interpretation Guardrails

- Output sistem adalah skor ketidaklaziman dan prioritas pemeriksaan.
- Jangan menyebut skor sebagai bukti fraud, korupsi, kolusi, bid-rigging, atau pelanggaran hukum.
- Jangan memakai accuracy, precision, recall, F1, atau confusion matrix sebagai evaluasi utama tanpa label tervalidasi.
- Top-N adalah kapasitas pemeriksaan, bukan label fraud.
- SHAP hanya ditampilkan jika konsistensinya terhadap anomaly score telah divalidasi.

## Approved Stack

- Python 3.11+, pandas, NumPy, scikit-learn, FastAPI, Pydantic.
- Next.js App Router, TypeScript strict, Tailwind CSS.
- `uv` untuk Python dan `npm` untuk frontend.
- Docker untuk backend, Vercel untuk frontend, Cloudflare Tunnel untuk public backend.
- Tidak ada database, auth, queue, microservices, atau global state manager pada v1.0 tanpa kebutuhan yang terbukti dan persetujuan pengguna.

## Research Method

- CRISP-DM untuk data dan Machine Learning.
- RAD untuk website.
- BAB 4 hanya ditulis setelah seluruh Release Gate v1.0 pada `TASKS.md` selesai dan output final diverifikasi.
