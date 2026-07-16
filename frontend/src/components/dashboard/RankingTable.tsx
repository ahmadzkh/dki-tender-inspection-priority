import Link from "next/link";
import { ArrowUpRight, SearchX } from "lucide-react";
import { RankingItem } from "@/lib/types";
import { formatCurrency, formatScore } from "@/lib/formatters";

interface RankingTableProps {
  items: RankingItem[];
}

export function RankingTable({ items }: RankingTableProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center glass-card rounded-2xl">
        <div className="bg-surface-100 dark:bg-surface-800 p-4 rounded-full mb-4">
          <SearchX className="h-8 w-8 text-surface-400" />
        </div>
        <h3 className="text-lg font-medium text-surface-900 dark:text-white mb-2">Tidak ada data ditemukan</h3>
        <p className="text-surface-500 max-w-sm">
          Cobalah menyesuaikan filter pencarian Anda untuk melihat hasil.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto glass-card rounded-2xl">
      <table className="w-full text-left text-sm whitespace-nowrap">
        <thead className="bg-surface-50/50 dark:bg-surface-900/50 text-surface-500 dark:text-surface-400 uppercase text-xs font-semibold tracking-wider">
          <tr>
            <th className="px-6 py-4 rounded-tl-2xl">Rank</th>
            <th className="px-6 py-4">Tahun</th>
            <th className="px-6 py-4">Satuan Kerja</th>
            <th className="px-6 py-4">Penyedia</th>
            <th className="px-6 py-4 text-right">Nilai Kontrak</th>
            <th className="px-6 py-4 text-right">Skor Anomali</th>
            <th className="px-6 py-4 text-center rounded-tr-2xl">Aksi</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-surface-200/50 dark:divide-surface-800/50">
          {items.map((item) => (
            <tr
              key={item.package_id}
              className="group hover:bg-white/50 dark:hover:bg-surface-800/30 transition-colors"
            >
              <td className="px-6 py-4">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 font-bold text-xs">
                  #{item.anomaly_rank}
                </span>
              </td>
              <td className="px-6 py-4 text-surface-600 dark:text-surface-300">
                {item.year}
                {item.is_partial_snapshot_year && <span className="text-orange-500 ml-1" title="Data parsial">*</span>}
              </td>
              <td className="px-6 py-4 text-surface-900 dark:text-white font-medium max-w-xs truncate" title={item.work_unit}>
                {item.work_unit || "-"}
              </td>
              <td className="px-6 py-4 text-surface-600 dark:text-surface-300 max-w-xs truncate" title={item.supplier_name}>
                {item.supplier_name || "-"}
              </td>
              <td className="px-6 py-4 text-right text-surface-600 dark:text-surface-300">
                {formatCurrency(item.contract_value)}
              </td>
              <td className="px-6 py-4 text-right font-mono text-primary-600 dark:text-primary-400 font-medium">
                {formatScore(item.anomaly_score)}
              </td>
              <td className="px-6 py-4 text-center">
                <Link
                  href={`/packages/${item.package_id}`}
                  className="inline-flex items-center justify-center p-2 text-surface-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-all opacity-0 group-hover:opacity-100 focus:opacity-100"
                  aria-label={`Lihat detail paket ${item.package_id}`}
                  title="Lihat Detail"
                >
                  <ArrowUpRight className="h-4 w-4" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
