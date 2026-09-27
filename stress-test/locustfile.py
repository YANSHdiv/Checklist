import random
from datetime import datetime, timezone
from locust import HttpUser, task, between

GRAPHQL_QUERY_RELEASES = """
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
"""

GRAPHQL_QUERY_SINGLE = """
query GetRelease($id: UUID!) {
  release(id: $id) {
    id
    name
    status
    completedSteps
  }
}
"""

GRAPHQL_MUTATION_CREATE = """
mutation CreateRelease($input: CreateReleaseInput!) {
  createRelease(input: $input) {
    id
    name
    status
    completedSteps
  }
}
"""

GRAPHQL_MUTATION_TOGGLE = """
mutation ToggleStep($releaseId: UUID!, $stepId: Int!) {
  toggleStep(releaseId: $releaseId, stepId: $stepId) {
    id
    status
    completedSteps
  }
}
"""

GRAPHQL_MUTATION_UPDATE = """
mutation UpdateRelease($input: UpdateReleaseInput!) {
  updateRelease(input: $input) {
    id
    additionalInfo
  }
}
"""

GRAPHQL_MUTATION_DELETE = """
mutation DeleteRelease($id: UUID!) {
  deleteRelease(id: $id)
}
"""


class ReleaseChecklistUser(HttpUser):
    # Wait between 0.1 and 0.5 seconds between simulated user actions
    wait_time = between(0.1, 0.5)

    def on_start(self):
        """Seed or discover release IDs on user start."""
        self.known_release_ids = []
        # Create an initial user-scoped release
        res = self.client.post(
            "/graphql",
            json={
                "query": GRAPHQL_MUTATION_CREATE,
                "variables": {
                    "input": {
                        "name": f"Stress Test Release - {random.randint(1000, 999999)}",
                        "dueDate": datetime.now(timezone.utc).isoformat(),
                        "additionalInfo": "Seeded by Locust virtual user",
                    }
                },
            },
            name="GraphQL: Create Release (Seed)",
        )
        if res.status_code == 200:
            data = res.json()
            if "data" in data and data["data"] and data["data"].get("createRelease"):
                self.known_release_ids.append(data["data"]["createRelease"]["id"])

    @task(5)
    def fetch_all_releases(self):
        """Dashboard query - most frequent operation."""
        with self.client.post(
            "/graphql",
            json={"query": GRAPHQL_QUERY_RELEASES},
            name="GraphQL: Query Releases",
            catch_response=True,
        ) as res:
            if res.status_code != 200:
                res.failure(f"HTTP {res.status_code}")
                return
            data = res.json()
            if "errors" in data:
                res.failure(f"GraphQL error: {data['errors']}")
            else:
                releases = data.get("data", {}).get("releases", [])
                if releases:
                    # Update local pool of active release IDs
                    self.known_release_ids = [r["id"] for r in releases[:10]]

    @task(3)
    def toggle_step(self):
        """User checking/unchecking a checklist step."""
        if not self.known_release_ids:
            return
        target_id = random.choice(self.known_release_ids)
        step_id = random.randint(1, 10)
        with self.client.post(
            "/graphql",
            json={
                "query": GRAPHQL_MUTATION_TOGGLE,
                "variables": {
                    "releaseId": target_id,
                    "stepId": step_id,
                },
            },
            name="GraphQL: Toggle Step",
            catch_response=True,
        ) as res:
            if res.status_code != 200:
                res.failure(f"HTTP {res.status_code}")
                return
            data = res.json()
            if "errors" in data:
                res.failure(f"GraphQL error: {data['errors']}")

    @task(2)
    def fetch_single_release(self):
        """Inspecting single release details."""
        if not self.known_release_ids:
            return
        target_id = random.choice(self.known_release_ids)
        with self.client.post(
            "/graphql",
            json={
                "query": GRAPHQL_QUERY_SINGLE,
                "variables": {"id": target_id},
            },
            name="GraphQL: Query Single Release",
            catch_response=True,
        ) as res:
            if res.status_code != 200:
                res.failure(f"HTTP {res.status_code}")
                return
            data = res.json()
            if "errors" in data:
                res.failure(f"GraphQL error: {data['errors']}")

    @task(1)
    def update_additional_info(self):
        """Updating notes/instructions on a release."""
        if not self.known_release_ids:
            return
        target_id = random.choice(self.known_release_ids)
        with self.client.post(
            "/graphql",
            json={
                "query": GRAPHQL_MUTATION_UPDATE,
                "variables": {
                    "input": {
                        "id": target_id,
                        "additionalInfo": f"Stress test update at {datetime.now(timezone.utc).isoformat()}",
                    }
                },
            },
            name="GraphQL: Update Release Info",
            catch_response=True,
        ) as res:
            if res.status_code != 200:
                res.failure(f"HTTP {res.status_code}")
                return
            data = res.json()
            if "errors" in data:
                res.failure(f"GraphQL error: {data['errors']}")

    @task(1)
    def lifecycle_create_and_delete(self):
        """Complete lifecycle: create temporary release then delete."""
        create_res = self.client.post(
            "/graphql",
            json={
                "query": GRAPHQL_MUTATION_CREATE,
                "variables": {
                    "input": {
                        "name": f"Temp Lifecycle Release {random.randint(100, 9999)}",
                        "dueDate": datetime.now(timezone.utc).isoformat(),
                        "additionalInfo": "Lifecycle stress test item",
                    }
                },
            },
            name="GraphQL: Create Temp Release",
        )
        if create_res.status_code == 200:
            created_data = create_res.json()
            rel_id = created_data.get("data", {}).get("createRelease", {}).get("id")
            if rel_id:
                # Delete it
                self.client.post(
                    "/graphql",
                    json={
                        "query": GRAPHQL_MUTATION_DELETE,
                        "variables": {"id": rel_id},
                    },
                    name="GraphQL: Delete Release",
                )
