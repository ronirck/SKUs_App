from config import SUPABASE_URL, SUPABASE_ANON_KEY
from supabase import create_client, Client
from session_manager import (
    save_auth_tokens,
    load_auth_tokens,
    clear_auth_tokens,
    clear_local_session_data,
    fetch_server_time_offset,
    has_pending_data,
    get_pending_data,
)

_supabase_client: Client = None


def _classify_error(e: Exception) -> str:
    error_str = str(e).lower()
    if any(x in error_str for x in [
        "timeout", "timed out", "handshake",
        "connection", "network", "unreachable",
        "name resolution", "socket", "ssl", "errno",
    ]):
        return "Sin conexión a internet. Verifica tu red e intenta de nuevo."
    if any(x in error_str for x in [
        "otp", "token", "expired", "invalid otp",
        "token has expired", "otp expired",
    ]):
        return "Código inválido o expirado. Solicita uno nuevo."
    if any(x in error_str for x in ["invalid", "credentials", "wrong password", "invalid login"]):
        return "Correo o contraseña incorrectos."
    if any(x in error_str for x in ["already", "exists", "registered", "already registered"]):
        return "Este correo ya está registrado."
    if any(x in error_str for x in ["weak password", "should be at least"]):
        return "La contraseña debe tener mínimo 6 caracteres."
    return "Error inesperado. Intenta de nuevo."


def get_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _supabase_client


# ─── Helpers internos ─────────────────────────────────────────────────────────

def _sync_pending_data(client: Client, user_id: str):
    if not has_pending_data():
        return
    pending_seconds, pending_date = get_pending_data()
    if pending_seconds <= 0 or pending_date is None:
        return
    try:
        existing = (
            client.table("session_logs")
            .select("id, duration_seconds")
            .eq("user_id", user_id)
            .eq("date", pending_date)
            .execute()
        )
        if existing.data:
            record = existing.data[0]
            client.table("session_logs").update(
                {"duration_seconds": record["duration_seconds"] + pending_seconds,
                 "updated_at": "now()"}
            ).eq("id", record["id"]).execute()
        else:
            client.table("session_logs").insert(
                {"user_id": user_id, "date": pending_date,
                 "duration_seconds": pending_seconds}
            ).execute()
        clear_local_session_data()
    except Exception:
        pass


def _read_user_data(client: Client, user_id: str, fallback_nombre: str = "") -> dict:
    """Lee perfil_usuario y usuario_config y retorna un dict unificado."""
    perfil = {}
    config = {}
    try:
        res = (
            client.table("perfil_usuario")
            .select("*")
            .eq("usuario_id", user_id)
            .execute()
        )
        if res.data:
            perfil = res.data[0]
    except Exception:
        pass
    try:
        res = (
            client.table("usuario_config")
            .select("*")
            .eq("usuario_id", user_id)
            .execute()
        )
        if res.data:
            config = res.data[0]
    except Exception:
        pass
    return {
        "nombre": perfil.get("nombre") or fallback_nombre,
        "rol": perfil.get("rol", "user"),
        "sede": config.get("sede", "FEBECA"),
        "marcas_permitidas": config.get("marcas_permitidas") or [],
        "solo_infaltables": config.get("solo_infaltables", False),
        "config_version": config.get("config_version", 1),
    }


# ─── Auth pública ─────────────────────────────────────────────────────────────

def login(email: str, password: str) -> dict:
    try:
        client = get_client()
        response = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        if response.user is None:
            return {"success": False, "error": "Credenciales incorrectas"}

        user_id = str(response.user.id)
        save_auth_tokens(
            response.session.access_token,
            response.session.refresh_token,
        )
        _sync_pending_data(client, user_id)

        user_data = _read_user_data(
            client, user_id,
            fallback_nombre=response.user.email.split("@")[0],
        )
        time_offset = fetch_server_time_offset()

        return {
            "success": True,
            "user_id": user_id,
            "email": response.user.email,
            **user_data,
            "time_offset": time_offset,
        }

    except Exception as e:
        return {"success": False, "error": _classify_error(e)}


def register(email: str, password: str, nombre: str) -> dict:
    """
    Registra en Supabase Auth. El trigger handle_new_user crea perfil_usuario
    y usuario_config automáticamente; aquí solo se actualiza el nombre.
    """
    try:
        client = get_client()
        response = client.auth.sign_up({"email": email, "password": password})

        if response.user is None:
            return {"success": False, "error": "No se pudo crear la cuenta"}

        user_id = str(response.user.id)
        save_auth_tokens(
            response.session.access_token,
            response.session.refresh_token,
        )

        nombre_limpio = nombre.strip()
        try:
            client.table("perfil_usuario").update(
                {"nombre": nombre_limpio, "email": email}
            ).eq("usuario_id", user_id).execute()
        except Exception:
            pass

        user_data = _read_user_data(client, user_id, fallback_nombre=nombre_limpio)
        time_offset = fetch_server_time_offset()

        return {
            "success": True,
            "user_id": user_id,
            "email": email,
            "nombre": nombre_limpio,
            "rol": user_data["rol"],
            "sede": user_data["sede"],
            "marcas_permitidas": user_data["marcas_permitidas"],
            "solo_infaltables": user_data["solo_infaltables"],
            "config_version": user_data["config_version"],
            "time_offset": time_offset,
        }

    except Exception as e:
        return {"success": False, "error": _classify_error(e)}


