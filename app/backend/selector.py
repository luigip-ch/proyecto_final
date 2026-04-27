"""Selecciona modelos de lotería desde el registro central de la aplicación."""

from app.ml.base_model import BaseModel
from app.config.registry import REGISTRY


def list_lotteries() -> list[str]:
    """Devuelve los slugs de loterías registradas en la aplicación."""
    return list(REGISTRY.keys())


def get_model(lottery: str) -> BaseModel:
    """
    Instancia el modelo asociado a una lotería registrada.

    Args:
        lottery: Slug interno de la lotería solicitada.

    Returns:
        Instancia concreta que implementa ``BaseModel``.

    Raises:
        ValueError: si ``lottery`` no existe en el registro central.
    """
    cls = REGISTRY.get(lottery)
    if cls is None:
        raise ValueError(
            f"'{lottery}': lotería no registrada. "
            f"Disponibles: {list_lotteries()}"
        )
    return cls()
