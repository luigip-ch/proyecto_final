"""Valida el orquestador de entrenamiento de modelos registrados."""

import pytest
from unittest.mock import MagicMock, call

from app.backend.model_trainer import ModelTrainer


@pytest.mark.unit
class TestModelTrainerInterface:
    """Pruebas de inicialización del orquestador de entrenamiento."""

    def test_instantiates_with_lottery_name(self):
        """Verifica que el trainer pueda crearse con un slug de lotería."""
        trainer = ModelTrainer("cundinamarca")
        assert trainer is not None

    def test_stores_lottery_name(self):
        """Verifica que el trainer conserve el slug recibido."""
        trainer = ModelTrainer("cundinamarca")
        assert trainer.lottery == "cundinamarca"


@pytest.mark.unit
class TestModelTrainerRun:
    """Pruebas del ciclo ``load_data`` seguido de ``train``."""

    def test_run_calls_load_data(self):
        """Verifica que ``run`` invoque la carga de datos del modelo."""
        mock_model = MagicMock()
        trainer = ModelTrainer("cundinamarca", model=mock_model)
        trainer.run()
        mock_model.load_data.assert_called_once()

    def test_run_calls_train_after_load(self):
        """Verifica que ``train`` se ejecute después de ``load_data``."""
        mock_model = MagicMock()
        trainer = ModelTrainer("cundinamarca", model=mock_model)
        trainer.run()
        expected = [call.load_data(), call.train()]
        assert mock_model.mock_calls == expected

    def test_run_raises_for_unknown_lottery(self):
        """Verifica que una lotería desconocida propague ``ValueError``."""
        with pytest.raises(ValueError, match="lotería no registrada"):
            trainer = ModelTrainer("inexistente")
            trainer.run()

    def test_run_sets_trained_true_on_success(self):
        """Verifica que ``trained`` quede en ``True`` tras un entrenamiento."""
        mock_model = MagicMock()
        trainer = ModelTrainer("cundinamarca", model=mock_model)
        trainer.run()
        assert trainer.trained is True

    def test_run_sets_trained_false_initially(self):
        """Verifica que ``trained`` inicie en ``False``."""
        mock_model = MagicMock()
        trainer = ModelTrainer("cundinamarca", model=mock_model)
        assert trainer.trained is False
