"""
preferences.py — Preferencias locales persistentes (sede seleccionada, etc.)
Se guarda en app_preferences.json junto al ejecutable.
"""

import json
from pathlib import Path

_PREFS_FILE = Path(__file__).parent / "app_preferences.json"
_DEFAULT_CASA = ""   # Sin casa → el usuario debe elegir al iniciar


def get_casa() -> str:
    """Retorna la casa guardada, o 'Prisma' si no hay preferencia."""
    try:
        if _PREFS_FILE.exists():
            data = json.loads(_PREFS_FILE.read_text(encoding="utf-8"))
            return data.get("sede", _DEFAULT_CASA)
    except Exception:
        pass
    return _DEFAULT_CASA


def limpiar() -> None:
    """Elimina el archivo de preferencias (al cerrar sesión)."""
    try:
        if _PREFS_FILE.exists():
            _PREFS_FILE.unlink()
    except Exception:
        pass


def set_casa(casa: str) -> None:
    """Guarda la casa seleccionada en disco."""
    try:
        data: dict = {}
        if _PREFS_FILE.exists():
            try:
                data = json.loads(_PREFS_FILE.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        data["sede"] = casa
        _PREFS_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
