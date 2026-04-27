from app.backend.selector import get_model
from app.ml.base_model import BaseModel


class ModelTrainer:
    """Orquesta el ciclo load_data → train para un modelo registrado."""

    def __init__(
        self,
        lottery: str,
        model: BaseModel | None = None,
    ) -> None:
        self.lottery = lottery
        self._model = model
        self.trained: bool = False

    def run(self) -> None:
        model = self._model if self._model is not None else get_model(
            self.lottery
        )
        model.load_data()
        model.train()
        self.trained = True
