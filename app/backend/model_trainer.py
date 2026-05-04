"""Centraliza la ejecución del ciclo de entrenamiento de modelos registrados."""

from app.backend.selector import get_model
from app.ml.base_model import BaseModel


class ModelTrainer:
    """Orquesta el ciclo load_data → train para un modelo registrado."""

    def __init__(
        self,
        lottery: str,
        model: BaseModel | None = None,
    ) -> None:
        """
        Configura el entrenador para una lotería o modelo específico.

        Args:
            lottery: Slug de la lotería a entrenar cuando no se inyecta modelo.
            model: Modelo opcional para pruebas o ejecución controlada.
        """
        self.lottery = lottery
        self._model = model
        self.trained: bool = False

    def run(self) -> None:
        """
        Carga los datos y entrena el modelo seleccionado.

        Si no se inyectó un modelo en el constructor, lo obtiene desde el
        registro central usando ``self.lottery``. Al terminar marca
        ``self.trained`` como ``True``.
        """
        model = self._model if self._model is not None else get_model(
            self.lottery
        )
        model.load_data()
        model.train()
        self.trained = True
