import pytest
from app.ml.base_model import BaseModel


class ConcreteTestModel(BaseModel):
    """Implementación concreta mínima para validar el contrato de BaseModel."""

    def load_data(self) -> None:
        self.data = [1, 2, 3, 4, 5]

    def train(self) -> None:
        pass

    def predict(self) -> list[int]:
        return [1, 2, 3]


@pytest.fixture
def concrete_model():
    return ConcreteTestModel()
