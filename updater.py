# -*- coding: utf-8 -*-
"""
updater.py — Gestión de actualizaciones de la app vía GitHub Releases / Supabase.

El script externo de distribución sube el APK y actualiza app_config en Supabase.
Esta clase solo lee esa tabla y reacciona.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Callable


class AppUpdater:
    """
    Detecta, descarga e instala actualizaciones de la app.
    Todos los métodos son estáticos — no requiere instancia.
    """

    # Única fuente de verdad de la versión instalada
    APP_VERSION = "1.1.0"

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
            apk_url        str   — URL directa de descarga del APK
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
        """Persiste las novedades antes de abrir el instalador, para mostrarlas al reiniciar."""
        estado = AppUpdater._leer_estado()
        estado["pending_release_notes"] = notes
        AppUpdater._guardar_estado(estado)

    @staticmethod
    def clear_pending_release_notes() -> None:
        """Elimina las novedades pendientes después de haberlas mostrado al usuario."""
        estado = AppUpdater._leer_estado()
        estado.pop("pending_release_notes", None)
        AppUpdater._guardar_estado(estado)

    # ── Descarga interrumpida (reanudación automática) ────────────────────────

    @staticmethod
    def save_pending_download(url: str, release_notes: str, latest_version: str) -> None:
        """
        Persiste los parámetros de la descarga en curso ANTES de arrancar el hilo.
        Si el proceso muere (usuario cierra la app), al reabrir se detecta esta
        entrada y la descarga se reanuda automáticamente sin preguntarle al usuario.
        """
        estado = AppUpdater._leer_estado()
        estado["pending_download"] = {
            "url":            url,
            "release_notes":  release_notes,
            "latest_version": latest_version,
        }
        AppUpdater._guardar_estado(estado)

    @staticmethod
    def get_pending_download() -> dict:
        """
        Retorna los parámetros de una descarga interrumpida, o dict vacío si no hay ninguna.
        """
        return AppUpdater._leer_estado().get("pending_download", {})

    @staticmethod
    def clear_pending_download() -> None:
        """Elimina la descarga pendiente al completarse o al fallar definitivamente."""
        estado = AppUpdater._leer_estado()
        estado.pop("pending_download", None)
        AppUpdater._guardar_estado(estado)

    # ── Descarga e instalación ────────────────────────────────────────────────

    @staticmethod
    def _resolver_url_descarga(url: str, token: str) -> str:
        """
        Para repos privados, la URL pública de GitHub Releases devuelve 404
        aunque el token sea válido, porque GitHub requiere usar la API REST
        para obtener la URL real del asset (distinta de browser_download_url).

        Extrae owner/repo de la URL, consulta la API con el tag 'latest' y
        retorna la URL de la API del primer asset .apk encontrado.
        Si falla por cualquier razón, retorna la url original sin modificar.
        """
        import re
        import httpx

        match = re.search(r"github\.com/([^/]+/[^/]+)/releases", url)
        if not match:
            return url

        repo    = match.group(1)
        api_url = f"https://api.github.com/repos/{repo}/releases/tags/latest"

        try:
            with httpx.Client(timeout=30.0) as cliente:
                resp = cliente.get(
                    api_url,
                    headers={
                        "Authorization": f"token {token}",
                        "Accept":        "application/vnd.github+json",
                    },
                )
                resp.raise_for_status()
                for asset in resp.json().get("assets", []):
                    if asset.get("name", "").endswith(".apk"):
                        # Retornar la URL de la API (no browser_download_url),
                        # que es la que acepta el header Accept: application/octet-stream
                        return asset["url"]
        except Exception:
            pass

        return url

    @staticmethod
    def download_apk(
        url: str,
        on_progress: Callable[[float], None],
        destino: Path,
    ) -> Path:
        """
        Descarga el APK en streaming con chunks de 1 MB.

        Para repos privados: lee github_download_token de app_config, resuelve
        la URL real del asset vía API de GitHub y descarga con el header
        Accept: application/octet-stream requerido por esa URL.
        Para repos públicos (sin token): descarga directamente siguiendo redirects.

        Reporta progreso de 0.0 a 1.0 vía on_progress.
        Elimina el archivo parcial si ocurre algún error.
        """
        import httpx

        destino = Path(destino)

        # Leer token desde app_config (vacío si no está configurado)
        config = AppUpdater.fetch_config()
        token  = config.get("github_download_token", "").strip()

        headers = {}
        if token:
            headers["Authorization"] = f"token {token}"
            # La URL de la API de assets requiere este header para devolver el binario
            headers["Accept"] = "application/octet-stream"
            url = AppUpdater._resolver_url_descarga(url, token)
        else:
            headers["Accept"] = "application/vnd.github+json"

        try:
            with httpx.Client(
                follow_redirects=True,
                timeout=httpx.Timeout(600.0),
            ) as cliente:
                with cliente.stream("GET", url, headers=headers) as resp:
                    resp.raise_for_status()
                    total      = int(resp.headers.get("content-length") or 0)
                    descargado = 0
                    tam_chunk  = 1024 * 1024  # 1 MB

                    with open(destino, "wb") as f:
                        for bloque in resp.iter_bytes(chunk_size=tam_chunk):
                            if not bloque:
                                continue
                            f.write(bloque)
                            descargado += len(bloque)
                            if total > 0:
                                try:
                                    on_progress(min(descargado / total, 1.0))
                                except Exception:
                                    pass

            try:
                on_progress(1.0)
            except Exception:
                pass
            return destino

        except Exception:
            try:
                destino.unlink(missing_ok=True)
            except Exception:
                pass
            raise

    @staticmethod
    def _es_android() -> bool:
        """
        Detecta si la app corre en Android.
        sys.platform devuelve 'linux' en Android (kernel Linux), por eso se
        comprueba la variable de entorno ANDROID_ROOT que solo existe en ese SO.
        """
        import os
        return bool(os.environ.get("ANDROID_ROOT"))

    @staticmethod
    def open_installer(apk_path: Path) -> None:
        """
        Abre el instalador del sistema operativo para instalar el APK.
        Soporta Android y Windows. En otros SO registra en el log.
        """
        apk_path = Path(apk_path)

        try:
            if AppUpdater._es_android():
                subprocess.Popen(
                    [
                        "am", "start",
                        "-a", "android.intent.action.VIEW",
                        "-d", f"file://{apk_path}",
                        "-t", "application/vnd.android.package-archive",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif sys.platform == "win32":
                import os
                os.startfile(str(apk_path))
            else:
                print(
                    f"[updater] Plataforma '{sys.platform}' no soportada para "
                    f"instalación automática. APK en: {apk_path}"
                )
        except Exception as e:
            print(f"[updater] Error al abrir el instalador: {e}")