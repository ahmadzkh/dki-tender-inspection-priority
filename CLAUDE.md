# CLAUDE.md — DKI Jakarta Tender Inspection Prioritization System

> This file is written in English because coding agents process technical constraints more consistently in English.
> It follows every section of the original project template. Update it as the implementation changes.

## Mandatory Agent Startup

Before any task:

1. Read `AGENTS.md`.
2. Read `PRD.md` completely, especially scope, acceptance criteria, risks, and open decisions.
3. Read this `CLAUDE.md` completely.
4. Read `TASKS.md`; select the earliest unchecked task whose dependencies are complete.
5. Load the `ponytail` skill. Apply YAGNI-first minimal implementation.
6. Load the `caveman/caveman` skill for concise progress reporting.
7. Inspect existing files and reuse established patterns before creating code.
8. Do not claim completion or check a task until implementation, machine verification, and required code review pass.

---

## 1. Project Overview

- **Name**: DKI Jakarta Government Tender Inspection Prioritization System
- **Research title**: Rancang Bangun Sistem Prioritas Pemeriksaan Realisasi Tender Pemerintah Provinsi DKI Jakarta Menggunakan Isolation Forest Berbasis Web
- **Description**: A web application that enriches official DKI Jakarta completed-tender data, builds financial, temporal, and supplier-concentration features, and ranks procurement packages using Isolation Forest. The result is an inspection-priority score, not a fraud verdict.
- **Goal**: Help auditors or procurement analysts decide which completed tender packages to inspect first using traceable data, reproducible anomaly scoring, and neutral explanations.
- **Target Users**: Government internal auditors/inspectorate staff, procurement analysts, thesis supervisors/examiners, and researchers.
- **Version**: `0.1.0` foundation/data-preparation stage
- **Status**: Active development; Python and Next.js foundations plus immutable source-data layout, reproducible source-data audit, resumable enrichment runner, full enrichment coverage report, and one-package-per-record canonical dataset exist. Feature engineering, model, backend API, product UI, containers, and deployment are still planned.
- **Research Methods**:
  - CRISP-DM for data understanding, preparation, modeling, evaluation, and deployment.
  - RAD for web requirements planning, user design, construction, and cutover.
- **Interpretation Boundary**: Never describe an anomaly score as proof of fraud, corruption, collusion, bid-rigging, or legal wrongdoing.

### Current Verified Data State

- Main merged input: `datasets/raw/realisasi_dki_jakarta_2024_2026.csv`
- Rows: 1,279
- Source columns: 14
- Unique package codes: 1,277
- Years: 2024 = 312, 2025 = 529, 2026 = 438
- All merged records: Province of DKI Jakarta, source transaction `Tender`, status `SELESAI`
- 2026 is a partial-year snapshot as of July 2026, not a complete calendar year.
- Package `10060212000` occurs three times with different suppliers and is retained as one canonical row with `eligible_for_model=false`.
- Five 2026 source rows with missing supplier names were excluded from the current merged file and are documented in the canonical data-quality report.

---

## 2. Tech Stack

### Planned and Approved

- **Languages**: Python 3.11+ for pipelines/model/backend; TypeScript for frontend
- **Machine Learning**: pandas, NumPy, scikit-learn Isolation Forest, joblib
- **Model Explanation**: permutation sensitivity as baseline; SHAP only after explanation-score consistency is verified
- **Backend Framework**: FastAPI with Pydantic models
- **Frontend Framework**: Next.js App Router with React and TypeScript strict mode
- **Styling**: Tailwind CSS and CSS variables
- **UI Library**: No mandatory component library. Prefer small local components. Add shadcn/ui only when a concrete repeated need exists and the user approves the dependency.
- **Charts**: Choose one lightweight chart library only when dashboard implementation starts; do not install multiple chart libraries.
- **Database**: None for v1.0 unless a proven runtime write/query requirement appears. Prefer immutable CSV/Parquet/JSON artifacts loaded by the backend.
- **ORM**: None in v1.0
- **Authentication**: None in v1.0; dashboard is read-only public research output
- **State Management**: URL search parameters, Server Component data, and local React state. No Redux/Zustand unless demonstrated necessary.
- **Data Fetching**: Native `fetch`; server-side by default; client-side only for interactive filtering that cannot be represented by navigation/search parameters
- **Python Package Manager**: `uv`
- **Frontend Package Manager**: `npm`; do not mix npm with yarn, pnpm, or bun
- **Backend Deployment**: Docker on VPS/server, exposed through Cloudflare Tunnel
- **Frontend Deployment**: Vercel
- **Source Data**: Official INAPROC portal and package-detail API

