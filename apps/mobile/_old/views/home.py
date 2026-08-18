import flet as ft


def home_view(
    page: ft.Page,
    user_email: str,
    username: str,
    time_offset: float,
    on_interaction,
    clock_text: ft.Text,
    primary_color,
):
    from session_manager import register_interaction

    def handle_interaction(e=None):
        register_interaction(time_offset)
        if on_interaction:
            on_interaction()

    # Actualizar estilo del clock_text para que combine con el diseño
    clock_text.size = 13
    clock_text.color = ft.Colors.with_opacity(0.6, primary_color)

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[

                            # ── Avatar / ícono con glow ───────────────────
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.HOME_ROUNDED,
                                    size=52,
                                    color=primary_color,
                                ),
                                width=96,
                                height=96,
                                border_radius=48,
                                bgcolor=ft.Colors.with_opacity(0.12, primary_color),
                                alignment=ft.Alignment(0, 0),
                            ),

                            ft.Container(height=8),

                            # ── Título ────────────────────────────────────
                            ft.Text(
                                value="Pantalla Principal",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                                color=ft.Colors.WHITE,
                            ),

                            # ── Bienvenida ────────────────────────────────
                            ft.Container(
                                content=ft.Text(
                                    value=f"Bienvenido, {username}",
                                    size=14,
                                    color=primary_color,
                                    text_align=ft.TextAlign.CENTER,
                                    weight=ft.FontWeight.W_500,
                                ),
                                bgcolor=ft.Colors.with_opacity(0.08, primary_color),
                                border_radius=20,
                                padding=ft.Padding.symmetric(horizontal=16, vertical=6),
                            ),

                            # ── Email ─────────────────────────────────────
                            ft.Text(
                                value=user_email,
                                size=12,
                                color=ft.Colors.GREY_600,
                                text_align=ft.TextAlign.CENTER,
                            ),

                            ft.Container(height=24),

                            # ── Cronómetro ────────────────────────────────
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.TIMER_OUTLINED,
                                            size=14,
                                            color=ft.Colors.with_opacity(0.6, primary_color),
                                        ),
                                        clock_text,
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=6,
                                ),
                                bgcolor=ft.Colors.with_opacity(0.06, primary_color),
                                border_radius=12,
                                padding=ft.Padding.symmetric(horizontal=16, vertical=8),
                            ),

                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                    on_click=handle_interaction,
                    padding=ft.Padding.symmetric(horizontal=24, vertical=16),
                ),
            ],
            expand=True,
        ),
        expand=True,
        on_click=handle_interaction,
    )