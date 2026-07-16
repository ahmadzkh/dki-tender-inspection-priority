"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = {
  primary: "#4f46e5",
  secondary: "#06b6d4",
  success: "#10b981",
  warning: "#f59e0b",
  danger: "#ef4444",
  muted: "#94a3b8",
};

// ---- Types ----------------------------------------------------------------

interface ScoreStats {
  count: number;
  min: number;
  p25: number;
  median: number;
  p75: number;
  p90: number;
  p95: number;
  max: number;
  mean: number;
  std: number;
}

interface ScoreDistribution {
  all: ScoreStats;
  train: ScoreStats;
  evaluation: ScoreStats;
}

interface SeedRow {
  variant: string;
  top_n: number;
  top_n_overlap_ratio: number;
  rank_correlation: number;
}

interface SensitivityRow {
  variant: string;
  top_n: number;
  top_n_overlap_ratio: number;
  rank_correlation: number;
}

interface OverlapEntry {
  overlap_ratio: number;
}

interface BaselineData {
  top_n_overlap: Record<string, OverlapEntry>;
  rank_correlation: number;
}

export interface EvaluationData {
  score_distribution: ScoreDistribution;
  seed_stability: SeedRow[];
  hyperparameter_sensitivity: SensitivityRow[];
  baseline_comparison: BaselineData;
  limitations: string[];
  row_count: number;
  feature_count: number;
}

export interface ModelConfig {
  model_version: string;
  train_row_count: number;
  evaluation_row_count: number;
  feature_columns: string[];
  hyperparameters: { n_estimators: number };
}

// ---- Shared UI ------------------------------------------------------------

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="glass-card p-5 rounded-2xl">
      <p className="text-xs font-medium text-surface-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-surface-900 dark:text-white">{value}</p>
      {sub && <p className="text-xs text-surface-400 mt-1">{sub}</p>}
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-xl font-bold text-surface-900 dark:text-white mb-4 mt-10 first:mt-0">
      {children}
    </h2>
  );
}

function ChartCard({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  return (
    <div className="glass-card rounded-2xl p-6">
      <h3 className="font-semibold text-surface-900 dark:text-white mb-1">{title}</h3>
      <p className="text-xs text-surface-500 mb-4">{description}</p>
      {children}
    </div>
  );
}

const tooltipStyle = { backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "12px", color: "#e2e8f0" };
type TooltipValue = number | string | readonly (number | string)[] | undefined;
const tooltipFormatter = (value: TooltipValue) => {
  if (value === undefined) return "";
  return `${Array.isArray(value) ? value.join(" - ") : value}%`;
};

// ---- Charts ---------------------------------------------------------------

function ScoreDistributionChart({ data }: { data: ScoreDistribution }) {
  const chartData = [
    { name: "Min",    train: data.train.min,    evaluation: data.evaluation.min },
    { name: "P25",    train: data.train.p25,    evaluation: data.evaluation.p25 },
    { name: "Median", train: data.train.median, evaluation: data.evaluation.median },
    { name: "P75",    train: data.train.p75,    evaluation: data.evaluation.p75 },
    { name: "P90",    train: data.train.p90,    evaluation: data.evaluation.p90 },
    { name: "P95",    train: data.train.p95,    evaluation: data.evaluation.p95 },
    { name: "Max",    train: data.train.max,    evaluation: data.evaluation.max },
  ];

  return (
    <ChartCard
      title="Distribusi Skor Anomali"
      description="Perbandingan distribusi skor antara data pelatihan (Train) dan data evaluasi (Evaluation). Distribusi yang serupa menunjukkan model stabil lintas waktu."
    >
      <ResponsiveContainer width="100%" height={320}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="gradTrain" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.3} />
              <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradEval" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={COLORS.secondary} stopOpacity={0.3} />
              <stop offset="95%" stopColor={COLORS.secondary} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
          <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 12 }} />
          <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} domain={["auto", "auto"]} />
          <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: "#f8fafc" }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Area type="monotone" dataKey="train" name="Train (2024-2025)" stroke={COLORS.primary} fill="url(#gradTrain)" strokeWidth={2} />
          <Area type="monotone" dataKey="evaluation" name="Evaluasi (2026)" stroke={COLORS.secondary} fill="url(#gradEval)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

interface ChartRow {
  name: string;
  overlap: number;
  correlation: number;
}

