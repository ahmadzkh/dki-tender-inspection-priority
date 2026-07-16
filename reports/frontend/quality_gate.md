# Frontend Quality Gate

Status: local frontend quality gate verified.

## Verified Scope

- landing page
- dashboard summary, filters, ranking, pagination, CSV export
- package detail page
- dataset transparency page
- methodology page
- evaluation page

## Commands

```bash
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend audit --audit-level=moderate
cd frontend && npm exec playwright test
```

## Playwright Coverage

- latest local run: 18 tests passed across Chrome, Edge, and Firefox
- browser matrix: Chrome, Edge, and Firefox projects run sequentially
- primary dashboard-to-detail flow
- dataset and methodology pages
- dashboard console error guard
- dashboard LCP budget under 2.5 seconds where the browser exposes LCP entries
- keyboard focus smoke
- mobile viewport smoke
- CSV export download smoke

## Deployment Boundary

This report verifies local production build and E2E readiness only. `TASK-FE-012` remains incomplete until a durable public backend URL exists, Vercel production environment is set, and public E2E smoke passes.
