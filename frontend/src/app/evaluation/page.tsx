import type { Metadata } from "next";
import { EvaluationCharts } from "@/components/evaluation/EvaluationCharts";
import type { EvaluationData, ModelConfig } from "@/components/evaluation/EvaluationCharts";
import { FlaskConical } from "lucide-react";
import { api } from "@/lib/api";

export const metadata: Metadata = {
  title: "Evaluasi Model | Prioritas Pemeriksaan Tender DKI Jakarta",
  description:
    "Hasil evaluasi model Isolation Forest: distribusi skor, stabilitas seed, sensitivitas hyperparameter, dan perbandingan baseline.",
};

export default async function EvaluationPage() {
  let data = null;
  let error: string | null = null;

  try {
    const res = await api.getEvaluation();
    data = res.data;
  } catch (err: unknown) {
    error = err instanceof Error ? err.message : "Gagal memuat data evaluasi model.";
  }

  return (
    <div className="flex-1 bg-surface-50 dark:bg-surface-950 py-12">
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-surface-900 dark:text-white tracking-tight mb-2 flex items-center gap-3">
            <FlaskConical className="h-8 w-8 text-primary-500" />
            Evaluasi Model
          </h1>
          <p className="text-surface-600 dark:text-surface-400 max-w-3xl">
            Halaman ini menyajikan bukti empiris bahwa model Isolation Forest yang digunakan
            sistem ini cukup <strong>stabil</strong>, <strong>robust</strong>, dan menghasilkan
            peringkat anomali yang konsisten. Evaluasi menggunakan metrik khusus
            <em> unsupervised learning</em> karena tidak tersedia label kepastian fraud.
          </p>
        </div>

        {error ? (
          <div className="glass-card rounded-2xl p-8 text-center">
            <p className="text-lg font-semibold text-surface-700 dark:text-surface-300 mb-2">Tidak dapat terhubung ke server</p>
            <p className="text-sm text-surface-500 dark:text-surface-400">{error}</p>
          </div>
        ) : data ? (
          <EvaluationCharts
            evaluation={data.evaluation as EvaluationData}
            modelConfig={data.model_config as ModelConfig}
          />
        ) : null}
      </div>
    </div>
  );
}
