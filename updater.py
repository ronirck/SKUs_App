"""
updater.py — Sistema de auto-actualización de la app.

Verifica la tabla `app_config` en Supabase al arrancar y actúa según el resultado:
  - maintenance_mode  → pantalla bloqueante de mantenimiento
  - force_update      → diálogo modal con barra de progreso de descarga
  - nueva versión     → banner ignorable con botón "Actualizar"
  - data_version      → invalida caché de productos si los datos cambiaron
  - pending_changelog → muestra novedades de la versión recién instalada (una sola vez)

Uso desde main.py:
    import updater
    updater.AppUpdater(page).verificar()
"""

import json
import os
import platform
import subprocess
import threading
from pathlib import Path
from typing import Optional

import flet as ft
import requests

import database

# ── Versión actual del binario (actualizar antes de cada build) ───────────────
APP_VERSION = "1.1.0"

# ── Timeouts de descarga ──────────────────────────────────────────────────────
_CONNECT_TIMEOUT = 15          # segundos para establecer conexión
_READ_TIMEOUT    = 600         # segundos para recibir datos (~10 min para 260 MB)
_CHUNK_SIZE      = 1024 * 256  # 256 KB por chunk

# ── Archivo de estado local ───────────────────────────────────────────────────
_UPDATE_STATE_FILE = Path(__file__).parent / "update_state.json"


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS DE ESTADO LOCAL
# ══════════════════════════════════════════════════════════════════════════════

def leer_estado_local() -> dict:
    """Lee update_state.json. Retorna dict vacío si no existe o está corrupto."""
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
    if t1 < t2: return -1
    if t1 > t2: return 1
    return 0


def _url_descarga(config: dict, page: ft.Page) -> Optional[str]:
    """Retorna la URL de descarga leída de app_config según la plataforma."""
    try:
        if page.platform in (ft.PagePlatform.ANDROID,):
            return config.get("apk_url")
    except Exception:
        pass
    if platform.system().lower() == "windows":
        return config.get("win_url")
    return config.get("apk_url")


def _es_verdadero(valor) -> bool:
    """Normaliza booleanos que pueden venir de Supabase como string o bool."""
    return valor in (True, "true", "True", "1", 1)


