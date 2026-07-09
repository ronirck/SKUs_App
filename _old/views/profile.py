import flet as ft
import threading
from collections import defaultdict


def profile_view(
    page: ft.Page,
    user_id: str,
    user_email: str,
    username: str,
    time_offset: float,
    on_interaction,
    on_logout,
    primary_color,
    on_theme_change,
    rol: str = "user",
    clock_text: ft.Text = None,
    # kept for signature compatibility — not used (color is determined by sede)
    color_name: str = None,
    on_color_change=None,
):
    from session_manager import register_interaction

    def handle_interaction(e=None):
        register_interaction(time_offset)
        if on_interaction:
            on_interaction()

    # ─── Helpers de UI ────────────────────────────────────────────────────────

    def section_title(text: str):
        return ft.Row(
            controls=[
                ft.Container(width=3, height=14, bgcolor=primary_color, border_radius=2),
                ft.Text(text, size=13, weight=ft.FontWeight.W_600,
                        color=ft.Colors.with_opacity(0.7, primary_color)),
            ],
            spacing=8,
        )

    def styled_field(label, password=False):
        return ft.TextField(
            label=label,
            password=password,
            can_reveal_password=password,
            border_radius=12,
            expand=True,
            border_color=ft.Colors.with_opacity(0.3, primary_color),
            focused_border_color=primary_color,
            cursor_color=primary_color,
            label_style=ft.TextStyle(color=ft.Colors.GREY_500),
        )

    def card_container(content):
        return ft.Container(
            content=content,
            bgcolor=ft.Colors.with_opacity(0.04, primary_color),
            border_radius=12,
            padding=ft.Padding.all(12),
        )

    # ─── Sección: cambiar nombre ──────────────────────────────────────────────

    username_field = styled_field("Nombre de usuario")
    username_field.value = username
    status_username = ft.Text(value="", size=12, text_align=ft.TextAlign.CENTER)

    def handle_change_username(e):
        handle_interaction()
        val = username_field.value.strip() if username_field.value else ""
        if len(val) < 3:
            status_username.value = "Mínimo 3 caracteres"
            status_username.color = ft.Colors.RED_400
            page.update()
            return
        if val.lower() == username.lower():
            status_username.value = "Es el mismo nombre actual"
            status_username.color = ft.Colors.ORANGE_400
            page.update()
            return
        status_username.value = "Actualizando..."
        status_username.color = ft.Colors.GREY_500
        page.update()
        from auth import change_username
        result = change_username(user_id, val)
        if result["success"]:
            status_username.value = "✓ Nombre actualizado"
            status_username.color = ft.Colors.GREEN_400
        else:
            status_username.value = result.get("error", "Error al actualizar")
            status_username.color = ft.Colors.RED_400
        page.update()

    # ─── Sección: cambiar contraseña ──────────────────────────────────────────

    password_field = styled_field("Nueva contraseña", password=True)
    confirm_field = styled_field("Confirmar contraseña", password=True)
    status_password = ft.Text(value="", size=12, text_align=ft.TextAlign.CENTER)

    def handle_change_password(e):
        handle_interaction()
        if not password_field.value or not confirm_field.value:
            status_password.value = "Completa ambos campos"
            status_password.color = ft.Colors.RED_400
            page.update()
            return
        if len(password_field.value) < 6:
            status_password.value = "Mínimo 6 caracteres"
            status_password.color = ft.Colors.RED_400
            page.update()
            return
        if password_field.value != confirm_field.value:
            status_password.value = "Las contraseñas no coinciden"
            status_password.color = ft.Colors.RED_400
            page.update()
            return
        status_password.value = "Actualizando..."
        status_password.color = ft.Colors.GREY_500
        page.update()
        from auth import change_password
        result = change_password(password_field.value)
        if result["success"]:
            status_password.value = "✓ Contraseña actualizada"
            status_password.color = ft.Colors.GREEN_400
            password_field.value = ""
            confirm_field.value = ""
        else:
            status_password.value = result.get("error", "Error al cambiar")
            status_password.color = ft.Colors.RED_400
        page.update()

    # ─── Apariencia ───────────────────────────────────────────────────────────

    is_dark = page.theme_mode == ft.ThemeMode.DARK

    theme_switch = ft.Switch(
        label="Modo oscuro",
        value=is_dark,
        active_color=primary_color,
    )

    def handle_theme(e):
        handle_interaction()
        new_mode = ft.ThemeMode.DARK if theme_switch.value else ft.ThemeMode.LIGHT
        if on_theme_change:
            on_theme_change(new_mode)

    theme_switch.on_change = handle_theme

    # ─── Modal: reportar error ────────────────────────────────────────────────

    def open_reporte_modal(e):
        handle_interaction()

        msg_field = ft.TextField(
            label="Describe el error o problema que encontraste...",
            multiline=True,
            min_lines=4,
            max_lines=8,
            border_radius=12,
            border_color=ft.Colors.with_opacity(0.3, primary_color),
            focused_border_color=primary_color,
            expand=True,
        )
        modal_status = ft.Text(value="", size=12, text_align=ft.TextAlign.CENTER)
        send_btn = ft.Button(
            content=ft.Text("Enviar reporte", color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                bgcolor=primary_color,
            ),
            expand=True,
        )

        def handle_send(e):
            handle_interaction()
            msg = (msg_field.value or "").strip()
            if len(msg) < 10:
                modal_status.value = "El mensaje es muy corto (mínimo 10 caracteres)"
                modal_status.color = ft.Colors.RED_400
                page.update()
                return

            send_btn.disabled = True
            modal_status.value = "Enviando..."
            modal_status.color = ft.Colors.GREY_500
            page.update()

            def do_send():
                try:
                    from auth import get_client
                    client = get_client()
                    client.table("reportes_error").insert({
                        "usuario_id": user_id,
                        "mensaje": msg,
                        "estatus": "sin_revisar",
                    }).execute()
                    try:
                        client.table("notificaciones_admin").insert({
                            "tipo": "nuevo_registro",
                            "payload": {"nombre": username, "email": user_email,
                                        "tipo": "reporte_error"},
                        }).execute()
                    except Exception:
                        pass
                    modal_status.value = "✓ Reporte enviado exitosamente"
                    modal_status.color = ft.Colors.GREEN_400
                    msg_field.value = ""
                    send_btn.disabled = False
                    page.update()
                    page.show_dialog(
                        ft.SnackBar(content=ft.Text("Reporte enviado. ¡Gracias!"), open=True)
                    )
                except Exception:
                    modal_status.value = "Error al enviar. Intenta de nuevo."
                    modal_status.color = ft.Colors.RED_400
                    send_btn.disabled = False
                    page.update()

            threading.Thread(target=do_send, daemon=True).start()

        send_btn.on_click = handle_send

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Reportar error", weight=ft.FontWeight.BOLD),
            content=ft.Column(
                controls=[
                    ft.Text("Cuéntanos qué salió mal:", size=12, color=ft.Colors.GREY_500),
                    ft.Container(height=4),
                    msg_field,
                    modal_status,
                ],
                spacing=8,
                tight=True,
            ),
            actions=[
                ft.Button(
                    content=ft.Text("Cancelar", color=ft.Colors.GREY_500),
                    on_click=lambda e: _close_dlg(dlg),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.TRANSPARENT,
                        shadow_color=ft.Colors.TRANSPARENT,
                        overlay_color=ft.Colors.TRANSPARENT,
                    ),
                ),
                send_btn,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _close_dlg(dlg):
        dlg.open = False
        if dlg in page.overlay:
            page.overlay.remove(dlg)
        page.update()

    # ─── Estadísticas (solo rol user) ─────────────────────────────────────────

    stats_container = ft.Container()

    def load_stats():
        if rol != "user":
            return

        stats_container.content = ft.Container(
            content=ft.Row(
                controls=[ft.ProgressRing(width=20, height=20),
                          ft.Text("Cargando estadísticas...", size=12, color=ft.Colors.GREY_500)],
                spacing=8,
            ),
            padding=ft.Padding.only(top=8),
        )
        page.update()

        def do_load():
            try:
                from auth import get_client
                client = get_client()

                practica = (
                    client.table("resultados_codex")
                    .select("aciertos, fallos, total_preguntas, duracion_segundos")
                    .eq("usuario_id", user_id)
                    .neq("tipo_juego", "contrarreloj")
                    .execute()
                ).data or []

                contrarreloj = (
                    client.table("resultados_codex")
                    .select("aciertos, fallos, total_preguntas")
                    .eq("usuario_id", user_id)
                    .eq("tipo_juego", "contrarreloj")
                    .execute()
                ).data or []

                session_data = (
                    client.table("session_logs")
                    .select("duration_seconds")
                    .eq("user_id", user_id)
                    .execute()
                ).data or []

                errores = (
                    client.table("errores_partida")
                    .select("elemento_codigo, elemento_nombre, veces_fallado")
                    .eq("usuario_id", user_id)
                    .execute()
                ).data or []

                # Práctica
                total_practica = len(practica)
                total_aciertos_p = sum(r.get("aciertos", 0) for r in practica)
                total_preguntas_p = sum(r.get("total_preguntas", 0) for r in practica)
                efectividad_p = round(total_aciertos_p / total_preguntas_p * 100) if total_preguntas_p else 0
                tiempo_min = sum(s.get("duration_seconds", 0) for s in session_data) // 60

                # Contrarreloj
                total_cr = len(contrarreloj)
                record_cr = max((r.get("aciertos", 0) for r in contrarreloj), default=0)
                total_aciertos_cr = sum(r.get("aciertos", 0) for r in contrarreloj)
                total_preguntas_cr = sum(r.get("total_preguntas", 0) for r in contrarreloj)
                efectividad_cr = round(total_aciertos_cr / total_preguntas_cr * 100) if total_preguntas_cr else 0

                # Puntos ciegos
                err_map = defaultdict(lambda: {"nombre": "", "total": 0})
                for err in errores:
                    cod = err.get("elemento_codigo", "")
                    err_map[cod]["nombre"] = err.get("elemento_nombre", "")
                    err_map[cod]["total"] += err.get("veces_fallado", 1)
                top5 = sorted(err_map.items(), key=lambda x: x[1]["total"], reverse=True)[:5]

                def stat_card(label, value):
                    return ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(value, size=20, weight=ft.FontWeight.BOLD,
                                        color=primary_color, text_align=ft.TextAlign.CENTER),
                                ft.Text(label, size=10, color=ft.Colors.GREY_500,
                                        text_align=ft.TextAlign.CENTER, no_wrap=False),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=2,
                        ),
                        bgcolor=ft.Colors.with_opacity(0.06, primary_color),
                        border_radius=10,
                        padding=ft.Padding.symmetric(horizontal=6, vertical=10),
                        expand=True,
                    )

                if top5:
                    ciegos_rows = []
                    for cod, info in top5:
                        ciegos_rows.append(
                            ft.Row(
                                controls=[
                                    ft.Text(cod, size=11, weight=ft.FontWeight.W_600,
                                            color=primary_color, font_family="monospace", width=70),
                                    ft.Text(info["nombre"], size=11, expand=True, no_wrap=True),
                                    ft.Text(f"×{info['total']}", size=11,
                                            color=ft.Colors.RED_400, width=32,
                                            text_align=ft.TextAlign.RIGHT),
                                ],
                                spacing=8,
                            )
                        )
                    ciegos_widget = ft.Column(controls=ciegos_rows, spacing=6)
                else:
                    ciegos_widget = ft.Text(
                        "¡No hay errores frecuentes registrados!",
                        size=12, color=ft.Colors.GREEN_400, italic=True,
                    )

                stats_container.content = ft.Column(
                    controls=[
                        ft.Container(height=8),
                        section_title("Modo Práctica y Retos"),
                        ft.Container(height=6),
                        card_container(
                            ft.Row(
                                controls=[
                                    stat_card("Efectividad global", f"{efectividad_p}%"),
                                    stat_card("Estudio (min)", str(tiempo_min)),
                                    stat_card("Partidas", str(total_practica)),
                                ],
                                spacing=8,
                            )
                        ),
                        ft.Container(height=8),
                        section_title("Puntos Ciegos"),
                        ft.Container(height=6),
                        card_container(ciegos_widget),
                        ft.Container(height=8),
                        section_title("Modo Contrarreloj"),
                        ft.Container(height=6),
                        card_container(
                            ft.Row(
                                controls=[
                                    stat_card("Récord", str(record_cr)),
                                    stat_card("Efectividad", f"{efectividad_cr}%"),
                                    stat_card("Partidas", str(total_cr)),
                                ],
                                spacing=8,
                            )
                        ),
                    ],
                    spacing=0,
                )
                page.update()

            except Exception:
                stats_container.content = ft.Container()
                page.update()

        threading.Thread(target=do_load, daemon=True).start()

    # ─── Layout principal ──────────────────────────────────────────────────────

    controls = [
        ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE_ROUNDED,
                                        size=44, color=primary_color),
                        width=68, height=68, border_radius=34,
                        bgcolor=ft.Colors.with_opacity(0.12, primary_color),
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(username, size=15, weight=ft.FontWeight.BOLD),
                            ft.Text(user_email, size=11, color=ft.Colors.GREY_500),
                            *(
                                [ft.Container(
                                    content=ft.Text(
                                        "Administrador",
                                        size=10, color=primary_color,
                                        weight=ft.FontWeight.W_600,
                                    ),
                                    bgcolor=ft.Colors.with_opacity(0.12, primary_color),
                                    border_radius=8,
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                )]
                                if rol == "admin" else []
                            ),
                        ],
                        spacing=3,
                        tight=True,
                    ),
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.with_opacity(0.05, primary_color),
            border_radius=16,
            padding=ft.Padding.all(14),
        ),

        ft.Container(height=8),

        section_title("Apariencia"),
        card_container(theme_switch),
        ft.Container(height=8),
    ]

    # Estadísticas solo para users
    if rol == "user":
        controls.append(stats_container)
        controls.append(ft.Container(height=8))

    controls += [
        section_title("Cambiar nombre de usuario"),
        card_container(
            ft.Column(
                controls=[
                    ft.Row(controls=[username_field]),
                    status_username,
                    ft.Button(
                        content=ft.Text("Actualizar nombre", color=ft.Colors.WHITE,
                                        weight=ft.FontWeight.W_500),
                        on_click=handle_change_username,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                            bgcolor=primary_color,
                            overlay_color=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                        ),
                        expand=True,
                    ),
                ],
                spacing=8,
            )
        ),
        ft.Container(height=8),

        section_title("Cambiar contraseña"),
        card_container(
            ft.Column(
                controls=[
                    ft.Row(controls=[password_field]),
                    ft.Row(controls=[confirm_field]),
                    status_password,
                    ft.Button(
                        content=ft.Text("Actualizar contraseña", color=ft.Colors.WHITE,
                                        weight=ft.FontWeight.W_500),
                        on_click=handle_change_password,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                            bgcolor=primary_color,
                            overlay_color=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                        ),
                        expand=True,
                    ),
                ],
                spacing=8,
            )
        ),
        ft.Container(height=8),

        ft.Button(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.BUG_REPORT_OUTLINED, size=18, color=primary_color),
                    ft.Text("Reportar un error", color=primary_color, weight=ft.FontWeight.W_500),
                ],
                spacing=6,
                tight=True,
            ),
            on_click=open_reporte_modal,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                bgcolor=ft.Colors.with_opacity(0.06, primary_color),
                overlay_color=ft.Colors.with_opacity(0.1, primary_color),
                side=ft.BorderSide(color=ft.Colors.with_opacity(0.3, primary_color), width=1),
            ),
            expand=True,
        ),
        ft.Container(height=8),

        ft.Button(
            content=ft.Text("Cerrar sesión", color=ft.Colors.RED_400, weight=ft.FontWeight.W_500),
            on_click=lambda e: on_logout() if on_logout else None,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                bgcolor=ft.Colors.TRANSPARENT,
                side=ft.BorderSide(color=ft.Colors.RED_400, width=1.5),
                overlay_color=ft.Colors.with_opacity(0.08, ft.Colors.RED_400),
            ),
            expand=True,
        ),
        ft.Container(height=20),
    ]

    load_stats()

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=controls,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    expand=True,
                    on_click=handle_interaction,
                    padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                ),
            ],
            expand=True,
        ),
        expand=True,
    )
