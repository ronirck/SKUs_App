"""
database.py — Cliente Supabase y todas las queries.
Cliente lazy: se crea la primera vez que se necesita, no al importar.
Esto evita bloquear el hilo principal de Flet al arrancar.
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from supabase import Client, create_client

from config import SUPABASE_URL, SUPABASE_KEY

_client: Optional[Client] = None

# ── Cachés en memoria ─────────────────────────────────────────────────────────
_cache_categorias:    Optional[dict] = None   # clave: (sede, codigo)
_cache_subcategorias: Optional[dict] = None   # clave: (sede, cat_codigo, codigo)
_cache_productos:     Optional[list] = None

# ── Cache en disco ────────────────────────────────────────────────────────────
_PRODUCTOS_CACHE_FILE = Path(__file__).parent / "cache_productos.json"
_CACHE_TTL_MINUTOS    = 14   # Máximo tiempo (min) cerrada la app para reusar cache

# Archivo de estado del updater (escrito por updater.py)
_UPDATE_STATE_FILE = Path(__file__).parent / "update_state.json"


def _leer_data_version_remota() -> Optional[str]:
    """
    Lee la última data_version conocida guardada por updater.py.
    Retorna None si el archivo no existe o no tiene ese campo.
    """
    try:
        if _UPDATE_STATE_FILE.exists():
            data = json.loads(_UPDATE_STATE_FILE.read_text(encoding="utf-8"))
            v = data.get("data_version")
            return str(v) if v is not None else None
    except Exception:
        pass
    return None

# ── Control de invalidación y concurrencia ─────────────────────────────────────
# _invalidation_count se incrementa cada vez que se invalida la cache.
# fetch_productos captura el valor antes del fetch y solo guarda en disco
# si el valor no cambió (evita reescribir después de un logout).
_invalidation_count: int = 0
_fetch_lock = threading.Lock()   # evita dos fetches simultáneos desde Supabase


def get_client() -> Client:
    """Singleton lazy — se instancia solo la primera vez que se llama."""
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# ── Cache en disco: productos ─────────────────────────────────────────────────

def _guardar_cache_disco(productos: list[dict], token_invalidacion: int) -> None:
    """
    Persiste la lista de productos en disco solo si la cache no fue invalidada
    mientras se hacía el fetch (evita reescribir tras un logout).
    Guarda también la data_version vigente para detectar cambios al releer.
    """
    if token_invalidacion != _invalidation_count:
        return   # Cache fue invalidada mientras se fetcheaba → no guardar
    try:
        data = {
            "cerrado_en":   None,
            "data_version": _leer_data_version_remota(),  # versión vigente al guardar
            "productos":    productos,
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
    Condiciones de invalidación:
    - No existe o está corrupto.
    - Los productos no tienen el campo 'sede' (esquema viejo).
    - TTL expirado (>= _CACHE_TTL_MINUTOS desde que se cerró la app).
    - data_version del cache difiere de la guardada por updater.py
      (los datos en Supabase cambiaron mientras la app estaba cerrada).
    Retorna None en cualquiera de esos casos.
    """
    try:
        if not _PRODUCTOS_CACHE_FILE.exists():
            return None
        data = json.loads(_PRODUCTOS_CACHE_FILE.read_text(encoding="utf-8"))
        productos = data.get("productos")
        if not productos:
            return None

        # Validar esquema: el campo 'sede' debe existir
        if "sede" not in productos[0]:
            _PRODUCTOS_CACHE_FILE.unlink(missing_ok=True)
            return None

        # Verificar TTL
        cerrado_str = data.get("cerrado_en")
        if cerrado_str:
            cerrado = datetime.fromisoformat(cerrado_str.replace("Z", "+00:00"))
            minutos = (datetime.now(timezone.utc) - cerrado).total_seconds() / 60
            if minutos > _CACHE_TTL_MINUTOS:
                return None   # Expirado por tiempo

        # Verificar data_version: si el updater ya conoce una versión más nueva,
        # el cache en disco está desactualizado aunque el TTL no haya expirado.
        version_remota = _leer_data_version_remota()
        version_cache  = data.get("data_version")
        if version_remota and version_cache and version_remota != str(version_cache):
            _PRODUCTOS_CACHE_FILE.unlink(missing_ok=True)
            return None   # Datos desactualizados

        return productos
    except Exception:
        return None


def invalidar_cache_productos() -> None:
    """
    Invalida la cache de productos: limpia memoria, borra disco e incrementa
    el contador de invalidación para que cualquier fetch en curso no guarde.
    """
    global _cache_productos, _invalidation_count
    _invalidation_count += 1
    _cache_productos = None
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

def fetch_categorias() -> dict:
    """
    Retorna todas las categorías de todas las sedes.
    Clave: (sede_upper, codigo) → {"nombre": ..., "mnemotecnia": ...}
    """
    global _cache_categorias
    if _cache_categorias is not None:
        return _cache_categorias
    rows = get_client().table("categorias").select("sede, codigo, nombre, mnemotecnia").execute().data
    _cache_categorias = {
        (r["sede"].strip().upper(), r["codigo"].strip()): {
            "nombre": r["nombre"], "mnemotecnia": r.get("mnemotecnia")
        }
        for r in rows
    }
    return _cache_categorias


