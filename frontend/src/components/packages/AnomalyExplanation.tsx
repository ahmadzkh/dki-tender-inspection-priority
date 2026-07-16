import { PackageDetail } from "@/lib/types";
import { formatScore } from "@/lib/formatters";
import { AlertCircle, Target, TrendingDown, TrendingUp } from "lucide-react";

interface AnomalyExplanationProps {
  data: PackageDetail;
}

export function AnomalyExplanation({ data }: AnomalyExplanationProps) {
  const { score, explanation, features } = data;

  const topFeatures = explanation?.factors;

  return (
    <div className="grid md:grid-cols-3 gap-6">
      {/* Score Summary */}
      <div className="md:col-span-1 glass-card rounded-2xl p-6 relative overflow-hidden bg-linear-to-br from-surface-50 to-primary-50/50 dark:from-surface-900/50 dark:to-primary-950/30">
        <h3 className="text-lg font-semibold text-surface-900 dark:text-white mb-6 flex items-center gap-2">
          <Target className="h-5 w-5 text-primary-500" />
          Indeks Anomali
        </h3>

        <div className="flex flex-col gap-4">
          <div>
            <p className="text-sm font-medium text-surface-500 dark:text-surface-400 mb-1">
              Peringkat (Rank)
            </p>
            <div className="text-4xl font-bold text-surface-900 dark:text-white">
              #{score.anomaly_rank}
            </div>
            <p className="text-xs text-surface-500 mt-1">
              Berdasarkan keseluruhan populasi
            </p>
          </div>

          <div className="h-px bg-surface-200 dark:bg-surface-800 w-full my-2" />

          <div>
            <p className="text-sm font-medium text-surface-500 dark:text-surface-400 mb-1">
              Skor Model
            </p>
            <div className="text-2xl font-mono font-medium text-primary-600 dark:text-primary-400">
              {formatScore(score.anomaly_score)}
            </div>
          </div>
        </div>
      </div>

      {/* Explanation Features */}
      <div className="md:col-span-2 glass-card rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-surface-900 dark:text-white mb-2">
          Faktor Utama (Indikator Anomali)
        </h3>
        <p className="text-sm text-surface-500 dark:text-surface-400 mb-6">
          Fitur dengan perubahan skor terbesar pada uji perturbasi lokal. Nilai ini adalah sensitivitas, bukan bukti sebab-akibat.
        </p>

        {topFeatures && topFeatures.length > 0 ? (
          <div className="space-y-4">
            {topFeatures.slice(0, 5).map((f, i) => (
              <div key={f.feature} className="bg-surface-50 dark:bg-surface-900/50 p-4 rounded-xl border border-surface-200 dark:border-surface-800 flex items-center justify-between group hover:border-primary-300 dark:hover:border-primary-700 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-surface-200 dark:bg-surface-800 text-surface-600 dark:text-surface-400 font-bold text-sm flex items-center justify-center shrink-0">
                    {i + 1}
                  </div>
                  <div>
                    <p className="font-semibold text-sm text-surface-900 dark:text-white mb-1 font-mono tracking-tight">
                      {f.feature}
                    </p>
                    <p className="text-xs text-surface-500">
                      Nilai Aktual: <span className="font-medium text-surface-700 dark:text-surface-300">
                        {f.formatted_value || (f.value !== null ? f.value : "Tidak tersedia")}
                      </span>
                    </p>
                  </div>
                </div>

                <div className="text-right">
                  <p className="text-xs font-medium text-surface-500 mb-1">Sensitivitas</p>
                  <div className="inline-flex items-center gap-1 font-medium text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-950/50 px-2 py-1 rounded text-sm">
                    {f.impact > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    {formatScore(f.absolute_impact)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-48 bg-surface-50 dark:bg-surface-900/30 rounded-xl border border-dashed border-surface-300 dark:border-surface-700 text-surface-500 text-center px-4">
            <AlertCircle className="h-8 w-8 mb-2 opacity-50" />
            <p className="font-medium">Faktor Utama Tidak Tersedia</p>
            <p className="text-sm mt-1 max-w-sm">Penjelasan model statistik tidak ditemukan untuk paket ini di dataset saat ini.</p>
          </div>
        )}
      </div>

      {/* RAW Features view (collapsible or scrollable if needed) */}
      <div className="md:col-span-3 glass-card rounded-2xl p-6 mt-4">
        <details className="group">
          <summary className="flex items-center justify-between cursor-pointer list-none">
            <h3 className="text-base font-medium text-surface-700 dark:text-surface-300">
              Lihat Seluruh Atribut Data ({Object.keys(features).length})
            </h3>
            <span className="text-primary-600 group-open:rotate-180 transition-transform">▼</span>
          </summary>
          <div className="mt-4 pt-4 border-t border-surface-200 dark:border-surface-800 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {Object.entries(features).map(([key, val]) => (
              <div key={key} className="p-3 bg-surface-50 dark:bg-surface-900/50 rounded-lg">
                <p className="text-xs text-surface-500 mb-1 truncate" title={key}>{key}</p>
                <p className="font-mono text-sm font-medium text-surface-900 dark:text-white truncate">
                  {val !== null ? val : "N/A"}
                </p>
              </div>
            ))}
          </div>
        </details>
      </div>
    </div>
  );
}