function StabilityBarChart({ chartData, height }: { chartData: ChartRow[]; height: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} barGap={2}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
        <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} angle={-15} textAnchor="end" height={60} />
        <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} domain={[0, 100]} unit="%" />
        <Tooltip contentStyle={tooltipStyle} formatter={tooltipFormatter} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="overlap" name="Overlap Ratio" radius={[6, 6, 0, 0]}>
          {chartData.map((entry) => (
            <Cell key={entry.name} fill={entry.overlap >= 90 ? COLORS.success : entry.overlap >= 80 ? COLORS.warning : COLORS.danger} />
          ))}
        </Bar>
        <Bar dataKey="correlation" name="Rank Correlation" fill={COLORS.primary} radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function SeedStabilityChart({ data }: { data: SeedRow[] }) {
  const chartData = data.map((row) => ({
    name: `${row.variant} (Top-${row.top_n})`,
    overlap: +(row.top_n_overlap_ratio * 100).toFixed(1),
    correlation: +(row.rank_correlation * 100).toFixed(1),
  }));

  return (
    <ChartCard
      title="Stabilitas Seed (Random State)"
      description="Mengukur seberapa konsisten daftar prioritas jika model dilatih ulang dengan seed acak berbeda. Overlap > 80% menandakan model sangat stabil."
    >
      <StabilityBarChart chartData={chartData} height={320} />
    </ChartCard>
  );
}

function SensitivityChart({ data }: { data: SensitivityRow[] }) {
  const chartData = data.map((row) => ({
    name: `${row.variant} (Top-${row.top_n})`,
    overlap: +(row.top_n_overlap_ratio * 100).toFixed(1),
    correlation: +(row.rank_correlation * 100).toFixed(1),
  }));

  return (
    <ChartCard
      title="Sensitivitas Hyperparameter"
      description="Mengukur dampak perubahan jumlah pohon (n_estimators), contamination, dan max_samples terhadap stabilitas peringkat. Overlap tinggi = model robust."
    >
      <StabilityBarChart chartData={chartData} height={400} />
    </ChartCard>
  );
}

function BaselineChart({ data }: { data: BaselineData }) {
  const items = Object.entries(data.top_n_overlap).map(([topN, overlap]) => ({
    name: `Top-${topN}`,
    overlap: +(overlap.overlap_ratio * 100).toFixed(1),
    correlation: +(data.rank_correlation * 100).toFixed(1),
  }));

  return (
    <ChartCard
      title="Perbandingan dengan Baseline (Metode Tradisional)"
      description="Isolation Forest dibandingkan dengan baseline penyortiran sederhana. Overlap rendah (< 60%) menunjukkan bahwa AI mendeteksi pola anomali yang tidak tertangkap oleh metode tradisional."
    >
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={items} layout="vertical" barGap={4}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
          <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 12 }} domain={[0, 100]} unit="%" />
          <YAxis dataKey="name" type="category" tick={{ fill: "#94a3b8", fontSize: 12 }} width={70} />
          <Tooltip contentStyle={tooltipStyle} formatter={tooltipFormatter} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="overlap" name="Overlap Ratio" fill={COLORS.warning} radius={[0, 6, 6, 0]} barSize={24} />
          <Bar dataKey="correlation" name="Rank Correlation" fill={COLORS.muted} radius={[0, 6, 6, 0]} barSize={24} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

const FEATURE_LABELS: Record<string, string> = {
  year_value: "Tahun",
  partial_snapshot_year_flag: "Tahun Snapshot Parsial",
  procurement_method_code: "Kode Metode Pengadaan",
  procurement_type_code: "Kode Jenis Pengadaan",
  log_contract_value: "Log Nilai Kontrak",
  log_hps: "Log HPS",
  log_pagu: "Log Pagu Anggaran",
  contract_to_hps_ratio: "Rasio Kontrak/HPS",
  hps_to_pagu_ratio: "Rasio HPS/Pagu",
  savings_to_hps_ratio: "Rasio Penghematan/HPS",
  pdn_to_contract_ratio: "Rasio PDN/Kontrak",
  tender_duration_days: "Durasi Tender (Hari)",
  bid_submission_duration_days: "Durasi Pengajuan Penawaran (Hari)",
  evaluation_duration_days: "Durasi Evaluasi (Hari)",
  schedule_invalid_timestamp_count: "Jumlah Timestamp Tidak Valid",
  supplier_prior_package_count_year: "Jumlah Paket Supplier (Tahun Sebelumnya)",
  supplier_prior_work_unit_package_count_year: "Jumlah Paket Supplier per Satker (Tahun Sebelumnya)",
  supplier_prior_contract_share_year: "Pangsa Kontrak Supplier (Tahun Sebelumnya)",
  supplier_prior_work_unit_contract_share_year: "Pangsa Kontrak Supplier per Satker (Tahun Sebelumnya)",
  work_unit_supplier_hhi_prior_package_count_year: "Indeks Konsentrasi Supplier (HHI) per Satker",
};

