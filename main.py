"""
main.py — Entry point.
Abre GuiaEstudioView al iniciar (pantalla principal).
InicioView (camino de niveles) comentada para versión futura.
"""

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

    # Mostrar pantalla de carga antes de lanzar el hilo.
    # Sin esta vista inicial, Flet renderiza un frame vacío y la pantalla queda
    # en blanco hasta que un evento externo (p.ej. redimensionar) fuerza el repaint.
    from components import estado_cargando
    page.views.append(ft.View(
        route="/cargando",
        padding=0,
        bgcolor=ft.Colors.SURFACE,
        controls=[estado_cargando("Iniciando...")],
    ))
    page.update()

    # page.run_thread integra el hilo con el event loop de Flet, garantizando
    # que los page.update() dentro del hilo propaguen el render correctamente.
    page.run_thread(lambda: _iniciar_app(page))


def _iniciar_app(page: ft.Page) -> None:
    """
    Punto de entrada real de la app. Se ejecuta en un hilo secundario.

    Orden deliberado para evitar pantalla en blanco en mobile:
      1. Restaurar sesión y montar la vista → el usuario ve contenido de inmediato.
      2. Mostrar novedades pendientes (lectura de disco, sin red).
      3. Verificar actualizaciones en Supabase (red).
         - Mantenimiento  → reemplaza la vista actual.
         - Actualización  → diálogo; al aceptar abre el navegador con la URL del APK.
    """
    from updater import AppUpdater
    from views import GuiaEstudioView, LoginView

    # ── Paso 1: montar vista de sesión ────────────────────────────────────────
    sesion = auth.restaurar_sesion()
    if sesion:
        GuiaEstudioView(page).mount()
    else:
        LoginView(page).mount()

    # ── Paso 2: novedades de versión recién instalada (solo disco) ────────────
    _mostrar_novedades_pendientes(page)

    # ── Paso 3: verificar actualizaciones (red) ───────────────────────────────
    try:
        resultado = AppUpdater.check_app_update()
    except Exception:
        return   # Sin internet: la app funciona normalmente

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
        return

    if not resultado["needs_update"]:
        return

    # ── Actualización disponible ──────────────────────────────────────────────
    apk_url        = resultado["apk_url"]
    release_notes  = resultado["release_notes"]
    latest_version = resultado["latest_version"]

    controles_info: list = [
        ft.Text(
            f"Versión {latest_version} ya está disponible.",
            size=13,
            weight=ft.FontWeight.BOLD,
        ),
    ]

    if release_notes:
        controles_info += [
            ft.Divider(height=12),
            ft.Text("¿Qué hay de nuevo?", weight=ft.FontWeight.BOLD, size=13),
        ]
        for linea in release_notes.splitlines():
            linea = linea.strip()
            if linea:
                controles_info.append(ft.Text(f"• {linea}", size=13))

    controles_info += [
        ft.Divider(height=12),
        ft.Text(
            "Para actualizar:\n"
            "1. Copia el enlace de descarga\n"
            "2. Ábrelo en tu navegador\n"
            "3. Descarga e instala el archivo APK",
            size=13,
        ),
        ft.Container(height=4),
        ft.Text(apk_url, selectable=True, size=11, color=ft.Colors.SECONDARY),
    ]

    dialogo_update = ft.AlertDialog(
        modal=True,
        title=ft.Text("Actualización disponible 🎉"),
        content=ft.Column(
            tight=True,
            scroll=ft.ScrollMode.AUTO,
            controls=controles_info,
        ),
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def copiar_enlace(e):
        page.set_clipboard(apk_url)
        page.snack_bar = ft.SnackBar(
            content=ft.Text("¡Enlace copiado! Pégalo en tu navegador."),
            duration=3000,
            bgcolor=ft.Colors.GREEN_700,
        )
        page.snack_bar.open = True
        page.update()

    def cerrar_app(e):
        page.window.close()

    dialogo_update.actions = [
        ft.ElevatedButton("📋 Copiar enlace", on_click=copiar_enlace),
        ft.ElevatedButton(
            "Cerrar app", icon=ft.Icons.CLOSE, on_click=cerrar_app,
        ),
    ]

    page.overlay.append(dialogo_update)
    dialogo_update.open = True
    page.update()


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
