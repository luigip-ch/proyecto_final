"""Expone el endpoint de salud usado para verificar el estado del servicio."""

from fastapi import APIRouter

from app.config import APP_VERSION

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """
    Reporta el estado básico del servicio.

    Returns:
        Diccionario con estado operativo y versión de la aplicación.
    """
    return {"status": "ok", "version": APP_VERSION}
