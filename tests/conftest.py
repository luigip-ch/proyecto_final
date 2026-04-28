"""Define fixtures compartidas por las pruebas unitarias e integración."""

import pytest
from app.backend import model_store
from app.ml.base_model import BaseModel


def pytest_configure(config):
    """Registra marcas usadas por la suite aunque el runner ignore pytest.ini."""
    config.addinivalue_line(
        "markers",
        "unit: pruebas unitarias aisladas",
    )
    config.addinivalue_line(
        "markers",
        "integration: pruebas de endpoints API",
    )
    config.addinivalue_line(
        "markers",
        "slow: pruebas de entrenamiento (omitir en CI rápido)",
    )


@pytest.fixture(autouse=True)
def clean_trained_model_store(monkeypatch, tmp_path):
    """Aísla cada prueba limpiando modelos entrenados en memoria y disco."""
    monkeypatch.setattr(model_store, "MODEL_STORE_DIR", str(tmp_path / "models"))
    model_store.clear_trained_models(delete_files=True)
    yield
    model_store.clear_trained_models(delete_files=True)


class ConcreteTestModel(BaseModel):
    """Implementación concreta mínima para validar el contrato de BaseModel."""

    def load_data(self) -> None:
        """Simula la carga de datos del modelo concreto de prueba."""
        self.data = [1, 2, 3, 4, 5]

    def train(self) -> None:
        """Simula un entrenamiento exitoso sin efectos secundarios."""
        pass

    def predict(self) -> list[int]:
        """Devuelve una predicción fija para validar el tipo de retorno."""
        return [1, 2, 3]


@pytest.fixture
def concrete_model():
    """Entrega una instancia concreta reutilizable de ``BaseModel``."""
    return ConcreteTestModel()
