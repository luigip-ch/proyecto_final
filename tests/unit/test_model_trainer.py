"""Valida el orquestador de entrenamiento de modelos registrados."""

import pytest
from unittest.mock import MagicMock, call

from app.backend.model_trainer import ModelTrainer


@pytest.mark.unit
class TestModelTrainerInterface:
    def test_instantiates_with_lottery_name(self):
        trainer = ModelTrainer("cundinamarca")
        assert trainer is not None

    def test_stores_lottery_name(self):
        trainer = ModelTrainer("cundinamarca")
        assert trainer.lottery == "cundinamarca"


@pytest.mark.unit
class TestModelTrainerRun:
    def test_run_calls_load_data(self):
        mock_model = MagicMock()
        trainer = ModelTrainer("cundinamarca", model=mock_model)
        trainer.run()
        mock_model.load_data.assert_called_once()

    def test_run_calls_train_after_load(self):
        mock_model = MagicMock()
        trainer = ModelTrainer("cundinamarca", model=mock_model)
        trainer.run()
        expected = [call.load_data(), call.train()]
        assert mock_model.mock_calls == expected

    def test_run_raises_for_unknown_lottery(self):
        with pytest.raises(ValueError, match="lotería no registrada"):
            trainer = ModelTrainer("inexistente")
            trainer.run()

    def test_run_sets_trained_true_on_success(self):
        mock_model = MagicMock()
        trainer = ModelTrainer("cundinamarca", model=mock_model)
        trainer.run()
        assert trainer.trained is True

    def test_run_sets_trained_false_initially(self):
        mock_model = MagicMock()
        trainer = ModelTrainer("cundinamarca", model=mock_model)
        assert trainer.trained is False
