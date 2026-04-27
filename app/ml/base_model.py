"""
Contrato base para todos los modelos ML de predicción de loterias.

Cualquier lotería nueva debe crear una subclase de ``BaseModel`` e
implementar los tres métodos abstractos. El selector y los endpoints
interactúan exclusivamente con esta interfaz, de modo que agregar una
nueva lotería no modifica ningún otro módulo.
"""

from abc import ABC, abstractmethod


class BaseModel(ABC):
    """
    Interfaz común para los modelos de predicción de loterias.

    Ciclo de vida obligatorio::

        model.load_data()  # 1. carga y filtra datos históricos
        model.train()      # 2. ajusta el modelo
        result = model.predict()  # 3. genera predicción

    Los tres métodos deben ejecutarse en ese orden. Las implementaciones
    concretas deben lanzar ``RuntimeError`` si se invoca un método antes
    de completar el paso anterior.
    """

    @abstractmethod
    def load_data(self) -> None:
        """
        Carga los datos históricos de la lotería desde la fuente configurada.

        Filtra únicamente los registros relevantes (p. ej. premio mayor)
        y los almacena internamente para que ``train()`` los consuma.

        Raises:
            FileNotFoundError: si el archivo de datos no existe en la ruta
                configurada.
        """
        ...

    @abstractmethod
    def train(self) -> None:
        """
        Entrena el modelo con los datos cargados por ``load_data()``.

        Construye las estructuras internas (distribuciones de frecuencia,
        pesos, etc.) que luego usa ``predict()`` para generar la predicción.

        Raises:
            RuntimeError: si se llama antes de ``load_data()``.
        """
        ...

    @abstractmethod
    def predict(self) -> list[int]:
        """
        Genera una predicción basada en el modelo entrenado.

        Returns:
            Lista de cinco enteros con el formato
            ``[miles, centenas, decenas, unidades, serie]``.
            Los primeros cuatro elementos son dígitos individuales (0-9);
            el último es el número de serie (0-999).

        Raises:
            RuntimeError: si se llama antes de ``train()``.
        """
        ...
