import os

import numpy as np
import pandas as pd

from app.config import BASE_DATA_DIR, PRIZE_TYPE_FILTER
from app.ml.base_model import BaseModel

_DEFAULT_DATA_PATH = os.path.join(
    BASE_DATA_DIR, "loteria_cundinamarca", "cundinamarca_historico.csv"
)


class CundinamarcaModel(BaseModel):
    """
    Frequency-Weighted Multinomial Sampling para la Lotería de Cundinamarca.

    Se descompone cada número ganador en sus posiciones (miles, centenas,
    decenas, unidades) y se construye una distribución de probabilidad
    empírica por posición. La predicción muestrea independientemente
    cada posición, respetando las frecuencias históricas.
    """

    def __init__(self, data_path: str | None = None) -> None:
        self.data_path: str = data_path or os.path.normpath(_DEFAULT_DATA_PATH)
        self.df: pd.DataFrame | None = None
        self.frecuencias: dict | None = None

    def load_data(self) -> None:
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Archivo de datos no encontrado: {self.data_path}")

        df = pd.read_csv(self.data_path)
        self.df = df[df["Tipo de Premio"] == PRIZE_TYPE_FILTER].copy()

    def train(self) -> None:
        if self.df is None:
            raise RuntimeError("Debe llamar a load_data() antes de train()")

        numeros = self.df["Numero billete ganador"].astype(int)

        self.frecuencias = {
            "miles":    self._build_freq(numeros // 1000 % 10),
            "centenas": self._build_freq(numeros // 100 % 10),
            "decenas":  self._build_freq(numeros // 10 % 10),
            "unidades": self._build_freq(numeros % 10),
        }

    def predict(self, seed: int | None = None) -> list[int]:
        if self.frecuencias is None:
            raise RuntimeError("Debe llamar a train() antes de predict()")

        rng = np.random.default_rng(seed)

        miles     = self._sample(rng, self.frecuencias["miles"])
        centenas  = self._sample(rng, self.frecuencias["centenas"])
        decenas   = self._sample(rng, self.frecuencias["decenas"])
        unidades  = self._sample(rng, self.frecuencias["unidades"])

        # Retornamos los 4 dígitos por separado para preservar los ceros a la
        # izquierda. Combinar en un entero (ej. 0048 → 48) perdía las cifras
        # de orden mayor cuando miles o centenas eran 0.
        series = self.df["Numero serie ganadora"].astype(int).values
        serie = int(rng.choice(series))

        return [miles, centenas, decenas, unidades, serie]

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _build_freq(digits: pd.Series) -> dict:
        counts = digits.value_counts().sort_index()
        total = counts.sum()
        return {int(d): int(c) / total for d, c in counts.items()}

    @staticmethod
    def _sample(rng: np.random.Generator, freq: dict) -> int:
        digits = list(freq.keys())
        probs = list(freq.values())
        return int(rng.choice(digits, p=probs))
