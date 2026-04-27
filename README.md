# Proyecto Final App  - ML Junior

## Participantes

- Denis Monsalve Naranjo
- Giovanni Galeano
- Luigi Piedrahita
- Daniel Rios Oquendo
- Ivan Rodriguez
- Andres Hincapie Vasquez
- Pedro Turriago Sanchez

## Objetivo General

Desarrollar e implementar modelos de Machine Learning orientados al análisis de series históricas, con el fin de generar combinaciones que cumplan criterios de distribución estadística, optimizando la proporción entre valores pares e impares y la frecuencia de sumas totales dentro de rangos probabilísticamente relevantes.

## Objetivos Específicos

1. Diseñar y entrenar modelos de Machine Learning capaces de identificar patrones, regularidades y comportamientos probabilísticos en series históricas, considerando variables como frecuencia, dispersión y distribución de datos.
2. Establecer e integrar reglas de optimización basadas en principios estadísticos (balance par/impar y rangos de suma total), que permitan validar y mejorar la calidad de las combinaciones generadas por los modelos, asegurando coherencia con tendencias históricas observadas.

## Alcance

Modelos de Machine Learning para analizar series históricas y generar combinaciones que cumplan reglas de oro de distribución estadística. Optimiza balances entre pares e impares y sumas totales frecuentes.

### Restricciones

- El análisis se enfoca exclusivamente en los **números ganadores del premio mayor** de las loterias.
- Se excluyen premios secundarios o categorías de premios menores.
- Los modelos se entrenan y validan únicamente con datos de premios mayores para asegurar la relevancia y calidad de las predicciones.

## Beneficios Esperados

Los beneficios del proyecto se pueden entender en tres niveles:

**Analítico:** Se logra una comprensión más profunda de los patrones subyacentes en los datos históricos. El modelo permite identificar regularidades, frecuencias y comportamientos que no son evidentes mediante análisis tradicionales, lo que incrementa la calidad del análisis estadístico y reduce la dependencia de supuestos intuitivos.

**Operativo:** Se optimiza la generación de combinaciones al incorporar reglas objetivas como el balance entre pares e impares y rangos de suma total frecuentes. Esto permite automatizar procesos que usualmente serían manuales, disminuyendo tiempos de análisis y aumentando la consistencia en los resultados.

**Toma de decisiones:** El proyecto aporta un enfoque basado en datos que mejora la coherencia y trazabilidad de las elecciones realizadas. Las combinaciones generadas no son aleatorias, sino sustentadas en criterios probabilísticos y evidencia histórica, lo que fortalece la justificación técnica del proceso.

Adicionalmente, el modelo es escalable y adaptable, permitiendo su actualización con nuevos datos y su aplicación en contextos similares. Contribuye también a la reducción de sesgos humanos en la selección de combinaciones, promoviendo decisiones más objetivas y alineadas con comportamientos observados en los datos.

## Arquitectura

La aplicación **ML Predictora de Números de Loterias** está estructurada en cuatro capas principales:

### 1. **Frontend (React)**
- Interfaz de usuario responsable de la selección de loterias
- Visualización de resultados y predicciones
- Comunicación con el backend mediante API REST

### 2. **Backend (Python)**
- **Selector:** Componente que gestiona la selección de loterias y coordina las predicciones
- **Entrenar Modelos:** Módulo responsable del entrenamiento de los modelos de ML con datos históricos
- **Scraper:** Herramienta para la recopilación automática de datos históricos de las loterias

### 3. **ML Layer (Python)**
- Modelos de Machine Learning especializados para cada loteria
- Análisis de series históricas y generación de predicciones
- Implementación de reglas de optimización estadística (balance par/impar, rangos de suma)

### 4. **BD Layer**
- Almacenamiento de datos históricos por loteria (Loteria 1, Loteria 2, ..., Loteria n)
- Gestión de archivos de datos para lectura y entrenamiento

**Flujos principales:**
- **Predicción:** Usuario → Frontend → Selector → Modelos ML → Resultados
- **Entrenamiento:** Scraper → Backend → Entrenar Modelos → ML Layer
- **Datos:** Archivos históricos ← Scraper (actualización automática)

![Arquitectura de la APP](./images/architecture.png)

## Stakeholders

- Lina Paola Soto Montes

## Instalación y ejecución local (Docker)

### Requisitos previos

| Herramienta | Versión mínima | Verificar |
|---|---|---|
| Docker Engine | 24+ | `docker --version` |
| docker-compose | 1.29+ | `docker-compose --version` |
| Git | cualquier | `git --version` |

