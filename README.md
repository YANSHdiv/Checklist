# Release Checklist Application

A modern, responsive, single-page software release management application. It provides engineering teams with an automated, reliable checklist workflow for coordinating software release cycles, tracking step completions in real-time, calculating delivery status, and managing release notes across desktop, tablet, and mobile devices.

---

## Architecture Overview

The system is architected as a clean, decoupled Single Page Application (SPA) powered by a GraphQL API and PostgreSQL database:

```
┌──────────────────────────────────────────────┐
│        Frontend (React 19 + TypeScript)      │
│     Apollo Client, Responsive CSS & Icons    │
└──────────────────────┬───────────────────────┘
                       │ HTTP POST /graphql
                       ▼
┌──────────────────────────────────────────────┐
│        Backend API (FastAPI + Strawberry)    │
│    Python 3.12, Uvicorn, Lifespan, CORS      │
└──────────────────────┬───────────────────────┘
                       │ SQLAlchemy 2.0 (psycopg)
                       ▼
┌──────────────────────────────────────────────┐
│          PostgreSQL Database (v16)           │
│   Single `releases` table with JSONB array   │
└──────────────────────────────────────────────┘
```

- **Frontend**: Built with React 19, TypeScript, and Vite. Leverages Apollo Client for GraphQL queries, mutations, cache normalization, and immediate UI state feedback.
- **Backend API**: Built with Python 3.12 and FastAPI. GraphQL schema and resolvers are implemented with Strawberry GraphQL. Database access is handled via modern SQLAlchemy 2.0 with connection pooling and PostgreSQL native types.
- **Database**: PostgreSQL 16 storing release entities with JSONB step tracking and indexed timestamp ordering.

---

## Features

- **Release Dashboard**: Comprehensive overview of all software releases with instant status badges (`planned`, `ongoing`, `done`).
- **Dynamic Status Automation**: Status is strictly computed from checklist progress—eliminating state synchronization bugs and manual user error:
  - `0 completed steps` → `planned`
  - `1–9 completed steps` → `ongoing`
  - `10 completed steps` → `done`
- **Interactive Checklist**: 10 canonical release steps (Code Freeze, Automated Tests, Security Checks, Staging Deploy, Smoke Tests, Production Verification, etc.) with real-time toggle mutations.
- **Additional Information**: Inline editable release notes, deployment plans, and rollback instructions saved instantly through GraphQL.
- **Modal Workflows**: Fast, accessible modal dialogs for creating new releases with date/time pickers and destructive delete confirmations.
- **Full Responsiveness**: Mobile-first design that adapts seamlessly from handheld touchscreens to wide desktop monitors.
- **Automated Testing Suite**: Pytest suite validating model integrity, business rules, status progressions, and GraphQL resolvers.
- **Containerized**: Fully Dockerized with `backend/Dockerfile` and `docker-compose.yaml` for 1-command startup.
- **Empirical Stress Testing**: Locust benchmark testing real GraphQL traffic under 50 and 150 concurrent users before and after targeted performance optimizations.

---

## Tech Stack

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite | Fast HMR, type safety, minimal bundle overhead |
| **Data Layer** | Apollo Client 4, GraphQL | Declarative queries, normalized cache, precise field queries |
| **Backend** | Python 3.12, FastAPI, Strawberry GraphQL | Asynchronous ASGI speed, Python type hint schema mapping |
| **ORM & DB Driver** | SQLAlchemy 2.0, psycopg 3 (binary) | Battle-tested session lifecycle, native pooling, async/sync consistency |
| **Database** | PostgreSQL 16 | ACID transactions, native JSONB support, robust indexing |
| **Testing** | pytest, pytest-asyncio, httpx | Fast in-memory unit and integration test coverage |
| **Benchmarking**| Locust | Realistic concurrent headless load and latency distribution measurement |
| **Deployment** | Vercel (Frontend), Render (API), Neon/Supabase/Render Postgres | Serverless edge frontend, managed containers, high availability database |

---

## Database Schema

Per system specifications, all release data is consolidated into a single primary table to avoid complex multi-table joins and locking contention:

```sql
CREATE TABLE releases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    additional_info TEXT NULL,
    completed_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Optimization B-Tree Index for sorted release retrieval
CREATE INDEX ix_releases_created_at_desc ON releases (created_at DESC);
CREATE INDEX ix_releases_name ON releases (name);
```