### Verified Installed Foundation

- **Python**: 3.11.15, managed through `.python-version` and `uv.lock`
- **Python Runtime**: NumPy 2.4.6, pandas 3.0.3, scikit-learn 1.9.0, joblib 1.5.3
- **Python Development**: pytest 9.1.1, Ruff 0.15.21
- **Frontend**: Next.js 16.2.10, React 19.2.4, TypeScript 5.9.3, Tailwind CSS 4.3.2
- **Frontend Security Override**: PostCSS 8.5.17 replaces Next.js nested PostCSS 8.4.31; `npm audit` must remain at zero known vulnerabilities
- **Not Installed Yet**: FastAPI/uvicorn, SHAP, chart library, frontend test framework, Playwright, Docker runtime files

### Deliberately Not Selected

- Deep learning or GPU training
- Multi-service backend
- Operational database
- Authentication/RBAC
- Real-time streaming
- Automatic retraining

---

## 3. Commands

### Current State

Python and frontend foundations, source-manifest verification, source-data audit, resumable enrichment runner, full enrichment coverage report, and canonical dataset builder are available. Feature engineering, model, backend, frontend test, E2E, and Docker commands remain planned until their corresponding tasks create and verify them.

```bash
# Python environment
uv sync
uv run python --version
uv run ruff check .
uv run ruff format --check .
uv run pytest

# Source-data integrity — available now
uv run python pipelines/verify_source_manifest.py

# Source-data audit — available now
uv run python pipelines/audit_source_data.py

# Enrichment runner — available now; requires configured INAPROC detail base URL
INAPROC_DETAIL_API_BASE_URL="<detail-api-base-url>" uv run python pipelines/enrich_tender_details.py --limit 10
uv run python pipelines/report_enrichment_coverage.py

# Data pipeline — canonicalization available; later feature commands remain planned
uv run python pipelines/build_canonical_dataset.py
uv run python pipelines/build_model_features.py

# Model — planned stable command interface
uv run python modeling/train_isolation_forest.py
uv run python modeling/evaluate_anomaly_ranking.py

# Backend development — planned after TASK-BE-001
uv run fastapi dev backend/app/main.py
uv run fastapi run backend/app/main.py

# Scoped Python tests — available when those folders contain tests
uv run pytest tests/unit
uv run pytest tests/integration

# Frontend development — available now
npm --prefix frontend install
npm --prefix frontend run dev
npm --prefix frontend run build
npm --prefix frontend run start
npm --prefix frontend run lint
npm --prefix frontend audit

# Frontend tests — planned after the first real frontend behavior requires them
# npm --prefix frontend run test
# npm --prefix frontend run test:e2e

# Docker — after compose configuration exists
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=100
docker compose down
```

### Package Management Rules

- Use `uv add <package>` for Python runtime dependencies.
- Use `uv add --dev <package>` for Python development dependencies.
- Use `npm --prefix frontend install <package>` for frontend dependencies.
- Never use bare `pip` on this host.
- Never add a dependency without first checking standard library, platform features, and existing dependencies.
- Ask for confirmation before installing a new package.

### Development Server Cleanup

After using `npm run dev` or another bounded development server for verification, terminate it and free its port. Do not leave port 3000 occupied.

### Database Commands

No database commands exist in v1.0. Do not add migrations, seeds, Prisma, SQLAlchemy, or database containers unless an approved requirement makes read-only artifacts insufficient.

---

## 4. Project Structure

**Architecture**: Simple research monorepo, separated by responsibility. Keep one FastAPI backend and one Next.js frontend. Avoid microservices.

### Current Structure

