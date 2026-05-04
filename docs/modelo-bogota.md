# Modelo ML — Lotería de Bogotá

## 1. Análisis del conjunto de datos

### Estructura del archivo histórico

| Campo | Tipo | Descripción |
|---|---|---|
| `FECHA` | string | Fecha del sorteo (formato flexible, se parsea con pandas) |
| `NUMERO` | int / string | Número ganador (4 dígitos) |
| `SERIE` | int / string | Serie ganadora (hasta 3 dígitos) |
| `SORTEO` | int / string | Número secuencial del sorteo |

### Fuente de datos

- Archivo histórico: `bd/historical/loteria_bogota/bogota_historico.csv`
- Separador: `;`
- Codificación: `latin1`
- Datos cargados por el modelo `BogotaModel` de `app/ml/bogota/bogota_ml.py`

---

## 2. Preparación de datos

### Limpieza y transformación

El modelo realiza los siguientes pasos en `load_data()`:

1. Leer el CSV desde `self.data_path`.
2. Parsear `FECHA` con `pd.to_datetime(..., format='mixed')`.
3. Extraer `Año` y `Mes` de la fecha.
4. Normalizar las columnas `NUMERO`, `SERIE` y `SORTEO`.
   - Se extraen solo los dígitos con `str.extract(r"(\d+)")`.
   - Cualquier valor no numérico se convierte en `0` si no contiene dígitos.
5. Guardar el DataFrame procesado en `self.df`.

### Características utilizadas

El modelo entrena usando estas columnas como entrada:

- `Año`
- `Mes`
- `SORTEO`

El objetivo es predecir:

- `NUMERO`
- `SERIE`

---

## 3. Arquitectura del modelo

### Tipo de modelo

`BogotaModel` utiliza un **MLPRegressor** de `scikit-learn`.

### Hiperparámetros

| Parámetro | Valor |
|---|---|
| `hidden_layer_sizes` | `(200, 100, 50)` |
| `max_iter` | `2500` |
| `random_state` | `42` |
| `test_size` | `0.15` |

### Escalado

Se aplica `StandardScaler` a las características antes de entrenar.
Esto ayuda al MLP a converger mejor y trata las columnas `Año`, `Mes` y `SORTEO`
como variables en la misma escala.

---

## 4. Flujo de entrenamiento

El ciclo completo es:

1. `load_data()`
   - Carga el DataFrame histórico
   - Procesa y normaliza columnas
2. `train()`
   - Extrae `X = ['Año', 'Mes', 'SORTEO']`
   - Extrae `y = ['NUMERO', 'SERIE']`
   - Escala `X`
   - Divide datos en entrenamiento/prueba
   - Ajusta `MLPRegressor`
   - Calcula `R²` sobre el conjunto de prueba
3. `predict()`
   - Proyecta el próximo sorteo usando `max(SORTEO) + 1`
   - Aplica el mismo escalador a la fila de predicción
   - Redondea valores predichos a enteros positivos

---

## 5. Resultado de la predicción

### Salida esperada

`predict()` devuelve una lista de dos elementos:

- `numero_predicho` (int)
- `serie_predicha` (int)

### Construcción del próximo sorteo

- Se usa el último año/mes presente en el histórico para la predicción.
- El siguiente sorteo se calcula como `max(SORTEO) + 1`.

### Normalización del número y la serie

Después de predecir, los valores se convierten en enteros con `int(abs(...))`
para garantizar que el resultado sea siempre un número no negativo.

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

---

## 7. Limitaciones y consideraciones

- El dataset es pequeño para un modelo de red neuronal; el MLP puede dar
  advertencias de convergencia con pocos registros.
- `NUMERO` y `SERIE` se predicen directamente como valores continuos
  regresivos y luego se redondean.
- El modelo no aplica reglas de validación adicionales sobre el número
  generado, más allá de usar la predicción del regresor.
- Si el CSV histórico no existe, `load_data()` lanza `FileNotFoundError`.

---

## 8. Recomendaciones futuras

- Añadir validación de formato para `NUMERO` y `SERIE` después de la predicción
  (por ejemplo, asegurar que `NUMERO` tenga 4 dígitos).
- Implementar un mecanismo de actualización de datos para la fuente histórica de
  Bogotá.
- Evaluar alternativas más simples si el dataset no crece significativamente,
  como modelos basados en frecuencia o transformaciones numéricas.
