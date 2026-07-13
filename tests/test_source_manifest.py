from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERIFY_SCRIPT = PROJECT_ROOT / "pipelines" / "verify_source_manifest.py"


def _write_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["kode_paket", "tahun_anggaran"])
        writer.writerow(["00123", "2024"])


def _write_manifest(project_root: Path, source_path: Path) -> None:
    content = source_path.read_bytes()
    manifest = {
        "manifest_version": 1,
        "files": [
            {
                "path": source_path.relative_to(project_root).as_posix(),
                "role": "annual_source",
                "source_years": [2024],
                "provenance": {"publisher": "INAPROC/LKPP"},
                "sha256": hashlib.sha256(content).hexdigest(),
                "byte_size": len(content),
                "row_count": 1,
                "schema": ["kode_paket", "tahun_anggaran"],
            }
        ],
    }
    manifest_path = project_root / "datasets" / "manifests" / "source_manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


def _run_verifier(project_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, VERIFY_SCRIPT, "--project-root", project_root],
        capture_output=True,
        check=False,
        text=True,
    )


def test_should_accept_manifest_when_file_metadata_matches(tmp_path: Path) -> None:
    source_path = tmp_path / "datasets" / "raw" / "source.csv"
    _write_csv(source_path)
    _write_manifest(tmp_path, source_path)

    result = _run_verifier(tmp_path)

    assert result.returncode == 0, result.stderr
    assert "Verified 1 source file(s)." in result.stdout


def test_should_reject_unlisted_csv_when_raw_directory_has_extra_file(tmp_path: Path) -> None:
    source_path = tmp_path / "datasets" / "raw" / "source.csv"
    _write_csv(source_path)
    _write_manifest(tmp_path, source_path)
    _write_csv(source_path.with_name("unlisted.csv"))

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "unlisted raw CSV" in result.stderr


def test_should_reject_manifest_when_provenance_is_missing(tmp_path: Path) -> None:
    source_path = tmp_path / "datasets" / "raw" / "source.csv"
    _write_csv(source_path)
    _write_manifest(tmp_path, source_path)
    manifest_path = tmp_path / "datasets" / "manifests" / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0].pop("provenance")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "missing required field: provenance" in result.stderr


def test_should_reject_manifest_when_root_is_not_object(tmp_path: Path) -> None:
    manifest_path = tmp_path / "datasets" / "manifests" / "source_manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("[]", encoding="utf-8")

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "Manifest root must be an object" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("invalid_version", [True, 1.0, "1", 2])
def test_should_reject_manifest_when_version_is_invalid(
    tmp_path: Path, invalid_version: object
) -> None:
    source_path = tmp_path / "datasets" / "raw" / "source.csv"
    _write_csv(source_path)
    _write_manifest(tmp_path, source_path)
    manifest_path = tmp_path / "datasets" / "manifests" / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["manifest_version"] = invalid_version
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "Unsupported manifest_version" in result.stderr


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("role", None),
        ("source_years", None),
        ("provenance", None),
    ],
)
def test_should_reject_manifest_when_required_metadata_is_invalid(
    tmp_path: Path, field: str, invalid_value: object
) -> None:
    source_path = tmp_path / "datasets" / "raw" / "source.csv"
    _write_csv(source_path)
    _write_manifest(tmp_path, source_path)
    manifest_path = tmp_path / "datasets" / "manifests" / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0][field] = invalid_value
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert f"invalid field: {field}" in result.stderr


def test_should_reject_unlisted_csv_when_nested_raw_directory_has_extra_file(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "datasets" / "raw" / "source.csv"
    _write_csv(source_path)
    _write_manifest(tmp_path, source_path)
    _write_csv(source_path.parent / "nested" / "unlisted.csv")

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "unlisted raw CSV" in result.stderr


def test_should_reject_manifest_when_source_content_changes(tmp_path: Path) -> None:
    source_path = tmp_path / "datasets" / "raw" / "source.csv"
    _write_csv(source_path)
    _write_manifest(tmp_path, source_path)
    source_path.write_bytes(source_path.read_bytes() + b"tampered")

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "sha256 mismatch" in result.stderr
