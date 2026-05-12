"""Modelo de predicción para la Lotería de Medellín.

Implementa ``BaseModel`` con la estrategia FWMS
(Frequency-Weighted Multinomial Sampling): cada posición del número
ganador (miles, centenas, decenas, unidades) se muestrea de forma
independiente usando una distribución de probabilidad empírica
construida a partir del histórico de resultados.

Fuente de datos:
    CSV en ``bd/historical/loteria_medellin/medellin_historico.csv``.
    Columnas requeridas:

    - ``Tipo de Premio``           (str)  — filtrado por ``PRIZE_TYPE_FILTER``
    - ``Numero billete ganador``   (int)  — número de 4 dígitos (ej. 1234)
    - ``Numero serie ganadora``    (int)  — serie de hasta 3 dígitos (ej. 42)
"""

import os

import numpy as np
import pandas as pd

from app.config import BASE_DATA_DIR, PRIZE_TYPE_FILTER
from app.ml.base_model import BaseModel

_DEFAULT_DATA_PATH = os.path.join(
    BASE_DATA_DIR, "loteria_medellin", "medellin_historico.csv"
)


class MedellinModel(BaseModel):
    """Modelo FWMS (Frequency-Weighted Multinomial Sampling) para la Lotería
    de Medellín.

    Cada número ganador de 4 dígitos se descompone en sus posiciones
    (miles, centenas, decenas, unidades) y se construye una distribución
    de probabilidad empírica por posición. La predicción muestrea
    independientemente cada posición, respetando las frecuencias históricas.
    La serie se elige uniformemente del conjunto histórico de series
    ganadoras.

    Attributes:
        data_path (str): Ruta absoluta al CSV de datos históricos.
        df (pd.DataFrame | None): DataFrame filtrado por premio mayor;
            ``None`` hasta que se llame ``load_data()``.
        frecuencias (dict | None): Distribuciones de probabilidad por
            posición; ``None`` hasta que se llame ``train()``.
    """

    def __init__(self, data_path: str | None = None) -> None:
        """Inicializa el modelo con la ruta al CSV de datos históricos.

        Args:
            data_path: Ruta absoluta al CSV. Si es ``None`` se usa la
                ruta por defecto configurada en ``app.config``.
        """
        self.data_path: str = data_path or os.path.normpath(_DEFAULT_DATA_PATH)
        self.df: pd.DataFrame | None = None
        self.frecuencias: dict | None = None

    def load_data(self) -> None:
        """Carga el CSV histórico y filtra solo los registros de premio mayor.

        Lee ``self.data_path``, filtra las filas donde ``Tipo de Premio``
        coincide con ``PRIZE_TYPE_FILTER`` y almacena el resultado en
        ``self.df``.

        Raises:
            FileNotFoundError: si ``self.data_path`` no existe en disco.
        """
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Archivo de datos no encontrado: {self.data_path}")

        df = pd.read_csv(self.data_path)
        self.df = df[df["Tipo de Premio"] == PRIZE_TYPE_FILTER].copy()

    def train(self) -> None:
        """Construye las distribuciones de frecuencia por posición del número.

        A partir de ``self.df`` extrae la columna ``Numero billete ganador``,
        descompone cada valor en sus 4 dígitos (miles, centenas, decenas,
        unidades) y calcula la probabilidad empírica de cada dígito (0-9)
        por posición. El resultado se almacena en ``self.frecuencias``.

        Raises:
            RuntimeError: si ``self.df`` es ``None`` (``load_data()`` no
                fue llamado previamente).
        """
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
        """Genera una predicción muestreando cada posición de forma independiente.

        Cada dígito se extrae de su distribución empírica con probabilidad
        proporcional a su frecuencia histórica. Los 4 dígitos se devuelven
        **por separado** para preservar los ceros a la izquierda (p. ej.
        ``0048`` → ``[0, 0, 4, 8]``). La serie se selecciona uniformemente
        del conjunto histórico de series ganadoras.

        Args:
            seed: Semilla opcional para reproducibilidad. ``None`` produce
                resultados aleatorios en cada llamada.

        Returns:
            Lista ``[miles, centenas, decenas, unidades, serie]`` donde cada
            dígito es un entero en ``[0, 9]`` y la serie es un entero en
            ``[0, 999]``.

        Raises:
            RuntimeError: si ``self.frecuencias`` es ``None`` (``train()``
                no fue llamado previamente).
        """
        if self.frecuencias is None:
            raise RuntimeError("Debe llamar a train() antes de predict()")

        rng = np.random.default_rng(seed)

        miles     = self._sample(rng, self.frecuencias["miles"])
        centenas  = self._sample(rng, self.frecuencias["centenas"])
        decenas   = self._sample(rng, self.frecuencias["decenas"])
        unidades  = self._sample(rng, self.frecuencias["unidades"])

        series = self.df["Numero serie ganadora"].astype(int).values
        serie = int(rng.choice(series))

        return [miles, centenas, decenas, unidades, serie]

    # ── helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _build_freq(digits: pd.Series) -> dict:
        """Construye un diccionario de probabilidades empíricas para una posición.

        Args:
            digits: Serie de enteros (0-9) correspondiente a una posición
                del número ganador en todos los sorteos históricos.

        Returns:
            Diccionario ``{dígito: probabilidad}`` donde la suma de
            probabilidades es 1.0.
        """
        counts = digits.value_counts().sort_index()
        total = counts.sum()
        return {int(d): int(c) / total for d, c in counts.items()}

    @staticmethod
    def _sample(rng: np.random.Generator, freq: dict) -> int:
        """Muestrea un dígito de acuerdo con su distribución de probabilidad.

        Args:
            rng: Generador de números aleatorios de NumPy.
            freq: Diccionario ``{dígito: probabilidad}`` producido por
                ``_build_freq()``.

        Returns:
            Entero en ``[0, 9]`` seleccionado según la distribución ``freq``.
        """
        digits = list(freq.keys())
        probs = list(freq.values())
        return int(rng.choice(digits, p=probs))
