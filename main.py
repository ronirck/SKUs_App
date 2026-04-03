"""
main.py — Entry point.
Abre GuiaEstudioView al iniciar (pantalla principal).
InicioView (camino de niveles) comentada para versión futura.
"""

import flet as ft
from config import APP_TITLE, COLOR_SEED, SEDE_COLORES, WINDOW_HEIGHT, WINDOW_WIDTH
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

    page.title = APP_TITLE
    page.theme_mode = ft.ThemeMode.LIGHT
    seed = SEDE_COLORES.get(sede, COLOR_SEED)
    page.theme = ft.Theme(color_scheme_seed=seed)

    es_escritorio = page.platform in (
        ft.PagePlatform.WINDOWS,
        ft.PagePlatform.MACOS,
        ft.PagePlatform.LINUX,
    )
    if es_escritorio:
        page.width  = WINDOW_WIDTH
        page.height = WINDOW_HEIGHT
        try:
            ico_rel       = _SEDE_ICONOS.get(sede, "Images/Prisma.ico")
            abs_icon_path = os.path.abspath(ico_rel)
            page.favicon  = ico_rel
            if hasattr(page, "window"):
                page.window.icon = abs_icon_path
        except Exception:
            pass


def main(page: ft.Page) -> None:
    configurar_pagina(page)

    # Detectar cierre de ventana y limpiar antes de que el proceso termine.
    # window.close() es async → el handler debe ser async.
    # prevent_close NO se usa: causaría loop infinito con window.close().
    # Cierre de ventana — solo aplica en escritorio
    if page.platform in (
        ft.PagePlatform.WINDOWS,
        ft.PagePlatform.MACOS,
        ft.PagePlatform.LINUX,
    ):
        async def on_window_event(e):
            es_cierre = (
                getattr(e, "type", None) == ft.WindowEventType.CLOSE
                or getattr(e, "data", None) == "close"
            )
            if es_cierre:
                auth.registrar_fin_uso()

        try:
            page.window.on_event = on_window_event
        except Exception:
            pass

    # Fallback para Ctrl+C, kill del proceso o desconexión en Android
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

    from views import GuiaEstudioView, LoginView
    import updater

    sesion = auth.restaurar_sesion()
    if sesion:
        GuiaEstudioView(page).mount()
    else:
        LoginView(page).mount()

    # Verificar actualizaciones en background después de mostrar la primera vista.
    # No bloquea el arranque; si no hay internet, simplemente no hace nada.
    updater.AppUpdater(page).verificar()


ft.run(main, assets_dir=".")
