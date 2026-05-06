"""
Tests for src/app.py using AAA (Arrange-Act-Assert) pattern.

Each test follows the AAA structure:
- Arrange: Set up test data and conditions
- Act: Execute the code being tested
- Assert: Verify the results
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Fixture: Create a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Fixture: Reset activities to initial state before and after each test.
    This prevents test contamination by deep copying the original state.
    """
    # Store the initial state
    original_activities = copy.deepcopy(activities)
    
    yield
    
    # Restore the initial state after test completes
    activities.clear()
    activities.update(original_activities)


# ============================================================================
# GET / (Root Redirect) Tests
# ============================================================================

def test_root_redirect(client, reset_activities):
    """
    Test: GET / should redirect to /static/index.html
    
    Arrange: No specific setup needed, using default app state
    Act: Send GET request to root endpoint
    Assert: Verify 307 redirect status and location header
    """
    # Arrange
    # (using default app state)
    
    # Act
    response = client.get("/", follow_redirects=False)
    
    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


# ============================================================================
# GET /activities Tests
# ============================================================================

def test_get_activities_returns_all_activities(client, reset_activities):
    """
    Test: GET /activities should return all activities
    
    Arrange: No specific setup needed, using default app state
    Act: Request activities endpoint
    Assert: Verify response contains all activities with correct structure
    """
    # Arrange
    expected_activity_count = len(activities)
    
    # Act
    response = client.get("/activities")
    data = response.json()
    
    # Assert
    assert response.status_code == 200
    assert len(data) == expected_activity_count
    assert "Chess Club" in data
    assert "description" in data["Chess Club"]
    assert "schedule" in data["Chess Club"]
    assert "max_participants" in data["Chess Club"]
    assert "participants" in data["Chess Club"]


def test_get_activities_includes_participants_list(client, reset_activities):
    """
    Test: GET /activities should include participants list
    
    Arrange: No specific setup needed, using default app state
    Act: Request activities endpoint
    Assert: Verify Chess Club has expected participants
    """
    # Arrange
    expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
    
    # Act
    response = client.get("/activities")
    data = response.json()
    
    # Assert
    assert response.status_code == 200
    assert data["Chess Club"]["participants"] == expected_participants


# ============================================================================
# POST /activities/{activity_name}/signup Tests
# ============================================================================

def test_signup_successful(client, reset_activities):
    """
    Test: POST /signup should add participant to activity
    
    Arrange: Get initial participant count for Tennis Club
    Act: Sign up a new student
    Assert: Verify participant is added and count increases
    """
    # Arrange
    activity_name = "Tennis Club"
    email = "newstudent@mergington.edu"
    initial_count = len(activities[activity_name]["participants"])
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == initial_count + 1


def test_signup_duplicate_participant_returns_400(client, reset_activities):
    """
    Test: POST /signup with duplicate email should return 400 error
    
    Arrange: Select an activity and a participant already signed up
    Act: Try to sign up the same participant again
    Assert: Verify 400 error with appropriate message
    """
    # Arrange
    activity_name = "Chess Club"
    duplicate_email = "michael@mergington.edu"  # Already in Chess Club
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": duplicate_email}
    )
    
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_nonexistent_activity_returns_404(client, reset_activities):
    """
    Test: POST /signup with invalid activity name should return 404
    
    Arrange: Use a non-existent activity name
    Act: Try to sign up for the invalid activity
    Assert: Verify 404 error with appropriate message
    """
    # Arrange
    invalid_activity = "Nonexistent Club"
    email = "student@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{invalid_activity}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


# ============================================================================
# POST /activities/{activity_name}/remove Tests
# ============================================================================

def test_remove_participant_successful(client, reset_activities):
    """
    Test: POST /remove should remove participant from activity
    
    Arrange: Get initial participant count and select existing participant
    Act: Remove the participant
    Assert: Verify participant is removed and count decreases
    """
    # Arrange
    activity_name = "Chess Club"
    email_to_remove = "michael@mergington.edu"
    initial_count = len(activities[activity_name]["participants"])
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/remove",
        params={"email": email_to_remove}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email_to_remove} from {activity_name}"
    assert email_to_remove not in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == initial_count - 1


def test_remove_nonexistent_participant_returns_404(client, reset_activities):
    """
    Test: POST /remove with non-existent participant should return 404
    
    Arrange: Select an activity and non-existent participant
    Act: Try to remove the non-existent participant
    Assert: Verify 404 error with appropriate message
    """
    # Arrange
    activity_name = "Chess Club"
    nonexistent_email = "notastudent@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/remove",
        params={"email": nonexistent_email}
    )
    
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_remove_from_nonexistent_activity_returns_404(client, reset_activities):
    """
    Test: POST /remove from invalid activity should return 404
    
    Arrange: Use a non-existent activity name
    Act: Try to remove participant from invalid activity
    Assert: Verify 404 error with appropriate message
    """
    # Arrange
    invalid_activity = "Nonexistent Club"
    email = "student@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{invalid_activity}/remove",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


# ============================================================================
# Integration Tests
# ============================================================================

def test_signup_and_remove_flow(client, reset_activities):
    """
    Test: Complete signup and remove workflow
    
    Arrange: Select activity and new student
    Act: Sign up student, then remove them
    Assert: Verify both operations succeed and participant list reflects changes
    """
    # Arrange
    activity_name = "Basketball Team"
    email = "newplayer@mergington.edu"
    
    # Act - Signup
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert signup_response.status_code == 200
    assert email in activities[activity_name]["participants"]
    
    # Act - Remove
    remove_response = client.post(
        f"/activities/{activity_name}/remove",
        params={"email": email}
    )
    
    # Assert
    assert remove_response.status_code == 200
    assert email not in activities[activity_name]["participants"]


def test_multiple_signups_and_state_isolation(client, reset_activities):
    """
    Test: Multiple signups in sequence maintain correct state
    
    Arrange: Select activity and multiple new students
    Act: Sign up multiple students sequentially
    Assert: Verify all are added and participant count is correct
    """
    # Arrange
    activity_name = "Programming Class"
    students = [
        "alice@mergington.edu",
        "bob@mergington.edu",
        "charlie@mergington.edu"
    ]
    initial_count = len(activities[activity_name]["participants"])
    
    # Act
    for student_email in students:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student_email}
        )
        assert response.status_code == 200
    
    # Assert
    assert len(activities[activity_name]["participants"]) == initial_count + len(students)
    for student_email in students:
        assert student_email in activities[activity_name]["participants"]
