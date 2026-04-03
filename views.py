# -*- coding: utf-8 -*-
"""
views.py
Arquitectura: cada tab del NavigationBar es una ft.View independiente.
Cambiar de tab = page.views.clear() + append(nueva_view) + update().
Este es el único patrón que funciona de forma confiable en Flet 0.82.
"""

import math
import time
from typing import Optional

import flet as ft

import auth
import database
import game_state as gs
import preferences
from components import (
    ALIGN_CENTER,
    campo_texto,
    estado_cargando,
    estado_error,
    estado_vacio,
    mostrar_snackbar,
    tarjeta_producto,
)


# ------------------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------------------

def _nav_bar(selected: int, page: ft.Page) -> ft.NavigationBar:
    """NavigationBar con 3 tabs: Catálogo, Desafíos, Perfil.
    InicioView (camino de niveles) comentada - implementar en versión futura."""
    def on_change(e):
        idx = int(e.control.selected_index)
        if idx != 0 and not preferences.get_sede():
            def cerrar_modal(_):
                dlg.open = False
                e.control.selected_index = 0
                page.update()
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Elige una casa primero"),
                content=ft.Text(
                    "Debes seleccionar tu casa en la Guía de Estudio "
                    "antes de acceder a los desafíos.",
                ),
                actions=[ft.TextButton("Entendido", on_click=cerrar_modal)],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(dlg)
            dlg.open = True
            e.control.selected_index = 0
            page.update()
            return
        if idx == 0: GuiaEstudioView(page).mount()
        elif idx == 1: DesafiosView(page).mount()
        elif idx == 2: PerfilView(page).mount()

    return ft.NavigationBar(
        selected_index=selected,
        bgcolor=ft.Colors.SURFACE,
        indicator_color=ft.Colors.PRIMARY_CONTAINER,
        on_change=on_change,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.MENU_BOOK_OUTLINED,
                selected_icon=ft.Icons.MENU_BOOK,
                label="Guía de Estudio",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.PSYCHOLOGY_ALT_OUTLINED,
                selected_icon=ft.Icons.PSYCHOLOGY_ALT,
                label="Desafíos",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.ACCOUNT_CIRCLE_OUTLINED,
                selected_icon=ft.Icons.ACCOUNT_CIRCLE,
                label="Perfil",
            ),
        ],
    )


def _get_logo_sede(page: ft.Page, height: int = 100) -> ft.Image:
    """Retorna el widget del logo oficial de la sede activa."""
    sede = preferences.get_sede()
    info = _SEDES_INFO.get(sede, _SEDES_INFO["Prisma"])
    return ft.Image(
        src=info["logo"],
        height=height,
        fit="contain",
    )

# Mapa sede → logo e ícono
_SEDES_INFO: dict[str, dict[str, str]] = {
    "Prisma":  {"logo": "Images/Prisma.png",  "ico": "Images/Prisma.ico"},
    "FEBECA":  {"logo": "Images/Febeca.png",  "ico": "Images/Febeca.ico"},
    "SILLACA": {"logo": "Images/Sillaca.png", "ico": "Images/Sillaca.ico"},
    "BEVAL":   {"logo": "Images/Beval.png",   "ico": "Images/Beval.ico"},
}

def _skeleton_catalogo() -> list[ft.Control]:
    """Placeholder visual mientras se cargan los productos del catálogo."""
    def _tile_skel():
        return ft.Container(
            margin=ft.Margin(16, 0, 16, 8),
            border_radius=12,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border=ft.Border(
                left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                top=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            ),
            content=ft.Container(
                padding=ft.Padding(12, 14, 12, 14),
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                content=ft.Row(spacing=10, controls=[
                    ft.Container(
                        width=36, height=36, border_radius=10,
                        bgcolor=ft.Colors.with_opacity(0.35, ft.Colors.ON_PRIMARY_CONTAINER),
                    ),
                    ft.Container(
                        expand=True, height=18, border_radius=6,
                        bgcolor=ft.Colors.with_opacity(0.22, ft.Colors.ON_PRIMARY_CONTAINER),
                    ),
                    ft.Container(
                        width=20, height=20, border_radius=10,
                        bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.ON_PRIMARY_CONTAINER),
                    ),
                ]),
            ),
        )

    return [ft.Container(height=8), *[_tile_skel() for _ in range(9)], ft.Container(height=24)]


def _montar(page: ft.Page, view: ft.View) -> None:
    """Reemplaza la vista actual. Patrón que funciona en Flet 0.82."""
    import auth as _auth
    _auth.registrar_actividad()   # cualquier navegación cuenta como actividad
    page.views.clear()
    page.views.append(view)
    page.update()

# -- Caché global del catálogo -------------------------------------------------
# Se carga una sola vez al iniciar la app y se reutiliza entre navegaciones.
_catalogo_cache: list[dict] = []
_catalogo_cargado: bool = False
# Caché de estructura agrupada y controles construidos
_catalogo_arbol_dict: dict = {}
_catalogo_tiles_cache: list[ft.Control] = []
# Modo vista especial "Infaltables Febeca"
_modo_infaltables_febeca: bool = False


def _precargar_catalogo(page) -> None:
    """Lanzar en background al iniciar la app para que el catálogo y desafíos están listos."""
    global _catalogo_cache, _catalogo_cargado
    try:
        # Cargar catálogo para la Guía de Estudio
        if not _catalogo_cargado:
            _catalogo_cache = database.fetch_productos()
            _catalogo_cargado = True
        
        # Precalentar la lista de productos (quiz la deriva en tiempo real, no necesita cache propio)
        # fetch_todos_para_quiz ya no tiene caché global; no es necesario precargarlo aquí.
    except Exception:
        pass




# ------------------------------------------------------------------------------
# TAB 0 - CATÁLOGO (árbol desplegable)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# TAB 1 - CATÁLOGO (árbol desplegable)
# ------------------------------------------------------------------------------

