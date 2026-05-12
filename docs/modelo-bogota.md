# Modelo ML — Lotería de Bogotá

## 1. Análisis del conjunto de datos

### Estructura del archivo histórico

| Campo | Tipo | Rango | Descripción |
|---|---|---|---|
| `LOTERIA` | int | 2 | Código de la lotería |
| `SORTEO` | int | 2216–2764 | Número secuencial del sorteo |
| `FECHA` | string | dd/mm/yyyy | Fecha del sorteo |
| `NOMBRE_PREMIO` | string | PREMIO MAYOR / PREMIOS SECOS | Tipo de premio |
| `NUMERO` | int | 0–9999 | **Número de 4 dígitos** (objetivo del modelo) |
| `SERIE` | int | 0–999 | Serie del billete ganador |

### Registros disponibles

- **Total de filas:** 30.155
- **Premio Mayor (objetivo):** 547 registros (2014–2024)
- **Secos (premios secundarios):** 29.608 registros — excluidos del entrenamiento según el alcance del proyecto
- **Frecuencia de sorteo:** semanal (aproximadamente 52 sorteos/año)

---

## 2. Análisis estadístico por posición de dígito

El número ganador es un entero de 4 dígitos (0000–9999). Se analizó la distribución de frecuencia de cada dígito (0–9) en cada posición sobre los 547 registros del Premio Mayor.

### Test Chi-cuadrado de uniformidad (hipótesis nula: distribución uniforme)

| Posición | Chi² | p-valor | Conclusión |
|---|---|---|---|
| **Miles** | 11.99 | 0.2136 | **Uniforme** |
| **Centenas** | 10.20 | 0.3343 | **Uniforme** |
| **Decenas** | 5.74 | 0.7654 | **Uniforme** |
| **Unidades** | 11.23 | 0.2605 | **Uniforme** |

### Frecuencia de dígitos en la posición Miles

| Dígito | Frecuencia | Esperado (uniforme) |
|---|---|---|
| 0 | 48 | 54.7 |
| 1 | 59 | 54.7 |
| 2 | 52 | 54.7 |
| 3 | 58 | 54.7 |
| 4 | 56 | 54.7 |
| 5 | 49 | 54.7 |
| 6 | 60 | 54.7 |
| 7 | 55 | 54.7 |
| 8 | 55 | 54.7 |
| 9 | 55 | 54.7 |

**Todas las posiciones de Bogotá son estadísticamente uniformes** (p > 0.05). No existe un sesgo significativo en ninguna posición.

---

## 3. Por qué los algoritmos complejos NO son apropiados

| Algoritmo | Razón de descarte |
|---|---|
| **LSTM / RNN** | Requiere mínimo 1.000–5.000 secuencias temporales. Con 547 registros sobreajustaría completamente. |
| **Random Forest / XGBoost** | El espacio de salida tiene 10.000 clases posibles (0000–9999). Con 547 muestras de entrenamiento el modelo puede generalizar parcialmente, pero es ineficiente. |
| **Regresión Lineal** | Los números de lotería no tienen relación lineal entre sorteos consecutivos. |
| **Cadenas de Markov** | Requeriría una matriz de transición de 10.000×10.000 estados. Con 547 observaciones la densidad de transiciones sería insuficiente. |
| **K-Nearest Neighbors** | En un espacio de 4 dimensiones con 547 puntos, los vecinos más cercanos capturan patrones limitados. |

---

## 4. Algoritmo seleccionado: Red Neuronal MLP Regressor

### Definición

**MLPRegressor** es una red neuronal de retropropagación que aprende la relación no lineal entre características temporales (año, mes, número de sorteo) y los valores del número ganador y serie.

### Justificación

- **Dataset moderado (547 registros):** suficiente para entrenar una red neuronal simple sin sobreajuste severo
- **Características temporales:** el modelo puede aprender patrones estacionales o tendencias en los sorteos
- **Salida continua:** permite modelar la relación entre tiempo y valores numéricos
- **Flexibilidad:** puede capturar relaciones no lineales que algoritmos más simples no detectarían

### Flujo del algoritmo

```
1. load_data()
   └── Leer bogota_historico.csv
   └── Filtrar solo NOMBRE_PREMIO contiene 'MAYOR'
   └── Procesar FECHA → extraer Año, Mes
   └── Limpiar NUMERO y SERIE → extraer dígitos numéricos
   └── Guardar DataFrame procesado

2. train()
   └── X = [Año, Mes, SORTEO]
   └── y = [NUMERO, SERIE]
   └── Escalar X con StandardScaler
   └── Entrenar MLPRegressor con capas (200, 100, 50)
   └── Calcular R² sobre conjunto de prueba

3. predict()
   └── Proyectar próximo sorteo: max(SORTEO) + 1
   └── Usar último Año/Mes conocido
   └── Escalar features de predicción
   └── Generar predicción continua
   └── Convertir a 4 dígitos + serie: [d0, d1, d2, d3, serie]
```

