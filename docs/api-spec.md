# API Specification — NEXLOT

**Base URL:** `http://localhost:9002`  
**Prefijo de endpoints:** `/api/`  
**Formato:** JSON  
**Versión:** 1.0.0

> Todos los endpoints bajo `/api/` son consumidos exclusivamente por el frontend. No están expuestos públicamente. Swagger disponible solo en `ENV=development` en `/docs`.

---

## Índice

- [GET /health](#get-health)
- [GET /api/lotteries](#get-apilotteries)
- [POST /api/predict](#post-apipredict)
- [POST /api/train](#post-apitrain)
- [GET /api/train/{job\_id}/status](#get-apitrainjob_idstatus)
- [POST /api/scrape](#post-apiscrape)
- [Códigos de error estándar](#códigos-de-error-estándar)
- [Reglas de implementación transversales](#reglas-de-implementación-transversales)

---

## GET /health

Verificación de estado del contenedor. Usado por Docker y monitoreo. No requiere autenticación.

### Response `200 OK`

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## GET /api/lotteries

Retorna la lista de loterias disponibles con toda la metadata necesaria para el frontend. El frontend construye el selector dinámicamente a partir de esta respuesta — ningún valor está hardcodeado en el frontend.

### Response `200 OK`

```json
{
  "lotteries": [
    {
      "id": "cundinamarca",
      "name": "Lotería de Cundinamarca",
      "short_name": "Cundinamarca",
      "draw_days": ["lunes"],
      "next_draw_date": "2024-05-27",
      "number_config": {
        "main_count": 4,
        "main_min": 0,
        "main_max": 9999,
        "has_special": false,
        "special_min": null,
        "special_max": null
      },
      "ui": {
        "primary_color": "#00E5CC",
        "special_number_color": null,
        "icon": "cundinamarca"
      },
      "model_status": "ready"
    },
    {
      "id": "baloto",
      "name": "Baloto",
      "short_name": "Baloto",
      "draw_days": ["miércoles", "sábado"],
      "next_draw_date": "2024-05-25",
      "number_config": {
        "main_count": 5,
        "main_min": 1,
        "main_max": 43,
        "has_special": true,
        "special_min": 1,
        "special_max": 16
      },
      "ui": {
        "primary_color": "#00E5CC",
        "special_number_color": "#E11D48",
        "icon": "baloto"
      },
      "model_status": "ready"
    }
  ]
}
```

### Descripción de campos

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `string` | Slug único de la lotería — usado en todos los demás endpoints |
| `name` | `string` | Nombre oficial completo |
| `short_name` | `string` | Nombre corto para UI compacta |
| `draw_days` | `string[]` | Días de sorteo en español, minúsculas |
| `next_draw_date` | `string` | Fecha ISO 8601 (`YYYY-MM-DD`) del próximo sorteo — usada para el countdown |
| `number_config.main_count` | `int` | Cantidad de números principales a generar |
| `number_config.main_min` | `int` | Valor mínimo del rango principal |
| `number_config.main_max` | `int` | Valor máximo del rango principal |
| `number_config.has_special` | `bool` | Si la lotería tiene número especial/balota |
| `number_config.special_min` | `int\|null` | Rango mínimo del número especial (`null` si `has_special: false`) |
| `number_config.special_max` | `int\|null` | Rango máximo del número especial (`null` si `has_special: false`) |
| `ui.primary_color` | `string` | Color hex para elementos de marca de esta lotería en el frontend |
| `ui.special_number_color` | `string\|null` | Color hex del número especial — `null` si no aplica |
| `ui.icon` | `string` | Identificador del ícono SVG de la lotería |
| `model_status` | `string` | Estado del modelo: `ready` \| `training` \| `not_trained` |

---

## POST /api/predict

Genera una combinación de números para la lotería indicada usando el modelo ML correspondiente.

### Request Body

```json
{
  "lottery": "cundinamarca"
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `lottery` | `string` | Sí | ID de la lotería (debe existir en el REGISTRY) |

### Response `200 OK` — Lotería sin número especial

```json
{
  "lottery": "cundinamarca",
  "prediction": {
    "main_numbers": [3, 17, 42, 68],
    "special_number": null
  },
  "statistics": {
    "even_count": 2,
    "odd_count": 2,
    "even_odd_ratio": "2:2",
    "sum": 130,
    "sum_in_optimal_range": true,
    "optimal_sum_range": {
      "min": 100,
      "max": 160
    },
    "frequency_score": 0.74,
    "pattern_score": 0.81
  },
  "generated_at": "2024-05-25T10:30:00Z"
}
```

### Response `200 OK` — Lotería con número especial (ej. Baloto)

```json
{
  "lottery": "baloto",
  "prediction": {
    "main_numbers": [7, 14, 23, 31, 42],
    "special_number": 5
  },
  "statistics": {
    "even_count": 2,
    "odd_count": 3,
    "even_odd_ratio": "2:3",
    "sum": 117,
    "sum_in_optimal_range": true,
    "optimal_sum_range": {
      "min": 85,
      "max": 150
    },
    "frequency_score": 0.68,
    "pattern_score": 0.77
  },
  "generated_at": "2024-05-25T10:30:00Z"
}
```

### Descripción de campos

| Campo | Tipo | Descripción |
|---|---|---|
| `prediction.main_numbers` | `int[]` | Números principales ordenados de menor a mayor |
| `prediction.special_number` | `int\|null` | Número especial — `null` si la lotería no tiene |
| `statistics.even_count` | `int` | Cantidad de números pares en la predicción |
| `statistics.odd_count` | `int` | Cantidad de números impares en la predicción |
| `statistics.even_odd_ratio` | `string` | Relación pares:impares — regla de oro del modelo |
| `statistics.sum` | `int` | Suma total de los números principales |
| `statistics.sum_in_optimal_range` | `bool` | Si la suma cae en el rango estadísticamente frecuente |
| `statistics.optimal_sum_range.min` | `int` | Límite inferior del rango de suma validado históricamente |
| `statistics.optimal_sum_range.max` | `int` | Límite superior del rango de suma validado históricamente |
| `statistics.frequency_score` | `float` | Score 0.00–1.00: frecuencia histórica de estos números |
| `statistics.pattern_score` | `float` | Score 0.00–1.00: coherencia del patrón con el modelo entrenado |
| `generated_at` | `string` | Timestamp ISO 8601 de generación |

### Errores

| Código HTTP | `code` | Condición |
|---|---|---|
| `400` | `INVALID_REQUEST` | Campo `lottery` ausente o vacío |
| `404` | `LOTTERY_NOT_FOUND` | Lotería no registrada en el REGISTRY |
| `409` | `MODEL_NOT_TRAINED` | Modelo de esa lotería sin entrenar |

---

## POST /api/train

Dispara el entrenamiento del modelo para una lotería. Operación asíncrona — responde de inmediato con un `job_id` y el entrenamiento corre en background.

### Request Body

```json
{
  "lottery": "cundinamarca"
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `lottery` | `string` | Sí | ID de la lotería |

### Response `202 Accepted`

```json
{
  "job_id": "train_cundinamarca_20240525_103000",
  "lottery": "cundinamarca",
  "status": "queued",
  "started_at": "2024-05-25T10:30:00Z",
  "message": "Entrenamiento iniciado. Consulta el estado en /api/train/train_cundinamarca_20240525_103000/status"
}
```

### Errores

| Código HTTP | `code` | Condición |
|---|---|---|
| `400` | `INVALID_REQUEST` | Campo `lottery` ausente |
| `404` | `LOTTERY_NOT_FOUND` | Lotería no registrada |
| `409` | `TRAINING_IN_PROGRESS` | Ya hay un job de entrenamiento activo para esa lotería |

---

## GET /api/train/{job\_id}/status

Consulta el estado de un job de entrenamiento. El frontend hace polling a este endpoint para actualizar la UI durante el proceso.

### Path Parameter

| Parámetro | Tipo | Descripción |
|---|---|---|
| `job_id` | `string` | ID retornado por `POST /api/train` |

### Response `200 OK` — En progreso

```json
{
  "job_id": "train_cundinamarca_20240525_103000",
  "lottery": "cundinamarca",
  "status": "running",
  "progress_pct": 45,
  "started_at": "2024-05-25T10:30:00Z",
  "estimated_completion": "2024-05-25T10:35:00Z"
}
```

### Response `200 OK` — Completado

```json
{
  "job_id": "train_cundinamarca_20240525_103000",
  "lottery": "cundinamarca",
  "status": "completed",
  "progress_pct": 100,
  "started_at": "2024-05-25T10:30:00Z",
  "completed_at": "2024-05-25T10:34:22Z",
  "estimated_completion": null,
  "metrics": {
    "records_trained": 1248,
    "model_accuracy": 0.83
  }
}
```

### Response `200 OK` — Fallido

```json
{
  "job_id": "train_cundinamarca_20240525_103000",
  "lottery": "cundinamarca",
  "status": "failed",
  "progress_pct": 12,
  "started_at": "2024-05-25T10:30:00Z",
  "completed_at": null,
  "estimated_completion": null,
  "failed_at": "2024-05-25T10:31:05Z",
  "error": "Datos históricos insuficientes para entrenar el modelo"
}
```

### Valores de `status`

| Valor | Descripción |
|---|---|
| `queued` | En cola, aún no inició |
| `running` | Ejecutando |
| `completed` | Finalizado con éxito |
| `failed` | Falló — ver campo `error` |

### Errores

| Código HTTP | `code` | Condición |
|---|---|---|
| `404` | `JOB_NOT_FOUND` | `job_id` no existe |

---

## POST /api/scrape

Dispara la actualización de datos históricos para una lotería. Operación asíncrona con el mismo patrón de polling que `/api/train`.

### Request Body

```json
{
  "lottery": "cundinamarca"
}
```

### Response `202 Accepted`

```json
{
  "job_id": "scrape_cundinamarca_20240525_103000",
  "lottery": "cundinamarca",
  "status": "queued",
  "started_at": "2024-05-25T10:30:00Z"
}
```

### Response de estado completado

```json
{
  "job_id": "scrape_cundinamarca_20240525_103000",
  "lottery": "cundinamarca",
  "status": "completed",
  "progress_pct": 100,
  "started_at": "2024-05-25T10:30:00Z",
  "completed_at": "2024-05-25T10:30:45Z",
  "estimated_completion": null,
  "metrics": {
    "new_records": 12,
    "total_records": 1260,
    "file_updated": "bd/historical/cundinamarca/cundinamarca.csv"
  }
}
```

> El estado del scrape se consulta en `GET /api/scrape/{job_id}/status` con la misma estructura que el endpoint de entrenamiento.

### Errores

| Código HTTP | `code` | Condición |
|---|---|---|
| `400` | `INVALID_REQUEST` | Campo `lottery` ausente |
| `404` | `LOTTERY_NOT_FOUND` | Lotería no registrada |
| `409` | `SCRAPE_IN_PROGRESS` | Ya hay un job de scraping activo para esa lotería |

---

## Códigos de error estándar

Todos los errores siguen la misma estructura. En `ENV=production` los mensajes nunca exponen detalles internos del sistema.

```json
{
  "error": {
    "code": "LOTTERY_NOT_FOUND",
    "message": "La lotería 'xxx' no está disponible",
    "status": 404
  }
}
```

| HTTP | `code` | Descripción |
|---|---|---|
| `400` | `INVALID_REQUEST` | Body malformado o campo requerido ausente |
| `404` | `LOTTERY_NOT_FOUND` | Lotería no registrada en el REGISTRY |
| `404` | `JOB_NOT_FOUND` | Job ID no existe |
| `409` | `MODEL_NOT_TRAINED` | Predicción solicitada con modelo sin entrenar |
| `409` | `TRAINING_IN_PROGRESS` | Ya hay un job de entrenamiento activo |
| `409` | `SCRAPE_IN_PROGRESS` | Ya hay un job de scraping activo |
| `429` | `RATE_LIMIT_EXCEEDED` | Demasiadas solicitudes |
| `500` | `INTERNAL_ERROR` | Error interno — log completo en servidor, mensaje genérico al cliente |

---

## Reglas de implementación transversales

1. **`lottery` siempre es el ID slug** (`cundinamarca`, `baloto`) — nunca el nombre completo
2. **`main_numbers` siempre ordenados** de menor a mayor
3. **Fechas siempre en ISO 8601** — fecha: `YYYY-MM-DD` / timestamp: `YYYY-MM-DDTHH:MM:SSZ`
4. **Scores siempre entre 0.00 y 1.00** con dos decimales
5. **`null` explícito** para campos opcionales ausentes — nunca omitir el campo
6. **`model_status`** en `/api/lotteries` refleja el estado real del modelo en el momento de la consulta
7. **Toda nueva lotería** que se agregue al REGISTRY debe implementar exactamente estos campos — este documento es el contrato del estándar
8. **`job_id` sigue el patrón** `{operacion}_{loteria}_{YYYYMMDD}_{HHMMSS}` — ej. `train_baloto_20240525_143000`
