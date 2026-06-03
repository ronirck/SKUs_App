import flet as ft
import threading
import asyncio
from auth import login, register, restore_session, logout, reset_password, verify_otp_token, update_password_after_reset
from session_manager import (
    start_interval,
    close_interval,
    register_interaction,
    check_midnight_crossing,
    has_pending_data,
    get_pending_data,
    clear_local_session_data,
    recover_incomplete_interval,
    save_theme_preferences,
    load_theme_preferences,
    save_productos_cache,
    load_productos_cache,
    fetch_all,
)
from updater import check_for_updates

COLORES_POR_SEDE = {
    "FEBECA": ft.Colors.BLUE_400,
    "COFERSA": ft.Colors.BLUE_400,
    "SILLACA": ft.Colors.PINK_400,
    "BEVAL": ft.Colors.GREEN_400,
    "MUNDIAL DE PARTES": ft.Colors.GREEN_400,
}

LOGOS_SEDE = {
    "FEBECA": "assets/images/Febeca.png",
    "SILLACA": "assets/images/Sillaca.png",
    "BEVAL": "assets/images/Beval.png",
    "COFERSA": "assets/images/Cofersa.png",
    "MUNDIAL DE PARTES": "assets/images/Mundial.png",
}

APP_VERSION = "2.2.0"


class AppState:
    def __init__(self):
        self.user_id: str = None
        self.user_email: str = None
        self.username: str = None
        self.time_offset: float = 0.0
        self.session_active: bool = False
        self.clock_running: bool = False
        self.elapsed_seconds: int = 0
        self.primary_color = ft.Colors.BLUE_400
        self.rol: str = "user"
        self.sede: str = "FEBECA"
        self.marcas_permitidas: list = []
        self.solo_infaltables: bool = False
        self.config_version: int = 0
        self.categorias_cache: list = []
        self.subcategorias_cache: list = []
        self.productos_cache: list = []
        self.notif_count: int = 0
        self.update_checked: bool = False


