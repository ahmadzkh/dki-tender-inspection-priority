import { api } from "@/lib/api";
import { formatNumber } from "@/lib/formatters";
import type { DatasetMetaData } from "@/lib/types";
import { AlertTriangle, Database, ExternalLink, FileCheck2, Layers3 } from "lucide-react";

export const metadata = {
  title: "Transparansi Dataset - Dashboard Analitik Pengadaan",
};

function CountCard({ label, value, note }: { label: string; value: number; note: string }) {
  return (
    <div className="glass-card rounded-xl p-5">
      <p className="text-sm text-surface-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-surface-900 dark:text-white">
        {formatNumber(value)}
      </p>
      <p className="mt-2 text-xs leading-relaxed text-surface-500">{note}</p>
    </div>
  );
}

export default async function DatasetPage() {
  let dataset: DatasetMetaData | null = null;
  let error: string | null = null;
  try {
    dataset = (await api.getMeta()).data;
  } catch (cause: unknown) {
    error = cause instanceof Error ? cause.message : "Metadata dataset tidak tersedia.";
  }

  if (!dataset) {
    return (
      <div className="container mx-auto flex-1 px-4 py-16">
        <div className="glass-card mx-auto max-w-2xl rounded-2xl p-8 text-center">
          <AlertTriangle className="mx-auto mb-3 h-8 w-8 text-orange-500" aria-hidden="true" />
          <h1 className="text-xl font-semibold">Metadata dataset tidak dapat dimuat</h1>
          <p className="mt-2 text-sm text-surface-500">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-surface-50 py-12 dark:bg-surface-950">
      <div className="container mx-auto max-w-6xl px-4">
        <header className="mb-10">
          <h1 className="flex items-center gap-3 text-3xl font-bold tracking-tight text-surface-900 dark:text-white">
            <Database className="h-8 w-8 text-primary-500" aria-hidden="true" />
            Transparansi Dataset
          </h1>
          <p className="mt-3 max-w-3xl text-surface-600 dark:text-surface-400">
            Snapshot realisasi tender Pemerintah Provinsi DKI Jakarta periode 2024 sampai 2026. Tahun 2026 merupakan snapshot parsial, bukan satu tahun penuh.
          </p>
        </header>

        <section aria-labelledby="population-heading" className="mb-10">
          <h2 id="population-heading" className="mb-4 flex items-center gap-2 text-xl font-semibold">
            <Layers3 className="h-5 w-5 text-primary-500" aria-hidden="true" />
            Populasi per Tahap Pemrosesan
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <CountCard label="Baris sumber tahunan" value={dataset.annual_source_row_count} note="Gabungan file tahunan sebelum aturan merge dan eksklusi." />
            <CountCard label="Baris hasil merge" value={dataset.merged_row_count} note={`${formatNumber(dataset.missing_supplier_row_count)} baris tanpa penyedia dikeluarkan dari sumber tahunan.`} />
            <CountCard label="Paket canonical" value={dataset.canonical_record_count} note="Satu record per package_id setelah canonicalization." />
            <CountCard label="Layak dimodelkan" value={dataset.eligible_record_count} note={`${formatNumber(dataset.multi_provider_package_count)} paket multi-provider disimpan tetapi tidak diberi skor model.`} />
          </div>
        </section>

        <section className="mb-10 grid gap-6 lg:grid-cols-2">
          <div className="glass-card rounded-2xl p-6">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <FileCheck2 className="h-5 w-5 text-emerald-500" aria-hidden="true" />
              Enrichment INAPROC
            </h2>
            <p className="mt-4 text-3xl font-bold text-emerald-600">
              {dataset.enrichment_coverage_pct.toLocaleString("id-ID", { maximumFractionDigits: 1 })}%
            </p>
            <p className="mt-2 text-sm leading-relaxed text-surface-600 dark:text-surface-400">
              {formatNumber(dataset.enrichment_success_count)} dari {formatNumber(dataset.canonical_record_count)} paket canonical memiliki respons enrichment. Persentase ini hanya menyatakan ketersediaan field enrichment, bukan kualitas atau kelengkapan data sumber di luar snapshot.
            </p>
          </div>

          <div className="glass-card rounded-2xl p-6">
            <h2 className="text-lg font-semibold">Versi dan Integritas</h2>
            <dl className="mt-4 space-y-3 text-sm">
              <div className="flex justify-between gap-4"><dt className="text-surface-500">Dataset</dt><dd className="font-mono">{dataset.dataset_version}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-surface-500">Model</dt><dd className="font-mono">{dataset.model_version}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-surface-500">Artefak tervalidasi</dt><dd>{formatNumber(dataset.artifact_count)}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-surface-500">Manifest dibuat</dt><dd>{new Date(dataset.generated_at).toLocaleString("id-ID")}</dd></div>
            </dl>
          </div>
        </section>

        <section className="rounded-2xl border border-orange-200 bg-orange-50 p-6 dark:border-orange-900/40 dark:bg-orange-950/20">
          <h2 className="flex items-center gap-2 font-semibold text-orange-900 dark:text-orange-300">
            <AlertTriangle className="h-5 w-5" aria-hidden="true" />
            Batas Data
          </h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-orange-800 dark:text-orange-300">
            <li>Snapshot 2026 bersifat parsial sehingga tidak boleh dibandingkan sebagai total tahunan final.</li>
            <li>Enrichment 100% tidak berarti data bebas kesalahan; angka hanya mengukur field yang tersedia untuk paket eligible.</li>
            <li>Record prioritas adalah ketidaklaziman statistik, bukan label fraud atau pelanggaran hukum.</li>
          </ul>
          <a href="https://data.go.id" target="_blank" rel="noreferrer" className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-primary-700 hover:underline dark:text-primary-400">
            Portal Satu Data Indonesia <ExternalLink className="h-4 w-4" aria-hidden="true" />
          </a>
        </section>
      </div>
    </div>
  );
}
