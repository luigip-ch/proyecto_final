# Modelo ML — Lotería de Boyacá

## 1. Análisis del conjunto de datos

### Estructura del archivo histórico

| Campo | Tipo | Descripción |
|---|---|---|
| `Año del Sorteo` | string | Año del sorteo, a veces con formato local. |
| `Mes del Sorteo` | int | Mes del sorteo. |
| `Fecha del Sorteo` | string | Fecha del sorteo en formato `dd/mm/yyyy`. |
| `Número del Sorteo` | int | Secuencia creciente del sorteo. |
| `Numero billete ganador` | int | Número ganador de 4 dígitos. |
| `Numero serie ganadora` | int | Serie ganadora hasta 3 dígitos. |
| `Tipo de Premio` | string | Identifica el premio mayor (`Mayor`). |

### Fuente de datos

- Archivo histórico: `bd/historical/loteria_boyaca/boyaca_historico.csv`
- El modelo carga y filtra solo los registros con `Tipo de Premio == "Mayor"`.

---

## 2. Preparación de datos

### Limpieza y transformación

El modelo realiza los siguientes pasos en `load_data()`:

1. Cargar el CSV desde `self.data_path`.
2. Filtrar únicamente los registros cuyo `Tipo de Premio` sea el valor
   definido en `PRIZE_TYPE_FILTER`.
3. Parsear `Fecha del Sorteo` con `pd.to_datetime(..., dayfirst=True)`.
4. Extraer componentes temporales:
   - `Año`
   - `Mes`
   - `DiaSemana`
5. Normalizar columnas numéricas con extracción de dígitos cuando sea necesario.
6. Descomponer el número ganador en sus 4 dígitos: `miles`, `centenas`,
   `decenas`, `unidades`.
7. Descomponer la serie en 3 dígitos: `serie_hundreds`, `serie_tens`,
   `serie_units`.
8. Construir características del sorteo anterior con desplazamiento (`shift(1)`).

### Características utilizadas

El conjunto de entrenamiento se construye con estas columnas:

- `Año`
- `Mes`
- `DiaSemana`
- `Numero del Sorteo`
- `prev_miles`
- `prev_centenas`
- `prev_decenas`
- `prev_unidades`
- `prev_serie_hundreds`
- `prev_serie_tens`
- `prev_serie_units`

Los objetivos predichos son:

- `miles`
- `centenas`
- `decenas`
- `unidades`
- `serie_hundreds`
- `serie_tens`
- `serie_units`

---

## 3. Arquitectura del modelo

### Tipo de modelo

`BoyacaModel` utiliza un conjunto de clasificadores `RandomForestClassifier`
de `scikit-learn`.

### Motivación del algoritmo

El algoritmo actual es mejor que una simple muestreo independiente porque:

- captura dependencias secuenciales entre sorteos a través de características
  del sorteo anterior,
- modela de forma separada cada posición del número y cada dígito de la serie,
- conserva la salida esperada por la API: 4 dígitos independientes más serie.

### Hiperparámetros

- `n_estimators`: 100
- `random_state`: 42

---

## 4. Flujo de entrenamiento

1. `load_data()`
   - Carga el CSV histórico.
   - Filtra por premio mayor.
   - Procesa fechas y números.
   - Calcula columnas previas para el sorteo anterior.
   - Deja `self.last_features` lista para la predicción.
2. `train()`
   - Extrae las características y los objetivos.
   - Entrena un clasificador por cada posición del número y de la serie.
3. `predict()`
   - Usa `self.last_features` como entrada para la predicción del próximo sorteo.
   - Muestrea según las probabilidades devueltas por cada clasificador.
   - Reconstruye la serie desde sus dígitos predichos.

---

## 5. Resultado de la predicción

### Salida esperada

`predict()` devuelve una lista de 5 enteros:

- `[miles, centenas, decenas, unidades, serie]`

### Construcción de la serie

La serie se reconstruye como:

- `serie_hundreds * 100 + serie_tens * 10 + serie_units`

Esto permite preservar la forma original de 3 dígitos cuando el valor
supera los 99.

---

## 6. Cumplimiento del contrato de la API

### Interfaz `BaseModel`

`BoyacaModel` cumple el contrato esperado por la aplicación:

- `load_data()`
- `train()`
- `predict()`

### Formato de predicción

La API espera que `predict()` devuelva una lista de enteros que pueda
normalizarse a:

- `main_numbers`: 4 dígitos
- `serie`: 1 entero

Este contrato se conserva exactamente.

---

## 7. Consideraciones

- El modelo utiliza un enfoque supervisado en lugar de dependencias de
  frecuencia aisladas.
- Requiere un histórico con al menos un sorteo previo para construir
  características `prev_*`.
- Si el histórico queda vacío después de filtrar y desplazar, el modelo
  falla explícitamente con un error de datos insuficientes.

---

## 8. Recomendaciones futuras

- Evaluar métricas de clasificación por posición para validar la calidad del
  modelo.
- Añadir pruebas de integridad para asegurarse de que la serie reconstruida
  mantiene el formato de 3 dígitos en el endpoint.
- Explorar modelos secuenciales si el histórico crece en cantidad y muestra
  comportamiento temporal más marcado.
