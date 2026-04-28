# API Specification - Proyecto Final

**Base URL:** `http://localhost:9002`
**Formato:** JSON
**Version:** `1.0.0`

> Los endpoints de negocio usan el prefijo `/api/`. El endpoint `/health`
> queda fuera del prefijo porque lo usa el healthcheck del contenedor.
> Swagger UI esta disponible en `/docs` solo cuando `ENV=development`.

---

## Estado actual

La API implementada actualmente expone solo estos endpoints:

- `GET /health`
- `GET /api/lotteries`
- `POST /api/predict`
- `POST /api/train`
- `GET /api/train/{job_id}/status`

No existe un endpoint HTTP para scraping. El modulo `app/backend/scrapper.py`
es una utilidad especifica para Baloto y no aplica automaticamente a las demas
loterias. Las loterías usan el CSV historico disponible en
`app/bd/historical/loteria_xxxxx/xxxxx_historico.csv`. donde xxxxx es la lotería.

Loterias registradas en el `REGISTRY` hoy:

```json
["cundinamarca"]
```

La API ya conoce el formato de respuesta de Baloto para evitar romper el
contrato cuando se implemente y se registre su modelo, pero Baloto no aparece
en `/api/lotteries` mientras no este en `REGISTRY`.

---

## GET /health

Verifica que el servicio este activo.

### Response `200 OK`

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## GET /api/lotteries

Retorna la lista de loterias registradas en el `REGISTRY`. El frontend puede
usar esta respuesta para construir el selector dinamicamente.

### Response `200 OK`

```json
{
  "lotteries": [
    {
      "id": "cundinamarca",
      "name": "Lotería de Cundinamarca"
    }
  ]
}
```

### Campos

| Campo | Tipo | Descripcion |
|---|---|---|
| `lotteries` | `array` | Lista de loterias disponibles |
| `lotteries[].id` | `string` | Slug interno usado en `/api/predict` y `/api/train` |
| `lotteries[].name` | `string` | Nombre legible para mostrar en UI |

---

## POST /api/predict

Genera una prediccion para la loteria indicada. La implementacion actual carga
datos, entrena el modelo y predice en la misma solicitud.

### Request Body

```json
{
  "lottery": "cundinamarca"
}
```

| Campo | Tipo | Requerido | Descripcion |
|---|---|---|---|
| `lottery` | `string` | Si | Slug de una loteria registrada |

### Response `200 OK` - Lotería de 4 cifras + serie

```json
{
  "lottery": "cundinamarca",
  "prediction": {
    "main_numbers": [0, 4, 7, 1],
    "special_number": null,
    "serie": "153"
  },
  "statistics": {
    "even_count": 2,
    "odd_count": 2,
    "even_odd_ratio": "2:2",
    "sum": 12,
    "sum_in_optimal_range": true,
    "optimal_sum_range": {
      "min": 10,
      "max": 26
    },
    "frequency_score": 0.0,
    "pattern_score": 0.0
  },
  "generated_at": "2024-05-27T10:30:00Z"
}
```

### Response `200 OK` - Lotería de 5 números + especial

Para loterías tipo Baloto, la respuesta mantiene el mismo contenedor
`prediction`, pero cambia la cardinalidad de los valores:

```json
{
  "lottery": "baloto",
  "prediction": {
    "main_numbers": [5, 12, 30, 36, 40],
    "special_number": 9,
    "serie": null
  },
  "statistics": {
    "even_count": 4,
    "odd_count": 1,
    "even_odd_ratio": "4:1",
    "sum": 123,
    "sum_in_optimal_range": null,
    "optimal_sum_range": null,
    "frequency_score": 0.0,
    "pattern_score": 0.0
  },
  "generated_at": "2024-05-27T10:30:00Z"
}
```

### Campos

| Campo | Tipo | Descripcion |
|---|---|---|
| `lottery` | `string` | Slug enviado en el request |
| `prediction.main_numbers` | `int[]` | Numeros principales normalizados segun el tipo de loteria |
| `prediction.special_number` | `int|null` | Numero especial cuando aplica. En loterias tipo Baloto corresponde a la superbalota |
| `prediction.serie` | `string|null` | Serie con cero-padding a 3 caracteres cuando aplica. En loterias sin serie es `null` |
| `statistics.even_count` | `int` | Cantidad de valores pares en `main_numbers` |
| `statistics.odd_count` | `int` | Cantidad de valores impares en `main_numbers` |
| `statistics.even_odd_ratio` | `string` | Relacion pares:impares |
| `statistics.sum` | `int` | Suma de los valores en `main_numbers` |
| `statistics.sum_in_optimal_range` | `bool|null` | `true` si la suma esta en el rango optimo configurado; `null` si la loteria no tiene rango definido |
| `statistics.optimal_sum_range` | `object|null` | Rango optimo configurado para el tipo de loteria. Para loterias de 4 cifras hoy es `{ "min": 10, "max": 26 }`; para Baloto es `null` hasta definir uno |
| `statistics.frequency_score` | `float` | Actualmente `0.0`; reservado para evolucion del modelo |
| `statistics.pattern_score` | `float` | Actualmente `0.0`; reservado para evolucion del modelo |
| `generated_at` | `string` | Timestamp UTC con formato `YYYY-MM-DDTHH:MM:SSZ` |