class GuiaEstudioView:
    """
    Catálogo con árbol desplegable de 3 niveles.
    Lazy loading: los productos de cada subcategoría se crean solo
    cuando el usuario abre esa subcategoría - no al construir el árbol.
    Los datos se leen del caché global _catalogo_cache para carga instantánea.
    """
    TAB = 0

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        sesion = auth.get_sesion()
        self._usuario_id = sesion.id if sesion else None
        self._area = ft.Column(
            expand=True,
            controls=[estado_cargando("Cargando catálogo...")],
        )
        self._sede_actual: str = preferences.get_sede()
        info = _SEDES_INFO.get(self._sede_actual, _SEDES_INFO["Prisma"])
        self._logo_img = ft.Image(
            src=info["logo"],
            height=120,
            fit="contain",
        )

    # -- Tiles -----------------------------------------------------------------

    def _producto_tile(self, p: dict) -> ft.Container:
        detalle = ft.Column(visible=False, spacing=0, controls=[
            ft.Container(
                padding=ft.Padding(16, 8, 16, 12),
                bgcolor=ft.Colors.SURFACE,
                content=ft.Row(spacing=8, controls=[
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=14,
                            color=ft.Colors.TERTIARY),
                    ft.Text(p.get("mnemotecnia") or "", size=12, italic=True,
                            color=ft.Colors.ON_SURFACE_VARIANT, expand=True),
                ]),
            )
        ])

        def toggle(_):
            detalle.visible = not detalle.visible
            self.page.update()

        return ft.Container(
            border=ft.Border(bottom=ft.BorderSide(0.5, ft.Colors.OUTLINE_VARIANT)),
            content=ft.Column(spacing=0, controls=[
                ft.Container(
                    padding=ft.Padding(16, 12, 16, 12),
                    on_click=toggle, ink=True,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(spacing=2, expand=True, controls=[
                                ft.Text(p.get("codigo_completo", ""), size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.PRIMARY),
                                ft.Text(p.get("nombre", ""), size=13),
                            ]),
                            # TODO: imagen desactivada — cada ft.Image dispara una
                            # descarga de red que congela la UI en Flet 0.82 con
                            # 100+ productos por subcategoría. Re-activar cuando
                            # se implemente carga diferida (lazy image loading).
                            ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=14,
                                    color=ft.Colors.OUTLINE),
                        ],
                    ),
                ),
                detalle,
            ]),
        )

    def _sub_tile(self, sub_cod: str, sub_nom: str,
                  productos: list[dict], abierto: bool = False,
                  sub_mnemo: str = "") -> ft.Container:
        """
        LAZY: prod_col empieza vacío, a menos que abierto=True.
        Muestra la mnemotecnia de la subcategoría al desplegarla.
        """
        prod_col  = ft.Column(visible=abierto, spacing=0, controls=[])
        icono     = ft.Icon(
            ft.Icons.KEYBOARD_ARROW_UP if abierto else ft.Icons.KEYBOARD_ARROW_DOWN,
            size=16, color=ft.Colors.OUTLINE)
        cargado   = [False]

        mnemo_panel = ft.Container(
            visible=abierto and bool(sub_mnemo),
            padding=ft.Padding(20, 8, 14, 10),
            bgcolor=ft.Colors.SECONDARY_CONTAINER,
            border=ft.Border(bottom=ft.BorderSide(0.5, ft.Colors.OUTLINE_VARIANT)),
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=13,
                            color=ft.Colors.SECONDARY),
                    ft.Text(sub_mnemo, size=12, italic=True,
                            color=ft.Colors.ON_SECONDARY_CONTAINER, expand=True),
                ],
            ),
        )

        def construir_productos():
            if not cargado[0]:
                ps = sorted(productos, key=lambda x: x.get("codigo", ""))
                prod_col.controls = [self._producto_tile(p) for p in ps]
                cargado[0] = True

        if abierto:
            construir_productos()

        def toggle(_):
            construir_productos()
            prod_col.visible = not prod_col.visible
            if sub_mnemo:
                mnemo_panel.visible = prod_col.visible
            icono.name = (ft.Icons.KEYBOARD_ARROW_UP if prod_col.visible
                          else ft.Icons.KEYBOARD_ARROW_DOWN)
            self.page.update()

        return ft.Container(
            border=ft.Border(bottom=ft.BorderSide(0.5, ft.Colors.OUTLINE_VARIANT)),
            content=ft.Column(spacing=0, controls=[
                ft.Container(
                    padding=ft.Padding(20, 12, 16, 12),
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    on_click=toggle, ink=True,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(spacing=10, expand=True, controls=[
                                ft.Container(width=6, height=6, border_radius=3,
                                             bgcolor=ft.Colors.SECONDARY),
                                ft.Text(f"{sub_cod}  -  {sub_nom}",
                                        size=13, weight=ft.FontWeight.W_500),
                            ]),
                            icono,
                        ],
                    ),
                ),
                mnemo_panel,
                prod_col,
            ]),
        )

    def _cat_tile(self, cat_cod: str, cat_nom: str,
                  arbol_subs: dict, abierto: bool = False,
                  sub_a_abrir: str = None, cat_mnemo: str = "") -> ft.Container:
        """
        LAZY: sub_col empieza vacío, a menos que abierto=True.
        Muestra la mnemotecnia de la categoría al desplegarla.
        """
        sub_col  = ft.Column(visible=abierto, spacing=0, controls=[])
        icono    = ft.Icon(
            ft.Icons.KEYBOARD_ARROW_UP if abierto else ft.Icons.KEYBOARD_ARROW_DOWN,
            size=20, color=ft.Colors.ON_PRIMARY_CONTAINER)
        cargado  = [False]

        mnemo_panel = ft.Container(
            visible=abierto and bool(cat_mnemo),
            padding=ft.Padding(14, 8, 14, 10),
            bgcolor=ft.Colors.TERTIARY_CONTAINER,
            border=ft.Border(bottom=ft.BorderSide(0.5, ft.Colors.OUTLINE_VARIANT)),
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=14,
                            color=ft.Colors.TERTIARY),
                    ft.Text(cat_mnemo, size=12, italic=True,
                            color=ft.Colors.ON_TERTIARY_CONTAINER, expand=True),
                ],
            ),
        )

        def construir_subs():
            if not cargado[0]:
                sub_col.controls = [
                    self._sub_tile(sc, arbol_subs[sc]["nombre"],
                                   arbol_subs[sc]["prods"],
                                   abierto=(sc == sub_a_abrir),
                                   sub_mnemo=arbol_subs[sc].get("mnemotecnia", ""))
                    for sc in sorted(arbol_subs)
                ]
                cargado[0] = True

        if abierto:
            construir_subs()

        def toggle(_):
            construir_subs()
            sub_col.visible = not sub_col.visible
            if cat_mnemo:
                mnemo_panel.visible = sub_col.visible
            icono.name = (ft.Icons.KEYBOARD_ARROW_UP if sub_col.visible
                          else ft.Icons.KEYBOARD_ARROW_DOWN)
            self.page.update()

        return ft.Container(
            margin=ft.Margin(16, 0, 16, 8),
            border_radius=12,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border=ft.Border(
                left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                top=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            ),
            content=ft.Column(spacing=0, controls=[
                ft.Container(
                    padding=ft.Padding(12, 14, 12, 14),
                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    on_click=toggle, ink=True,
                    content=ft.Row(spacing=10, controls=[
                        ft.Container(
                            width=36, height=36, border_radius=10,
                            bgcolor=ft.Colors.PRIMARY, alignment=ALIGN_CENTER,
                            content=ft.Text(cat_cod, size=13,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.ON_PRIMARY),
                        ),
                        ft.Text(cat_nom, size=15, weight=ft.FontWeight.W_500,
                                color=ft.Colors.ON_PRIMARY_CONTAINER, expand=True),
                        icono,
                    ]),
                ),
                mnemo_panel,
                sub_col,
            ]),
        )

    # -- Filtro por sede -------------------------------------------------------

    def _get_prods_sede(self) -> list[dict]:
        """Retorna los productos filtrados por la sede activa. Vacío si no hay sede."""
        if not self._sede_actual:
            return []
        sede_upper = self._sede_actual.strip().upper()
        if _modo_infaltables_febeca:
            return [
                p for p in _catalogo_cache
                if (p.get("sede") or "").upper() == "FEBECA"
                and p.get("imagen_url") not in (None, "", "null")
            ]
        return [p for p in _catalogo_cache if (p.get("sede") or "").upper() == sede_upper]

    def _ir_a_infaltables_febeca(self) -> None:
        """Activa la vista filtrada de productos FEBECA con imagen_url no nulo."""
        global _modo_infaltables_febeca, _catalogo_arbol_dict, _catalogo_tiles_cache
        from config import SEDE_COLORES
        _modo_infaltables_febeca = True
        # Guardar FEBECA como sede activa para que los lookups de cat/sub funcionen
        # y el nav bar permita acceder a Desafíos.
        preferences.set_sede("FEBECA")
        database.invalidar_cache_catalogo()
        database.re_enriquecer_productos()
        _catalogo_arbol_dict  = {}
        _catalogo_tiles_cache = []
        self.page.theme = ft.Theme(color_scheme_seed=SEDE_COLORES.get("FEBECA", "blue"))
        GuiaEstudioView(self.page).mount()

    def _ir_a_sede(self, sede: str) -> None:
        """Guarda la nueva sede, re-enriquece los productos y recarga la vista."""
        import os
        from config import SEDE_COLORES
        global _modo_infaltables_febeca
        venia_de_infaltables = _modo_infaltables_febeca
        _modo_infaltables_febeca = False  # salir del modo especial al elegir sede real
        if sede == self._sede_actual and not venia_de_infaltables:
            return
        preferences.set_sede(sede)
        # 1. Limpiar cachés de cats/subs → re-fetch desde Supabase
        database.invalidar_cache_catalogo()
        # 2. Re-enriquecer productos en memoria con los nuevos nombres
        database.re_enriquecer_productos()
        # 3. Limpiar cachés de controles Flet para que el árbol se reconstruya
        global _catalogo_arbol_dict, _catalogo_tiles_cache
        _catalogo_arbol_dict  = {}
        _catalogo_tiles_cache = []
        # 4. Actualizar ícono de ventana
        try:
            info = _SEDES_INFO.get(sede, _SEDES_INFO["Prisma"])
            if hasattr(self.page, "window"):
                self.page.window.icon = os.path.abspath(info["ico"])
        except Exception:
            pass
        # 5. Aplicar paleta de color de la sede
        color = SEDE_COLORES.get(sede, "blue")
        self.page.theme = ft.Theme(color_scheme_seed=color)
        GuiaEstudioView(self.page).mount()

    def _build_arbol(self, productos: list[dict],
                     cat_abierta: str = None,
                     sub_abierta: str = None) -> list[ft.Control]:
        global _catalogo_arbol_dict, _catalogo_tiles_cache
        
        # Si usamos el catálogo completo y ya tenemos los tiles cacheados...
        es_completo = (productos is _catalogo_cache)
        if es_completo and not cat_abierta and not sub_abierta and _catalogo_tiles_cache:
            return _catalogo_tiles_cache

        # Agrupar productos si no están en caché o si es una lista filtrada
        if es_completo and _catalogo_arbol_dict:
            arbol = _catalogo_arbol_dict
        else:
            # Obtener mnemotecnias de categorías (ya en caché de memoria, sin red)
            try:
                cats_data  = database.fetch_categorias()
                sede_upper = (self._sede_actual or "").strip().upper()
            except Exception:
                cats_data  = {}
                sede_upper = ""

            try:
                subs_data = database.fetch_subcategorias()
            except Exception:
                subs_data = {}

            arbol = {}
            for p in productos:
                cc, sc = p["categoria_codigo"], p["subcategoria_codigo"]
                if cc not in arbol:
                    cat_info = cats_data.get((sede_upper, cc)) or {}
                    arbol[cc] = {
                        "nombre":      p.get("categoria_nombre", cc) or cc,
                        "subs":        {},
                        "mnemotecnia": cat_info.get("mnemotecnia") or "",
                    }
                if sc not in arbol[cc]["subs"]:
                    sub_info = subs_data.get((sede_upper, cc, sc)) or {}
                    arbol[cc]["subs"][sc] = {
                        "nombre":      p.get("subcategoria_nombre", sc) or sc,
                        "prods":       [],
                        "mnemotecnia": sub_info.get("mnemotecnia") or "",
                    }
                arbol[cc]["subs"][sc]["prods"].append(p)

            if es_completo:
                _catalogo_arbol_dict = arbol

        tiles = [
            self._cat_tile(cc, arbol[cc]["nombre"], arbol[cc]["subs"],
                           cat_mnemo=arbol[cc].get("mnemotecnia", ""),
                           abierto=(cc == cat_abierta),
                           sub_a_abrir=sub_abierta if cc == cat_abierta else None)
            for cc in sorted(arbol)
        ]
        
        final_controls = [ft.Container(height=8), *tiles, ft.Container(height=24)]
        
        # Cachear controles si es el catálogo completo
        if es_completo and not cat_abierta and not sub_abierta:
            _catalogo_tiles_cache = final_controls
            
        return final_controls

    # -- Carga y mount ---------------------------------------------------------

    def _mostrar_arbol(self, productos: list[dict]) -> None:
        """Construye el árbol y lo muestra. Llama a page.update()."""
        import auth
        auth.registrar_inicio_uso()
        # Se elimina el registro de progreso individual por producto por ser 
        # incompatible con el nuevo esquema y extremadamente lento para 6500+ items.
        
        # Obtener controles del árbol
        controles_arbol = self._build_arbol(productos)
        
        self._lista_view.controls.clear()
        for c in controles_arbol:
            self._lista_view.controls.append(c)
        self.page.update()

    def _fetch(self) -> None:
        global _catalogo_cache, _catalogo_cargado

        # Sin sede seleccionada → mostrar indicación, no cargar nada
        if not self._sede_actual:
            self._lista_view.controls.clear()
            self._lista_view.controls.append(estado_vacio(
                "Elige tu casa",
                "Usa el menú desplegable para seleccionar tu sede.",
            ))
            self.page.update()
            return

        def _mostrar_o_error(prods):
            try:
                self._mostrar_arbol(prods)
            except Exception as exc:
                self._lista_view.controls.clear()
                self._lista_view.controls.append(estado_error(
                    str(exc),
                    on_reintentar=lambda: self.page.run_thread(self._fetch),
                ))
                self.page.update()
                raise

        try:
            if _catalogo_cargado and _catalogo_cache:
                # Cache en memoria listo — reconstruir controles frescos
                _mostrar_o_error(self._get_prods_sede())
                return

            # Mostrar skeleton mientras se espera la carga (red o disco)
            self._lista_view.controls.clear()
            for c in _skeleton_catalogo():
                self._lista_view.controls.append(c)
            self.page.update()

            productos = database.fetch_productos()
            if not productos:
                self._lista_view.controls.clear()
                self._lista_view.controls.append(estado_vacio(
                    "Sin productos", "Ejecuta el seed SQL en Supabase."))
                self.page.update()
                return
            _catalogo_cache   = productos
            _catalogo_cargado = True
            _mostrar_o_error(self._get_prods_sede())
        except Exception as exc:
            self._lista_view.controls.clear()
            self._lista_view.controls.append(estado_error(
                str(exc),
                on_reintentar=lambda: self.page.run_thread(self._fetch),
            ))
            self.page.update()

    def _refrescar(self) -> None:
        """Fuerza recarga desde Supabase ignorando el caché."""
        global _catalogo_cargado, _catalogo_arbol_dict, _catalogo_tiles_cache
        _catalogo_cargado = False
        _catalogo_arbol_dict = {}
        _catalogo_tiles_cache = []
        self._lista_view.controls.clear()
        self._lista_view.controls.append(estado_cargando("Actualizando catálogo..."))
        self.page.update()
        self.page.run_thread(self._fetch)

    def _aplicar_filtros(self, e=None) -> None:
        cat_txt = (self._filtro_cat.value or "").strip().lower()
        sub_txt = (self._filtro_sub.value or "").strip().lower()

        prods = self._get_prods_sede()
        cat_cod = None
        sub_cod = None

        # 1. Filtrar por Categoría
        if cat_txt:
            prods = [p for p in prods if cat_txt in p.get("categoria_nombre", "").lower()]
            if prods:
                cat_cod = prods[0]["categoria_codigo"]

        # 2. Filtrar por Subcategoría (Búsqueda de texto)
        if sub_txt:
            prods = [p for p in prods if sub_txt in p.get("subcategoria_nombre", "").lower()]
            if prods:
                # Si hay una coincidencia exacta o preferente, intentamos obtener el código
                # para expandir esa subcategoría específica
                exactas = [p for p in prods if p.get("subcategoria_nombre", "").lower() == sub_txt]
                res = exactas[0] if exactas else prods[0]
                cat_cod = res["categoria_codigo"]
                sub_cod = res["subcategoria_codigo"]

        # --- Reconstruir árbol ---
        nuevo_arbol = self._build_arbol(prods, cat_abierta=cat_cod, sub_abierta=sub_cod)
        self._lista_view.controls.clear()
        for c in nuevo_arbol:
            self._lista_view.controls.append(c)
        self.page.update()

    def _actualizar_sugerencias_cat(self, e) -> None:
        txt = self._filtro_cat.value.strip().lower()
        if not txt:
            self._sugerencias_cat_card.visible = False
            self.page.update()
            return

        # Obtener todas las categorías únicas
        cats_encontradas = sorted(list(set(
            p.get("categoria_nombre", "").strip()
            for p in self._get_prods_sede()
            if txt in p.get("categoria_nombre", "").lower()
        )))[:5]

        if not cats_encontradas:
            self._sugerencias_cat_card.visible = False
            self.page.update()
            return

        # Construir lista de sugerencias
        self._sugerencias_cat_view.controls = [
            ft.ListTile(
                title=ft.Text(s, size=13),
                dense=True,
                on_click=lambda _, s=s: self._seleccionar_sugerencia_cat(s)
            ) for s in cats_encontradas
        ]
        self._sugerencias_cat_card.visible = True
        self.page.update()

    def _seleccionar_sugerencia_cat(self, cat_nom: str) -> None:
        self._filtro_cat.value = cat_nom
        self._sugerencias_cat_card.visible = False
        self._aplicar_filtros()

    def _actualizar_sugerencias(self, e) -> None:
        txt = self._filtro_sub.value.strip().lower()
        if not txt:
            self._sugerencias_card.visible = False
            self.page.update()
            return

        cat_nom = self._filtro_cat.value

        # Obtener todas las subcategorías (filtrando por categoría si corresponde)
        prods = self._get_prods_sede()
        if cat_nom != "Todas las Categorías":
            prods = [p for p in prods if p.get("categoria_nombre", "").strip() == cat_nom]
        
        # Extraer nombres únicos que coincidan con el texto
        subs_encontradas = sorted(list(set(
            p.get("subcategoria_nombre", "").strip() 
            for p in prods 
            if txt in p.get("subcategoria_nombre", "").lower()
        )))[:8] # Limitar a 8 sugerencias

        if not subs_encontradas:
            self._sugerencias_card.visible = False
            self.page.update()
            return

        # Construir lista de sugerencias
        self._sugerencias_view.controls = [
            ft.ListTile(
                title=ft.Text(s, size=13),
                dense=True,
                on_click=lambda _, s=s: self._seleccionar_sugerencia(s)
            ) for s in subs_encontradas
        ]
        self._sugerencias_card.visible = True
        self.page.update()

    def _seleccionar_sugerencia(self, sub_nom: str) -> None:
        self._filtro_sub.value = sub_nom
        self._sugerencias_card.visible = False
        self._aplicar_filtros()

    def mount(self) -> None:
        global _catalogo_tiles_cache
        # Los controles Flet no se pueden reusar entre sesiones de vista distintas.
        # Limpiar la caché obliga a reconstruir controles frescos para este mount.
        _catalogo_tiles_cache = []

        self._filtro_cat = ft.TextField(
            label="Categoría (Escribe para buscar...):",
            hint_text="Ej: Electricidad",
            expand=True,
            text_size=13,
        )
        self._filtro_cat.on_submit = self._aplicar_filtros
        self._filtro_cat.on_change = self._actualizar_sugerencias_cat

        self._filtro_sub = ft.TextField(
            label="Subcategoría (Escribe para buscar...):",
            hint_text="Ej: Accesorios",
            expand=True,
            text_size=13,
        )
        self._filtro_sub.on_submit = self._aplicar_filtros
        self._filtro_sub.on_change = self._actualizar_sugerencias

        # Sugerencias Categoría
        self._sugerencias_cat_view = ft.Column(spacing=0)
        self._sugerencias_cat_card = ft.Container(
            visible=False,
            margin=ft.Margin(0, -8, 0, 0),
            padding=ft.Padding(4, 4, 4, 4),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=8,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)),
            content=self._sugerencias_cat_view
        )

        # Sugerencias
        self._sugerencias_view = ft.Column(spacing=0)
        self._sugerencias_card = ft.Container(
            visible=False,
            margin=ft.Margin(0, -8, 0, 0),
            padding=ft.Padding(4, 4, 4, 4),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=8,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)),
            content=self._sugerencias_view
        )

        self._lista_view = ft.ListView(
            expand=True, spacing=0,
            controls=[ft.Container(height=8)],
        )

        # PopupMenuButton: cada ítem tiene on_click propio → no depende de e.data del Dropdown
        if _modo_infaltables_febeca:
            _label_sede = "Infaltables Febeca"
        elif self._sede_actual:
            _label_sede = self._sede_actual
        else:
            _label_sede = None

        self._sede_btn = ft.PopupMenuButton(
            content=ft.Container(
                padding=ft.Padding(8, 6, 4, 6),
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=8,
                content=ft.Row(
                    spacing=2, tight=True,
                    controls=[
                        ft.Text(
                            _label_sede if _label_sede else "Elegir una casa",
                            size=13,
                            color=ft.Colors.ON_SURFACE if _label_sede
                                  else ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=18),
                    ],
                ),
            ),
            items=[
                ft.PopupMenuItem(
                    content="FEBECA",
                    on_click=lambda _: self._ir_a_sede("FEBECA"),
                ),
                ft.PopupMenuItem(
                    content="SILLACA",
                    on_click=lambda _: self._ir_a_sede("SILLACA"),
                ),
                ft.PopupMenuItem(
                    content="BEVAL",
                    on_click=lambda _: self._ir_a_sede("BEVAL"),
                ),
                ft.PopupMenuItem(),  # separador
                ft.PopupMenuItem(
                    content=ft.Row(spacing=8, controls=[
                        ft.Icon(ft.Icons.STAR_OUTLINED, size=16,
                                color=ft.Colors.AMBER_700),
                        ft.Text("Infaltables Febeca", size=13,
                                color=ft.Colors.AMBER_700),
                    ]),
                    on_click=lambda _: self._ir_a_infaltables_febeca(),
                ),
            ],
        )

        view = ft.View(
            route="/guia_estudio",
            padding=0,
            bgcolor=ft.Colors.SURFACE,
            navigation_bar=_nav_bar(self.TAB, self.page),
            controls=[
                ft.Column(
                    expand=True, spacing=0,
                    controls=[
                        ft.Container(
                            padding=ft.Padding(20, 48, 20, 12),
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                                controls=[
                                    ft.Column(spacing=2, expand=True, controls=[
                                        self._logo_img,
                                        ft.Text("Guía de Estudio: Códigos y Mnemotécnicas",
                                                size=13, weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.SECONDARY),
                                    ]),
                                    ft.Column(
                                        horizontal_alignment=ft.CrossAxisAlignment.END,
                                        spacing=4,
                                        controls=[
                                            ft.IconButton(icon=ft.Icons.REFRESH,
                                                          on_click=lambda _: self._refrescar()),
                                            self._sede_btn,
                                        ],
                                    ),
                                ],
                            ),
                        ),
                        # Estructura del Código (Informativo)
                        ft.Container(
                            margin=ft.Margin(16, 0, 16, 12),
                            padding=ft.Padding(12, 12, 12, 12),
                            bgcolor=ft.Colors.BLUE_50,
                            border=ft.Border.all(1, ft.Colors.BLUE_400),
                            border_radius=12,
                            content=ft.Row(spacing=16, controls=[
                                ft.Container(
                                    bgcolor=ft.Colors.BLUE_500,
                                    padding=ft.Padding(8, 6, 8, 6),
                                    border_radius=8,
                                    content=ft.Text("XX-XX-XXX", color=ft.Colors.WHITE,
                                                    weight=ft.FontWeight.BOLD, size=16),
                                ),
                                ft.Column(expand=True, spacing=2, controls=[
                                    ft.Text("Estructura del Código:", size=13,
                                            weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                                    ft.Row(spacing=4, controls=[
                                        ft.Text("XX", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800, size=12),
                                        ft.Text("Cat |", color=ft.Colors.BLUE_700, size=12),
                                        ft.Text("XX", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800, size=12),
                                        ft.Text("Sub |", color=ft.Colors.BLUE_700, size=12),
                                        ft.Text("XXX", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800, size=12),
                                        ft.Text("Prod", color=ft.Colors.BLUE_700, size=12),
                                    ]),
                                ]),
                            ]),
                        ),
                        # Filtros (Categoría + Subcategoría con Sugerencias)
                        ft.Container(
                            padding=ft.Padding(16, 0, 16, 12),
                            content=ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Column([
                                        self._filtro_cat,
                                        self._sugerencias_cat_card
                                    ], spacing=0),
                                    ft.Column([
                                        self._filtro_sub,
                                        self._sugerencias_card
                                    ], spacing=0)
                                ]
                            )
                        ),
                        # Resultados
                        self._lista_view,
                    ],
                )
            ],
        )
        _montar(self.page, view)
        self.page.run_thread(self._fetch)


