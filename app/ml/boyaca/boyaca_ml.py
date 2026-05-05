"""Modelo de predicción para la Lotería de Boyacá.

Implementa un algoritmo inspirado en el FWMS de Cundinamarca:
- Distribución empírica por posición de dígitos (miles, centenas, decenas, unidades)
- Serie muestreada según su frecuencia histórica
- Reglas de validación estadística post-generación basadas en el histórico
"""

import os

import numpy as np
import pandas as pd

from app.ml.base_model import BaseModel

BASE_DATA_DIR = "app/bd/historical"
PRIZE_TYPE_FILTER = "Mayor"

_DEFAULT_DATA_PATH = os.path.join(
    BASE_DATA_DIR, "loteria_boyaca", "boyaca_historico.csv"
)


class BoyacaModel(BaseModel):
    """
    Modelo FWMS con validación histórica para la Lotería de Boyacá.

    Este modelo aprovecha el contrato de la API existente para loterías de
    4 cifras + serie. Carga los datos históricos del CSV de Boyacá, construye
    distribuciones de probabilidad empíricas por posición, y genera una predicción
    que valida la paridad, la suma de dígitos y la diversidad de dígitos.
    """

    def __init__(self, data_path: str | None = None) -> None:
        self.data_path: str = data_path or os.path.normpath(_DEFAULT_DATA_PATH)
        self.df: pd.DataFrame | None = None
        self.frecuencias: dict | None = None
        self.serie_frecuencias: dict | None = None
        self.sum_range: tuple[int, int] | None = None
        self.valid_even_counts: set[int] | None = None

    def load_data(self) -> None:
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Archivo de datos no encontrado: {self.data_path}")

        df = pd.read_csv(self.data_path)
        self.df = df[df["Tipo de Premio"] == PRIZE_TYPE_FILTER].copy()

    def train(self) -> None:
        if self.df is None:
            raise RuntimeError("Debe llamar a load_data() antes de train()")

        numeros = self.df["Numero billete ganador"].astype(int)
        series = self.df["Numero serie ganadora"].astype(int)

        self.frecuencias = {
            "miles":    self._build_freq(numeros // 1000 % 10),
            "centenas": self._build_freq(numeros // 100 % 10),
            "decenas":  self._build_freq(numeros // 10 % 10),
            "unidades": self._build_freq(numeros % 10),
        }
        self.serie_frecuencias = self._build_freq(series)

        digits = numeros.apply(lambda x: [int(d) for d in f"{x:04d}"])
        sums = digits.apply(sum).astype(int)
        self.sum_range = (int(sums.min()), int(sums.max()))

        even_counts = digits.apply(lambda d: sum(1 for n in d if n % 2 == 0))
        self.valid_even_counts = set(int(c) for c in even_counts.unique())

    def predict(self, seed: int | None = None) -> list[int]:
        if self.frecuencias is None or self.serie_frecuencias is None:
            raise RuntimeError("Debe llamar a train() antes de predict()")

        rng = np.random.default_rng(seed)
        candidate: list[int] | None = None

        for _ in range(10):
            miles = self._sample(rng, self.frecuencias["miles"])
            centenas = self._sample(rng, self.frecuencias["centenas"])
            decenas = self._sample(rng, self.frecuencias["decenas"])
            unidades = self._sample(rng, self.frecuencias["unidades"])
            serie = self._sample(rng, self.serie_frecuencias)

            candidate = [miles, centenas, decenas, unidades, serie]
            if self._is_valid_number(candidate[:4]):
                return candidate

        # Si no se encuentra una opción validada en 10 intentos, se devuelve
        # la última candidata generada. El modelo sigue siendo consistente
        # con las distribuciones entrenadas.
        assert candidate is not None
        return candidate

    def _is_valid_number(self, digits: list[int]) -> bool:
        if len(set(digits)) == 1:
            return False

        if self.sum_range is None or self.valid_even_counts is None:
            return False

        total = sum(digits)
        if not (self.sum_range[0] <= total <= self.sum_range[1]):
            return False

        even_count = sum(1 for d in digits if d % 2 == 0)
        if even_count not in self.valid_even_counts:
            return False

        return True

    @staticmethod
    def _build_freq(values: pd.Series) -> dict:
        counts = values.value_counts().sort_index()
        total = counts.sum()
        return {int(v): int(c) / total for v, c in counts.items()}

    @staticmethod
    def _sample(rng: np.random.Generator, freq: dict) -> int:
        digits = list(freq.keys())
        probs = list(freq.values())
        return int(rng.choice(digits, p=probs))
