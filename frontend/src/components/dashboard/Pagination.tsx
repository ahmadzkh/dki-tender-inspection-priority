import { ChevronLeft, ChevronRight } from "lucide-react";
import { PaginationMeta } from "@/lib/types";

interface PaginationProps {
  meta: PaginationMeta;
  onPageChange: (page: number) => void;
  disabled?: boolean;
}

export function Pagination({ meta, onPageChange, disabled }: PaginationProps) {
  const { page, total_pages, total_items, size, has_previous, has_next } = meta;

  if (total_pages <= 1) return null;

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between mt-6 px-6 py-4 glass-card rounded-2xl gap-4">
      <div className="text-sm text-surface-600 dark:text-surface-400 text-center sm:text-left">
        Menampilkan data <span className="font-semibold text-surface-900 dark:text-white">{((page - 1) * size) + 1}</span> hingga{" "}
        <span className="font-semibold text-surface-900 dark:text-white">{Math.min(page * size, total_items)}</span> dari{" "}
        <span className="font-semibold text-surface-900 dark:text-white">{total_items}</span> hasil
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={!has_previous || disabled}
          className="flex items-center justify-center p-2 rounded-xl border border-surface-200 dark:border-surface-800 text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Halaman Sebelumnya"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>

        <div className="px-4 py-2 text-sm font-semibold text-surface-900 dark:text-white bg-surface-50 dark:bg-surface-900/50 rounded-xl border border-surface-200 dark:border-surface-800 min-w-[100px] text-center">
          Hal {page} / {total_pages}
        </div>

        <button
          onClick={() => onPageChange(page + 1)}
          disabled={!has_next || disabled}
          className="flex items-center justify-center p-2 rounded-xl border border-surface-200 dark:border-surface-800 text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Halaman Selanjutnya"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}
