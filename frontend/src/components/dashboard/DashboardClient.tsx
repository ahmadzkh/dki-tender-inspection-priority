"use client";

import type { FilterOptionsData, RankingData, SummaryData } from "@/lib/types";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Pagination } from "./Pagination";
import { FilterControls } from "./FilterControls";
import { RankingTable } from "./RankingTable";
import { DashboardCharts } from "./DashboardCharts";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/formatters";

interface DashboardClientProps {
  initialSummary: SummaryData;
  filterOptions: FilterOptionsData;
  initialRankings: RankingData;
}

export function DashboardClient({
  initialSummary,
  filterOptions,
  initialRankings,
}: DashboardClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [rankings, setRankings] = useState<RankingData>(initialRankings);
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Convert URLSearchParams to a Record
  const getFiltersFromUrl = useCallback(() => {
    const params: Record<string, string> = { top_n: "20", page: "1" };
    searchParams.forEach((value, key) => {
      params[key] = value;
    });
    return params;
  }, [searchParams]);

  const [currentFilters, setCurrentFilters] = useState<Record<string, string>>(getFiltersFromUrl());
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  // Sync state with URL when URL changes externally (e.g. back button)
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCurrentFilters(getFiltersFromUrl());
  }, [getFiltersFromUrl]);

  useEffect(
    () => () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    },
    [],
  );

  const fetchRankings = async (filters: Record<string, string>) => {
    setIsLoading(true);
    setError(null);
    try {
      // Create clean params for API
      const apiParams: Record<string, string> = {};
      for (const [k, v] of Object.entries(filters)) {
        if (v) apiParams[k] = v;
      }

      // Best Practice UI/UX:
      // If user requests a large top_n (e.g. 100, 500), we paginate by size=50 to maintain performance and avoid overwhelming UI.
      // If user requests small top_n (e.g. 10, 20, 50), we show all of them on 1 page (size=top_n).
      const topN = parseInt(filters.top_n || "20", 10);
      apiParams.size = Math.min(topN, 50).toString();

      const res = await api.getRankings(apiParams);
      setRankings(res.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Gagal memuat data ranking");
    } finally {
      setIsLoading(false);
    }
  };

  const updateUrl = (filters: Record<string, string>) => {
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(filters)) {
      if (v) params.set(k, v);
    }
    const queryString = params.toString();
    router.replace(queryString ? `/dashboard?${queryString}` : "/dashboard", { scroll: false });
  };

  const handleFilterChange = (key: string, value: string) => {
    const newFilters = { ...currentFilters, [key]: value };

    // Reset page to 1 if any filter (other than page) changes
    if (key !== 'page') {
      newFilters.page = "1";
    }

    setCurrentFilters(newFilters);
    updateUrl(newFilters);

    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      fetchRankings(newFilters);
    }, 400); // Debounce API calls slightly
  };

  const handlePageChange = (newPage: number) => {
    handleFilterChange('page', newPage.toString());
  };

  const handleReset = () => {
    const defaultFilters = { top_n: "20", page: "1" };
    setCurrentFilters(defaultFilters);
    updateUrl(defaultFilters);
    fetchRankings(defaultFilters);
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const exportFilters = { ...currentFilters };
      delete exportFilters.page;
      delete exportFilters.size;
      const url = api.getExportUrl(exportFilters);
      const res = await fetch(url);
      if (!res.ok) throw new Error("Gagal mengunduh CSV");

      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = `prioritas_pemeriksaan_${new Date().toISOString().split("T")[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch {
      setError("Terjadi kesalahan saat mengunduh CSV. Silakan coba lagi.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <>
      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="glass-card p-6 rounded-2xl">
          <p className="text-sm font-medium text-surface-500 mb-1">Total Paket</p>
          <p className="text-2xl font-bold text-surface-900 dark:text-white">
            {initialSummary.total_packages.toLocaleString("id-ID")}
          </p>
        </div>
        <div className="glass-card p-6 rounded-2xl">
          <p className="text-sm font-medium text-surface-500 mb-1">Total Supplier</p>
          <p className="text-2xl font-bold text-surface-900 dark:text-white">
            {initialSummary.unique_suppliers.toLocaleString("id-ID")}
          </p>
        </div>
        <div className="glass-card p-6 rounded-2xl">
          <p className="text-sm font-medium text-surface-500 mb-1">Total Satuan Kerja</p>
          <p className="text-2xl font-bold text-surface-900 dark:text-white">
            {initialSummary.unique_work_units.toLocaleString("id-ID")}
          </p>
        </div>
        <div className="glass-card p-6 rounded-2xl">
          <p className="text-sm font-medium text-surface-500 mb-1">Total Nilai Kontrak</p>
          <p className="text-lg font-bold text-surface-900 dark:text-white mt-2">
            {formatCurrency(initialSummary.total_contract_value)}
          </p>
        </div>
      </div>

      <DashboardCharts
        packagesByYear={initialSummary.packages_by_year}
        scoreDistribution={initialSummary.score_distribution}
      />

      <FilterControls
        options={filterOptions}
        currentFilters={currentFilters}
        onFilterChange={handleFilterChange}
        onReset={handleReset}
        onExport={handleExport}
        isLoading={isLoading}
        isExporting={isExporting}
      />

      <div className="relative">
        {error && (
          <div className="glass-card rounded-xl p-4 mb-4 text-center">
            <p className="text-sm text-surface-600 dark:text-surface-400">{error}</p>
          </div>
        )}

        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-surface-900 dark:text-white flex items-center gap-2">
            Tabel Prioritas Pemeriksaan
            {isLoading && <span className="flex h-3 w-3 rounded-full bg-primary-500 animate-ping ml-2"></span>}
          </h2>
          <span className="text-sm text-surface-500">
            Menampilkan {rankings.items.length} dari {rankings.pagination.total_items} paket
          </span>
        </div>

        <div className={`transition-opacity duration-200 ${isLoading ? 'opacity-60' : 'opacity-100'}`}>
          <RankingTable items={rankings.items} />

          {rankings.pagination && (
            <Pagination
              meta={rankings.pagination}
              onPageChange={handlePageChange}
              disabled={isLoading}
            />
          )}
        </div>
      </div>
    </>
  );
}
