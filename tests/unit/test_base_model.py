"""Valida el contrato abstracto que deben cumplir los modelos ML."""

import pytest
from app.ml.base_model import BaseModel


# ── RED: estas pruebas fallarán hasta que base_model.py exista ──


@pytest.mark.unit
def test_cannot_instantiate_base_model_directly():
    """Verifica que la interfaz abstracta no pueda instanciarse."""
    with pytest.raises(TypeError):
        BaseModel()


@pytest.mark.unit
def test_subclass_missing_train_cannot_be_instantiated():
    """Verifica que una subclase sin ``train`` siga siendo abstracta."""
    class MissingTrain(BaseModel):
        """Subclase incompleta que omite el método ``train``."""

        def load_data(self) -> None:
            """Implementa carga de datos para aislar la ausencia de train."""
            pass

        def predict(self) -> list[int]:
            """Implementa predicción para aislar la ausencia de train."""
            return []

    with pytest.raises(TypeError):
        MissingTrain()


@pytest.mark.unit
def test_subclass_missing_predict_cannot_be_instantiated():
    """Verifica que una subclase sin ``predict`` siga siendo abstracta."""
    class MissingPredict(BaseModel):
        """Subclase incompleta que omite el método ``predict``."""

        def load_data(self) -> None:
            """Implementa carga de datos para aislar la ausencia de predict."""
            pass

        def train(self) -> None:
            """Implementa entrenamiento para aislar la ausencia de predict."""
            pass

    with pytest.raises(TypeError):
        MissingPredict()


@pytest.mark.unit
def test_subclass_missing_load_data_cannot_be_instantiated():
    """Verifica que una subclase sin ``load_data`` siga siendo abstracta."""
    class MissingLoadData(BaseModel):
        """Subclase incompleta que omite el método ``load_data``."""

        def train(self) -> None:
            """Implementa entrenamiento para aislar la ausencia de load_data."""
            pass

        def predict(self) -> list[int]:
            """Implementa predicción para aislar la ausencia de load_data."""
            return []

    with pytest.raises(TypeError):
        MissingLoadData()


@pytest.mark.unit
def test_valid_subclass_can_be_instantiated(concrete_model):
    """Verifica que una subclase completa pueda instanciarse."""
    assert concrete_model is not None


@pytest.mark.unit
def test_predict_returns_list(concrete_model):
    """Verifica que ``predict`` retorne una lista."""
    concrete_model.load_data()
    result = concrete_model.predict()
    assert isinstance(result, list)


@pytest.mark.unit
def test_predict_returns_list_of_ints(concrete_model):
    """Verifica que la predicción contenga solo enteros."""
    concrete_model.load_data()
    result = concrete_model.predict()
    assert all(isinstance(n, int) for n in result)
