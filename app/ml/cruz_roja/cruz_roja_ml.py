"""
Modelo de predicción para la Lotería de la Cruz Roja.

Implementa ``BaseModel`` con la estrategia FWMS
(Frequency-Weighted Multinomial Sampling): cada posición del número
ganador (miles, centenas, decenas, unidades) se muestrea de forma
independiente usando una distribución de probabilidad empírica
construida a partir del histórico de resultados.

Fuente de datos:
    CSV en ``bd/historical/loteria_cruz_roja/cruz_roja_historico.csv``.
    Columnas requeridas:

    - ``Tipo de Premio``           (str)  — filtrado por ``PRIZE_TYPE_FILTER``
    - ``Numero billete ganador``   (int)  — número de 4 dígitos (ej. 2773)
    - ``Numero serie ganadora``    (int)  — serie de hasta 3 dígitos (ej. 184)
"""

import os
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from app.config import BASE_DATA_DIR, PRIZE_TYPE_FILTER
from app.ml.base_model import BaseModel

_DEFAULT_DATA_PATH = os.path.join(
    BASE_DATA_DIR, "loteria_cruz_roja", "cruz_roja_historico.csv"
)


class CruzRojaModel(BaseModel):
    """
    Modelo FWMS (Frequency-Weighted Multinomial Sampling) para la Lotería
    de la Cruz Roja.

    Cada número ganador de 4 dígitos se descompone en sus posiciones
    (miles, centenas, decenas, unidades) y se construye una distribución
    de probabilidad empírica por posición. La predicción muestrea
    independientemente cada posición, respetando las frecuencias históricas.
    La serie se elige uniformemente del conjunto histórico de series
    ganadoras.

    Attributes:
        data_path (str): Ruta absoluta al CSV de datos históricos.
        df (pd.DataFrame | None): DataFrame filtrado y procesado;
            ``None`` hasta que se llame ``load_data()``.
        models (dict | None): Diccionario de modelos RandomForest por
            posición (miles, centenas, decenas, unidades, serie);
            ``None`` hasta que se llame ``train()``.
        last_features (pd.DataFrame | None): Características del último
            sorteo conocido para la predicción futura.
    """

    def __init__(self, data_path: str | None = None) -> None:
        """
        Inicializa el modelo con la ruta al CSV de datos históricos.

        Asegura que el contrato de la API para esta lotería esté correctamente
        definido en memoria para evitar errores de tipo en los endpoints.

        Args:
            data_path: Ruta absoluta al CSV. Si es ``None`` se usa la
                ruta por defecto configurada en ``app.config``.
        """
        # Ajuste al contrato de la API: asegura que la configuración no sea un string
        from app.config import DEFAULT_PREDICTION_FORMAT, LOTTERY_PREDICTION_FORMATS
        if not isinstance(LOTTERY_PREDICTION_FORMATS.get("cruz_roja"), dict):
            LOTTERY_PREDICTION_FORMATS["cruz_roja"] = DEFAULT_PREDICTION_FORMAT

        self.data_path: str = data_path or os.path.normpath(_DEFAULT_DATA_PATH)
        self.df: pd.DataFrame | None = None
        self.models: dict | None = None
        self.last_features: pd.DataFrame | None = None


    def load_data(self) -> None:
        """
        Carga el CSV histórico, filtra por premio mayor y prepara características.

        Lee ``self.data_path``, filtra las filas de premio mayor, extrae
        componentes temporales y genera lags (valores del sorteo anterior)
        como predictores.
        """
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Archivo de datos no encontrado: {self.data_path}")

        df = pd.read_csv(self.data_path)
        
        # Filtro y limpieza
        df = df[df["Tipo de Premio"] == PRIZE_TYPE_FILTER].copy()
        
        # Parseo de fechas y ordenamiento
        df["Fecha del Sorteo"] = pd.to_datetime(df["Fecha del Sorteo"], dayfirst=True)
        df = df.sort_values("Fecha del Sorteo")

        # Descomposición de dígitos
        df["miles"]    = (df["Numero billete ganador"] // 1000 % 10)
        df["centenas"] = (df["Numero billete ganador"] // 100 % 10)
        df["decenas"]  = (df["Numero billete ganador"] // 10 % 10)
        df["unidades"] = (df["Numero billete ganador"] % 10)
        df["serie"]    = df["Numero serie ganadora"].astype(int)

        # Ingeniería de Características (Features)
        # Lags del sorteo anterior
        for col in ["miles", "centenas", "decenas", "unidades", "serie"]:
            df[f"prev_{col}"] = df[col].shift(1)

        # Características temporales del sorteo actual
        df["mes"] = df["Fecha del Sorteo"].dt.month
        df["dia_semana"] = df["Fecha del Sorteo"].dt.dayofweek

        # Eliminar primera fila (no tiene lag)
        self.df = df.dropna().copy()
        
        # Guardar las características para predecir el SIGUIENTE sorteo
        # Usamos la fecha del último sorteo + 7 días para los componentes temporales
        last_row = df.iloc[-1]
        next_date = last_row["Fecha del Sorteo"] + pd.Timedelta(days=7)
        
        self.last_features = pd.DataFrame([{
            "prev_miles":    last_row["miles"],
            "prev_centenas": last_row["centenas"],
            "prev_decenas":  last_row["decenas"],
            "prev_unidades": last_row["unidades"],
            "prev_serie":    last_row["serie"],
            "mes":           next_date.month,
            "dia_semana":    next_date.dayofweek
        }])

    def train(self) -> None:
        """
        Entrena modelos de Random Forest para cada posición del número.

        Utiliza los lags del sorteo anterior y datos temporales para entrenar
        5 clasificadores (4 para el número y 1 para la serie).
        """
        if self.df is None:
            raise RuntimeError("Debe llamar a load_data() antes de train()")

        X = self.df[[
            "prev_miles", "prev_centenas", "prev_decenas", 
            "prev_unidades", "prev_serie", "mes", "dia_semana"
        ]]

        self.models = {}
        targets = ["miles", "centenas", "decenas", "unidades", "serie"]

        for target in targets:
            model = RandomForestClassifier(
                n_estimators=100, 
                max_depth=10, 
                random_state=42
            )
            model.fit(X, self.df[target])
            self.models[target] = model

    def predict(self, seed: int | None = None) -> list[int]:
        """
        Genera una predicción utilizando los modelos de Random Forest entrenados.

        A diferencia de una predicción de clase pura, este método muestrea
        de la distribución de probabilidades predicha para cada posición,
        permitiendo variabilidad estadística y respetando el 'seed'.

        Args:
            seed: Semilla para el generador aleatorio.

        Returns:
            Lista ``[miles, centenas, decenas, unidades, serie]``.
        """
        if self.models is None or self.last_features is None:
            raise RuntimeError("Debe llamar a train() antes de predict()")

        rng = np.random.default_rng(seed)
        prediction = []

        for target in ["miles", "centenas", "decenas", "unidades", "serie"]:
            model = self.models[target]
            # Obtener probabilidades para cada clase posible
            probs = model.predict_proba(self.last_features)[0]
            classes = model.classes_
            
            # Muestrear un valor basado en las probabilidades predichas
            val = rng.choice(classes, p=probs)
            prediction.append(int(val))

        return prediction

