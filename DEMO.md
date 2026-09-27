# Release Checklist — 3–4 Minute Demo Video Plan

This guide provides the exact script, on-screen actions, and real benchmark numbers to present in your 3–4 minute walkthrough video.

---

## Video Timeline & Script

### `0:00 – 0:30` | Overview & Architecture
- **Voiceover**:
  > "Hi everyone! This is the Release Checklist application—a modern single-page application built to coordinate software releases and eliminate state synchronization bugs.
  > The frontend is built in React 19, TypeScript, and Vite with Apollo Client. It communicates exclusively through GraphQL to a Python 3.12 FastAPI backend powered by Strawberry GraphQL. Data is persisted in PostgreSQL using SQLAlchemy 2.0 with native JSONB step tracking. The entire stack is containerized with Docker and Docker Compose."
- **Visual**:
  - Show the running application on screen.
  - Briefly show the architecture diagram:
    `React Frontend (Apollo Client) ──POST /graphql──▶ FastAPI (Strawberry) ──SQLAlchemy 2.0──▶ PostgreSQL 16`

---

### `0:30 – 1:20` | Core Functional Walkthrough
- **Voiceover**:
  > "Let's create a release: 'v2.5.0 Production Launch' with a target due date and deployment instructions.
  > Notice the status immediately defaults to 'planned' because 0 steps are completed.
  > When we check off the first step—'Code freeze'—the status automatically transitions to 'ongoing' in real time.
  > As we check off subsequent steps, the progress bar updates seamlessly.
  > When all 10 canonical steps are completed, the status transitions to 'done'. Status is strictly computed from completed steps in backend business logic and cannot be manually edited by users.
  > We can also edit additional information inline and save it directly via GraphQL, or delete a release with confirmation."
- **Visual**:
  - Click **"+ New Release"**.
  - Fill Name: `v2.5.0 Production Launch`, pick Due Date, enter additional info, click **"Create Release"**.
  - Point out badge: `PLANNED` (0/10).
  - Check `1. Code freeze` -> Badge flips to `ONGOING` (1/10).
  - Toggle remaining steps to 10/10 -> Badge flips to `DONE` (10/10).
  - Click **"Edit"** on Additional Information, change text, and click **"Save"**.
  - Click the **trash icon** on a release to display the Delete Confirmation modal.

---

