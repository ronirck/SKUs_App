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


def _ejecutar_descarga(
    page: ft.Page,
    apk_url: str,
    release_notes: str,
    latest_version: str,
) -> None:
    """
    Guarda los parámetros de descarga en disco y arranca el hilo.

    Al persistir ANTES de arrancar el hilo, si el proceso muere (el usuario
    cierra la app), al reabrir se detecta la entrada en update_state.json y
    la descarga se reanuda automáticamente desde _iniciar_app.
    """
    import tempfile
    from pathlib import Path
    from updater import AppUpdater

    # Persistir parámetros antes de arrancar — garantiza reanudación al reabrir
    AppUpdater.save_pending_download(apk_url, release_notes, latest_version)

    # ── Tarjeta de progreso persistente (visible desde cualquier pestaña) ─────
    barra_progreso = ft.ProgressBar(value=0, expand=True)
    texto_porcentaje = ft.Text("0 %", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
    tarjeta_progreso = ft.Container(
        content=ft.Column(
            spacing=6,
            tight=True,
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.DOWNLOAD, size=16, color=ft.Colors.PRIMARY),
                        ft.Text(
                            f"Descargando v{latest_version}…",
                            size=12,
                            expand=True,
                            color=ft.Colors.ON_SURFACE,
                        ),
                        texto_porcentaje,
                    ],
                    spacing=6,
                ),
                barra_progreso,
            ],
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        margin=ft.margin.only(left=12, right=12, bottom=16),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        border_radius=12,
        shadow=ft.BoxShadow(
            blur_radius=8,
            color=ft.Colors.with_opacity(0.18, ft.Colors.BLACK),
        ),
    )
    # Envolver en una columna alineada al fondo para que no tape el contenido
    overlay_progreso = ft.Column(
        controls=[tarjeta_progreso],
        alignment=ft.MainAxisAlignment.END,
        expand=True,
    )
    page.overlay.append(overlay_progreso)
    page.update()

    def en_progreso(fraccion: float) -> None:
        barra_progreso.value = fraccion
        texto_porcentaje.value = f"{int(fraccion * 100)} %"
        try:
            page.update()
        except Exception:
            pass

    def descargar():
        try:
            destino = Path(tempfile.gettempdir()) / "sku_update.apk"
            AppUpdater.download_apk(apk_url, en_progreso, destino)

            # Descarga completa — quitar tarjeta de progreso
            if overlay_progreso in page.overlay:
                page.overlay.remove(overlay_progreso)

            AppUpdater.clear_pending_download()
            AppUpdater.save_pending_release_notes(release_notes)

            btn_instalar = ft.ElevatedButton("Instalar ahora", icon=ft.Icons.SYSTEM_UPDATE)

            def instalar(ev):
                btn_instalar.disabled = True
                page.update()
                AppUpdater.open_installer(destino)

            btn_instalar.on_click = instalar

            dialogo_instalar = ft.AlertDialog(
                modal=True,
                title=ft.Text("¡Actualización lista para instalar!"),
                content=ft.Column(
                    tight=True,
                    controls=[
                        ft.Text(
                            f"Versión {latest_version} descargada.",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "Instala ahora para continuar con la versión más reciente.",
                            size=13,
                        ),
                    ],
                ),
                actions=[btn_instalar],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(dialogo_instalar)
            dialogo_instalar.open = True
            page.update()

        except Exception as exc:
            # Quitar tarjeta de progreso y limpiar estado
            if overlay_progreso in page.overlay:
                page.overlay.remove(overlay_progreso)
            AppUpdater.clear_pending_download()
            snack_error = ft.SnackBar(
                content=ft.Text(f"Error al descargar: {exc}"),
                bgcolor=ft.Colors.ERROR_CONTAINER,
            )
            page.overlay.append(snack_error)
            snack_error.open = True
            page.update()

    page.run_thread(descargar)


def _iniciar_app(page: ft.Page) -> None:
    """
    Punto de entrada real de la app. Se ejecuta en un hilo secundario.

    Orden deliberado para evitar pantalla en blanco en mobile:
      1. Restaurar sesión y montar la vista → el usuario ve contenido de inmediato.
      2. Mostrar novedades pendientes (lectura de disco, sin red).
      3. Si hay una descarga interrumpida → reanudarla sin preguntar y salir.
      4. Verificar actualizaciones en Supabase (red).
         - Mantenimiento  → reemplaza la vista actual.
         - Actualización  → diálogo de confirmación; descarga en segundo plano.
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

    # ── Paso 3: reanudar descarga interrumpida si la hay ──────────────────────
    # Si el usuario cerró la app mientras descargaba, los parámetros quedaron
    # guardados en update_state.json. Los retomamos sin pedirle nada al usuario.
    descarga_pendiente = AppUpdater.get_pending_download()
    if descarga_pendiente:
        _ejecutar_descarga(
            page,
            descarga_pendiente["url"],
            descarga_pendiente.get("release_notes", ""),
            descarga_pendiente.get("latest_version", ""),
        )
        return   # No hace falta consultar Supabase — ya sabemos que hay actualización

    # ── Paso 4: verificar actualizaciones (red) ───────────────────────────────
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
    # Diálogo informativo obligatorio (modal=True, sin botón de cierre).
    # Al aceptar: el diálogo se cierra, la descarga ocurre en segundo plano
    # y el usuario sigue usando la app con normalidad.
    controles_info = []
    if resultado["message"]:
        controles_info.append(ft.Text(resultado["message"], size=13))
        controles_info.append(ft.Container(height=4))
    controles_info.append(
        ft.Text(
            f"Versión disponible: {resultado['latest_version']}",
            size=13,
            weight=ft.FontWeight.BOLD,
        )
    )
    if resultado["release_notes"]:
        controles_info += [
            ft.Divider(height=12),
            ft.Text("¿Qué hay de nuevo?", weight=ft.FontWeight.BOLD, size=13),
            ft.Text(resultado["release_notes"], size=13),
        ]
    controles_info += [
        ft.Container(height=4),
        ft.Text(
            "La descarga ocurrirá en segundo plano. "
            "Te avisaremos cuando esté lista para instalar.",
            size=12,
            color=ft.Colors.SECONDARY,
        ),
    ]

    btn_descargar = ft.ElevatedButton("Descargar", icon=ft.Icons.DOWNLOAD)

    dialogo_info = ft.AlertDialog(
        modal=True,
        title=ft.Text("Actualización disponible"),
        content=ft.Column(
            tight=True,
            scroll=ft.ScrollMode.AUTO,
            controls=controles_info,
        ),
        actions=[btn_descargar],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def aceptar_descarga(e):
        dialogo_info.open = False
        page.update()
        _ejecutar_descarga(
            page,
            resultado["apk_url"],
            resultado["release_notes"],
            resultado["latest_version"],
        )

    btn_descargar.on_click = aceptar_descarga

    page.overlay.append(dialogo_info)
    dialogo_info.open = True
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
