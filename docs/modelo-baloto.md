# Modelo ML — Baloto

## 1. Análisis del conjunto de datos

### Estructura del archivo histórico

| Campo | Tipo | Descripción |
|---|---|---|
| `fecha` | string | Fecha del sorteo |
| `n1` | int | Primera balota ganadora |
| `n2` | int | Segunda balota ganadora |
| `n3` | int | Tercera balota ganadora |
| `n4` | int | Cuarta balota ganadora |
| `n5` | int | Quinta balota ganadora |
| `superbalota` | int | Balota especial (superbalota) |

### Fuente de datos

- Archivo histórico: `bd/historical/baloto/baloto_historico.csv`
- Separador: `,` (formato estándar CSV)
- Datos cargados por el modelo `BalotoModel` de `app/ml/baloto/baloto_ml.py`

---

## 2. Preparación de datos

### Limpieza y transformación

El modelo realiza los siguientes pasos en `load_data()`:

1. Leer el CSV desde `self.data_path`.
2. A diferencia de las loterías convencionales, **Baloto no tiene la columna "Tipo de Premio"**, por lo que se asume que todos los registros del CSV histórico corresponden a sorteos válidos del acumulado principal y se cargan sin filtrado de premio mayor.

### Características utilizadas

El modelo entrena analizando la frecuencia histórica de cada número en las columnas:

- `n1` a `n5` (para las 5 balotas principales)
- `superbalota` (para el número especial)

---

## 3. Arquitectura del modelo

### Tipo de modelo

`BalotoModel` utiliza un enfoque estadístico de **Muestreo Ponderado por Frecuencia** (Frequency-Weighted Sampling). 

### Reglas de negocio

- **Distribución Conjunta:** Los números de las columnas `n1` a `n5` se combinan en un único conjunto de datos para determinar la frecuencia real de aparición de cada número del 1 al 43, sin importar en qué posición exacta salió.
- **Distribución Independiente:** La `superbalota` (1 al 16) mantiene su propia distribución de frecuencia.
- **Muestreo sin reemplazo:** Las 5 balotas principales se eligen asegurando que no haya números repetidos en la misma predicción.

---

## 4. Flujo de entrenamiento

El ciclo completo es:

1. `load_data()`
   - Verifica la existencia del archivo.
   - Carga el DataFrame completo desde el archivo CSV.
2. `train()`
   - Concatena las columnas de `n1` a `n5` en una sola serie y calcula la frecuencia empírica de aparición de cada número.
   - Calcula la frecuencia empírica para la columna `superbalota`.
   - Genera dos diccionarios de probabilidades que guiarán la predicción.
3. `predict()`
   - Utiliza `numpy.random.choice` con `replace=False` y las probabilidades calculadas para extraer 5 números principales.
   - Ordena los 5 números principales de menor a mayor.
   - Utiliza `numpy.random.choice` para extraer 1 superbalota basada en su propia probabilidad.

---

## 5. Resultado de la predicción

### Salida esperada

`predict()` devuelve una lista de 6 elementos en el siguiente formato:

- `[n1, n2, n3, n4, n5, superbalota]`

Donde `n1` a `n5` son enteros ordenados ascendentemente, y `superbalota` es el sexto entero.

### Integración con el Formato de la API

Este retorno cumple con la configuración registrada en `LOTTERY_PREDICTION_FORMATS` para baloto, la cual especifica:
- `main_count: 5`
- `has_special: True`
- `has_serie: False`

---

## 6. Reglas de contrato e integración

### Interfaz `BaseModel`

`BalotoModel` cumple con el contrato general de la aplicación:

- `load_data()`
- `train()`
- `predict()`

### Registro centralizado

El modelo se añade correctamente en:
- `app/config/registry.py` bajo la clave `"baloto"`.
- `app/config/__init__.py` con su nombre visual `"Baloto"`.

---

## 7. Limitaciones y consideraciones

- Al basarse exclusivamente en frecuencias históricas directas, el modelo asume que las tendencias pasadas se mantendrán. Si existiesen cambios en la mecánica del juego de Baloto (por ejemplo, agregar o quitar balotas de la urna), se requeriría depurar el archivo CSV de sorteos antiguos.
- La semilla (`seed`) provista en `predict()` asegura resultados deterministas, lo cual es vital para reproducibilidad en pruebas y peticiones concurrentes a la API.

---

## 8. Recomendaciones futuras

- **Incorporación de Reglas de Oro:** Validar estadísticas secundarias (como cantidad de pares/impares y suma total del array generado) de manera similar a cómo se aplica en loterías de 4 cifras.
- **Diferenciación de Sorteo Revancha:** Incorporar la capacidad de predecir o diferenciar los sorteos de Baloto Revancha si se integran los datos históricos en el CSV.
