"""
main.py — Entry point.
Abre GuiaEstudioView al iniciar (pantalla principal).
InicioView (camino de niveles) comentada para versión futura.
"""

import threading
import flet as ft
from config import APP_TITLE, COLOR_SEED, WINDOW_HEIGHT, WINDOW_WIDTH
import auth
import preferences

_SEDE_ICONOS = {
    "Prisma":  "Images/Prisma.ico",
    "FEBECA":  "Images/Febeca.ico",
    "SILLACA": "Images/Sillaca.ico",
    "BEVAL":   "Images/Beval.ico",
}


def configurar_pagina(page: ft.Page) -> None:
    import os
    sede = preferences.get_sede()
    ico_rel = _SEDE_ICONOS.get(sede, "Images/Prisma.ico")
    abs_icon_path = os.path.abspath(ico_rel)

    page.title = APP_TITLE
    page.favicon = ico_rel
    page.window_icon = abs_icon_path

    # Intentar forzar el icono en el objeto window si existe
    if hasattr(page, "window"):
        page.window.icon = abs_icon_path

    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=COLOR_SEED)
    if page.platform in (
        ft.PagePlatform.WINDOWS,
        ft.PagePlatform.MACOS,
        ft.PagePlatform.LINUX,
    ):
        page.width = WINDOW_WIDTH
        page.height = WINDOW_HEIGHT


def main(page: ft.Page) -> None:
    configurar_pagina(page)

    # Detectar cierre de ventana y limpiar antes de que el proceso termine.
    # window.close() es async → el handler debe ser async.
    # prevent_close NO se usa: causaría loop infinito con window.close().
    async def on_window_event(e):
        es_cierre = (
            getattr(e, "type", None) == ft.WindowEventType.CLOSE
            or getattr(e, "data", None) == "close"
        )
        if es_cierre:
            auth.registrar_fin_uso()

    page.window.on_event = on_window_event

    # Fallback para Ctrl+C o kill del proceso
    def on_disconnect(e):
        auth.registrar_fin_uso()

    page.on_disconnect = on_disconnect

    # Detectar actividad por teclado (búsquedas, navegación con teclas, etc.)
    page.on_keyboard_event = lambda e: auth.registrar_actividad()

    def corazon():
        import time
        while True:
            time.sleep(10)   # cada 10 s: detecta inactividad de 1 min con precisión razonable
            try:
                auth.registrar_corazon()
            except Exception:
                pass

    page.run_thread(corazon)

    # Verificar actualizaciones ANTES de montar cualquier vista.
    # Si hay actualización disponible, la app queda bloqueada hasta instalarla.
    threading.Thread(target=_iniciar_app, args=(page,), daemon=True).start()


