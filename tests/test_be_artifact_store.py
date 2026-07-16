"""
Tests for TASK-BE-002: ArtifactStore integrity, load, and failure paths.

Two kinds of tests:
  1. Integration tests using real project artifacts — verify count, ordering,
     indexing, and schema correctness against the committed artifact set.
  2. Synthetic failure tests using tmp_path fixtures — verify each failure
     mode raises the correct exception with a descriptive message.
"""

import json
from pathlib import Path

import pytest

from backend.app.config import (
    CANONICAL_PATH,
    EVALUATION_PATH,
    EXPLANATIONS_PATH,
    FEATURES_PATH,
    MANIFEST_PATH,
    MODEL_CONFIG_PATH,
    PROJECT_ROOT,
    RANKING_PATH,
)
from backend.app.services.artifact_store import ArtifactStore, _build_checksum_index

# ---------------------------------------------------------------------------
# Fixture — load real artifact store once for integration tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def store() -> ArtifactStore:
    return ArtifactStore.load(
        manifest_path=MANIFEST_PATH,
        ranking_path=RANKING_PATH,
        explanations_path=EXPLANATIONS_PATH,
        canonical_path=CANONICAL_PATH,
        features_path=FEATURES_PATH,
        evaluation_path=EVALUATION_PATH,
        model_config_path=MODEL_CONFIG_PATH,
        project_root=PROJECT_ROOT,
    )


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


def test_should_load_valid_artifacts_without_error(store: ArtifactStore) -> None:
    """Real artifacts load without raising."""
    assert store is not None


def test_should_contain_all_eligible_records(store: ArtifactStore) -> None:
    """Ranking must contain exactly 1276 eligible records."""
    assert len(store.ranking) == 1276


def test_should_sort_ranking_by_anomaly_score_descending(store: ArtifactStore) -> None:
    """Highest anomaly_score must appear in the first row."""
    scores = store.ranking["anomaly_score"].tolist()
    assert scores == sorted(scores, reverse=True)


def test_should_index_explanations_by_package_id(store: ArtifactStore) -> None:
    """Explanation for the top-ranked package must be retrievable by package_id."""
    top_id: str = store.manifest["summary"]["top_20_package_ids"][0]
    assert top_id in store.explanations_by_id
    record = store.explanations_by_id[top_id]
    assert "factors" in record
    assert len(record["factors"]) >= 3, "Top-N package must have at least 3 explanation factors"


def test_should_expose_model_version_matching_manifest(store: ArtifactStore) -> None:
    """model_version must equal the manifest 'version' field."""
    assert store.model_version == store.manifest["version"]
    assert store.dataset_version == store.manifest["dataset_version"]
    assert store.evaluation["artifact_versions"]["model_version"] == store.model_version
    assert store.model_config["model_version"] == store.model_version
    assert store.ranking["contract_value"].notna().all()


def test_should_preserve_package_id_as_string(store: ArtifactStore) -> None:
    """package_id column must be a string dtype (not int), regardless of pandas version."""
    import pandas as pd

    assert pd.api.types.is_string_dtype(store.ranking["package_id"])


def test_should_not_coerce_nulls_to_zero(store: ArtifactStore) -> None:
    """anomaly_score must be non-null for all records; no silent zero-fill."""
    assert store.ranking["anomaly_score"].notna().all()
    assert (store.ranking["anomaly_rank"] >= 1).all()


def test_should_surface_score_direction_in_manifest(store: ArtifactStore) -> None:
    """Manifest isolation_forest_config must document score_direction."""
    config_path = PROJECT_ROOT / "artifacts" / "isolation_forest_config.json"
    import json

    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert "score_direction" in config
    assert "higher" in config["score_direction"].lower()


def test_should_normalize_manifest_paths_for_linux_container() -> None:
    """Windows-style manifest paths must match POSIX paths inside Docker."""
    manifest = {
        "artifacts": {
            "model": [
                {
                    "path": "artifacts\\isolation_forest_ranking.csv",
                    "sha256": "abc",
                }
            ]
        }
    }

    index = _build_checksum_index(manifest, PROJECT_ROOT)

    assert index["artifacts/isolation_forest_ranking.csv"] == "abc"