def restore_session() -> dict:
    try:
        access_token, refresh_token = load_auth_tokens()

        if access_token is None or refresh_token is None:
            return {"success": False}

        client = get_client()
        response = client.auth.set_session(access_token, refresh_token)

        if response.user is None:
            clear_auth_tokens()
            return {"success": False}

        user_id = str(response.user.id)
        save_auth_tokens(
            response.session.access_token,
            response.session.refresh_token,
        )
        _sync_pending_data(client, user_id)

        user_data = _read_user_data(
            client, user_id,
            fallback_nombre=response.user.email.split("@")[0],
        )
        time_offset = fetch_server_time_offset()

        return {
            "success": True,
            "user_id": user_id,
            "email": response.user.email,
            **user_data,
            "time_offset": time_offset,
        }

    except Exception as e:
        clear_auth_tokens()
        return {"success": False, "error": _classify_error(e)}


def logout(user_id: str, time_offset: float):
    try:
        client = get_client()
        _sync_pending_data(client, user_id)
        client.auth.sign_out()
    except Exception:
        pass
    finally:
        clear_auth_tokens()
        clear_local_session_data()
        from session_manager import clear_all_cache
        clear_all_cache()


# ─── Consultas de perfil/config ───────────────────────────────────────────────

def get_remote_config_version(user_id: str) -> int:
    """Consulta liviana para comparar versión antes de recargar caché."""
    try:
        client = get_client()
        res = (
            client.table("usuario_config")
            .select("config_version")
            .eq("usuario_id", user_id)
            .execute()
        )
        return res.data[0]["config_version"] if res.data else 1
    except Exception:
        return 1


def update_usuario_config(
    user_id: str,
    sede: str,
    marcas_permitidas: list,
    solo_infaltables: bool,
) -> dict:
    """Solo accesible por admin. Actualiza config e incrementa config_version."""
    try:
        client = get_client()
        current = (
            client.table("usuario_config")
            .select("config_version")
            .eq("usuario_id", user_id)
            .execute()
        )
        current_ver = current.data[0]["config_version"] if current.data else 1
        new_ver = current_ver + 1

        client.table("usuario_config").update({
            "sede": sede,
            "marcas_permitidas": marcas_permitidas,
            "solo_infaltables": solo_infaltables,
            "config_version": new_ver,
        }).eq("usuario_id", user_id).execute()

        return {"success": True, "config_version": new_ver}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_all_usuarios() -> list:
    """Solo accesible por admin. Retorna todos los usuarios con perfil y config."""
    try:
        client = get_client()
        perfiles = (
            client.table("perfil_usuario")
            .select("*")
            .order("creado_en", desc=True)
            .execute()
        )
        configs = client.table("usuario_config").select("*").execute()
        cfg_map = {c["usuario_id"]: c for c in (configs.data or [])}

        result = []
        for p in (perfiles.data or []):
            cfg = cfg_map.get(p["usuario_id"], {})
            result.append({**p, **cfg})
        return result
    except Exception:
        return []


# ─── Edición del perfil ───────────────────────────────────────────────────────

def change_password(new_password: str) -> dict:
    try:
        client = get_client()
        client.auth.update_user({"password": new_password})
        return {"success": True}
    except Exception:
        return {"success": False, "error": "No se pudo cambiar la contraseña"}


def change_username(user_id: str, new_nombre: str) -> dict:
    """Actualiza perfil_usuario.nombre (llamado 'username' en profile.py)."""
    try:
        client = get_client()
        client.table("perfil_usuario").update(
            {"nombre": new_nombre.strip()}
        ).eq("usuario_id", user_id).execute()
        return {"success": True}
    except Exception:
        return {"success": False, "error": "No se pudo actualizar el nombre"}


def reset_password(email: str) -> dict:
    try:
        client = get_client()
        client.auth.reset_password_for_email(email)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": _classify_error(e)}


def verify_otp_token(email: str, token: str) -> dict:
    try:
        client = get_client()
        response = client.auth.verify_otp(
            {"email": email, "token": token, "type": "recovery"}
        )
        if response.user:
            save_auth_tokens(
                response.session.access_token,
                response.session.refresh_token,
            )
            return {"success": True}
        print(f"[otp] Respuesta sin user: {response}")
        return {"success": False, "error": "Código inválido o expirado."}
    except Exception as e:
        print(f"[otp] EXCEPCION: {type(e).__name__}: {e}")
        print(f"[otp] Detalle: {repr(e)}")
        return {"success": False, "error": _classify_error(e)}


def update_password_after_reset(new_password: str) -> dict:
    try:
        client = get_client()
        client.auth.update_user({"password": new_password})
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": _classify_error(e)}
