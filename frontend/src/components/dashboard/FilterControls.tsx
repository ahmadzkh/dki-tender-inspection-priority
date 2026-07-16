import type { FilterOptionsData } from "@/lib/types";
import { Download, Filter, RefreshCcw } from "lucide-react";
import type { ChangeEvent } from "react";

interface FilterControlsProps {
  options: FilterOptionsData;
  currentFilters: Record<string, string>;
  onFilterChange: (key: string, value: string) => void;
  onReset: () => void;
  onExport: () => void;
  isLoading: boolean;
  isExporting: boolean;
}

const controlClass =
  "h-10 w-full rounded-lg border border-surface-200 bg-white px-3 text-sm text-surface-900 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 dark:border-surface-800 dark:bg-surface-950 dark:text-white";
const labelClass = "text-xs font-medium text-surface-600 dark:text-surface-400";

export function FilterControls({
  options,
  currentFilters,
  onFilterChange,
  onReset,
  onExport,
  isLoading,
  isExporting,
}: FilterControlsProps) {
  const handleChange = (
    event: ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => onFilterChange(event.target.name, event.target.value);

  return (
    <section className="glass-card mb-8 rounded-2xl p-6 shadow-sm" aria-labelledby="filter-heading">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 font-semibold text-surface-900 dark:text-white">
          <Filter className="h-5 w-5 text-primary-500" aria-hidden="true" />
          <h2 id="filter-heading">Filter Data</h2>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onReset}
            disabled={isLoading}
            className="flex items-center gap-2 rounded-lg bg-surface-100 px-3 py-2 text-sm font-medium text-surface-600 transition-colors hover:bg-surface-200 hover:text-surface-900 disabled:opacity-50 dark:bg-surface-800 dark:text-surface-400 dark:hover:bg-surface-700 dark:hover:text-white"
          >
            <RefreshCcw className="h-4 w-4" aria-hidden="true" />
            <span>Reset</span>
          </button>
          <button
            type="button"
            onClick={onExport}
            disabled={isExporting}
            className="flex items-center gap-2 rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-primary-500 disabled:opacity-50"
          >
            {isExporting ? (
              <RefreshCcw className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Download className="h-4 w-4" aria-hidden="true" />
            )}
            <span>{isExporting ? "Mengekspor..." : "Export CSV"}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <label className="space-y-1.5">
          <span className={labelClass}>Tahun</span>
          <select name="year" value={currentFilters.year || ""} onChange={handleChange} className={controlClass}>
            <option value="">Semua Tahun</option>
            {options.years.map((year) => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </label>

        <label className="space-y-1.5">
          <span className={labelClass}>Satuan Kerja</span>
          <input
            type="search"
            name="work_unit"
            list="work-units"
            value={currentFilters.work_unit || ""}
            onChange={handleChange}
            placeholder="Cari satuan kerja..."
            className={controlClass}
          />
          <datalist id="work-units">
            {options.work_units.map((unit) => <option key={unit} value={unit} />)}
          </datalist>
        </label>

        <label className="space-y-1.5">
          <span className={labelClass}>Penyedia</span>
          <input
            type="search"
            name="supplier_name"
            value={currentFilters.supplier_name || ""}
            onChange={handleChange}
            placeholder="Cari nama penyedia..."
            className={controlClass}
          />
        </label>

        <label className="space-y-1.5">
          <span className={labelClass}>Metode Pengadaan</span>
          <select name="procurement_method" value={currentFilters.procurement_method || ""} onChange={handleChange} className={controlClass}>
            <option value="">Semua Metode</option>
            {options.procurement_methods.map((method) => (
              <option key={method} value={method}>{method}</option>
            ))}
          </select>
        </label>

        <label className="space-y-1.5">
          <span className={labelClass}>Jenis Pengadaan</span>
          <select name="procurement_type" value={currentFilters.procurement_type || ""} onChange={handleChange} className={controlClass}>
            <option value="">Semua Jenis</option>
            {options.procurement_types.map((type) => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </label>

        <label className="space-y-1.5">
          <span className={labelClass}>Skor Minimum</span>
          <input type="number" name="min_score" min="0" max="1" step="0.01" value={currentFilters.min_score || ""} onChange={handleChange} placeholder="0.50" className={controlClass} />
        </label>

        <label className="space-y-1.5">
          <span className={labelClass}>Skor Maksimum</span>
          <input type="number" name="max_score" min="0" max="1" step="0.01" value={currentFilters.max_score || ""} onChange={handleChange} placeholder="0.70" className={controlClass} />
        </label>

        <label className="space-y-1.5">
          <span className={labelClass}>Nilai Kontrak Minimum</span>
          <input type="number" name="min_contract_value" min="0" step="1000000" value={currentFilters.min_contract_value || ""} onChange={handleChange} placeholder="1000000000" className={controlClass} />
        </label>

        <label className="space-y-1.5">
          <span className={labelClass}>Nilai Kontrak Maksimum</span>
          <input type="number" name="max_contract_value" min="0" step="1000000" value={currentFilters.max_contract_value || ""} onChange={handleChange} placeholder="5000000000" className={controlClass} />
        </label>

        <label className="space-y-1.5">
          <span className={labelClass}>Top-N Kapasitas</span>
          <select name="top_n" value={currentFilters.top_n || "20"} onChange={handleChange} className={controlClass}>
            {[10, 20, 50, 100, 500].map((value) => (
              <option key={value} value={value}>Top {value}</option>
            ))}
          </select>
        </label>
      </div>
    </section>
  );
}