# ------------------------------------------------------------------------------
# TAB 2 - DESAFÍOS
# ------------------------------------------------------------------------------

class DesafiosView:
    TAB = 1

    def __init__(self, page: ft.Page) -> None:
        self.page = page

    def _card(self, icono, titulo, subtitulo, descripcion,
              color, on_click=None, habilitado=True) -> ft.Container:
        return ft.Container(
            margin=ft.Margin(16, 0, 16, 12),
            padding=ft.Padding(20, 20, 20, 20),
            border_radius=16,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            opacity=1.0 if habilitado else 0.45,
            on_click=on_click if habilitado else None,
            ink=habilitado,
            border=ft.Border(
                left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                top=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            ),
            content=ft.Row(spacing=16, controls=[
                ft.Container(
                    width=56, height=56, border_radius=16,
                    bgcolor=color, alignment=ALIGN_CENTER,
                    content=ft.Icon(icono, size=28, color=ft.Colors.WHITE),
                ),
                ft.Column(expand=True, spacing=4, controls=[
                    ft.Text(titulo, size=16, weight=ft.FontWeight.W_500),
                    ft.Text(subtitulo, size=12, color=ft.Colors.SECONDARY),
                    ft.Text(descripcion, size=11, color=ft.Colors.OUTLINE),
                ]),
                ft.Icon(
                    ft.Icons.CHEVRON_RIGHT if habilitado else ft.Icons.LOCK_OUTLINE,
                    color=ft.Colors.OUTLINE),
            ]),
        )

    def mount(self) -> None:
        view = ft.View(
            route="/desafios",
            padding=0,
            bgcolor=ft.Colors.SURFACE,
            navigation_bar=_nav_bar(self.TAB, self.page),
            controls=[
                ft.Column(
                    expand=True, spacing=0,
                    controls=[
                        ft.Container(
                            padding=ft.Padding(20, 48, 20, 8),
                            content=ft.Column(spacing=2, controls=[
                                _get_logo_sede(self.page, 120),
                                ft.Text("Aprende los códigos de productos (SKU)",
                                        size=13, color=ft.Colors.SECONDARY),
                            ]),
                        ),
                        ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                        ft.ListView(
                            expand=True,
                            padding=ft.Padding(0, 12, 0, 12),
                            controls=[
                                self._card(
                                    icono=ft.Icons.CATEGORY_OUTLINED,
                                    titulo="Reto Categorías",
                                    subtitulo="Identifica la categoría principal",
                                    descripcion="Básico - Se muestra el inicio del código",
                                    color=ft.Colors.BLUE,
                                    on_click=lambda _: ConfigurarPartidaView(self.page, "categorias").mount(),
                                ),
                                self._card(
                                    icono=ft.Icons.ACCOUNT_TREE_OUTLINED,
                                    titulo="Reto Subcategorías",
                                    subtitulo="Identifica la subcategoría correcta",
                                    descripcion="Medio - Afina tu precisión con el inicio del código",
                                    color=ft.Colors.TEAL,
                                    on_click=lambda _: ConfigurarPartidaView(self.page, "subcategorias").mount(),
                                ),
                                self._card(
                                    icono=ft.Icons.QR_CODE_OUTLINED,
                                    titulo="Reto Código Productos",
                                    subtitulo="Nivel experto de memorización",
                                    descripcion="Dificultad alta - Selecciona el código completo",
                                    color=ft.Colors.DEEP_PURPLE,
                                    on_click=lambda _: ConfigurarPartidaView(self.page, "productos").mount(),
                                ),
                                ft.Container(height=12),
                                ft.Container(
                                    padding=ft.Padding(16, 0, 16, 8),
                                    content=ft.Text("ESPECIAL", size=11,
                                                    color=ft.Colors.OUTLINE,
                                                    weight=ft.FontWeight.W_500),
                                ),
                                self._card(
                                    icono=ft.Icons.TIMER_OUTLINED,
                                    titulo="Desafío (Categorías)",
                                    subtitulo="90 segundos para demostrar tu racha",
                                    descripcion="Contrarreloj - ¿Cuántas categorías logras responder¡",
                                    color=ft.Colors.RED_ACCENT_700,
                                    on_click=lambda _: ConfigurarPartidaView(self.page, "contrarreloj").mount(),
                                ),
                            ]
                        )
                    ],
                )
            ],
        )
        _montar(self.page, view)