### Pasos

**1. Clonar el repositorio**

```bash
git clone <url-del-repositorio>
cd proyecto_final
```

**2. Configurar variables de entorno**

```bash
cp .env.example .env
```

El archivo `.env` contiene los valores por defecto para desarrollo local:

```
ENV=development
PORT=9002
DATA_DIR=/code/app/bd/historical
```

> `ENV=development` habilita Swagger UI en `http://localhost:9002/docs`.

**3. Construir y levantar el contenedor**

```bash
docker-compose up -d --build
```

El primer build puede tardar 2–5 minutos mientras descarga la imagen base e instala dependencias ML (pandas, numpy, scikit-learn).

**4. Verificar que la app está corriendo**

```bash
curl http://localhost:9002/health
# Respuesta esperada: {"status":"ok","version":"1.0.0"}
```

También puedes acceder a la documentación interactiva en:
`http://localhost:9002/docs`

**5. Detener el contenedor**

```bash
docker-compose down
```

### Ejecución de tests (fuera de Docker)

Requiere Python 3.11+ y el entorno virtual activado:

```bash
# Crear entorno virtual (primera vez)
python3 -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows

# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Correr todos los tests
pytest

# Solo tests unitarios (rápidos)
pytest -m unit

# Solo tests de integración
pytest -m integration

# Ver cobertura detallada
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## API Reference

Base URL: `http://localhost:9002`

> Todos los endpoints de negocio tienen el prefijo `/api/`. El endpoint `/health` está fuera del prefijo y es utilizado por el healthcheck del contenedor.
> La documentación interactiva (Swagger UI) está disponible en `/docs` cuando `ENV=development`.

### `GET /health`

Verifica que el servicio está activo.

**Respuesta `200 OK`**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

### `GET /api/lotteries`

Retorna la lista de loterias disponibles. El frontend usa este endpoint para construir el selector dinámicamente — nunca tiene la lista hardcodeada.

**Respuesta `200 OK`**
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

| Campo | Tipo | Descripción |
|---|---|---|
| `lotteries` | array | Lista de loterias registradas |
| `lotteries[].id` | string | Identificador interno (usar en `/api/predict` y `/api/train`) |
| `lotteries[].name` | string | Nombre para mostrar en la interfaz |

---

### `POST /api/predict`

Genera una predicción para la loteria indicada. Ejecuta el ciclo completo: carga datos históricos → entrena el modelo → genera predicción.

**Request body**
```json
{
  "lottery": "cundinamarca"
}
```

