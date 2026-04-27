"""Expone el endpoint que lista las loterías disponibles en la API."""

from fastapi import APIRouter

from app.backend.selector import list_lotteries
from app.config import LOTTERY_DISPLAY_NAMES

router = APIRouter(prefix="/api")


@router.get("/lotteries")
def lotteries() -> dict:
    """
    Lista las loterías disponibles para predicción y entrenamiento.

    Returns:
        Diccionario con los slugs internos y nombres legibles registrados.
    """
    items = [
        {
            "id": key,
            "name": LOTTERY_DISPLAY_NAMES.get(key, key.capitalize()),
        }
        for key in list_lotteries()
    ]
    return {"lotteries": items}