> En loterias de 4 cifras, `main_numbers` contiene digitos individuales. Se
> devuelven separados para preservar ceros a la izquierda: el numero `0471` se
> representa como `[0, 4, 7, 1]`, no como el entero `471`.

### Errores

| HTTP | Causa | Forma actual |
|---|---|---|
| `422` | Falta `lottery` o el body no cumple el schema Pydantic | Error de validacion de FastAPI |
| `404` | La loteria no existe en el `REGISTRY` | `{"detail": "..."} ` |

Ejemplo `404`:

```json
{
  "detail": "'invalida': lotería no registrada. Disponibles: ['cundinamarca']"
}
```

---

## POST /api/train

Encola el entrenamiento del modelo para una loteria. La tarea corre como
`BackgroundTask` de FastAPI y el estado se guarda en memoria del proceso.

### Request Body

```json
{
  "lottery": "cundinamarca"
}
```

| Campo | Tipo | Requerido | Descripcion |
|---|---|---|---|
| `lottery` | `string` | Si | Slug de una loteria registrada |

### Response `202 Accepted`

```json
{
  "job_id": "e1e3c00c-febf-469a-b081-c7d2b2270f7c",
  "status": "queued",
  "lottery": "cundinamarca"
}
```

### Campos

| Campo | Tipo | Descripcion |
|---|---|---|
| `job_id` | `string` | UUID generado para el trabajo |
| `status` | `string` | Estado inicial: `queued` |
| `lottery` | `string` | Loteria solicitada |

### Errores

| HTTP | Causa | Forma actual |
|---|---|---|
| `422` | Falta `lottery` o el body no cumple el schema Pydantic | Error de validacion de FastAPI |
| `404` | La loteria no existe en el `REGISTRY` | `{"detail": "..."} ` |

---

## GET /api/train/{job_id}/status

Consulta el estado de un trabajo creado por `POST /api/train`.

### Path Parameter

| Parametro | Tipo | Descripcion |
|---|---|---|
| `job_id` | `string` | UUID retornado por `POST /api/train` |

### Response `200 OK`

```json
{
  "job_id": "e1e3c00c-febf-469a-b081-c7d2b2270f7c",
  "status": "completed",
  "lottery": "cundinamarca",
  "error": null
}
```

### Campos

| Campo | Tipo | Descripcion |
|---|---|---|
| `job_id` | `string` | UUID del trabajo |
| `status` | `string` | Estado actual: `queued`, `running`, `completed` o `failed` |
| `lottery` | `string` | Loteria asociada al trabajo |
| `error` | `string|null` | Mensaje de error si el trabajo fallo; `null` en caso contrario |

### Valores de `status`

| Valor | Significado |
|---|---|
| `queued` | El trabajo fue recibido, aun no inicio |
| `running` | El entrenamiento esta en curso |
| `completed` | El entrenamiento termino exitosamente |
| `failed` | El entrenamiento fallo; ver campo `error` |

### Flujo recomendado

```text
POST /api/train  ->  recibe job_id
GET /api/train/{job_id}/status  ->  polling cada 2-3 segundos
status == "completed"  ->  mostrar exito
status == "failed"     ->  mostrar error
```

### Errores

| HTTP | Causa | Forma actual |
|---|---|---|
| `404` | El `job_id` no existe en el registro en memoria | `{"detail": "job '<id>' no encontrado"}` |

---

## Notas de implementacion

1. `lottery` siempre es el slug registrado, por ejemplo `cundinamarca`.
2. La API normaliza la prediccion segun `LOTTERY_PREDICTION_FORMATS`.
3. Para loterias de 4 cifras, los valores de `main_numbers` son digitos individuales, no un entero compuesto.
4. La serie se devuelve como string de 3 caracteres con cero-padding cuando aplica; si no aplica, se devuelve `null`.
5. `job_id` es un UUID, no sigue un patron basado en fecha.
6. Los trabajos de entrenamiento se guardan en memoria; se pierden si el proceso reinicia.
7. Los errores usan la forma nativa de FastAPI (`detail` y errores `422` de Pydantic), no un wrapper `error.code`.
8. El scraping no esta expuesto como API y, en el codigo actual, solo existe como utilidad para Baloto.