# ------------------------------------------------------------------------------
# TAB 3 - PERFIL
# ------------------------------------------------------------------------------

class PerfilView:
    TAB = 2

    def __init__(self, page: ft.Page) -> None:
        self.page = page

    def _stat(self, valor, etiqueta, icono, color) -> ft.Container:
        return ft.Container(
            expand=True,
            padding=ft.Padding(14, 14, 14, 14),
            border_radius=14,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            content=ft.Column(spacing=6, controls=[
                ft.Icon(icono, size=22, color=color),
                ft.Text(str(valor), size=20, weight=ft.FontWeight.BOLD),
                ft.Text(etiqueta, size=11, color=ft.Colors.SECONDARY),
            ]),
        )

    def mount(self) -> None:
        sesion  = auth.get_sesion()
        nombre  = sesion.nombre if sesion else "Usuario"
        email   = sesion.email  if sesion else ""
        inicial = nombre[0].upper()

        def confirmar_cierre(_):
            def cancelar(e):
                d.open = False; self.page.update()
            def confirmar(e):
                d.open = False; self.page.update()
                
                import local_state as ls
                ls.limpiar()
                auth.cerrar_sesion()
                LoginView(self.page).mount()
            d = ft.AlertDialog(
                modal=True,
                title=ft.Text("¿Cerrar sesión?"),
                content=ft.Text("Tendrás que volver a iniciar sesión."),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancelar),
                    ft.TextButton("Cerrar sesión",
                                  style=ft.ButtonStyle(color=ft.Colors.ERROR),
                                  on_click=confirmar),
                ],
            )
            self.page.overlay.append(d)
            d.open = True
            self.page.update()

        view = ft.View(
            route="/perfil",
            padding=0,
            bgcolor=ft.Colors.SURFACE,
            navigation_bar=_nav_bar(self.TAB, self.page),
            controls=[
                ft.Column(
                    expand=True, spacing=0,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Container(
                            padding=ft.Padding(20, 48, 20, 24),
                            bgcolor=ft.Colors.PRIMARY_CONTAINER,
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=12,
                                controls=[
                                    ft.Container(
                                        width=80, height=80, border_radius=40,
                                        bgcolor=ft.Colors.PRIMARY,
                                        alignment=ALIGN_CENTER,
                                        content=ft.Text(
                                            inicial, size=32,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.ON_PRIMARY),
                                    ),
                                    ft.Text(nombre, size=20,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.ON_PRIMARY_CONTAINER),
                                    ft.Text(email, size=13,
                                            color=ft.Colors.ON_PRIMARY_CONTAINER),
                                ],
                            ),
                        ),
                        ft.Container(height=8),
                        ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                        ft.Container(height=8),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.LOGOUT,
                                            color=ft.Colors.ERROR),
                            title=ft.Text("Cerrar sesión",
                                          color=ft.Colors.ERROR),
                            on_click=confirmar_cierre,
                        ),
                        ft.Container(expand=True),
                    ],
                )
            ],
        )
        _montar(self.page, view)


