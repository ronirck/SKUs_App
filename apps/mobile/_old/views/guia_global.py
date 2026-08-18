import flet as ft

SEDES_ORDEN = ["FEBECA", "SILLACA", "BEVAL", "COFERSA", "MUNDIAL DE PARTES"]
_INFALTABLES = {"B", "D", "F"}


def guia_global_view(
    page: ft.Page,
    time_offset: float,
    on_interaction,
    primary_color,
):
    from session_manager import register_interaction, save_admin_cache, load_admin_cache
    from views.filtros import get_elementos_visibles

    is_dark = page.theme_mode == ft.ThemeMode.DARK
    text_color = ft.Colors.WHITE if is_dark else ft.Colors.BLACK

    def handle_interaction(e=None):
        register_interaction(time_offset)
        if on_interaction:
            on_interaction()

    content_area = ft.Container(expand=True)

    data = {
        "sede": "FEBECA",
        "categorias": [],
        "subcategorias": [],
        "productos": [],
        "solo_infaltables": False,
        "cat_search": "",
        "sub_search": "",
    }

    # ─── Paginación Supabase ──────────────────────────────────────────────────

    def _fetch_all_admin(sede: str, tabla: str) -> list:
        from auth import get_client
        client = get_client()
        PAGE_SIZE = 1000
        all_data = []
        offset = 0
        while True:
            result = (
                client.table(tabla)
                .select("*")
                .eq("sede", sede)
                .range(offset, offset + PAGE_SIZE - 1)
                .execute()
            )
            if not result.data:
                break
            all_data.extend(result.data)
            if len(result.data) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
        return all_data

    # ─── Imagen en pantalla completa ──────────────────────────────────────────

    def open_fullscreen(url: str):
        overlay = ft.Container(
            content=ft.Image(src=url, fit="contain", expand=True),
            bgcolor=ft.Colors.BLACK,
            expand=True,
            alignment=ft.Alignment(0, 0),
        )
        overlay.on_click = lambda e, ov=overlay: close_fullscreen(ov)
        page.overlay.append(overlay)
        page.update()

    def close_fullscreen(overlay):
        if overlay in page.overlay:
            page.overlay.remove(overlay)
        page.update()

    # ─── Fila de producto ─────────────────────────────────────────────────────

    def product_row(prod):
        is_infaltable = prod.get("estatus") in _INFALTABLES
        img_url = prod.get("imagen_url")
        codigo = prod.get("codigo_completo") or (
            f"{prod.get('categoria_codigo','')}-"
            f"{prod.get('subcategoria_codigo','')}-"
            f"{prod.get('codigo','')}"
        )
        mnem = prod.get("mnemotecnia")

        controls = [
            ft.Text(
                value=codigo,
                size=11,
                weight=ft.FontWeight.W_600,
                color=primary_color,
                font_family="monospace",
                width=96,
            ),
            ft.Column(
                controls=[
                    ft.Text(value=prod.get("nombre", ""), size=12,
                            no_wrap=False, color=text_color),
                    *(
                        [ft.Text(value=mnem, size=10, italic=True,
                                 color=ft.Colors.with_opacity(0.8, primary_color),
                                 no_wrap=False)]
                        if mnem else []
                    ),
                ],
                spacing=1,
                tight=True,
                expand=True,
            ),
        ]

        if is_infaltable and img_url:
            controls.append(
                ft.GestureDetector(
                    content=ft.Image(
                        src=img_url, width=44, height=44,
                        fit="cover", border_radius=6,
                    ),
                    on_tap=lambda e, u=img_url: open_fullscreen(u),
                )
            )

        return ft.Container(
            content=ft.Row(
                controls=controls,
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=5),
            border=ft.Border(
                bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, primary_color))
            ),
            on_click=handle_interaction,
        )

    # ─── Tile de subcategoría ─────────────────────────────────────────────────

    def _build_sub_tile(sub, prods):
        sub_cod = sub.get("codigo", "")
        sub_name = sub.get("nombre", "")
        mnem_sub = sub.get("mnemotecnia")

        sub_expanded = [False]
        prod_col = ft.Column(visible=False, spacing=0, controls=[])
        sub_arrow = ft.Icon(
            ft.Icons.KEYBOARD_ARROW_DOWN, size=16,
            color=ft.Colors.with_opacity(0.5, text_color),
        )
        sub_mnemo = ft.Container(
            visible=False,
            bgcolor=ft.Colors.with_opacity(0.06, primary_color),
            padding=ft.Padding.symmetric(horizontal=16, vertical=6),
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=12,
                            color=ft.Colors.with_opacity(0.8, primary_color)),
                    ft.Text(mnem_sub, size=11, italic=True,
                            color=ft.Colors.with_opacity(0.8, primary_color),
                            expand=True),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ) if mnem_sub else None

        def sub_toggle(e):
            handle_interaction()
            sub_expanded[0] = not sub_expanded[0]
            if sub_expanded[0] and not prod_col.controls:
                sorted_prods = sorted(prods, key=lambda x: x.get("codigo", ""))
                prod_col.controls = (
                    [product_row(p) for p in sorted_prods]
                    if sorted_prods else [
                        ft.Container(
                            content=ft.Text("Sin productos", size=11,
                                            color=ft.Colors.GREY_600),
                            padding=ft.Padding.all(8),
                        )
                    ]
                )
            prod_col.visible = sub_expanded[0]
            if sub_mnemo:
                sub_mnemo.visible = sub_expanded[0]
            sub_arrow.name = (ft.Icons.KEYBOARD_ARROW_UP if sub_expanded[0]
                              else ft.Icons.KEYBOARD_ARROW_DOWN)
            page.update()

        sub_header = ft.Container(
            bgcolor=ft.Colors.SURFACE,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            on_click=sub_toggle,
            border=ft.Border(
                bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, primary_color))
            ),
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=6, height=6, border_radius=3,
                        bgcolor=ft.Colors.with_opacity(0.5, primary_color),
                    ),
                    ft.Text(
                        f"{sub_cod}  {sub_name}",
                        size=13, weight=ft.FontWeight.W_500,
                        color=text_color,
                        expand=True,
                    ),
                    sub_arrow,
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        parts = [sub_header]
        if sub_mnemo:
            parts.append(sub_mnemo)
        parts.append(prod_col)
        return ft.Column(spacing=0, controls=parts)

    # ─── Card de categoría ────────────────────────────────────────────────────

    def _build_cat_card(cat, sub_map, prod_map):
        cat_cod = cat.get("codigo", "")
        cat_name = cat.get("nombre", "")
        mnem_cat = cat.get("mnemotecnia")

        cat_expanded = [False]
        sub_col = ft.Column(visible=False, spacing=0, controls=[])
        cat_arrow = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, size=20,
                            color=ft.Colors.WHITE)
        cat_mnemo = ft.Container(
            visible=False,
            bgcolor=ft.Colors.with_opacity(0.08, primary_color),
            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=14,
                            color=ft.Colors.with_opacity(0.8, primary_color)),
                    ft.Text(mnem_cat, size=12, italic=True,
                            color=ft.Colors.with_opacity(0.8, primary_color),
                            expand=True),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ) if mnem_cat else None

        def cat_toggle(e):
            handle_interaction()
            cat_expanded[0] = not cat_expanded[0]
            if cat_expanded[0] and not sub_col.controls:
                subs = sorted(sub_map.get(cat_cod, []),
                              key=lambda x: x.get("codigo", ""))
                sub_col.controls = [
                    _build_sub_tile(s, prod_map.get(
                        (cat_cod, s.get("codigo", "")), []))
                    for s in subs
                ] or [
                    ft.Container(
                        content=ft.Text("Sin subcategorías visibles", size=11,
                                        color=ft.Colors.GREY_600),
                        padding=ft.Padding.all(8),
                    )
                ]
            sub_col.visible = cat_expanded[0]
            if cat_mnemo:
                cat_mnemo.visible = cat_expanded[0]
            cat_arrow.name = (ft.Icons.KEYBOARD_ARROW_UP if cat_expanded[0]
                              else ft.Icons.KEYBOARD_ARROW_DOWN)
            page.update()

        cat_header = ft.Container(
            bgcolor=primary_color,
            padding=ft.Padding(12, 12, 12, 12),
            on_click=cat_toggle,
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            cat_cod, color=primary_color,
                            weight=ft.FontWeight.BOLD, size=13,
                        ),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Text(
                        cat_name, color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_600, size=14,
                        expand=True,
                    ),
                    cat_arrow,
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        parts = [cat_header]
        if cat_mnemo:
            parts.append(cat_mnemo)
        parts.append(sub_col)

        return ft.Container(
            border_radius=12,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            shadow=ft.BoxShadow(
                blur_radius=4,
                offset=ft.Offset(0, 2),
                color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK),
            ),
            content=ft.Column(spacing=0, controls=parts),
        )

    # ─── Acordeón ─────────────────────────────────────────────────────────────

    def build_accordion():
        cats_v, subs_v, prods_v = get_elementos_visibles(
            categorias=data["categorias"],
            subcategorias=data["subcategorias"],
            productos=data["productos"],
            marca_filtro=None,
            solo_infaltables=data["solo_infaltables"],
            busqueda_cat=data["cat_search"],
            busqueda_sub=data["sub_search"],
        )

        if not cats_v:
            msg = (
                "No hay datos para esta sede. Pulsa ↻ para cargar."
                if not data["categorias"]
                else "No hay elementos que mostrar con los filtros activos."
            )
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=48,
                                color=ft.Colors.GREY_700),
                        ft.Text(msg, size=13, color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=ft.Padding.all(24),
            )

        prod_map = {}
        for p in prods_v:
            key = (p.get("categoria_codigo"), p.get("subcategoria_codigo"))
            prod_map.setdefault(key, []).append(p)

        sub_map = {}
        for s in subs_v:
            sub_map.setdefault(s.get("categoria_codigo"), []).append(s)

        panels = [
            _build_cat_card(cat, sub_map, prod_map)
            for cat in sorted(cats_v, key=lambda x: x.get("codigo", ""))
        ]

        return ft.ListView(
            controls=panels,
            expand=True,
            spacing=8,
            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        )

    def usar_datos(cached: dict):
        data["categorias"] = cached.get("categorias", [])
        data["subcategorias"] = cached.get("subcategorias", [])
        data["productos"] = cached.get("productos", [])
        content_area.content = build_accordion()
        page.update()

    def cargar_sede(sede: str, forzar_refresh: bool = False):
        if not forzar_refresh:
            cached = load_admin_cache(sede)
            if cached:
                usar_datos(cached)
                return

        content_area.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(),
                    ft.Text("Cargando sede...", size=13, color=ft.Colors.GREY_500),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )
        page.update()

        def do_load():
            try:
                cats = _fetch_all_admin(sede, "categorias")
                subs = _fetch_all_admin(sede, "subcategorias")
                prods = _fetch_all_admin(sede, "productos")
                cache_data = {
                    "sede": sede,
                    "categorias": cats,
                    "subcategorias": subs,
                    "productos": prods,
                }
                save_admin_cache(sede, cache_data)
                usar_datos(cache_data)
            except Exception as ex:
                print(f"[guia_global] Error cargando {sede}: {ex}")
                content_area.content = ft.Container(
                    content=ft.Text("Error al cargar datos",
                                    color=ft.Colors.RED_400,
                                    text_align=ft.TextAlign.CENTER),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
                page.update()

        page.run_thread(do_load)

    def rebuild():
        content_area.content = build_accordion()
        page.update()

    # ─── Filtros ──────────────────────────────────────────────────────────────

    infaltables_sw = ft.Switch(
        label="Solo Infaltables",
        value=False,
        active_color=primary_color,
    )

    def on_infaltables_change(e):
        handle_interaction()
        data["solo_infaltables"] = infaltables_sw.value
        rebuild()

    infaltables_sw.on_change = on_infaltables_change

    cat_search_field = ft.TextField(
        hint_text="Buscar categoría...",
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        border_radius=10,
        border_color=ft.Colors.with_opacity(0.3, primary_color),
        focused_border_color=primary_color,
        text_size=13,
        height=44,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        expand=True,
    )

    sub_search_field = ft.TextField(
        hint_text="Buscar subcategoría...",
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        border_radius=10,
        border_color=ft.Colors.with_opacity(0.3, primary_color),
        focused_border_color=primary_color,
        text_size=13,
        height=44,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        expand=True,
    )

    def on_cat_search(e):
        handle_interaction()
        data["cat_search"] = cat_search_field.value or ""
        rebuild()

    def on_sub_search(e):
        handle_interaction()
        data["sub_search"] = sub_search_field.value or ""
        rebuild()

    cat_search_field.on_change = on_cat_search
    sub_search_field.on_change = on_sub_search

    # ─── Dropdown de sede ─────────────────────────────────────────────────────

    sede_actual = ["FEBECA"]

    sede_dd = ft.Dropdown(
        label="Sede",
        value="FEBECA",
        options=[ft.dropdown.Option(key=s, text=s) for s in SEDES_ORDEN],
        border_radius=10,
        border_color=ft.Colors.with_opacity(0.3, primary_color),
        focused_border_color=primary_color,
        expand=True,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=6),
    )

    def handle_sede_change(e):
        nueva_sede = sede_dd.value
        print(f"[guia_global] Sede cambiada a: {nueva_sede}")
        if not nueva_sede or nueva_sede == sede_actual[0]:
            return
        handle_interaction()
        sede_actual[0] = nueva_sede
        data["sede"] = nueva_sede
        data["cat_search"] = ""
        data["sub_search"] = ""
        data["solo_infaltables"] = False
        cat_search_field.value = ""
        sub_search_field.value = ""
        infaltables_sw.value = False
        page.update()
        cargar_sede(nueva_sede)

    sede_dd.on_select = handle_sede_change

    def handle_refresh(e):
        handle_interaction()
        cargar_sede(sede_actual[0], forzar_refresh=True)

    # ─── Header ───────────────────────────────────────────────────────────────

    header_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Image(
                            src="assets/images/Prisma.png",
                            height=34,
                            fit="contain",
                            error_content=ft.Text(
                                "Prisma", size=13,
                                weight=ft.FontWeight.BOLD,
                                color=primary_color,
                            ),
                        ),
                        ft.Text(
                            "Guía Global",
                            size=16, weight=ft.FontWeight.BOLD, expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH_ROUNDED,
                            icon_color=primary_color,
                            on_click=handle_refresh,
                            tooltip="Recargar desde servidor",
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                ft.Row(
                    controls=[sede_dd, infaltables_sw],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    controls=[cat_search_field, sub_search_field],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=10,
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
    )

    # ─── Init ─────────────────────────────────────────────────────────────────

    cargar_sede("FEBECA")

    return ft.Container(
        content=ft.Column(
            controls=[
                header_section,
                ft.Divider(
                    height=1,
                    thickness=0.5,
                    color=ft.Colors.with_opacity(0.2, primary_color),
                ),
                ft.Container(content=content_area, expand=True),
            ],
            expand=True,
            spacing=0,
        ),
        expand=True,
        on_click=handle_interaction,
    )