### Explanation of `completed_steps JSONB`
Rather than introducing a separate `steps` table with 10 rows per release and expensive foreign key joins, completed steps are stored as a compact JSONB array of completed step IDs (e.g. `[1, 2, 5]`). The 10 fixed checklist items are stored as immutable constants in code:
1. Code freeze
2. Run automated tests
3. Review changelog
4. Update documentation
5. Run security checks
6. Build production bundle
7. Deploy to staging
8. Run smoke tests
9. Deploy to production
10. Verify production

---

## GraphQL API Reference

Endpoint: `POST /graphql` (Interactive GraphQL IDE available at `http://localhost:8000/graphql`)

### Queries

#### 1. `releases`
Retrieves all releases ordered by creation date.
```graphql
query GetReleases {
  releases {
    id
    name
    dueDate
    status
    additionalInfo
    completedSteps
    createdAt
    updatedAt
  }
}
```

#### 2. `release(id: UUID!)`
Fetches a single release by UUID.
```graphql
query GetRelease($id: UUID!) {
  release(id: $id) {
    id
    name
    dueDate
    status
    additionalInfo
    completedSteps
  }
}
```

#### 3. `steps`
Lists the fixed checklist step definitions.
```graphql
query GetSteps {
  steps {
    id
    title
  }
}
```

### Mutations

#### 1. `createRelease(input: CreateReleaseInput!)`
Creates a new release record. Status defaults to `planned`.
```graphql
mutation CreateRelease($input: CreateReleaseInput!) {
  createRelease(input: $input) {
    id
    name
    dueDate
    status
    additionalInfo
    completedSteps
  }
}

# Variables
{
  "input": {
    "name": "v2.5.0 - Billing Engine Launch",
    "dueDate": "2026-10-15T18:00:00Z",
    "additionalInfo": "Requires DB migration during low-traffic window."
  }
}
```

#### 2. `toggleStep(releaseId: UUID!, stepId: Int!)`
Toggles a step ID (1–10) in `completed_steps` and recalculates status automatically.
```graphql
mutation ToggleStep($releaseId: UUID!, $stepId: Int!) {
  toggleStep(releaseId: $releaseId, stepId: $stepId) {
    id
    status
    completedSteps
    updatedAt
  }
}
```

#### 3. `updateRelease(input: UpdateReleaseInput!)`
Updates release name, due date, or additional notes.
```graphql
mutation UpdateRelease($input: UpdateReleaseInput!) {
  updateRelease(input: $input) {
    id
    name
    additionalInfo
    updatedAt
  }
}
```

#### 4. `deleteRelease(id: UUID!)`
Deletes a release. Returns `true` if deleted.
```graphql
mutation DeleteRelease($id: UUID!) {
  deleteRelease(id: $id)
}
```

---

## Design Decisions

1. **Why No Steps Table?**
   Checklist steps are fixed and universal across all releases (10 standard deployment milestones). Storing steps as relational rows would require 10 rows per release (1,000 releases = 10,000 step rows) with joins, foreign keys, and multi-row locks during step updates. Using a JSONB array in the `releases` table allows single-row atomic updates, zero join overhead, and millisecond writes.

2. **Why Compute Status Instead of Storing as User Input?**
   Allowing users to manually select "Done" while steps remain uncompleted introduces state inconsistencies. Computing status purely from `completed_steps` (`0` -> `planned`, `1..9` -> `ongoing`, `10` -> `done`) guarantees single-source-of-truth integrity.

3. **Why GraphQL?**
   GraphQL allows client-driven payload selection (the dashboard cards can request only the fields they need, while detail views can fetch full metadata), provides built-in schema introspection and type generation, and consolidates operations into a single predictable endpoint.

4. **Why PostgreSQL?**
   PostgreSQL provides superior native JSONB indexing, atomic array manipulation, and ACID consistency under concurrent write traffic.

5. **Deployment Architecture**
   Vercel edge static hosting for the React frontend ensures global low-latency CDN delivery. Render managed container hosting for the FastAPI backend paired with PostgreSQL gives instant container deployment, zero DevOps overhead, and scalable worker allocation.

---

## Local Setup & Development

### Prerequisites
- Python 3.11+ or Python 3.12
- Node.js 18+ and npm
- Docker & Docker Compose (optional for containerized run)

### Running Locally with Docker Compose (Recommended)

Start PostgreSQL and the FastAPI backend in Docker:
```bash
docker compose up -d --build
```
Verify the backend is healthy:
```bash
curl http://localhost:8000/health
# Output: {"status":"healthy","database":"connected"}
```

Start the frontend development server:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

### Running Locally Without Docker

#### Backend:
```bash
cd backend
python -m venv .venv
# Windows:
.\.venv\Scripts\pip install -r requirements.txt
# Linux/macOS:
source .venv/bin/activate && pip install -r requirements.txt

# Start API server (defaults to local SQLite if no DATABASE_URL set)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables

### Backend (`backend/.env`)
| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+psycopg://user:pass@localhost:5432/release_db` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173,https://your-frontend.vercel.app` |
| `PORT` | Web server port | `8000` |