**Respuesta `200 OK`**
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
    "optimal_sum_range": { "min": 10, "max": 26 },
    "frequency_score": 0.0,
    "pattern_score": 0.0
  },
  "generated_at": "2024-05-27T10:30:00Z"
}
```

> **Nota:** `main_numbers` es un arreglo de **4 dígitos individuales** (miles, centenas, decenas, unidades). Se devuelven separados para preservar los ceros a la izquierda — por ejemplo, el número `0471` se representa como `[0, 4, 7, 1]`, no como el entero `471`.

| Campo | Tipo | Descripción |
|---|---|---|
| `lottery` | string | ID de la loteria (igual al enviado) |
| `prediction.main_numbers` | integer[4] | Los 4 dígitos del número ganador (0–9 cada uno), en orden miles → unidades |
| `prediction.special_number` | integer \| null | Número especial — `null` para Cundinamarca |
| `prediction.serie` | string | Serie predicha, siempre 3 caracteres con cero-padding — ej. `"053"`, `"153"` |
| `statistics.even_count` | integer | Cantidad de dígitos pares entre los 4 principales |
| `statistics.odd_count` | integer | Cantidad de dígitos impares entre los 4 principales |
| `statistics.even_odd_ratio` | string | Relación pares:impares — ej. `"2:2"` |
| `statistics.sum` | integer | Suma de los 4 dígitos (rango 0–36) |
| `statistics.sum_in_optimal_range` | boolean | `true` si la suma está entre 10 y 26 (rango históricamente frecuente) |
| `statistics.optimal_sum_range.min` | integer | Límite inferior del rango óptimo de suma (`10`) |
| `statistics.optimal_sum_range.max` | integer | Límite superior del rango óptimo de suma (`26`) |
| `statistics.frequency_score` | float | Score 0.00–1.00 de frecuencia histórica (en desarrollo) |
| `statistics.pattern_score` | float | Score 0.00–1.00 de coherencia del patrón (en desarrollo) |
| `generated_at` | string | Timestamp ISO 8601 de generación (UTC) |

**Errores**

| Código | Causa |
|---|---|
| `422 Unprocessable Entity` | El campo `lottery` está ausente o no es string |
| `404 Not Found` | La loteria no está registrada |

**Ejemplo error `404`**
```json
{
  "detail": "'invalida': lotería no registrada. Disponibles: ['cundinamarca']"
}
```

---

### `POST /api/train`

Lanza el entrenamiento del modelo en segundo plano. Retorna inmediatamente un `job_id` sin bloquear la respuesta.

**Request body**
```json
{
  "lottery": "cundinamarca"
}
```

**Respuesta `202 Accepted`**
```json
{
  "job_id": "e1e3c00c-febf-469a-b081-c7d2b2270f7c",
  "status": "queued",
  "lottery": "cundinamarca"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `job_id` | string (UUID) | Identificador único del trabajo de entrenamiento |
| `status` | string | Estado inicial: siempre `"queued"` |
| `lottery` | string | Loteria que se está entrenando |

**Errores**

| Código | Causa |
|---|---|
| `422 Unprocessable Entity` | El campo `lottery` está ausente |
| `404 Not Found` | La loteria no está registrada |

---

### `GET /api/train/{job_id}/status`

Consulta el estado de un trabajo de entrenamiento iniciado con `POST /api/train`. El frontend debe hacer polling a este endpoint para saber cuándo terminó.

**Parámetro de ruta**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `job_id` | string (UUID) | Identificador retornado por `POST /api/train` |

**Respuesta `200 OK`**
```json
{
  "job_id": "02e4b831-7aa2-498c-aa3f-96e46c2b9966",
  "status": "completed",
  "lottery": "cundinamarca",
  "error": null
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `job_id` | string | UUID del trabajo |
| `status` | string | Estado actual del entrenamiento |
| `lottery` | string | Loteria que se entrenó |
| `error` | string \| null | Mensaje de error si `status == "failed"`, `null` en caso contrario |

**Valores posibles de `status`**

| Valor | Significado |
|---|---|
| `queued` | El trabajo fue recibido, aún no inició |
| `running` | El entrenamiento está en curso |
| `completed` | El entrenamiento terminó exitosamente |
| `failed` | El entrenamiento falló (ver campo `error`) |

**Flujo recomendado para el frontend**

```
POST /api/train  →  recibe job_id
    ↓
GET /api/train/{job_id}/status  (polling cada 2-3 segundos)
    ↓
status == "completed"  →  mostrar éxito
status == "failed"     →  mostrar error
```

**Errores**

| Código | Causa |
|---|---|
| `404 Not Found` | El `job_id` no existe |

---

## Agregar una nueva lotería

Esta sección documenta el contrato que debe cumplir cualquier desarrollador que quiera integrar una nueva lotería al sistema. El diseño sigue el principio **Open/Closed**: agregar una lotería nueva **no modifica** ningún archivo existente de lógica — solo se crean archivos nuevos y se registra la clase en dos lugares.

### Pasos obligatorios

#### 1. Crear el archivo de datos históricos

Los datos deben estar en formato CSV dentro de la carpeta:

```
app/bd/historical/<id_loteria>/<id_loteria>_historico.csv
```

**Ejemplo para una lotería ficticia `medellin`:**

```
app/bd/historical/medellin/medellin_historico.csv
```

El archivo CSV debe contener al menos las columnas que el modelo va a consumir. Para loterias de número único (como Cundinamarca), la estructura mínima es:

| Columna | Tipo | Descripción |
|---|---|---|
| `Tipo de Premio` | string | Filtro para quedarse solo con `"Mayor"` |
| `Numero billete ganador` | integer | Número ganador del premio mayor |
| `Numero serie ganadora` | integer | Serie ganadora (0–999) |

> Las columnas adicionales son ignoradas por el modelo. Solo se usan las que el modelo explícitamente lee en `load_data()`.

---

#### 2. Implementar el modelo ML

Crear el archivo:

```
app/ml/<id_loteria>/<id_loteria>_ml.py
```

La clase **debe** heredar de `BaseModel` e implementar los tres métodos abstractos:

```python
# app/ml/medellin/medellin_ml.py

import os
import numpy as np
import pandas as pd
from app.ml.base_model import BaseModel

_DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "bd", "historical",
    "medellin", "medellin_historico.csv",
)