# ---------------------------------------------------------------------------
# Failure-path tests (synthetic fixtures via tmp_path)
# ---------------------------------------------------------------------------


def test_should_raise_when_manifest_is_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Manifest not found"):
        ArtifactStore.load(
            manifest_path=tmp_path / "nonexistent.json",
            ranking_path=RANKING_PATH,
            explanations_path=EXPLANATIONS_PATH,
            canonical_path=CANONICAL_PATH,
            features_path=FEATURES_PATH,
            evaluation_path=EVALUATION_PATH,
            model_config_path=MODEL_CONFIG_PATH,
            project_root=PROJECT_ROOT,
        )


def test_should_raise_when_manifest_has_wrong_schema_version(tmp_path: Path) -> None:
    bad: dict = {
        "schema_version": 99,
        "version": "test",
        "generated_at": "2026-01-01T00:00:00Z",
        "artifacts": {},
    }
    bad_path = tmp_path / "manifest.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="schema_version"):
        ArtifactStore.load(
            manifest_path=bad_path,
            ranking_path=RANKING_PATH,
            explanations_path=EXPLANATIONS_PATH,
            canonical_path=CANONICAL_PATH,
            features_path=FEATURES_PATH,
            evaluation_path=EVALUATION_PATH,
            model_config_path=MODEL_CONFIG_PATH,
            project_root=PROJECT_ROOT,
        )


def test_should_raise_on_corrupt_ranking_checksum(tmp_path: Path) -> None:
    """Tampered SHA-256 entry in manifest must be detected before loading."""
    real_manifest: dict = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for item in real_manifest.get("artifacts", {}).get("model", []):
        if "isolation_forest_ranking.csv" in item["path"]:
            item["sha256"] = "deadbeef" * 8  # corrupt checksum (256 bits of garbage)
    bad_path = tmp_path / "manifest.json"
    bad_path.write_text(json.dumps(real_manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="[Cc]hecksum"):
        ArtifactStore.load(
            manifest_path=bad_path,
            ranking_path=RANKING_PATH,
            explanations_path=EXPLANATIONS_PATH,
            canonical_path=CANONICAL_PATH,
            features_path=FEATURES_PATH,
            evaluation_path=EVALUATION_PATH,
            model_config_path=MODEL_CONFIG_PATH,
            project_root=PROJECT_ROOT,
        )


def test_should_raise_when_ranking_file_is_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Artifact file missing"):
        ArtifactStore.load(
            manifest_path=MANIFEST_PATH,
            ranking_path=tmp_path / "nonexistent_ranking.csv",
            explanations_path=EXPLANATIONS_PATH,
            canonical_path=CANONICAL_PATH,
            features_path=FEATURES_PATH,
            evaluation_path=EVALUATION_PATH,
            model_config_path=MODEL_CONFIG_PATH,
            project_root=PROJECT_ROOT,
        )


def test_should_raise_when_explanations_file_is_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Artifact file missing"):
        ArtifactStore.load(
            manifest_path=MANIFEST_PATH,
            ranking_path=RANKING_PATH,
            explanations_path=tmp_path / "nonexistent_explanations.json",
            canonical_path=CANONICAL_PATH,
            features_path=FEATURES_PATH,
            evaluation_path=EVALUATION_PATH,
            model_config_path=MODEL_CONFIG_PATH,
            project_root=PROJECT_ROOT,
        )


def test_should_raise_when_manifest_is_not_valid_json(tmp_path: Path) -> None:
    bad_path = tmp_path / "manifest.json"
    bad_path.write_text("{not json}", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        ArtifactStore.load(
            manifest_path=bad_path,
            ranking_path=RANKING_PATH,
            explanations_path=EXPLANATIONS_PATH,
            canonical_path=CANONICAL_PATH,
            features_path=FEATURES_PATH,
            evaluation_path=EVALUATION_PATH,
            model_config_path=MODEL_CONFIG_PATH,
            project_root=PROJECT_ROOT,
        )
