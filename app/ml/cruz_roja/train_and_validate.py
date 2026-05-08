"""
Script para entrenar y validar el modelo de la Cruz Roja con el dataset completo.
Calcula la precisión (Accuracy) para cada posición del número.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score
from app.ml.cruz_roja.cruz_roja_ml import CruzRojaModel

def main():
    print("=== Validación del Modelo Cruz Roja ===")
    
    # 1. Cargar el modelo y los datos reales
    model = CruzRojaModel()
    try:
        # Activamos include_secos para aumentar masivamente el volumen de entrenamiento
        model.load_data(include_secos=True)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # 2. División temporal (80% entrenamiento, 20% prueba)
    # Usamos división secuencial para respetar la naturaleza temporal de la lotería
    df = model.df
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    print(f"Registros totales: {len(df)}")
    print(f"Entrenamiento:     {len(train_df)} sorteos")
    print(f"Prueba (Test):      {len(test_df)} sorteos\n")

    # 3. Entrenamiento y Evaluación de Random Forest
    print("--- Evaluación Random Forest ---")
    model.df = train_df
    model.train()
    features = model._feature_cols
    targets = ["miles", "centenas", "decenas", "unidades", "serie"]
    X_test = test_df[features]

    for target in targets:
        y_test = test_df[target]
        y_pred = model.models[target].predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f" [RF]  {target.capitalize():<9}: {acc:.2%}")

    print("\n--- Importancia de Características (Top 3 por Posición) ---")
    importancias = model.get_feature_importance()
    for target in targets:
        top_features = importancias[target].head(3).index.tolist()
        print(f" - {target.capitalize():<9}: {', '.join(top_features)}")

if __name__ == "__main__":
    main()