# ------------------------------------------------------------------------------
# LOGIN VIEW
# ------------------------------------------------------------------------------

class LoginView:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self._cargando = False
        self._campo_email = campo_texto(
            label="Correo electrónico", icono=ft.Icons.EMAIL_OUTLINED,
            on_submit=lambda _: self._iniciar_login(),
        )
        self._campo_password = campo_texto(
            label="Contraseña", icono=ft.Icons.LOCK_OUTLINE,
            password=True, on_submit=lambda _: self._iniciar_login(),
        )
        self._btn = ft.Button(
            "Iniciar sesión", icon=ft.Icons.LOGIN,
            expand=True, on_click=lambda _: self._iniciar_login(),
        )
        self._indicador = ft.ProgressBar(visible=False)

    def _set_cargando(self, estado: bool) -> None:
        self._cargando = estado
        self._btn.disabled = estado
        self._indicador.visible = estado
        self._campo_email.disabled = estado
        self._campo_password.disabled = estado
        self.page.update()

    def _iniciar_login(self) -> None:
        if self._cargando:
            return
        self._set_cargando(True)
        self.page.run_thread(self._hacer_login)

    def _hacer_login(self) -> None:
        try:
            resultado = auth.intentar_login(
                email=self._campo_email.value or "",
                password=self._campo_password.value or "",
            )
            if resultado.exitoso:
                # Arrancar descarga de productos en background inmediatamente,
                # antes de que la GuiaEstudioView la solicite.
                self.page.run_thread(database.fetch_productos)
                GuiaEstudioView(self.page).mount()
            else:
                mostrar_snackbar(self.page, resultado.mensaje, error=True)
                self._set_cargando(False)
        except Exception as exc:
            mostrar_snackbar(self.page, f"Error: {exc}", error=True)
            self._set_cargando(False)

    def mount(self) -> None:
        view = ft.View(
            route="/", scroll=None, padding=0,
            bgcolor=ft.Colors.SURFACE,
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[ft.Container(
                width=340, padding=ft.Padding(24, 24, 24, 24),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                    controls=[
                        _get_logo_sede(self.page, 120),
                        ft.Text("Códigos de Producto", size=22,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER),
                        ft.Text("Inicia sesión para continuar", size=14,
                                color=ft.Colors.SECONDARY,
                                text_align=ft.TextAlign.CENTER),
                        ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                        self._campo_email,
                        self._campo_password,
                        self._indicador,
                        ft.Row(controls=[self._btn]),
                        ft.TextButton(
                            "¿No tienes cuenta? Crear usuario",
                            on_click=lambda _: RegistroView(self.page).mount(),
                        ),
                    ],
                ),
            )],
        )
        _montar(self.page, view)


# ------------------------------------------------------------------------------
# REGISTRO VIEW
# ------------------------------------------------------------------------------

class RegistroView:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self._cargando = False
        self._campo_nombre   = campo_texto(label="Nombre completo",
                                           icono=ft.Icons.PERSON_OUTLINE)
        self._campo_email    = campo_texto(label="Correo electrónico",
                                           icono=ft.Icons.EMAIL_OUTLINED)
        self._campo_password = campo_texto(
            label="Contraseña", icono=ft.Icons.LOCK_OUTLINE, password=True,
            on_submit=lambda _: self._iniciar_registro())
        self._btn = ft.Button("Crear usuario", icon=ft.Icons.PERSON_ADD,
                              expand=True,
                              on_click=lambda _: self._iniciar_registro())
        self._indicador = ft.ProgressBar(visible=False)

    def _set_cargando(self, estado: bool) -> None:
        self._cargando = estado
        self._btn.disabled = estado
        self._indicador.visible = estado
        for c in [self._campo_nombre, self._campo_email, self._campo_password]:
            c.disabled = estado
        self.page.update()

    def _iniciar_registro(self) -> None:
        if self._cargando:
            return
        self._set_cargando(True)
        self.page.run_thread(self._hacer_registro)

    def _hacer_registro(self) -> None:
        try:
            resultado = auth.registrar_usuario(
                nombre=self._campo_nombre.value or "",
                email=self._campo_email.value or "",
                password=self._campo_password.value or "",
            )
            if resultado.exitoso:
                mostrar_snackbar(self.page, resultado.mensaje)
                LoginView(self.page).mount()
            else:
                mostrar_snackbar(self.page, resultado.mensaje, error=True)
                self._set_cargando(False)
        except Exception as exc:
            mostrar_snackbar(self.page, f"Error: {exc}", error=True)
            self._set_cargando(False)

    def mount(self) -> None:
        view = ft.View(
            route="/registro", scroll=None, padding=0,
            bgcolor=ft.Colors.SURFACE,
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.AppBar(
                    title=ft.Text("Crear usuario", weight=ft.FontWeight.W_500),
                    bgcolor=ft.Colors.SURFACE,
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: LoginView(self.page).mount()),
                ),
                ft.Container(
                    width=340, padding=ft.Padding(24, 24, 24, 24),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20,
                        controls=[
                            self._campo_nombre, self._campo_email,
                            self._campo_password, self._indicador,
                            ft.Row(controls=[self._btn]),
                        ],
                    ),
                ),
            ],
        )
        _montar(self.page, view)


