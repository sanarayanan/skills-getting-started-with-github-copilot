"""
Shared pytest fixtures and configuration for all tests.
"""
import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
from src.app import app, activities


@pytest.fixture
def client():
    """
    Provides a TestClient for making HTTP requests to the FastAPI app.
    """
    return TestClient(app)


@pytest.fixture
def clean_activities():
    """
    Provides a fresh copy of the activities dictionary for each test.
    This ensures test isolation by resetting the in-memory database before each test.
    """
    # Store the original activities
    original = deepcopy(activities)
    
    # Yield the activities for the test to use
    yield activities
    
    # Restore original state after test completes
    activities.clear()
    activities.update(original)


@pytest.fixture
def sample_activity():
    """
    Provides a sample activity object for unit tests.
    """
    return {
        "description": "Test activity for unit testing",
        "schedule": "Mondays, 3:00 PM - 4:00 PM",
        "max_participants": 10,
        "participants": ["alice@test.edu", "bob@test.edu"]
    }


@pytest.fixture
def sample_participant():
    """
    Provides a sample participant email for testing.
    """
    return "charlie@test.edu"
