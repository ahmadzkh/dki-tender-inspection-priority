# Backend API Contract

Status: backend integration contract for `TASK-BE-009`.

## Scope

API is read-only. Scores are inspection-priority signals, not proof of fraud, corruption, collusion, bid-rigging, or legal violation.

## Endpoints

| Endpoint | Purpose | Required response |
|---|---|---|
| `GET /api/v1/health` | readiness check | `ApiResponse[HealthResponse]` |
| `GET /api/v1/meta` | artifact and model metadata | `ApiResponse[MetaResponse]` |
| `GET /api/v1/summary` | dashboard aggregates | `ApiResponse[SummaryResponse]` |
| `GET /api/v1/filters` | filter option lists | `ApiResponse[FilterOptionsResponse]` |
| `GET /api/v1/rankings` | filtered ranking list | `ApiResponse[RankingResponse]` |
| `GET /api/v1/packages/{package_id}` | package detail | `ApiResponse[PackageDetailResponse]` |
| `GET /api/v1/export.csv` | filter-consistent CSV export | UTF-8 CSV with disclaimer first line |
| `GET /api/v1/evaluation` | precomputed model evaluation | `ApiResponse[dict]` |

## Performance Target

`GET /api/v1/summary` and `GET /api/v1/rankings?top_n=20&size=20` must keep combined p95 below 1 second after warm-up on dataset v1. Test coverage is in `tests/test_be_integration_contract.py`.

## Verification Commands

```bash
PYTHONPATH= uv run ruff check .
PYTHONPATH= uv run ruff format --check .
PYTHONPATH= uv run pytest --basetemp=.hermes-pytest-procurement
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
curl -fsS http://127.0.0.1:8000/api/v1/health
curl -fsS http://127.0.0.1:8000/openapi.json
```
