"""
Modelo de predicción para la Lotería de Risaralda.

Implementa ``BaseModel`` con modelos separados para cada dígito del número
y la serie, utilizando características temporales y lags.
"""

import os
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import joblib

from app.config import BASE_DATA_DIR
from app.ml.base_model import BaseModel

_DEFAULT_DATA_PATH = os.path.join(
    BASE_DATA_DIR, "loteria_del_risaralda", "loteria_del_risaralda_historico.csv"
)

# Configuración del modelo
_RANDOM_SEED = 42
_TEST_SIZE = 0.15


class RisaraldaModel(BaseModel):
    """
    Modelo para la Lotería de Risaralda.

    Entrena modelos separados para cada dígito (4 dígitos) y la serie.
    """

    def __init__(self, data_path: str | None = None) -> None:
        self.data_path: str = data_path or os.path.normpath(_DEFAULT_DATA_PATH)
        self.df: pd.DataFrame | None = None
        self.models: dict[str, RandomForestRegressor] | None = None
        self.scaler: StandardScaler | None = None

    def load_data(self) -> None:
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Archivo de datos no encontrado: {self.data_path}")

        df = pd.read_csv(self.data_path, sep=',', encoding='latin1')

        # Filtrar solo premio mayor
        df = df[df['Tipo de Premio'] == 'Mayor']

        # Procesar fechas
        df['FECHA'] = pd.to_datetime(df['Fecha del Sorteo'], format='mixed', dayfirst=True)
        df['Año'] = df['FECHA'].dt.year
        df['Mes'] = df['FECHA'].dt.month

        # Extraer números
        df['NUMERO'] = df['Numero billete ganador'].astype(str).str.zfill(4)
        df['d0'] = df['NUMERO'].str[0].astype(int)
        df['d1'] = df['NUMERO'].str[1].astype(int)
        df['d2'] = df['NUMERO'].str[2].astype(int)
        df['d3'] = df['NUMERO'].str[3].astype(int)
        df['SERIE'] = df['Numero serie ganadora'].astype(int)

        # Crear lags
        df = df.sort_values('FECHA')
        for col in ['d0', 'd1', 'd2', 'd3', 'SERIE']:
            df[f'{col}_lag1'] = df[col].shift(1).fillna(0)

        self.df = df

    def train(self) -> None:
        if self.df is None:
            raise RuntimeError("Debe llamar a load_data() antes de train()")

        # Características
        features = ['Año', 'Mes', 'd0_lag1', 'd1_lag1', 'd2_lag1', 'd3_lag1', 'SERIE_lag1']
        X = self.df[features].values
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.models = {}
        for target in ['d0', 'd1', 'd2', 'd3', 'SERIE']:
            y = self.df[target].values
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=_TEST_SIZE, random_state=_RANDOM_SEED
            )
            model = RandomForestRegressor(random_state=_RANDOM_SEED)
            model.fit(X_train, y_train)
            self.models[target] = model
            r2 = r2_score(y_test, model.predict(X_test))
            print(f"✔ Modelo {target} entrenado. R² Score: {r2:.4f}")

    def predict(self) -> list[int]:
        if self.models is None or self.scaler is None or self.df is None:
            raise RuntimeError("Debe llamar a train() antes de predict()")

        # Usar el último registro para predecir
        last_row = self.df.iloc[-1]
        current_X = np.array([[
            last_row['Año'], last_row['Mes'],
            last_row['d0'], last_row['d1'], last_row['d2'], last_row['d3'], last_row['SERIE']
        ]])
        current_X_scaled = self.scaler.transform(current_X)

        prediction = []
        for i in range(4):
            digit = int(self.models[f'd{i}'].predict(current_X_scaled)[0])
            prediction.append(digit)
        serie = int(self.models['SERIE'].predict(current_X_scaled)[0])
        prediction.append(serie)

        return prediction