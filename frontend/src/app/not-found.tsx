import Link from "next/link";
import { SearchX } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center bg-surface-50 dark:bg-surface-950 px-4 py-24 text-center">
      <div className="w-24 h-24 bg-surface-200 dark:bg-surface-800 rounded-full flex items-center justify-center mb-8 mx-auto relative">
        <SearchX className="h-12 w-12 text-surface-500 absolute" />
      </div>

      <h1 className="text-4xl font-bold text-surface-900 dark:text-white tracking-tight mb-4">
        Halaman Tidak Ditemukan
      </h1>

      <p className="text-lg text-surface-600 dark:text-surface-400 max-w-md mx-auto mb-8 leading-relaxed">
        Maaf, rute yang Anda cari tidak tersedia atau mungkin telah dipindahkan.
      </p>

      <Link
        href="/dashboard"
        className="inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white bg-primary-600 hover:bg-primary-500 rounded-lg transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-surface-950"
      >
        Kembali ke Dashboard
      </Link>
    </div>
  );
}
