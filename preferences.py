"""
preferences.py — Preferencias locales persistentes (sede seleccionada, etc.)
Se guarda en app_preferences.json junto al ejecutable.
"""

import json
from pathlib import Path

_PREFS_FILE = Path(__file__).parent / "app_preferences.json"
_DEFAULT_SEDE = "Prisma"


def get_sede() -> str:
    """Retorna la sede guardada, o 'Prisma' si no hay preferencia."""
    try:
        if _PREFS_FILE.exists():
            data = json.loads(_PREFS_FILE.read_text(encoding="utf-8"))
            return data.get("sede", _DEFAULT_SEDE)
    except Exception:
        pass
    return _DEFAULT_SEDE


def set_sede(sede: str) -> None:
    """Guarda la sede seleccionada en disco."""
    try:
        data: dict = {}
        if _PREFS_FILE.exists():
            try:
                data = json.loads(_PREFS_FILE.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        data["sede"] = sede
        _PREFS_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