def _iniciar_app(page: ft.Page) -> None:
    """
    Punto de entrada real de la app. Se ejecuta en un hilo secundario para no
    bloquear el hilo de Flet mientras se consulta Supabase.

    Orden:
      1. Verifica mantenimiento / actualización obligatoria antes de cualquier vista.
         Si hay actualización disponible la app queda bloqueada hasta instalarla.
      2. Si todo está en orden, monta la vista de sesión y muestra las novedades
         de la versión recién instalada (si las hay).
    """
    import tempfile
    from pathlib import Path
    from updater import AppUpdater

    try:
        resultado = AppUpdater.check_app_update()
    except Exception:
        resultado = {
            "maintenance": False, "needs_update": False, "force": False,
            "latest_version": AppUpdater.APP_VERSION,
            "apk_url": "", "message": "", "release_notes": "",
        }

    # ── Mantenimiento ─────────────────────────────────────────────────────────
    if resultado["maintenance"]:
        vista = ft.View(
            route="/mantenimiento",
            controls=[
                ft.Column(
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                    controls=[
                        ft.Icon(ft.Icons.BUILD_CIRCLE_OUTLINED,
                                size=64, color=ft.Colors.SECONDARY),
                        ft.Text("Mantenimiento",
                                size=22, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            resultado["message"]
                            or "La app está en mantenimiento.\nVuelve pronto.",
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.SECONDARY,
                        ),
                    ],
                )
            ],
        )
        page.views.clear()
        page.views.append(vista)
        page.update()
        return   # La app queda en pantalla de mantenimiento sin vistas normales

    # ── Actualización disponible — siempre bloqueante ─────────────────────────
    # Toda actualización es obligatoria: el usuario no puede usar la app hasta
    # instalar la nueva versión.
    if resultado["needs_update"]:
        barra_progreso = ft.ProgressBar(value=0, visible=False, expand=True)
        texto_estado   = ft.Text("", size=12, color=ft.Colors.SECONDARY, visible=False)
        btn_actualizar = ft.ElevatedButton("Actualizar ahora", icon=ft.Icons.DOWNLOAD)

        controles_contenido = []
        if resultado["message"]:
            controles_contenido.append(ft.Text(resultado["message"], size=13))
            controles_contenido.append(ft.Container(height=4))
        controles_contenido.append(
            ft.Text(
                f"Versión disponible: {resultado['latest_version']}",
                size=13,
                weight=ft.FontWeight.BOLD,
            )
        )
        if resultado["release_notes"]:
            controles_contenido += [
                ft.Divider(height=12),
                ft.Text("¿Qué hay de nuevo?", weight=ft.FontWeight.BOLD, size=13),
                ft.Text(resultado["release_notes"], size=13),
            ]
        controles_contenido += [ft.Container(height=8), barra_progreso, texto_estado]

        def iniciar_descarga(e):
            """Deshabilita el botón, muestra la barra y lanza la descarga en un hilo."""
            btn_actualizar.disabled = True
            barra_progreso.visible  = True
            texto_estado.visible    = True
            texto_estado.value      = "Preparando descarga..."
            page.update()

            def descargar():
                try:
                    destino = Path(tempfile.gettempdir()) / "sku_update.apk"

                    def en_progreso(progreso: float):
                        barra_progreso.value = progreso
                        texto_estado.value   = f"Descargando... {int(progreso * 100)}%"
                        page.update()

                    ruta = AppUpdater.download_apk(resultado["apk_url"], en_progreso, destino)
                    texto_estado.value = "¡Descarga completa! Abriendo instalador..."
                    page.update()

                    # Guardar novedades antes de abrir el instalador para mostrarlas al reiniciar
                    AppUpdater.save_pending_release_notes(resultado["release_notes"])
                    AppUpdater.open_installer(ruta)

                except Exception as exc:
                    texto_estado.value      = f"Error al descargar: {exc}"
                    barra_progreso.visible  = False
                    btn_actualizar.disabled = False
                    page.update()

            threading.Thread(target=descargar, daemon=True).start()

        btn_actualizar.on_click = iniciar_descarga

        dialogo = ft.AlertDialog(
            modal=True,   # Sin posibilidad de cerrar — la actualización es obligatoria
            title=ft.Text("Actualización disponible"),
            content=ft.Column(
                tight=True,
                scroll=ft.ScrollMode.AUTO,
                controls=controles_contenido,
            ),
            actions=[btn_actualizar],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()
        return   # La app queda bloqueada hasta que el usuario instale la actualización

    # ── Sin actualizaciones: flujo normal ─────────────────────────────────────
    from views import GuiaEstudioView, LoginView
    sesion = auth.restaurar_sesion()
    if sesion:
        GuiaEstudioView(page).mount()
    else:
        LoginView(page).mount()

    # Mostrar novedades de la versión recién instalada (si el instalador las guardó)
    _mostrar_novedades_pendientes(page)


def _mostrar_novedades_pendientes(page: ft.Page) -> None:
    """
    Muestra un AlertDialog con las novedades de la versión recién instalada.
    Solo actúa si el instalador dejó novedades pendientes en update_state.json.
    """
    from updater import AppUpdater

    novedades = AppUpdater.get_pending_release_notes()
    if not novedades:
        return

    def cerrar(e):
        dialogo.open = False
        page.update()
        AppUpdater.clear_pending_release_notes()

    dialogo = ft.AlertDialog(
        modal=True,
        title=ft.Text("¡Actualización instalada! 🎉"),
        content=ft.Column(
            tight=True,
            controls=[
                ft.Text(
                    f"Versión {AppUpdater.APP_VERSION}",
                    weight=ft.FontWeight.BOLD,
                    size=14,
                ),
                ft.Divider(height=8),
                ft.Text("¿Qué hay de nuevo?", weight=ft.FontWeight.BOLD, size=13),
                ft.Text(novedades, size=13),
            ],
        ),
        actions=[ft.TextButton("¡Entendido!", on_click=cerrar)],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(dialogo)
    dialogo.open = True
    page.update()


ft.run(main, assets_dir=".")
