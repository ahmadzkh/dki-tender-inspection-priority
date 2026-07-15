"""
Backend path configuration.

All paths are resolved from environment variables with defaults derived
from this file's position in the repository.  No absolute machine paths
are hardcoded.

Environment variables:
    PROJECT_ROOT       – override the inferred project root directory.
    ARTIFACT_DIR       – override the default <root>/artifacts directory.
    PROCESSED_DATA_DIR – override the default <root>/datasets/processed.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root resolution
# ---------------------------------------------------------------------------
# backend/app/config.py → parent → backend/app
#                       → parent.parent → backend
#                       → parent.parent.parent → project root


def _resolve_project_root() -> Path:
    if raw := os.environ.get("PROJECT_ROOT"):
        return Path(raw).resolve()
    return Path(__file__).resolve().parent.parent.parent


PROJECT_ROOT: Path = _resolve_project_root()

# ---------------------------------------------------------------------------
# Directory paths (env-overridable)
# ---------------------------------------------------------------------------

ARTIFACT_DIR: Path = Path(os.environ.get("ARTIFACT_DIR", str(PROJECT_ROOT / "artifacts")))
PROCESSED_DATA_DIR: Path = Path(
    os.environ.get("PROCESSED_DATA_DIR", str(PROJECT_ROOT / "datasets" / "processed"))
)

# ---------------------------------------------------------------------------
# Key artifact file paths
# ---------------------------------------------------------------------------

MANIFEST_PATH: Path = ARTIFACT_DIR / "manifest.json"
RANKING_PATH: Path = ARTIFACT_DIR / "isolation_forest_ranking.csv"
EXPLANATIONS_PATH: Path = ARTIFACT_DIR / "ranking_explanations.json"

# ---------------------------------------------------------------------------
# API interpretation constants
# ---------------------------------------------------------------------------

SCORE_DIRECTION: str = "higher score means higher inspection priority"

DISCLAIMER: str = (
    "Scores represent statistical unusualness relative to the 2024-2025 training "
    "baseline and are intended solely for ordering inspection workload.  They do not "
    "constitute proof of fraud, corruption, collusion, bid-rigging, or any legal or "
    "administrative violation."
)