```text
procurement_data/
├── .python-version
├── AGENTS.md
├── CLAUDE.md
├── PRD.md
├── README.md
├── TASKS.md
├── pyproject.toml
├── uv.lock
├── src/
│   └── procurement_priority/
├── tests/
│   ├── test_audit_source_data.py
│   ├── test_build_canonical_dataset.py
│   ├── test_enrichment_coverage.py
│   ├── test_environment.py
│   └── test_source_manifest.py
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   └── src/app/
├── pipelines/
│   ├── audit_source_data.py
│   ├── build_canonical_dataset.py
│   ├── enrich_tender_details.py
│   ├── report_enrichment_coverage.py
│   └── verify_source_manifest.py
├── reports/
│   └── data/
│       ├── canonical_data_quality.json
│       ├── canonical_data_quality.md
│       ├── enrichment_coverage.json
│       ├── enrichment_coverage.md
│       ├── source_audit.json
│       └── source_audit.md
└── datasets/
    ├── manifests/
    │   └── source_manifest.json
    ├── processed/
    │   └── tenders_canonical.csv
    └── raw/
        ├── inaproc_realisasi_tender_dki_jakarta_2024.csv
        ├── inaproc_realisasi_tender_dki_jakarta_2025.csv
        ├── inaproc_realisasi_tender_dki_jakarta_2026.csv
        └── realisasi_dki_jakarta_2024_2026.csv
```

### Approved Target Structure

Create directories only when their first real file is needed. Do not generate empty architecture boilerplate.

```text
procurement_data/
├── AGENTS.md                    # Cross-agent startup instructions
├── CLAUDE.md                    # Engineering conventions and project context
├── PRD.md                       # Product requirements and scope
├── README.md                    # Public project overview and usage status
├── TASKS.md                     # Operational task tracker and dependencies
├── pyproject.toml               # Python dependencies/tooling after Python scaffold
├── uv.lock                      # Locked Python environment
├── src/
│   └── procurement_priority/    # Shared Python package
├── docker-compose.yml           # Backend runtime after deployment work starts
├── datasets/
│   ├── raw/                     # Immutable source exports and API snapshots
│   ├── processed/               # Canonical/enriched datasets
│   └── manifests/               # Checksums, row counts, schemas, provenance
├── pipelines/                   # Audit, enrichment, canonicalization, feature scripts
├── modeling/                    # Train/evaluate/export model artifacts
├── artifacts/                   # Versioned model, feature schema, evaluation outputs
├── backend/
│   └── app/
│       ├── main.py              # FastAPI entry point
│       ├── api/                 # Route definitions
│       ├── schemas/             # Pydantic request/response models
│       └── services/            # Read-only ranking/report logic
├── frontend/
│   ├── src/app/                 # Next.js routes and layouts
│   ├── src/components/          # Shared presentation components
│   ├── src/lib/                 # Typed API and formatting utilities
│   ├── public/                  # Static public assets
│   └── package.json
├── reports/                     # Generated research tables/figures, not hand-edited data
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

### File Placement Rules

- Source exports and API responses belong under `datasets/raw/` once migration is approved.
- Derived canonical/enriched data belongs under `datasets/processed/`.
- Model binaries and feature schemas belong under `artifacts/`; never under frontend.
- Data transformation business logic belongs in `pipelines/` or reusable Python modules, not notebooks.
- Model training/evaluation belongs in `modeling/`.
- FastAPI routes stay thin; data access and ranking logic belong in backend services.
- New shared frontend UI components belong in `frontend/components/`.
- Frontend API clients and formatters belong in `frontend/lib/`.
- TypeScript types live beside their domain when local; shared API types belong in `frontend/lib/`.
- Do not create a new top-level directory not listed above without confirmation.
- Do not create all approved directories preemptively. Ponytail/YAGNI applies.

---

## 5. Naming Conventions

```text
# Files and Folders
- React components : PascalCase       Example: PriorityTable.tsx
- React hooks       : camelCase       Example: usePriorityFilters.ts
- TS utilities      : kebab-case      Example: format-currency.ts
- Python modules    : snake_case      Example: build_model_features.py
- Python classes    : PascalCase      Example: RankingService
- Folders           : kebab-case for frontend; snake_case only where Python package rules require it
- Next.js pages     : page.tsx
- Next.js layouts   : layout.tsx
- Python tests      : test_<behavior>.py
- TypeScript tests  : <name>.test.ts or <name>.test.tsx