# ------------------------------------------------------------------------------
# CONFIGURAR PARTIDA
# ------------------------------------------------------------------------------

class ConfigurarPartidaView:
    def __init__(self, page: ft.Page, modo: str) -> None:
        self.page  = page
        self.modo  = modo
        self._num_opciones = 4
        self._data = None
        self._area = ft.Container(expand=True,
                                  content=estado_cargando("Cargando..."))

    def _titulo(self):
        return {
            "categorias":    "Reto Categorías",
            "subcategorias": "Reto Subcategorías",
            "productos":     "Reto Código Productos",
            "contrarreloj":  "Desafío (Categorías)"
        }.get(self.modo, "Reto")

    def _icono(self):
        return {
            "categorias":    ft.Icons.CATEGORY_OUTLINED,
            "subcategorias": ft.Icons.ACCOUNT_TREE_OUTLINED,
            "productos":     ft.Icons.QR_CODE_OUTLINED,
            "contrarreloj":  ft.Icons.TIMER_OUTLINED
        }.get(self.modo, ft.Icons.EXTENSION_OUTLINED)

    def _color(self):
        return {
            "categorias":    ft.Colors.BLUE,
            "subcategorias": ft.Colors.TEAL,
            "productos":     ft.Colors.DEEP_PURPLE,
            "contrarreloj":  ft.Colors.RED_ACCENT_700
        }.get(self.modo, ft.Colors.PRIMARY)

    def _descripcion(self):
        return {
            "categorias":    "Se te mostrará el inicio de un código y deberás seleccionar a qué categoría principal pertenece.",
            "subcategorias": "Deberás identificar la subcategoría correcta dado un código.",
            "productos":     "El nivel experto. Se muestra el nombre de un producto y debes seleccionar su código correcto.",
            "contrarreloj":  "Una prueba contrarreloj donde debes responder la mayor cantidad de categorías en 90 segundos."
        }.get(self.modo, "")

    def _build_selector(self) -> ft.Column:
        txt = ft.Text(f"{self._num_opciones} opciones", size=32,
                      weight=ft.FontWeight.BOLD, color=self._color(),
                      text_align=ft.TextAlign.CENTER)

        def on_change(e):
            # En Flet, e.control.selected suele ser un set. Lo convertimos a lista.
            seleccion = list(e.control.selected)
            if seleccion:
                self._num_opciones = int(seleccion[0])
                # Forzamos que la selección sea una lista para evitar crash de serialización msgpack
                e.control.selected = [str(self._num_opciones)]
                txt.value = f"{self._num_opciones} opciones"
                self.page.update()

        selector = ft.SegmentedButton(
            selected=[str(self._num_opciones)],
            on_change=on_change,
            segments=[
                ft.Segment(value="2", label=ft.Text("2")),
                ft.Segment(value="4", label=ft.Text("4")),
                ft.Segment(value="6", label=ft.Text("6")),
                ft.Segment(value="8", label=ft.Text("8")),
            ],
            style=ft.ButtonStyle(
                color={"selected": ft.Colors.WHITE, "": self._color()},
                bgcolor={"selected": self._color()},
            )
        )

        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=24,
            controls=[
                ft.Container(width=80, height=80, border_radius=24,
                             bgcolor=ft.Colors.SURFACE_CONTAINER,
                             alignment=ALIGN_CENTER,
                             content=ft.Icon(self._icono(), size=44,
                                             color=self._color())),
                ft.Text(self._titulo(), size=24, weight=ft.FontWeight.BOLD),
                ft.Text(self._descripcion(), size=14, color=ft.Colors.SECONDARY,
                        text_align=ft.TextAlign.CENTER),
                ft.Divider(color=ft.Colors.OUTLINE_VARIANT),
                ft.Text("Selecciona la dificultad", size=14,
                        color=ft.Colors.SECONDARY),
                txt,
                selector,
                ft.Container(height=10),
                ft.Button("Comenzar", icon=ft.Icons.PLAY_ARROW,
                          expand=True, on_click=lambda _: self._iniciar()),
            ],
        )

    def _fetch(self) -> None:
        try:
            sesion = auth.get_sesion()
            if not sesion:
                LoginView(self.page).mount()
                return
            sede = preferences.get_sede()
            if not sede:
                self._area.content = estado_vacio(
                    "Elige tu casa",
                    "Ve a la Guía de Estudio y selecciona tu sede antes de iniciar un desafío.",
                )
                self.page.update()
                return
            self._data = database.fetch_todos_para_quiz(sede)
            self._area.content = self._build_selector()
        except Exception as exc:
            self._area.content = estado_error(
                str(exc),
                on_reintentar=lambda: self.page.run_thread(self._fetch))
        finally:
            self.page.update()

    def _iniciar(self) -> None:
        if self.modo == "contrarreloj":
            DesafioContrarrelojView(self.page, gs.crear_partida_contrarreloj(
                self._data, self._num_opciones)).mount()
        else:
            # Categorias, Subcategorias, Productos
            QuizView(self.page, gs.crear_partida_quiz(
                self._data, 10, self.modo, self._num_opciones), self.modo).mount()

    def mount(self) -> None:
        view = ft.View(
            route="/configurar", padding=0, bgcolor=ft.Colors.SURFACE,
            controls=[
                ft.AppBar(
                    title=_get_logo_sede(self.page, 22),
                    bgcolor=ft.Colors.SURFACE,
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: DesafiosView(self.page).mount()),
                ),
                ft.Container(expand=True,
                             padding=ft.Padding(16, 24, 16, 16),
                             content=self._area),
            ],
        )
        _montar(self.page, view)
        self.page.run_thread(self._fetch)


# ------------------------------------------------------------------------------
# QUIZ VIEW
# ------------------------------------------------------------------------------