def _fmt_mb(bytes_: Optional[int]) -> str:
    """Convierte bytes a string legible en MB, o '' si es None."""
    if bytes_ and bytes_ > 0:
        return f"{bytes_ / 1_048_576:.0f} MB"
    return ""


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
            # 0. Mostrar changelog de la versión recién instalada (una sola vez)
            self._mostrar_changelog_pendiente()

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
            pass  # Sin internet u otro error: la app sigue normalmente

    # ── Changelog post-instalación ────────────────────────────────────────────

    def _mostrar_changelog_pendiente(self) -> None:
        """
        Si update_state.json tiene un pending_changelog lo muestra una sola vez
        y luego lo borra del archivo.
        """
        estado = leer_estado_local()
        entrada = estado.get("pending_changelog")
        if not entrada:
            return

        version  = entrada.get("version", "")
        cambios  = entrada.get("cambios", "")
        if not cambios:
            return

        def cerrar(_):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(spacing=8, controls=[
                ft.Icon(ft.Icons.NEW_RELEASES_OUTLINED,
                        color=ft.Colors.PRIMARY, size=22),
                ft.Text(f"Novedades de la v{version}",
                        weight=ft.FontWeight.BOLD, size=15),
            ]),
            content=ft.Column(
                tight=True, spacing=0,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Text(cambios, size=13, color=ft.Colors.ON_SURFACE),
                ],
            ),
            actions=[ft.TextButton("Entendido", on_click=cerrar)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

        # Borrar para que no vuelva a aparecer
        del estado["pending_changelog"]
        guardar_estado_local(estado)

    # ── Verificación de datos ─────────────────────────────────────────────────

    def _verificar_datos(self, config: dict) -> None:
        """
        Compara data_version remota con la guardada localmente.
        Si cambió, invalida el caché de productos y actualiza el estado local.
        """
        data_version_remota = config.get("data_version")
        if not data_version_remota:
            return

        estado = leer_estado_local()
        if estado.get("data_version") != str(data_version_remota):
            database.invalidar_cache_productos()
            estado["data_version"] = str(data_version_remota)
            guardar_estado_local(estado)

    # ── Verificación de binario ───────────────────────────────────────────────

    def _verificar_binario(self, config: dict) -> None:
        """
        Compara APP_VERSION con latest_app_version y min_app_version.
        Muestra diálogo forzado, banner ignorable o nada según corresponda.
        """
        latest   = config.get("latest_app_version")
        min_ver  = config.get("min_app_version")
        mensaje  = config.get("update_message") or "Hay una nueva versión disponible."
        forzar   = _es_verdadero(config.get("force_update"))
        changelog = config.get("changelog") or ""

        if not latest:
            return

        if comparar_versiones(APP_VERSION, latest) >= 0:
            return  # Ya tenemos la versión más reciente

        debe_forzar = forzar or (
            min_ver and comparar_versiones(APP_VERSION, min_ver) < 0
        )

        url = _url_descarga(config, self.page)

        if debe_forzar:
            self._mostrar_dialogo_forzado(latest, mensaje, url, changelog)
        else:
            self._mostrar_banner(latest, mensaje, url, changelog)

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
                                  url: Optional[str], changelog: str) -> None:
        """
        Diálogo modal bloqueante con barra de progreso durante la descarga.
        Resuelve el tamaño del archivo con un HEAD request antes de mostrar el botón.
        """
        # Intentar obtener tamaño del archivo para mostrarlo al usuario
        tam_str = ""
        if url:
            try:
                r = requests.head(url, timeout=(_CONNECT_TIMEOUT, 10), allow_redirects=True)
                tam = int(r.headers.get("content-length", 0))
                tam_str = _fmt_mb(tam)
            except Exception:
                pass

        barra   = ft.ProgressBar(value=0, width=260,
                                  color=ft.Colors.PRIMARY,
                                  bgcolor=ft.Colors.SURFACE_CONTAINER)
        txt_est = ft.Text("", size=12, color=ft.Colors.SECONDARY,
                          text_align=ft.TextAlign.CENTER)
        label_btn = f"Actualizar ahora  ({tam_str})" if tam_str else "Actualizar ahora"
        btn_act = ft.FilledButton(label_btn, icon=ft.Icons.DOWNLOAD, expand=True)

        cuerpo = ft.Column(tight=True, spacing=12, controls=[
            ft.Text(mensaje, size=13, color=ft.Colors.ON_SURFACE,
                    text_align=ft.TextAlign.CENTER),
        ])

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Row(spacing=8, controls=[
                ft.Icon(ft.Icons.SYSTEM_UPDATE, color=ft.Colors.PRIMARY, size=22),
                ft.Text(f"SKUs app  v{version}",
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
                args=(url, version, changelog, barra, txt_est, dialogo),
                daemon=True,
            ).start()

        btn_act.on_click = iniciar_descarga

        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()

    # ── Banner ignorable ──────────────────────────────────────────────────────

    def _mostrar_banner(self, version: str, mensaje: str,
                         url: Optional[str], changelog: str) -> None:
        """Banner no bloqueante con botones 'Actualizar ahora' e 'Ignorar'."""

        def al_actualizar(_):
            banner.open = False
            self.page.update()
            if url:
                self._mostrar_dialogo_forzado(version, mensaje, url, changelog)

        def al_ignorar(_):
            banner.open = False
            self.page.update()

        banner = ft.Banner(
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            leading=ft.Icon(ft.Icons.UPDATE,
                            color=ft.Colors.PRIMARY, size=28),
            content=ft.Text(
                f"SKUs app v{version} disponible. {mensaje}",
                size=13, color=ft.Colors.ON_SURFACE,
            ),
            actions=[
                ft.TextButton("Actualizar ahora", on_click=al_actualizar),
                ft.TextButton("Ignorar",          on_click=al_ignorar),
            ],
        )

        self.page.banner = banner
        banner.open = True
        self.page.update()

    # ── Descarga del binario ──────────────────────────────────────────────────

    def _descargar(self, url: str, version: str, changelog: str,
                    barra: ft.ProgressBar, txt_est: ft.Text,
                    dialogo: ft.AlertDialog) -> None:
        """
        Descarga el APK usando requests con stream=True y chunks de 256 KB.
        - Timeout: 15 s conexión / 600 s lectura.
        - Si la descarga falla a mitad, elimina el archivo parcial.
        - Al completar, guarda el changelog en update_state.json y abre el instalador.
        """
        nombre  = url.split("/")[-1].split("?")[0] or "update_app.apk"
        destino = Path(__file__).parent / nombre

        try:
            with requests.get(
                url,
                stream=True,
                timeout=(_CONNECT_TIMEOUT, _READ_TIMEOUT),
                allow_redirects=True,
            ) as resp:
                resp.raise_for_status()

                tam_total = int(resp.headers.get("content-length", 0))
                recibido  = 0

                with open(destino, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=_CHUNK_SIZE):
                        if not chunk:
                            continue
                        f.write(chunk)
                        recibido += len(chunk)

                        if tam_total > 0:
                            avance        = min(recibido / tam_total, 1.0)
                            barra.value   = avance
                            txt_est.value = (
                                f"{_fmt_mb(recibido)} / {_fmt_mb(tam_total)}"
                                f"  ({int(avance * 100)} %)"
                            )
                        else:
                            barra.value   = None  # indeterminado
                            txt_est.value = f"{_fmt_mb(recibido)} descargados..."

                        self.page.update()

            # Descarga completa
            barra.value   = 1.0
            txt_est.value = "Descarga completa. Abriendo instalador..."
            self.page.update()

            # Guardar changelog para mostrarlo tras reiniciar con la nueva versión
            if changelog:
                estado = leer_estado_local()
                estado["pending_changelog"] = {
                    "version": version,
                    "cambios": changelog,
                }
                guardar_estado_local(estado)

            self._abrir_instalador(destino)

        except requests.exceptions.Timeout:
            _limpiar_parcial(destino)
            txt_est.value = "Error: tiempo de espera agotado. Comprueba tu conexión."
            barra.value   = 0
            self.page.update()

        except requests.exceptions.ConnectionError:
            _limpiar_parcial(destino)
            txt_est.value = "Error: no se pudo conectar. Verifica tu internet."
            barra.value   = 0
            self.page.update()

        except requests.exceptions.HTTPError as exc:
            _limpiar_parcial(destino)
            txt_est.value = f"Error del servidor: {exc.response.status_code}."
            barra.value   = 0
            self.page.update()

        except Exception as exc:
            _limpiar_parcial(destino)
            txt_est.value = f"Error inesperado: {exc}"
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
                subprocess.Popen([
                    "am", "start",
                    "-a", "android.intent.action.VIEW",
                    "-d", ruta.as_uri(),
                    "-t", "application/vnd.android.package-archive",
                ])
        except Exception:
            pass


# ── Helpers de archivo ────────────────────────────────────────────────────────

def _limpiar_parcial(ruta: Path) -> None:
    """Elimina el archivo si existe (descarga incompleta)."""
    try:
        if ruta.exists():
            ruta.unlink()
    except Exception:
        pass
