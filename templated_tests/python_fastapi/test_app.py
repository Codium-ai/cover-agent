from datetime import date

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_root():
    """

    def test_current_date():
        response = client.get("/current-date")
        assert response.status_code == 200
        assert "date" in response.json()

    Test the root endpoint by sending a GET request to "/" and checking the response status code and JSON body.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the FastAPI application!"}


def test_current_date():
    response = client.get("/current-date")
    assert response.status_code == 200
    assert "date" in response.json()
    assert response.json()["date"] == date.today().isoformat()