# Inside Code
- TS variables/functions : camelCase
- Python variables/functions: snake_case
- Constants              : UPPER_SNAKE_CASE
- Types/interfaces/classes: PascalCase
- Enum                    : PascalCase
- CSS classes             : Tailwind utilities or kebab-case custom class

# Git Branches
- Feature  : feat/<short-feature-name>
- Bug fix  : fix/<short-bug-name>
- Hotfix   : hotfix/<short-name>
- Refactor : refactor/<short-name>
- Docs     : docs/<short-name>
```

Additional rules:

- Name scripts by function, never by milestone or task ID.
- Scan existing filenames in the target directory before choosing a name.
- Names must describe what running the file does.
- Use `package_id`, `supplier_name`, `work_unit`, and `anomaly_score` consistently in internal English code; map Indonesian source column names explicitly at the boundary.
- Never silently rename source columns in raw files.

---

## 6. Code Conventions

```text
# Coding Approach
- Apply ponytail/YAGNI: smallest correct implementation after tracing the real flow.
- Prefer standard library and existing dependencies.
- Do not add abstractions for hypothetical reuse.
- Extract shared logic only after real duplication or when a trust boundary needs one validator.
- Keep pure transformations separate from file/network I/O.
- Every non-trivial transformation leaves one runnable verification test.
```

### Python

- Target Python 3.11+.
- Use type hints for public functions and data boundaries.
- Use `pathlib.Path`, not concatenated path strings.
- Use explicit schemas/column lists for processed datasets.
- Do not mutate raw data files.
- Do not use broad `except Exception` without logging context and re-raising or returning a typed failure.
- Network calls require timeout, bounded retry, checkpoint/cache, and explicit failure reporting.
- Randomized algorithms require a fixed and recorded seed.
- Save model configuration, feature order, library versions, and dataset manifest with every artifact.
- Avoid row-wise pandas `apply` when vectorized operations are clearer and tested.
- Keep identifiers such as `kode_paket` as strings.
- Never convert missing enrichment to zero unless zero is semantically correct.

### TypeScript

- Enable strict mode.
- Do not use `any`; use `unknown` at untrusted boundaries and validate it.
- Explicitly type public function returns and component props.
- Use `interface` for object contracts and `type` for unions/intersections where practical.
- Validate backend responses at one boundary rather than scattering casts.
- Prefer Server Components; add `"use client"` only for actual interactivity.

### Import Order

1. Standard library/runtime imports
2. External libraries
3. Internal absolute imports
4. Internal relative imports
5. Type-only imports
6. Assets/styles

### Export Pattern

- Use named exports for reusable components, functions, and types.
- Use default exports only where Next.js requires them, such as `page.tsx` and `layout.tsx`.

### Error Handling

- Handle errors at trust boundaries: file input, external API, backend request, export generation, and artifact loading.
- Return specific user-safe error messages.
- Log internal context without secrets.
- Do not catch errors merely to hide them.
- Invalid filters/parameters return 4xx; unexpected backend failures return 500 without stack traces in client responses.

### Domain Language

Use neutral terms:

- Allowed: `priority`, `anomaly`, `unusual`, `requires review`, `inspection candidate`.
- Forbidden as model conclusions: `fraud`, `corrupt`, `collusive`, `guilty`, `proven violation`.

---

## 7. Component Rules

```text
# Component File Order
1. Imports
2. Types/interfaces
3. Small static constants
4. Component definition
5. Hooks
6. Derived values
7. Handlers/local functions
8. JSX return
9. Export
```

### Props

- Type all props explicitly.
- Use defaults for optional props where a real default exists.
- Prefer fewer than seven props. If a component needs more, first check whether the component is doing multiple jobs.
- Do not create generic component systems before two real usages exist.

### Server vs Client Components

Use Server Components by default. Use `"use client"` only for:

- `useState`, `useEffect`, or browser-only hooks;
- event handlers such as `onClick` and `onChange`;
- browser APIs;
- chart libraries that require the DOM;
- interactive filters that cannot be expressed through server navigation.

Do not use `useEffect` for initial data fetching. Prefer Server Components or explicit client query handlers.

### Component Size and Reuse

- Keep one-off page sections local when short.
- Move a component to its own file when reused, complex, or independently testable.
- Tables always receive full content width. Never place a multi-column table beside a chart or summary card.
- Put charts above full-width tables.
- Do not show raw JSON, model internals, or duplicate tables in the user-facing dashboard.

### Required UI States

Every data-driven page/component must define:

- loading state;
- empty state;
- error state;
- valid-data state;
- unavailable-field rendering as `Tidak tersedia`, never fake zero.

---

## 8. Styling Rules

```text
# Styling Approach
- Use Tailwind CSS utilities and CSS variables.
- Avoid inline styles except genuinely dynamic chart values.
- Do not use !important.
- Do not add a design-system package without need.
```

### Tailwind CSS

- Use utility classes directly in JSX.
- Use the project `cn` helper only after it exists and conditional classes justify it.
- Extract repeated visual patterns into components, not long custom CSS abstractions.
- Keep class order broadly: layout, spacing, sizing, border, color, typography, state.

### Responsive Design

- Mobile-first.
- Standard breakpoints: `sm`, `md`, `lg`, `xl`.
- Dashboard tables are desktop-first content but must remain accessible on mobile through safe horizontal overflow or condensed card rendering.
- Never hide critical score, package ID, or disclaimer merely to fit mobile.

### Dark Mode

- Dark mode is not P1 for v1.0.
- If added, use CSS variables/Tailwind `dark:` consistently.
- Test all charts, tables, focus states, and contrast in both themes.
- Do not partially implement dark mode.

### Design Tokens

- Define colors, spacing, radii, and typography through CSS variables/theme configuration.
- Do not hardcode arbitrary hex colors across components.
- Priority colors must not imply guilt. Use neutral analytical colors and text labels.
- Color cannot be the only signal; include text/icon/shape where needed.

### Accessibility

- Target WCAG 2.1 AA on primary flows.
- Use semantic headings and tables.
- Ensure keyboard navigation and visible focus.
- Provide chart summaries or accessible data tables.
- Use Indonesian number/currency formatting consistently.

---

## 9. API & Data Fetching Rules

### Server vs Client Fetch

- Use server-side fetch for initial dashboard, dataset, methodology, and detail pages.
- Use URL search parameters for shareable filters.
- Use client fetch only for interactions that need immediate updates without navigation.
- Use native `fetch`; do not add Axios, SWR, or React Query without a measured need.
- Never use `useEffect` for initial page data.

### Response Format

Use consistent typed responses. Example:

```json
{
  "data": {},
  "meta": {
    "dataset_version": "string",
    "model_version": "string",
    "generated_at": "ISO-8601",
    "filters": {}
  },
  "error": null
}
```

Error example:

```json
{
  "data": null,
  "meta": null,
  "error": {
    "code": "INVALID_FILTER",
    "message": "Pesan aman untuk pengguna"
  }
}
```

### API Error Handling

- Use correct status codes: 200, 400, 404, 422, 500, 503.
- Validate query parameters with Pydantic.
- Do not expose stack traces, local paths, secrets, or raw external API errors.
- Missing HPS/pagu is valid missing data, not automatically an API failure.
- Backend startup must fail clearly if required model/data artifacts are missing or incompatible.

### Fetch Function Location

- Typed frontend fetch functions belong in `frontend/lib/`.
- Do not call backend URLs directly inside presentation components.
- FastAPI routes belong in `backend/app/api/`; business logic belongs in `backend/app/services/`.

### Environment and URLs

- All deploy-specific URLs come from environment variables.
- Do not hardcode Vercel, VPS, or Cloudflare Tunnel URLs in application code.
- The INAPROC detail API base URL must be configurable for pipeline runs.

### Data Contract Rules

- Include dataset and model versions in ranking/detail/export responses.
- The anomaly score direction must be documented and consistent everywhere.
- A ranking response must include the disclaimer or a mandatory disclaimer identifier.
- CSV export must reflect active filters and ordering exactly.

---

## 10. State Management Rules

### State Hierarchy

1. Server-derived page data
2. URL search parameters for shareable filters/sort/pagination/Top-N
3. Local `useState` for transient UI state such as open menus
4. Lifted state for adjacent components
5. Global state only after a demonstrated cross-route requirement

### Global State

No global state manager is planned for v1.0. Do not install Redux, Zustand, Jotai, or similar libraries unless:

- state is required across unrelated routes;
- URL/server state cannot represent it;
- the user approves the dependency.

### Derived State

- Do not store data that can be derived from current API response or URL parameters.
- Do not duplicate filtered records in multiple stores.
- Use memoization only after profiling demonstrates a costly recalculation.

### Context

Use React Context only for stable cross-tree configuration such as theme or static app metadata. Do not use Context for rapidly changing ranking/filter data.

### Persistence

- No user-specific persistence is required in v1.0.
- Shareable filter state should use the URL, not localStorage.
- Do not persist model results in the browser as a source of truth.

---

## 11. Performance Rules

### Targets

- Backend summary/ranking API p95: under 1 second after warm-up on target VPS for v1.0 data.
- Frontend LCP: under 2.5 seconds on a normal connection.
- Filter interaction: no long main-thread blocking.
- Model training: CPU-only and reproducible; optimize only if measurements justify it.

### Code Splitting

- Use dynamic import for large client-only charts below the fold.
- Do not lazy-load small components solely for theoretical bundle savings.
- Keep methodology/data pages mostly server-rendered.

### Image Optimization

- Use Next.js `Image` for raster images.
- Set width and height.
- Prefer WebP/AVIF for new raster assets.
- SVG diagrams may be inline or served as static assets when safe.
- Do not use raw `<img>` for local application assets without a reason.

### Re-render Optimization

- Profile before adding `useMemo` or `useCallback`.
- Keep filter state close to usage.
- Avoid creating huge client-side copies of the full dataset if server filtering is sufficient.

### Bundle Size

- Import only required modules.
- Use one chart library.
- Do not ship Python/model artifacts to the frontend.
- Avoid general-purpose utility libraries for one or two functions.

### SSR, SSG, and Caching

- Default to Server Components.
- Use static generation or revalidation for methodology and stable dataset summaries.
- Use server-side dynamic rendering only where active query filters require it.
- Do not apply global `no-store` if data changes only when artifacts are redeployed.
- Cache versioned, immutable summary data safely.

### Data/Model Runtime

- Precompute rankings and explanations when possible instead of running Isolation Forest for every page request.
- Load compatible artifacts once per backend process.
- Use pagination; do not send every row to the initial dashboard.

---

## 12. Git Rules

### Current State

The project root uses Git with `main` as its default branch. Verify the current remote, status, branch, and recent commits before making Git or GitHub claims.

### Commit Policy

Do not automatically commit or push unless the user explicitly requests it. When requested:

```text
Format: type: subject
Maximum subject length: 72 characters
One logical task per commit
```

Allowed types:

- `feat`: new capability
- `fix`: bug correction
- `refactor`: behavior-preserving restructure/rename
- `style`: formatting/styling only
- `docs`: documentation only
- `test`: tests only
- `chore`: tooling/configuration

Examples:

```text
docs: define anomaly-ranking product requirements
feat: add resumable INAPROC enrichment pipeline
fix: preserve package identifiers as strings
```

### Pre-Commit Verification

Before every requested commit:

1. Inspect fresh `git status` and diff.
2. Verify task-specific tests/build/lint.
3. Scan staged files for secrets, tokens, credentials, and private endpoints.
4. Confirm raw datasets were not unintentionally modified.
5. Confirm generated artifacts are intentionally tracked or ignored.
6. Use one task per commit.
7. Stop on any blocker; never commit known failures.

### Additional Rules

- Never commit `.env`, credentials, API tokens, SSH material, or private server details.
- Keep `.gitignore` changes in a separate commit.
- Do not mix file rename and behavior changes in one commit.
- Do not force-push or rewrite history without explicit instruction.
- Never report a push/merge as successful without verifying the remote result.

---

## 13. Features

### Operational Source of Truth

`TASKS.md` is the only operational checklist. It contains ordered `TASK-ML-*`, `TASK-BE-*`, and `TASK-FE-*` work, dependencies, deliverables, acceptance criteria, verification, code-review gates, and release gates. Do not maintain a duplicate checkbox list here.

### Current Verified Baseline

- Thesis topic, v1.0 scope, and interpretation boundary are defined.
- DKI Jakarta completed-tender source datasets for 2024, 2025, and the partial 2026 snapshot are tracked.
- The merged dataset contains 1,279 rows and 1,277 unique package codes.
- The canonical dataset contains 1,277 package rows, one row per `kode_paket`.
- Initial manual audit identified five missing-supplier source rows and one multi-provider package code; canonicalization documents the five exclusions and marks package `10060212000` as `eligible_for_model=false`.
- `README.md`, `PRD.md`, `CLAUDE.md`, `AGENTS.md`, and `TASKS.md` define project, engineering, and execution rules.
- Git and the public GitHub repository are configured on `main`.
- Application, model, API, frontend, tests, containers, and deployment are not complete until their corresponding `TASKS.md` entries are checked.

### Task Completion Contract

- One task ID per logical change.
- Update the task checkbox only after task-specific checks, `verify-gate`, and required review pass.
- Use `software-development:requesting-code-review` for non-trivial code before completion.
- Use `ponytail-review` for medium/large changes and `github:github-code-review` for Pull Requests.
- Project commit format remains `type: subject`; ignore any review-skill suggestion to use a non-conventional commit prefix.

---

## 14. Testing

### Testing Approach

- **Python unit tests**: `pytest`
- **Python integration tests**: `pytest`, temporary files, mocked/local HTTP responses
- **Backend API tests**: FastAPI TestClient or HTTPX through pytest
- **Frontend unit/component tests**: Vitest + Testing Library after frontend exists
- **End-to-end tests**: Playwright after primary flows stabilize
- **Functional verification**: Black-box scenarios aligned with BAB 3/RAD requirements
- **Deployment verification**: HTTP smoke tests against public frontend and backend

Do not install all frameworks upfront. Add each when its first real test exists.

### Must Test

- Source schema validation and identifier preservation.
- Missing supplier/enrichment behavior.
- Duplicate and multi-provider package handling.
- Safe financial ratios for zero/null HPS or pagu.
- Date parsing and tender-duration calculations.
- Supplier frequency/share and HHI grouping context.
- Prevention of temporal leakage.
- Stable feature order and model artifact compatibility.
- Reproducibility for fixed seed/configuration.
- Score direction and Top-N ordering.
- Filter combination, pagination, detail lookup, and export ordering.
- API happy paths, invalid parameters, missing artifacts, and unavailable fields.
- Mandatory disclaimer presence in dashboard, detail, and export.
- Primary frontend accessibility and responsive behavior.

### Does Not Need Direct Testing

- scikit-learn, pandas, FastAPI, Next.js, or chart-library internals.
- Trivial presentational wrappers with no behavior.
- Static configuration files beyond syntax/schema validation.
- Third-party INAPROC service behavior; test our timeout, cache, retry, and parsing behavior instead.

### Test Writing Rules

- One focused test module per module/behavior group.
- Use descriptive names: `test_should_<expected>_when_<condition>`.
- Follow Arrange, Act, Assert.
- Keep fixtures small and representative; do not copy the full production CSV into tests.
- Test one edge-case-correct path for each non-trivial transformation.
- No network access in normal unit tests.
- Integration tests using live INAPROC must be explicit and opt-in.

### Coverage Target

- Target minimum: 80% for Python domain/pipeline/backend business logic.
- Prioritize transformation correctness, model artifact contracts, and API behavior over a vanity global percentage.
- Frontend priority: critical flows and interactive components, not every static paragraph.

### Release Gates

Before finalizing any implementation task, run the smallest relevant check. Before v1.0 release, run:

1. Python lint/format check
2. Python unit and integration tests
3. Frontend lint, tests, and production build
4. API contract/integration tests
5. E2E primary flow
6. Docker build and health check
7. Public deployment smoke test
8. Secret scan and artifact/version consistency check

---

## 15. Do Not

If a prompt is materially ambiguous and different interpretations would change data, model, architecture, or scope, ask before coding. For low-risk details with an obvious default, use the PRD and existing patterns.

```text
# Structure and Files
- Do not delete or overwrite raw datasets.
- Do not move current data files without a verified migration and updated references.
- Do not create unapproved top-level directories.
- Do not scaffold empty layers or boilerplate.
- Do not edit thesis documents under the outer Skripsi/docs folder unless explicitly requested.

