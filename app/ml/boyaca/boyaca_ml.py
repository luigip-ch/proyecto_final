"""Modelo de predicción para la Lotería de Boyacá.

Implementa ``BaseModel`` usando un enfoque supervisado con árboles de
clasificación. El objetivo es capturar la dependencia temporal y la
correlación entre los dígitos del número ganador y la serie, en lugar de
tratar cada posición de forma completamente independiente.

Fuente de datos:
    CSV en ``bd/historical/loteria_boyaca/boyaca_historico.csv``.
    Columnas requeridas:

    - ``Tipo de Premio``           (str)  — filtrado por ``PRIZE_TYPE_FILTER``
    - ``Numero billete ganador``   (int)  — número de 4 dígitos (ej. 1234)
    - ``Numero serie ganadora``    (int)  — serie de hasta 3 dígitos (ej. 42)
    - ``Fecha del Sorteo``         (str)  — fecha del sorteo, se usa para extraer
      componentes temporales.
    - ``Número del Sorteo``        (int)  — secuencia del sorteo, usada como
      referencia temporal.
"""

import os

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from app.config import PRIZE_TYPE_FILTER
from app.ml.base_model import BaseModel

_DEFAULT_DATA_PATH = os.path.normpath(
    os.path.join("app", "bd", "historical", "loteria_boyaca", "boyaca_historico.csv")
)


class BoyacaModel(BaseModel):
    """
    Modelo supervisado para la Lotería de Boyacá.

    Construye clasificadores por posición de dígito y por dígitos de la
    serie. Usa características temporales y el resultado del sorteo anterior
    para capturar dependencias secuenciales en los datos históricos.
    """

    def __init__(self, data_path: str | None = None) -> None:
        self.data_path: str = data_path or os.path.normpath(_DEFAULT_DATA_PATH)
        self.df: pd.DataFrame | None = None
        self.models: dict[str, RandomForestClassifier] | None = None
        self.last_features: pd.DataFrame | None = None

    def load_data(self) -> None:
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Archivo de datos no encontrado: {self.data_path}")

        df = pd.read_csv(self.data_path)
        df = df[df["Tipo de Premio"] == PRIZE_TYPE_FILTER].copy()

        df["Fecha del Sorteo"] = pd.to_datetime(
            df["Fecha del Sorteo"], dayfirst=True, errors="coerce"
        )
        df["Año"] = df["Fecha del Sorteo"].dt.year.fillna(0).astype(int)
        df["Mes"] = df["Fecha del Sorteo"].dt.month.fillna(0).astype(int)
        df["DiaSemana"] = df["Fecha del Sorteo"].dt.dayofweek.fillna(0).astype(int)

        df["Numero del Sorteo"] = (
            df["Número del Sorteo"].astype(str)
            .str.extract(r"(\d+)", expand=False)
            .fillna("0")
            .astype(int)
        )

        df["Numero billete ganador"] = (
            df["Numero billete ganador"].astype(str)
            .str.extract(r"(\d+)", expand=False)
            .fillna("0")
            .astype(int)
        )

        df["Numero serie ganadora"] = (
            df["Numero serie ganadora"].astype(str)
            .str.extract(r"(\d+)", expand=False)
            .fillna("0")
            .astype(int)
        )

        df = df.sort_values("Fecha del Sorteo").reset_index(drop=True)

        df["miles"] = df["Numero billete ganador"] // 1000 % 10
        df["centenas"] = df["Numero billete ganador"] // 100 % 10
        df["decenas"] = df["Numero billete ganador"] // 10 % 10
        df["unidades"] = df["Numero billete ganador"] % 10

        df["serie_hundreds"] = df["Numero serie ganadora"] // 100 % 10
        df["serie_tens"] = df["Numero serie ganadora"] // 10 % 10
        df["serie_units"] = df["Numero serie ganadora"] % 10

        for col in [
            "miles",
            "centenas",
            "decenas",
            "unidades",
            "serie_hundreds",
            "serie_tens",
            "serie_units",
        ]:
            df[f"prev_{col}"] = df[col].shift(1)

        self.df = df.dropna().reset_index(drop=True).copy()

        if self.df.empty:
            raise RuntimeError("No hay suficientes datos históricos después del filtrado")

        last_row = self.df.iloc[-1]
        next_date = last_row["Fecha del Sorteo"] + pd.Timedelta(days=7)

        self.last_features = pd.DataFrame([
            {
                "Año": int(next_date.year),
                "Mes": int(next_date.month),
                "DiaSemana": int(next_date.dayofweek),
                "Numero del Sorteo": int(last_row["Numero del Sorteo"]) + 1,
                "prev_miles": int(last_row["miles"]),
                "prev_centenas": int(last_row["centenas"]),
                "prev_decenas": int(last_row["decenas"]),
                "prev_unidades": int(last_row["unidades"]),
                "prev_serie_hundreds": int(last_row["serie_hundreds"]),
                "prev_serie_tens": int(last_row["serie_tens"]),
                "prev_serie_units": int(last_row["serie_units"]),
            }
        ])

    def train(self) -> None:
        if self.df is None:
            raise RuntimeError("Debe llamar a load_data() antes de train()")

        features = [
            "Año",
            "Mes",
            "DiaSemana",
            "Numero del Sorteo",
            "prev_miles",
            "prev_centenas",
            "prev_decenas",
            "prev_unidades",
            "prev_serie_hundreds",
            "prev_serie_tens",
            "prev_serie_units",
        ]

        self.models = {}
        targets = [
            "miles",
            "centenas",
            "decenas",
            "unidades",
            "serie_hundreds",
            "serie_tens",
            "serie_units",
        ]

        X = self.df[features].astype(int)

        for target in targets:
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X, self.df[target].astype(int))
            self.models[target] = model

    def predict(self, seed: int | None = None) -> list[int]:
        if self.models is None or self.last_features is None:
            raise RuntimeError("Debe llamar a train() antes de predict()")

        rng = np.random.default_rng(seed)
        prediction: list[int] = []

        for target, model in self.models.items():
            probabilities = model.predict_proba(self.last_features)[0]
            classes = model.classes_
            prediction.append(int(rng.choice(classes, p=probabilities)))

        serie = prediction[4] * 100 + prediction[5] * 10 + prediction[6]
        return prediction[:4] + [serie]
