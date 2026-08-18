import flet as ft
from collections import defaultdict
from datetime import datetime, timedelta, timezone

COLORES_SEDE = {
    "FEBECA": ft.Colors.BLUE_400,
    "COFERSA": ft.Colors.BLUE_400,
    "SILLACA": ft.Colors.PINK_400,
    "BEVAL": ft.Colors.GREEN_400,
    "MUNDIAL DE PARTES": ft.Colors.GREEN_400,
}

SEDES = ["FEBECA", "COFERSA", "SILLACA", "BEVAL", "MUNDIAL DE PARTES"]
_SEDES_ORDER = ["FEBECA", "COFERSA", "SILLACA", "BEVAL", "MUNDIAL DE PARTES", None]


def admin_usuarios_view(
    page: ft.Page,
    time_offset: float,
    on_interaction,
    primary_color,
    notif_count: int,
    on_notif_cleared,
):
    from session_manager import register_interaction, fetch_all

    is_dark = page.theme_mode == ft.ThemeMode.DARK
    text_color = ft.Colors.WHITE if is_dark else ft.Colors.BLACK
    text_secondary = ft.Colors.GREY_400 if is_dark else ft.Colors.GREY_700

    def handle_interaction(e=None):
        register_interaction(time_offset)
        if on_interaction:
            on_interaction()

    content_area = ft.Container(expand=True)
    usuarios_data = []
    stats_map_ref = {}

    # ─── Notificaciones ───────────────────────────────────────────────────────

    def mark_notifs_read():
        def do_mark():
            try:
                from auth import get_client
                client = get_client()
                client.table("notificaciones_admin").update(
                    {"leido": True}
                ).eq("leido", False).execute()
                if on_notif_cleared:
                    on_notif_cleared()
            except Exception:
                pass
        page.run_thread(do_mark)

    # ─── Carga de usuarios ────────────────────────────────────────────────────

    def load_usuarios():
        content_area.content = ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )
        page.update()

        def do_load():
            nonlocal usuarios_data
            try:
                from auth import get_client
                client = get_client()

                perfiles = (
                    client.table("perfil_usuario")
                    .select("*")
                    .order("creado_en", desc=True)
                    .execute()
                )
                configs = client.table("usuario_config").select("*").execute()
                cfg_map = {c["usuario_id"]: c for c in (configs.data or [])}

                usuarios_data = []
                for p in (perfiles.data or []):
                    cfg = cfg_map.get(p["usuario_id"], {})
                    usuarios_data.append({**cfg, **p})

                # ── Estadísticas en bloque ────────────────────────────────────
                uids = [u["usuario_id"] for u in usuarios_data if u.get("usuario_id")]

                resultados_bulk = []
                session_bulk = []
                if uids:
                    try:
                        resultados_bulk = fetch_all(
                            client, "resultados_codex",
                            lambda q: q.select("usuario_id, aciertos, total_preguntas")
                                       .in_("usuario_id", uids),
                        )
                    except Exception:
                        pass
                    try:
                        session_bulk = fetch_all(
                            client, "session_logs",
                            lambda q: q.select("user_id, duration_seconds")
                                       .in_("user_id", uids),
                        )
                    except Exception:
                        pass

                res_by_uid = defaultdict(lambda: {"aciertos": 0, "total": 0, "partidas": 0})
                for r in resultados_bulk:
                    uid = r.get("usuario_id", "")
                    if uid:
                        res_by_uid[uid]["aciertos"] += r.get("aciertos", 0)
                        res_by_uid[uid]["total"] += r.get("total_preguntas", 0)
                        res_by_uid[uid]["partidas"] += 1

                sess_by_uid = defaultdict(int)
                for s in session_bulk:
                    uid = s.get("user_id", "")
                    if uid:
                        sess_by_uid[uid] += s.get("duration_seconds", 0)

                stats_result = {}
                active_uids = set(res_by_uid.keys()) | set(sess_by_uid.keys())
                for uid in active_uids:
                    totals = res_by_uid[uid]
                    ef = (
                        round(totals["aciertos"] / totals["total"] * 100)
                        if totals["total"] > 0 else 0
                    )
                    stats_result[uid] = {
                        "efectividad": ef,
                        "partidas": totals["partidas"],
                        "tiempo_min": sess_by_uid[uid] // 60,
                    }

                stats_map_ref.clear()
                stats_map_ref.update(stats_result)

            except Exception:
                usuarios_data = []

            build_list()
            page.update()

        page.run_thread(do_load)

    # ─── Filtro de rol ────────────────────────────────────────────────────────

    filter_state = {"rol": "user"}
    search_state = {"query": ""}
    filter_refs = {}

    def make_filter_chip(label, rol_key):
        active = filter_state["rol"] == rol_key
        txt = ft.Text(
            label, size=11, weight=ft.FontWeight.W_500,
            color=ft.Colors.WHITE if active else ft.Colors.GREY_500,
        )
        c = ft.Container(
            content=txt,
            bgcolor=primary_color if active else ft.Colors.TRANSPARENT,
            border_radius=20,
            border=None if active else ft.Border.all(
                1, ft.Colors.with_opacity(0.3, ft.Colors.GREY_500)
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=5),
        )
        filter_refs[rol_key] = (c, txt)

        def on_tap(e, key=rol_key):
            handle_interaction()
            filter_state["rol"] = key
            for k, (btn, t) in filter_refs.items():
                is_active = filter_state["rol"] == k
                btn.bgcolor = primary_color if is_active else ft.Colors.TRANSPARENT
                btn.border = None if is_active else ft.Border.all(
                    1, ft.Colors.with_opacity(0.3, ft.Colors.GREY_500)
                )
                t.color = ft.Colors.WHITE if is_active else ft.Colors.GREY_500
            build_list()
            page.update()

        return ft.GestureDetector(content=c, on_tap=on_tap)

    filter_row = ft.Row(
        controls=[
            make_filter_chip("Todos", "all"),
            make_filter_chip("Usuarios", "user"),
            make_filter_chip("Admins", "admin"),
            make_filter_chip("Nuevos", "new"),
        ],
        spacing=6,
    )

    # ─── Buscador ─────────────────────────────────────────────────────────────

    def _on_search_change(e):
        handle_interaction()
        search_state["query"] = (e.control.value or "").strip().lower()
        build_list()
        page.update()

    search_field = ft.TextField(
        hint_text="Buscar por nombre o correo...",
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        border_radius=12,
        height=40,
        text_size=13,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        on_change=_on_search_change,
    )

    # ─── Card de usuario ──────────────────────────────────────────────────────

    def _is_new_user(u: dict) -> bool:
        created = u.get("creado_en")
        if not created:
            return False
        try:
            ts = datetime.fromisoformat(created.replace("Z", "+00:00"))
            return ts >= datetime.now(timezone.utc) - timedelta(days=7)
        except Exception:
            return False

    def _user_card(u: dict) -> ft.GestureDetector:
        uid = u.get("usuario_id", "")
        marcas = u.get("marcas_permitidas") or []
        chips = []
        for m in marcas[:3]:
            chips.append(
                ft.Container(
                    content=ft.Text(m, size=9, color=ft.Colors.GREY_400),
                    bgcolor=ft.Colors.with_opacity(0.12, primary_color),
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                )
            )
        if len(marcas) > 3:
            chips.append(ft.Text(f"+{len(marcas)-3}", size=9, color=ft.Colors.GREY_600))

        sede = u.get("sede") or ""
        sede_color = COLORES_SEDE.get(sede, ft.Colors.GREY_500)
        COLORES_SEDE_CLARO = {
            "FEBECA": ft.Colors.BLUE_700,
            "COFERSA": ft.Colors.BLUE_700,
            "SILLACA": ft.Colors.PINK_700,
            "BEVAL": ft.Colors.GREEN_700,
            "MUNDIAL DE PARTES": ft.Colors.GREEN_700,
        }
        sede_color_text = sede_color if is_dark else COLORES_SEDE_CLARO.get(sede, ft.Colors.GREY_700)
        sede_text = ft.Text(
            sede, size=10,
            color=sede_color_text,
            weight=ft.FontWeight.W_500,
        )

        is_new = _is_new_user(u)

        # ── Stats mini-row ────────────────────────────────────────────────────
        user_stats = stats_map_ref.get(uid)
        if user_stats is None:
            stats_row = ft.Row(
                controls=[
                    ft.Text("Sin actividad", size=10,
                            color=ft.Colors.GREY_600, italic=True),
                ],
                spacing=4,
            )
        else:
            ef = user_stats["efectividad"]
            ef_color = (
                ft.Colors.GREEN_400 if ef >= 70
                else ft.Colors.YELLOW_600 if ef >= 40
                else ft.Colors.RED_400
            )
            stats_row = ft.Row(
                controls=[
                    ft.Text(f"{ef}% ef.", size=10, color=ef_color,
                            weight=ft.FontWeight.W_500),
                    ft.Text("·", size=10, color=ft.Colors.GREY_600),
                    ft.Text(f"{user_stats['partidas']} partidas", size=10,
                            color=ft.Colors.GREY_600),
                    ft.Text("·", size=10, color=ft.Colors.GREY_600),
                    ft.Text(f"{user_stats['tiempo_min']}min", size=10,
                            color=ft.Colors.GREY_600),
                ],
                spacing=4,
            )

        name_row_controls = [
            ft.Text(u.get("nombre", ""), size=13,
                    weight=ft.FontWeight.W_600, no_wrap=True, color=text_color),
        ]
        if is_new:
            name_row_controls.append(
                ft.Container(
                    content=ft.Text("Nuevo", size=9, color=ft.Colors.WHITE,
                                    weight=ft.FontWeight.W_600),
                    bgcolor=primary_color,
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                )
            )

        info_controls = [
            ft.Row(
                controls=name_row_controls,
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Text(u.get("email", ""), size=11,
                    color=ft.Colors.GREY_500, no_wrap=True),
        ]
        if chips:
            info_controls.append(ft.Row(controls=chips, spacing=4, wrap=True))
        else:
            info_controls.append(sede_text)
        info_controls.append(stats_row)

        return ft.GestureDetector(
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.PERSON_ROUNDED,
                                size=20,
                                color=ft.Colors.with_opacity(0.6, primary_color),
                            ),
                            width=40, height=40, border_radius=20,
                            bgcolor=ft.Colors.with_opacity(0.1, primary_color),
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Column(
                            controls=info_controls,
                            spacing=2,
                            expand=True,
                            tight=True,
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED,
                                color=ft.Colors.GREY_500, size=20),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                border=ft.Border(
                    bottom=ft.BorderSide(
                        0.5, ft.Colors.with_opacity(0.1, primary_color)
                    )
                ),
            ),
            on_tap=lambda e, user=u: open_detail(user),
        )

    # ─── Lista agrupada con ExpansionTile ─────────────────────────────────────

    def build_list():
        fil = filter_state["rol"]
        query = search_state["query"]

        if fil == "new":
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            after_rol = [u for u in usuarios_data if _is_new_user(u)]
        else:
            after_rol = (
                usuarios_data if fil == "all"
                else [u for u in usuarios_data if u.get("rol", "user") == fil]
            )

        if query:
            visible = [
                u for u in after_rol
                if query in (u.get("nombre") or "").lower()
                or query in (u.get("email") or "").lower()
            ]
        else:
            visible = after_rol

        if not visible:
            msg = "Sin resultados" if query else "No hay usuarios registrados"
            content_area.content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.GROUP_OFF_ROUNDED, size=48,
                                color=ft.Colors.GREY_700),
                        ft.Text(msg, size=14, color=ft.Colors.GREY_500),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
            )
            return

        groups: dict[str | None, list] = {}
        for u in visible:
            sede = u.get("sede") or None
            key = sede if sede in SEDES else None
            groups.setdefault(key, []).append(u)

        tiles = []
        for sede_key in _SEDES_ORDER:
            group = groups.get(sede_key)
            if not group:
                continue

            label = sede_key if sede_key else "Sin sede asignada"
            color = COLORES_SEDE.get(sede_key, ft.Colors.GREY_400)
            sorted_group = sorted(group, key=lambda u: u.get("creado_en", ""))

            tile = ft.ExpansionTile(
                title=ft.Row(
                    controls=[
                        ft.Container(
                            width=3, height=20,
                            bgcolor=color, border_radius=2,
                        ),
                        ft.Text(label, size=12, weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREY_300 if is_dark else ft.Colors.GREY_800, expand=True),
                        ft.Container(
                            content=ft.Text(
                                str(len(group)), size=10,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.WHITE,
                            ),
                            bgcolor=ft.Colors.with_opacity(0.30, color),
                            border_radius=8,
                            padding=ft.Padding.symmetric(horizontal=7, vertical=2),
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                controls=[_user_card(u) for u in sorted_group],
                expanded=False,
                tile_padding=ft.Padding.symmetric(horizontal=12, vertical=4),
            )
            tiles.append(tile)

        content_area.content = ft.ListView(controls=tiles, expand=True, spacing=0)

    # ─── Detalle de usuario ───────────────────────────────────────────────────

    def open_detail(user: dict):
        handle_interaction()

        user_sede = user.get("sede", "FEBECA")
        sede_state = {"value": user_sede}
        config_ver = user.get("config_version", 1)
        marcas_state = {}
        status_text = ft.Text(value="", size=12, text_align=ft.TextAlign.CENTER)

        sede_dd = ft.Dropdown(
            label="Sede",
            value=sede_state["value"],
            options=[ft.dropdown.Option(key=s, text=s) for s in SEDES],
            border_radius=12,
            border_color=ft.Colors.with_opacity(0.3, primary_color),
            focused_border_color=primary_color,
            expand=True,
        )

        marcas_col = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)

        def load_marcas(sede: str):
            marcas_col.controls.clear()
            marcas_col.controls.append(ft.ProgressRing(width=20, height=20))
            page.update()

            def do_load():
                try:
                    from auth import get_client
                    client = get_client()
                    res = (
                        client.table("marcas")
                        .select("nombre")
                        .eq("sede", sede)
                        .order("nombre")
                        .execute()
                    )
                    disponibles = [r["nombre"] for r in (res.data or [])]
                except Exception:
                    disponibles = []

                actuales = user.get("marcas_permitidas") or []
                marcas_state.clear()
                marcas_col.controls.clear()

                for m in disponibles:
                    checked = (m in actuales) if sede == user_sede else False
                    marcas_state[m] = checked
                    cb = ft.Checkbox(
                        label=m, value=checked, active_color=primary_color,
                        on_change=lambda e, nombre=m: marcas_state.update(
                            {nombre: e.control.value}
                        ),
                    )
                    marcas_col.controls.append(cb)

                if not disponibles:
                    marcas_col.controls.append(
                        ft.Text("Sin marcas para esta sede", size=12,
                                color=ft.Colors.GREY_500)
                    )
                page.update()

            page.run_thread(do_load)

        def on_sede_select(e):
            handle_interaction()
            sede_state["value"] = sede_dd.value
            load_marcas(sede_state["value"])

        sede_dd.on_select = on_sede_select

        infaltables_sw = ft.Switch(
            label="Solo Infaltables",
            value=user.get("solo_infaltables", False),
            active_color=primary_color,
        )

        save_btn = ft.Button(
            content=ft.Text("Guardar", color=ft.Colors.WHITE,
                            weight=ft.FontWeight.W_600),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                bgcolor=primary_color,
            ),
            expand=True,
        )

        def handle_save(e):
            handle_interaction()
            save_btn.disabled = True
            status_text.value = "Guardando..."
            status_text.color = ft.Colors.GREY_500
            page.update()

            def do_save():
                try:
                    from auth import get_client
                    client = get_client()
                    selected = [m for m, v in marcas_state.items() if v]
                    new_ver = config_ver + 1
                    client.table("usuario_config").update({
                        "sede": sede_state["value"],
                        "marcas_permitidas": selected,
                        "solo_infaltables": infaltables_sw.value,
                        "config_version": new_ver,
                    }).eq("usuario_id", user["usuario_id"]).execute()

                    for u in usuarios_data:
                        if u.get("usuario_id") == user["usuario_id"]:
                            u.update({
                                "sede": sede_state["value"],
                                "marcas_permitidas": selected,
                                "solo_infaltables": infaltables_sw.value,
                                "config_version": new_ver,
                            })

                    status_text.value = "✓ Configuración guardada"
                    status_text.color = ft.Colors.GREEN_400
                except Exception as ex:
                    status_text.value = f"Error: {str(ex)[:60]}"
                    status_text.color = ft.Colors.RED_400

                save_btn.disabled = False
                page.update()

            page.run_thread(do_save)

        save_btn.on_click = handle_save

        # ── Estadísticas del usuario ───────────────────────────────────────────

        stats_container = ft.Container(
            content=ft.Row(
                controls=[
                    ft.ProgressRing(width=18, height=18),
                    ft.Text("Cargando estadísticas...", size=12,
                            color=ft.Colors.GREY_500),
                ],
                spacing=8,
            ),
            padding=ft.Padding.only(top=4),
        )

        uid = user.get("usuario_id", "")
        cached = stats_map_ref.get(uid)
        if cached:
            def _quick_card(label, value, subtitle=None):
                sub = (
                    [ft.Text(subtitle, size=9, color=ft.Colors.GREY_600,
                             text_align=ft.TextAlign.CENTER, no_wrap=False)]
                    if subtitle else []
                )
                return ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(value, size=18, weight=ft.FontWeight.BOLD,
                                    color=primary_color,
                                    text_align=ft.TextAlign.CENTER),
                            ft.Text(label, size=10, color=ft.Colors.GREY_500,
                                    text_align=ft.TextAlign.CENTER, no_wrap=False),
                            *sub,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                    bgcolor=ft.Colors.with_opacity(0.06, primary_color),
                    border_radius=10,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=10),
                    expand=True,
                )
            stats_container.content = ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.BAR_CHART_ROUNDED,
                                    size=16, color=primary_color),
                            ft.Text("Estadísticas", size=13,
                                    weight=ft.FontWeight.W_600,
                                    color=primary_color),
                        ],
                        spacing=6,
                    ),
                    ft.Container(height=6),
                    ft.Row(
                        controls=[
                            _quick_card("Aciertos", f"{cached['efectividad']}%",
                                        subtitle="% de respuestas correctas"),
                            _quick_card("Partidas", str(cached["partidas"])),
                            _quick_card("Tiempo (min)", str(cached["tiempo_min"])),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=0,
                tight=True,
            )

        def load_user_stats():
            uid = user.get("usuario_id", "")

            def do_load():
                try:
                    from auth import get_client
                    client = get_client()

                    print(f"[STATS] Consultando resultados_codex para uid={uid}")
                    resultados = (
                        client.table("resultados_codex")
                        .select("aciertos, total_preguntas")
                        .eq("usuario_id", uid)
                        .range(0, 9999)
                        .execute()
                    ).data or []
                    print(f"[STATS] resultados_codex → {len(resultados)} filas: {resultados}")

                    print(f"[STATS] Consultando session_logs para uid={uid}")
                    session_logs = (
                        client.table("session_logs")
                        .select("duration_seconds")
                        .eq("user_id", uid)
                        .range(0, 9999)
                        .execute()
                    ).data or []
                    print(f"[STATS] session_logs → {len(session_logs)} filas: {session_logs}")

                    print(f"[STATS] Consultando errores_partida para uid={uid}")
                    errores = (
                        client.table("errores_partida")
                        .select("elemento_codigo, elemento_nombre, veces_fallado")
                        .eq("usuario_id", uid)
                        .range(0, 9999)
                        .execute()
                    ).data or []
                    print(f"[STATS] errores_partida → {len(errores)} filas: {errores}")

                    total_aciertos = sum(r.get("aciertos", 0) for r in resultados)
                    total_preguntas = sum(r.get("total_preguntas", 0) for r in resultados)
                    efectividad = (
                        round(total_aciertos / total_preguntas * 100)
                        if total_preguntas else 0
                    )
                    partidas = len(resultados)
                    tiempo_min = sum(
                        s.get("duration_seconds", 0) for s in session_logs
                    ) // 60
                    print(f"[STATS] RESULTADO FINAL uid={uid} → efectividad={efectividad}% partidas={partidas} tiempo={tiempo_min}min")

                    err_map = defaultdict(lambda: {"nombre": "", "total": 0})
                    for err in errores:
                        cod = err.get("elemento_codigo", "")
                        err_map[cod]["nombre"] = err.get("elemento_nombre", "")
                        err_map[cod]["total"] += err.get("veces_fallado", 1)
                    top5 = sorted(
                        err_map.items(),
                        key=lambda x: x[1]["total"], reverse=True
                    )[:5]

                    def stat_card(label, value, subtitle=None):
                        label_controls = [
                            ft.Text(label, size=10,
                                    color=ft.Colors.GREY_500,
                                    text_align=ft.TextAlign.CENTER,
                                    no_wrap=False),
                        ]
                        if subtitle:
                            label_controls.append(
                                ft.Text(subtitle, size=9,
                                        color=ft.Colors.GREY_600,
                                        text_align=ft.TextAlign.CENTER,
                                        no_wrap=False),
                            )
                        return ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(value, size=18,
                                            weight=ft.FontWeight.BOLD,
                                            color=primary_color,
                                            text_align=ft.TextAlign.CENTER),
                                    *label_controls,
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
                        ciegos_rows = [
                            ft.Row(
                                controls=[
                                    ft.Text(cod, size=11,
                                            weight=ft.FontWeight.W_600,
                                            color=primary_color,
                                            font_family="monospace",
                                            width=70),
                                    ft.Text(info["nombre"], size=11,
                                            expand=True, no_wrap=True,
                                            color=text_color),
                                    ft.Text(f"×{info['total']}", size=11,
                                            color=ft.Colors.RED_400, width=32,
                                            text_align=ft.TextAlign.RIGHT),
                                ],
                                spacing=8,
                            )
                            for cod, info in top5
                        ]
                        ciegos_widget = ft.Column(controls=ciegos_rows, spacing=6)
                    else:
                        ciegos_widget = ft.Text(
                            "Sin errores frecuentes registrados",
                            size=12, color=ft.Colors.GREEN_400, italic=True,
                        )

                    stats_container.content = ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.BAR_CHART_ROUNDED,
                                            size=16, color=primary_color),
                                    ft.Text("Estadísticas", size=13,
                                            weight=ft.FontWeight.W_600,
                                            color=primary_color),
                                ],
                                spacing=6,
                            ),
                            ft.Container(height=6),
                            ft.Row(
                                controls=[
                                    stat_card("Aciertos", f"{efectividad}%",
                                              subtitle="% de respuestas correctas"),
                                    stat_card("Partidas", str(partidas)),
                                    stat_card("Tiempo (min)", str(tiempo_min)),
                                ],
                                spacing=8,
                            ),
                            ft.Container(height=8),
                            ft.Text("Puntos Ciegos", size=12,
                                    color=ft.Colors.GREY_500,
                                    weight=ft.FontWeight.W_500),
                            ft.Container(height=4),
                            ft.Container(
                                content=ciegos_widget,
                                bgcolor=ft.Colors.with_opacity(0.04, primary_color),
                                border_radius=10,
                                padding=ft.Padding.all(10),
                            ),
                        ],
                        spacing=0,
                        tight=True,
                    )
                    page.update()

                except Exception:
                    stats_container.content = ft.Container()
                    page.update()

            page.run_thread(do_load)

        bs_ref = {"sheet": None}

        def handle_close(e):
            sheet = bs_ref["sheet"]
            if sheet:
                sheet.open = False
                if sheet in page.overlay:
                    page.overlay.remove(sheet)
                page.update()

        close_icon_btn = ft.IconButton(
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_color=ft.Colors.GREY_500,
            on_click=handle_close,
        )

        bs = ft.BottomSheet(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text(user.get("nombre", ""), size=15,
                                                weight=ft.FontWeight.BOLD,
                                                color=text_color),
                                        ft.Text(user.get("email", ""), size=12,
                                                color=ft.Colors.GREY_500),
                                    ],
                                    spacing=2, expand=True, tight=True,
                                ),
                                close_icon_btn,
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        ft.Divider(height=1),
                        ft.Container(height=4),
                        stats_container,
                        ft.Divider(height=1),
                        ft.Container(height=4),
                        sede_dd,
                        ft.Container(height=8),
                        ft.Text("Marcas asignadas", size=12, color=ft.Colors.GREY_500),
                        ft.Container(
                            content=marcas_col,
                            bgcolor=ft.Colors.with_opacity(0.04, primary_color),
                            border_radius=10,
                            padding=ft.Padding.all(10),
                            height=150,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        ),
                        ft.Container(height=6),
                        infaltables_sw,
                        ft.Container(height=8),
                        status_text,
                        save_btn,
                        ft.Container(height=16),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=8,
                ),
                padding=ft.Padding.all(16),
            ),
            open=True,
        )

        bs_ref["sheet"] = bs

        load_marcas(sede_state["value"])
        load_user_stats()
        page.overlay.append(bs)
        page.update()

    def _close(bs):
        bs.open = False
        if bs in page.overlay:
            page.overlay.remove(bs)
        page.update()

    # ─── Header ───────────────────────────────────────────────────────────────

    header = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Image(
                            src="assets/images/Prisma.png",
                            height=34,
                            fit="contain",
                            error_content=ft.Text(
                                "Prisma", size=13, weight=ft.FontWeight.BOLD,
                                color=primary_color,
                            ),
                        ),
                        ft.Text("Usuarios", size=16, weight=ft.FontWeight.BOLD,
                                expand=True),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH_ROUNDED,
                            icon_color=primary_color,
                            on_click=lambda e: load_usuarios(),
                            tooltip="Actualizar",
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                filter_row,
                search_field,
            ],
            spacing=6,
            tight=True,
        ),
        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        border=ft.Border(
            bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.2, primary_color))
        ),
    )

    # ─── Init ─────────────────────────────────────────────────────────────────

    mark_notifs_read()
    load_usuarios()

    return ft.Container(
        content=ft.Column(
            controls=[header, content_area],
            expand=True,
            spacing=0,
        ),
        expand=True,
        on_click=handle_interaction,
    )
