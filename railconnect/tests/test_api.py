import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Use a clean test database and deterministic development configuration.
os.environ["DATABASE_URL"] = "sqlite:///./test_railconnect.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-tests-only"
os.environ["ADMIN_EMAIL"] = "admin@railconnect.local"

from app.main import app
from app.database import create_db_and_tables, engine
from sqlmodel import SQLModel

@pytest.fixture(autouse=True)
def reset_database():
    SQLModel.metadata.drop_all(engine)
    create_db_and_tables()
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

def signup_and_login(client, email="user@example.com", password="Password123!"):
    response = client.post("/auth/signup", json={"email": email, "password": password})
    assert response.status_code == 201, response.text
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]

def test_signup_login_and_failed_login(client):
    token = signup_and_login(client)
    assert token
    failed = client.post("/auth/login", json={"email": "user@example.com", "password": "wrong-password"})
    assert failed.status_code == 401

def test_admin_add_train_and_search(client):
    signup_and_login(client, "admin@railconnect.local")
    login = client.post("/auth/login", json={
        "email": "admin@railconnect.local", "password": "Password123!"
    })
    token = login.json()["access_token"]
    response = client.post("/admin/trains", headers={"Authorization": f"Bearer {token}"}, json={
        "train_number": "RC100", "name": "RailConnect Express",
        "source": "Delhi", "destination": "Jaipur",
        "departure_time": "08:30", "arrival_time": "13:00", "total_seats": 50
    })
    assert response.status_code == 201, response.text
    results = client.get("/trains", params={"source": "Delhi", "destination": "Jaipur"})
    assert results.status_code == 200
    assert len(results.json()) == 1

def test_booking_cancel_and_seat_restore(client):
    user_token = signup_and_login(client)
    admin_token = signup_and_login(client, "admin@railconnect.local")
    train_response = client.post("/admin/trains", headers={"Authorization": f"Bearer {admin_token}"}, json={
        "train_number": "RC200", "name": "Test Express",
        "source": "Delhi", "destination": "Agra",
        "departure_time": "09:00", "arrival_time": "11:00", "total_seats": 10
    })
    assert train_response.status_code == 201, train_response.text
    train_id = train_response.json()["id"]
    booking = client.post("/bookings", headers={"Authorization": f"Bearer {user_token}"}, json={
        "train_id": train_id, "seats": 2
    })
    assert booking.status_code == 201, booking.text
    pnr = booking.json()["pnr"]
    seats = client.get(f"/trains/{train_id}/seats").json()["available_seats"]
    assert seats == 8
    cancelled = client.post(f"/bookings/{pnr}/cancel", headers={"Authorization": f"Bearer {user_token}"})
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"
    assert client.get(f"/trains/{train_id}/seats").json()["available_seats"] == 10

def test_forgot_reset_password_token_is_one_time(client):
    signup_and_login(client)
    forgot = client.post("/auth/forgot-password", json={"email": "user@example.com"})
    assert forgot.status_code == 200
    token = forgot.json()["reset_token"]
    assert token
    reset = client.post("/auth/reset-password", json={
        "token": token, "new_password": "NewPassword123!"
    })
    assert reset.status_code == 200
    reused = client.post("/auth/reset-password", json={
        "token": token, "new_password": "AnotherPassword123!"
    })
    assert reused.status_code == 400
    login = client.post("/auth/login", json={
        "email": "user@example.com", "password": "NewPassword123!"
    })
    assert login.status_code == 200
