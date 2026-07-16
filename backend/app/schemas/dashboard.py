"""
Schemas for dashboard summary and filter options.
"""

from pydantic import BaseModel, ConfigDict


class ScoreBin(BaseModel):
    model_config = ConfigDict(frozen=True)
    range_label: str
    count: int


class SummaryResponse(BaseModel):
    """Aggregate statistics for the dashboard."""

    model_config = ConfigDict(frozen=True)

    total_packages: int
    total_contract_value: float
    unique_suppliers: int
    unique_work_units: int
    packages_by_year: dict[str, int]
    score_distribution: list[ScoreBin]


class FilterOptionsResponse(BaseModel):
    """Available options for frontend dropdown filters."""

    model_config = ConfigDict(frozen=True)

    years: list[int]
    procurement_methods: list[str]
    procurement_types: list[str]
    work_units: list[str]
