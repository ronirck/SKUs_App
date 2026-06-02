import json
import os
from datetime import datetime, timezone
from pathlib import Path


def _get_data_dir() -> Path:
    flet_storage = os.environ.get("FLET_APP_STORAGE_DATA")
    if flet_storage:
        base = Path(flet_storage)
    else:
        base = Path(__file__).parent / "storage" / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_storage_path() -> Path:
    return _get_data_dir() / "session_data.json"


STORAGE_FILE = get_storage_path()
STORAGE_DIR = STORAGE_FILE.parent


def _get_corrected_time(time_offset: float) -> datetime:
    local_time = datetime.now(timezone.utc)
    corrected = local_time.timestamp() + time_offset
    return datetime.fromtimestamp(corrected, tz=timezone.utc)


def fetch_server_time_offset() -> float:
    try:
        server_time = datetime.now(timezone.utc)
        local_time = datetime.now(timezone.utc)
        offset = server_time.timestamp() - local_time.timestamp()
        return offset
    except Exception:
        return 0.0


def load_local_data() -> dict:
    if STORAGE_FILE.exists():
        try:
            with open(STORAGE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_local_data(data: dict):
    try:
        with open(STORAGE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def recover_incomplete_interval() -> int:
    data = load_local_data()
    interval_start = data.get("interval_start")
    last_interaction = data.get("last_interaction")

    if interval_start is None or last_interaction is None:
        return 0

    elapsed = int(last_interaction - interval_start)
    elapsed = max(0, elapsed)

    if elapsed > 0:
        current_pending = data.get("pending_seconds", 0)
        current_date = data.get("pending_date")

        if current_date is None:
            current_date = datetime.fromtimestamp(
                last_interaction, tz=timezone.utc
            ).date().isoformat()

        data["pending_seconds"] = current_pending + elapsed
        data["pending_date"] = current_date

    data.pop("interval_start", None)
    data.pop("last_interaction", None)
    save_local_data(data)

    return elapsed


def clear_local_session_data():
    data = load_local_data()
    data.pop("pending_seconds", None)
    data.pop("pending_date", None)
    data.pop("interval_start", None)
    data.pop("last_interaction", None)
    save_local_data(data)


def start_interval(time_offset: float):
    now = _get_corrected_time(time_offset).timestamp()
    data = load_local_data()
    data["interval_start"] = now
    data["last_interaction"] = now
    save_local_data(data)


def register_interaction(time_offset: float):
    now = _get_corrected_time(time_offset).timestamp()
    data = load_local_data()
    last = data.get("last_interaction")

    if last is not None:
        inactive_seconds = now - last
        if inactive_seconds >= 60:
            close_interval(time_offset)
            data = load_local_data()
            data["interval_start"] = now

    data["last_interaction"] = now
    save_local_data(data)


def close_interval(time_offset: float) -> int:
    now = _get_corrected_time(time_offset).timestamp()
    data = load_local_data()
    interval_start = data.get("interval_start")

    elapsed = 0
    if interval_start is not None:
        elapsed = int(now - interval_start)
        elapsed = max(0, elapsed)

    current_pending = data.get("pending_seconds", 0)
    current_date = data.get("pending_date")
    today = _get_corrected_time(time_offset).date().isoformat()

    if current_date is None:
        current_date = today

    data["pending_seconds"] = current_pending + elapsed
    data["pending_date"] = current_date
    data.pop("interval_start", None)
    data.pop("last_interaction", None)
    save_local_data(data)

    return elapsed


def check_midnight_crossing(time_offset: float) -> bool:
    data = load_local_data()
    pending_date = data.get("pending_date")
    today = _get_corrected_time(time_offset).date().isoformat()

    if pending_date is not None and pending_date != today:
        return True
    return False


def has_pending_data() -> bool:
    data = load_local_data()
    pending = data.get("pending_seconds", 0)
    pending_date = data.get("pending_date")
    return pending > 0 and pending_date is not None


def get_pending_data() -> tuple:
    data = load_local_data()
    return data.get("pending_seconds", 0), data.get("pending_date")


def save_auth_tokens(access_token: str, refresh_token: str):
    data = load_local_data()
    data["access_token"] = access_token
    data["refresh_token"] = refresh_token
    save_local_data(data)


def load_auth_tokens() -> tuple:
    data = load_local_data()
    return data.get("access_token"), data.get("refresh_token")


def clear_auth_tokens():
    data = load_local_data()
    data.pop("access_token", None)
    data.pop("refresh_token", None)
    save_local_data(data)

def save_theme_preferences(color_name: str, is_dark: bool):
    data = load_local_data()
    data["color_name"] = color_name
    data["is_dark"] = is_dark
    save_local_data(data)


def load_theme_preferences() -> tuple:
    data = load_local_data()
    color_name = data.get("color_name", "Azul")
    is_dark = data.get("is_dark", False)
    return color_name, is_dark


# ─── Paginación Supabase ─────────────────────────────────────────────────────

def fetch_all(client, table: str, query_fn=None) -> list:
    """Descarga todas las filas de una tabla sorteando el límite de 1000 de Supabase."""
    PAGE_SIZE = 1000
    all_data = []
    offset = 0
    while True:
        q = client.table(table)
        if query_fn:
            q = query_fn(q)
        result = q.range(offset, offset + PAGE_SIZE - 1).execute()
        if not result.data:
            break
        all_data.extend(result.data)
        if len(result.data) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return all_data


# ─── Caché de productos ───────────────────────────────────────────────────────

def _get_productos_cache_path() -> Path:
    return _get_data_dir() / "productos_cache.json"


def save_productos_cache(data: dict) -> None:
    try:
        path = _get_productos_cache_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"[cache] productos_cache.json guardado en {path} (version={data.get('config_version')})")
    except Exception as e:
        print(f"[cache] Error guardando productos_cache: {e}")


def load_productos_cache() -> dict | None:
    try:
        path = _get_productos_cache_path()
        if not path.exists():
            print(f"[cache] productos_cache.json no existe en {path}")
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[cache] productos_cache.json cargado (version={data.get('config_version')}, sede={data.get('sede')}, productos={len(data.get('productos', []))})")
        return data
    except Exception as e:
        print(f"[cache] Error leyendo productos_cache: {e}")
        return None


def clear_productos_cache() -> None:
    try:
        path = _get_productos_cache_path()
        if path.exists():
            path.unlink()
        print("[cache] productos_cache.json eliminado")
    except Exception as e:
        print(f"[cache] Error eliminando productos_cache: {e}")


# ─── Caché admin por sede ─────────────────────────────────────────────────────

def get_admin_cache_path(sede: str) -> Path:
    sede_slug = sede.lower().replace(" ", "_").replace("de_", "")
    return STORAGE_DIR / f"cache_admin_{sede_slug}.json"


def save_admin_cache(sede: str, data: dict) -> None:
    path = get_admin_cache_path(sede)
    payload = {
        "sede": sede,
        "categorias": data["categorias"],
        "subcategorias": data["subcategorias"],
        "productos": data["productos"],
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        print(f"[cache_admin] {sede} guardado ({len(data['productos'])} productos)")
    except Exception as e:
        print(f"[cache_admin] Error guardando {sede}: {e}")


def load_admin_cache(sede: str) -> dict | None:
    path = get_admin_cache_path(sede)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[cache_admin] {sede} cargado ({len(data.get('productos', []))} productos)")
        return data
    except Exception as e:
        print(f"[cache_admin] Error leyendo {sede}: {e}")
        return None


def clear_all_cache() -> None:
    archivos = [
        STORAGE_DIR / "productos_cache.json",
        STORAGE_DIR / "session_data.json",
        STORAGE_DIR / "app_preferences.json",
    ]
    for path in archivos:
        try:
            if path.exists():
                path.unlink()
                print(f"[cache] Borrado: {path.name}")
        except Exception as e:
            print(f"[cache] Error borrando {path.name}: {e}")

    try:
        for path in STORAGE_DIR.glob("cache_admin_*.json"):
            path.unlink()
            print(f"[cache] Borrado: {path.name}")
    except Exception as e:
        print(f"[cache] Error borrando caches admin: {e}")