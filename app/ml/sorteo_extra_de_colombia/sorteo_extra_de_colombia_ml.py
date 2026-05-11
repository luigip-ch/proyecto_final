"""
Modelo de predicción para el Sorteo Extra de Colombia.

Implementa ``BaseModel`` utilizando Random Forest con validación cruzada
(Cross-Validation) y ajuste de hiperparámetros (Train/Test Tuning) a través
de GridSearchCV.
"""

import os
import warnings
from datetime import datetime

# Suprimir la advertencia global de dependencias de requests para limpiar la consola
warnings.filterwarnings("ignore", message=".*urllib3.*chardet.*charset_normalizer.*")

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, KFold

from app.config import BASE_DATA_DIR, PRIZE_TYPE_FILTER
from app.ml.base_model import BaseModel

_DEFAULT_DATA_PATH = os.path.join(
    BASE_DATA_DIR, "sorteo_extra_de_colombia", "sorteo_extra_de_colombia_historico.csv"
)

_TARGET_COLUMNS = ["miles", "centenas", "decenas", "unidades", "serie"]


class SorteoExtraDeColombiaModel(BaseModel):
    """
    Modelo Random Forest con validación cruzada y tuning de hiperparámetros
    para el Sorteo Extra de Colombia.
    """

    def __init__(self, data_path: str | None = None) -> None:
        self.data_path: str = data_path or os.path.normpath(_DEFAULT_DATA_PATH)
        self.df: pd.DataFrame | None = None
        self.models: dict | None = None
        self.last_features: pd.DataFrame | None = None

    def load_data(self) -> None:
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Archivo de datos no encontrado: {self.data_path}")

        df = pd.read_csv(self.data_path)
        
        # Filtro por premio mayor
        df = df[df["Tipo de Premio"] == PRIZE_TYPE_FILTER].copy()
        
        df["Fecha del Sorteo"] = pd.to_datetime(df["Fecha del Sorteo"], dayfirst=True)
        df = df.sort_values("Fecha del Sorteo")

        # Descomposición de dígitos
        df["miles"]    = (df["Numero billete ganador"] // 1000 % 10)
        df["centenas"] = (df["Numero billete ganador"] // 100 % 10)
        df["decenas"]  = (df["Numero billete ganador"] // 10 % 10)
        df["unidades"] = (df["Numero billete ganador"] % 10)
        df["serie"]    = df["Numero serie ganadora"].astype(int)

        # Lags del sorteo anterior
        for col in ["miles", "centenas", "decenas", "unidades", "serie"]:
            df[f"prev_{col}"] = df[col].shift(1)

        df["mes"] = df["Fecha del Sorteo"].dt.month
        df["dia_semana"] = df["Fecha del Sorteo"].dt.dayofweek

        self._feature_cols = [
            "prev_miles", "prev_centenas", "prev_decenas", 
            "prev_unidades", "prev_serie", "mes", "dia_semana"
        ]

        self.df = df.dropna().copy()
        
        last_row = df.iloc[-1]
        next_date = last_row["Fecha del Sorteo"] + pd.Timedelta(days=7)
        
        next_features_dict = {
            "prev_miles":    last_row["miles"],
            "prev_centenas": last_row["centenas"],
            "prev_decenas":  last_row["decenas"],
            "prev_unidades": last_row["unidades"],
            "prev_serie":    last_row["serie"],
            "mes":           next_date.month,
            "dia_semana":    next_date.dayofweek
        }
        self.last_features = pd.DataFrame([next_features_dict])[self._feature_cols]

    def train(self) -> None:
        """
        Entrena modelos de Random Forest para cada posición del número
        utilizando validación cruzada y ajuste de hiperparámetros.
        """
        if self.df is None:
            raise RuntimeError("Debe llamar a load_data() antes de train()")

        X = self.df[self._feature_cols]
        self.models = {}

        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [5, 10, 15],
            'min_samples_split': [2, 5],
        }

        # Usar KFold estandar en lugar del StratifiedKFold por defecto para evitar 
        # errores cuando una clase (número) tiene muy pocas apariciones históricas.
        cv_strategy = KFold(n_splits=3, shuffle=True, random_state=42)

        for target in _TARGET_COLUMNS:
            rf = RandomForestClassifier(random_state=42, class_weight='balanced')
            # GridSearchCV para validación cruzada y Train/Test Tuning
            grid_search = GridSearchCV(
                estimator=rf, 
                param_grid=param_grid, 
                cv=cv_strategy, 
                scoring='accuracy',
                n_jobs=-1
            )
            
            # Silenciamos advertencias sobre pocas muestras de clases minoritarias
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                grid_search.fit(X, self.df[target])
                
            self.models[target] = grid_search.best_estimator_

    def predict(self, seed: int | None = None) -> list[int]:
        if self.models is None or self.last_features is None:
            raise RuntimeError("Debe llamar a train() antes de predict()")

        rng = np.random.default_rng(seed)
        prediction = []

        for target in _TARGET_COLUMNS:
            model = self.models[target]
            probs = model.predict_proba(self.last_features)[0]
            classes = model.classes_
            
            val = rng.choice(classes, p=probs)
            prediction.append(int(val))

        return prediction