function FeatureTable({ columns }: { columns: string[] }) {
  return (
    <ChartCard
      title="20 Atribut (Feature) yang Digunakan Model"
      description="Seluruh fitur diekstrak dari data pengadaan publik DKI Jakarta. Tidak ada fitur yang berisi informasi bocoran (data leakage)."
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-200 dark:border-surface-800">
              <th className="text-left py-2 pr-4 text-surface-500 font-medium">#</th>
              <th className="text-left py-2 pr-4 text-surface-500 font-medium">Nama Teknis</th>
              <th className="text-left py-2 text-surface-500 font-medium">Deskripsi</th>
            </tr>
          </thead>
          <tbody>
            {columns.map((col, i) => (
              <tr key={col} className="border-b border-surface-100 dark:border-surface-800/50 hover:bg-surface-50 dark:hover:bg-surface-900/30 transition-colors">
                <td className="py-2 pr-4 text-surface-400 font-mono text-xs">{i + 1}</td>
                <td className="py-2 pr-4 font-mono text-xs text-primary-600 dark:text-primary-400">{col}</td>
                <td className="py-2 text-surface-600 dark:text-surface-300">{FEATURE_LABELS[col] ?? col}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </ChartCard>
  );
}

// ---- Main -----------------------------------------------------------------

export interface EvaluationChartsProps {
  evaluation: EvaluationData;
  modelConfig: ModelConfig;
}

export function EvaluationCharts({ evaluation, modelConfig }: EvaluationChartsProps) {
  const dist = evaluation.score_distribution;

  return (
    <div className="space-y-8">
      <SectionTitle>Ringkasan Model</SectionTitle>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard label="Versi Model" value={modelConfig.model_version.slice(0, 8)} sub="SHA-256 hash" />
        <StatCard label="Total Data" value={evaluation.row_count.toLocaleString("id-ID")} sub="paket tender" />
        <StatCard label="Jumlah Fitur" value={evaluation.feature_count} sub="atribut input" />
        <StatCard label="Data Latih" value={modelConfig.train_row_count.toLocaleString("id-ID")} sub="2024-2025" />
        <StatCard label="Data Evaluasi" value={modelConfig.evaluation_row_count.toLocaleString("id-ID")} sub="2026 (parsial)" />
        <StatCard label="Jumlah Pohon" value={modelConfig.hyperparameters.n_estimators} sub="n_estimators" />
      </div>

      <SectionTitle>Distribusi Skor Anomali</SectionTitle>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <StatCard label="Skor Rata-rata (Semua)" value={dist.all.mean.toFixed(4)} sub={`Std: ${dist.all.std.toFixed(4)}`} />
        <StatCard label="Skor Median (Semua)" value={dist.all.median.toFixed(4)} sub={`P95: ${dist.all.p95.toFixed(4)}`} />
        <StatCard label="Skor Maksimum" value={dist.all.max.toFixed(4)} sub="Paket paling anomali" />
      </div>
      <ScoreDistributionChart data={dist} />

      <SectionTitle>Uji Stabilitas Seed</SectionTitle>
      <SeedStabilityChart data={evaluation.seed_stability} />

      <SectionTitle>Uji Sensitivitas Hyperparameter</SectionTitle>
      <SensitivityChart data={evaluation.hyperparameter_sensitivity} />

      <SectionTitle>Perbandingan dengan Baseline</SectionTitle>
      <BaselineChart data={evaluation.baseline_comparison} />

      <SectionTitle>Atribut Model</SectionTitle>
      <FeatureTable columns={modelConfig.feature_columns} />

      <SectionTitle>Batasan Evaluasi</SectionTitle>
      <div className="glass-card rounded-2xl p-6">
        <ul className="space-y-2">
          {evaluation.limitations.map((lim) => (
            <li key={lim} className="flex items-start gap-2 text-sm text-surface-600 dark:text-surface-400">
              <span className="mt-1 h-1.5 w-1.5 rounded-full bg-warning-500 shrink-0" />
              {lim}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
