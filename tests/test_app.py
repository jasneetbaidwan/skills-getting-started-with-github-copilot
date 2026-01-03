import copy
import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from app import app, activities

client = TestClient(app)


def _reset_activities(original):
    activities.clear()
    activities.update(copy.deepcopy(original))


@pytest.fixture(autouse=True)
def preserve_activities():
    original = copy.deepcopy(activities)
    try:
        yield
    finally:
        _reset_activities(original)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Expect some known activities from seed data
    assert "Basketball" in data


def test_signup_and_reflects_in_activities():
    email = "teststudent@mergington.edu"
    activity = "Basketball"

    signup_resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert signup_resp.status_code == 200
    assert email in signup_resp.json()["message"]

    # Check that the activity now includes the participant
    activities_resp = client.get("/activities").json()
    assert email in activities_resp[activity]["participants"]


def test_double_signup_returns_400():
    email = "double@mergington.edu"
    activity = "Soccer"

    r1 = client.post(f"/activities/{activity}/signup?email={email}")
    assert r1.status_code == 200

    r2 = client.post(f"/activities/{activity}/signup?email={email}")
    assert r2.status_code == 400


def test_unregister_removes_participant():
    # Add then remove
    email = "temp@mergington.edu"
    activity = "Art Club"
    client.post(f"/activities/{activity}/signup?email={email}")

    # Now unregister
    r = client.post(f"/activities/{activity}/unregister?email={email}")
    assert r.status_code == 200
    assert "Unregistered" in r.json()["message"]

    data = client.get("/activities").json()
    assert email not in data[activity]["participants"]


def test_unregister_nonexistent_returns_400():
    email = "nobody@mergington.edu"
    activity = "Drama Club"
    r = client.post(f"/activities/{activity}/unregister?email={email}")
    assert r.status_code == 400