class MedellinModel(BaseModel):

    def __init__(self, data_path: str | None = None) -> None:
        self.data_path: str = data_path or os.path.normpath(_DEFAULT_DATA_PATH)
        self.df = None
        # ... atributos del modelo entrenado

    def load_data(self) -> None:
        """Carga y filtra el CSV de datos históricos."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Archivo no encontrado: {self.data_path}")
        df = pd.read_csv(self.data_path)
        self.df = df[df["Tipo de Premio"] == "Mayor"].copy()

    def train(self) -> None:
        """Entrena el modelo con los datos cargados."""
        if self.df is None:
            raise RuntimeError("Debe llamar a load_data() antes de train()")
        # ... lógica de entrenamiento

    def predict(self, seed: int | None = None) -> list[int]:
        """Genera una predicción.

        Returns:
            list[int]: Los valores predichos. El contrato de retorno depende
            del tipo de lotería (ver tabla de contratos más abajo).
        """
        if self.df is None:
            raise RuntimeError("Debe llamar a train() antes de predict()")
        # ... lógica de predicción
        return [...]
```

**Contrato del método `predict()`:**

El valor de retorno varía según el tipo de lotería. La API en `main.py` construye la respuesta a partir de esta lista:

| Tipo de lotería | Ejemplo | Retorno esperado de `predict()` |
|---|---|---|
| Número de 4 cifras + serie | Cundinamarca | `[miles, centenas, decenas, unidades, serie]` — 5 enteros |
| Números de bolillas (sin especial) | Bogotá | `[n1, n2, n3, n4, n5]` — lista de enteros en el rango de la lotería |
| Números de bolillas (con especial) | Baloto | `[n1, n2, n3, n4, n5, especial]` — el último es el número especial |

> **Regla de oro:** Los ceros a la izquierda **nunca** se combinan en un entero. Para Cundinamarca, el número `0471` se retorna como `[0, 4, 7, 1]`, no como `471`. La API aplica el formato final (zero-padding, strings) antes de enviar al frontend.

---

#### 3. Registrar la clase en el REGISTRY

Abrir `app/backend/selector.py` y añadir la nueva lotería:

```python
# app/backend/selector.py

from app.ml.base_model import BaseModel
from app.ml.cundinamarca.cundinamarca_ml import CundinamarcaModel
from app.ml.medellin.medellin_ml import MedellinModel          # ← nueva línea

REGISTRY: dict[str, type[BaseModel]] = {
    "cundinamarca": CundinamarcaModel,
    "medellin":     MedellinModel,                             # ← nueva línea
}
```

> El `id` usado como clave del diccionario (`"medellin"`) es el mismo que el frontend enviará en el campo `lottery` de cada request. Debe ser un slug en minúsculas sin espacios ni tildes.

---

#### 4. Registrar el nombre para mostrar

Abrir `app/main.py` y añadir el nombre legible al diccionario de display names:

```python
_LOTTERY_DISPLAY_NAMES: dict[str, str] = {
    "cundinamarca": "Lotería de Cundinamarca",
    "medellin":     "Lotería de Medellín",    # ← nueva línea
}
```

> Si el `id` no está en este diccionario, el endpoint `GET /api/lotteries` mostrará el id capitalizado como nombre. Siempre es preferible registrarlo explícitamente.

---

### Verificación

Después de los cuatro pasos, verificar que todo funciona:

```bash
# 1. La lotería aparece en el listado
curl http://localhost:9002/api/lotteries

# 2. La predicción responde correctamente
curl -X POST http://localhost:9002/api/predict \
  -H "Content-Type: application/json" \
  -d '{"lottery": "medellin"}'

# 3. Los tests pasan
pytest -m unit
pytest -m integration
```

---

### Checklist de nueva lotería

- [ ] CSV en `app/bd/historical/<id>/<id>_historico.csv`
- [ ] Clase en `app/ml/<id>/<id>_ml.py` que hereda `BaseModel`
- [ ] Métodos `load_data()`, `train()`, `predict()` implementados
- [ ] `predict()` retorna lista de enteros según el contrato del tipo de lotería
- [ ] Clase registrada en `REGISTRY` de `app/backend/selector.py`
- [ ] Nombre de display registrado en `_LOTTERY_DISPLAY_NAMES` de `app/main.py`
- [ ] Tests unitarios escritos para la nueva clase (mínimo: `load_data`, `train`, `predict`)
- [ ] `pytest` pasa al 100% sin errores

---

## Referencias

- [Definición del Proyecto en Miro](https://miro.com/app/board/uXjVHec2Ol0=/?moveToWidget=3458764668982159419&cot=14)