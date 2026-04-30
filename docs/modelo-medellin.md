# Modelo ML — Lotería de Medellín

## 1. Análisis del conjunto de datos

### Estructura del archivo histórico

| Campo | Tipo | Rango | Descripción |
|---|---|---|---|
| `Año del Sorteo` | int | 2021–2023 | Año del sorteo |
| `Mes del Sorteo` | int | 1–12 | Mes del sorteo |
| `Fecha del Sorteo` | string | dd/mm/yyyy | Fecha exacta |
| `Lotería` | string | Loteria de Medellin | Nombre de la lotería |
| `Número del Sorteo` | int | 4510–4696 | Consecutivo oficial |
| `Numero billete ganador` | int | 4–9979 | **Número de 4 dígitos** (objetivo del modelo) |
| `Numero serie ganadora` | int | 2–453 | Serie del billete ganador |
| `Tipo de Premio` | string | Mayor / Secos | Categoría del premio |

### Registros disponibles

- **Total de filas:** 6.829
- **Premio Mayor (objetivo):** 191 registros (2021–2023)
- **Secos (premios secundarios):** 6.638 registros — excluidos del entrenamiento según el alcance del proyecto
- **Frecuencia de sorteo:** semanal (aproximadamente 50 sorteos/año)

---

## 2. Análisis estadístico por posición de dígito

El número ganador es un entero de 4 dígitos (0000–9999). Se analizó la distribución de frecuencia de cada dígito (0–9) en cada posición sobre los 191 registros del Premio Mayor.

### Test Chi-cuadrado de uniformidad (hipótesis nula: distribución uniforme)

| Posición | Chi² | p-valor | Conclusión |
|---|---|---|---|
| **Miles** | 13.55 | **0.1391** | **Uniforme** |
| **Centenas** | 9.05 | **0.4325** | **Uniforme** |
| **Decenas** | 6.64 | **0.6741** | **Uniforme** |
| **Unidades** | 6.33 | **0.7065** | **Uniforme** |

### Frecuencia de dígitos en la posición Miles

| Dígito | Frecuencia | Esperado (uniforme) |
|---|---|---|
| 0 | 12 | 19.1 |
| 1 | 25 | 19.1 |
| 2 | 17 | 19.1 |
| 3 | 27 | 19.1 |
| 4 | 19 | 19.1 |
| 5 | 13 | 19.1 |
| 6 | 15 | 19.1 |
| 7 | 26 | 19.1 |
| 8 | 20 | 19.1 |
| 9 | 17 | 19.1 |

A diferencia de Cundinamarca, **todas las posiciones de Medellín son estadísticamente uniformes** (p > 0.05). No existe un sesgo significativo en ninguna posición.

---

## 3. Por qué los algoritmos complejos NO son apropiados

| Algoritmo | Razón de descarte |
|---|---|
| **LSTM / RNN** | Requiere mínimo 1.000–5.000 secuencias temporales. Con 191 registros sobreajustaría completamente. |
| **Random Forest / XGBoost** | El espacio de salida tiene 10.000 clases posibles (0000–9999). Con 191 muestras de entrenamiento el modelo no puede generalizar. |
| **Regresión Lineal** | Los números de lotería no tienen relación lineal entre sorteos consecutivos. |
| **Cadenas de Markov** | Requeriría una matriz de transición de 10.000×10.000 estados. Con 191 observaciones la densidad de transiciones sería virtualmente cero. |
| **K-Nearest Neighbors** | En un espacio de 4 dimensiones con solo 191 puntos, los vecinos más cercanos no capturan ningún patrón probabilístico real. |

---

## 4. Algoritmo seleccionado: Muestreo Multinomial Ponderado por Frecuencia (FWMS)

### Definición

**Frequency-Weighted Multinomial Sampling (FWMS)** es un modelo estadístico generativo que:

1. Calcula la distribución empírica de frecuencia de cada dígito (0–9) en cada una de las 4 posiciones del número ganador, a partir del histórico de Premio Mayor
2. Usa esas distribuciones como pesos para el muestreo multinomial independiente por posición
3. Aplica reglas de validación estadística sobre el número generado

### Justificación científica

- **Todas las posiciones son uniformes (p > 0.05):** el muestreo ponderado por frecuencia empírica degrada suavemente a uniforme en todas las posiciones, lo cual es correcto estadísticamente.
- **191 registros son suficientes** para estimar distribuciones de 10 categorías (dígitos) por posición. La regla general es ≥5 observaciones por categoría; se cumple para todas las posiciones.
- **KISS y YAGNI:** el algoritmo más simple que el análisis estadístico justifica. No se introduce complejidad que los datos no soporten.

### Flujo del algoritmo

```
1. load_data()
   └── Leer medellin_historico.csv
   └── Filtrar solo Tipo de Premio == 'Mayor'
   └── Extraer columna 'Numero billete ganador'
   └── Descomponer en 4 dígitos por posición

2. train()
   └── Para cada posición [miles, centenas, decenas, unidades]:
       └── Contar frecuencia de cada dígito (0–9)
       └── Normalizar → distribución de probabilidad p[posición][dígito]
   └── Guardar distribuciones entrenadas en self.frecuencias

3. predict() → list[int]
   └── Para cada posición: muestrear 1 dígito según p[posición]
   └── Mantener los 4 dígitos por separado para preservar ceros a la izquierda
   └── Calcular estadísticas del número (paridad, suma, frecuencia)
   └── Retornar [miles, centenas, decenas, unidades, serie] como list[int]
```

### Propiedades del modelo

| Propiedad | Valor |
|---|---|
| Complejidad de entrenamiento | O(n) — un solo recorrido sobre los datos |
| Complejidad de predicción | O(1) — muestreo directo |
| Memoria requerida | O(40) — 4 posiciones × 10 dígitos |
| Interpretabilidad | Alta — las distribuciones son legibles |
| Riesgo de sobreajuste | Ninguno — el modelo no memoriza secuencias |

---

## 5. Reglas de validación estadística (capa post-generación)

Independientemente del dígito generado, el número final se valida contra las siguientes reglas derivadas del histórico:

| Regla | Cálculo sobre histórico | Rango observado |
|---|---|---|
| Paridad | Conteo de dígitos pares e impares en el número | 49.2% par / 50.8% impar |
| Suma de dígitos | Suma de los 4 dígitos del número (4–33) | Promedio: 18.01 |
| Diversidad de dígitos | Que no todos los dígitos sean iguales (ej. 1111) | Histórico: 0 repeticiones perfectas |

**Rango óptimo de suma observado:** 10–25 (164 de 191 sorteos, ~86% de los casos).

Si el número generado no cumple las reglas, se regenera hasta obtener uno válido (máximo 10 intentos).

---

## 6. Nota sobre el scrapper

El `scrapper.py` actual está implementado exclusivamente para **Baloto** (fuente: `baloto.com/resultados`). No está montado como endpoint HTTP y no forma parte del contrato de la API actual. Los datos históricos de la Lotería de Medellín provienen de una fuente diferente y ya están disponibles en el archivo CSV. El scraper de Medellín debe implementarse por separado cuando se requiera actualización de datos.

---

## 7. Conclusión

El **Muestreo Multinomial Ponderado por Frecuencia (FWMS)** es el algoritmo óptimo para la Lotería de Medellín porque:

1. Es el único algoritmo estadísticamente justificado dado el tamaño del dataset (191 registros)
2. Al ser todas las posiciones uniformes, el modelo degrada suavemente a distribución uniforme, lo cual es estadísticamente correcto
3. Cumple con los principios KISS y YAGNI — no introduce complejidad que los datos no soporten
4. Es 100% interpretable — el equipo puede auditar las distribuciones entrenadas
5. Produce predicciones coherentes con las reglas de oro del proyecto (paridad, suma, frecuencia)
