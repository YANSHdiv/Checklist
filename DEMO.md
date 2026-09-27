# Release Checklist — 3–4 Minute Demo Plan

This guide provides the exact script, on-screen actions, and real benchmarks to present in your 3–4 minute walkthrough video.

---

## Video Timeline & Script

### `0:00 – 0:30` | Introduction & Architecture
- **Voiceover**:
  > "Hi everyone! This is the Release Checklist application—a modern single-page application built to automate software release tracking and eliminate state synchronization bugs.
  > The frontend is built in React 19, TypeScript, and Vite with Apollo Client. It communicates exclusively through GraphQL to a Python 3.12 FastAPI backend powered by Strawberry GraphQL. Data is persisted in PostgreSQL using SQLAlchemy 2.0 with native JSONB step tracking. The entire stack is containerized with Docker and Docker Compose."
- **Visual**:
  - Show the project README or the architecture diagram:
    `React Frontend (Apollo Client) ──GraphQL /graphql──▶ FastAPI (Strawberry) ──SQLAlchemy 2.0──▶ PostgreSQL 16`

---

### `0:30 – 1:15` | Frontend Walkthrough & Automatic Status Rules
- **Voiceover**:
  > "Let's open the frontend. Notice the clean dashboard showing planned, ongoing, and done releases.
  > Let's create a new release: 'v2.5.0 Production Launch' with due date and deployment instructions.
  > Notice the status immediately defaults to 'planned' because 0 steps are checked.
  > When we check off the first step—'Code freeze'—the status automatically transitions to 'ongoing' in real time.
  > As we check off subsequent steps, the progress bar updates seamlessly.
  > When all 10 canonical steps are completed, the status computes to 'done'. Status is strictly derived from completed steps in backend logic, preventing manual user error."
- **Visual**:
  - Click **"+ New Release"**.
  - Fill Name: `v2.5.0 Production Launch`, pick Due Date, click **"Create Release"**.
  - Show status badge: `PLANNED` (0/10).
  - Check `1. Code freeze` -> Badge flips to `ONGOING` (1/10).
  - Toggle steps until 10/10 -> Badge flips to `DONE` (10/10).
  - Edit **Additional Information** notes inline and click **Save**.

---

### `1:15 – 2:00` | GraphQL Verification & Schema Inspection
- **Voiceover**:
  > "The frontend uses purely GraphQL without any REST CRUD endpoints.
  > Let's open the GraphQL interactive endpoint at `/graphql`.
  > We can query all releases, request only the fields we need, and query specific releases by UUID.
  > We can execute the `toggleStep` mutation directly and observe that the response returns the updated release with the re-computed status and timestamp."
- **Visual**:
  - Open browser tab at `http://localhost:8000/graphql`.
  - Execute Query:
    ```graphql
    query {
      releases {
        id
        name
        status
        completedSteps
      }
    }
    ```
  - Execute Mutation:
    ```graphql
    mutation {
      toggleStep(releaseId: "<RELEASE_UUID>", stepId: 2) {
        id
        status
        completedSteps
      }
    }
    ```
  - Open browser DevTools Network tab on the React app to show `POST /graphql` requests on checkbox clicks.

---

### `2:00 – 2:40` | Baseline Load Test & Breaking Point Demonstration
- **Voiceover**:
  > "Now let's examine the performance experiments.
  > In our initial baseline implementation, the backend ran on a single Uvicorn worker process with a conservative SQLAlchemy connection pool of 5 connections and 5 overflow.
  > We used Locust to execute headless stress tests with realistic traffic across increasing loads: 50, 100, 150, 200, 300, and 500 concurrent users.
  > While the baseline handled 50 to 100 users reasonably, at 150 users throughput plateaued.
  > At 200 users, throughput collapsed from 284 RPS down to 172 RPS as queue wait times inflated to 1,400 ms.
  > At 300 users, we reached the actual breaking point: 246 requests were dropped with a 9.18% failure rate, and 95th percentile latency reached the 5.0-second timeout ceiling.
  > At 500 users, the system experienced catastrophic failure with a 32.37% dropped request rate."
