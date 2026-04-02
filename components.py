"""
components.py — Widgets reutilizables de UI.
Sin dependencias de Supabase ni lógica de negocio.
"""

from typing import Callable, Optional
import flet as ft

ALIGN_CENTER = ft.alignment.Alignment(0, 0)


def mostrar_snackbar(page: ft.Page, mensaje: str, error: bool = False) -> None:
    try:
        sb = ft.SnackBar(
            open=True,
            content=ft.Text(mensaje),
            bgcolor=ft.Colors.ERROR_CONTAINER if error else None,
            action="OK",
        )
        page.overlay.append(sb)
        page.update()
    except Exception:
        pass


def estado_cargando(mensaje: str = "Cargando...") -> ft.Container:
    return ft.Container(
        expand=True, alignment=ALIGN_CENTER,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16,
            controls=[
                ft.ProgressRing(width=40, height=40, stroke_width=3),
                ft.Text(mensaje, color=ft.Colors.SECONDARY),
            ],
        ),
    )


def estado_vacio(titulo: str, subtitulo: str) -> ft.Container:
    return ft.Container(
        expand=True, alignment=ALIGN_CENTER,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12,
            controls=[
                ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, size=64, color=ft.Colors.OUTLINE),
                ft.Text(titulo, size=18, weight=ft.FontWeight.W_500,
                        color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(subtitulo, size=13, text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.OUTLINE),
            ],
        ),
    )


def estado_error(mensaje: str, on_reintentar: Callable) -> ft.Container:
    return ft.Container(
        expand=True, alignment=ALIGN_CENTER,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16,
            controls=[
                ft.Container(
                    padding=ft.Padding(20, 16, 20, 16),
                    border_radius=12,
                    bgcolor=ft.Colors.RED,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.CLOUD_OFF_OUTLINED, size=48,
                                    color=ft.Colors.BLACK),
                            ft.Text("Error de conexión", size=16,
                                    weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                            ft.Text(mensaje, size=12, text_align=ft.TextAlign.CENTER,
                                    color=ft.Colors.BLACK, max_lines=8),
                        ],
                    ),
                ),
                ft.Button("Reintentar", icon=ft.Icons.REFRESH,
                          on_click=lambda _: on_reintentar()),
            ],
        ),
    )


def tarjeta_producto(producto: dict) -> ft.Container:
    return ft.Container(
        margin=ft.Margin(0, 0, 0, 12),
        padding=ft.Padding(16, 16, 16, 16),
        border_radius=12,
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        border=ft.Border(
            left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            top=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
        ),
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(producto.get("codigo_completo", ""), size=18,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                        ft.Container(
                            padding=ft.Padding(8, 4, 8, 4),
                            border_radius=20,
                            bgcolor=ft.Colors.PRIMARY_CONTAINER,
                            content=ft.Text(producto.get("categoria_nombre", ""),
                                            size=11,
                                            color=ft.Colors.ON_PRIMARY_CONTAINER),
                        ),
                    ],
                ),
                ft.Text(producto.get("nombre", ""), size=15, weight=ft.FontWeight.W_500),
                ft.Text(producto.get("subcategoria_nombre", ""),
                        size=12, color=ft.Colors.SECONDARY),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Row(spacing=6, controls=[
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=14, color=ft.Colors.TERTIARY),
                    ft.Text(producto.get("mnemotecnia", ""), size=12, italic=True,
                            color=ft.Colors.ON_SURFACE_VARIANT, expand=True),
                ]),
            ],
        ),
    )


def campo_texto(
    label: str,
    icono: str,
    password: bool = False,
    on_change: Optional[Callable] = None,
    on_submit: Optional[Callable] = None,
) -> ft.TextField:
    return ft.TextField(
        label=label,
        prefix_icon=icono,
        password=password,
        can_reveal_password=password,
        border_radius=12,
        on_change=on_change,
        on_submit=on_submit,
        keyboard_type=(
            ft.KeyboardType.EMAIL if "correo" in label.lower()
            else ft.KeyboardType.TEXT
        ),
    )