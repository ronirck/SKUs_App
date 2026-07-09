import flet as ft
from datetime import datetime

ESTATUS_COLORS = {
    "sin_revisar": ft.Colors.GREY_600,
    "en_revision": ft.Colors.BLUE_400,
    "pendiente": ft.Colors.ORANGE_400,
    "resuelto": ft.Colors.GREEN_400,
}

ESTATUS_LABELS = {
    "sin_revisar": "Sin revisar",
    "en_revision": "En revisión",
    "pendiente": "Pendiente",
    "resuelto": "Resuelto",
}


def admin_reportes_view(
    page: ft.Page,
    time_offset: float,
    on_interaction,
    primary_color,
):
    from session_manager import register_interaction

    def handle_interaction(e=None):
        register_interaction(time_offset)
        if on_interaction:
            on_interaction()

    content_area = ft.Container(expand=True)
    reportes_data = []

    def fmt_date(s: str) -> str:
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return s

    def load_reportes():
        content_area.content = ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )
        page.update()

        def do_load():
            try:
                from auth import get_client
                client = get_client()
                res = (
                    client.table("reportes_error")
                    .select("*, perfil_usuario(nombre, email)")
                    .order("creado_en", desc=True)
                    .execute()
                )
                nonlocal reportes_data
                reportes_data = res.data or []
            except Exception:
                reportes_data = []

            build_list()
            page.update()

        page.run_thread(do_load)

    def build_list():
        if not reportes_data:
            content_area.content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.ASSIGNMENT_OUTLINED, size=48, color=ft.Colors.GREY_700),
                        ft.Text("No hay reportes aún", size=14, color=ft.Colors.GREY_500),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
            )
            return

        rows = []
        for r in reportes_data:
            perfil = r.get("perfil_usuario") or {}
            nombre = perfil.get("nombre", "Usuario")
            estatus = r.get("estatus", "sin_revisar")
            preview = (r.get("mensaje", ""))[:80]
            color = ESTATUS_COLORS.get(estatus, ft.Colors.GREY_600)

            rows.append(
                ft.GestureDetector(
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(nombre, size=13, weight=ft.FontWeight.W_600,
                                                expand=True, no_wrap=True),
                                        ft.Container(
                                            content=ft.Text(
                                                ESTATUS_LABELS.get(estatus, estatus),
                                                size=9, color=ft.Colors.WHITE,
                                                weight=ft.FontWeight.W_600,
                                            ),
                                            bgcolor=color,
                                            border_radius=8,
                                            padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                ft.Text(preview, size=12, color=ft.Colors.GREY_400, no_wrap=True),
                                ft.Text(fmt_date(r.get("creado_en", "")),
                                        size=10, color=ft.Colors.GREY_600),
                            ],
                            spacing=3,
                            tight=True,
                        ),
                        padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                        border=ft.Border(
                            bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.1, primary_color))
                        ),
                    ),
                    on_tap=lambda e, rep=r: open_detail(rep),
                )
            )

        content_area.content = ft.ListView(controls=rows, expand=True, spacing=0)

    def open_detail(reporte: dict):
        handle_interaction()

        perfil = reporte.get("perfil_usuario") or {}
        nombre = perfil.get("nombre", "Usuario")
        email = perfil.get("email", "")
        estatus_cur = [reporte.get("estatus", "sin_revisar")]

        status_text = ft.Text(value="", size=12, text_align=ft.TextAlign.CENTER)

        estatus_dd = ft.Dropdown(
            label="Estatus",
            value=estatus_cur[0],
            options=[ft.dropdown.Option(key=k, text=v) for k, v in ESTATUS_LABELS.items()],
            border_radius=12,
            border_color=ft.Colors.with_opacity(0.3, primary_color),
            focused_border_color=primary_color,
            expand=True,
        )

        def on_estatus_select(e):
            handle_interaction()
            new_est = estatus_dd.value
            if new_est == estatus_cur[0]:
                return
            estatus_cur[0] = new_est
            status_text.value = "Guardando..."
            status_text.color = ft.Colors.GREY_500
            page.update()

            def do_update():
                try:
                    from auth import get_client
                    client = get_client()
                    client.table("reportes_error").update({
                        "estatus": new_est,
                        "actualizado_en": "now()",
                    }).eq("id", reporte["id"]).execute()
                    reporte["estatus"] = new_est
                    status_text.value = "✓ Estatus actualizado"
                    status_text.color = ft.Colors.GREEN_400
                    build_list()
                except Exception:
                    status_text.value = "Error al actualizar"
                    status_text.color = ft.Colors.RED_400
                page.update()

            page.run_thread(do_update)

        estatus_dd.on_select = on_estatus_select

        bs = ft.BottomSheet(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text(nombre, size=15, weight=ft.FontWeight.BOLD),
                                        ft.Text(email, size=12, color=ft.Colors.GREY_500),
                                        ft.Text(fmt_date(reporte.get("creado_en", "")),
                                                size=11, color=ft.Colors.GREY_600),
                                    ],
                                    spacing=2, expand=True, tight=True,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CLOSE_ROUNDED,
                                    icon_color=ft.Colors.GREY_500,
                                    on_click=lambda e: _close(bs),
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        ft.Divider(height=1),
                        ft.Container(
                            content=ft.Text(reporte.get("mensaje", ""), size=13, no_wrap=False),
                            bgcolor=ft.Colors.with_opacity(0.05, primary_color),
                            border_radius=10,
                            padding=ft.Padding.all(12),
                        ),
                        ft.Container(height=8),
                        estatus_dd,
                        status_text,
                        ft.Container(height=8),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10,
                ),
                padding=ft.Padding.all(16),
            ),
            open=True,
        )

        page.overlay.append(bs)
        page.update()

    def _close(bs):
        bs.open = False
        if bs in page.overlay:
            page.overlay.remove(bs)
        page.update()

    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.ASSIGNMENT_ROUNDED, color=primary_color, size=24),
                ft.Text("Reportes", size=16, weight=ft.FontWeight.BOLD, expand=True),
                ft.IconButton(
                    icon=ft.Icons.REFRESH_ROUNDED,
                    icon_color=primary_color,
                    on_click=lambda e: load_reportes(),
                    tooltip="Actualizar",
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        border=ft.Border(
            bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.2, primary_color))
        ),
    )

    load_reportes()

    return ft.Container(
        content=ft.Column(
            controls=[header, content_area],
            expand=True,
            spacing=0,
        ),
        expand=True,
        on_click=handle_interaction,
    )
