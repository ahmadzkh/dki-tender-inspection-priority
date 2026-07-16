import Link from "next/link";
import { AlertCircle } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full bg-surface-50 dark:bg-surface-950 border-t border-surface-200 dark:border-surface-800 mt-auto">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:justify-between">
          <div className="max-w-xl space-y-4">
            <div className="flex items-center gap-2 text-primary-600 dark:text-primary-400 font-semibold">
              <AlertCircle className="h-5 w-5" />
              <span>Batas Interpretasi & Penafian (Disclaimer)</span>
            </div>
            <p className="text-sm text-surface-600 dark:text-surface-400 leading-relaxed">
              Sistem ini murni berbasis analisis statistik anomali pada fitur-fitur yang dirancang secara mandiri.
              Skor kejanggalan yang tinggi <strong>hanya</strong> merepresentasikan prioritas pemeriksaan,
              <strong>bukan</strong> vonis hukum, korupsi, fraud, atau bentuk kecurangan lainnya.
            </p>
          </div>

          <div className="flex flex-col gap-2 text-sm text-surface-500 dark:text-surface-400">
            <p className="font-medium text-surface-700 dark:text-surface-300">Tautan Terkait</p>
            <Link href="https://lpse.jakarta.go.id/eproc4" target="_blank" rel="noopener noreferrer" className="hover:text-primary-600 transition-colors">
              LPSE DKI Jakarta
            </Link>
            <Link href="https://inaproc.id/cari-paket" target="_blank" rel="noopener noreferrer" className="hover:text-primary-600 transition-colors">
              INAPROC
            </Link>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-surface-200 dark:border-surface-800 text-xs text-center text-surface-500 dark:text-surface-500">
          <p>&copy; {new Date().getFullYear()} Riset Skripsi - Sistem Prioritas Pemeriksaan Realisasi Tender DKI Jakarta</p>
        </div>
      </div>
    </footer>
  );
}
