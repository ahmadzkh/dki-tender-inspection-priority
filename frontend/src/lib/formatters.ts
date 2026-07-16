export function formatCurrency(value: number | null | undefined): string {
  if (value == null || isNaN(value)) return "Tidak tersedia";

  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null || isNaN(value)) return "Tidak tersedia";

  return new Intl.NumberFormat("id-ID").format(value);
}

export function formatScore(value: number | null | undefined): string {
  if (value == null || isNaN(value)) return "Tidak tersedia";

  return new Intl.NumberFormat("id-ID", {
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(value);
}
