"""Shared ranking filters used by JSON and CSV endpoints."""

import pandas as pd


def filter_rankings(
    ranking: pd.DataFrame,
    *,
    year: int | None = None,
    work_unit: str | None = None,
    procurement_method: str | None = None,
    procurement_type: str | None = None,
    supplier_name: str | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
    min_contract_value: float | None = None,
    max_contract_value: float | None = None,
    top_n: int | None = None,
) -> pd.DataFrame:
    """Return ranking rows in frozen score order after all active filters."""
    result = ranking
    if year is not None:
        result = result[result["year"] == year]
    if work_unit:
        result = result[result["work_unit"].str.contains(work_unit, case=False, na=False)]
    if procurement_method:
        result = result[result["procurement_method"] == procurement_method]
    if procurement_type:
        result = result[result["procurement_type"] == procurement_type]
    if supplier_name:
        result = result[result["supplier_name"].str.contains(supplier_name, case=False, na=False)]
    if min_score is not None:
        result = result[result["anomaly_score"] >= min_score]
    if max_score is not None:
        result = result[result["anomaly_score"] <= max_score]
    if min_contract_value is not None:
        result = result[result["contract_value"] >= min_contract_value]
    if max_contract_value is not None:
        result = result[result["contract_value"] <= max_contract_value]
    if top_n is not None:
        result = result.head(top_n)
    return result
