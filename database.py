"""
database.py — Cliente Supabase y todas las queries.
Cliente lazy: se crea la primera vez que se necesita, no al importar.
Esto evita bloquear el hilo principal de Flet al arrancar.
"""

from typing import Optional
from supabase import Client, create_client
from config import SUPABASE_URL, SUPABASE_KEY

_client: Optional[Client] = None

# ── Cachés Globales ───────────────────────────────────────────────────────────
_cache_categorias:    Optional[dict] = None
_cache_subcategorias: Optional[dict] = None
_cache_productos:     Optional[list] = None
_cache_quiz_data:     Optional[dict] = None


def get_client() -> Client:
    """Singleton lazy — se instancia solo la primera vez que se llama."""
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# ── Auth ──────────────────────────────────────────────────────────────────────

def fetch_usuario_por_email(email: str) -> Optional[dict]:
    result = (
        get_client().table("usuarios")
        .select("id, nombre, email, password_hash, status, rol, creado_en, ultimo_acceso")
        .eq("email", email.strip().lower())
        .eq("status", True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def insertar_usuario(nombre: str, email: str, password_hash: str) -> dict:
    result = (
        get_client().table("usuarios")
        .insert({
            "nombre":         nombre.strip(),
            "email":          email.strip().lower(),
            "password_hash":  password_hash,
        })
        .execute()
    )
    if not result.data:
        raise RuntimeError("El servidor no retornó datos.")
    return result.data[0]


def actualizar_ultimo_acceso(usuario_id: str) -> None:
    from datetime import datetime, timezone
    get_client().table("usuarios").update(
        {"ultimo_acceso": datetime.now(timezone.utc).isoformat()}
    ).eq("id", usuario_id).execute()


# ── Catálogo ──────────────────────────────────────────────────────────────────

def fetch_categorias() -> dict[str, str]:
    global _cache_categorias
    if _cache_categorias is not None:
        return _cache_categorias
    # Nuevo esquema: codigo (PK), nombre, mnemotecnia
    rows = get_client().table("categorias").select("codigo, nombre, mnemotecnia").execute().data
    _cache_categorias = {r["codigo"].strip(): {"nombre": r["nombre"], "mnemotecnia": r.get("mnemotecnia")} for r in rows}
    return _cache_categorias


def fetch_subcategorias() -> dict[tuple[str, str], str]:
    global _cache_subcategorias
    if _cache_subcategorias is not None:
        return _cache_subcategorias
    # Nuevo esquema: categoria_codigo, codigo (PK), nombre, mnemotecnia
    rows = (
        get_client().table("subcategorias")
        .select("categoria_codigo, codigo, nombre, mnemotecnia")
        .execute().data
    )
    _cache_subcategorias = {
        (r["categoria_codigo"].strip(), r["codigo"].strip()): {"nombre": r["nombre"], "mnemotecnia": r.get("mnemotecnia")}
        for r in rows
    }
    return _cache_subcategorias


def fetch_productos() -> list[dict]:
    global _cache_productos
    if _cache_productos is not None:
        return _cache_productos
    
    # 6500+ productos: Carga optimizada
    cats = fetch_categorias()
    subs = fetch_subcategorias()
    
    all_rows = []
    chunk_size = 1000
    offset = 0
    
    while True:
        rows = (
            get_client().table("productos")
            .select(
                "categoria_codigo, subcategoria_codigo, codigo, "
                "nombre, mnemotecnia, codigo_completo, imagen_url"
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
    
    rows = all_rows
    
    for p in rows:
        # Limpieza de códigos (Postgres bpchar tiene espacios de relleno)
        ck = p.get("categoria_codigo", "").strip() or ""
        sk = p.get("subcategoria_codigo", "").strip() or ""
        pk = p.get("codigo", "").strip() or ""
        
        p["categoria_codigo"] = ck
        p["subcategoria_codigo"] = sk
        p["codigo"] = pk
        if p.get("codigo_completo"):
            p["codigo_completo"] = p["codigo_completo"].strip()

        cat_data = cats.get(ck, {"nombre": ck})
        sub_data = subs.get((ck, sk), {"nombre": sk})
        
        p["categoria_nombre"]    = cat_data["nombre"]
        p["subcategoria_nombre"] = sub_data["nombre"]
        
    _cache_productos = rows
    return rows


# ── Juego: productos vistos ───────────────────────────────────────────────────





def fetch_todos_para_quiz() -> dict:
    """
    Retorna todo lo necesario para generar preguntas del Quiz de Opciones:
    categorias, subcategorias y productos con sus nombres.
    """
    global _cache_quiz_data
    if _cache_quiz_data is not None:
        return _cache_quiz_data
        
    cats_raw = fetch_categorias()
    subs_raw = fetch_subcategorias()
    prods_raw = fetch_productos()

    _cache_quiz_data = {
        "categorias":    [{"codigo": k, "nombre": v["nombre"], "mnemotecnia": v["mnemotecnia"]} for k, v in cats_raw.items()],
        "subcategorias": [{"categoria_codigo": k[0], "codigo": k[1], "nombre": v["nombre"], "mnemotecnia": v["mnemotecnia"]} for k, v in subs_raw.items()],
        "productos":     prods_raw,
    }
    return _cache_quiz_data


# ── Progreso ──────────────────────────────────────────────────────────────────

# ── Sesiones de Uso ───────────────────────────────────────────────────────────

def iniciar_sesion_uso(usuario_id: str) -> Optional[str]:
    """Crea una entrada en sesiones_uso y retorna el ID."""
    try:
        result = (
            get_client().table("sesiones_uso")
            .insert({"usuario_id": usuario_id})
            .execute()
        )
        return result.data[0]["id"] if result.data else None
    except Exception:
        return None


def finalizar_sesion_uso(sesion_id: str) -> None:
    """Registra el fin de la sesión."""
    from datetime import datetime, timezone
    try:
        get_client().table("sesiones_uso").update({
            "fin_en": datetime.now(timezone.utc).isoformat()
        }).eq("id", sesion_id).execute()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# FIN DEL MÓDULO
# ══════════════════════════════════════════════════════════════════════════════