### Frontend (`frontend/.env`)
| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `VITE_GRAPHQL_URL` | Full URL to GraphQL endpoint | `http://localhost:8000/graphql` |

---

## Automated Tests

Run the backend test suite:
```bash
cd backend
.\.venv\Scripts\pytest -v
```
**Test Results**:
```
tests/test_api.py::test_status_computation_unit PASSED                   [ 16%]
tests/test_api.py::test_health_check PASSED                              [ 33%]
tests/test_api.py::test_create_and_query_release PASSED                  [ 50%]
tests/test_api.py::test_toggle_step_and_status_progression PASSED        [ 66%]
tests/test_api.py::test_update_and_delete_release PASSED                 [ 83%]
tests/test_api.py::test_validation_and_bounds PASSED                     [100%]

======================== 6 passed in 1.45s =========================
```

---

## Empirical Performance & Stress Testing

We conducted real-world load testing using Locust against the GraphQL API. The workload simulated realistic user interactions:
- Dashboard querying (`releases` query, weight 5)
- Step toggling (`toggleStep` mutation, weight 3)
- Single release inspection (`release` query, weight 2)
- Note updates (`updateRelease` mutation, weight 1)
- Full lifecycle creation and cleanup (`createRelease` -> `deleteRelease`, weight 1)

### Baseline Bottlenecks Identified

During initial baseline testing with 150 concurrent users:
1. **Server Worker Starvation**: The backend ran with a single Uvicorn process (`workers=1`). The single Python GIL event loop queue became saturated under high concurrency.
2. **SQLAlchemy Connection Pool Starvation**: Default pool (`pool_size=10, max_overflow=20`) capped concurrent checkouts at 30 connections. Requests queued waiting for available database handles, inflating latency past 9 seconds.
3. **Missing Indexing on Release Ordering**: Every dashboard query ran `ORDER BY created_at DESC` without an index on `created_at`, forcing full sequential table scans and sorts as releases accumulated.
4. **Session Lifecycle Inefficiency**: Resolvers opened separate session context managers within each query rather than sharing a request-scoped session.

### Concrete Optimizations Performed

1. **Multi-Worker Process Scaling**: Configured production Uvicorn with `--workers 4 --loop uvloop --http httptools` in Docker to distribute incoming load across CPU cores.
2. **High-Concurrency Connection Pooling**: Upgraded connection pool in `database.py`:
   - `pool_size = 50`
   - `max_overflow = 50`
   - `pool_timeout = 15s`
   - `pool_recycle = 1800s`
3. **Database Indexing**: Added a B-tree index on `created_at DESC` (`ix_releases_created_at_desc`) in `Release` model to achieve $O(\log N)$ sorted scans.
4. **FastAPI Request-Scoped Session Injection**: Injected a single request-scoped database session directly into Strawberry GraphQL's `context_getter`, eliminating redundant connection checkouts per resolver.
5. **Fast-Path Status Calculation**: Optimized `compute_status` to bypass redundant `set()` allocations when step lists are empty or fully populated.

---

### Before vs. After Benchmark Results

All measurements below are **actual observed results** from running the Locust suite for 30 seconds at 50 and 150 concurrent users:

#### Load Level: 50 Concurrent Users
| Metric | Baseline (Single Worker, Pool=10) | Optimized (4 Workers, Pool=50, Index) | Improvement |
| :--- | :--- | :--- | :--- |
| **Total Requests Served** | 3,542 | **3,990** | **+12.6%** |
| **Throughput (RPS)** | 120.5 req/s | **135.6 req/s** | **+12.5%** |
| **Average Latency** | 112 ms | **67 ms** | **-40.2%** |
| **Median Latency (50%)** | 100 ms | **64 ms** | **-36.0%** |
| **95th Percentile** | 240 ms | **130 ms** | **-45.8%** |
| **99th Percentile** | 320 ms | **190 ms** | **-40.6%** |
| **Failure Rate** | 0.00% | **0.00%** | 0 failures |

