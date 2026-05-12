# Implementación de Modelo de ML para Baloto

De acuerdo con el plan de implementación y siguiendo las directrices de `README.md` y `api-spec.md`, se ha integrado exitosamente la Lotería de Baloto al sistema de Machine Learning.

## Resumen de Cambios

### 1. Implementación del Modelo `BalotoModel`
Se creó la clase predictora del modelo específico en [baloto_ml.py](file:///c:/_04_proyecto_baloto/proyecto_final/app/ml/baloto/baloto_ml.py).

> [!NOTE]
> - **Carga de Datos:** Se lee del histórico el CSV existente sin la restricción de tipo de premio "Mayor", ya que Baloto no posee esa categoría y todos los registros son relevantes.
> - **Entrenamiento:** Se unifican todas las posiciones de las balotas principales para generar una única distribución estadística para los números del 1 al 43 y una distinta para la superbalota.
> - **Predicción:** Se aseguran 5 números irrepetibles (muestreo sin reemplazo) además de la superbalota. Esto devuelve un arreglo `[n1, n2, n3, n4, n5, superbalota]` que respeta la configuración establecida en los formatos de API de la documentación.

### 2. Configuración y Registro
Para que el modelo se conecte a la API, la lotería se agregó a las dependencias de inicialización:
- En [registry.py](file:///c:/_04_proyecto_baloto/proyecto_final/app/config/registry.py), se registró el modelo asociándolo al ID `baloto`.
- En [__init__.py](file:///c:/_04_proyecto_baloto/proyecto_final/app/config/__init__.py), se definió su display string `Baloto`.

### 3. Pruebas Unitarias
Se crearon pruebas unitarias completas en [test_baloto_ml.py](file:///c:/_04_proyecto_baloto/proyecto_final/tests/unit/test_baloto_ml.py) para validar:
- La carga correcta y estructura de las frecuencias de entrenamiento.
- La validez de las predicciones, asegurando siempre arreglos de tamaño 6, que las balotas principales no se repitan y estén ordenadas.
- La determinismo mediante el uso de la semilla.

## Validación

Se ejecutó la suite de `pytest` sobre el nuevo test de baloto y todas las pruebas **pasaron exitosamente**:
```
tests\unit\test_baloto_ml.py ............ [100%]
================= 12 passed ====================
```

El modelo de baloto ya está completamente disponible para su uso por parte del sistema.