# Data and Research
- Do not claim 2026 is a complete year.
- Do not silently drop, impute, deduplicate, normalize, or merge records.
- Do not convert package identifiers to numeric values.
- Do not treat missing HPS/pagu as zero.
- Do not use future-year aggregates to score historical records.
- Do not report sample API coverage as full-dataset coverage.
- Do not fabricate labels, metrics, expert validation, API responses, or research results.

# Model
- Do not call a high score proof of fraud/corruption/collusion.
- Do not use accuracy, precision, recall, F1, or confusion matrix as primary metrics without validated labels.
- Do not hardcode a Top-N or contamination value without experiment evidence and documentation.
- Do not show SHAP explanations unless their relationship to the Isolation Forest score is verified.
- Do not retrain the model on every API request.

# Code
- Do not use TypeScript any.
- Do not hardcode deployment URLs, secrets, or machine-specific paths in runtime code.
- Do not add dependencies without confirmation.
- Do not add a database, ORM, auth, queue, microservice, or state manager without a demonstrated requirement.
- Do not use useEffect for initial data fetching.
- Do not suppress errors or return fake fallback data that looks real.

# UI
- Do not place wide tables in half-width grid columns.
- Do not duplicate the same data across multiple tables/charts.
- Do not expose raw JSON or stack traces to users.
- Do not use accusatory labels or alarming colors without neutral context.
- Do not omit loading, empty, error, and unavailable-data states.

