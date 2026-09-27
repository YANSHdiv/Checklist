import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models import Base, compute_status, TOTAL_STEPS
from app.database import engine as app_engine

# Use in-memory SQLite for test suite
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    import app.database as db_module

    Base.metadata.create_all(bind=test_engine)
    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "SessionLocal", TestingSessionLocal)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_status_computation_unit():
    """Verify status logic: 0 -> planned, 1..9 -> ongoing, 10 -> done."""
    assert compute_status([]) == "planned"
    assert compute_status([1]) == "ongoing"
    assert compute_status([1, 2, 3, 4, 5]) == "ongoing"
    assert compute_status(list(range(1, TOTAL_STEPS + 1))) == "done"
    # Duplicate step IDs should not falsely inflate count
    assert compute_status([1, 1, 1]) == "ongoing"


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_and_query_release(client):
    query_create = """
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
    """
    due_iso = datetime.now(timezone.utc).isoformat()
    variables = {
        "input": {
            "name": "v1.0.0 Stable",
            "dueDate": due_iso,
            "additionalInfo": "Initial production launch",
        }
    }
    res = client.post("/graphql", json={"query": query_create, "variables": variables})
    assert res.status_code == 200
    data = res.json()["data"]["createRelease"]
    assert data["name"] == "v1.0.0 Stable"
    assert data["status"] == "planned"
    assert data["completedSteps"] == []
    assert data["additionalInfo"] == "Initial production launch"
    release_id = data["id"]

    # Query single release
    query_single = """
    query GetRelease($id: UUID!) {
        release(id: $id) {
            id
            name
            status
        }
    }
    """
    res2 = client.post(
        "/graphql", json={"query": query_single, "variables": {"id": release_id}}
    )
    assert res2.status_code == 200
    assert res2.json()["data"]["release"]["id"] == release_id


def test_toggle_step_and_status_progression(client):
    # 1. Create release
    create_mutation = """
    mutation {
        createRelease(input: {name: "v2.0.0", dueDate: "2026-10-01T12:00:00Z"}) {
            id
            status
            completedSteps
        }
    }
    """
    res = client.post("/graphql", json={"query": create_mutation})
    release_id = res.json()["data"]["createRelease"]["id"]
    assert res.json()["data"]["createRelease"]["status"] == "planned"

    # 2. Toggle step 1 -> status should become 'ongoing'
    toggle_mutation = """
    mutation Toggle($releaseId: UUID!, $stepId: Int!) {
        toggleStep(releaseId: $releaseId, stepId: $stepId) {
            id
            status
            completedSteps
        }
    }
    """
    res_toggle1 = client.post(
        "/graphql",
        json={
            "query": toggle_mutation,
            "variables": {"releaseId": release_id, "stepId": 1},
        },
    )
    data1 = res_toggle1.json()["data"]["toggleStep"]
    assert data1["status"] == "ongoing"
    assert data1["completedSteps"] == [1]

    # 3. Complete all 10 steps -> status should become 'done'
    for step in range(2, 11):
        res_step = client.post(
            "/graphql",
            json={
                "query": toggle_mutation,
                "variables": {"releaseId": release_id, "stepId": step},
            },
        )
    final_data = res_step.json()["data"]["toggleStep"]
    assert final_data["status"] == "done"
    assert len(final_data["completedSteps"]) == 10

    # 4. Uncheck step 1 -> status should return to 'ongoing'
    res_uncheck = client.post(
        "/graphql",
        json={
            "query": toggle_mutation,
            "variables": {"releaseId": release_id, "stepId": 1},
        },
    )
    uncheck_data = res_uncheck.json()["data"]["toggleStep"]
    assert uncheck_data["status"] == "ongoing"
    assert 1 not in uncheck_data["completedSteps"]


def test_update_and_delete_release(client):
    # Create
    create_res = client.post(
        "/graphql",
        json={
            "query": """
            mutation {
                createRelease(input: {name: "To Delete", dueDate: "2026-10-15T00:00:00Z"}) {
                    id
                }
            }
            """
        },
    )
    release_id = create_res.json()["data"]["createRelease"]["id"]

    # Update additional info
    update_res = client.post(
        "/graphql",
        json={
            "query": """
            mutation Update($input: UpdateReleaseInput!) {
                updateRelease(input: $input) {
                    id
                    additionalInfo
                }
            }
            """,
            "variables": {
                "input": {
                    "id": release_id,
                    "additionalInfo": "Updated notes for release",
                }
            },
        },
    )
    assert (
        update_res.json()["data"]["updateRelease"]["additionalInfo"]
        == "Updated notes for release"
    )

    # Delete
    del_res = client.post(
        "/graphql",
        json={
            "query": """
            mutation Delete($id: UUID!) {
                deleteRelease(id: $id)
            }
            """,
            "variables": {"id": release_id},
        },
    )
    assert del_res.json()["data"]["deleteRelease"] is True

    # Confirm deletion
    query_res = client.post(
        "/graphql",
        json={
            "query": """
            query Get($id: UUID!) {
                release(id: $id) {
                    id
                }
            }
            """,
            "variables": {"id": release_id},
        },
    )
    assert query_res.json()["data"]["release"] is None


def test_validation_and_bounds(client):
    # Test invalid step ID (0 or 99)
    create_res = client.post(
        "/graphql",
        json={
            "query": """
            mutation {
                createRelease(input: {name: "Bounds Test", dueDate: "2026-12-01T00:00:00Z"}) {
                    id
                }
            }
            """
        },
    )
    release_id = create_res.json()["data"]["createRelease"]["id"]

    # Toggle invalid step 99
    toggle_res = client.post(
        "/graphql",
        json={
            "query": """
            mutation Toggle($releaseId: UUID!, $stepId: Int!) {
                toggleStep(releaseId: $releaseId, stepId: $stepId) {
                    id
                }
            }
            """,
            "variables": {"releaseId": release_id, "stepId": 99},
        },
    )
    assert toggle_res.json().get("errors") is not None

    # Test empty name creation
    empty_name_res = client.post(
        "/graphql",
        json={
            "query": """
            mutation {
                createRelease(input: {name: "   ", dueDate: "2026-12-01T00:00:00Z"}) {
                    id
                }
            }
            """
        },
    )
    assert empty_name_res.json().get("errors") is not None

