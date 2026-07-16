const FEATURE_LABELS: Record<string, string> = {
  year_value: "Tahun anggaran",
  partial_snapshot_year_flag: "Penanda tahun berjalan parsial",
  procurement_method_code: "Metode pemilihan penyedia",
  procurement_type_code: "Jenis pengadaan",
  log_contract_value: "Besaran nilai kontrak",
  log_hps: "Besaran HPS",
  log_pagu: "Besaran pagu anggaran",
  contract_to_hps_ratio: "Kedekatan nilai kontrak terhadap HPS",
  hps_to_pagu_ratio: "Kedekatan HPS terhadap pagu",
  savings_to_hps_ratio: "Efisiensi nilai kontrak terhadap HPS",
  pdn_to_contract_ratio: "Proporsi PDN terhadap nilai kontrak",
  tender_duration_days: "Durasi keseluruhan tender",
  bid_submission_duration_days: "Durasi pemasukan penawaran",
  evaluation_duration_days: "Durasi evaluasi penawaran",
  schedule_invalid_timestamp_count: "Kelengkapan dan validitas jadwal",
  supplier_prior_package_count_year: "Riwayat kemenangan penyedia pada tahun yang sama",
  supplier_prior_work_unit_package_count_year: "Riwayat penyedia pada satuan kerja yang sama",
  supplier_prior_contract_share_year: "Porsi nilai kontrak penyedia pada tahun yang sama",
  supplier_prior_work_unit_contract_share_year: "Porsi nilai kontrak penyedia di satuan kerja terkait",
  work_unit_supplier_hhi_prior_package_count_year: "Konsentrasi penyedia pada satuan kerja",
};

export function getFeatureLabel(feature: string): string {
  return FEATURE_LABELS[feature] ?? feature;
}
