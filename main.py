"""
main.py — Entry point.
Abre GuiaEstudioView al iniciar (pantalla principal).
InicioView (camino de niveles) comentada para versión futura.
"""

import flet as ft
from config import APP_TITLE, COLOR_SEED, WINDOW_HEIGHT, WINDOW_WIDTH
import auth


def configurar_pagina(page: ft.Page) -> None:
    import os
    abs_icon_path = os.path.abspath("favicon.ico")
    
    page.title = APP_TITLE
    page.favicon = "favicon.ico"
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
        page.width  = WINDOW_WIDTH
        page.height = WINDOW_HEIGHT


def main(page: ft.Page) -> None:
    configurar_pagina(page)

    # Fallback genérico para web o cierres forzados
    def on_disconnect(e):
        auth.registrar_fin_uso()

    page.on_disconnect = on_disconnect

    def corazon():
        import time
        while True:
            time.sleep(60)
            try:
                auth.registrar_corazon()
            except Exception:
                pass
    
    page.run_thread(corazon)

    from views import GuiaEstudioView, LoginView
    sesion = auth.restaurar_sesion()
    if sesion:
        GuiaEstudioView(page).mount()
    else:
        LoginView(page).mount()


ft.run(main, assets_dir=".")