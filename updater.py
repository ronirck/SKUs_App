"""
updater.py — Sistema de auto-actualización de la app.

Verifica la tabla `app_config` en Supabase al arrancar y actúa según el resultado:
  - maintenance_mode  → pantalla bloqueante de mantenimiento
  - force_update      → diálogo modal con barra de progreso de descarga
  - nueva versión     → banner ignorable con botón "Actualizar"
  - data_version      → invalida caché de productos si los datos cambiaron

Uso desde main.py:
    import updater
    updater.AppUpdater(page).verificar()
"""

import json
import os
import platform
import subprocess
import threading
import urllib.request
from pathlib import Path
from typing import Optional

import flet as ft

import database

# ── Versión actual del binario (actualizar antes de cada build) ───────────────
APP_VERSION = "1.1.0"

# ── Archivo de estado local ───────────────────────────────────────────────────
_UPDATE_STATE_FILE = Path(__file__).parent / "update_state.json"


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS DE ESTADO LOCAL
# ══════════════════════════════════════════════════════════════════════════════

def leer_estado_local() -> dict:
    """Lee el archivo update_state.json. Retorna dict vacío si no existe o está corrupto."""
    try:
        if _UPDATE_STATE_FILE.exists():
            return json.loads(_UPDATE_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def guardar_estado_local(estado: dict) -> None:
    """Persiste el estado de actualización en update_state.json."""
    try:
        _UPDATE_STATE_FILE.write_text(
            json.dumps(estado, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ══════════════════════════════════════════════════════════════════════════════

def comparar_versiones(v1: str, v2: str) -> int:
    """
    Compara dos versiones semánticas (ej: "1.2.3").
    Retorna -1 si v1 < v2, 0 si son iguales, 1 si v1 > v2.
    """
    def parsear(v: str) -> tuple:
        try:
            return tuple(int(x) for x in str(v).strip().split("."))
        except Exception:
            return (0,)
    t1, t2 = parsear(v1), parsear(v2)
    if t1 < t2:
        return -1
    if t1 > t2:
        return 1
    return 0


def _url_descarga(config: dict, page: ft.Page) -> Optional[str]:
    """Retorna la URL de descarga adecuada según la plataforma."""
    try:
        plataforma = page.platform
        if plataforma in (ft.PagePlatform.ANDROID,):
            return config.get("apk_url")
    except Exception:
        pass
    # Fallback por plataforma del SO
    if platform.system().lower() == "windows":
        return config.get("win_url")
    return config.get("apk_url")


def _es_verdadero(valor) -> bool:
    """Normaliza valores booleanos que vienen de Supabase como string o bool."""
    return valor in (True, "true", "True", "1", 1)


# ══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class AppUpdater:
    """
    Verifica app_config en Supabase y gestiona actualizaciones de datos y binario.
    Toda la lógica de red corre en un hilo secundario; los cambios de UI
    se aplican llamando page.update() desde ese hilo.
    """

    def __init__(self, page: ft.Page) -> None:
        self.page = page

    def verificar(self) -> None:
        """Lanza la verificación en un hilo secundario (no bloqueante)."""
        threading.Thread(target=self._run, daemon=True).start()

    # ── Lógica principal ──────────────────────────────────────────────────────

    def _run(self) -> None:
        """Se ejecuta en hilo secundario. Consulta app_config y decide qué hacer."""
        try:
            config = database.fetch_app_config()
            if not config:
                return

            # 1. Modo mantenimiento — bloquea todo
            if _es_verdadero(config.get("maintenance_mode")):
                self._mostrar_mantenimiento(config.get("update_message", ""))
                return

            # 2. Verificar si los datos cambiaron
            self._verificar_datos(config)

            # 3. Verificar versión del binario
            self._verificar_binario(config)

        except Exception:
            pass  # Sin internet u otro error: la app sigue funcionando normalmente

    def _verificar_datos(self, config: dict) -> None:
        """
        Compara data_version remota con la guardada localmente.
        Si cambió, invalida el caché de productos y actualiza el estado local.
        """
        data_version_remota = config.get("data_version")
        if not data_version_remota:
            return

        estado = leer_estado_local()
        data_version_local = estado.get("data_version")

        if data_version_local != str(data_version_remota):
            database.invalidar_cache_productos()
            estado["data_version"] = str(data_version_remota)
            guardar_estado_local(estado)

    def _verificar_binario(self, config: dict) -> None:
        """
        Compara APP_VERSION con latest_app_version y min_app_version.
        Muestra diálogo forzado, banner ignorable o nada según corresponda.
        """
        latest  = config.get("latest_app_version")
        min_ver = config.get("min_app_version")
        mensaje = config.get("update_message") or "Hay una nueva versión disponible."
        forzar  = _es_verdadero(config.get("force_update"))

        if not latest:
            return  # Sin info de versión → nada que hacer

        if comparar_versiones(APP_VERSION, latest) >= 0:
            return  # Ya tenemos la versión más reciente

        # Versión desactualizada: ¿forzar o sugerir?
        debe_forzar = forzar or (
            min_ver and comparar_versiones(APP_VERSION, min_ver) < 0
        )

        url = _url_descarga(config, self.page)

        if debe_forzar:
            self._mostrar_dialogo_forzado(latest, mensaje, url)
        else:
            self._mostrar_banner(latest, mensaje, url)

    # ── Pantalla de mantenimiento ─────────────────────────────────────────────

    def _mostrar_mantenimiento(self, mensaje: str) -> None:
        """Reemplaza toda la vista con una pantalla de mantenimiento bloqueante."""
        pantalla = ft.View(
            route="/mantenimiento",
            bgcolor=ft.Colors.SURFACE,
            controls=[
                ft.Container(
                    expand=True,
                    alignment=ft.alignment.Alignment(0, 0),
                    padding=ft.Padding(32, 0, 32, 0),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=24,
                        controls=[
                            ft.Icon(ft.Icons.BUILD_CIRCLE_OUTLINED,
                                    size=80, color=ft.Colors.ORANGE_700),
                            ft.Text("En mantenimiento", size=26,
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER),
                            ft.Text(
                                mensaje or (
                                    "Estamos mejorando la app.\n"
                                    "Vuelve en unos minutos."
                                ),
                                size=14, color=ft.Colors.SECONDARY,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                    ),
                )
            ],
        )
        self.page.views.clear()
        self.page.views.append(pantalla)
        self.page.update()

    # ── Diálogo de actualización forzada ──────────────────────────────────────

    def _mostrar_dialogo_forzado(self, version: str, mensaje: str,
                                  url: Optional[str]) -> None:
        """
        Diálogo modal bloqueante. El usuario no puede cerrarlo.
        Muestra barra de progreso durante la descarga.
        """
        barra   = ft.ProgressBar(value=0, width=260,
                                  color=ft.Colors.BLUE,
                                  bgcolor=ft.Colors.BLUE_50)
        txt_est = ft.Text("", size=12, color=ft.Colors.SECONDARY,
                          text_align=ft.TextAlign.CENTER)
        btn_act = ft.Button(
            f"Actualizar a v{version}",
            icon=ft.Icons.DOWNLOAD,
            expand=True,
        )

        cuerpo = ft.Column(tight=True, spacing=12, controls=[
            ft.Text(mensaje, size=13, color=ft.Colors.ON_SURFACE,
                    text_align=ft.TextAlign.CENTER),
        ])

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Row(spacing=8, controls=[
                ft.Icon(ft.Icons.SYSTEM_UPDATE, color=ft.Colors.BLUE, size=22),
                ft.Text(f"Actualización requerida  v{version}",
                        weight=ft.FontWeight.BOLD, size=15),
            ]),
            content=cuerpo,
            actions=[btn_act],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )

        def iniciar_descarga(_):
            if not url:
                cuerpo.controls = [
                    ft.Text("No hay enlace de descarga para esta plataforma.",
                            color=ft.Colors.RED, text_align=ft.TextAlign.CENTER),
                ]
                self.page.update()
                return

            btn_act.disabled = True
            cuerpo.controls = [
                ft.Text(f"Descargando v{version}...", size=13),
                barra,
                txt_est,
            ]
            self.page.update()

            threading.Thread(
                target=self._descargar,
                args=(url, barra, txt_est, dialogo),
                daemon=True,
            ).start()

        btn_act.on_click = iniciar_descarga

        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()

    # ── Banner ignorable ──────────────────────────────────────────────────────

    def _mostrar_banner(self, version: str, mensaje: str,
                         url: Optional[str]) -> None:
        """Banner no bloqueante en la parte superior con botones 'Actualizar' e 'Ignorar'."""

        def al_actualizar(_):
            banner.open = False
            self.page.update()
            if url:
                self._mostrar_dialogo_forzado(version, mensaje, url)

        def al_ignorar(_):
            banner.open = False
            self.page.update()

        banner = ft.Banner(
            bgcolor=ft.Colors.BLUE_50,
            leading=ft.Icon(ft.Icons.UPDATE, color=ft.Colors.BLUE, size=28),
            content=ft.Text(
                f"v{version} disponible. {mensaje}",
                size=13, color=ft.Colors.ON_SURFACE,
            ),
            actions=[
                ft.TextButton("Actualizar", on_click=al_actualizar),
                ft.TextButton("Ignorar",    on_click=al_ignorar),
            ],
        )

        self.page.banner = banner
        banner.open = True
        self.page.update()

    # ── Descarga del binario ──────────────────────────────────────────────────

    def _descargar(self, url: str, barra: ft.ProgressBar,
                    txt_est: ft.Text, dialogo: ft.AlertDialog) -> None:
        """
        Descarga el archivo con reporte de progreso (0.0 → 1.0).
        Al terminar, invoca el instalador del sistema.
        """
        try:
            nombre  = url.split("/")[-1].split("?")[0] or "update_app"
            destino = Path(__file__).parent / nombre

            def progreso(bloques_recibidos, tam_bloque, tam_total):
                if tam_total > 0:
                    avance = min(bloques_recibidos * tam_bloque / tam_total, 1.0)
                    barra.value    = avance
                    txt_est.value  = f"{int(avance * 100)} %"
                    self.page.update()

            urllib.request.urlretrieve(url, destino, reporthook=progreso)

            barra.value   = 1.0
            txt_est.value = "Descarga completa. Abriendo instalador..."
            self.page.update()

            self._abrir_instalador(destino)

        except Exception as exc:
            txt_est.value = f"Error al descargar: {exc}"
            barra.value   = 0
            self.page.update()

    @staticmethod
    def _abrir_instalador(ruta: Path) -> None:
        """Abre el instalador según la plataforma."""
        sistema = platform.system().lower()
        try:
            if sistema == "windows":
                os.startfile(str(ruta))
            else:
                # Android: intent para instalar APK
                subprocess.Popen([
                    "am", "start",
                    "-a", "android.intent.action.VIEW",
                    "-d", ruta.as_uri(),
                    "-t", "application/vnd.android.package-archive",
                ])
        except Exception:
            pass
