export interface Meta {
  model_version: string;
  dataset_version: string;
  generated_at: string;
  disclaimer?: string;
  total_records?: number | null;
  filters?: Record<string, unknown> | null;
}

export interface ApiResponse<T> {
  data: T;
  meta: Meta;
  error: null;
}

export interface ScoreBin {
  range_label: string;
  count: number;
}

export interface SummaryData {
  total_packages: number;
  total_contract_value: number;
  unique_suppliers: number;
  unique_work_units: number;
  packages_by_year: Record<string, number>;
  score_distribution: ScoreBin[];
}

export interface FilterOptionsData {
  years: number[];
  work_units: string[];
  procurement_methods: string[];
  procurement_types: string[];
}

export interface RankingItem {
  package_id: string;
  year: number;
  supplier_name: string;
  work_unit: string;
  procurement_method: string;
  procurement_type: string;
  is_partial_snapshot_year: boolean;
  split: string;
  contract_value: number;
  anomaly_score: number;
  anomaly_rank: number;
}

export interface PaginationMeta {
  page: number;
  size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface RankingData {
  items: RankingItem[];
  pagination: PaginationMeta;
}

export interface SourceDetail {
  package_name: string | null;
  url: string | null;
  contract_value: number | null;
  hps: number | null;
  pagu: number | null;
}

export interface EnrichmentDetail {
  jadwal: Array<Record<string, unknown>> | null;
  metadata: Record<string, unknown> | null;
}

export interface ScoreDetail {
  anomaly_score: number;
  anomaly_rank: number;
}

export interface ExplanationFactor {
  feature: string;
  value: number | null;
  formatted_value: string;
  percentile: number | null;
  impact: number;
  absolute_impact: number;
}

export interface PackageExplanation {
  factors: ExplanationFactor[];
  rank: number;
  anomaly_score: number;
  split: string;
}

export interface PackageDetail {
  package_id: string;
  year: number;
  supplier_name: string;
  work_unit: string;
  procurement_method: string;
  procurement_type: string;
  is_partial_snapshot_year: boolean;
  source: SourceDetail;
  enrichment: EnrichmentDetail;
  features: Record<string, number>;
  score: ScoreDetail;
  explanation: PackageExplanation | null;
}

export interface DatasetMetaData {
  project_name: string;
  dataset_version: string;
  model_version: string;
  schema_version: number;
  generated_at: string;
  artifact_count: number;
  total_records: number;
  annual_source_row_count: number;
  merged_row_count: number;
  canonical_record_count: number;
  eligible_record_count: number;
  missing_supplier_row_count: number;
  multi_provider_package_count: number;
  enrichment_success_count: number;
  enrichment_coverage_pct: number;
  library_versions: Record<string, string>;
}
