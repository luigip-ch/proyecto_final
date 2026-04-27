import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── /health ───────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_returns_200(client):
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_returns_status_ok(client):
    response = await client.get("/health")
    assert response.json()["status"] == "ok"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_returns_version(client):
    response = await client.get("/health")
    assert "version" in response.json()


# ── /api/lotteries ────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_lotteries_returns_200(client):
    response = await client.get("/api/lotteries")
    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_lotteries_contains_cundinamarca(client):
    response = await client.get("/api/lotteries")
    data = response.json()
    names = [item["id"] for item in data["lotteries"]]
    assert "cundinamarca" in names


@pytest.mark.integration
@pytest.mark.asyncio
async def test_lotteries_response_has_required_fields(client):
    response = await client.get("/api/lotteries")
    data = response.json()
    assert "lotteries" in data
    assert isinstance(data["lotteries"], list)
    for item in data["lotteries"]:
        assert "id" in item
        assert "name" in item


# ── /api/predict ──────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_predict_returns_200(client):
    mock_model = MagicMock()
    mock_model.predict.return_value = [1, 2, 3, 4, 55]
    with patch("app.backend.api.predict.get_model", return_value=mock_model):
        response = await client.post(
            "/api/predict", json={"lottery": "cundinamarca"}
        )
    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_predict_response_has_main_numbers(client):
    mock_model = MagicMock()
    mock_model.predict.return_value = [5, 6, 7, 8, 99]
    with patch("app.backend.api.predict.get_model", return_value=mock_model):
        response = await client.post(
            "/api/predict", json={"lottery": "cundinamarca"}
        )
    data = response.json()
    assert "prediction" in data
    assert "main_numbers" in data["prediction"]
    assert len(data["prediction"]["main_numbers"]) == 4
    assert "serie" in data["prediction"]
    assert isinstance(data["prediction"]["serie"], str)
    assert len(data["prediction"]["serie"]) == 3
    assert "statistics" in data
    assert "generated_at" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_predict_returns_422_for_missing_lottery(client):
    response = await client.post("/api/predict", json={})
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_predict_returns_404_for_unknown_lottery(client):
    with patch(
        "app.backend.api.predict.get_model",
        side_effect=ValueError("lotería no registrada"),
    ):
        response = await client.post(
            "/api/predict", json={"lottery": "inexistente"}
        )
    assert response.status_code == 404


# ── /api/train ────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_train_returns_202(client):
    with patch("app.backend.api.train.get_model", return_value=MagicMock()):
        response = await client.post(
            "/api/train", json={"lottery": "cundinamarca"}
        )
    assert response.status_code == 202


@pytest.mark.integration
@pytest.mark.asyncio
async def test_train_response_has_job_id(client):
    with patch("app.backend.api.train.get_model", return_value=MagicMock()):
        response = await client.post(
            "/api/train", json={"lottery": "cundinamarca"}
        )
    data = response.json()
    assert "job_id" in data
    assert isinstance(data["job_id"], str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_train_returns_422_for_missing_lottery(client):
    response = await client.post("/api/train", json={})
    assert response.status_code == 422


# ── /api/train/{job_id}/status ────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_train_status_returns_200_for_known_job(client):
    with patch("app.backend.api.train.get_model", return_value=MagicMock()):
        train_resp = await client.post(
            "/api/train", json={"lottery": "cundinamarca"}
        )
    job_id = train_resp.json()["job_id"]
    response = await client.get(f"/api/train/{job_id}/status")
    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_train_status_has_required_fields(client):
    with patch("app.backend.api.train.get_model", return_value=MagicMock()):
        train_resp = await client.post(
            "/api/train", json={"lottery": "cundinamarca"}
        )
    job_id = train_resp.json()["job_id"]
    data = (await client.get(f"/api/train/{job_id}/status")).json()
    assert "job_id" in data
    assert "status" in data
    assert "lottery" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_train_status_valid_values(client):
    with patch("app.backend.api.train.get_model", return_value=MagicMock()):
        train_resp = await client.post(
            "/api/train", json={"lottery": "cundinamarca"}
        )
    job_id = train_resp.json()["job_id"]
    data = (await client.get(f"/api/train/{job_id}/status")).json()
    assert data["status"] in {"queued", "running", "completed", "failed"}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_train_status_returns_404_for_unknown_job(client):
    response = await client.get("/api/train/job-inexistente/status")
    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_train_status_completed_after_sync_run(client):
    """El background task completa sincrónicamente en el test client."""
    mock_model = MagicMock()
    with patch("app.backend.api.train.get_model", return_value=mock_model):
        train_resp = await client.post(
            "/api/train", json={"lottery": "cundinamarca"}
        )
    job_id = train_resp.json()["job_id"]
    data = (await client.get(f"/api/train/{job_id}/status")).json()
    assert data["status"] == "completed"