def main(page: ft.Page):
    page.title = "SKUs App"
    page.padding = ft.Padding.only(top=40)
    page.safe_area = True

    state = AppState()

    _, is_dark = load_theme_preferences()
    page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT

    clock_text = ft.Text(
        value="00:00:00",
        size=13,
        color=ft.Colors.GREY_500,
        text_align=ft.TextAlign.CENTER,
    )

    # ─── Sincronización con Supabase ─────────────────────────────────────────

    def sync_to_supabase():
        if not state.user_id or not has_pending_data():
            return
        pending_seconds, pending_date = get_pending_data()
        if pending_seconds <= 0 or pending_date is None:
            return
        try:
            from auth import get_client
            client = get_client()
            existing = (
                client.table("session_logs")
                .select("id, duration_seconds")
                .eq("user_id", state.user_id)
                .eq("date", pending_date)
                .execute()
            )
            if existing.data:
                record = existing.data[0]
                client.table("session_logs").update(
                    {"duration_seconds": record["duration_seconds"] + pending_seconds, "updated_at": "now()"}
                ).eq("id", record["id"]).execute()
            else:
                client.table("session_logs").insert(
                    {"user_id": state.user_id, "date": pending_date, "duration_seconds": pending_seconds}
                ).execute()
            clear_local_session_data()
        except Exception:
            pass

    # ─── Cronómetro ──────────────────────────────────────────────────────────

    def format_time(seconds: int) -> str:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    async def clock_loop():
        inactivity_counter = [0]
        while state.clock_running:
            await asyncio.sleep(1)
            if not state.clock_running:
                break
            state.elapsed_seconds += 1
            clock_text.value = format_time(state.elapsed_seconds)
            inactivity_counter[0] += 1
            if check_midnight_crossing(state.time_offset):
                handle_midnight_crossing()
                inactivity_counter[0] = 0
            if inactivity_counter[0] >= 60:
                elapsed = close_interval(state.time_offset)
                if elapsed > 0:
                    threading.Thread(target=sync_to_supabase, daemon=True).start()
                inactivity_counter[0] = 0
            try:
                page.update()
            except Exception:
                state.clock_running = False
                break

    def start_clock():
        state.clock_running = True
        state.elapsed_seconds = 0
        clock_text.value = "00:00:00"
        page.run_task(clock_loop)

    # ─── Lógica de sesión ────────────────────────────────────────────────────

    def handle_midnight_crossing():
        close_interval(state.time_offset)
        from auth import get_client
        try:
            client = get_client()
            pending_seconds, pending_date = get_pending_data()
            if pending_seconds > 0 and pending_date is not None:
                existing = (
                    client.table("session_logs")
                    .select("id, duration_seconds")
                    .eq("user_id", state.user_id)
                    .eq("date", pending_date)
                    .execute()
                )
                if existing.data:
                    record = existing.data[0]
                    client.table("session_logs").update(
                        {"duration_seconds": record["duration_seconds"] + pending_seconds, "updated_at": "now()"}
                    ).eq("id", record["id"]).execute()
                else:
                    client.table("session_logs").insert(
                        {"user_id": state.user_id, "date": pending_date, "duration_seconds": pending_seconds}
                    ).execute()
                clear_local_session_data()
        except Exception:
            pass
        start_interval(state.time_offset)

    def on_interaction():
        if state.session_active:
            register_interaction(state.time_offset)

    def on_theme_change(new_mode: ft.ThemeMode):
        page.theme_mode = new_mode
        save_theme_preferences("sede_color", new_mode == ft.ThemeMode.DARK)
        page.update()
        profile_index = 3 if state.rol == "admin" else 2
        show_main_view(selected_index=profile_index)

    def end_session():
        state.clock_running = False
        state.session_active = False
        close_interval(state.time_offset)
        logout(state.user_id, state.time_offset)
        state.user_id = None
        state.user_email = None
        state.username = None
        state.elapsed_seconds = 0
        state.rol = "user"
        state.sede = "FEBECA"
        state.marcas_permitidas = []
        state.categorias_cache = []
        state.subcategorias_cache = []
        state.productos_cache = []
        state.notif_count = 0
        clock_text.value = "00:00:00"
        show_auth_view()

    # ─── Caché SKU ───────────────────────────────────────────────────────────

    def reload_sku_cache(client, remote_version: int):
        sede = state.sede
        print(f"[cache] Recargando caché para sede={sede}, marcas={state.marcas_permitidas}")
        cats = fetch_all(client, "categorias", lambda q: q.select("*").eq("sede", sede))
        subs = fetch_all(client, "subcategorias", lambda q: q.select("*").eq("sede", sede))
        marcas = state.marcas_permitidas
        prods = fetch_all(
            client, "productos",
            lambda q: q.select("*").eq("sede", sede).in_("marca", marcas) if marcas
            else q.select("*").eq("sede", sede),
        )
        print(f"[cache] Descargados: cats={len(cats)}, subs={len(subs)}, prods={len(prods)}")
        state.config_version = remote_version
        state.categorias_cache = cats
        state.subcategorias_cache = subs
        state.productos_cache = prods
        save_productos_cache({
            "config_version": remote_version,
            "sede": sede,
            "marcas_permitidas": state.marcas_permitidas,
            "solo_infaltables": state.solo_infaltables,
            "categorias": cats,
            "subcategorias": subs,
            "productos": prods,
        })

    def save_cache_callback(cats, subs, prods, new_version=None):
        state.categorias_cache = cats
        state.subcategorias_cache = subs
        state.productos_cache = prods
        if new_version is not None:
            state.config_version = new_version
        save_productos_cache({
            "config_version": state.config_version,
            "sede": state.sede,
            "marcas_permitidas": state.marcas_permitidas,
            "solo_infaltables": state.solo_infaltables,
            "categorias": cats,
            "subcategorias": subs,
            "productos": prods,
        })

    # ─── Setup post-autenticación ─────────────────────────────────────────────

    def post_auth_setup(user_id: str, user_email: str, username: str, time_offset: float):
        state.user_id = user_id
        state.user_email = user_email
        state.username = username
        state.time_offset = time_offset

        page.controls.clear()
        page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(),
                        ft.Text("Preparando tu sesión...", color=ft.Colors.GREY_500, size=13),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
            )
        )
        page.update()

        try:
            from auth import get_client
            client = get_client()

            perfil_res = (
                client.table("perfil_usuario").select("*").eq("usuario_id", user_id).execute()
            )

            if not perfil_res.data:
                client.table("perfil_usuario").insert({
                    "usuario_id": user_id, "nombre": username,
                    "email": user_email, "rol": "user",
                }).execute()
                client.table("usuario_config").insert({
                    "usuario_id": user_id, "sede": "FEBECA",
                    "marcas_permitidas": [], "solo_infaltables": False, "config_version": 1,
                }).execute()
                try:
                    client.table("notificaciones_admin").insert({
                        "tipo": "nuevo_registro",
                        "payload": {"nombre": username, "email": user_email},
                    }).execute()
                except Exception:
                    pass
                state.rol = "user"
            else:
                client.table("perfil_usuario").update(
                    {"nombre": username, "email": user_email}
                ).eq("usuario_id", user_id).execute()
                state.rol = perfil_res.data[0].get("rol", "user")

            config_res = (
                client.table("usuario_config").select("*").eq("usuario_id", user_id).execute()
            )
            remote_version = 1
            if config_res.data:
                cfg = config_res.data[0]
                state.sede = cfg.get("sede", "FEBECA")
                state.marcas_permitidas = cfg.get("marcas_permitidas") or []
                state.solo_infaltables = cfg.get("solo_infaltables", False)
                remote_version = cfg.get("config_version", 1)
            else:
                state.sede = "FEBECA"
                state.marcas_permitidas = []
                state.solo_infaltables = False

            if state.rol == "admin":
                state.primary_color = ft.Colors.GREY_600
            else:
                state.primary_color = COLORES_POR_SEDE.get(state.sede, ft.Colors.BLUE_400)

            if state.rol == "admin":
                try:
                    notif_res = (
                        client.table("notificaciones_admin")
                        .select("id").eq("leido", False).execute()
                    )
                    state.notif_count = len(notif_res.data) if notif_res.data else 0
                except Exception:
                    state.notif_count = 0

            if state.rol == "user":
                local_cache = load_productos_cache()
                needs_reload = (
                    local_cache is None
                    or local_cache.get("config_version") != remote_version
                    or local_cache.get("sede") != state.sede
                    or local_cache.get("marcas_permitidas") != state.marcas_permitidas
                )
                print(f"[cache] needs_reload={needs_reload}, remote_ver={remote_version}, "
                      f"cached_ver={local_cache.get('config_version') if local_cache else None}")
                if needs_reload:
                    reload_sku_cache(client, remote_version)
                else:
                    state.config_version = remote_version
                    state.categorias_cache = local_cache.get("categorias", [])
                    state.subcategorias_cache = local_cache.get("subcategorias", [])
                    state.productos_cache = local_cache.get("productos", [])
                    print(f"[cache] Usando caché local: cats={len(state.categorias_cache)}, "
                          f"prods={len(state.productos_cache)}")

        except Exception:
            if state.rol == "admin":
                state.primary_color = ft.Colors.GREY_600
            else:
                state.primary_color = COLORES_POR_SEDE.get(state.sede, ft.Colors.BLUE_400)

        state.session_active = True
        start_interval(time_offset)
        start_clock()
        show_main_view()

    # ─── Vista de autenticación ───────────────────────────────────────────────

    def show_auth_view(mode: str = "login", otp_email: str = ""):
        page.controls.clear()

        def _back_btn():
            return ft.Button(
                content=ft.Text("Volver al inicio de sesión", color=ft.Colors.BLUE_400),
                on_click=lambda e: show_auth_view(mode="login"),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.TRANSPARENT,
                    shadow_color=ft.Colors.TRANSPARENT,
                    overlay_color=ft.Colors.TRANSPARENT,
                ),
            )

        def _wrap(controls):
            page.add(
                ft.Container(
                    content=ft.Column(
                        controls=controls,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    expand=True,
                    padding=ft.Padding.symmetric(horizontal=24),
                )
            )
            page.update()

        # ─── Estado VERIFY_TOKEN: ingresar código OTP ─────────────────────────

        if mode == "verify_token":
            token_field = ft.TextField(
                label="Código de verificación",
                input_filter=ft.NumbersOnlyInputFilter(),
                max_length=8,
                border_radius=10,
                width=200,
                text_align=ft.TextAlign.CENTER,
                text_size=28,
                on_change=lambda e: on_interaction(),
            )
            verify_status = ft.Text(value="", size=13, text_align=ft.TextAlign.CENTER, color=ft.Colors.RED_400)

            verify_btn = ft.Button(
                content=ft.Text("Verificar código", color=ft.Colors.WHITE),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    bgcolor=ft.Colors.BLUE_400,
                ),
                width=300,
            )

            def handle_verify(e):
                token = token_field.value.strip()
                if not (6 <= len(token) <= 8):
                    verify_status.value = "El código debe tener entre 6 y 8 dígitos"
                    verify_status.color = ft.Colors.RED_400
                    page.update()
                    return

                verify_btn.content = ft.Row(
                    controls=[ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE)],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
                verify_btn.disabled = True
                verify_status.value = ""
                page.update()

                def do_verify():
                    result = verify_otp_token(otp_email, token)
                    if result["success"]:
                        show_auth_view(mode="new_password", otp_email=otp_email)
                    else:
                        verify_btn.content = ft.Text("Verificar código", color=ft.Colors.WHITE)
                        verify_btn.disabled = False
                        verify_status.value = result.get("error", "Código inválido o expirado")
                        verify_status.color = ft.Colors.RED_400
                        page.update()

                page.run_thread(do_verify)

            verify_btn.on_click = handle_verify

            def handle_resend(e):
                def do_resend():
                    reset_password(otp_email)
                page.run_thread(do_resend)
                verify_status.value = "Código reenviado"
                verify_status.color = ft.Colors.GREY_500
                page.update()

            _wrap([
                ft.Container(height=60),
                ft.Icon(ft.Icons.MARK_EMAIL_READ_ROUNDED, size=64, color=ft.Colors.BLUE_400),
                ft.Container(height=4),
                ft.Text("SKUs App", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                ft.Container(height=4),
                ft.Text(
                    "Verifica tu correo",
                    size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=8),
                ft.Text(
                    f"Ingresa el código de 6 dígitos\nque enviamos a {otp_email}",
                    size=13, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=20),
                token_field,
                ft.Container(height=6),
                verify_status,
                ft.Container(height=8),
                verify_btn,
                ft.Button(
                    content=ft.Text("¿No recibiste el código? Reenviar", color=ft.Colors.BLUE_400),
                    on_click=handle_resend,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.TRANSPARENT,
                        shadow_color=ft.Colors.TRANSPARENT,
                        overlay_color=ft.Colors.TRANSPARENT,
                    ),
                ),
                _back_btn(),
            ])
            return

        # ─── Estado NEW_PASSWORD: establecer nueva contraseña ─────────────────

        if mode == "new_password":
            new_pass_field = ft.TextField(
                label="Nueva contraseña",
                password=True,
                can_reveal_password=True,
                border_radius=10,
                width=300,
                on_change=lambda e: on_interaction(),
            )
            confirm_pass_field = ft.TextField(
                label="Confirmar contraseña",
                password=True,
                can_reveal_password=True,
                border_radius=10,
                width=300,
                on_change=lambda e: on_interaction(),
            )
            pass_status = ft.Text(value="", size=13, text_align=ft.TextAlign.CENTER, color=ft.Colors.RED_400)

            save_btn = ft.Button(
                content=ft.Text("Guardar contraseña", color=ft.Colors.WHITE),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    bgcolor=ft.Colors.BLUE_400,
                ),
                width=300,
            )

            def handle_save(e):
                new_pass = new_pass_field.value
                confirm = confirm_pass_field.value
                if len(new_pass) < 6:
                    pass_status.value = "La contraseña debe tener mínimo 6 caracteres"
                    pass_status.color = ft.Colors.RED_400
                    page.update()
                    return
                if new_pass != confirm:
                    pass_status.value = "Las contraseñas no coinciden"
                    pass_status.color = ft.Colors.RED_400
                    page.update()
                    return

                save_btn.content = ft.Row(
                    controls=[ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE)],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
                save_btn.disabled = True
                pass_status.value = ""
                page.update()

                def do_save():
                    result = update_password_after_reset(new_pass)
                    if result["success"]:
                        show_auth_view(mode="login")
                        page.show_dialog(
                            ft.SnackBar(
                                content=ft.Text("¡Contraseña actualizada correctamente!"),
                                open=True,
                            )
                        )
                    else:
                        save_btn.content = ft.Text("Guardar contraseña", color=ft.Colors.WHITE)
                        save_btn.disabled = False
                        pass_status.value = result.get("error", "Error inesperado")
                        pass_status.color = ft.Colors.RED_400
                        page.update()

                page.run_thread(do_save)

            save_btn.on_click = handle_save

            _wrap([
                ft.Container(height=60),
                ft.Icon(ft.Icons.LOCK_OPEN_ROUNDED, size=64, color=ft.Colors.BLUE_400),
                ft.Container(height=4),
                ft.Text("SKUs App", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                ft.Container(height=4),
                ft.Text(
                    "Crea tu nueva contraseña",
                    size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=20),
                new_pass_field,
                ft.Container(height=6),
                confirm_pass_field,
                ft.Container(height=6),
                pass_status,
                ft.Container(height=8),
                save_btn,
                _back_btn(),
            ])
            return

        # ─── Estado FORGOT: solicitar email ───────────────────────────────────

        if mode == "forgot":
            forgot_email = ft.TextField(
                label="Correo electrónico",
                keyboard_type=ft.KeyboardType.EMAIL,
                border_radius=10,
                width=300,
                on_change=lambda e: on_interaction(),
            )
            forgot_status = ft.Text(value="", size=13, text_align=ft.TextAlign.CENTER, color=ft.Colors.RED_400)

            send_btn = ft.Button(
                content=ft.Text("Enviar código", color=ft.Colors.WHITE),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    bgcolor=ft.Colors.BLUE_400,
                ),
                width=300,
            )

            def handle_send(e):
                email = forgot_email.value.strip()
                if not email:
                    forgot_status.value = "Ingresa tu correo electrónico"
                    forgot_status.color = ft.Colors.RED_400
                    page.update()
                    return
                if "@" not in email or "." not in email.split("@")[-1]:
                    forgot_status.value = "Ingresa un correo electrónico válido"
                    forgot_status.color = ft.Colors.RED_400
                    page.update()
                    return

                send_btn.content = ft.Row(
                    controls=[ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE)],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
                send_btn.disabled = True
                forgot_status.value = ""
                page.update()

                def do_reset():
                    result = reset_password(email)
                    if result["success"]:
                        show_auth_view(mode="verify_token", otp_email=email)
                    else:
                        send_btn.content = ft.Text("Enviar código", color=ft.Colors.WHITE)
                        send_btn.disabled = False
                        forgot_status.value = result.get("error", "Error inesperado")
                        forgot_status.color = ft.Colors.RED_400
                        page.update()

                page.run_thread(do_reset)

            send_btn.on_click = handle_send

            _wrap([
                ft.Container(height=60),
                ft.Icon(ft.Icons.LOCK_RESET_ROUNDED, size=64, color=ft.Colors.BLUE_400),
                ft.Container(height=4),
                ft.Text("SKUs App", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                ft.Container(height=4),
                ft.Text(
                    "Recuperar contraseña",
                    size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=8),
                ft.Text(
                    "Te enviaremos un código de 6 dígitos\na tu correo para recuperar tu cuenta",
                    size=13, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=20),
                forgot_email,
                ft.Container(height=6),
                forgot_status,
                ft.Container(height=8),
                send_btn,
                _back_btn(),
            ])
            return

        # ─── Estados LOGIN / REGISTER ─────────────────────────────────────────

        show_register = (mode == "register")

        email_field = ft.TextField(
            label="Correo electrónico",
            keyboard_type=ft.KeyboardType.EMAIL,
            border_radius=10,
            width=300,
            on_change=lambda e: on_interaction(),
        )
        password_field = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            border_radius=10,
            width=300,
            on_change=lambda e: on_interaction(),
        )
        username_field = ft.TextField(
            label="Nombre de usuario",
            border_radius=10,
            width=300,
            on_change=lambda e: on_interaction(),
            visible=show_register,
        )
        auth_status = ft.Text(value="", size=13, text_align=ft.TextAlign.CENTER, color=ft.Colors.RED_400)

        def handle_submit(e):
            if show_register:
                if not all([email_field.value, password_field.value, username_field.value]):
                    auth_status.value = "Completa todos los campos"
                    auth_status.color = ft.Colors.RED_400
                    page.update()
                    return
                if len(password_field.value) < 6:
                    auth_status.value = "La contraseña debe tener mínimo 6 caracteres"
                    auth_status.color = ft.Colors.RED_400
                    page.update()
                    return
                if len(username_field.value.strip()) < 3:
                    auth_status.value = "El nombre de usuario debe tener mínimo 3 caracteres"
                    auth_status.color = ft.Colors.RED_400
                    page.update()
                    return
            else:
                if not all([email_field.value, password_field.value]):
                    auth_status.value = "Completa todos los campos"
                    auth_status.color = ft.Colors.RED_400
                    page.update()
                    return

            auth_status.value = "Cargando..."
            auth_status.color = ft.Colors.GREY_500
            page.update()

            def do_auth():
                if show_register:
                    result = register(email_field.value, password_field.value, username_field.value)
                else:
                    result = login(email_field.value, password_field.value)

                if result["success"]:
                    post_auth_setup(
                        result["user_id"], result["email"],
                        result["nombre"], result["time_offset"],
                    )
                else:
                    auth_status.value = result.get("error", "Error desconocido")
                    auth_status.color = ft.Colors.RED_400
                    page.update()

            page.run_thread(do_auth)

        submit_btn = ft.Button(
            content=ft.Text(
                value="Crear cuenta" if show_register else "Ingresar",
                color=ft.Colors.WHITE,
            ),
            on_click=handle_submit,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                bgcolor=ft.Colors.BLUE_400,
            ),
            width=300,
        )

        toggle_btn = ft.Button(
            content=ft.Text(
                value="¿Ya tienes cuenta? Inicia sesión" if show_register else "¿No tienes cuenta? Regístrate",
                color=ft.Colors.BLUE_400,
            ),
            on_click=lambda e: show_auth_view(mode="register" if mode == "login" else "login"),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TRANSPARENT,
                shadow_color=ft.Colors.TRANSPARENT,
                overlay_color=ft.Colors.TRANSPARENT,
            ),
        )

        controls = [
            ft.Container(height=60),
            ft.Icon(ft.Icons.INVENTORY_2_ROUNDED, size=64, color=ft.Colors.BLUE_400),
            ft.Container(height=4),
            ft.Text("SKUs App", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
            ft.Container(height=4),
            ft.Text(
                "Crear cuenta" if show_register else "Iniciar sesión",
                size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=20),
            email_field,
            ft.Container(height=6),
        ]
        if show_register:
            controls += [username_field, ft.Container(height=6)]
        controls += [
            password_field,
            ft.Container(height=6),
            auth_status,
            ft.Container(height=8),
            submit_btn,
            toggle_btn,
        ]

        if mode == "login":
            controls.append(
                ft.Button(
                    content=ft.Text("Olvidé mi contraseña", color=ft.Colors.BLUE_400),
                    on_click=lambda e: show_auth_view(mode="forgot"),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.TRANSPARENT,
                        shadow_color=ft.Colors.TRANSPARENT,
                        overlay_color=ft.Colors.TRANSPARENT,
                    ),
                )
            )

        page.add(
            ft.Container(
                content=ft.Column(
                    controls=controls,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                ),
                expand=True,
                padding=ft.Padding.symmetric(horizontal=24),
            )
        )
        page.update()

    # ─── Vista principal con navegación ──────────────────────────────────────

    def show_main_view(selected_index: int = 0):
        page.controls.clear()
        content_area = ft.Container(expand=True)

        def navigate(index: int):
            if state.rol == "user":
                if index == 0:
                    from views.guia_estudio import guia_estudio_view
                    content_area.content = guia_estudio_view(
                        page=page,
                        time_offset=state.time_offset,
                        on_interaction=on_interaction,
                        primary_color=state.primary_color,
                        sede=state.sede,
                        sede_logo=LOGOS_SEDE.get(state.sede, "assets/images/Febeca.png"),
                        categorias=state.categorias_cache,
                        subcategorias=state.subcategorias_cache,
                        productos=state.productos_cache,
                        marcas_permitidas=state.marcas_permitidas,
                        user_id=state.user_id,
                        save_cache_callback=save_cache_callback,
                    )
                elif index == 1:
                    from views.panel_desafios import panel_desafios_view
                    content_area.content = panel_desafios_view(
                        page=page,
                        time_offset=state.time_offset,
                        on_interaction=on_interaction,
                        primary_color=state.primary_color,
                        categorias=state.categorias_cache,
                        subcategorias=state.subcategorias_cache,
                        productos=state.productos_cache,
                        user_id=state.user_id,
                        sede=state.sede,
                    )
                elif index == 2:
                    from views.profile import profile_view
                    content_area.content = profile_view(
                        page=page,
                        user_id=state.user_id,
                        user_email=state.user_email,
                        username=state.username,
                        time_offset=state.time_offset,
                        on_interaction=on_interaction,
                        on_logout=end_session,
                        primary_color=state.primary_color,
                        on_theme_change=on_theme_change,
                        rol=state.rol,
                        clock_text=clock_text,
                    )
            else:  # admin
                if index == 0:
                    from views.admin_usuarios import admin_usuarios_view
                    content_area.content = admin_usuarios_view(
                        page=page,
                        time_offset=state.time_offset,
                        on_interaction=on_interaction,
                        primary_color=state.primary_color,
                        notif_count=state.notif_count,
                        on_notif_cleared=lambda: _on_notif_cleared(nav_bar),
                    )
                elif index == 1:
                    from views.admin_reportes import admin_reportes_view
                    content_area.content = admin_reportes_view(
                        page=page,
                        time_offset=state.time_offset,
                        on_interaction=on_interaction,
                        primary_color=state.primary_color,
                    )
                elif index == 2:
                    from views.guia_global import guia_global_view
                    content_area.content = guia_global_view(
                        page=page,
                        time_offset=state.time_offset,
                        on_interaction=on_interaction,
                        primary_color=state.primary_color,
                    )
                elif index == 3:
                    from views.profile import profile_view
                    content_area.content = profile_view(
                        page=page,
                        user_id=state.user_id,
                        user_email=state.user_email,
                        username=state.username,
                        time_offset=state.time_offset,
                        on_interaction=on_interaction,
                        on_logout=end_session,
                        primary_color=state.primary_color,
                        on_theme_change=on_theme_change,
                        rol=state.rol,
                        clock_text=clock_text,
                    )
            page.update()

        def on_nav_change(e):
            on_interaction()
            navigate(e.control.selected_index)

        destinations = _admin_destinations() if state.rol == "admin" else _user_destinations()

        nav_bar = ft.NavigationBar(
            destinations=destinations,
            selected_index=selected_index,
            on_change=on_nav_change,
            indicator_color=state.primary_color,
        )

        page.add(
            ft.Column(
                controls=[content_area, nav_bar],
                expand=True,
                spacing=0,
            )
        )
        navigate(selected_index)

    def _on_notif_cleared(nav_bar):
        state.notif_count = 0
        nav_bar.destinations = _admin_destinations()
        page.update()

    def _user_destinations():
        return [
            ft.NavigationBarDestination(
                icon=ft.Icons.MENU_BOOK_OUTLINED,
                selected_icon=ft.Icons.MENU_BOOK_ROUNDED,
                label="Guía",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SPORTS_ESPORTS_OUTLINED,
                selected_icon=ft.Icons.SPORTS_ESPORTS_ROUNDED,
                label="Desafíos",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
                selected_icon=ft.Icons.PERSON_ROUNDED,
                label="Perfil",
            ),
        ]

    def _admin_destinations():
        if state.notif_count > 0:
            badge_label = str(state.notif_count) if state.notif_count < 100 else "99+"
            usuarios_icon = ft.Stack(
                controls=[
                    ft.Icon(ft.Icons.GROUP_OUTLINED),
                    ft.Container(
                        content=ft.Text(
                            badge_label, size=8, color=ft.Colors.WHITE,
                            text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD,
                        ),
                        bgcolor=ft.Colors.RED_400,
                        border_radius=8,
                        width=16,
                        height=16,
                        alignment=ft.Alignment(0, 0),
                        right=0,
                        top=0,
                    ),
                ],
                width=28,
                height=28,
            )
        else:
            usuarios_icon = ft.Icons.GROUP_OUTLINED

        return [
            ft.NavigationBarDestination(
                icon=usuarios_icon,
                selected_icon=ft.Icons.GROUP_ROUNDED,
                label="Usuarios",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.ASSIGNMENT_OUTLINED,
                selected_icon=ft.Icons.ASSIGNMENT_ROUNDED,
                label="Reportes",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.MENU_BOOK_OUTLINED,
                selected_icon=ft.Icons.MENU_BOOK_ROUNDED,
                label="Guía Global",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
                selected_icon=ft.Icons.PERSON_ROUNDED,
                label="Perfil",
            ),
        ]

    # ─── Arranque de la app ───────────────────────────────────────────────────

    def initialize():
        page.controls.clear()
        page.add(
            ft.Container(content=ft.ProgressRing(), alignment=ft.Alignment(0, 0), expand=True)
        )
        page.update()
        recover_incomplete_interval()

        def do_update_check():
            if state.update_checked:
                _finish_init()
                return
            state.update_checked = True

            update_info = check_for_updates(APP_VERSION)
            if not update_info["update_available"]:
                _finish_init()
                return

            target = update_info.get("target", "all")
            if target != "all" and target != state.rol:
                _finish_init()
                return

            latest = update_info["latest_version"]
            is_critical = update_info["is_critical"]
            apk_url = update_info["apk_url"] or ""
            changelog = update_info["changelog"]

            async def copy_link():
                await ft.Clipboard().set(apk_url)
                page.show_dialog(
                    ft.SnackBar(content=ft.Text("¡Enlace copiado! Pégalo en tu navegador."), open=True)
                )

            def on_copy(e):
                page.run_task(copy_link)

            changelog_items = [
                ft.Text(f"• {item}", size=13, color=ft.Colors.GREY_400)
                for item in changelog
            ] if changelog else []

            if is_critical:
                dlg = ft.AlertDialog(
                    modal=True,
                    bgcolor=ft.Colors.with_opacity(0.97, ft.Colors.GREY_800),
                    title=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(ft.Icons.SYSTEM_UPDATE_ROUNDED, color=ft.Colors.WHITE, size=20),
                                bgcolor=ft.Colors.BLUE_400, border_radius=10, padding=8,
                            ),
                            ft.Text("Actualización requerida", weight=ft.FontWeight.BOLD, size=16),
                        ],
                        spacing=10,
                    ),
                    content=ft.Column(
                        controls=[
                            ft.Divider(height=1, color=ft.Colors.with_opacity(0.15, ft.Colors.BLUE_400)),
                            ft.Container(height=4),
                            ft.Text(
                                f"Esta versión ({APP_VERSION}) ya no es compatible.\n"
                                f"Descarga la versión {latest} para continuar.",
                                size=13, color=ft.Colors.GREY_400,
                            ),
                        ] + changelog_items,
                        tight=True, spacing=4,
                    ),
                    actions=[
                        ft.Button(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.CONTENT_COPY_ROUNDED, size=15, color=ft.Colors.WHITE),
                                    ft.Text("Copiar enlace", color=ft.Colors.WHITE, size=13),
                                ],
                                spacing=6, tight=True,
                            ),
                            on_click=on_copy,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10),
                                bgcolor=ft.Colors.BLUE_400,
                            ),
                        ),
                    ],
                    actions_alignment=ft.MainAxisAlignment.CENTER,
                )
                page.overlay.append(dlg)
                dlg.open = True
                page.update()
            else:
                changelog_text = "  •  ".join(changelog) if changelog else ""

                def close_banner(e):
                    banner.open = False
                    page.update()

                banner = ft.Banner(
                    bgcolor=ft.Colors.with_opacity(0.97, ft.Colors.GREY_900),
                    leading=ft.Container(
                        content=ft.Icon(ft.Icons.SYSTEM_UPDATE_ROUNDED, color=ft.Colors.WHITE, size=20),
                        bgcolor=ft.Colors.BLUE_400, border_radius=8, padding=8,
                    ),
                    content=ft.Column(
                        controls=[
                            ft.Text(f"Nueva versión {latest} disponible", size=13, weight=ft.FontWeight.W_500),
                            ft.Text(changelog_text, size=12, color=ft.Colors.GREY_500, visible=bool(changelog_text)),
                        ],
                        spacing=2, tight=True,
                    ),
                    actions=[
                        ft.Button(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.CONTENT_COPY_ROUNDED, size=14, color=ft.Colors.BLUE_400),
                                    ft.Text("Copiar", color=ft.Colors.BLUE_400, size=13),
                                ],
                                spacing=4, tight=True,
                            ),
                            on_click=on_copy,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.TRANSPARENT,
                                shadow_color=ft.Colors.TRANSPARENT,
                                overlay_color=ft.Colors.TRANSPARENT,
                            ),
                        ),
                        ft.Button(
                            content=ft.Text("Ignorar", color=ft.Colors.GREY_500, size=13),
                            on_click=close_banner,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.TRANSPARENT,
                                shadow_color=ft.Colors.TRANSPARENT,
                                overlay_color=ft.Colors.TRANSPARENT,
                            ),
                        ),
                    ],
                )
                banner.open = True
                _finish_init()
                page.show_dialog(banner)

        def _finish_init():
            result = restore_session()
            if result["success"]:
                post_auth_setup(
                    result["user_id"], result["email"],
                    result["nombre"], result["time_offset"],
                )
            else:
                show_auth_view()

        page.run_thread(do_update_check)

    initialize()


ft.run(main)
