from fastapi import BackgroundTasks, HTTPException
from unittest.mock import MagicMock, patch

import pytest

from app.backend.api import train as train_module
from app.backend.api.schemas import LotteryRequest


@pytest.mark.unit
class TestApiTrainEndpoint:
    def setup_method(self):
        train_module._jobs.clear()

    def test_train_queues_job_and_returns_job_id(self):
        background_tasks = BackgroundTasks()
        mock_model = MagicMock()

        with patch("app.backend.api.train.get_model", return_value=mock_model):
            result = train_module.train(
                LotteryRequest(lottery="cundinamarca"),
                background_tasks,
            )

        assert result["status"] == "queued"
        assert result["lottery"] == "cundinamarca"
        assert isinstance(result["job_id"], str)
        assert result["job_id"] in train_module._jobs
        assert train_module._jobs[result["job_id"]]["status"] == "queued"

    def test_train_status_returns_existing_job(self):
        job_id = "test-job"
        train_module._jobs[job_id] = {
            "status": "queued",
            "lottery": "bogota",
            "error": None,
        }

        status = train_module.train_status(job_id)

        assert status["job_id"] == job_id
        assert status["status"] == "queued"
        assert status["lottery"] == "bogota"
        assert status["error"] is None

    def test_train_status_raises_404_for_unknown_job(self):
        with pytest.raises(HTTPException, match="job 'missing' no encontrado"):
            train_module.train_status("missing")

    def test_train_raises_404_for_unknown_lottery(self):
        background_tasks = BackgroundTasks()

        with patch(
            "app.backend.api.train.get_model",
            side_effect=ValueError("lotería no registrada"),
        ):
            with pytest.raises(HTTPException, match="lotería no registrada"):
                train_module.train(
                    LotteryRequest(lottery="inexistente"),
                    background_tasks,
                )
