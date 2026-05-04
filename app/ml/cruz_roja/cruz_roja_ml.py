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
# Silenciar logs de TensorFlow y optimizaciones oneDNN para una terminal limpia
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
try:
    import tensorflow as tf
    # Silenciar advertencias internas de TensorFlow sobre dispositivos/GPU
    tf.get_logger().setLevel('ERROR')
except ImportError:
    tf = None

from app.config import BASE_DATA_DIR, PRIZE_TYPE_FILTER
from app.ml.base_model import BaseModel

_DEFAULT_DATA_PATH = os.path.join(
    BASE_DATA_DIR, "loteria_cruz_roja", "cruz_roja_historico.csv"
)

_TARGET_COLUMNS = ["miles", "centenas", "decenas", "unidades", "serie"]


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
        rnn_models (dict | None): Diccionario de modelos LSTM entrenados.
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
        self.data_path: str = data_path or os.path.normpath(_DEFAULT_DATA_PATH)
        self.df: pd.DataFrame | None = None
        self.models: dict | None = None
        self.rnn_models: dict | None = None
        self.last_features: pd.DataFrame | None = None


    def load_data(self, include_secos: bool = False) -> None:
        """
        Carga el CSV histórico, filtra por premio mayor y prepara características.

        Lee ``self.data_path``, filtra las filas de premio mayor, extrae
        componentes temporales y genera lags (valores del sorteo anterior)
        como predictores.

        Args:
            include_secos: Si es True, incluye todos los tipos de premios para 
                aumentar el volumen de entrenamiento (Recomendado para >10% acc).
        """
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Archivo de datos no encontrado: {self.data_path}")

        df = pd.read_csv(self.data_path)
        
        # Filtro y limpieza: Si no se incluyen secos, se filtra por Mayor
        if not include_secos:
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

        # Características de paridad (Esencial para reducir el ruido en unidades)
        df["prev_unidades_par"] = (df["prev_unidades"] % 2 == 0).astype(int)
        # Nueva: Racha de paridad (últimos 3 sorteos)
        df["prev_unidades_par_streak"] = df["prev_unidades_par"].rolling(window=3, min_periods=1).sum().shift(1)

        # Nueva: Suma total del sorteo anterior
        df["prev_sum_digits"] = (df["prev_miles"] + df["prev_centenas"] + df["prev_decenas"] + df["prev_unidades"]).fillna(0)

        # NUEVA CARACTERÍSTICA: Dormancia (Recency)
        # Mide cuántos sorteos han pasado desde la última vez que salió el dígito actual
        df["recency_unidades"] = self._calculate_recency(df["unidades"])
        df["prev_recency_unidades"] = df["recency_unidades"].shift(1)
        
        # Probabilidad Global como Feature (FWMS)
        unidades_probs = df["unidades"].value_counts(normalize=True).to_dict()
        df["global_prob_unidades"] = df["unidades"].map(unidades_probs).shift(1)

        # NUEVAS CARACTERÍSTICAS: Frecuencia acumulada y tendencias
        # Ayuda a identificar números "fríos" o "calientes" en las unidades
        for col in ["unidades", "decenas"]:
            # Cuántas veces salió este dígito en los últimos 10 sorteos
            df[f"freq_10_{col}"] = df[col].rolling(window=10).apply(
                lambda x: (x == x.iloc[-1]).sum()
            ).shift(1)

            # Frecuencia de corto plazo (últimos 5) para detectar rachas rápidas
            df[f"freq_5_{col}"] = df[col].rolling(window=5).apply(
                lambda x: (x == x.iloc[-1]).sum()
            ).shift(1)
            
            # Diferencia (distancia) con el número anterior
            df[f"diff_{col}"] = df[col].diff().shift(1)

        # Características temporales del sorteo actual
        df["mes"] = df["Fecha del Sorteo"].dt.month
        df["dia_semana"] = df["Fecha del Sorteo"].dt.dayofweek
        
        # Codificación cíclica (Mes y Día) para capturar estacionalidad real
        df["sin_mes"] = np.sin(2 * np.pi * df["mes"] / 12)
        df["cos_mes"] = np.cos(2 * np.pi * df["mes"] / 12) # Corregido de sin a cos
        df["sin_dia"] = np.sin(2 * np.pi * df["dia_semana"] / 7)
        df["cos_dia"] = np.cos(2 * np.pi * df["dia_semana"] / 7)

        # Definir lista maestra de características para asegurar consistencia
        self._feature_cols = [
            col for col in df.columns 
            if col.startswith(('prev_', 'freq_', 'diff_', 'sin_', 'cos_', 'global_', 'sin_dia', 'cos_dia'))
        ]

        # Eliminar primera fila (no tiene lag)
        self.df = df.dropna().copy()
        
        # Guardar las características para predecir el SIGUIENTE sorteo
        # Usamos la fecha del último sorteo + 7 días para los componentes temporales
        last_row = df.iloc[-1]
        next_date = last_row["Fecha del Sorteo"] + pd.Timedelta(days=7)
        
        # Construcción dinámica para evitar drift de características
        next_features_dict = {
            "prev_miles":    last_row["miles"],
            "prev_centenas": last_row["centenas"],
            "prev_decenas":  last_row["decenas"],
            "prev_unidades": last_row["unidades"],
            "prev_serie":    last_row["serie"],
            "prev_unidades_par": int(last_row["unidades"] % 2 == 0),
            # La racha para el siguiente sorteo es la suma de paridad de los últimos 3 sorteos conocidos
            "prev_unidades_par_streak": df["prev_unidades_par"].tail(2).sum() + int(last_row["unidades"] % 2 == 0),
            "prev_sum_digits": last_row["miles"] + last_row["centenas"] + last_row["decenas"] + last_row["unidades"],
            "prev_recency_unidades": last_row["recency_unidades"],
            "global_prob_unidades": unidades_probs.get(last_row["unidades"], 0.1),
            "freq_10_unidades": (df["unidades"].tail(10) == last_row["unidades"]).sum(),
            "freq_5_unidades":  (df["unidades"].tail(5) == last_row["unidades"]).sum(),
            "freq_10_decenas":  (df["decenas"].tail(10) == last_row["decenas"]).sum(),
            "freq_5_decenas":   (df["decenas"].tail(5) == last_row["decenas"]).sum(),
            # Diferencia entre el sorteo más reciente (T) y el anterior (T-1)
            "diff_unidades":    last_row["unidades"] - df["unidades"].iloc[-2] if len(df) > 1 else 0,
            "diff_decenas":     last_row["decenas"] - df["decenas"].iloc[-2] if len(df) > 1 else 0,
            "sin_mes":          np.sin(2 * np.pi * next_date.month / 12),
            "cos_mes":          np.cos(2 * np.pi * next_date.month / 12),
            "sin_dia":          np.sin(2 * np.pi * next_date.dayofweek / 7),
            "cos_dia":          np.cos(2 * np.pi * next_date.dayofweek / 7)
        }
        self.last_features = pd.DataFrame([next_features_dict])[self._feature_cols]

    def _calculate_recency(self, series: pd.Series) -> pd.Series:
        """Calcula cuántos sorteos han pasado desde la última vez que salió cada dígito."""
        recency = np.zeros(len(series))
        last_seen = {}
        for i, val in enumerate(series):
            if val in last_seen:
                recency[i] = i - last_seen[val]
            else:
                recency[i] = 20 # Valor por defecto para la primera aparición
            last_seen[val] = i
        return pd.Series(recency, index=series.index)

    def train(self) -> None:
        """
        Entrena modelos de Random Forest para cada posición del número.

        Utiliza los lags del sorteo anterior y datos temporales para entrenar
        5 clasificadores (4 para el número y 1 para la serie).
        """
        if self.df is None:
            raise RuntimeError("Debe llamar a load_data() antes de train()")

        # Usar la lista de características definida en load_data
        X = self.df[self._feature_cols]

        self.models = {}

        for target in _TARGET_COLUMNS:
            # Unidades tiene mucha entropía: necesita menos profundidad y más hojas para generalizar.
            # Miles y centenas tienen patrones más claros: se benefician de más profundidad.
            if target == "unidades":
                n_trees, max_d, min_leaf = 1000, 8, 12
            elif target == "miles":
                n_trees, max_d, min_leaf = 700, 16, 4
            elif target == "serie":
                # La serie tiene 1000 clases, necesita más capacidad para no generalizar de más
                n_trees, max_d, min_leaf = 400, 12, 4
            else:
                # Centenas y Decenas
                n_trees, max_d, min_leaf = 400, 12, 5
            
            model = RandomForestClassifier(
                n_estimators=n_trees,
                max_depth=max_d,
                min_samples_leaf=min_leaf,
                max_features='sqrt',
                random_state=42
            )
            model.fit(X, self.df[target])
            self.models[target] = model

    def train_rnn(self, epochs: int = 50, window_size: int = 5) -> None:
        """
        Entrena una Red Neuronal Recurrente (LSTM) para cada posición.
        
        Args:
            epochs: Cantidad de iteraciones de entrenamiento.
            window_size: Cantidad de sorteos previos para ver como secuencia.
        """
        if tf is None:
            raise ImportError("TensorFlow no está instalado. Ejecute 'pip install tensorflow'.")
        if self.df is None:
            raise RuntimeError("Debe llamar a load_data() antes de train_rnn()")

        X_raw = self.df[self._feature_cols].values
        self.rnn_models = {}
        self.window_size = window_size
        
        
        for target in _TARGET_COLUMNS:
            y_raw = self.df[target].values
            
            # Preparar secuencias (Windowing)
            X_seq, y_seq = [], []
            for i in range(len(X_raw) - window_size):
                X_seq.append(X_raw[i : i + window_size])
                y_seq.append(y_raw[i + window_size])
            
            # Forzar dtypes para compatibilidad con TensorFlow/Keras 3 en Windows
            X_seq = np.array(X_seq).astype(np.float32)
            y_seq = np.array(y_seq).astype(np.int32)

            # Definir arquitectura RNN (LSTM)
            num_classes = 10 if target != "serie" else 1000
            model = tf.keras.Sequential([
                tf.keras.layers.Input(shape=(window_size, len(self._feature_cols))),
                tf.keras.layers.LSTM(50, activation='tanh', return_sequences=False),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(num_classes, activation='softmax')
            ])
            
            model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
            
            # Entrenamiento
            model.fit(X_seq, y_seq, epochs=epochs, verbose=0, batch_size=32)
            self.rnn_models[target] = model

    def _get_rnn_prediction(self, rng: np.random.Generator) -> list[int]:
        """Inferencia interna usando las secuencias y modelos RNN."""
        prediction = []
        # Necesitamos los últimos N registros del histórico para formar la secuencia
        last_sequence = self.df[self._feature_cols].tail(self.window_size).values
        last_sequence = last_sequence.reshape(1, self.window_size, len(self._feature_cols))

        for target in _TARGET_COLUMNS:
            model = self.rnn_models[target]
            probs = model.predict(last_sequence, verbose=0)[0]
            classes = np.arange(len(probs))
            
            val = rng.choice(classes, p=probs)
            prediction.append(int(val))
        
        return prediction

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
        if self.models is None and self.rnn_models is None:
            raise RuntimeError("Debe llamar a train() o train_rnn() antes de predict()")

        rng = np.random.default_rng(seed)

        # Si se entrenó con RNN, dar prioridad a esa predicción
        if self.rnn_models is not None:
            return self._get_rnn_prediction(rng)

        prediction = []
        for target in _TARGET_COLUMNS:
            model = self.models[target]
            # Obtener probabilidades para cada clase posible
            probs = model.predict_proba(self.last_features)[0]
            classes = model.classes_
            
            # Muestrear un valor basado en las probabilidades predichas
            val = rng.choice(classes, p=probs)
            prediction.append(int(val))

        return prediction

    def get_feature_importance(self) -> dict[str, pd.Series]:
        """
        Extrae la importancia de las características para cada modelo entrenado.
        
        Útil para verificar qué variables (lags, mes, frecuencia) están
        influyendo más en la predicción.
        """
        if self.models is None:
            raise RuntimeError("El modelo debe estar entrenado.")
            
        importance_dict = {}
        for target, model in self.models.items():
            importance_dict[target] = pd.Series(
                model.feature_importances_,
                index=self._feature_cols
            ).sort_values(ascending=False)
            
        return importance_dict

if __name__ == "__main__":
    # Bloque de prueba para ejecución directa
    print("--- Iniciando Modelo Lotería de la Cruz Roja ---")
    model = CruzRojaModel()
    
    try:
        print("Cargando datos históricos...")
        model.load_data(include_secos=True)
        print(f"Dataset cargado con {len(model.df)} registros.")

        print("Entrenando modelos (Random Forest)...")
        model.train()
        
        print("\nGenerando predicción para el próximo sorteo:")
        # Para obtener predicciones diferentes basadas en la probabilidad,
        # puedes quitar el 'seed=42' o usar None.
        prediccion = model.predict(seed=None)
        
        numero = "".join(map(str, prediccion[:4]))
        serie = str(prediccion[4]).zfill(3)
        
        print(f"Número Sugerido: {numero}")
        print(f"Serie Sugerida:  {serie}")
        
        print("\nImportancia de características (Top 3 Unidades):")
        print(model.get_feature_importance()["unidades"].head(3))

    except Exception as e:
        print(f"Error durante la ejecución: {e}")