### `1:20 – 2:00` | GraphQL API Verification
- **Voiceover**:
  > "The application uses purely GraphQL for all frontend/backend communication.
  > Let's open the GraphQL interactive endpoint at `/graphql`.
  > We can run the `releases` query to fetch all releases, or fetch single releases by UUID.
  > Let's run the `toggleStep` mutation directly. Notice that the mutation returns the updated release entity with the automatically re-calculated status.
  > In the browser DevTools Network tab, you can verify that all checkbox interactions and form submissions send `POST /graphql` requests."
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
      toggleStep(releaseId: "<RELEASE_UUID>", stepId: 1) {
        id
        status
        completedSteps
      }
    }
    ```
  - Open DevTools Network tab on the React frontend to show `POST /graphql` payloads.

---

### `2:00 – 2:40` | Baseline Load Test & Breaking Point
- **Voiceover**:
  > "Now let's examine the performance experiments.
  > In our initial baseline implementation, the backend ran on a single Uvicorn worker process with a limited connection pool of 5 connections and 5 overflow.
  > We used Locust to execute headless stress tests with realistic traffic across increasing loads: 50, 100, 150, 200, 300, and 500 concurrent users.
  > Up to 200 concurrent users, the baseline succeeded with 0 failures, but latency degraded sharply to 895 ms and throughput dropped from 284 down to 172 RPS.
  > At 300 users, we reached the actual breaking point: 246 requests timed out and failed, producing a 9.18% failure rate, with P95 latency hitting the 5.0-second timeout ceiling.
  > At 500 users, the system experienced severe collapse with a 32.37% failure rate."
- **Visual**:
  - Display the Baseline Summary Table:
    ```
    SUMMARY TABLE FOR BASELINE:
    | Concurrent Users | RPS   | Avg Latency | P95 Latency | Failures | Failure % |
    | 50               | 191.5 | 63.5 ms     | 100.0 ms    | 0        | 0.0%      |
    | 100              | 284.1 | 147.2 ms    | 320.0 ms    | 0        | 0.0%      |
    | 150              | 236.2 | 414.7 ms    | 690.0 ms    | 0        | 0.0%      |
    | 200              | 172.8 | 895.9 ms    | 1,400.0 ms  | 0        | 0.0%      |
    | 300              | 139.9 | 1,758.9 ms  | 5,000.0 ms  | 246      | 9.18% ❌   |
    | 500              | 148.4 | 2,753.6 ms  | 5,300.0 ms  | 921      | 32.37% ❌  |
    ```

---

### `2:40 – 3:20` | Root Causes & Concrete Optimizations
- **Voiceover**:
  > "Based on our observations, what were the actual bottlenecks?
  > 1. Single-worker application saturation: All GraphQL AST parsing and event loop handling queued behind a single process.
  > 2. Connection pool checkout contention: 300 concurrent requests were contending for only 10 total database handles, causing pool timeouts.
  > 3. Database connection limits: PostgreSQL's default limit of 100 connections must be matched to worker pools to prevent connection refusal.
  > 4. Unindexed ordering: Queries sorted by `created_at DESC` without an index.
  > To solve this, we implemented concrete optimizations:
  > - Scaled Uvicorn to 4 worker processes with `uvloop` and `httptools`.
  > - Configured per-worker `pool_size=25, max_overflow=25` (up to 200 connections across workers) and set PostgreSQL's `max_connections=300`.
  > - Added a B-tree index on `created_at DESC`.
  > - Injected a single request-scoped database session directly into Strawberry's context getter.
  > - Bounded the default release query payload to 100 items."
- **Visual**:
  - Show the diffs in `docker-compose.yaml` (`WORKERS: 4`, `DB_POOL_SIZE: 25`, `max_connections=300`), `backend/app/models.py` (`Index("ix_releases_created_at_desc")`), and `backend/app/main.py` (`get_graphql_context`).

---

### `3:20 – 4:00` | Optimized Benchmark Results & Final Capacity
- **Voiceover**:
  > "We then re-ran the exact same Locust test suite against the optimized configuration.
  > At 200 users, throughput surged from 172.8 RPS to 328.8 RPS (+90.3%), and P95 latency dropped by 58% down to 590 ms.
  > At 300 users—where the baseline experienced 246 dropped requests and a 9.18% failure rate—the optimized system achieved 100% success with 0 failures, 297.7 RPS, and a 1.0-second P95.
  > To locate the optimized breaking point precisely, we tested 350, 400, and 450 users:
  > The optimized system remained completely failure-free at 300 concurrent users. Failures first began at 350 concurrent users with a modest 1.43% failure rate.
  > The optimized architecture delivered over 2x throughput under load and extended zero-failure concurrency from 200 to 300 users."
- **Visual**:
  - Show the Clean Before/After Failure Rate Table:
    ```
    | Concurrent Users | Baseline Failure % | Optimized Failure % |
    |:---:|:---:|:---:|
    | 50  | 0.0% | 0.0% |
    | 100 | 0.0% | 0.0% |
    | 150 | 0.0% | 0.0% |
    | 200 | 0.0% | 0.0% |
    | 300 | 9.18% ❌ | 0.0% ✅ |
    | 350 | — | 1.43% ❌ |
    | 400 | — | 0.88% ❌ |
    | 450 | — | 2.92% ❌ |
    | 500 | 32.37% ❌ | 9.08% ❌ |
    ```
  - Highlight the summary lines:
    - **Baseline highest tested zero-failure load**: 200 users (failed at 300)
    - **Optimized highest tested zero-failure load**: 300 users (failures began at 350)
