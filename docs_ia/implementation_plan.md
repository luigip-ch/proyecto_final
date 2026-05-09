# Implementación de Modelo de ML para Baloto

Este plan detalla los pasos para agregar el modelo de entrenamiento para la lotería Baloto siguiendo estrictamente lo descrito en `api-spec.md` y `README.md`.

## Proposed Changes

### Model Layer (app/ml/baloto)

#### [NEW] [baloto_ml.py](file:///c:/_04_proyecto_baloto/proyecto_final/app/ml/baloto/baloto_ml.py)
Se creará la clase `BalotoModel` que hereda de `BaseModel` y se encarga del análisis de los datos históricos de Baloto.
- **`load_data()`**: Cargará `app/bd/historical/baloto/baloto_historico.csv`. A diferencia de otras loterías, este CSV no contiene la columna `Tipo de Premio`, sino directamente `fecha, n1, n2, n3, n4, n5, superbalota`.
- **`train()`**: Consolidará las apariciones de los números `n1` a `n5` para crear una distribución de probabilidad empírica de las 43 balotas principales. También creará una distribución independiente para la `superbalota` (1 a 16).
- **`predict(seed)`**: Muestreará 5 balotas principales sin reemplazo basándose en la probabilidad histórica y 1 superbalota basándose en su respectiva probabilidad. Retornará el arreglo `[n1, n2, n3, n4, n5, superbalota]` tal como lo requiere el contrato de `api-spec.md`.

### Configuración y Registro (app/config)

#### [MODIFY] [__init__.py](file:///c:/_04_proyecto_baloto/proyecto_final/app/config/__init__.py)
- Añadir `"baloto": "Baloto"` al diccionario `LOTTERY_DISPLAY_NAMES`. (Nota: `LOTTERY_PREDICTION_FORMATS` ya cuenta con la configuración para Baloto).

#### [MODIFY] [registry.py](file:///c:/_04_proyecto_baloto/proyecto_final/app/config/registry.py)
- Importar `BalotoModel`.
- Registrar la clase en el diccionario `REGISTRY` usando la clave `"baloto"`.

### Tests Layer (tests)

#### [NEW] [test_baloto_ml.py](file:///c:/_04_proyecto_baloto/proyecto_final/tests/unit/test_baloto_ml.py)
Creación de pruebas unitarias para asegurar que:
- Se puedan cargar los datos y se lance `FileNotFoundError` si la ruta es inválida.
- El modelo se entrene y cree las frecuencias correctamente.
- La predicción devuelva siempre una lista de 6 enteros únicos para los primeros 5 y un sexto valor correspondiente a la superbalota.

## Verification Plan

### Automated Tests
Ejecutaré los comandos de pytest definidos en el README:
- `pytest -m unit` (para verificar que las pruebas del modelo de baloto pasen exitosamente y verificar la integridad de las pruebas anteriores).

### Manual Verification
- Validaré que el endpoint liste la lotería de baloto adecuadamente si está corriendo el servicio (aunque nos enfocamos en el código del modelo).

### comentar
