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
    # Simulated user pacing: 0.1s to 0.3s between actions
    wait_time = between(0.1, 0.3)

    def on_start(self):
        """Seed initial release ID for this simulated user."""
        self.known_release_ids = []
        try:
            with self.client.post(
                "/graphql",
                json={
                    "query": GRAPHQL_MUTATION_CREATE,
                    "variables": {
                        "input": {
                            "name": f"Stress Seed {random.randint(1000, 999999)}",
                            "dueDate": datetime.now(timezone.utc).isoformat(),
                            "additionalInfo": "Seeded on virtual user initialization",
                        }
                    },
                },
                timeout=5.0,
                name="GraphQL: Create Release (Seed)",
                catch_response=True,
            ) as res:
                if res.status_code == 200:
                    data = res.json()
                    if "data" in data and data["data"] and data["data"].get("createRelease"):
                        self.known_release_ids.append(data["data"]["createRelease"]["id"])
                elif res.status_code >= 400:
                    res.failure(f"HTTP {res.status_code}: {res.text[:100]}")
        except Exception as e:
            pass

    @task(5)
    def fetch_all_releases(self):
        """Dashboard query - most frequent operation."""
        try:
            with self.client.post(
                "/graphql",
                json={"query": GRAPHQL_QUERY_RELEASES},
                timeout=5.0,
                name="GraphQL: Query Releases",
                catch_response=True,
            ) as res:
                if res.status_code != 200:
                    res.failure(f"HTTP {res.status_code}")
                    return
                data = res.json()
                if "errors" in data and data["errors"]:
                    res.failure(f"GraphQL Error: {data['errors'][0].get('message', 'Unknown')}")
                else:
                    releases = data.get("data", {}).get("releases", [])
                    if releases:
                        self.known_release_ids = [r["id"] for r in releases[:15]]
        except Exception as e:
            pass

    @task(3)
    def toggle_step(self):
        """User toggling a checklist step."""
        if not self.known_release_ids:
            return
        target_id = random.choice(self.known_release_ids)
        step_id = random.randint(1, 10)
        try:
            with self.client.post(
                "/graphql",
                json={
                    "query": GRAPHQL_MUTATION_TOGGLE,
                    "variables": {
                        "releaseId": target_id,
                        "stepId": step_id,
                    },
                },
                timeout=5.0,
                name="GraphQL: Toggle Step",
                catch_response=True,
            ) as res:
                if res.status_code != 200:
                    res.failure(f"HTTP {res.status_code}")
                    return
                data = res.json()
                if "errors" in data and data["errors"]:
                    res.failure(f"GraphQL Error: {data['errors'][0].get('message', 'Unknown')}")
        except Exception as e:
            pass

    @task(2)
    def fetch_single_release(self):
        """Inspecting single release details."""
        if not self.known_release_ids:
            return
        target_id = random.choice(self.known_release_ids)
        try:
            with self.client.post(
                "/graphql",
                json={
                    "query": GRAPHQL_QUERY_SINGLE,
                    "variables": {"id": target_id},
                },
                timeout=5.0,
                name="GraphQL: Query Single Release",
                catch_response=True,
            ) as res:
                if res.status_code != 200:
                    res.failure(f"HTTP {res.status_code}")
                    return
                data = res.json()
                if "errors" in data and data["errors"]:
                    res.failure(f"GraphQL Error: {data['errors'][0].get('message', 'Unknown')}")
        except Exception as e:
            pass

    @task(1)
    def update_additional_info(self):
        """Updating release notes."""
        if not self.known_release_ids:
            return
        target_id = random.choice(self.known_release_ids)
        try:
            with self.client.post(
                "/graphql",
                json={
                    "query": GRAPHQL_MUTATION_UPDATE,
                    "variables": {
                        "input": {
                            "id": target_id,
                            "additionalInfo": f"Load test note at {datetime.now(timezone.utc).isoformat()}",
                        }
                    },
                },
                timeout=5.0,
                name="GraphQL: Update Release Info",
                catch_response=True,
            ) as res:
                if res.status_code != 200:
                    res.failure(f"HTTP {res.status_code}")
                    return
                data = res.json()
                if "errors" in data and data["errors"]:
                    res.failure(f"GraphQL Error: {data['errors'][0].get('message', 'Unknown')}")
        except Exception as e:
            pass

    @task(1)
    def lifecycle_create_and_delete(self):
        """Full lifecycle: create release then delete it."""
        try:
            with self.client.post(
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
                timeout=5.0,
                name="GraphQL: Create Temp Release",
                catch_response=True,
            ) as create_res:
                if create_res.status_code != 200:
                    create_res.failure(f"HTTP {create_res.status_code}")
                    return
                created_data = create_res.json()
                if "errors" in created_data and created_data["errors"]:
                    create_res.failure(f"GraphQL Error: {created_data['errors'][0].get('message', 'Unknown')}")
                    return
                rel_id = created_data.get("data", {}).get("createRelease", {}).get("id")

            if rel_id:
                with self.client.post(
                    "/graphql",
                    json={
                        "query": GRAPHQL_MUTATION_DELETE,
                        "variables": {"id": rel_id},
                    },
                    timeout=5.0,
                    name="GraphQL: Delete Release",
                    catch_response=True,
                ) as del_res:
                    if del_res.status_code != 200:
                        del_res.failure(f"HTTP {del_res.status_code}")
                        return
                    del_data = del_res.json()
                    if "errors" in del_data and del_data["errors"]:
                        del_res.failure(f"GraphQL Error: {del_data['errors'][0].get('message', 'Unknown')}")
        except Exception as e:
            pass