class QuizView:
    def __init__(self, page: ft.Page, partida: gs.EstadoQuiz, modo: str) -> None:
        self.page    = page
        self.partida = partida
        self.modo    = modo
        self._bloqueado = False
        self._area = ft.Container(expand=True)

    def _tipo_label(self, tipo):
        return {
            gs.TipoPreguntaQuiz.CATEGORIA:    "¿A qué categoría principal pertenece?",
            gs.TipoPreguntaQuiz.SUBCATEGORIA: "¿A qué subcategoría pertenece?",
            gs.TipoPreguntaQuiz.PRODUCTO:     "¿Cuál es el código completo?",
        }[tipo]

    def _color(self):
        return {
            "categorias":    ft.Colors.BLUE,
            "subcategorias": ft.Colors.TEAL,
            "productos":     ft.Colors.DEEP_PURPLE
        }.get(self.modo, ft.Colors.PRIMARY)

    def _mostrar_pregunta(self) -> None:
        self._bloqueado = False
        pregunta = self.partida.pregunta_actual
        if pregunta is None:
            ResultadoQuizView(self.page, self.partida, self.modo).mount()
            return

        botones_map: dict[str, ft.OutlinedButton] = {}
        feedback = ft.Container(visible=False, border_radius=10)

        def on_opcion(opcion: str) -> None:
            if self._bloqueado:
                return
            self._bloqueado = True
            correcta = self.partida.responder(opcion)
            for op, btn in botones_map.items():
                btn.disabled = True
                if op == pregunta.respuesta_correcta:
                    btn.style = ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE)
                elif op == opcion and not correcta:
                    btn.style = ft.ButtonStyle(
                        bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
            feedback.visible = True
            if correcta:
                feedback.bgcolor = ft.Colors.GREEN_100
                feedback.padding = ft.Padding(12, 12, 12, 12)
                feedback.content = ft.Row(spacing=8, controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=20),
                    ft.Text("¡Correcto!", color=ft.Colors.GREEN_900,
                            size=14, weight=ft.FontWeight.W_500),
                ])
            else:
                feedback.bgcolor = ft.Colors.ORANGE_100
                feedback.padding = ft.Padding(12, 12, 12, 12)
                feedback.content = ft.Column(spacing=6, controls=[
                    ft.Row(spacing=8, controls=[
                        ft.Icon(ft.Icons.CANCEL, color=ft.Colors.RED, size=20),
                        ft.Text("Incorrecto", color=ft.Colors.RED_900,
                                size=14, weight=ft.FontWeight.W_500),
                    ]),
                    ft.Row(spacing=6, controls=[
                        ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=14,
                                color=ft.Colors.ORANGE),
                        ft.Text(pregunta.mnemotecnia, size=12, italic=True,
                                color=ft.Colors.ORANGE_900, expand=True),
                    ]),
                ])
            self.page.update()

            def avanzar():
                time.sleep(1.0)
                if self.partida.terminado:
                    ResultadoQuizView(self.page, self.partida, self.modo).mount()
                else:
                    self._mostrar_pregunta()
                    self.page.update()
            self.page.run_thread(avanzar)

        filas = []
        opciones = pregunta.opciones
        # Mostrar en columnas de 2
        for i in range(0, len(opciones), 2):
            fila = []
            for op in opciones[i:i+2]:
                btn = ft.OutlinedButton(
                    op, expand=True,
                    on_click=lambda e, o=op: on_opcion(o),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=12)),
                )
                botones_map[op] = btn
                fila.append(btn)
            filas.append(ft.Row(spacing=8, controls=fila))

        self._area.content = ft.Column(
            expand=True, spacing=16,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"Pregunta {self.partida.progreso}",
                                size=13, color=ft.Colors.SECONDARY),
                        ft.Row(spacing=12, controls=[
                            ft.Row(spacing=4, controls=[
                                ft.Icon(ft.Icons.CHECK_CIRCLE, size=14,
                                        color=ft.Colors.GREEN),
                                ft.Text(str(self.partida.aciertos), size=13,
                                        color=ft.Colors.GREEN,
                                        weight=ft.FontWeight.W_500),
                            ]),
                            ft.Row(spacing=4, controls=[
                                ft.Icon(ft.Icons.CANCEL, size=14,
                                        color=ft.Colors.RED),
                                ft.Text(str(self.partida.errores), size=13,
                                        color=ft.Colors.RED,
                                        weight=ft.FontWeight.W_500),
                            ]),
                        ]),
                    ],
                ),
                ft.ProgressBar(
                    value=self.partida.indice_actual / self.partida.total_preguntas,
                    color=self._color(), bgcolor=ft.Colors.OUTLINE_VARIANT),
                ft.Text(self._tipo_label(pregunta.tipo), size=12,
                        color=ft.Colors.SECONDARY,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(
                    padding=ft.Padding(20, 20, 20, 20), border_radius=16,
                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    content=ft.Text(pregunta.enunciado, size=22,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.ON_PRIMARY_CONTAINER,
                                    text_align=ft.TextAlign.CENTER),
                ),
                *filas,
                feedback,
            ],
        )
        self.page.update()

    def _confirmar_salida(self, _) -> None:
        def cerrar(e): d.open = False; self.page.update()
        def confirmar(e):
            d.open = False; self.page.update()
            DesafiosView(self.page).mount()
        d = ft.AlertDialog(
            modal=True, title=ft.Text("¿Abandonar?"),
            content=ft.Text("Se perderá el progreso."),
            actions=[ft.TextButton("Cancelar", on_click=cerrar),
                     ft.TextButton("Abandonar", on_click=confirmar)],
        )
        self.page.overlay.append(d)
        d.open = True
        self.page.update()

    def mount(self) -> None:
        view = ft.View(
            route="/quiz", padding=0, bgcolor=ft.Colors.SURFACE,
            controls=[
                ft.AppBar(
                    title=_get_logo_sede(self.page, 22), 
                    bgcolor=ft.Colors.SURFACE,
                    leading=ft.IconButton(icon=ft.Icons.CLOSE,
                                          on_click=self._confirmar_salida),
                ),
                ft.Container(expand=True, padding=ft.Padding(16, 8, 16, 16),
                             content=self._area),
            ],
        )
        _montar(self.page, view)
        self._mostrar_pregunta()


# ------------------------------------------------------------------------------
# RESULTADO QUIZ
# ------------------------------------------------------------------------------

class ResultadoQuizView:
    def __init__(self, page: ft.Page, partida: gs.EstadoQuiz, modo: str) -> None:
        self.page = page; self.partida = partida; self.modo = modo



    def mount(self) -> None:
        pct = self.partida.porcentaje
        emoji, msg = (("🏆", "¡Excelente!") if pct >= 80
                      else ("👍", "¡Buen trabajo!") if pct >= 50
                      else ("💪", "Sigue practicando"))
        view = ft.View(
            route="/resultado_quiz", scroll=ft.ScrollMode.AUTO,
            padding=ft.Padding(16, 0, 16, 16), bgcolor=ft.Colors.SURFACE,
            controls=[
                ft.AppBar(title=_get_logo_sede(self.page, 22),
                          bgcolor=ft.Colors.SURFACE,
                          automatically_imply_leading=False),
                ft.Container(
                    padding=ft.Padding(24, 24, 24, 24), border_radius=20,
                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=18,
                        controls=[
                            ft.Text(emoji, size=52, text_align=ft.TextAlign.CENTER),
                            ft.Text(msg, size=18, weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.ON_PRIMARY_CONTAINER,
                                    text_align=ft.TextAlign.CENTER),
                            ft.Row(alignment=ft.MainAxisAlignment.CENTER,
                                   spacing=20, controls=[
                                ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                          spacing=2, controls=[
                                    ft.Text(str(self.partida.aciertos), size=28,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.GREEN),
                                    ft.Text("correctas", size=12,
                                            color=ft.Colors.ON_PRIMARY_CONTAINER),
                                ]),
                                ft.Text("|", size=28,
                                        color=ft.Colors.ON_PRIMARY_CONTAINER),
                                ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                          spacing=2, controls=[
                                    ft.Text(str(self.partida.errores), size=28,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.RED),
                                    ft.Text("incorrectas", size=12,
                                            color=ft.Colors.ON_PRIMARY_CONTAINER),
                                ]),
                            ]),
                            ft.Text(f"{pct}% de aciertos", size=16,
                                    weight=ft.FontWeight.W_500,
                                    color=ft.Colors.ON_PRIMARY_CONTAINER),
                        ],
                    ),
                ),

                ft.Button("Jugar otra vez", icon=ft.Icons.REPLAY, expand=True,
                          on_click=lambda _: ConfigurarPartidaView(
                              self.page, self.modo).mount()),
                ft.Container(height=8),
                ft.OutlinedButton("Volver", icon=ft.Icons.HOME_OUTLINED,
                                  expand=True,
                                  on_click=lambda _: DesafiosView(
                                      self.page).mount()),
            ],
        )
        _montar(self.page, view)

        # Completar un desafío cuenta como actividad
        auth.registrar_actividad()


# ------------------------------------------------------------------------------
# DESAFÍO CONTRARRELOJ (VIEW)
# ------------------------------------------------------------------------------

