# Modelo de predicción para la Lotería de Manizales.

import os
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor

from app.config import BASE_DATA_DIR
from app.ml.base_model import BaseModel

_DEFAULT_DATA_PATH = os.path.join(
    BASE_DATA_DIR, "loteria_de_manizales", "loteria_de_manizales_historico.csv"
)

# Configuración del modelo
_RANDOM_SEED = 42


class ManizalesModel(BaseModel):
    """
    Modelo RandomForest para la Lotería de Manizales.

    Entrena un modelo que aprende la relación entre características
    temporales (día, mes, día de la semana) y el resultado histórico
    (dígitos del número y serie).

    Attributes:
        data_path (str): Ruta absoluta al CSV de datos históricos.
        df (pd.DataFrame | None): DataFrame cargado; ``None`` hasta que
            se llame ``load_data()``.
        model (MultiOutputRegressor | None): Modelo entrenado; ``None`` hasta que
            se llame ``train()``.
    """

    def __init__(self, data_path: str | None = None) -> None:
        """
        Inicializa el modelo con la ruta al CSV de datos históricos.

        Args:
            data_path: Ruta absoluta al CSV. Si es ``None`` se usa la
                ruta por defecto configurada.
        """
        self.data_path: str = data_path or os.path.normpath(_DEFAULT_DATA_PATH)
        self.df: pd.DataFrame | None = None
        self.model: MultiOutputRegressor | None = None

    def load_data(self) -> None:
        """
        Carga el CSV histórico y prepara las características.

        Lee ``self.data_path``, filtra por premio mayor, procesa fechas
        y extrae dígitos. Almacena el resultado en ``self.df``.

        Raises:
            FileNotFoundError: si ``self.data_path`` no existe en disco.
        """
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(
                f"Archivo de datos no encontrado: {self.data_path}")

        df = pd.read_csv(self.data_path)
        # Filtrar solo por el Premio Mayor
        df_mayor = df[df['Tipo de Premio'] == 'Mayor'].copy()

        # Formatear fechas
        df_mayor['Fecha del Sorteo'] = pd.to_datetime(
            df_mayor['Fecha del Sorteo'], dayfirst=True)
        df_mayor = df_mayor.sort_values('Fecha del Sorteo')

        # Preprocesamiento
        df_mayor['billete_full'] = df_mayor['Numero billete ganador'].astype(
            str).str.zfill(4)

        # Descomponer en 4 columnas (una por dígito)
        for i in range(4):
            df_mayor[f'd{i}'] = df_mayor['billete_full'].str[i].astype(int)

        # Extraer características temporales
        df_mayor['day'] = df_mayor['Fecha del Sorteo'].dt.day
        df_mayor['month'] = df_mayor['Fecha del Sorteo'].dt.month
        df_mayor['weekday'] = df_mayor['Fecha del Sorteo'].dt.weekday

        self.df = df_mayor

    def train(self) -> None:
        """
        Entrena el modelo RandomForest con los datos cargados.

        Utiliza características temporales (day, month, weekday) para predecir
        los dígitos del número y la serie.

        Raises:
            RuntimeError: si ``self.df`` es ``None`` (``load_data()`` no
                fue llamado previamente).
        """
        if self.df is None:
            raise RuntimeError("Debe llamar a load_data() antes de train()")

        X = self.df[['day', 'month', 'weekday']]
        y = self.df[['d0', 'd1', 'd2', 'd3', 'Numero serie ganadora']]

        self.model = MultiOutputRegressor(
            RandomForestRegressor(n_estimators=100, random_state=_RANDOM_SEED))
        self.model.fit(X, y)
        print("✔ Modelo Manizales entrenado.")

    def predict(self) -> list[int]:
        """
        Genera predicción para el próximo sorteo.

        Utiliza la fecha actual para proyectar el siguiente sorteo.
        Retorna [d0, d1, d2, d3, serie], donde d0-d3 son los dígitos del número.

        Returns:
            Lista con cinco enteros: [d0, d1, d2, d3, serie_predicha]

        Raises:
            RuntimeError: si el modelo no ha sido entrenado (``train()``
                no fue llamado previamente).
        """
        if self.model is None:
            raise RuntimeError("Debe llamar a train() antes de predict()")

        now = datetime.now()
        features = [[now.day, now.month, now.weekday()]]
        pred = self.model.predict(features)[0]

        # Normalizar dígitos
        digits = [int(round(d)) % 10 for d in pred[:4]]
        serie = int(round(pred[4])) % 1000

        return digits + [serie]
