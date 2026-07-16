import type { FilterOptionsData, RankingData, SummaryData } from "@/lib/types";
import { DashboardClient } from "@/components/dashboard/DashboardClient";
import { api } from "@/lib/api";

type SearchParams = Promise<{ [key: string]: string | string[] | undefined }>;

export default async function DashboardPage(props: { searchParams: SearchParams }) {
  const searchParams = await props.searchParams;

  const queryParams: Record<string, string> = { top_n: "20", page: "1" };
  for (const key in searchParams) {
    if (searchParams[key]) {
      queryParams[key] = String(searchParams[key]);
    }
  }

  const topN = parseInt(queryParams.top_n || "20", 10);
  queryParams.size = Math.min(topN, 50).toString();

  let summary: SummaryData | null = null;
  let filters: FilterOptionsData | null = null;
  let rankings: RankingData | null = null;
  let error: string | null = null;

  try {
    const [summaryRes, filterRes, rankingRes] = await Promise.all([
      api.getSummary(),
      api.getFilters(),
      api.getRankings(queryParams)
    ]);

    summary = summaryRes.data;
    filters = filterRes.data;
    rankings = rankingRes.data;
  } catch (err: unknown) {
    error = err instanceof Error ? err.message : "Gagal memuat data dari server.";
  }

  return (
    <div className="flex-1 bg-surface-50 dark:bg-surface-950 py-12">
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-surface-900 dark:text-white tracking-tight mb-2">
            Dashboard Analitik
          </h1>
          <p className="text-surface-600 dark:text-surface-400">
            Daftar prioritas pemeriksaan tender berdasarkan anomali statistik.
          </p>
        </div>

        {error || !summary || !filters || !rankings ? (
          <div className="glass-card rounded-2xl p-8 text-center">
            <p className="text-lg font-semibold text-surface-700 dark:text-surface-300 mb-2">Tidak dapat terhubung ke server</p>
            <p className="text-sm text-surface-500 dark:text-surface-400">
              {error || "Server backend sedang tidak aktif. Pastikan server berjalan di port 8000, lalu muat ulang halaman ini."}
            </p>
          </div>
        ) : (
          <DashboardClient
            initialSummary={summary}
            filterOptions={filters}
            initialRankings={rankings}
          />
        )}
      </div>
    </div>
  );
}
