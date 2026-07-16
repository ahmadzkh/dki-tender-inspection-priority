import type {
  ApiResponse,
  DatasetMetaData,
  FilterOptionsData,
  PackageDetail,
  RankingData,
  SummaryData,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type Query = Record<string, string | number | undefined>;
type Validator<T> = (value: unknown) => value is T;

class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

const isSummary: Validator<SummaryData> = (value): value is SummaryData =>
  isRecord(value) &&
  isNumber(value.total_packages) &&
  isNumber(value.total_contract_value) &&
  isNumber(value.unique_suppliers) &&
  isNumber(value.unique_work_units) &&
  isRecord(value.packages_by_year) &&
  Array.isArray(value.score_distribution);

const isFilters: Validator<FilterOptionsData> = (
  value,
): value is FilterOptionsData =>
  isRecord(value) &&
  Array.isArray(value.years) &&
  Array.isArray(value.work_units) &&
  Array.isArray(value.procurement_methods) &&
  Array.isArray(value.procurement_types);

const isRanking: Validator<RankingData> = (value): value is RankingData =>
  isRecord(value) &&
  Array.isArray(value.items) &&
  value.items.every(
    (item) =>
      isRecord(item) &&
      typeof item.package_id === "string" &&
      isNumber(item.contract_value) &&
      isNumber(item.anomaly_score) &&
      isNumber(item.anomaly_rank),
  ) &&
  isRecord(value.pagination) &&
  isNumber(value.pagination.total_items) &&
  isNumber(value.pagination.total_pages);

const isPackageDetail: Validator<PackageDetail> = (
  value,
): value is PackageDetail =>
  isRecord(value) &&
  typeof value.package_id === "string" &&
  isRecord(value.source) &&
  isRecord(value.score) &&
  isNumber(value.score.anomaly_score) &&
  isNumber(value.score.anomaly_rank);

const isDatasetMeta: Validator<DatasetMetaData> = (
  value,
): value is DatasetMetaData =>
  isRecord(value) &&
  typeof value.dataset_version === "string" &&
  typeof value.model_version === "string" &&
  isNumber(value.annual_source_row_count) &&
  isNumber(value.merged_row_count) &&
  isNumber(value.canonical_record_count) &&
  isNumber(value.eligible_record_count) &&
  isNumber(value.enrichment_coverage_pct);

const isObject: Validator<Record<string, unknown>> = (
  value,
): value is Record<string, unknown> => isRecord(value);

function toQueryString(query?: Query): string {
  if (!query) return "";
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== "") params.set(key, String(value));
  }
  const encoded = params.toString();
  return encoded ? `?${encoded}` : "";
}

function assertEnvelope<T>(
  payload: unknown,
  validator: Validator<T>,
): asserts payload is ApiResponse<T> {
  if (
    !isRecord(payload) ||
    !validator(payload.data) ||
    !isRecord(payload.meta) ||
    typeof payload.meta.model_version !== "string" ||
    typeof payload.meta.dataset_version !== "string" ||
    typeof payload.meta.generated_at !== "string" ||
    payload.error !== null
  ) {
    throw new Error("Respons API tidak sesuai kontrak yang dibekukan.");
  }
}

async function fetchApi<T>(
  path: string,
  validator: Validator<T>,
  query?: Query,
): Promise<ApiResponse<T>> {
  const response = await fetch(`${API_BASE_URL}${path}${toQueryString(query)}`, {
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new ApiRequestError(
      `API request failed with status ${response.status}`,
      response.status,
    );
  }
  const payload: unknown = await response.json();
  assertEnvelope(payload, validator);
  return payload;
}

export function getSummary() {
  return fetchApi("/summary", isSummary);
}

export function getFilterOptions() {
  return fetchApi("/filters", isFilters);
}

export function getRankings(query?: Query) {
  return fetchApi("/rankings", isRanking, query);
}

export function getPackage(packageId: string) {
  return fetchApi(`/packages/${encodeURIComponent(packageId)}`, isPackageDetail);
}

export function getMeta() {
  return fetchApi("/meta", isDatasetMeta);
}

export function getEvaluation() {
  return fetchApi("/evaluation", isObject);
}

export function getExportUrl(query?: Query): string {
  return `${API_BASE_URL}/export.csv${toQueryString(query)}`;
}

export const api = {
  getSummary,
  getFilters: getFilterOptions,
  getRankings,
  getPackage,
  getMeta,
  getEvaluation,
  getExportUrl,
};
