"""
database.py — Cliente Supabase y todas las queries.
Cliente lazy: se crea la primera vez que se necesita, no al importar.
Esto evita bloquear el hilo principal de Flet al arrancar.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from supabase import Client, create_client

from config import SUPABASE_URL, SUPABASE_KEY

_client: Optional[Client] = None

# ── Cachés en memoria ─────────────────────────────────────────────────────────
_cache_categorias:    Optional[dict] = None
_cache_subcategorias: Optional[dict] = None
_cache_productos:     Optional[list] = None
_cache_quiz_data:     Optional[dict] = None

# ── Cache en disco ────────────────────────────────────────────────────────────
_PRODUCTOS_CACHE_FILE = Path(__file__).parent / "cache_productos.json"
_CACHE_TTL_MINUTOS    = 30   # Máximo tiempo (min) cerrada la app para reusar cache


def get_client() -> Client:
    """Singleton lazy — se instancia solo la primera vez que se llama."""
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# ── Cache en disco: productos ─────────────────────────────────────────────────

def _guardar_cache_disco(productos: list[dict]) -> None:
    """Persiste la lista de productos en disco. cerrado_en = None (app abierta)."""
    try:
        data = {
            "cerrado_en": None,
            "productos":  productos,
        }
        _PRODUCTOS_CACHE_FILE.write_text(
            json.dumps(data, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except Exception:
        pass


def marcar_cierre_cache() -> None:
    """Registra el timestamp de cierre para calcular TTL en la próxima apertura."""
    try:
        if not _PRODUCTOS_CACHE_FILE.exists():
            return
        data = json.loads(_PRODUCTOS_CACHE_FILE.read_text(encoding="utf-8"))
        data["cerrado_en"] = datetime.now(timezone.utc).isoformat()
        _PRODUCTOS_CACHE_FILE.write_text(
            json.dumps(data, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except Exception:
        pass


def _leer_cache_disco() -> Optional[list[dict]]:
    """
    Lee el cache de disco si sigue siendo válido.
    - Sin cerrado_en  → la app se cerró abruptamente; se reutiliza igual.
    - Con cerrado_en  → válido solo si lleva menos de _CACHE_TTL_MINUTOS cerrada.
    - Si los productos no tienen el campo 'sede' → cache desactualizado, se descarta.
    Retorna None si expiró, no existe, está corrupto o es de esquema viejo.
    """
    try:
        if not _PRODUCTOS_CACHE_FILE.exists():
            return None
        data = json.loads(_PRODUCTOS_CACHE_FILE.read_text(encoding="utf-8"))
        productos = data.get("productos")
        if not productos:
            return None
        # Validar que el cache incluya el campo 'sede' (agregado en versión reciente).
        # Si no lo tiene, es un cache de esquema anterior → forzar re-fetch.
        if "sede" not in productos[0]:
            _PRODUCTOS_CACHE_FILE.unlink(missing_ok=True)
            return None
        cerrado_str = data.get("cerrado_en")
        if cerrado_str:
            cerrado = datetime.fromisoformat(cerrado_str.replace("Z", "+00:00"))
            minutos = (datetime.now(timezone.utc) - cerrado).total_seconds() / 60
            if minutos > _CACHE_TTL_MINUTOS:
                return None   # Expirado
        return productos
    except Exception:
        return None


def invalidar_cache_productos() -> None:
    """Elimina el cache de disco (al cerrar sesión)."""
    try:
        if _PRODUCTOS_CACHE_FILE.exists():
            _PRODUCTOS_CACHE_FILE.unlink()
    except Exception:
        pass


# ── Auth ──────────────────────────────────────────────────────────────────────

def fetch_usuario_por_email(email: str) -> Optional[dict]:
    """Busca usuario por email combinando usuarios + usuarios_auth."""
    user_result = (
        get_client().table("usuarios")
        .select("id, nombre, email, rol, creado_en")
        .eq("email", email.strip().lower())
        .limit(1)
        .execute()
    )
    if not user_result.data:
        return None

    usuario = user_result.data[0]

    auth_result = (
        get_client().table("usuarios_auth")
        .select("password_hash, status, ultimo_acceso")
        .eq("usuario_id", usuario["id"])
        .eq("status", True)
        .limit(1)
        .execute()
    )
    if not auth_result.data:
        return None  # Usuario sin auth activa = inactivo

    usuario.update(auth_result.data[0])
    return usuario


def insertar_usuario(nombre: str, email: str, password_hash: str) -> dict:
    """Crea el usuario en 'usuarios' y su registro en 'usuarios_auth'."""
    user_result = (
        get_client().table("usuarios")
        .insert({
            "nombre": nombre.strip(),
            "email":  email.strip().lower(),
        })
        .execute()
    )
    if not user_result.data:
        raise RuntimeError("El servidor no retornó datos al crear el usuario.")

    usuario = user_result.data[0]

    get_client().table("usuarios_auth").insert({
        "usuario_id":    usuario["id"],
        "password_hash": password_hash,
    }).execute()

    return usuario


def actualizar_ultimo_acceso(usuario_id: str) -> None:
    get_client().table("usuarios_auth").update(
        {"ultimo_acceso": datetime.now(timezone.utc).isoformat()}
    ).eq("usuario_id", usuario_id).execute()


# ── Catálogo ──────────────────────────────────────────────────────────────────

def fetch_categorias() -> dict[str, str]:
    global _cache_categorias
    if _cache_categorias is not None:
        return _cache_categorias
    rows = get_client().table("categorias").select("codigo, nombre, mnemotecnia").execute().data
    _cache_categorias = {
        r["codigo"].strip(): {"nombre": r["nombre"], "mnemotecnia": r.get("mnemotecnia")}
        for r in rows
    }
    return _cache_categorias


def fetch_subcategorias() -> dict[tuple[str, str], str]:
    global _cache_subcategorias
    if _cache_subcategorias is not None:
        return _cache_subcategorias
    rows = (
        get_client().table("subcategorias")
        .select("categoria_codigo, codigo, nombre, mnemotecnia")
        .execute().data
    )
    _cache_subcategorias = {
        (r["categoria_codigo"].strip(), r["codigo"].strip()): {
            "nombre": r["nombre"], "mnemotecnia": r.get("mnemotecnia")
        }
        for r in rows
    }
    return _cache_subcategorias


def fetch_productos() -> list[dict]:
    """
    Retorna todos los productos.
    Orden de prioridad:
      1. Cache en memoria  (_cache_productos)
      2. Cache en disco    (cache_productos.json, si no expiró)
      3. Supabase          (6500+ registros en chunks)
    """
    global _cache_productos
    if _cache_productos is not None:
        return _cache_productos

    # ── Intentar cache en disco ───────────────────────────────────────────────
    cached = _leer_cache_disco()
    if cached:
        _cache_productos = cached
        return cached

    # ── Fetch desde Supabase ──────────────────────────────────────────────────
    cats = fetch_categorias()
    subs = fetch_subcategorias()

    all_rows: list[dict] = []
    chunk_size = 1000
    offset = 0

    while True:
        rows = (
            get_client().table("productos")
            .select(
                "categoria_codigo, subcategoria_codigo, codigo, "
                "nombre, mnemotecnia, codigo_completo, imagen_url, sede"
            )
            .range(offset, offset + chunk_size - 1)
            .execute().data
        )
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < chunk_size:
            break
        offset += chunk_size

    for p in all_rows:
        ck = p.get("categoria_codigo", "").strip() or ""
        sk = p.get("subcategoria_codigo", "").strip() or ""
        pk = p.get("codigo", "").strip() or ""

        p["categoria_codigo"]    = ck
        p["subcategoria_codigo"] = sk
        p["codigo"]              = pk

        if p.get("codigo_completo"):
            p["codigo_completo"] = p["codigo_completo"].strip()
        if p.get("sede"):
            p["sede"] = p["sede"].strip().upper()

        cat_data = cats.get(ck, {"nombre": ck})
        sub_data = subs.get((ck, sk), {"nombre": sk})

        p["categoria_nombre"]    = cat_data["nombre"]
        p["subcategoria_nombre"] = sub_data["nombre"]

    # Guardar en disco para la próxima sesión
    _guardar_cache_disco(all_rows)

    _cache_productos = all_rows
    return all_rows


# ── Quiz ──────────────────────────────────────────────────────────────────────

def fetch_todos_para_quiz() -> dict:
    """
    Retorna todo lo necesario para generar preguntas del Quiz de Opciones:
    categorias, subcategorias y productos con sus nombres.
    """
    global _cache_quiz_data
    if _cache_quiz_data is not None:
        return _cache_quiz_data

    cats_raw  = fetch_categorias()
    subs_raw  = fetch_subcategorias()
    prods_raw = fetch_productos()

    _cache_quiz_data = {
        "categorias":    [{"codigo": k, "nombre": v["nombre"], "mnemotecnia": v["mnemotecnia"]} for k, v in cats_raw.items()],
        "subcategorias": [{"categoria_codigo": k[0], "codigo": k[1], "nombre": v["nombre"], "mnemotecnia": v["mnemotecnia"]} for k, v in subs_raw.items()],
        "productos":     prods_raw,
    }
    return _cache_quiz_data


# ── Sesiones de Uso ───────────────────────────────────────────────────────────

def obtener_sesion_hoy(usuario_id: str) -> Optional[dict]:
    """
    Busca la sesion_uso más reciente de HOY para el usuario.
    Retorna {"id": ..., "duracion_seg": ...} o None si no existe.
    """
    try:
        from datetime import date
        hoy = date.today().isoformat()          # "2026-04-01"
        result = (
            get_client().table("sesiones_uso")
            .select("id, duracion_seg")
            .eq("usuario_id", usuario_id)
            .gte("inicio_en", f"{hoy}T00:00:00+00:00")
            .lte("inicio_en", f"{hoy}T23:59:59.999999+00:00")
            .order("inicio_en", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception:
        return None


def iniciar_sesion_uso(usuario_id: str) -> Optional[str]:
    """Crea un nuevo registro en sesiones_uso y retorna el ID."""
    try:
        result = (
            get_client().table("sesiones_uso")
            .insert({"usuario_id": usuario_id})
            .execute()
        )
        return result.data[0]["id"] if result.data else None
    except Exception:
        return None


def acumular_tiempo_sesion(sesion_id: str, segundos: int) -> None:
    """
    Suma `segundos` al duracion_seg existente del registro y actualiza fin_en.
    Usa READ + WRITE porque Supabase no soporta UPDATE col = col + N via postgrest fácilmente.
    """
    if segundos <= 0:
        return
    try:
        row = (
            get_client().table("sesiones_uso")
            .select("duracion_seg")
            .eq("id", sesion_id)
            .limit(1)
            .execute()
        )
        actual = (row.data[0].get("duracion_seg") or 0) if row.data else 0
        get_client().table("sesiones_uso").update({
            "duracion_seg": actual + segundos,
            "fin_en":       datetime.now(timezone.utc).isoformat(),
        }).eq("id", sesion_id).execute()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# FIN DEL MÓDULO
# ══════════════════════════════════════════════════════════════════════════════
