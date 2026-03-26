"""
config.py
Responsabilidad única: leer el archivo .env y exponer las variables
de entorno como constantes tipadas. Ningún otro módulo debe llamar
a os.getenv() directamente.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Busca el .env en el mismo directorio que este archivo
load_dotenv(Path(__file__).parent / ".env")


def _require(key: str) -> str:
    """Obtiene una variable de entorno o lanza un error claro si no existe."""
    value = os.getenv(key, "").strip()
    if not value:
        raise EnvironmentError(
            f"'{key}' no está definida en el archivo .env\n"
            f"Asegúrate de que el archivo .env existe junto a config.py."
        )
    return value


# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL: str = _require("SUPABASE_URL")
SUPABASE_KEY: str = _require("SUPABASE_KEY")

# ── UI / App ──────────────────────────────────────────────────────────────────
APP_TITLE:        str = "Códigos de Producto"
WINDOW_WIDTH:     int = 390   # Simula Pixel 7 en desarrollo escritorio
WINDOW_HEIGHT:    int = 844
COLOR_SEED:       str = "blue"