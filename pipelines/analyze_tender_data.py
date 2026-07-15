from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.build_canonical_dataset import CANONICAL_COLUMNS  # noqa: E402

DEFAULT_CANONICAL_CSV = Path("datasets/processed/tenders_canonical.csv")
DEFAULT_OUTPUT_DIR = Path("reports/eda")
PARTIAL_SNAPSHOT_YEARS = {"2026"}
NUMERIC_FIELDS = ("contract_value", "pdn_value", "hps", "pagu")
RATIO_FIELDS = (
    "contract_to_hps_ratio",
    "hps_to_pagu_ratio",
    "savings_to_hps_ratio",
    "pdn_to_contract_ratio",
)
CATEGORY_FIELDS = ("year", "procurement_method", "procurement_type")
MISSINGNESS_FIELDS = (
    ("contract_value", None),
    ("pdn_value", None),
    ("hps", "hps_available"),
    ("pagu", "pagu_available"),
    ("metode_evaluasi", "metode_evaluasi_available"),
    ("metadata", "metadata_available"),
    ("jadwal", "jadwal_available"),
    ("supplier_name", None),
    ("work_unit", None),
)


def _relative_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _round(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return round(number, 6)


def _number_series(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column].replace("", pd.NA), errors="coerce")


def _safe_share(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return _round(numerator / denominator)


def _read_canonical(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False)
    if list(frame.columns) != CANONICAL_COLUMNS:
        raise ValueError(f"{path}: schema mismatch; expected canonical dataset columns")
    blank_ids = int(frame["package_id"].astype(str).str.strip().eq("").sum())
    if blank_ids:
        raise ValueError(f"{path}: package_id contains {blank_ids} blank value(s)")
    duplicate_count = int(frame["package_id"].duplicated().sum())
    if duplicate_count:
        raise ValueError(
            f"{path}: package_id must be unique; found {duplicate_count} duplicate row(s)"
        )
    bad_identifier_cast = frame["package_id"].str.endswith(".0") | frame["rup_code"].str.endswith(
        ".0"
    )
    if bool(bad_identifier_cast.any()):
        raise ValueError(f"{path}: identifier appears to have been coerced to numeric text")
    return frame


def _prepare_frame(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()
    for column in NUMERIC_FIELDS:
        prepared[f"_{column}"] = _number_series(prepared, column)
    prepared["_contract_to_hps_ratio"] = prepared["_contract_value"] / prepared["_hps"]
    prepared["_hps_to_pagu_ratio"] = prepared["_hps"] / prepared["_pagu"]
    prepared["_savings_to_hps_ratio"] = (prepared["_hps"] - prepared["_contract_value"]) / prepared[
        "_hps"
    ]
    prepared["_pdn_to_contract_ratio"] = prepared["_pdn_value"] / prepared["_contract_value"]
    for column in RATIO_FIELDS:
        prepared.loc[~prepared[f"_{column}"].map(math.isfinite), f"_{column}"] = pd.NA
    return prepared


def _series_stats(series: pd.Series) -> dict[str, Any]:
    values = series.dropna().astype(float)
    if values.empty:
        return {
            "count": 0,
            "missing_count": int(series.isna().sum()),
            "min": None,
            "p25": None,
            "median": None,
            "p75": None,
            "max": None,
            "mean": None,
        }
    return {
        "count": int(values.count()),
        "missing_count": int(series.isna().sum()),
        "min": _round(values.min()),
        "p25": _round(values.quantile(0.25)),
        "median": _round(values.median()),
        "p75": _round(values.quantile(0.75)),
        "max": _round(values.max()),
        "mean": _round(values.mean()),
    }


def _missingness(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    total = len(frame)
    result: dict[str, dict[str, Any]] = {}
    for field, availability_field in MISSINGNESS_FIELDS:
        if availability_field:
            missing_mask = frame[availability_field].str.lower().ne("true")
        else:
            missing_mask = frame[field].astype(str).str.strip().eq("")
        missing_count = int(missing_mask.sum())
        result[field] = {
            "missing_count": missing_count,
            "available_count": total - missing_count,
            "missing_pct": _safe_share(missing_count, total),
        }
    return result


def _value_summary(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    summary = {field: _series_stats(frame[f"_{field}"]) for field in NUMERIC_FIELDS}
    for field in RATIO_FIELDS:
        summary[field] = _series_stats(frame[f"_{field}"])
    return summary


def _iqr_outliers(frame: pd.DataFrame, numeric_column: str) -> dict[str, Any]:
    values = frame[f"_{numeric_column}"].dropna().astype(float)
    if len(values) < 4:
        return {
            "count": int(values.count()),
            "q1": None,
            "q3": None,
            "iqr": None,
            "lower_bound": None,
            "upper_bound": None,
            "lower_outlier_count": 0,
            "upper_outlier_count": 0,
            "top_upper_outliers": [],
        }
    q1 = float(values.quantile(0.25))
    q3 = float(values.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    lower_mask = frame[f"_{numeric_column}"] < lower
    upper_mask = frame[f"_{numeric_column}"] > upper
    top_upper = (
        frame.loc[upper_mask, ["package_id", "year", "work_unit", f"_{numeric_column}"]]
        .sort_values([f"_{numeric_column}", "package_id"], ascending=[False, True])
        .head(10)
    )
    top_upper_records = [
        {
            "package_id": str(row["package_id"]),
            "year": str(row["year"]),
            "work_unit": str(row["work_unit"]),
            "value": _round(row[f"_{numeric_column}"]),
        }
        for row in top_upper.to_dict("records")
    ]
    return {
        "count": int(values.count()),
        "q1": _round(q1),
        "q3": _round(q3),
        "iqr": _round(iqr),
        "lower_bound": _round(lower),
        "upper_bound": _round(upper),
        "lower_outlier_count": int(lower_mask.sum()),
        "upper_outlier_count": int(upper_mask.sum()),
        "top_upper_outliers": top_upper_records,
    }


def _category_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    total = len(frame)
    for field in CATEGORY_FIELDS:
        counts = frame[field].replace("", pd.NA).dropna().value_counts()
        for value, count in counts.items():
            rows.append(
                {
                    "field": field,
                    "value": str(value),
                    "count": int(count),
                    "share": _safe_share(float(count), total),
                }
            )
    return sorted(rows, key=lambda row: (row["field"], -row["count"], row["value"]))


def _year_summary(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for year, group in frame.groupby("year", sort=True):
        eligible = group[group["eligible_for_model"].str.lower().eq("true")]
        result[str(year)] = {
            "package_count": int(len(group)),
            "eligible_for_model_count": int(len(eligible)),
            "total_contract_value": _round(eligible["_contract_value"].sum()),
            "median_contract_value": _round(eligible["_contract_value"].median()),
            "supplier_count": int(
                eligible["supplier_name"].replace("", pd.NA).nunique(dropna=True)
            ),
            "work_unit_count": int(eligible["work_unit"].replace("", pd.NA).nunique(dropna=True)),
            "is_partial_snapshot": str(year) in PARTIAL_SNAPSHOT_YEARS,
        }
    return result


def _hhi(values: pd.Series) -> float | None:
    total = float(values.sum())
    if total <= 0:
        return None
    return _round(float(((values / total) ** 2).sum()))


def _supplier_concentration_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    grouped = frame[frame["supplier_name"].str.strip().ne("")].groupby("supplier_name", sort=True)
    total_packages = len(frame)
    total_value = float(frame["_contract_value"].sum())
    rows = []
    for supplier, group in grouped:
        package_count = int(len(group))
        total_contract_value = float(group["_contract_value"].sum())
        rows.append(
            {
                "supplier_name": str(supplier),
                "package_count": package_count,
                "package_share": _safe_share(package_count, total_packages),
                "total_contract_value": _round(total_contract_value),
                "value_share": _safe_share(total_contract_value, total_value),
                "work_unit_count": int(group["work_unit"].nunique()),
                "year_count": int(group["year"].nunique()),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            -row["package_count"],
            -(row["total_contract_value"] or 0),
            row["supplier_name"],
        ),
    )


def _work_unit_concentration_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for work_unit, group in frame.groupby("work_unit", sort=True):
        supplier_counts = group.groupby("supplier_name").size()
        supplier_values = group.groupby("supplier_name")["_contract_value"].sum()
        total_contract_value = float(group["_contract_value"].sum())
        rows.append(
            {
                "work_unit": str(work_unit),
                "package_count": int(len(group)),
                "supplier_count": int(
                    group["supplier_name"].replace("", pd.NA).nunique(dropna=True)
                ),
                "total_contract_value": _round(total_contract_value),
                "hhi_supplier_package_count": _hhi(supplier_counts.astype(float)),
                "hhi_supplier_value": _hhi(supplier_values.astype(float)),
            }
        )
    return sorted(rows, key=lambda row: (-row["package_count"], row["work_unit"]))


def _concentration_summary(frame: pd.DataFrame) -> dict[str, Any]:
    supplier_counts = (
        frame[frame["supplier_name"].str.strip().ne("")].groupby("supplier_name").size()
    )
    supplier_values = (
        frame[frame["supplier_name"].str.strip().ne("")]
        .groupby("supplier_name")["_contract_value"]
        .sum()
    )
    return {
        "supplier_count": int(supplier_counts.count()),
        "work_unit_count": int(frame["work_unit"].replace("", pd.NA).nunique(dropna=True)),
        "supplier_hhi_by_package_count": _hhi(supplier_counts.astype(float)),
        "supplier_hhi_by_contract_value": _hhi(supplier_values.astype(float)),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _value_summary_rows(summary: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"field": field, **values} for field, values in summary.items()]


def _missingness_rows(summary: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"field": field, **values} for field, values in summary.items()]


def _year_rows(summary: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"year": year, **values} for year, values in summary.items()]


def _outlier_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "field": field,
            **{key: value for key, value in values.items() if key != "top_upper_outliers"},
        }
        for field, values in summary.items()
    ]


def _svg_bar_chart(path: Path, title: str, items: list[tuple[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width = 900
    bar_height = 24
    gap = 10
    left = 260
    top = 54
    height = max(160, top + len(items) * (bar_height + gap) + 40)
    max_value = max((value for _, value in items), default=1) or 1
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        'viewBox="0 0 900 {height}" role="img">'.replace("{height}", str(height)),
        f"<title>{html.escape(title)}</title>",
        '<rect width="100%" height="100%" fill="#0f172a"/>',
        f'<text x="24" y="32" fill="#e2e8f0" font-family="Arial" font-size="20">'
        f"{html.escape(title)}</text>",
    ]
    for index, (label, value) in enumerate(items):
        y = top + index * (bar_height + gap)
        bar_width = int((value / max_value) * (width - left - 80)) if max_value else 0
        lines.extend(
            [
                f'<text x="24" y="{y + 17}" fill="#cbd5e1" font-family="Arial" '
                f'font-size="13">{html.escape(label[:34])}</text>',
                f'<rect x="{left}" y="{y}" width="{bar_width}" height="{bar_height}" '
                'fill="#38bdf8"/>',
                f'<text x="{left + bar_width + 8}" y="{y + 17}" fill="#e2e8f0" '
                f'font-family="Arial" font-size="13">{value:,.0f}</text>',
            ]
        )
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _histogram_items(values: pd.Series, bins: int = 8) -> list[tuple[str, float]]:
    positive = values.dropna().astype(float)
    positive = positive[positive > 0]
    if positive.empty:
        return []
    logs = positive.map(math.log10)
    min_log = float(logs.min())
    max_log = float(logs.max())
    if math.isclose(min_log, max_log):
        return [(f"10^{min_log:.1f}", float(len(positive)))]
    step = (max_log - min_log) / bins
    items: list[tuple[str, float]] = []
    for index in range(bins):
        start = min_log + index * step
        end = min_log + (index + 1) * step
        if index == bins - 1:
            mask = logs.between(start, end, inclusive="both")
        else:
            mask = (logs >= start) & (logs < end)
        count = int(mask.sum())
        if count:
            items.append((f"10^{start:.1f}–10^{end:.1f}", float(count)))
    return items


def _write_figures(
    output_dir: Path, frame: pd.DataFrame, supplier_rows: list[dict[str, Any]]
) -> None:
    _svg_bar_chart(
        output_dir / "figures" / "contract_value_distribution.svg",
        "Distribusi log nilai kontrak",
        _histogram_items(frame["_contract_value"]),
    )
    top_suppliers = [
        (row["supplier_name"], float(row["package_count"])) for row in supplier_rows[:10]
    ]
    _svg_bar_chart(
        output_dir / "figures" / "supplier_concentration_top10.svg",
        "Top penyedia berdasarkan jumlah paket",
        top_suppliers,
    )


def _write_markdown(path: Path, summary: dict[str, Any]) -> None:
    dataset = summary["dataset"]
    value_summary = summary["value_summary"]
    concentration = summary["concentration"]
    lines = [
        "# Exploratory Data Analysis Tender DKI Jakarta",
        "",
        "This report is generated by `pipelines/analyze_tender_data.py`. Do not edit manually.",
        "",
        "## Dataset version",
        "",
        f"- Source: `{dataset['canonical_csv']}`",
        f"- SHA-256: `{dataset['canonical_csv_sha256']}`",
        f"- Row count: {dataset['row_count']} canonical rows",
        f"- Unique package IDs: {dataset['unique_package_count']}",
        f"- Eligible for model: {dataset['eligible_for_model_count']}",
        f"- Multi-provider not eligible: {dataset['multi_provider_count']}",
        "",
        "## Key findings",
        "",
        "- 2026 adalah snapshot parsial, sehingga perbandingan tahunan harus diberi label "
        "dan tidak boleh dianggap setara dengan tahun penuh.",
        "- Nilai HPS, pagu, dan kontrak dipakai untuk memahami distribusi dan calon fitur; "
        "hasil EDA bukan label fraud atau bukti pelanggaran.",
        "- Konsentrasi penyedia dan satuan kerja menjadi sinyal awal untuk feature engineering, "
        "bukan kesimpulan audit.",
        "",
        "## Value summary",
        "",
        "Value statistics use rows with `eligible_for_model=true`; missingness uses all "
        "canonical rows.",
        "",
        "| Field | Count | Missing | Min | Median | Max | Mean |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for field in (*NUMERIC_FIELDS, *RATIO_FIELDS):
        stats = value_summary[field]
        lines.append(
            f"| `{field}` | {stats['count']} | {stats['missing_count']} | "
            f"{stats['min']} | {stats['median']} | {stats['max']} | {stats['mean']} |"
        )
    lines.extend(
        [
            "",
            "## Missingness",
            "",
            "| Field | Missing | Available | Missing % |",
            "|---|---:|---:|---:|",
        ]
    )
    for field, item in summary["missingness"].items():
        lines.append(
            f"| `{field}` | {item['missing_count']} | {item['available_count']} | "
            f"{item['missing_pct']} |"
        )
    lines.extend(
        [
            "",
            "## Concentration",
            "",
            f"- Supplier count: {concentration['supplier_count']}",
            f"- Work-unit count: {concentration['work_unit_count']}",
            f"- Supplier HHI by package count: {concentration['supplier_hhi_by_package_count']}",
            f"- Supplier HHI by contract value: {concentration['supplier_hhi_by_contract_value']}",
            "",
            "## Output tables and figures",
            "",
            "- `tables/value_summary.csv`",
            "- `tables/missingness.csv`",
            "- `tables/year_summary.csv`",
            "- `tables/category_summary.csv`",
            "- `tables/supplier_concentration.csv`",
            "- `tables/work_unit_concentration.csv`",
            "- `tables/outlier_summary.csv`",
            "- `figures/contract_value_distribution.svg`",
            "- `figures/supplier_concentration_top10.svg`",
            "",
            "## Feature implications",
            "",
            "1. Financial ratios are supported where denominator values are positive "
            "and available.",
            "2. Temporal features must preserve the 2026 partial-snapshot flag.",
            "3. Supplier/work-unit concentration features need leakage-safe temporal windows in "
            "the next task.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze_tender_data(
    canonical_csv: Path = DEFAULT_CANONICAL_CSV,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    project_root: Path | None = None,
) -> dict[str, Any]:
    project_root = (project_root or Path.cwd()).resolve()
    canonical_csv = canonical_csv if canonical_csv.is_absolute() else project_root / canonical_csv
    output_dir = output_dir if output_dir.is_absolute() else project_root / output_dir

    frame = _prepare_frame(_read_canonical(canonical_csv))
    eligible = frame[frame["eligible_for_model"].str.lower().eq("true")].copy()
    value_summary = _value_summary(eligible)
    missingness = _missingness(frame)
    year_summary = _year_summary(frame)
    supplier_rows = _supplier_concentration_rows(eligible)
    work_unit_rows = _work_unit_concentration_rows(eligible)
    category_rows = _category_rows(frame)
    outliers = {field: _iqr_outliers(eligible, field) for field in (*NUMERIC_FIELDS, *RATIO_FIELDS)}

    summary = {
        "schema_version": 1,
        "dataset": {
            "canonical_csv": _relative_path(canonical_csv, project_root),
            "canonical_csv_sha256": _sha256(canonical_csv),
            "row_count": int(len(frame)),
            "unique_package_count": int(frame["package_id"].nunique()),
            "eligible_for_model_count": int(len(eligible)),
            "multi_provider_count": int(frame["is_multi_provider"].str.lower().eq("true").sum()),
            "partial_snapshot_years": sorted(PARTIAL_SNAPSHOT_YEARS),
        },
        "missingness": missingness,
        "value_summary": value_summary,
        "year_summary": year_summary,
        "outliers": outliers,
        "concentration": _concentration_summary(eligible),
    }

    table_dir = output_dir / "tables"
    _write_rows(
        table_dir / "value_summary.csv",
        _value_summary_rows(value_summary),
        ["field", "count", "missing_count", "min", "p25", "median", "p75", "max", "mean"],
    )
    _write_rows(
        table_dir / "missingness.csv",
        _missingness_rows(missingness),
        ["field", "missing_count", "available_count", "missing_pct"],
    )
    _write_rows(
        table_dir / "year_summary.csv",
        _year_rows(year_summary),
        [
            "year",
            "package_count",
            "eligible_for_model_count",
            "total_contract_value",
            "median_contract_value",
            "supplier_count",
            "work_unit_count",
            "is_partial_snapshot",
        ],
    )
    _write_rows(
        table_dir / "category_summary.csv",
        category_rows,
        ["field", "value", "count", "share"],
    )
    _write_rows(
        table_dir / "supplier_concentration.csv",
        supplier_rows,
        [
            "supplier_name",
            "package_count",
            "package_share",
            "total_contract_value",
            "value_share",
            "work_unit_count",
            "year_count",
        ],
    )
    _write_rows(
        table_dir / "work_unit_concentration.csv",
        work_unit_rows,
        [
            "work_unit",
            "package_count",
            "supplier_count",
            "total_contract_value",
            "hhi_supplier_package_count",
            "hhi_supplier_value",
        ],
    )
    _write_rows(
        table_dir / "outlier_summary.csv",
        _outlier_rows(outliers),
        [
            "field",
            "count",
            "q1",
            "q3",
            "iqr",
            "lower_bound",
            "upper_bound",
            "lower_outlier_count",
            "upper_outlier_count",
        ],
    )
    _write_figures(output_dir, eligible, supplier_rows)
    _write_json(output_dir / "summary.json", summary)
    _write_markdown(output_dir / "summary.md", summary)
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate reproducible EDA for canonical tenders")
    parser.add_argument("--canonical-csv", type=Path, default=DEFAULT_CANONICAL_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        summary = analyze_tender_data(
            canonical_csv=args.canonical_csv,
            output_dir=args.output_dir,
            project_root=args.project_root,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"EDA generation failed: {error}", file=sys.stderr)
        return 1
    print(
        "Wrote EDA report: "
        f"{args.output_dir / 'summary.md'} | rows={summary['dataset']['row_count']} "
        f"eligible={summary['dataset']['eligible_for_model_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
