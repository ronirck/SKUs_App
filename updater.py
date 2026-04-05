# -*- coding: utf-8 -*-
"""
updater.py — Gestión de actualizaciones de la app vía Supabase app_config.

El script externo de distribución sube el APK a un repositorio público y
actualiza app_config en Supabase. Esta clase solo lee esa tabla y reacciona.
La descarga e instalación se delegan al navegador del sistema operativo.
"""

import json
from pathlib import Path


class AppUpdater:
    """
    Detecta e instala actualizaciones de la app.
    Todos los métodos son estáticos — no requiere instancia.
    """

    # Única fuente de verdad de la versión instalada
    APP_VERSION = "1.2.0"

    # Estado local: data_version y novedades pendientes de mostrar
    _ESTADO_FILE = Path(__file__).parent / "update_state.json"

    # ── Estado local ──────────────────────────────────────────────────────────

    @staticmethod
    def _leer_estado() -> dict:
        """Lee update_state.json. Retorna dict vacío si no existe o está corrupto."""
        try:
            f = AppUpdater._ESTADO_FILE
            if f.exists():
                return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    @staticmethod
    def _guardar_estado(estado: dict) -> None:
        """Persiste el estado en update_state.json."""
        try:
            AppUpdater._ESTADO_FILE.write_text(
                json.dumps(estado, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass

    # ── Configuración remota ──────────────────────────────────────────────────

    @staticmethod
    def fetch_config() -> dict:
        """
        Consulta la tabla app_config en Supabase.
        Retorna {clave: valor} o dict vacío si falla (sin internet).
        """
        try:
            import database
            filas = (
                database.get_client()
                .table("app_config")
                .select("clave, valor")
                .execute()
                .data
            )
            return {f["clave"]: f["valor"] for f in filas}
        except Exception:
            return {}

    # ── Versión de la app ─────────────────────────────────────────────────────

    @staticmethod
    def _parsear_version(v: str) -> tuple:
        """Convierte '1.2.3' en (1, 2, 3) para comparación semántica."""
        try:
            return tuple(int(x) for x in str(v).strip().split("."))
        except Exception:
            return (0,)

    @staticmethod
    def check_app_update() -> dict:
        """
        Compara APP_VERSION con la configuración remota.
        Retorna dict con:
            needs_update   bool  — hay versión más reciente disponible
            force          bool  — actualización obligatoria (bloquea la app)
            maintenance    bool  — app en mantenimiento
            latest_version str   — última versión en el servidor
            apk_url        str   — URL pública de descarga del APK
            message        str   — mensaje para el usuario
            release_notes  str   — novedades de la versión (una por línea)
        """
        resultado = {
            "needs_update":   False,
            "force":          False,
            "maintenance":    False,
            "latest_version": AppUpdater.APP_VERSION,
            "apk_url":        "",
            "message":        "",
            "release_notes":  "",
        }

        config = AppUpdater.fetch_config()
        if not config:
            return resultado

        # Mantenimiento tiene precedencia sobre todo lo demás
        if config.get("maintenance_mode") == "true":
            resultado["maintenance"] = True
            resultado["message"]     = config.get("update_message", "")
            return resultado

        resultado["apk_url"]       = config.get("apk_url", "")
        resultado["message"]       = config.get("update_message", "")
        resultado["release_notes"] = config.get("release_notes", "")

        latest = config.get("latest_app_version", AppUpdater.APP_VERSION)
        resultado["latest_version"] = latest

        actual  = AppUpdater._parsear_version(AppUpdater.APP_VERSION)
        mas_rec = AppUpdater._parsear_version(latest)
        minima  = AppUpdater._parsear_version(
            config.get("min_app_version", AppUpdater.APP_VERSION)
        )

        if actual < mas_rec:
            resultado["needs_update"] = True
        if actual < minima or config.get("force_update") == "true":
            resultado["force"] = True

        return resultado

    # ── Versión de datos del catálogo ─────────────────────────────────────────

    @staticmethod
    def check_data_version() -> bool:
        """
        Compara data_version remota vs local (guardada en update_state.json).
        Si la remota es mayor: persiste la nueva versión y retorna True.
        Retorna False si fetch_config() falla o las versiones coinciden.
        """
        config = AppUpdater.fetch_config()
        if not config:
            return False

        try:
            remota = int(config.get("data_version", 0))
        except (ValueError, TypeError):
            return False

        estado = AppUpdater._leer_estado()
        try:
            local = int(estado.get("data_version", 0))
        except (ValueError, TypeError):
            local = 0

        if remota > local:
            estado["data_version"] = remota
            AppUpdater._guardar_estado(estado)
            return True
        return False

    @staticmethod
    def save_data_version(v: int) -> None:
        """Persiste la data_version en update_state.json."""
        estado = AppUpdater._leer_estado()
        estado["data_version"] = v
        AppUpdater._guardar_estado(estado)

    # ── Novedades pendientes ──────────────────────────────────────────────────

    @staticmethod
    def get_pending_release_notes() -> str:
        """
        Lee novedades pendientes de update_state.json.
        Retorna cadena vacía si no hay nada pendiente.
        """
        return AppUpdater._leer_estado().get("pending_release_notes", "")

    @staticmethod
    def save_pending_release_notes(notes: str) -> None:
        """Persiste las novedades para mostrarlas al reiniciar."""
        estado = AppUpdater._leer_estado()
        estado["pending_release_notes"] = notes
        AppUpdater._guardar_estado(estado)

    @staticmethod
    def clear_pending_release_notes() -> None:
        """Elimina las novedades pendientes después de haberlas mostrado."""
        estado = AppUpdater._leer_estado()
        estado.pop("pending_release_notes", None)
        AppUpdater._guardar_estado(estado)

