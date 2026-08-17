"""
Integration tests for FastAPI endpoints using TestClient.
"""
import pytest


class TestRootEndpoint:
    """Tests for the GET / endpoint"""
    
    def test_root_redirects_to_index(self, client):
        """Test that the root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""
    
    def test_get_all_activities(self, client, clean_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) == 9  # We have 9 sample activities
        
        # Verify structure of an activity
        first_activity = list(activities.values())[0]
        assert "description" in first_activity
        assert "schedule" in first_activity
        assert "max_participants" in first_activity
        assert "participants" in first_activity
        assert isinstance(first_activity["participants"], list)
    
    def test_activities_contain_expected_fields(self, client, clean_activities):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(activity_data.keys())
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self, client, clean_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "newstudent@mergington.edu" in result["message"]
        
        # Verify participant was actually added
        activities = client.get("/activities").json()
        participants = activities["Chess Club"]["participants"]
        assert "newstudent@mergington.edu" in participants
    
    def test_signup_nonexistent_activity(self, client, clean_activities):
        """Test signup fails for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]
    
    def test_signup_duplicate_registration(self, client, clean_activities):
        """Test signup fails when student is already registered"""
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"]
    
    def test_signup_multiple_students(self, client, clean_activities):
        """Test multiple students can sign up for same activity"""
        students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for student in students:
            response = client.post(
                "/activities/Programming Class/signup",
                params={"email": student}
            )
            assert response.status_code == 200
        
        # Verify all were added
        activities = client.get("/activities").json()
        participants = activities["Programming Class"]["participants"]
        for student in students:
            assert student in participants


class TestUnregisterEndpoint:
    """Tests for the POST /activities/{activity_name}/unregister endpoint"""
    
    def test_successful_unregister(self, client, clean_activities):
        """Test successful unregistration from an activity"""
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "Unregistered" in result["message"]
        
        # Verify participant was actually removed
        activities = client.get("/activities").json()
        participants = activities["Chess Club"]["participants"]
        assert "michael@mergington.edu" not in participants
    
    def test_unregister_nonexistent_activity(self, client, clean_activities):
        """Test unregister fails for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]
    
    def test_unregister_not_registered_student(self, client, clean_activities):
        """Test unregister fails when student is not registered"""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        
        assert response.status_code == 400
        result = response.json()
        assert "not registered" in result["detail"]
    
    def test_signup_then_unregister(self, client, clean_activities):
        """Test full cycle: signup then unregister"""
        email = "cycle@mergington.edu"
        activity = "Art Studio"
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify signed up
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify unregistered
        activities = client.get("/activities").json()
        assert email not in activities[activity]["participants"]
