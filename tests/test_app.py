"""
Tests for the High School Management System API.
"""

import pytest
from fastapi import HTTPException


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, reset_activities, client):
        """Test that all activities are returned."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_has_required_fields(self, reset_activities, client):
        """Test that activities have all required fields."""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
    
    def test_get_activities_participants_list(self, reset_activities, client):
        """Test that participants are returned as a list."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)
            assert len(activity_data["participants"]) <= activity_data["max_participants"]


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_new_student_success(self, reset_activities, client):
        """Test successful signup for a new student."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_adds_student_to_participants(self, reset_activities, client):
        """Test that signup actually adds the student to participants."""
        email = "newstudent@mergington.edu"
        client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Programming Class"]["participants"]
    
    def test_signup_nonexistent_activity(self, reset_activities, client):
        """Test signup for an activity that doesn't exist."""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_already_registered_student(self, reset_activities, client):
        """Test that a student cannot sign up twice for the same activity."""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_multiple_activities(self, reset_activities, client):
        """Test that a student can sign up for multiple different activities."""
        email = "newstudent@mergington.edu"
        
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            "/activities/Tennis Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups succeeded
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Tennis Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, reset_activities, client):
        """Test successful unregistration from an activity."""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]
    
    def test_unregister_removes_from_participants(self, reset_activities, client):
        """Test that unregister removes the student from participants."""
        email = "michael@mergington.edu"
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, reset_activities, client):
        """Test unregister from an activity that doesn't exist."""
        response = client.delete(
            "/activities/Nonexistent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_student_not_registered(self, reset_activities, client):
        """Test that unregister fails if student is not registered."""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notstudent@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()
    
    def test_signup_after_unregister(self, reset_activities, client):
        """Test that a student can re-sign up after unregistering."""
        email = "michael@mergington.edu"
        
        # Unregister
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        
        # Re-signup
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify registered
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]