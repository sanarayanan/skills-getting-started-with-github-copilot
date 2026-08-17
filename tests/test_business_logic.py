"""
Unit tests for business logic and validation in the FastAPI app.
"""
import pytest


class TestSignupValidation:
    """Tests for signup validation logic"""
    
    def test_signup_prevents_duplicate_registration(self, client, clean_activities):
        """Test that the same student cannot register twice for same activity"""
        email = "testdup@mergington.edu"
        activity = "Chess Club"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_rejects_nonexistent_activity(self, client, clean_activities):
        """Test that signup fails gracefully for invalid activity names"""
        response = client.post(
            "/activities/Fake Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_same_student_different_activities(self, client, clean_activities):
        """Test that a student can register for multiple different activities"""
        email = "multiclass@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Art Studio"]
        
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify student is in all activities
        all_activities = client.get("/activities").json()
        for activity in activities_to_join:
            assert email in all_activities[activity]["participants"]


class TestUnregisterValidation:
    """Tests for unregister validation logic"""
    
    def test_unregister_fails_for_unregistered_student(self, client, clean_activities):
        """Test that unregister fails when student was never registered"""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "neverregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_fails_for_nonexistent_activity(self, client, clean_activities):
        """Test that unregister fails for invalid activity names"""
        response = client.post(
            "/activities/Fake Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_cannot_be_done_twice(self, client, clean_activities):
        """Test that unregistering twice fails the second time"""
        email = "testunreg@mergington.edu"
        activity = "Programming Class"
        
        # First signup
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # First unregister should succeed
        response1 = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second unregister should fail
        response2 = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "not registered" in response2.json()["detail"]


class TestDataIntegrity:
    """Tests for data integrity and state management"""
    
    def test_participants_list_updated_correctly(self, client, clean_activities):
        """Test that participants list is correctly modified during signup/unregister"""
        email = "datatest@mergington.edu"
        activity = "Gym Class"
        
        # Get initial participant count
        initial = client.get("/activities").json()
        initial_count = len(initial[activity]["participants"])
        
        # Sign up
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        after_signup = client.get("/activities").json()
        signup_count = len(after_signup[activity]["participants"])
        assert signup_count == initial_count + 1
        
        # Unregister
        client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        after_unregister = client.get("/activities").json()
        final_count = len(after_unregister[activity]["participants"])
        assert final_count == initial_count
    
    def test_other_activities_unaffected_by_signup(self, client, clean_activities):
        """Test that signup in one activity doesn't affect others"""
        email = "isolated@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Theater Club"
        
        # Get initial state
        initial = client.get("/activities").json()
        activity2_initial = initial[activity2]["participants"].copy()
        
        # Sign up for different activity
        client.post(
            f"/activities/{activity1}/signup",
            params={"email": email}
        )
        
        # Verify activity2 unchanged
        after = client.get("/activities").json()
        assert after[activity2]["participants"] == activity2_initial
        assert email not in after[activity2]["participants"]
    
    def test_max_participants_not_enforced_yet(self, client, clean_activities):
        """
        Test that we can add participants beyond max_participants.
        This documents current behavior (no capacity validation implemented yet).
        """
        activity = "Chess Club"  # max_participants: 12
        
        # Get initial state
        initial = client.get("/activities").json()
        current_count = len(initial[activity]["participants"])
        max_cap = initial[activity]["max_participants"]
        
        # Try to add more participants than remaining capacity
        for i in range(max_cap + 5):
            email = f"overcap{i}@mergington.edu"
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            # This should succeed (capacity validation not implemented)
            # Once implemented, this test should be updated
            assert response.status_code == 200
        
        # Verify we exceeded max_participants
        final = client.get("/activities").json()
        final_count = len(final[activity]["participants"])
        assert final_count > max_cap


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""
    
    @pytest.mark.parametrize("email", [
        "test@example.com",
        "student@mergington.edu",
        "a@b.co",
        "first.last@domain.co.uk"
    ])
    def test_signup_accepts_various_email_formats(self, client, clean_activities, email):
        """Test that signup works with various valid email formats"""
        response = client.post(
            "/activities/Science Club/signup",
            params={"email": email}
        )
        # Email validation not strict in current implementation
        assert response.status_code == 200
    
    def test_activity_names_are_case_sensitive(self, client, clean_activities):
        """Test that activity names are matched case-sensitively"""
        response = client.post(
            "/activities/chess club/signup",  # lowercase
            params={"email": "test@mergington.edu"}
        )
        # Should fail because "chess club" != "Chess Club"
        assert response.status_code == 404
    
    def test_empty_participants_list_for_new_activity_signup(self, client, clean_activities):
        """
        Test the response when signing up.
        Verifies we get confirmation message, not the full activity details.
        """
        response = client.post(
            "/activities/Theater Club/signup",
            params={"email": "newactor@mergington.edu"}
        )
        
        result = response.json()
        assert "message" in result
        assert isinstance(result["message"], str)
        # Verify we're not returning the entire activity object
        assert "description" not in result