def fetch_subcategorias() -> dict:
    """
    Retorna todas las subcategorías de todas las sedes.
    Clave: (sede_upper, cat_codigo, codigo) → {"nombre": ..., "mnemotecnia": ...}
    """
    global _cache_subcategorias
    if _cache_subcategorias is not None:
        return _cache_subcategorias
    rows = (
        get_client().table("subcategorias")
        .select("sede, categoria_codigo, codigo, nombre, mnemotecnia")
        .execute().data
    )
    _cache_subcategorias = {
        (r["sede"].strip().upper(), r["categoria_codigo"].strip(), r["codigo"].strip()): {
            "nombre": r["nombre"], "mnemotecnia": r.get("mnemotecnia")
        }
        for r in rows
    }
    return _cache_subcategorias


def fetch_app_config() -> dict:
    """
    Obtiene la configuración global de la app desde la tabla `app_config`.
    Se espera que la tabla tenga columnas `clave` y `valor`.
    Retorna un dict {clave: valor}. En caso de error retorna dict vacío.
    """
    try:
        rows = (
            get_client()
            .table("app_config")
            .select("clave, valor")
            .execute()
            .data
        )
        return {r["clave"]: r["valor"] for r in rows}
    except Exception:
        return {}


def invalidar_cache_catalogo() -> None:
    """Limpia los cachés de categorías y subcategorías (al cambiar de sede)."""
    global _cache_categorias, _cache_subcategorias
    _cache_categorias    = None
    _cache_subcategorias = None


def re_enriquecer_productos() -> None:
    """
    Re-aplica nombres de categoría/subcategoría a los productos ya en memoria,
    usando el caché de categorías recién recargado.
    Llamar siempre DESPUÉS de invalidar_cache_catalogo().
    """
    global _cache_productos
    if not _cache_productos:
        return
    cats = fetch_categorias()
    subs = fetch_subcategorias()
    for p in _cache_productos:
        ck     = p.get("categoria_codigo", "")
        sk     = p.get("subcategoria_codigo", "")
        sede_p = (p.get("sede") or "").strip().upper()
        p["categoria_nombre"]    = cats.get((sede_p, ck), {"nombre": ck})["nombre"]
        p["subcategoria_nombre"] = subs.get((sede_p, ck, sk), {"nombre": sk})["nombre"]


def fetch_productos() -> list[dict]:
    """
    Retorna todos los productos.
    Orden de prioridad:
      1. Cache en memoria  (_cache_productos)
      2. Cache en disco    (cache_productos.json, si no expiró el TTL)
      3. Supabase          (6500+ registros en chunks)

    Thread-safe: _fetch_lock evita dos descargas simultáneas desde Supabase.
    El token de invalidación previene guardar en disco si el usuario cerró sesión
    mientras se realizaba el fetch.
    """
    global _cache_productos

    # Revisión rápida sin lock (camino feliz)
    if _cache_productos is not None:
        return _cache_productos

    with _fetch_lock:
        # Segunda revisión dentro del lock (otro hilo pudo haber terminado primero)
        if _cache_productos is not None:
            return _cache_productos

        # ── Intentar cache en disco ───────────────────────────────────────────
        cached = _leer_cache_disco()
        if cached:
            _cache_productos = cached
            return cached

        # ── Capturar token antes de la descarga ───────────────────────────────
        token = _invalidation_count

        # ── Fetch desde Supabase ──────────────────────────────────────────────
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
            sede_p = p["sede"] if p.get("sede") else ""
            if sede_p:
                p["sede"] = sede_p.strip().upper()
            sede_p = p["sede"]

            cat_data = cats.get((sede_p, ck), {"nombre": ck})
            sub_data = subs.get((sede_p, ck, sk), {"nombre": sk})

            p["categoria_nombre"]    = cat_data["nombre"]
            p["subcategoria_nombre"] = sub_data["nombre"]

        # Guardar en disco solo si no hubo logout durante el fetch
        _guardar_cache_disco(all_rows, token)

        # Solo almacenar en memoria si la cache sigue vigente
        if token == _invalidation_count:
            _cache_productos = all_rows

        return all_rows


# ── Quiz ──────────────────────────────────────────────────────────────────────

def fetch_todos_para_quiz(sede: str = "Prisma") -> dict:
    """
    Retorna categorías, subcategorías y productos filtrados por sede.
    Las categorías y subcategorías se derivan de los productos ya cargados,
    garantizando que reflejen exactamente la sede seleccionada.
    No usa caché propio: los productos ya están en memoria.
    """
    prods_raw = fetch_productos()

    if sede != "Prisma":
        sede_upper = sede.strip().upper()
        prods = [p for p in prods_raw if (p.get("sede") or "").upper() == sede_upper]
    else:
        prods = prods_raw

    # Derivar categorías y subcategorías únicas de los productos filtrados
    cats_dict: dict[str, str] = {}
    subs_dict: dict[tuple, str] = {}
    for p in prods:
        ck = p["categoria_codigo"]
        sk = p["subcategoria_codigo"]
        if ck not in cats_dict:
            cats_dict[ck] = p.get("categoria_nombre") or ck
        if (ck, sk) not in subs_dict:
            subs_dict[(ck, sk)] = p.get("subcategoria_nombre") or sk

    return {
        "categorias": [
            {"codigo": k, "nombre": v, "mnemotecnia": None}
            for k, v in sorted(cats_dict.items())
        ],
        "subcategorias": [
            {"categoria_codigo": k[0], "codigo": k[1], "nombre": v, "mnemotecnia": None}
            for k, v in sorted(subs_dict.items())
        ],
        "productos": prods,
    }


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
