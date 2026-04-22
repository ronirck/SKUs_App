"""
main.py — Entry point.
Abre GuiaEstudioView al iniciar (pantalla principal).
InicioView (camino de niveles) comentada para versión futura.
"""

import flet as ft
from config import APP_TITLE, COLOR_SEED, WINDOW_HEIGHT, WINDOW_WIDTH
import auth
import preferences

_CASA_ICONOS = {
    "Prisma":  "Images/Prisma.ico",
    "FEBECA":  "Images/Febeca.ico",
    "SILLACA": "Images/Sillaca.ico",
    "BEVAL":   "Images/Beval.ico",
    "COFERSA": "Images/Febeca.ico",
    "MUNDIAL DE PARTES": "Images/Beval.ico",
}


def configurar_pagina(page: ft.Page) -> None:
    import os
    from config import CASA_COLORS
    casa = preferences.get_casa()
    color_seed = CASA_COLORS.get(casa, COLOR_SEED)
    ico_rel = _CASA_ICONOS.get(casa, "Images/Prisma.ico")
    abs_icon_path = os.path.abspath(ico_rel)

    page.title = APP_TITLE
    page.favicon = ico_rel
    page.window_icon = abs_icon_path

    # Intentar forzar el icono en el objeto window si existe
    if hasattr(page, "window"):
        page.window.icon = abs_icon_path

    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.WHITE
    page.theme = ft.Theme(
        color_scheme_seed=color_seed,
        color_scheme=ft.ColorScheme(
            surface=ft.Colors.WHITE,
        ),
    )
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

    # Detectar actividad por teclado y toque/clic
    page.on_keyboard_event = lambda e: auth.registrar_actividad()
    page.on_click = lambda e: auth.registrar_actividad()

    def corazon():
        import time
        while True:
            time.sleep(10)
            try:
                auth.registrar_corazon()
            except Exception:
                pass

    page.run_thread(corazon)

    # Pantalla de carga inicial
    from components import estado_cargando
    page.views.append(ft.View(
        route="/cargando",
        padding=0,
        bgcolor=ft.Colors.SURFACE,
        controls=[estado_cargando("Iniciando...")],
    ))
    page.update()

    page.run_thread(lambda: _iniciar_app(page))


def _iniciar_app(page: ft.Page) -> None:
    """
    Punto de entrada real de la app. Se ejecuta en un hilo secundario.
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
        return

    # ── Mantenimiento ─────────────────────────────────────────────────────────
    if resultado.get("maintenance"):
        vista = ft.View(
            route="/mantenimiento",
            controls=[
                ft.Column(
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                    controls=[
                        ft.Icon(ft.Icons.BUILD_CIRCLE_OUTLINED, size=64, color=ft.Colors.SECONDARY),
                        ft.Text("Mantenimiento", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            resultado.get("message") or "En mantenimiento. Vuelve pronto.",
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

    if not resultado.get("needs_update"):
        return

    # ── Actualización disponible ──────────────────────────────────────────────
    apk_url        = str(resultado.get("apk_url") or "")
    release_notes  = str(resultado.get("release_notes") or "")
    latest_version = str(resultado.get("latest_version") or "1.0.0")
    es_forzada     = bool(resultado.get("force"))

    controles_info: list = [
        ft.Text(
            f"Versión {latest_version} ya está disponible.",
            weight=ft.FontWeight.BOLD,
        ),
    ]

    if es_forzada:
        controles_info.append(
            ft.Text(
                "Esta actualización es obligatoria. Por favor actualiza la app para continuar.",
                color=ft.Colors.ERROR,
                size=13,
            )
        )

    if release_notes:
        controles_info += [
            ft.Divider(height=12),
            ft.Text("¿Qué hay de nuevo?", weight=ft.FontWeight.BOLD, size=13),
        ]
        for linea in release_notes.splitlines():
            linea = linea.strip()
            if linea:
                controles_info.append(ft.Text(f"• {linea}", size=13))

    # Limpiar URL (sin espacios)
    url_final = apk_url.strip().replace(" ", "%20")

    if url_final:
        controles_info += [
            ft.Divider(height=12),
            ft.Text(
                "Si el botón no funciona, copia este enlace en tu navegador:",
                size=13,
                weight=ft.FontWeight.W_500,
            ),
            ft.Row(
                controls=[
                    ft.TextField(
                        value=url_final,
                        read_only=True,
                        expand=True,
                        text_size=13,
                    )
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ]

    async def abrir_enlace(e):
        try:
            if url_final:
                await page.launch_url(url_final)
        except Exception:
            pass

    async def cerrar_app(e):
        try:
            auth.registrar_fin_uso()
            if hasattr(page, "window") and hasattr(page.window, "close"):
                try: await page.window.close()
                except Exception: page.window.close()
            elif hasattr(page, "window_close"):
                page.window_close()
            else:
                import os
                os._exit(0)
        except Exception:
            import os
            os._exit(0)

    def mas_tarde(e):
        """Cierra el diálogo y deja que el usuario siga usando la app."""
        dialogo_update.open = False
        page.update()

    # Botón secundario: "Cerrar app" si es forzada, "Más tarde" si es opcional
    if es_forzada:
        boton_secundario = ft.TextButton("Cerrar app", on_click=cerrar_app)
    else:
        boton_secundario = ft.TextButton("Más tarde", on_click=mas_tarde)

    dialogo_update = ft.AlertDialog(
        modal=True,
        title=ft.Text("Actualización disponible 🎉"),
        content=ft.Column(
            tight=True,
            scroll=ft.ScrollMode.AUTO,
            controls=controles_info,
        ),
        actions=[
            ft.TextButton("⬇️ Abrir navegador", on_click=abrir_enlace),
            boton_secundario,
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(dialogo_update)
    dialogo_update.open = True
    page.update()


def _mostrar_novedades_pendientes(page: ft.Page) -> None:
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
                ft.Text(f"Versión {AppUpdater.APP_VERSION}", weight=ft.FontWeight.BOLD, size=14),
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
