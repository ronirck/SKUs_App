import flet as ft

INFALTABLES = {"B", "D", "F"}


def guia_estudio_view(
    page: ft.Page,
    time_offset: float,
    on_interaction,
    primary_color,
    sede: str,
    sede_logo: str,
    categorias: list,
    subcategorias: list,
    productos: list,
    marcas_permitidas: list,
    user_id: str,
    save_cache_callback,
):
    from session_manager import register_interaction

    def handle_interaction(e=None):
        register_interaction(time_offset)
        if on_interaction:
            on_interaction()

    # ─── Estado mutable ───────────────────────────────────────────────────────

    data = {
        "categorias": list(categorias),
        "subcategorias": list(subcategorias),
        "productos": list(productos),
        "marca": None,
        "solo_infaltables": False,
        "cat_search": "",
        "sub_search": "",
    }

    content_area = ft.Container(expand=True)

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

    # ─── Construcción del acordeón ────────────────────────────────────────────

    def filtered_products():
        prods = data["productos"]
        if data["marca"]:
            prods = [p for p in prods if p.get("marca") == data["marca"]]
        if data["solo_infaltables"]:
            prods = [p for p in prods if p.get("estatus") in INFALTABLES]
        return prods

    def product_row(prod):
        is_infaltable = prod.get("estatus") in INFALTABLES
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
                    ft.Text(value=prod.get("nombre", ""), size=12, no_wrap=False),
                    *(
                        [ft.Text(value=mnem, size=10, italic=True,
                                 color=ft.Colors.with_opacity(0.6, primary_color), no_wrap=False)]
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

    def _build_sub_tile(sub, prods):
        sub_cod = sub.get("codigo", "")
        sub_name = sub.get("nombre", "")
        mnem_sub = sub.get("mnemotecnia")

        sub_expanded = [False]
        prod_col = ft.Column(visible=False, spacing=0, controls=[])
        sub_arrow = ft.Icon(
            ft.Icons.KEYBOARD_ARROW_DOWN, size=16,
            color=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
        )
        sub_mnemo = ft.Container(
            visible=False,
            bgcolor=ft.Colors.with_opacity(0.06, primary_color),
            padding=ft.Padding.symmetric(horizontal=16, vertical=6),
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=12,
                            color=ft.Colors.with_opacity(0.6, primary_color)),
                    ft.Text(mnem_sub, size=11, italic=True,
                            color=ft.Colors.with_opacity(0.6, primary_color),
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
                bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.BLACK))
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
                        color=ft.Colors.with_opacity(0.87, ft.Colors.BLACK),
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
                            color=ft.Colors.with_opacity(0.7, primary_color)),
                    ft.Text(mnem_cat, size=12, italic=True,
                            color=ft.Colors.with_opacity(0.7, primary_color),
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
                sub_filter = data["sub_search"].strip().lower()
                subs = sorted(sub_map.get(cat_cod, []), key=lambda x: x.get("codigo", ""))
                if sub_filter:
                    subs = [s for s in subs if sub_filter in s.get("nombre", "").lower()]
                sub_col.controls = [
                    _build_sub_tile(s, prod_map.get((cat_cod, s.get("codigo", "")), []))
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

    def build_accordion():
        visible_prods = filtered_products()

        prod_map = {}
        for p in visible_prods:
            key = (p.get("categoria_codigo"), p.get("subcategoria_codigo"))
            prod_map.setdefault(key, []).append(p)

        sub_map = {}
        for s in data["subcategorias"]:
            sub_map.setdefault(s.get("categoria_codigo"), []).append(s)

        cat_filter = data["cat_search"].strip().lower()
        sub_filter = data["sub_search"].strip().lower()

        panels = []
        for cat in sorted(data["categorias"], key=lambda x: x.get("codigo", "")):
            cat_cod = cat.get("codigo", "")

            if cat_filter and cat_filter not in cat.get("nombre", "").lower():
                continue

            has_products = any(k[0] == cat_cod for k in prod_map)
            if data["solo_infaltables"] and not has_products:
                continue

            if sub_filter:
                matching_subs = [
                    s for s in sub_map.get(cat_cod, [])
                    if sub_filter in s.get("nombre", "").lower()
                ]
                if not matching_subs:
                    continue

            panels.append(_build_cat_card(cat, sub_map, prod_map))

        if not panels:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=48,
                                color=ft.Colors.GREY_700),
                        ft.Text(
                            "No hay elementos que mostrar con los filtros activos.",
                            size=13, color=ft.Colors.GREY_500,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=ft.Padding.all(24),
            )

        return ft.ListView(
            controls=panels,
            expand=True,
            spacing=8,
            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        )

    def rebuild():
        content_area.content = build_accordion()
        page.update()

    # ─── Filtros ──────────────────────────────────────────────────────────────

    all_marcas = sorted({p.get("marca") for p in data["productos"] if p.get("marca")})
    show_dropdown = (
        len(marcas_permitidas) > 1
        or (len(marcas_permitidas) == 0 and len(all_marcas) > 1)
    )

    marca_dd = ft.Dropdown(
        label="Marca",
        value="",
        options=[ft.dropdown.Option(key="", text="Todas las marcas")]
        + [ft.dropdown.Option(key=m, text=m) for m in all_marcas],
        border_radius=10,
        border_color=ft.Colors.with_opacity(0.3, primary_color),
        focused_border_color=primary_color,
        expand=True,
        visible=show_dropdown,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=6),
    )

    def on_marca_select(e):
        handle_interaction()
        data["marca"] = marca_dd.value or None
        rebuild()

    marca_dd.on_select = on_marca_select

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

    # ─── Buscadores de texto ──────────────────────────────────────────────────

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

    def update_marca_dropdown():
        new_marcas = sorted({p.get("marca") for p in data["productos"] if p.get("marca")})
        should_show = (
            len(marcas_permitidas) > 1
            or (len(marcas_permitidas) == 0 and len(new_marcas) > 1)
        )
        marca_dd.options = (
            [ft.dropdown.Option(key="", text="Todas las marcas")]
            + [ft.dropdown.Option(key=m, text=m) for m in new_marcas]
        )
        marca_dd.visible = should_show
        marca_dd.value = ""
        data["marca"] = None

    # ─── Card de taxonomía ────────────────────────────────────────────────────

    cat_count_ref = ft.Text(
        str(len(data["categorias"])),
        size=12, weight=ft.FontWeight.BOLD, color=primary_color,
    )
    sub_count_ref = ft.Text(
        str(len(data["subcategorias"])),
        size=12, weight=ft.FontWeight.BOLD, color=primary_color,
    )
    prod_count_ref = ft.Text(
        str(len(data["productos"])),
        size=12, weight=ft.FontWeight.BOLD, color=primary_color,
    )

    def _update_taxonomy_counts():
        cat_count_ref.value = str(len(data["categorias"]))
        sub_count_ref.value = str(len(data["subcategorias"]))
        prod_count_ref.value = str(len(data["productos"]))

    taxonomy_card = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(
                        "XX-XX-XXX",
                        size=12, color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD, font_family="monospace",
                    ),
                    bgcolor=primary_color,
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            "Estructura del Código:",
                            size=11, weight=ft.FontWeight.BOLD,
                        ),
                        ft.Row(
                            controls=[
                                ft.Text(" Cat  |  ", size=12, color=ft.Colors.GREY_600),
                                ft.Text(" Sub  |  ", size=12, color=ft.Colors.GREY_600),
                                ft.Text(" Prod", size=12, color=ft.Colors.GREY_600),
                            ],
                            spacing=0,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=3,
                    tight=True,
                    expand=True,
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.with_opacity(0.05, primary_color),
        border=ft.Border(
            left=ft.BorderSide(1, ft.Colors.with_opacity(0.3, primary_color)),
            right=ft.BorderSide(1, ft.Colors.with_opacity(0.3, primary_color)),
            top=ft.BorderSide(1, ft.Colors.with_opacity(0.3, primary_color)),
            bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.3, primary_color)),
        ),
        border_radius=10,
        padding=ft.Padding.all(12),
    )

    # ─── Refresh manual ───────────────────────────────────────────────────────

    def do_refresh():
        content_area.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(),
                    ft.Text("Actualizando...", size=13, color=ft.Colors.GREY_500),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )
        page.update()

        try:
            from auth import get_client
            from session_manager import fetch_all
            client = get_client()

            cats = fetch_all(client, "categorias", lambda q: q.select("*").eq("sede", sede))
            subs = fetch_all(client, "subcategorias", lambda q: q.select("*").eq("sede", sede))
            mp = marcas_permitidas
            prods = fetch_all(
                client, "productos",
                lambda q: q.select("*").eq("sede", sede).in_("marca", mp) if mp
                else q.select("*").eq("sede", sede),
            )

            cfg_res = (
                client.table("usuario_config")
                .select("config_version")
                .eq("usuario_id", user_id)
                .execute()
            )
            remote_ver = cfg_res.data[0]["config_version"] if cfg_res.data else None

            print(f"[guia] Refresh: cats={len(cats)}, subs={len(subs)}, prods={len(prods)}, ver={remote_ver}")

            data["categorias"] = cats
            data["subcategorias"] = subs
            data["productos"] = prods

            _update_taxonomy_counts()

            if save_cache_callback:
                save_cache_callback(cats, subs, prods, remote_ver)

            update_marca_dropdown()

        except Exception as ex:
            print(f"[guia] Error en refresh: {ex}")

        rebuild()

    def handle_refresh(e):
        handle_interaction()
        page.run_thread(do_refresh)

    # ─── Header ───────────────────────────────────────────────────────────────

    header_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Image(
                            src=sede_logo,
                            width=80,
                            height=40,
                            fit="contain",
                            error_content=ft.Text(
                                sede, size=13, weight=ft.FontWeight.BOLD, color=primary_color
                            ),
                        ),
                        ft.Text(
                            "Guía de Estudio",
                            size=16, weight=ft.FontWeight.BOLD, expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH_ROUNDED,
                            icon_color=primary_color,
                            on_click=handle_refresh,
                            tooltip="Actualizar desde servidor",
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                taxonomy_card,
                ft.Row(
                    controls=[marca_dd, infaltables_sw],
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

    content_area.content = build_accordion()

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
