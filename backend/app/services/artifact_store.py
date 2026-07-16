"""
Read-only artifact store for the DKI Jakarta Tender Inspection API.

Artifacts are loaded and validated exactly once during FastAPI application
startup (via the lifespan context in main.py).  A failed load halts
startup with a clear error rather than silently serving stale or invalid data.

Integrity guarantee:
    SHA-256 checksums stored in artifacts/manifest.json are verified
    against all key artifacts before any request is served.

Null handling:
    Null / NaN values in source data remain null in the DataFrame; they are
    never coerced to zero or empty string.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_EXPECTED_SCHEMA_VERSION: int = 1

# Columns that must exist in the ranking CSV before the store is accepted.
_RANKING_REQUIRED_COLUMNS: frozenset[str] = frozenset(
    {
        "package_id",
        "year",
        "anomaly_score",
        "anomaly_rank",
        "supplier_name",
        "work_unit",
        "procurement_method",
        "procurement_type",
        "split",
    }
)


# ---------------------------------------------------------------------------
# Public data class
# ---------------------------------------------------------------------------


@dataclass
class ArtifactStore:
    """Immutable, validated snapshot of all precomputed backend artifacts.

    Fields:
        manifest         – parsed artifacts/manifest.json.
        ranking          – DataFrame sorted by anomaly_score DESC; package_id is str.
        explanations_by_id – dict keyed by package_id (str) → explanation record.
        model_version    – short hash identifying the trained model.
        generated_at     – ISO-8601 timestamp from the manifest.
        schema_version   – manifest schema_version (int).
    """

    manifest: dict
    ranking: pd.DataFrame
    explanations_by_id: dict
    features_by_id: dict
    canonical_by_id: dict
    evaluation: dict
    model_config: dict
    model_version: str
    dataset_version: str
    generated_at: str
    schema_version: int

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def load(
        cls,
        *,
        manifest_path: Path,
        ranking_path: Path,
        explanations_path: Path,
        canonical_path: Path,
        features_path: Path,
        evaluation_path: Path,
        model_config_path: Path,
        project_root: Path,
    ) -> "ArtifactStore":
        """Load and validate all artifacts.

        Raises:
            FileNotFoundError – a required file does not exist.
            ValueError        – manifest is invalid, schema version is wrong,
                                a checksum does not match, or required columns
                                are missing from the ranking CSV.
        """
        logger.info("Loading artifacts (project_root=%s)", project_root)

        manifest = _load_manifest(manifest_path)
        checksum_index = _build_checksum_index(manifest, project_root)

        _validate_checksum(ranking_path, checksum_index, project_root)
        _validate_checksum(explanations_path, checksum_index, project_root)
        _validate_checksum(canonical_path, checksum_index, project_root)
        _validate_checksum(features_path, checksum_index, project_root)
        _validate_checksum(evaluation_path, checksum_index, project_root)
        _validate_checksum(model_config_path, checksum_index, project_root)

        explanations_by_id = _load_explanations(explanations_path)
        canonical_by_id = _load_csv_as_dict(canonical_path, "package_id")
        features_by_id = _load_csv_as_dict(features_path, "package_id")
        ranking = _load_ranking(ranking_path)
        contract_values = {
            package_id: row.get("contract_value") for package_id, row in canonical_by_id.items()
        }
        ranking["contract_value"] = pd.to_numeric(
            ranking["package_id"].map(contract_values), errors="coerce"
        )
        evaluation = _load_json_object(evaluation_path, "Evaluation")
        model_config = _load_json_object(model_config_path, "Model config")

        model_version: str = manifest["version"]
        dataset_version: str = manifest["dataset_version"]
        generated_at: str = manifest["generated_at"]
        schema_version: int = manifest["schema_version"]

        logger.info(
            "Artifact store ready: model_version=%s, rows=%d, explanations=%d",
            model_version,
            len(ranking),
            len(explanations_by_id),
        )

        return cls(
            manifest=manifest,
            ranking=ranking,
            explanations_by_id=explanations_by_id,
            features_by_id=features_by_id,
            canonical_by_id=canonical_by_id,
            evaluation=evaluation,
            model_config=model_config,
            model_version=model_version,
            dataset_version=dataset_version,
            generated_at=generated_at,
            schema_version=schema_version,
        )


# ---------------------------------------------------------------------------
# Internal helpers — not part of the public API
# ---------------------------------------------------------------------------


def _load_manifest(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Manifest is not valid JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("Manifest root must be a JSON object")
    schema_version = manifest.get("schema_version")
    if schema_version != _EXPECTED_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported manifest schema_version: {schema_version!r}; "
            f"expected {_EXPECTED_SCHEMA_VERSION}"
        )
    return manifest


def _build_checksum_index(manifest: dict, _project_root: Path) -> dict[str, str]:
    """Build posix-normalised relative-path → sha256 from all artifact categories."""
    index: dict[str, str] = {}
    for category_items in manifest.get("artifacts", {}).values():
        for item in category_items:
            posix_key = str(item["path"]).replace("\\", "/")
            index[posix_key] = item["sha256"]
    return index


def _validate_checksum(file_path: Path, checksum_index: dict[str, str], root: Path) -> None:
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact file missing: {file_path}")
    relative_posix = file_path.resolve().relative_to(root.resolve()).as_posix()
    expected = checksum_index.get(relative_posix)
    if expected is None:
        raise ValueError(f"No checksum entry in manifest for: {relative_posix}")
    actual = hashlib.sha256(file_path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(
            f"Checksum mismatch for {relative_posix}: expected {expected!r}, got {actual!r}"
        )


def _load_ranking(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"package_id": str})
    missing = _RANKING_REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Ranking CSV missing required columns: {sorted(missing)}")
    df = df.sort_values("anomaly_score", ascending=False).reset_index(drop=True)
    return df


def _load_explanations(path: Path) -> dict:
    """Load ranking_explanations.json and index all records by package_id (str).

    Expected format:
        {"20": [...top-20 records...], "50": [...top-50...], "all": [...all explained...]}

    The "all" list is used as the authoritative source.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Explanations file is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict) or "all" not in raw:
        raise ValueError("Explanations JSON must be an object with an 'all' key containing a list")
    indexed: dict[str, dict] = {}
    for record in raw["all"]:
        pid = str(record["package_id"])
        indexed[pid] = record
    return indexed


def _load_json_object(path: Path, label: str) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} root must be a JSON object")
    return payload


def _load_csv_as_dict(path: Path, index_col: str) -> dict:
    """Load a CSV and return a dict indexed by index_col (as string)."""
    df = pd.read_csv(path, dtype={index_col: str}, low_memory=False)
    # Convert to list of dicts and then index
    records = df.to_dict(orient="records")
    indexed = {}
    for r in records:
        pid = str(r[index_col])
        indexed[pid] = r
    return indexed
