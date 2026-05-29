"""
Modelo de predicción para la Lotería de Bogotá.

Implementa ``BaseModel`` con una estrategia de red neuronal MLP (MLPRegressor)
que utiliza características temporales (Año, Mes, Número de Sorteo) para
predecir el número ganador y la serie.

Fuente de datos:
    CSV en ``bd/historical/loteria_bogota/bogota_historico.csv``.
    Columnas requeridas:

    - ``FECHA``             (str)  — fecha del sorteo
    - ``NUMERO``            (int)  — número ganador (4 dígitos)
    - ``SERIE``             (int)  — serie ganadora (hasta 3 dígitos)
    - ``SORTEO``            (int)  — número secuencial del sorteo
"""

import os
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sklearn.exceptions import ConvergenceWarning, UndefinedMetricWarning
import joblib

from app.config import BASE_DATA_DIR
from app.ml.base_model import BaseModel

_DEFAULT_DATA_PATH = os.path.join(
    BASE_DATA_DIR, "loteria_bogota", "bogota_historico.csv"
)

# Configuración del modelo
_RANDOM_SEED = 42
_TEST_SIZE = 0.15
_HIDDEN_LAYERS = (200, 100, 50)
_MAX_ITERATIONS = 2500


class BogotaModel(BaseModel):
    """
    Modelo MLP para la Lotería de Bogotá.

    Entrena una red neuronal que aprende la relación entre características
    temporales (año, mes, sorteo) y el resultado histórico (número y serie).

    Attributes:
        data_path (str): Ruta absoluta al CSV de datos históricos.
        df (pd.DataFrame | None): DataFrame cargado; ``None`` hasta que
            se llame ``load_data()``.
        model (MLPRegressor | None): Modelo entrenado; ``None`` hasta que
            se llame ``train()``.
        scaler (StandardScaler | None): Escalador de características;
            ``None`` hasta que se llame ``train()``.
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
        self.model: MLPRegressor | None = None
        self.scaler: StandardScaler | None = None

    def load_data(self) -> None:
        """
        Carga el CSV histórico y prepara las características.

        Lee ``self.data_path``, procesa fechas y extrae números limpios.
        Almacena el resultado en ``self.df``.

        Raises:
            FileNotFoundError: si ``self.data_path`` no existe en disco.
        """
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Archivo de datos no encontrado: {self.data_path}")

        df = pd.read_csv(self.data_path, sep=';', encoding='latin1')

        # Procesamiento flexible de fechas
        df['FECHA'] = pd.to_datetime(df['FECHA'], format='mixed', dayfirst=False)
        df['Año'] = df['FECHA'].dt.year
        df['Mes'] = df['FECHA'].dt.month

        # Limpieza robusta: Extraer solo números
        for col in ['NUMERO', 'SERIE', 'SORTEO']:
            df[col] = (
                df[col].astype(str)
                .str.extract(r'(\d+)', expand=False)
                .fillna('0')
                .astype(int)
            )

        self.df = df

    def train(self) -> None:
        """
        Entrena la red neuronal MLP con los datos cargados.

        Utiliza características temporales (Año, Mes, SORTEO) para predecir
        el NUMERO y SERIE. El modelo se escala antes del entrenamiento y
        el escalador se conserva para predicciones futuras.

        Raises:
            RuntimeError: si ``self.df`` es ``None`` (``load_data()`` no
                fue llamado previamente).
        """
        if self.df is None:
            raise RuntimeError("Debe llamar a load_data() antes de train()")

        # Preparar características y objetivo
        X = self.df[['Año', 'Mes', 'SORTEO']].values
        y = self.df[['NUMERO', 'SERIE']].values

        # Escalar características
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Dividir en entrenamiento y prueba
        # Para evitar advertencias con conjuntos de datos muy pequeños (ej. tests unitarios)
        # nos aseguramos de que el test_size devuelva al menos 2 muestras si es posible,
        # o usamos todo el conjunto si hay muy pocas muestras en total.
        n_samples = len(self.df)
        if n_samples > 5:
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=_TEST_SIZE, random_state=_RANDOM_SEED
            )
        else:
            X_train, y_train = X_scaled, y
            X_test, y_test = X_scaled, y

        # Entrenar modelo
        self.model = MLPRegressor(
            hidden_layer_sizes=_HIDDEN_LAYERS,
            max_iter=_MAX_ITERATIONS,
            random_state=_RANDOM_SEED,
        )
        
        # Ocultar advertencia de no convergencia, ya que es normal en pruebas rápidas
        # o datasets reducidos.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            self.model.fit(X_train, y_train)

        # Evaluar en prueba de manera segura
        # Ocultamos la advertencia UndefinedMetricWarning y evitamos calcular R² si el conjunto de prueba es inválido
        if len(y_test) >= 2 and np.var(y_test, axis=0).min() > 0:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UndefinedMetricWarning)
                r2 = r2_score(y_test, self.model.predict(X_test))
        else:
            r2 = 0.0
            
        print(f"✔ Modelo Bogotá entrenado. R² Score: {r2:.4f}")

    def predict(self) -> list[int]:
        """
        Genera predicción para el próximo sorteo.

        Utiliza el último sorteo del histórico para proyectar el siguiente,
        manteniendo el año/mes más reciente. Devuelve cuatro dígitos
        principales y la serie como entero, conforme al contrato de API.

        Returns:
            Lista con cinco enteros: [d1, d2, d3, d4, serie_predicha]

        Raises:
            RuntimeError: si el modelo no ha sido entrenado (``train()``
                no fue llamado previamente).
        """
        if self.model is None or self.scaler is None:
            raise RuntimeError("Debe llamar a train() antes de predict()")

        if self.df is None:
            raise RuntimeError("Debe llamar a load_data() antes de predict()")

        # Próximo sorteo
        max_sorteo = int(self.df['SORTEO'].max())
        ultimo_año = int(self.df['Año'].iloc[-1])
        ultimo_mes = int(self.df['Mes'].iloc[-1])

        proximo_sorteo = np.array([[ultimo_año, ultimo_mes, max_sorteo + 1]])
        proximo_scaled = self.scaler.transform(proximo_sorteo)

        # Predicción y redondeo
        prediccion = self.model.predict(proximo_scaled)[0]
        numero_predicho = int(abs(prediccion[0])) % 10000
        serie_predicha = int(abs(prediccion[1])) % 1000

        numero_str = str(numero_predicho).zfill(4)
        main_digits = [int(d) for d in numero_str]

        return main_digits + [serie_predicha]
