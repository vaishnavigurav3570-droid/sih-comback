from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_nowcast_demo_mode():
    # Use heuristic to avoid heavy PyTorch initialization during tests
    response = client.get("/api/v1/forecast/now?mode=demo&use_heuristic=true")

    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code} with body: {response.text}"

    data = response.json()
    assert "forecast_id" in data
    assert "region" in data
    assert "grid_forecasts" in data

    assert data["is_demo_mode"] is True
    assert "SYNTHETIC" in data["data_sources_used"]