# Git and Security
- Do not commit or push without explicit user instruction.
- Do not commit .env files, credentials, tokens, private hostnames, or SSH material.
- Do not modify production data or remote infrastructure without confirming scope.
- Do not report success without verifying the actual result.
```

---

## 16. Environment Variables

### Setup

- Backend/pipeline: copy `.env.example` to `.env` only after `.env.example` exists.
- Frontend: use `frontend/.env.local` for local public configuration.
- Never commit `.env`, `.env.local`, secrets, tokens, or private endpoints.
- Validate required environment variables at process startup.

### Public Frontend Variables

```text
NEXT_PUBLIC_API_BASE_URL     # Public FastAPI base URL exposed through Cloudflare Tunnel
NEXT_PUBLIC_APP_VERSION      # Optional displayed application version; not a secret
```

Only variables prefixed with `NEXT_PUBLIC_` may be referenced by browser code. Never place secrets there.

### Server-Only Backend/Pipeline Variables

```text
INAPROC_DETAIL_API_BASE_URL  # Package-detail API base URL; may contain {kode_paket} or accept kode_paket query
INAPROC_REQUEST_TIMEOUT_S    # Per-request timeout for enrichment
INAPROC_MAX_RETRIES          # Bounded retry count
INAPROC_REQUEST_DELAY_S      # Polite delay/rate control between requests
RAW_DATA_DIR                 # Raw source/snapshot directory
PROCESSED_DATA_DIR           # Canonical/enriched dataset directory
ARTIFACT_DIR                 # Model and feature-schema artifact directory
MODEL_ARTIFACT_PATH          # Isolation Forest pipeline artifact
RANKING_DATA_PATH            # Precomputed ranking/explanation artifact
CORS_ORIGINS                 # Explicit allowed frontend origins
LOG_LEVEL                    # Application logging level
```

### Database Variables

```text
DATABASE_URL                 # Not used in v1.0; do not introduce without approved need
```

### Auth Variables

```text
AUTH_SECRET                  # Not used in v1.0
AUTH_URL                     # Not used in v1.0
OAUTH_CLIENT_ID              # Not used in v1.0
OAUTH_CLIENT_SECRET          # Not used in v1.0
```

Authentication is out of scope. These placeholders remain documented because the original template contains an auth-variable section; they must not be configured or implemented for v1.0.

### Secret Handling

- `.env.example` contains names and safe placeholders only.
- Logs must not print secret values.
- Cloudflare credentials belong in deployment secret storage, not the repository.
- Vercel environment configuration must be set through Vercel project settings/CLI secret handling.
- Use separate local and production values.

---

_This file remains a living engineering contract. Update it only when code, dependencies, commands, architecture, or verified project status changes. Product scope changes belong in `PRD.md` first._
