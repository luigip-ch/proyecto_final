"""
Configuración centralizada de la aplicación.

Toda constante de entorno, ruta, regla de negocio o parámetro estadístico
debe definirse aquí. Los módulos importan desde este archivo — nunca definen
sus propios magic numbers o strings hardcodeados.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ── Entorno ───────────────────────────────────────────────────────────────────

ENV: str = os.getenv("ENV", "production")
APP_VERSION: str = "1.0.0"
PORT: int = int(os.getenv("PORT", "9002"))

# ── Paths ─────────────────────────────────────────────────────────────────────

# Directorio raíz de datos históricos.
BASE_DATA_DIR: str = os.path.normpath(
    os.getenv(
        "DATA_DIR",
        os.path.join(os.path.dirname(__file__), "..", "bd", "historical"),
    )
)

# Directorio donde se persisten modelos entrenados.
MODEL_STORE_DIR: str = os.path.normpath(
    os.getenv(
        "MODEL_STORE_DIR",
        os.path.join(os.path.dirname(__file__), "..", "bd", "models"),
    )
)

# ── Reglas de negocio ─────────────────────────────────────────────────────────

# Valor del campo "Tipo de Premio" que identifica el premio mayor en los CSVs.
PRIZE_TYPE_FILTER: str = "Mayor"

# Cantidad de dígitos con los que se representa la serie (zero-padding).
SERIE_PADDING: int = 3

# Rango óptimo empírico de la suma de los 4 dígitos del número ganador (0–36).
# Basado en análisis histórico: las sumas más frecuentes caen en este rango.
OPTIMAL_SUM_MIN: int = 10
OPTIMAL_SUM_MAX: int = 26

# ── Loterias ──────────────────────────────────────────────────────────────────

# Nombres legibles para mostrar en el frontend.
# Clave: slug interno (igual al usado en el REGISTRY y en los requests).
# Al agregar una nueva lotería, añadir la entrada aquí además del REGISTRY.
LOTTERY_DISPLAY_NAMES: dict[str, str] = {
    "cundinamarca": "Lotería de Cundinamarca",
}