class DesafioContrarrelojView:
    def __init__(self, page: ft.Page, partida: gs.EstadoContrarreloj) -> None:
        self.page    = page
        self.partida = partida
        self._bloqueado = False
        self._timer_running = False
        self._timer_txt = ft.Text("90s", size=24, weight=ft.FontWeight.BOLD,
                                  color=ft.Colors.RED_ACCENT_700)
        self._area = ft.Container(expand=True)

    def _update_timer(self):
        self._timer_running = True
        while self.partida.segundos_restantes > 0 and self._timer_running:
            time.sleep(1)
            self.partida.segundos_restantes -= 1
            self._timer_txt.value = f"{self.partida.segundos_restantes}s"
            if self.partida.segundos_restantes <= 10:
                self._timer_txt.color = ft.Colors.RED
            self.page.update()
        
        if self._timer_running:
            self._timer_running = False
            ResultadoContrarrelojView(self.page, self.partida).mount()

    def _mostrar_pregunta(self) -> None:
        self._bloqueado = False
        pregunta = self.partida.pregunta_actual
        if pregunta is None or self.partida.segundos_restantes <= 0:
            self._timer_running = False
            # Evitar doble montaje si el timer ya disparó
            if "/resultado_contrarreloj" not in self.page.route:
                ResultadoContrarrelojView(self.page, self.partida).mount()
            return

        # Pista de mnemotecnia (oculta hasta el primer error)
        pista = ft.Container(
            visible=False,
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=12,
            bgcolor=ft.Colors.AMBER_50,
            border=ft.Border.all(1, ft.Colors.AMBER_300),
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE,
                            color=ft.Colors.AMBER_700, size=18),
                    ft.Text(
                        pregunta.mnemotecnia,
                        size=13, color=ft.Colors.AMBER_900,
                        expand=True,
                    ),
                ],
            ),
        )

        # Mapa opcion → botón para poder colorearlo al fallar
        botones: dict[str, ft.OutlinedButton] = {}
        for op in pregunta.opciones:
            botones[op] = ft.OutlinedButton(
                op, expand=True,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            )

        def on_opcion(opcion: str) -> None:
            if self._bloqueado:
                return
            self._bloqueado = True
            correcta = self.partida.responder(opcion)

            if correcta:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("+1 Punto", weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.GREEN, duration=600)
                self.page.snack_bar.open = True
                self.page.update()
                self._mostrar_pregunta()
            else:
                # Marcar botón erróneo en rojo
                botones[opcion].style = ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.RED_400,
                    shape=ft.RoundedRectangleBorder(radius=12),
                )
                # Mostrar pista y desbloquear para reintentar
                pista.visible = True
                self._bloqueado = False
                self.page.update()

        for op, btn in botones.items():
            btn.on_click = lambda e, o=op: on_opcion(o)

        filas = []
        ops = list(botones.values())
        for i in range(0, len(ops), 2):
            filas.append(ft.Row(spacing=8, controls=ops[i:i+2]))

        self._area.content = ft.Column(
            expand=True, spacing=16, scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(spacing=2, controls=[
                            ft.Text("Puntaje", size=12, color=ft.Colors.SECONDARY),
                            ft.Text(str(self.partida.aciertos), size=24,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.GREEN),
                        ]),
                        ft.Column(horizontal_alignment=ft.CrossAxisAlignment.END,
                                  spacing=2, controls=[
                            ft.Text("Tiempo", size=12, color=ft.Colors.SECONDARY),
                            self._timer_txt,
                        ]),
                    ],
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Text("Categoría de:", size=13, color=ft.Colors.SECONDARY,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(
                    padding=ft.Padding(20, 24, 20, 24), border_radius=16,
                    bgcolor=ft.Colors.RED_50,
                    border=ft.Border.all(1, ft.Colors.RED_100),
                    content=ft.Text(pregunta.enunciado, size=24,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.RED_900,
                                    text_align=ft.TextAlign.CENTER),
                ),
                *filas,
                pista,
            ],
        )
        self.page.update()

    def _confirmar_salida(self, _) -> None:
        def cerrar(e): d.open = False; self.page.update()
        def confirmar(e):
            self._timer_running = False
            d.open = False; self.page.update()
            DesafiosView(self.page).mount()
        d = ft.AlertDialog(
            modal=True, title=ft.Text("¿Terminar desafío¡"),
            content=ft.Text("Se perderá el progreso de esta sesión."),
            actions=[ft.TextButton("Continuar", on_click=cerrar),
                     ft.TextButton("Salir", on_click=confirmar)],
        )
        self.page.overlay.append(d)
        d.open = True
        self.page.update()

    def mount(self) -> None:
        view = ft.View(
            route="/contrarreloj", padding=0, bgcolor=ft.Colors.SURFACE,
            controls=[
                ft.AppBar(
                    title=_get_logo_sede(self.page, 22),
                    bgcolor=ft.Colors.SURFACE,
                    leading=ft.IconButton(icon=ft.Icons.CLOSE,
                                          on_click=self._confirmar_salida),
                ),
                ft.Container(expand=True, padding=ft.Padding(16, 16, 16, 16),
                             content=self._area),
            ],
        )
        _montar(self.page, view)
        self._mostrar_pregunta()
        self.page.run_thread(self._update_timer)


class ResultadoContrarrelojView:
    def __init__(self, page: ft.Page, partida: gs.EstadoContrarreloj) -> None:
        self.page = page; self.partida = partida

    def mount(self) -> None:
        view = ft.View(
            route="/resultado_contrarreloj", padding=ft.Padding(16, 0, 16, 16),
            bgcolor=ft.Colors.SURFACE,
            controls=[
                ft.AppBar(title=_get_logo_sede(self.page, 22),
                          bgcolor=ft.Colors.SURFACE,
                          automatically_imply_leading=False),
                ft.Container(
                    padding=ft.Padding(32, 40, 32, 40), border_radius=24,
                    bgcolor=ft.Colors.RED_ACCENT_700,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20,
                        controls=[
                            ft.Icon(ft.Icons.TIMER_OFF_OUTLINED, size=64,
                                    color=ft.Colors.WHITE),
                            ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                      spacing=4, controls=[
                                ft.Text("¡TIEMPO!", size=32,
                                        weight=ft.FontWeight.W_900,
                                        color=ft.Colors.WHITE),
                                ft.Text("Has logrado responder", size=14,
                                        color=ft.Colors.RED_50),
                            ]),
                            ft.Container(
                                padding=ft.Padding(24, 16, 24, 16),
                                border_radius=12, bgcolor=ft.Colors.RED_900,
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=12, controls=[
                                    ft.Text(str(self.partida.aciertos), size=48,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE),
                                    ft.Text("Categorías", size=16,
                                            color=ft.Colors.WHITE,
                                            weight=ft.FontWeight.W_500),
                                ])
                            ),
                            ft.Text(f"Con {self.partida.errores} errores",
                                    size=14, color=ft.Colors.RED_100),
                        ],
                    ),
                ),
                ft.Container(height=32),
                ft.Button("Intentar de nuevo", icon=ft.Icons.REPLAY, expand=True,
                          on_click=lambda _: ConfigurarPartidaView(
                              self.page, "contrarreloj").mount(),
                          style=ft.ButtonStyle(bgcolor=ft.Colors.RED_ACCENT_700,
                                               color=ft.Colors.WHITE)),
                ft.Container(height=8),
                ft.OutlinedButton("Volver a Desafíos", icon=ft.Icons.HOME_OUTLINED,
                                  expand=True,
                                  on_click=lambda _: DesafiosView(self.page).mount()),
            ],
        )
        _montar(self.page, view)

        # Completar un desafío cuenta como actividad
        auth.registrar_actividad()


# -------------¡# ------------------------------------------------------------------------------
# FIN DEL MÓDULO - VISTAS OPTIMIZADAS (CATÁLOGO Y DESAFÍOS)
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# RESULTADO NIVEL VIEW
# ------------------------------------------------------------------------------

class ResultadoNivelView:
    def __init__(self, page: ft.Page, partida: gs.EstadoNivel) -> None:
        self.page    = page
        self.partida = partida

    def mount(self) -> None:
        aprobado  = self.partida.aprobado
        aciertos  = self.partida.aciertos
        total     = self.partida.total
        pct       = self.partida.porcentaje
        siguiente = self.partida.numero + 1

        if pct == 100:
            emoji, msg, color_msg = "★", "¡Perfecto!", ft.Colors.AMBER
        elif aprobado:
            emoji, msg, color_msg = "★", "¡Nivel superado!", ft.Colors.GREEN
        else:
            emoji, msg, color_msg = "-¡", "Sigue practicando", ft.Colors.ORANGE

        # Barra de estrellas (1-3 según puntaje)
        estrellas = 1 if pct >= 70 else 0
        if pct >= 85: estrellas = 2
        if pct == 100: estrellas = 3

        star_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Icon(
                    ft.Icons.STAR if i < estrellas else ft.Icons.STAR_BORDER,
                    color=ft.Colors.AMBER if i < estrellas else ft.Colors.OUTLINE,
                    size=36,
                ) for i in range(3)
            ],
        )

        acciones = []
        if aprobado and siguiente <= 20:
            acciones.append(ft.Button(
                f"Nivel {siguiente} -",
                icon=ft.Icons.ARROW_FORWARD,
                expand=True,
                on_click=lambda _: GuiaEstudioView(self.page).mount(),
            ))
        acciones.append(ft.OutlinedButton(
            "Reintentar", icon=ft.Icons.REPLAY, expand=True,
            on_click=lambda _: GuiaEstudioView(self.page).mount(),
        ))
        acciones.append(ft.OutlinedButton(
            "Volver al mapa", icon=ft.Icons.MAP_OUTLINED, expand=True,
            on_click=lambda _: GuiaEstudioView(self.page).mount(),
        ))

        view = ft.View(
            route="/resultado_nivel",
            padding=ft.Padding(24, 48, 24, 24),
            bgcolor=ft.Colors.SURFACE,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=24,
                    controls=[
                        ft.Text(emoji, size=72, text_align=ft.TextAlign.CENTER),
                        ft.Text(msg, size=24, weight=ft.FontWeight.BOLD,
                                color=color_msg, text_align=ft.TextAlign.CENTER),
                        star_row,
                        ft.Container(
                            padding=ft.Padding(24, 20, 24, 20),
                            border_radius=20,
                            bgcolor=ft.Colors.PRIMARY_CONTAINER,
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=8,
                                controls=[
                                    ft.Text(f"Nivel {self.partida.numero}",
                                            size=14, color=ft.Colors.ON_PRIMARY_CONTAINER),
                                    ft.Text(f"{aciertos} / {total} correctas",
                                            size=28, weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.ON_PRIMARY_CONTAINER),
                                    ft.Text(f"{pct}% de aciertos", size=16,
                                            color=ft.Colors.ON_PRIMARY_CONTAINER),
                                ],
                            ),
                        ),

                        ft.Column(spacing=8, controls=acciones),
                    ],
                )
            ],
        )
        _montar(self.page, view)