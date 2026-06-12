"""Tests for the activities API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Provide a test client for the FastAPI app."""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_200(self, client):
        """Arrange: Setup test client.
        Act: GET /activities.
        Assert: Status code is 200.
        """
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Arrange: Setup test client.
        Act: GET /activities.
        Assert: Response is a dictionary.
        """
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_keys(self, client):
        """Arrange: Setup test client.
        Act: GET /activities.
        Assert: Response contains expected activity keys.
        """
        response = client.get("/activities")
        activities = response.json()
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities

    def test_activity_has_required_fields(self, client):
        """Arrange: Setup test client.
        Act: GET /activities.
        Assert: Each activity has required fields.
        """
        response = client.get("/activities")
        activities = response.json()
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_with_valid_activity_and_email(self, client):
        """Arrange: Valid activity name and email.
        Act: POST /activities/Chess Club/signup with email.
        Assert: Status code is 200 and message is returned.
        """
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Arrange: Valid activity and email.
        Act: POST to signup, then GET activities.
        Assert: Email appears in participants list.
        """
        email = "testuser@mergington.edu"
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )

        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]

    def test_signup_with_nonexistent_activity(self, client):
        """Arrange: Non-existent activity name.
        Act: POST /activities/Invalid Activity/signup.
        Assert: Status code is 404 and error detail is returned.
        """
        response = client.post(
            "/activities/Invalid Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_allows_duplicate_registrations(self, client):
        """Arrange: Valid activity and email.
        Act: POST signup twice with the same email.
        Assert: First succeeds, second fails with 400 (duplicate prevention).
        """
        email = "duplicate@mergington.edu"
        activity = "Programming Class"

        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        assert response1.status_code == 200
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

        # Verify email appears only once
        response = client.get("/activities")
        activities = response.json()
        count = activities[activity]["participants"].count(email)
        assert count == 1  # Should only appear once due to prevention


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""

    def test_remove_existing_participant(self, client):
        """Arrange: Add a participant, then remove them.
        Act: DELETE /activities/{activity}/signup with email.
        Assert: Status code is 200 and success message is returned.
        """
        email = "remove@mergington.edu"
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )

        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]

    def test_remove_participant_from_list(self, client):
        """Arrange: Add participant, then remove.
        Act: DELETE endpoint, then GET activities.
        Assert: Email no longer in participants list.
        """
        email = "remove2@mergington.edu"
        activity = "Gym Class"
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]

    def test_remove_nonexistent_activity(self, client):
        """Arrange: Non-existent activity name.
        Act: DELETE /activities/Invalid Activity/signup.
        Assert: Status code is 404 and activity not found error.
        """
        response = client.delete(
            "/activities/Invalid Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_remove_nonexistent_participant(self, client):
        """Arrange: Valid activity, non-existent participant.
        Act: DELETE with email not in participants.
        Assert: Status code is 404 and participant not found error.
        """
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"
