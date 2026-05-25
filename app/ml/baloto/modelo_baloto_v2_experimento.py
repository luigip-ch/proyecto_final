"""
Modelo de predicción V2 para Baloto (Experimento).

Implementa ``BaseModel`` utilizando un Random Forest Classifier y
Feature Engineering (Ingeniería de Características) para intentar
encontrar patrones complejos más allá de la frecuencia pura.
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from app.config import BASE_DATA_DIR
from app.ml.base_model import BaseModel

_DEFAULT_DATA_PATH = os.path.join(
    BASE_DATA_DIR, "baloto", "baloto_historico.csv"
)

class BalotoModelV2(BaseModel):
    """
    Modelo experimental usando Random Forest para calcular las probabilidades
    de extracción de las balotas principales basándose en Ingeniería de Características.
    """

    def __init__(self, data_path: str | None = None) -> None:
        self.data_path: str = data_path or os.path.normpath(_DEFAULT_DATA_PATH)
        self.df: pd.DataFrame | None = None
        self.rf_model: RandomForestClassifier | None = None
        self.frecuencias_superbalota: dict | None = None
        self.current_features: list | None = None

    def load_data(self) -> None:
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Archivo de datos no encontrado: {self.data_path}")
        self.df = pd.read_csv(self.data_path)

    def train(self) -> None:
        if self.df is None:
            raise RuntimeError("Debe llamar a load_data() antes de train()")

        # 1. Preparar datos para Superbalota (mantenemos el modelo frecuentista simple para ella)
        superbalotas = self.df["superbalota"].astype(int)
        counts = superbalotas.value_counts().sort_index()
        self.frecuencias_superbalota = {int(d): float(c) / counts.sum() for d, c in counts.items()}

        # 2. Ingeniería de Características (Feature Engineering)
        X_train = []
        y_train = []
        
        # Pre-calculamos las listas de sorteos históricos para facilitar las búsquedas
        draws = []
        for _, row in self.df.iterrows():
            draws.append(set([row['n1'], row['n2'], row['n3'], row['n4'], row['n5']]))
            
        total_draws = len(draws)
        # Entrenamos con los últimos 150 sorteos para tener agilidad y enfocarnos en patrones recientes
        train_start = max(50, total_draws - 150) 
        
        for t in range(train_start, total_draws):
            target_draw = draws[t]
            history = draws[:t]
            
            for num in range(1, 44):  # Asumiendo balotas del 1 al 43
                # Feature 1: ¿Es par?
                is_even = 1 if num % 2 == 0 else 0
                
                # Feature 2: Momentum (Frecuencia en los últimos 10 sorteos)
                freq_last_10 = sum(1 for d in history[-10:] if num in d)
                
                # Feature 3: Rezago (Sorteos transcurridos desde su última aparición)
                draws_since_last = 0
                for d in reversed(history):
                    if num in d:
                        break
                    draws_since_last += 1
                
                # Feature 4: Frecuencia histórica global hasta este punto en el tiempo
                freq_global = sum(1 for d in history if num in d) / len(history)

                X_train.append([is_even, freq_last_10, draws_since_last, freq_global])
                # Target: 1 si salió en el sorteo 't', 0 si no salió
                y_train.append(1 if num in target_draw else 0)

        # 3. Entrenar el Random Forest
        # Ajustamos hiperparámetros:
        # - max_depth=5: Profundidad controlada para evitar sobreajuste (overfitting) en un entorno de alto ruido (azar).
        # - class_weight="balanced": Le da más importancia a la clase 1 (cuando el número sale), ya que solo salen 5 de 43.
        self.rf_model = RandomForestClassifier(
            n_estimators=100, 
            max_depth=5, 
            random_state=42,
            class_weight="balanced"
        )
        self.rf_model.fit(X_train, y_train)

        # 4. Generar Features del "Estado Actual" para usar en predict()
        current_history = draws
        current_X = []
        for num in range(1, 44):
            is_even = 1 if num % 2 == 0 else 0
            freq_last_10 = sum(1 for d in current_history[-10:] if num in d)
            
            draws_since_last = 0
            for d in reversed(current_history):
                if num in d:
                    break
                draws_since_last += 1
                
            freq_global = sum(1 for d in current_history if num in d) / len(current_history)
            
            current_X.append([is_even, freq_last_10, draws_since_last, freq_global])
            
        self.current_features = current_X

    def predict(self, seed: int | None = None) -> list[int]:
        if self.rf_model is None or self.current_features is None:
            raise RuntimeError("Debe llamar a train() antes de predict()")

        # El modelo RF predice la "probabilidad de que el número sea seleccionado"
        probs = self.rf_model.predict_proba(self.current_features)[:, 1]
        
        # Suavizamos y normalizamos las probabilidades para que sumen 1
        probs = np.array(probs)
        probs = probs / probs.sum()
        
        rng = np.random.default_rng(seed)
        
        # Muestreamos 5 balotas principales basados en las nuevas probabilidades calculadas por la IA
        numeros = list(range(1, 44))
        prediccion_principal = rng.choice(
            numeros, size=5, replace=False, p=probs
        ).tolist()
        
        prediccion_principal.sort()
        prediccion_principal = [int(x) for x in prediccion_principal]

        # Para la superbalota usamos el muestreo frecuentista precalculado
        digits_super = list(self.frecuencias_superbalota.keys())
        probs_super = list(self.frecuencias_superbalota.values())
        superbalota = int(rng.choice(digits_super, p=probs_super))

        return prediccion_principal + [superbalota]
