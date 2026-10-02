from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_root_redirects_to_static_page(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_initial_participants(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_student_to_activity(client):
    email = "new.student@mergington.edu"

    response = client.post("/activities/Chess%20Club/signup", params={"email": email})
    activities_response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert activities_response.json()["Chess Club"]["participants"][-1] == email


def test_signup_rejects_unknown_activity(client):
    original_participants = activities["Chess Club"]["participants"].copy()

    response = client.post("/activities/Unknown/signup", params={"email": "new@mergington.edu"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities["Chess Club"]["participants"] == original_participants


def test_signup_rejects_existing_student(client):
    original_participants = activities["Chess Club"]["participants"].copy()

    response = client.post(
        "/activities/Chess%20Club/signup", params={"email": "michael@mergington.edu"}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert activities["Chess Club"]["participants"] == original_participants


def test_signup_requires_email(client):
    original_participants = activities["Chess Club"]["participants"].copy()

    response = client.post("/activities/Chess%20Club/signup")

    assert response.status_code == 422
    assert activities["Chess Club"]["participants"] == original_participants