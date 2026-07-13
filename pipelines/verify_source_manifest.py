from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST_PATH = Path("datasets/manifests/source_manifest.json")


def _read_csv_metadata(path: Path) -> tuple[int, list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        try:
            schema = next(reader)
        except StopIteration as error:
            raise ValueError(f"CSV is empty: {path}") from error
        return sum(1 for _ in reader), schema


def _resolve_source_path(project_root: Path, relative_path: str) -> Path:
    candidate = (project_root / relative_path).resolve()
    if not candidate.is_relative_to(project_root):
        raise ValueError(f"Source path escapes project root: {relative_path}")
    return candidate


def verify_source_manifest(project_root: Path) -> int:
    project_root = project_root.resolve()
    manifest_path = project_root / DEFAULT_MANIFEST_PATH
    manifest: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Manifest root must be an object")
    manifest_version = manifest.get("manifest_version")
    if type(manifest_version) is not int or manifest_version != 1:
        raise ValueError("Unsupported manifest_version")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("Manifest must contain a non-empty files list")

    required_fields = (
        "path",
        "role",
        "source_years",
        "provenance",
        "sha256",
        "byte_size",
        "row_count",
        "schema",
    )
    raw_dir = (project_root / "datasets/raw").resolve()
    listed_paths: set[str] = set()

    for entry in files:
        if not isinstance(entry, dict):
            raise ValueError("Each manifest file entry must be an object")
        for field in required_fields:
            if field not in entry:
                raise ValueError(f"Manifest file entry missing required field: {field}")

        metadata_is_valid = {
            "role": isinstance(entry["role"], str) and bool(entry["role"].strip()),
            "source_years": isinstance(entry["source_years"], list)
            and bool(entry["source_years"])
            and all(type(year) is int for year in entry["source_years"]),
            "provenance": isinstance(entry["provenance"], dict) and bool(entry["provenance"]),
        }
        for field, is_valid in metadata_is_valid.items():
            if not is_valid:
                raise ValueError(f"Manifest file entry has invalid field: {field}")

        relative_path = entry["path"]
        if not isinstance(relative_path, str):
            raise ValueError("Manifest file path must be a string")

        source_path = _resolve_source_path(project_root, relative_path)
        if not source_path.is_relative_to(raw_dir):
            raise ValueError(f"Source file must be inside datasets/raw: {relative_path}")
        normalized_path = source_path.relative_to(project_root).as_posix()
        if normalized_path in listed_paths:
            raise ValueError(f"duplicate manifest path: {relative_path}")
        listed_paths.add(normalized_path)
        content = source_path.read_bytes()
        row_count, schema = _read_csv_metadata(source_path)
        actual = {
            "sha256": hashlib.sha256(content).hexdigest(),
            "byte_size": len(content),
            "row_count": row_count,
            "schema": schema,
        }
        for field, actual_value in actual.items():
            if entry.get(field) != actual_value:
                raise ValueError(
                    f"{relative_path}: {field} mismatch "
                    f"(expected {entry.get(field)!r}, actual {actual_value!r})"
                )

    raw_paths = {path.relative_to(project_root).as_posix() for path in raw_dir.rglob("*.csv")}
    unlisted_paths = sorted(raw_paths - listed_paths)
    if unlisted_paths:
        raise ValueError(f"unlisted raw CSV file(s): {', '.join(unlisted_paths)}")

    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify immutable source files against manifest")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    try:
        verified_count = verify_source_manifest(args.project_root)
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Manifest verification failed: {error}", file=sys.stderr)
        return 1

    print(f"Verified {verified_count} source file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
