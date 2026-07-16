import { PackageDetail } from "@/lib/types";
import { formatCurrency } from "@/lib/formatters";
import { Building2, FileText, Info, Link as LinkIcon, User } from "lucide-react";
import Link from "next/link";

interface PackageDetailViewProps {
  data: PackageDetail;
}

export function PackageDetailView({ data }: PackageDetailViewProps) {
  const { source, year, is_partial_snapshot_year } = data;

  return (
    <div className="glass-card rounded-2xl p-6 lg:p-8 mb-8 shadow-sm relative overflow-hidden">
      {/* Decorative gradient */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-primary-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 pointer-events-none" />

      <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 relative z-10">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-4">
            <span className="px-3 py-1 bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300 text-xs font-semibold rounded-full uppercase tracking-wider">
              {data.procurement_type}
            </span>
            <span className="px-3 py-1 bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300 text-xs font-semibold rounded-full uppercase tracking-wider">
              {data.procurement_method}
            </span>
            <span className="px-3 py-1 bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 text-xs font-semibold rounded-full uppercase tracking-wider">
              Tahun {year} {is_partial_snapshot_year && "(Parsial)"}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-surface-900 dark:text-white leading-tight mb-4">
            {source.package_name || "Nama Paket Tidak Tersedia"}
          </h1>

          <div className="grid sm:grid-cols-2 gap-4 mb-8">
            <div className="flex items-start gap-3">
              <Building2 className="h-5 w-5 text-surface-400 mt-0.5" />
              <div>
                <p className="text-xs text-surface-500 font-medium">Satuan Kerja</p>
                <p className="text-surface-900 dark:text-surface-200 font-medium">
                  {data.work_unit || "Tidak tersedia"}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <User className="h-5 w-5 text-surface-400 mt-0.5" />
              <div>
                <p className="text-xs text-surface-500 font-medium">Pemenang / Penyedia</p>
                <p className="text-surface-900 dark:text-surface-200 font-medium">
                  {data.supplier_name || "Tidak tersedia"}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Source Link & Identity Box */}
        <div className="md:w-72 shrink-0 bg-surface-50 dark:bg-surface-900/50 p-5 rounded-xl border border-surface-200 dark:border-surface-800">
          <h3 className="text-sm font-semibold text-surface-900 dark:text-white mb-4 flex items-center gap-2">
            <FileText className="h-4 w-4 text-primary-500" />
            Identitas Paket
          </h3>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-surface-500">ID Paket:</span>
              <span className="font-mono font-medium text-surface-900 dark:text-surface-200">{data.package_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-surface-500">Sumber:</span>
              <span>LPSE DKI Jakarta</span>
            </div>

            {source.url ? (
              <Link
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 flex items-center justify-center gap-2 w-full py-2 bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 hover:border-primary-500 hover:text-primary-600 dark:hover:text-primary-400 transition-colors rounded-lg font-medium text-surface-700 dark:text-surface-300"
              >
                <LinkIcon className="h-4 w-4" />
                Buka di LPSE Asli
              </Link>
            ) : (
              <div className="mt-4 flex items-center gap-2 p-2 text-xs text-surface-500 bg-surface-100 dark:bg-surface-800 rounded-lg">
                <Info className="h-4 w-4 shrink-0" />
                URL tidak tersedia
              </div>
            )}

            {source.url && (
              <p className="text-[11px] text-surface-500 leading-tight mt-2 opacity-80">
                *Catatan: Server LPSE DKI Jakarta kerap mengalami gangguan akses (DNS error) secara publik.
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="grid sm:grid-cols-3 gap-6 pt-6 mt-6 border-t border-surface-200 dark:border-surface-800">
        <div>
          <p className="text-sm text-surface-500 font-medium mb-1">Nilai Kontrak</p>
          <p className="text-xl font-bold text-surface-900 dark:text-white">
            {formatCurrency(source.contract_value)}
          </p>
        </div>
        <div>
          <p className="text-sm text-surface-500 font-medium mb-1">HPS</p>
          <p className="text-xl font-bold text-surface-900 dark:text-white">
            {formatCurrency(source.hps)}
          </p>
        </div>
        <div>
          <p className="text-sm text-surface-500 font-medium mb-1">Pagu Anggaran</p>
          <p className="text-xl font-bold text-surface-900 dark:text-white">
            {formatCurrency(source.pagu)}
          </p>
        </div>
      </div>
    </div>
  );
}
