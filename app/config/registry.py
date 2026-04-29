"""
Registro centralizado de modelos ML disponibles.

Separado de __init__.py para evitar importaciones circulares:
  - __init__.py  → solo constantes primitivas, sin imports de clases ML
  - los modelos ML importan desde __init__.py
  - registry.py importa los modelos sin crear ciclos

Al agregar una nueva lotería:
  1. Importar la nueva clase de modelo aquí.
  2. Añadir una entrada al diccionario REGISTRY.
  3. Añadir el nombre display en LOTTERY_DISPLAY_NAMES de __init__.py.
  El slug (clave) debe ser idéntico en ambos lugares.
"""

from app.ml.base_model import BaseModel
from app.ml.cundinamarca.cundinamarca_ml import CundinamarcaModel
from app.ml.cruz_roja.cruz_roja_ml import CruzRojaModel

REGISTRY: dict[str, type[BaseModel]] = {
    "cundinamarca": CundinamarcaModel,
    "cruz_roja": CruzRojaModel,
}
