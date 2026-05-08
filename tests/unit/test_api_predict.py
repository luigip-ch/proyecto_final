from fastapi import HTTPException
from unittest.mock import MagicMock, patch

import pytest

from app.backend.api.predict import predict
from app.backend.api.schemas import LotteryRequest


@pytest.mark.unit
class TestApiPredictEndpoint:
    def test_predict_raises_404_for_unknown_lottery(self):
        with patch(
            "app.backend.api.predict.get_model",
            side_effect=ValueError("lotería no registrada"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                predict(LotteryRequest(lottery="inexistente"))

        assert exc_info.value.status_code == 404
        assert "lotería no registrada" in exc_info.value.detail

    def test_predict_returns_expected_structure_for_cundinamarca(self):
        mock_model = MagicMock()
        mock_model.predict.return_value = [1, 2, 3, 4, 55]

        with patch("app.backend.api.predict.get_model", return_value=mock_model):
            result = predict(LotteryRequest(lottery="cundinamarca"))

        assert result["lottery"] == "cundinamarca"
        assert result["prediction"]["main_numbers"] == [1, 2, 3, 4]
        assert result["prediction"]["serie"] == "055"
        assert result["prediction"]["special_number"] is None
        assert result["statistics"]["sum"] == 10
        assert result["statistics"]["even_count"] == 2
        assert result["statistics"]["odd_count"] == 2
        assert result["statistics"]["even_odd_ratio"] == "2:2"
        assert result["statistics"]["sum_in_optimal_range"] is True
        assert result["statistics"]["optimal_sum_range"] == {"min": 10, "max": 26}
