# Sorteo Extra de Colombia - ML Model

## Resumen del Modelo

Este documento describe la arquitectura y el diseño del modelo de Machine Learning desarrollado para predecir los resultados del **Sorteo Extra de Colombia**. A diferencia de otros modelos, esta implementación emplea explícitamente **Random Forest con Validación Cruzada (Cross-Validation)** y **Ajuste de Hiperparámetros (Train/Test Tuning)** para maximizar la eficacia en la predicción del premio mayor.

## Estructura y Funcionamiento

El modelo reside en el archivo `app/ml/sorteo_extra_de_colombia/sorteo_extra_de_colombia_ml.py` y define la clase `SorteoExtraDeColombiaModel`. Este hereda de `BaseModel` y mantiene la compatibilidad con el contrato estricto de la API devolviendo un número de 4 dígitos y una serie de 3.

### Proceso de Entrenamiento y Validación Cruzada (Train/Test Tuning)

A diferencia del FWMS tradicional o RNN, este algoritmo busca los parámetros óptimos del clasificador de Random Forest empleando `GridSearchCV` de la librería scikit-learn.

1. **Definición del Grid de Hiperparámetros**:
   - `n_estimators`: [100, 200]
   - `max_depth`: [5, 10, 15]
   - `min_samples_split`: [2, 5]
   - `class_weight`: 'balanced' para mejorar el manejo del ruido y la distribución desigual de clases.
   
2. **Validación Cruzada**:
   El modelo divide la serie de tiempo en ventanas con `cv=3`. De esta manera, evalúa sistemáticamente varias configuraciones del bosque aleatorio y elige el mejor estimador basado en métricas de precisión ("accuracy").

3. **Entrenamiento de los estimadores**:
   Se entrenan 5 modelos independientes, correspondientes a cada una de las posiciones objetivo (miles, centenas, decenas, unidades, y serie), garantizando así que cada variable cuente con su mejor clasificador Random Forest optimizado independientemente.

### Características (Features) Utilizadas

Las características con las que se alimentan los estimadores son:
- **Lags**: Valores del sorteo inmediatamente anterior (`prev_miles`, `prev_centenas`, `prev_decenas`, `prev_unidades`, `prev_serie`).
- **Componentes temporales**: Mes del año (`mes`) y Día de la semana (`dia_semana`) extraídos del campo temporal.

### Generación de la Predicción

Al invocar el método `predict()`, el modelo sigue la convención del proyecto:
1. Calcula las características (features) estimadas para el siguiente sorteo futuro (fecha del último sorteo histórico + 7 días).
2. Con los estimadores `RandomForestClassifier` óptimos extraídos del GridSearchCV, predice las probabilidades subyacentes (`predict_proba()`) para cada posición del número ganador y para la serie.
3. Se emplea un generador probabilístico pseudoaleatorio (numpy) para escoger las clases usando las probabilidades asignadas.
4. Se devuelve una lista final del tipo `[miles, centenas, decenas, unidades, serie]` cumpliendo exhaustivamente el contrato esperado por el endpoint.

## Integración con la API y Contrato

- **Endpoint**: `/api/predict?loteria=sorteo_extra_de_colombia`
- **Output Contrato**: 
  El output cumple con `DEFAULT_PREDICTION_FORMAT` definido en `app/config/__init__.py`. 
  Incluye `main_count: 4` (un número de 4 cifras), `has_serie: True` y un cálculo sobre los umbrales de suma óptima (`optimal_sum_min`, `optimal_sum_max`).
- **Segregación Estricta**:
  El diseño orientado a objetos asegura que las modificaciones y este motor de Cross-Validation impacten exclusivamente al Sorteo Extra de Colombia, sin alterar el funcionamiento interno ni los algoritmos ya calibrados de ninguna otra lotería (como la Cruz Roja, Cundinamarca, Medellín, etc.).