#### Load Level: 150 Concurrent Users (Stress Scenario)
| Metric | Baseline (Single Worker, Pool=10) | Optimized (4 Workers, Pool=50, Index) | Improvement |
| :--- | :--- | :--- | :--- |
| **Total Requests Served** | 2,757 | **5,459** | **+98.0% (~2x capacity)** |
| **Throughput (RPS)** | 93.6 req/s | **184.3 req/s** | **+96.9% throughput** |
| **Average Latency** | 1,198 ms | **482 ms** | **-59.8% faster** |
| **Median Latency (50%)** | 1,300 ms | **480 ms** | **-63.1% faster** |
| **95th Percentile** | 1,600 ms | **810 ms** | **-49.4% faster** |
| **99th Percentile** | 5,500 ms | **940 ms** | **-82.9% faster** |
| **Max Latency** | 9,823 ms | **1,266 ms** | **-87.1% faster** |

---

## Deployment Guide

The application is architected and configured for zero-friction cloud deployment.

### 1. Database (Neon / Supabase / Render PostgreSQL)
1. Create a free PostgreSQL instance on [Neon](https://neon.tech), [Supabase](https://supabase.com), or [Render](https://render.com).
2. Copy the connection string. Example:
   `postgresql+psycopg://user:password@ep-sample.neon.tech/release_db?sslmode=require`

### 2. Backend API (Render)
1. Link this repository to [Render](https://render.com).
2. Use either the included `render.yaml` Blueprint or create a **Web Service**:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4`
   - **Environment Variables**:
     - `DATABASE_URL`: Your hosted PostgreSQL connection string
     - `CORS_ORIGINS`: `*` (or your Vercel frontend URL)
     - `PYTHON_VERSION`: `3.12.4`
3. Health Check Path: `/health`

### 3. Frontend (Vercel)
1. Import this repository in [Vercel](https://vercel.com).
2. Set **Root Directory** to `frontend`.
3. Framework Preset: **Vite**.
4. Configure Environment Variable:
   - `VITE_GRAPHQL_URL`: `https://<YOUR-RENDER-API-URL>/graphql`
5. Click **Deploy**.

### Production Endpoints

| Resource | Production URL |
| :--- | :--- |
| **Frontend** | `https://release-checklist-delta.vercel.app` *(deploy your Vercel project)* |
| **Backend Health** | `https://release-checklist-api.onrender.com/health` |
| **GraphQL Endpoint** | `https://release-checklist-api.onrender.com/graphql` |

---

## Project Structure

```
c:\Users\div18\Desktop\Checklist\
├── .gitignore
├── docker-compose.yaml               # Docker Compose: PostgreSQL & multi-worker FastAPI backend
├── render.yaml                       # Infrastructure-as-code blueprint for Render
├── README.md                         # Architecture, schema, API docs, and benchmarks
│
├── backend/
│   ├── .dockerignore
│   ├── .env.example
│   ├── Dockerfile                    # Multi-worker production image with uvloop/httptools
│   ├── pytest.ini                    # Pytest configuration
│   ├── requirements.txt              # FastAPI, Strawberry, SQLAlchemy, psycopg, Locust
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py               # Engine configuration, high-concurrency pool, lifecycle
│   │   ├── graphql.py                # Strawberry GraphQL types, queries, mutations, context
│   │   ├── main.py                   # FastAPI application, CORS, health endpoint
│   │   ├── models.py                 # SQLAlchemy Release model, JSONB steps, indexing
│   │   └── services.py               # Release CRUD operations and status logic
│   └── tests/
│       └── test_api.py               # Automated pytest suite
│
├── frontend/
│   ├── .env.example
│   ├── .gitignore
│   ├── index.html                    # HTML shell
│   ├── package.json
│   ├── tsconfig.json
│   ├── vercel.json                   # SPA routing rewrites for Vercel
│   ├── vite.config.ts
│   └── src/
│       ├── App.css                   # Custom responsive design system
│       ├── App.tsx                   # Main stateful dashboard component
│       ├── main.tsx                  # React DOM entrypoint with ApolloProvider
│       ├── types.ts                  # Release, Step, and Status TypeScript definitions
│       ├── components/
│       │   ├── CreateReleaseModal.tsx # New release creation form modal
│       │   ├── DeleteConfirmModal.tsx # Destructive action confirmation modal
│       │   ├── Header.tsx            # Header with branding and summary metrics
│       │   └── ReleaseCard.tsx       # Release card with interactive checklist & note editor
│       └── graphql/
│           ├── client.ts             # Apollo Client setup with cache policy
│           └── queries.ts            # GraphQL queries, mutations, and fragments
│
└── stress-test/
    ├── locustfile.py                 # Headless GraphQL user simulation scenario
    ├── baseline_50_stats.csv         # 50 users baseline benchmark results
    ├── baseline_150_stats.csv        # 150 users baseline benchmark results
    ├── optimized_50_stats.csv        # 50 users optimized benchmark results
    └── optimized_150_stats.csv       # 150 users optimized benchmark results
```