- **Visual**:
  - Show the terminal or Locust dashboard output for the Baseline test:
    ```
    SUMMARY TABLE FOR BASELINE:
    | Users | RPS   | Avg Latency | P95 Latency | Failures | Failure % |
    | 50    | 191.5 | 63.5 ms     | 100.0 ms    | 0        | 0.0%      |
    | 100   | 284.1 | 147.2 ms    | 320.0 ms    | 0        | 0.0%      |
    | 150   | 236.2 | 414.7 ms    | 690.0 ms    | 0        | 0.0%      |
    | 200   | 172.8 | 895.9 ms    | 1,400.0 ms  | 0        | 0.0%      |
    | 300   | 139.9 | 1,758.9 ms  | 5,000.0 ms  | 246      | 9.18% ❌   |
    | 500   | 148.4 | 2,753.6 ms  | 5,300.0 ms  | 921      | 32.37% ❌  |
    ```

---

### `2:40 – 3:20` | Root Cause Analysis & Optimizations
- **Voiceover**:
  > "Why did this bottleneck happen?
  > 1. Process Starvation: A single Uvicorn event loop was constrained by Python's GIL while executing synchronous GraphQL resolvers in anyio thread pools.
  > 2. Connection Pool Checkout Contention: 300 concurrent requests were contending for only 10 total database connections, triggering pool timeout errors.
  > 3. Unindexed Sorting: `ORDER BY created_at DESC` forced sequential table scans and in-memory sorts on every query.
  > To solve this, we implemented four concrete optimizations:
  > - Configured 4 multi-worker processes using `uvloop` and `httptools` in Docker.
  > - Sized the connection pool to 50 connections across workers, paired with `max_connections=300` in PostgreSQL.
  > - Added a B-tree index on `created_at DESC`.
  > - Injected a single request-scoped database session directly into Strawberry's context getter."
- **Visual**:
  - Show the diffs in `docker-compose.yaml` (`WORKERS: 4`, `DB_POOL_SIZE: 25`), `models.py` (`Index("ix_releases_created_at_desc")`), and `main.py` (`get_graphql_context`).

---

### `3:20 – 4:00` | Optimized Benchmark Results & Final Verdict
- **Voiceover**:
  > "We then re-ran the exact same Locust test suite against the optimized configuration.
  > Look at the transformation:
  > At 200 users, throughput nearly doubled from 172.8 RPS to 328.8 RPS, and P95 latency dropped by 58% from 1,400 ms down to 590 ms.
  > Most importantly, at 300 users—where the baseline experienced 246 dropped requests and a 9.18% failure rate—the optimized system achieved 100% success with 0 failures, 297.7 RPS, and a sub-second P95 of 1,000 ms.
  > The sustainable concurrency limit increased from 200 users to over 300 users, successfully eliminating the failure point."
- **Visual**:
  - Show the before/after comparison table:
    ```
    | Metric                     | Baseline (1 Worker, Pool=10) | Optimized (4 Workers, Pool=50) | Improvement       |
    |:---------------------------|:-----------------------------|:-------------------------------|:------------------|
    | Sustainable Concurrency    | 200 users                    | 300+ users                     | +50% user load    |
    | Throughput @ 200 users     | 172.8 RPS                    | 328.8 RPS                      | +90.3% throughput |
    | Throughput @ 300 users     | 139.9 RPS                    | 297.7 RPS                      | +112.8% (>2x RPS) |
    | Failures @ 300 users       | 246 (9.18%)                  | 0 (0.00%)                      | 100% eliminated   |
    | P95 Latency @ 200 users    | 1,400 ms                     | 590 ms                         | -57.9% faster     |
    | P95 Latency @ 300 users    | 5,000 ms (timeout)           | 1,000 ms                       | -80.0% faster     |
    ```
  - End with the live, passing pytest test suite (`6 passed in 2.4s`).
