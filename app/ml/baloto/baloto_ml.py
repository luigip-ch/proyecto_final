"""
Modelo de predicción para Baloto.

Implementa ``BaseModel`` con muestreo basado en frecuencias históricas.
Se crea una distribución conjunta para las 5 balotas principales (n1 a n5)
y otra distribución para la superbalota.

Fuente de datos:
    CSV en ``bd/historical/baloto/baloto_historico.csv``.
    Columnas requeridas:
    - ``n1, n2, n3, n4, n5`` (int) — balotas principales
    - ``superbalota``        (int) — balota especial
"""

import os
import numpy as np
import pandas as pd

from app.config import BASE_DATA_DIR
from app.ml.base_model import BaseModel

_DEFAULT_DATA_PATH = os.path.join(
    BASE_DATA_DIR, "baloto", "baloto_historico.csv"
)

class BalotoModel(BaseModel):
    """
    Modelo basado en frecuencias históricas para Baloto.

    Las 5 balotas principales se extraen sin reemplazo de una distribución 
    construida con la aparición histórica de números en cualquiera de las 5 posiciones.
    La superbalota se extrae de su propia distribución histórica.
    """

    def __init__(self, data_path: str | None = None) -> None:
        self.data_path: str = data_path or os.path.normpath(_DEFAULT_DATA_PATH)
        self.df: pd.DataFrame | None = None
        self.frecuencias_principales: dict | None = None
        self.frecuencias_superbalota: dict | None = None

    def load_data(self) -> None:
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Archivo de datos no encontrado: {self.data_path}")

        # Baloto no tiene "Tipo de Premio", usamos todos los registros
        self.df = pd.read_csv(self.data_path)

    def train(self) -> None:
        if self.df is None:
            raise RuntimeError("Debe llamar a load_data() antes de train()")

        # Consolidar las 5 balotas principales
        balotas_principales = pd.concat([
            self.df["n1"], self.df["n2"], self.df["n3"], 
            self.df["n4"], self.df["n5"]
        ]).astype(int)

        self.frecuencias_principales = self._build_freq(balotas_principales)
        
        # Frecuencias para superbalota
        superbalotas = self.df["superbalota"].astype(int)
        self.frecuencias_superbalota = self._build_freq(superbalotas)

    def predict(self, seed: int | None = None) -> list[int]:
        if self.frecuencias_principales is None or self.frecuencias_superbalota is None:
            raise RuntimeError("Debe llamar a train() antes de predict()")

        rng = np.random.default_rng(seed)

        digits_princ = list(self.frecuencias_principales.keys())
        probs_princ = list(self.frecuencias_principales.values())

        # Muestrear 5 balotas sin reemplazo
        prediccion_principal = rng.choice(
            digits_princ, size=5, replace=False, p=probs_princ
        ).tolist()
        
        # Ordenamos las balotas principales por convención de presentación
        prediccion_principal.sort()
        prediccion_principal = [int(x) for x in prediccion_principal]

        digits_super = list(self.frecuencias_superbalota.keys())
        probs_super = list(self.frecuencias_superbalota.values())

        # Muestrear 1 superbalota
        superbalota = int(rng.choice(digits_super, p=probs_super))

        return prediccion_principal + [superbalota]

    @staticmethod
    def _build_freq(digits: pd.Series) -> dict:
        counts = digits.value_counts().sort_index()
        total = counts.sum()
        return {int(d): float(c) / total for d, c in counts.items()}
