# AGENTS.md — Project Procurement Data

## Instruksi untuk semua agent

Sebelum mengerjakan task apa pun, agent WAJIB:

1. **Baca PRD.md** — pahami scope, fitur, dan non-fitur project.
2. **Load skill ponytail** — YAGNI-first minimal coding. Tidak boleh ada boilerplate atau abstraksi yang tidak diminta.
3. **Load skill `caveman/caveman`** — respon singkat, padat, langsung ke inti.

## Project root path

```
C:\Data Central\Documents\Code\julius\Skripsi\procurement_data
```

## Dataset

- Merged: `datasets/realisasi_dki_jakarta_2024_2026.csv` (1.279 baris, 14 kolom)
- Raw per tahun di `datasets/inaproc_realisasi_tender_dki_jakarta_{tahun}.csv`
- Enrichment HPS via API detail perlu dilakukan di awal pipeline

## Tech stack

- Python (scikit-learn, pandas, FastAPI)
- Next.js (frontend)
- Docker + Cloudflare Tunnel (deploy)

## Notes

- Isolation Forest + SHAP untuk interpretasi
- Judul skripsi: "Rancang Bangun Sistem Prioritas Pemeriksaan Realisasi Tender Pemerintah Provinsi DKI Jakarta Menggunakan Isolation Forest Berbasis Web"
- BAB 3 metode: CRISP-DM (ML) + RAD (website)
- Penulisan BAB 4 dilakukan setelah semua implementasi selesai
