import flet as ft
import asyncio
import random
import time

INFALTABLES = {"B", "D", "F"}

_INSTRUCCIONES = {
    "categorias":    "¿A qué categoría principal pertenece?",
    "subcategorias": "¿A qué subcategoría pertenece?",
    "productos":     "¿Cuál es el código completo?",
    "contrarreloj":  "¿A qué categoría pertenece?",
}

_LABELS = {
    "categorias":    "Reto Categorías",
    "subcategorias": "Reto Subcategorías",
    "productos":     "Reto Productos",
    "contrarreloj":  "Contrarreloj",
}


def panel_desafios_view(
    page: ft.Page,
    time_offset: float,
    on_interaction,
    primary_color,
    categorias: list,
    subcategorias: list,
    productos: list,
    user_id: str,
    sede: str,
):
    from session_manager import register_interaction

    is_dark = page.theme_mode == ft.ThemeMode.DARK
    text_color = ft.Colors.WHITE if is_dark else ft.Colors.BLACK
    text_secondary = ft.Colors.GREY_400 if is_dark else ft.Colors.GREY_700

    def handle_interaction(e=None):
        register_interaction(time_offset)
        if on_interaction:
            on_interaction()

    # ─── Estado del juego ─────────────────────────────────────────────────────

    game = {
        "tipo": None,
        "difficulty": 4,
        "questions": [],
        "index": 0,
        "aciertos": 0,
        "fallos": 0,
        "errors": [],
        "start_time": 0.0,
        "timer_running": False,
        "seconds_left": 90,
        "game_over": False,
        "saved": False,
    }

    content_area = ft.Container(expand=True)
    timer_ref = [None]

    # ─── Generación de preguntas ──────────────────────────────────────────────

    def _code_prod(p):
        return p.get("codigo_completo") or (
            f"{p.get('categoria_codigo','')}-"
            f"{p.get('subcategoria_codigo','')}-"
            f"{p.get('codigo','')}"
        )

    def make_cat_questions(diff):
        if len(categorias) < 2:
            return []
        pool = categorias[:]
        random.shuffle(pool)
        qs = []
        for cat in pool[:10]:
            correct = (cat.get("codigo") or "").strip()
            others = [(c.get("codigo") or "").strip() for c in categorias
                      if (c.get("codigo") or "").strip() != correct]
            if len(others) < diff - 1:
                continue
            opts = [correct] + random.sample(others, diff - 1)
            random.shuffle(opts)
            qs.append({
                "tipo_elemento": "categoria",
                "display": cat.get("nombre", ""),
                "correct": correct,
                "options": opts,
                "codigo": correct,
                "nombre": cat.get("nombre", ""),
                "mnemotecnia": cat.get("mnemotecnia"),
            })
        return qs

    def make_sub_questions(diff):
        if len(subcategorias) < 2:
            return []
        pool = subcategorias[:]
        random.shuffle(pool)
        qs = []
        for sub in pool[:10]:
            correct = (sub.get("codigo") or "").strip()
            others = [(s.get("codigo") or "").strip() for s in subcategorias
                      if (s.get("codigo") or "").strip() != correct]
            if len(others) < diff - 1:
                continue
            opts = [correct] + random.sample(others, diff - 1)
            random.shuffle(opts)
            qs.append({
                "tipo_elemento": "subcategoria",
                "display": sub.get("nombre", ""),
                "correct": correct,
                "options": opts,
                "codigo": f"{sub.get('categoria_codigo','')}-{correct}",
                "nombre": sub.get("nombre", ""),
                "mnemotecnia": sub.get("mnemotecnia"),
            })
        return qs

    def make_prod_questions(diff):
        if len(productos) < 2:
            return []
        pool = productos[:]
        random.shuffle(pool)
        qs = []
        all_codes = [_code_prod(p) for p in productos]
        for prod in pool[:10]:
            correct = _code_prod(prod)
            others = [c for c in all_codes if c != correct]
            if len(others) < diff - 1:
                continue
            opts = [correct] + random.sample(others, diff - 1)
            random.shuffle(opts)
            qs.append({
                "tipo_elemento": "producto",
                "display": prod.get("nombre", ""),
                "correct": correct,
                "options": opts,
                "codigo": correct,
                "nombre": prod.get("nombre", ""),
                "mnemotecnia": prod.get("mnemotecnia"),
            })
        return qs

    def make_mixed(diff):
        qs = make_cat_questions(diff) + make_sub_questions(diff) + make_prod_questions(diff)
        random.shuffle(qs)
        return qs

    # ─── Guardado en BD ───────────────────────────────────────────────────────

    def save_result():
        if game["saved"]:
            return
        game["saved"] = True
        duration = max(1, int(time.time() - game["start_time"]))
        tipo = game["tipo"]
        errors = list(game["errors"])

        def do_save():
            try:
                from auth import get_client
                client = get_client()
                res = client.table("resultados_codex").insert({
                    "usuario_id": user_id,
                    "tipo_juego": tipo,
                    "aciertos": game["aciertos"],
                    "fallos": game["fallos"],
                    "total_preguntas": game["aciertos"] + game["fallos"],
                    "duracion_segundos": duration,
                    "sede": sede,
                    "configuracion": {"dificultad": game["difficulty"]},
                    "detalle_interacciones": [],
                }).execute()
                if res.data and errors:
                    resultado_id = res.data[0]["id"]
                    for err in errors:
                        client.table("errores_partida").insert({
                            "resultado_id": resultado_id,
                            "usuario_id": user_id,
                            "tipo_elemento": err["tipo_elemento"],
                            "elemento_codigo": err["codigo"],
                            "elemento_nombre": err["nombre"],
                            "mnemotecnia": err.get("mnemotecnia"),
                            "veces_fallado": 1,
                        }).execute()
            except Exception:
                pass

        page.run_thread(do_save)

    # ─── Menú principal ───────────────────────────────────────────────────────

    def show_menu():
        game["timer_running"] = False
        game["game_over"] = True
        handle_interaction()

        def card(icon, title, sub, tipo):
            return ft.GestureDetector(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(icon, size=32, color=primary_color),
                            ft.Text(title, size=14, weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER),
                            ft.Text(sub, size=11, color=ft.Colors.GREY_500,
                                    text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    bgcolor=ft.Colors.with_opacity(0.07, primary_color),
                    border_radius=16,
                    padding=ft.Padding.all(16),
                    border=ft.Border.all(1, ft.Colors.with_opacity(0.2, primary_color)),
                    alignment=ft.Alignment(0, 0),
                ),
                on_tap=lambda e, t=tipo: show_difficulty(t),
            )

        content_area.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text("Panel de Desafíos", size=18,
                                        weight=ft.FontWeight.BOLD),
                        padding=ft.Padding.only(bottom=12),
                    ),
                    ft.GridView(
                        controls=[
                            card(ft.Icons.FOLDER_OUTLINED, "Categorías",
                                 "Identifica el código de 2 dígitos", "categorias"),
                            card(ft.Icons.CATEGORY_OUTLINED, "Subcategorías",
                                 "Identifica los 2 dígitos del centro", "subcategorias"),
                            card(ft.Icons.INVENTORY_2_OUTLINED, "Productos",
                                 "Selecciona el código completo", "productos"),
                            card(ft.Icons.TIMER_OUTLINED, "Contrarreloj",
                                 "90 segundos, preguntas mixtas", "contrarreloj"),
                        ],
                        max_extent=220,
                        runs_count=2,
                        spacing=12,
                        run_spacing=12,
                        expand=True,
                    ),
                ],
                spacing=0,
            ),
            expand=True,
            padding=ft.Padding.all(16),
        )
        page.update()

    # ─── Selección de dificultad ──────────────────────────────────────────────

    def show_difficulty(tipo: str):
        handle_interaction()
        game["tipo"] = tipo
        sel = {"n": 4}
        btn_refs = {}

        def diff_btn(n):
            c = ft.Container(
                content=ft.Text(str(n), size=16, weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER),
                width=60, height=60, border_radius=30,
                alignment=ft.Alignment(0, 0),
                bgcolor=ft.Colors.with_opacity(0.1, primary_color),
                border=ft.Border.all(2, ft.Colors.with_opacity(0.3, primary_color)),
            )
            btn_refs[n] = c

            def on_tap(e, num=n):
                handle_interaction()
                sel["n"] = num
                for k, b in btn_refs.items():
                    if k == num:
                        b.bgcolor = primary_color
                        b.border = ft.Border.all(2, primary_color)
                    else:
                        b.bgcolor = ft.Colors.with_opacity(0.1, primary_color)
                        b.border = ft.Border.all(2, ft.Colors.with_opacity(0.3, primary_color))
                page.update()

            return ft.GestureDetector(content=c, on_tap=on_tap)

        content_area.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Button(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, size=18),
                                ft.Text("Volver"),
                            ],
                            spacing=4, tight=True,
                        ),
                        on_click=lambda e: show_menu(),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.TRANSPARENT,
                            shadow_color=ft.Colors.TRANSPARENT,
                            overlay_color=ft.Colors.TRANSPARENT,
                        ),
                    ),
                    ft.Container(height=8),
                    ft.Text(_LABELS.get(tipo, tipo), size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(height=4),
                    ft.Text("Número de opciones por pregunta:", size=13,
                            color=ft.Colors.GREY_500),
                    ft.Container(height=16),
                    ft.Row(
                        controls=[diff_btn(n) for n in [2, 4, 6, 8]],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=16,
                    ),
                    ft.Container(height=24),
                    ft.Button(
                        content=ft.Text("Comenzar", color=ft.Colors.WHITE,
                                        weight=ft.FontWeight.W_600),
                        on_click=lambda e: start_game(sel["n"]),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                            bgcolor=primary_color,
                        ),
                        width=200,
                        height=48,
                    ),
                    ft.Container(height=24),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            expand=True,
            padding=ft.Padding.all(24),
        )
        page.update()

    # ─── Inicio del juego ─────────────────────────────────────────────────────

    def start_game(difficulty: int):
        handle_interaction()
        content_area.content = ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )
        page.update()

        def do_start():
            game.update({
                "difficulty": difficulty,
                "index": 0,
                "aciertos": 0,
                "fallos": 0,
                "errors": [],
                "saved": False,
                "game_over": False,
                "start_time": time.time(),
            })
            tipo = game["tipo"]

            if tipo == "categorias":
                game["questions"] = make_cat_questions(difficulty)
            elif tipo == "subcategorias":
                game["questions"] = make_sub_questions(difficulty)
            elif tipo == "productos":
                game["questions"] = make_prod_questions(difficulty)
            else:
                game["questions"] = make_mixed(difficulty)
                game["seconds_left"] = 90
                game["timer_running"] = True
                page.run_task(run_timer)

            if not game["questions"]:
                show_no_data()
                return

            show_question()

        page.run_thread(do_start)

    async def run_timer():
        while game["timer_running"] and game["seconds_left"] > 0:
            await asyncio.sleep(1)
            if not game["timer_running"]:
                break
            game["seconds_left"] -= 1
            if timer_ref[0] is not None:
                timer_ref[0].value = str(game["seconds_left"])
            try:
                page.update()
            except Exception:
                game["timer_running"] = False
                break
        if game["timer_running"] and game["seconds_left"] == 0:
            game["timer_running"] = False
            show_results()

    # ─── Pantalla de pregunta ─────────────────────────────────────────────────

    def show_question():
        if game["game_over"]:
            return

        questions = game["questions"]
        idx = game["index"]

        if idx >= len(questions):
            game["timer_running"] = False
            show_results()
            return

        q = questions[idx]
        tipo = game["tipo"]
        total = len(questions)
        answered = [False]

        is_last = (idx == total - 1)

        # ── Widgets de estado (se mutan al responder) ──────────────────────────

        aciertos_txt = ft.Text(
            str(game["aciertos"]), size=13,
            weight=ft.FontWeight.W_600, color=ft.Colors.GREEN_600,
        )
        fallos_txt = ft.Text(
            str(game["fallos"]), size=13,
            weight=ft.FontWeight.W_600, color=ft.Colors.RED_600,
        )
        progress_bar = ft.ProgressBar(
            value=idx / total if total > 0 else 0,
            color=primary_color,
            bgcolor=ft.Colors.with_opacity(0.2, primary_color),
            height=5,
        )

        # ── Feedback (oculto hasta responder) ─────────────────────────────────

        feedback = ft.Container(visible=False, border_radius=10)

        # ── Botón siguiente (oculto hasta responder) ───────────────────────────

        next_label = "Ver resultados →" if is_last else "Siguiente →"
        next_btn = ft.Container(visible=False)

        def on_next(e):
            handle_interaction()
            game["index"] += 1
            show_question()

        next_btn.content = ft.Button(
            content=ft.Text(next_label, color=ft.Colors.WHITE,
                            weight=ft.FontWeight.W_600, size=15),
            on_click=on_next,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                bgcolor=primary_color,
            ),
            expand=True,
        )

        # ── Opciones de respuesta ──────────────────────────────────────────────

        options_state = []  # (opt_val, container, text_widget)

        def make_opt_btn(opt):
            opt_txt = ft.Text(
                opt, size=13, text_align=ft.TextAlign.CENTER,
                weight=ft.FontWeight.W_500, no_wrap=False,
                color=text_color,
            )
            c = ft.Container(
                content=opt_txt,
                bgcolor=ft.Colors.with_opacity(0.07, primary_color),
                border_radius=30,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.2, primary_color)),
                padding=ft.Padding.symmetric(vertical=14, horizontal=16),
                alignment=ft.Alignment(0, 0),
                expand=True,
            )
            options_state.append((opt, c, opt_txt))

            def on_tap(e, chosen=opt):
                if answered[0]:
                    return
                answered[0] = True
                handle_interaction()

                correct = q["correct"]
                is_ok = chosen.strip() == correct.strip()

                # Colorear todos los botones
                for o_val, o_cont, o_txt in options_state:
                    if o_val.strip() == correct.strip():
                        o_cont.bgcolor = ft.Colors.GREEN_400
                        o_cont.border = ft.Border.all(2, ft.Colors.GREEN_700)
                        o_txt.color = ft.Colors.WHITE
                    elif o_val == chosen and not is_ok:
                        o_cont.bgcolor = ft.Colors.RED_400
                        o_cont.border = ft.Border.all(2, ft.Colors.RED_700)
                        o_txt.color = ft.Colors.WHITE

                if is_ok:
                    game["aciertos"] += 1
                    aciertos_txt.value = str(game["aciertos"])
                    feedback.visible = True
                    feedback.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.GREEN_400)
                    feedback.padding = ft.Padding.all(12)
                    feedback.content = ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED,
                                    color=ft.Colors.GREEN_400, size=20),
                            ft.Text("¡Correcto!", color=ft.Colors.GREEN_400,
                                    size=14, weight=ft.FontWeight.W_500),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                else:
                    game["fallos"] += 1
                    fallos_txt.value = str(game["fallos"])
                    game["errors"].append(q)

                    mnem = q.get("mnemotecnia")
                    show_hint = (tipo in ("categorias", "contrarreloj")) and bool(mnem)

                    hint_row = ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LIGHTBULB_OUTLINE,
                                    size=14, color=ft.Colors.ORANGE_400),
                            ft.Text(mnem, size=12, italic=True,
                                    color=ft.Colors.ORANGE_400, expand=True,
                                    no_wrap=False),
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ) if show_hint else None

                    feedback.visible = True
                    feedback.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.ORANGE_400)
                    feedback.padding = ft.Padding.all(12)
                    feedback.content = ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.CANCEL_ROUNDED,
                                            color=ft.Colors.RED_400, size=20),
                                    ft.Text("Incorrecto", color=ft.Colors.RED_400,
                                            size=14, weight=ft.FontWeight.W_500),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            *(([hint_row]) if hint_row else []),
                        ],
                        spacing=6,
                        tight=True,
                    )

                next_btn.visible = True
                page.update()

            return ft.GestureDetector(content=c, on_tap=on_tap)

        opt_controls = [make_opt_btn(o) for o in q["options"]]
        rows = []
        for i in range(0, len(opt_controls), 2):
            rows.append(ft.Row(controls=opt_controls[i:i + 2], spacing=10))
        opts_widget = ft.Column(controls=rows, spacing=10)

        # ── Card de la pregunta ────────────────────────────────────────────────

        q_card = ft.Container(
            content=ft.Text(
                q["display"], size=17, weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER, no_wrap=False,
                color=ft.Colors.with_opacity(0.85, primary_color),
            ),
            bgcolor=ft.Colors.with_opacity(0.1, primary_color),
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=12, vertical=12),
            alignment=ft.Alignment(0, 0),
        )

        # ── Ensamblado ─────────────────────────────────────────────────────────

        top_controls = []

        if tipo == "contrarreloj":
            t_label = ft.Text(
                str(game["seconds_left"]), size=22,
                weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_400,
            )
            timer_ref[0] = t_label
            top_controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.TIMER_ROUNDED,
                                    color=ft.Colors.ORANGE_400, size=18),
                            t_label,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    padding=ft.Padding.only(bottom=8),
                )
            )

        top_controls += [
            # Fila: "Pregunta X/Y" + contadores
            ft.Row(
                controls=[
                    ft.Text(
                        f"Pregunta {idx + 1} / {total}",
                        size=13, weight=ft.FontWeight.W_500,
                        color=text_secondary,
                    ),
                    ft.Container(expand=True),
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED,
                            size=16, color=ft.Colors.GREEN_600),
                    aciertos_txt,
                    ft.Container(width=10),
                    ft.Icon(ft.Icons.CANCEL_ROUNDED,
                            size=16, color=ft.Colors.RED_600),
                    fallos_txt,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Container(height=6),
            progress_bar,
            ft.Container(height=16),
            # Instrucción
            ft.Text(
                _INSTRUCCIONES.get(tipo, ""),
                size=12, color=ft.Colors.GREY_500,
            ),
            ft.Container(height=6),
            # Card del elemento a identificar
            q_card,
            ft.Container(height=18),
            # Grid de opciones
            opts_widget,
            ft.Container(height=12),
            # Feedback (oculto)
            feedback,
            ft.Container(height=8),
            # Botón siguiente (oculto)
            next_btn,
        ]

        content_area.content = ft.Container(
            content=ft.Column(
                controls=top_controls,
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            padding=ft.Padding.all(16),
        )
        page.update()

    # ─── Pantalla de resultados ───────────────────────────────────────────────

    def show_results():
        if game["game_over"]:
            return
        game["game_over"] = True
        game["timer_running"] = False
        timer_ref[0] = None
        save_result()
        handle_interaction()

        total = game["aciertos"] + game["fallos"]
        efectividad = round(game["aciertos"] / total * 100) if total > 0 else 0
        errors = game["errors"]

        if efectividad >= 80:
            result_emoji, result_msg = "🏆", "¡Excelente!"
            result_color = ft.Colors.AMBER_600
        elif efectividad >= 50:
            result_emoji, result_msg = "👍", "¡Buen trabajo!"
            result_color = ft.Colors.GREEN_600
        else:
            result_emoji, result_msg = "💪", "Sigue practicando"
            result_color = ft.Colors.ORANGE_600

        def stat_card(label, value, color):
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(value, size=24, weight=ft.FontWeight.BOLD,
                                color=color, text_align=ft.TextAlign.CENTER),
                        ft.Text(label, size=11, color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                ),
                bgcolor=ft.Colors.with_opacity(0.08, color),
                border_radius=12,
                padding=ft.Padding.symmetric(horizontal=8, vertical=14),
                expand=True,
            )

        # ── Cards de errores ───────────────────────────────────────────────────

        error_section = []
        if errors:
            error_section = [
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED,
                                size=16, color=ft.Colors.ORANGE_500),
                        ft.Text("Errores cometidos", size=14,
                                weight=ft.FontWeight.W_600),
                    ],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=8),
            ]
            for err in errors:
                mnem = err.get("mnemotecnia")
                error_section.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            content=ft.Text(
                                                err.get("codigo", ""),
                                                size=12, weight=ft.FontWeight.BOLD,
                                                color=primary_color,
                                                font_family="monospace",
                                            ),
                                            bgcolor=ft.Colors.with_opacity(
                                                0.15, primary_color),
                                            border_radius=6,
                                            padding=ft.Padding.symmetric(
                                                horizontal=8, vertical=3),
                                        ),
                                        ft.Text(
                                            err.get("nombre", ""),
                                            size=13, expand=True, no_wrap=False,
                                            weight=ft.FontWeight.W_500,
                                        ),
                                    ],
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Text(
                                    mnem if mnem else "Mnemotecnia pendiente",
                                    size=11, italic=True, no_wrap=False,
                                    color=(ft.Colors.GREY_600 if mnem
                                           else ft.Colors.with_opacity(
                                               0.5, ft.Colors.GREY_600)),
                                ),
                            ],
                            spacing=6,
                            tight=True,
                        ),
                        bgcolor=ft.Colors.SURFACE,
                        border_radius=10,
                        padding=ft.Padding.all(12),
                        border=ft.Border(
                            left=ft.BorderSide(3, primary_color)
                        ),
                        shadow=ft.BoxShadow(
                            blur_radius=3,
                            offset=ft.Offset(0, 1),
                            color=ft.Colors.with_opacity(0.08, primary_color),
                        ),
                    )
                )
                error_section.append(ft.Container(height=8))
        else:
            error_section = [
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.VERIFIED_ROUNDED,
                                    color=ft.Colors.GREEN_400, size=20),
                            ft.Text("¡Sin errores! Perfecto 🎉",
                                    size=13, color=ft.Colors.GREEN_400,
                                    weight=ft.FontWeight.W_500),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN_400),
                    border_radius=10,
                    padding=ft.Padding.all(14),
                )
            ]

        content_area.content = ft.Container(
            content=ft.Column(
                controls=[
                    # ── Card de resultado ──────────────────────────────────────
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(result_emoji, size=48,
                                        text_align=ft.TextAlign.CENTER),
                                ft.Text(result_msg, size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=result_color,
                                        text_align=ft.TextAlign.CENTER),
                                ft.Container(height=4),
                                ft.Text(
                                    _LABELS.get(game["tipo"], ""),
                                    size=12, color=ft.Colors.GREY_500,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                        ),
                        bgcolor=ft.Colors.with_opacity(0.06, primary_color),
                        border_radius=16,
                        padding=ft.Padding.all(20),
                        border=ft.Border.all(
                            1, ft.Colors.with_opacity(0.15, primary_color)
                        ),
                    ),
                    ft.Container(height=12),
                    # ── Métricas ───────────────────────────────────────────────
                    ft.Row(
                        controls=[
                            stat_card("Aciertos", str(game["aciertos"]),
                                      ft.Colors.GREEN_600),
                            stat_card("Fallos", str(game["fallos"]),
                                      ft.Colors.RED_500),
                            stat_card("Efectividad", f"{efectividad}%",
                                      primary_color),
                        ],
                        spacing=8,
                    ),
                    ft.Container(height=16),
                    # ── Tabla de errores / mensaje de éxito ────────────────────
                    *error_section,
                    ft.Container(height=20),
                    # ── Botones de acción ──────────────────────────────────────
                    ft.Button(
                        content=ft.Text("Jugar otra vez", color=ft.Colors.WHITE,
                                        weight=ft.FontWeight.W_600),
                        on_click=lambda e: show_difficulty(game["tipo"]),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                            bgcolor=primary_color,
                        ),
                        expand=True,
                    ),
                    ft.Container(height=8),
                    ft.OutlinedButton(
                        content=ft.Text("Volver al menú",
                                        weight=ft.FontWeight.W_500),
                        on_click=lambda e: show_menu(),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                            side=ft.BorderSide(1, primary_color),
                        ),
                        expand=True,
                    ),
                    ft.Container(height=8),
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            padding=ft.Padding.all(16),
        )
        page.update()

    # ─── Sin datos ────────────────────────────────────────────────────────────

    def show_no_data():
        content_area.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=48,
                            color=ft.Colors.ORANGE_400),
                    ft.Text(
                        "No hay suficientes elementos para este reto.\n"
                        "Asegúrate de tener datos en caché.",
                        size=13, text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.GREY_400,
                    ),
                    ft.Container(height=12),
                    ft.Button(
                        content=ft.Text("Volver", color=ft.Colors.WHITE),
                        on_click=lambda e: show_menu(),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                            bgcolor=primary_color,
                        ),
                        expand=True,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            alignment=ft.Alignment(0, 0),
            expand=True,
            padding=ft.Padding.all(24),
        )
        page.update()

    # ─── Init ─────────────────────────────────────────────────────────────────

    show_menu()

    return ft.Container(
        content=content_area,
        expand=True,
        on_click=handle_interaction,
    )