### Hiperparámetros

| Parámetro | Valor | Justificación |
|---|---|---|
| `hidden_layer_sizes` | `(200, 100, 50)` | Arquitectura profunda para capturar relaciones complejas |
| `max_iter` | `2500` | Suficiente para convergencia en dataset moderado |
| `random_state` | `42` | Reproducibilidad |
| `test_size` | `0.15` | Validación sobre ~82 muestras |

### Propiedades del modelo

| Propiedad | Valor |
|---|---|
| Complejidad de entrenamiento | O(iteraciones × neuronas) |
| Complejidad de predicción | O(1) — forward pass |
| Memoria requerida | O(neuronas × features) |
| Interpretabilidad | Baja — caja negra |
| Riesgo de sobreajuste | Moderado con regularización implícita |

---

## 5. Resultado de la predicción

### Salida esperada

`predict()` devuelve una lista de cinco elementos:

- `[d0, d1, d2, d3, serie_predicha]`
- `d0-d3`: dígitos individuales del número (0-9 cada uno)
- `serie_predicha`: entero de hasta 3 dígitos (0-999)

### Construcción del próximo sorteo

- Se usa el último año/mes presente en el histórico para la predicción
- El siguiente sorteo se calcula como `max(SORTEO) + 1`
- La red neuronal predice valores continuos que se convierten a enteros

### Normalización del número y la serie

Después de predecir, los valores se convierten:
- `numero_predicho = int(abs(prediccion[0])) % 10000`
- `numero_str = str(numero_predicho).zfill(4)`
- `main_digits = [int(d) for d in numero_str]`
- `serie = int(abs(prediccion[1])) % 1000`
- `return main_digits + [serie]`

---

## 6. Reglas de contrato e integración

### Interfaz `BaseModel`

`BogotaModel` cumple con el contrato de la aplicación:

- `load_data()`
- `train()`
- `predict()`

Esto permite que el modelo sea usado por el selector general y por los
endpoints `/api/train` y `/api/predict`.

### Registro en `app/config/registry.py`

El modelo se añade con el slug:

- `"bogota"`

Esto hace que la API pueda reconocer y ejecutar la lotería de Bogotá
cuando se solicite por ese identificador.

### Formato de predicción en `LOTTERY_PREDICTION_FORMATS`

Bogotá usa el formato estándar de 4 dígitos + serie:

```python
"bogota": {
    "main_count": 4,
    "has_special": False,
    "has_serie": True,
    "optimal_sum_min": 10,
    "optimal_sum_max": 26,
}
```

---

## 7. Limitaciones y consideraciones

- **Dataset moderado:** 547 registros permiten entrenamiento de red neuronal pero limitan la generalización
- **Sobreajuste potencial:** MLP puede memorizar patrones específicos del histórico
- **Interpretabilidad baja:** como modelo de caja negra, es difícil explicar por qué genera ciertos números
- **Convergencia:** puede requerir múltiples iteraciones; usa `max_iter=2500` como límite superior
- Si el CSV histórico no existe, `load_data()` lanza `FileNotFoundError`

---

## 8. Recomendaciones futuras

- **Evaluar FWMS alternativo:** dado que todas las posiciones son uniformes, considerar Muestreo Multinomial Ponderado por Frecuencia como en Medellín
- Añadir validación de formato para `NUMERO` y `SERIE` después de la predicción
- Implementar un mecanismo de actualización de datos para la fuente histórica de Bogotá
- Considerar ensemble de modelos (MLP + FWMS) para combinar aprendizaje profundo con estadística robusta
- Añadir métricas de incertidumbre en las predicciones

---

## 9. Conclusión

El **MLPRegressor** proporciona una aproximación viable para la Lotería de Bogotá dado el tamaño moderado del dataset (547 registros). Aunque estadísticamente todas las posiciones son uniformes (lo que favorecería FWMS), el modelo de red neuronal permite explorar relaciones temporales complejas que podrían existir en los datos.

Sin embargo, para máxima robustez estadística y simplicidad, se recomienda evaluar FWMS como alternativa, especialmente si el dataset crece poco en el futuro.
