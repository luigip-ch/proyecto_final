import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_predict_manizales_integration(client):
    """Verifica que la API genere predicción para la lotería Manizales."""
    response = await client.post("/api/predict", json={"lottery": "manizales"})

    assert response.status_code == 200

    data = response.json()
    assert "prediction" in data
    assert "main_numbers" in data["prediction"]
    assert len(data["prediction"]["main_numbers"]) == 4
    assert "serie" in data["prediction"]
    assert isinstance(data["prediction"]["serie"], str)
    assert len(data["prediction"]["serie"]) == 3
    assert "statistics" in data
    assert "generated_at" in data
