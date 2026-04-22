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
_cache_categorias:    Optional[dict] = None   # clave: (casa, codigo)
_cache_subcategorias: Optional[dict] = None   # clave: (casa, cat_codigo, codigo)
_cache_productos:     Optional[list] = None

# ── Cache en disco ────────────────────────────────────────────────────────────
_PRODUCTOS_CACHE_FILE = Path(__file__).parent / "cache_productos.json"
_CACHE_TTL_MINUTOS    = 14   # Máximo tiempo (min) cerrada la app para reusar cache

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
    """
    if token_invalidacion != _invalidation_count:
        return   # Cache fue invalidada mientras se fetcheaba → no guardar
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
                return None   # Expirado por TTL

        # Verificar si la versión de datos del servidor cambió mientras la app estuvo cerrada.
        # Si fetch_config() falla (sin internet) se usa la caché normalmente sin crashear.
        try:
            from updater import AppUpdater
            if AppUpdater.check_data_version():
                return None   # Datos desactualizados — forzar re-fetch desde Supabase
        except Exception:
            pass

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
    Retorna todas las categorías de todas las casas.
    Clave: (casa_upper, codigo) → {"nombre": ..., "mnemotecnia": ...}
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
    Retorna todas las subcategorías de todas las casas.
    Clave: (casa_upper, cat_codigo, codigo) → {"nombre": ..., "mnemotecnia": ...}
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


def invalidar_cache_catalogo() -> None:
    """Limpia los cachés de categorías, subcategorías y productos para forzar recarga."""
    global _cache_categorias, _cache_subcategorias, _cache_productos, _invalidation_count
    _cache_categorias    = None
    _cache_subcategorias = None
    _cache_productos     = None
    _invalidation_count += 1
    
    # También eliminamos el cache en disco para asegurar que traiga las nuevas sedes
    try:
        if _PRODUCTOS_CACHE_FILE.exists():
            _PRODUCTOS_CACHE_FILE.unlink()
    except Exception:
        pass


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
        ck      = p.get("categoria_codigo", "")
        sk      = p.get("subcategoria_codigo", "")
        casa_p  = (p.get("sede") or "").strip().upper()
        p["categoria_nombre"]    = cats.get((casa_p, ck), {"nombre": ck})["nombre"]
        p["subcategoria_nombre"] = subs.get((casa_p, ck, sk), {"nombre": sk})["nombre"]


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
                    "nombre, mnemotecnia, codigo_completo, imagen_url, sede, marca"
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
            mk = (p.get("marca") or "").strip()

            p["categoria_codigo"]    = ck
            p["subcategoria_codigo"] = sk
            p["codigo"]              = pk
            p["marca"]               = mk

            if p.get("codigo_completo"):
                p["codigo_completo"] = p["codigo_completo"].strip()
            casa_p = p["sede"] if p.get("sede") else ""
            if casa_p:
                p["sede"] = casa_p.strip().upper()
            casa_p = p["sede"]

            cat_data = cats.get((casa_p, ck), {"nombre": ck})
            sub_data = subs.get((casa_p, ck, sk), {"nombre": sk})

            p["categoria_nombre"]    = cat_data["nombre"]
            p["subcategoria_nombre"] = sub_data["nombre"]

        # Guardar en disco solo si no hubo logout durante el fetch
        _guardar_cache_disco(all_rows, token)

        # Solo almacenar en memoria si la cache sigue vigente
        if token == _invalidation_count:
            _cache_productos = all_rows

        return all_rows


# ── Quiz ──────────────────────────────────────────────────────────────────────

def fetch_todos_para_quiz(casa: str = "FEBECA") -> dict:
    """
    Retorna categorías, subcategorías y productos filtrados por casa.
    Las categorías y subcategorías se derivan de los productos ya cargados,
    garantizando que reflejen exactamente la casa seleccionada.
    No usa caché propio: los productos ya están en memoria.
    """
    prods_raw = fetch_productos()
    cats_cache = fetch_categorias()
    subs_cache = fetch_subcategorias()

    if casa:
        casa_upper = casa.strip().upper()
        prods = [p for p in prods_raw if (p.get("sede") or "").upper() == casa_upper]
    else:
        prods = prods_raw

    # ── Filtro por usuario (solo Pavco para cuentas de prueba/soporte) ────────
    import auth
    sesion = auth.get_sesion()
    email = (sesion.email or "").lower() if sesion else ""
    if email in ["carmonaluise@gmail.com", "test@test.test", "mirelis.cabrera.c@gmail.com"]:
        prods = [p for p in prods if (p.get("marca") or "").upper() == "PAVCO"]

    # Derivar categorías y subcategorías únicas, preservando la mnemotecnia de BD
    cats_dict: dict[str, dict] = {}
    subs_dict: dict[tuple, dict] = {}
    for p in prods:
        ck      = p["categoria_codigo"]
        sk      = p["subcategoria_codigo"]
        casa_p  = (p.get("sede") or "").strip().upper()
        if ck not in cats_dict:
            cat_data = cats_cache.get((casa_p, ck), {})
            cats_dict[ck] = {
                "nombre":      p.get("categoria_nombre") or ck,
                "mnemotecnia": cat_data.get("mnemotecnia"),
            }
        if (ck, sk) not in subs_dict:
            sub_data = subs_cache.get((casa_p, ck, sk), {})
            subs_dict[(ck, sk)] = {
                "nombre":      p.get("subcategoria_nombre") or sk,
                "mnemotecnia": sub_data.get("mnemotecnia"),
            }

    return {
        "categorias": [
            {"codigo": k, "nombre": v["nombre"], "mnemotecnia": v["mnemotecnia"]}
            for k, v in sorted(cats_dict.items())
        ],
        "subcategorias": [
            {"categoria_codigo": k[0], "codigo": k[1],
             "nombre": v["nombre"], "mnemotecnia": v["mnemotecnia"]}
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


def actualizar_o_crear_sesion_uso(usuario_id: str, segundos: int) -> Optional[str]:
    """
    Suma `segundos` al duracion_seg del registro de HOY o crea uno nuevo si cambió el día.
    Retorna el ID de la sesión (nueva o actualizada).
    """
    if segundos <= 0:
        return None
    try:
        ahora = datetime.now(timezone.utc)
        hoy_str = ahora.date().isoformat()
        print(f"[DB_SESION] Usuario: {usuario_id}, Segundos: {segundos}")

        # 1. Buscar la última sesión para ver si es de hoy
        result = (
            get_client().table("sesiones_uso")
            .select("id, inicio_en, duracion_seg")
            .eq("usuario_id", usuario_id)
            .order("inicio_en", desc=True)
            .limit(1)
            .execute()
        )

        ultima = result.data[0] if (result.data and len(result.data) > 0) else None

        if ultima:
            inicio_dt = datetime.fromisoformat(ultima["inicio_en"].replace("Z", "+00:00"))
            if inicio_dt.date().isoformat() == hoy_str:
                # MISMO DÍA: Actualizar fin_en y sumar segundos
                actual = (ultima.get("duracion_seg") or 0)
                print(f"[DB_SESION] Actualizando sesión {ultima['id']} (Hoy: {hoy_str})")
                get_client().table("sesiones_uso").update({
                    "duracion_seg": actual + segundos,
                    "fin_en":       ahora.isoformat(),
                }).eq("id", ultima["id"]).execute()
                return ultima["id"]
            else:
                print(f"[DB_SESION] Diferente día. Ultima fue: {inicio_dt.date().isoformat()}, Hoy: {hoy_str}")
        else:
            print("[DB_SESION] No se encontró sesión previa.")

        # DÍA DIFERENTE (o no hay sesión previa): Crear nuevo registro
        new_row = {
            "usuario_id":   usuario_id,
            "inicio_en":    ahora.isoformat(),
            "fin_en":       ahora.isoformat(),
            "duracion_seg": segundos
        }
        res_ins = get_client().table("sesiones_uso").insert(new_row).execute()
        
        if res_ins.data:
            new_id = res_ins.data[0]["id"]
            print(f"[DB_SESION] Nueva sesión creada: {new_id}")
            return new_id
        else:
            print(f"[DB_SESION] Error: insert retornó vacío. {res_ins}")
            return None
    except Exception as e:
        print(f"[DB_SESION] EXCEPCIÓN: {e}")
        return None




import threading

def guardar_resultado_juego(
    usuario_id: str, 
    tipo_juego: str, 
    aciertos: int, 
    fallos: int, 
    total_preguntas: int,
    duracion_segundos: int,
    configuracion: dict,
    detalle_interacciones: list[dict]
) -> None:
    """Guarda el resultado completo de un juego en un hilo separado para no bloquear la interfaz."""
    def _run():
        try:
            get_client().table("resultados_codex").insert({
                "usuario_id": usuario_id,
                "tipo_juego": tipo_juego,
                "aciertos": aciertos,
                "fallos": fallos,
                "total_preguntas": total_preguntas,
                "duracion_segundos": duracion_segundos,
                "configuracion": configuracion,
                "detalle_interacciones": detalle_interacciones
            }).execute()
        except Exception as e:
            print(f"Error guardando resultado de juego: {e}")
            
    threading.Thread(target=_run, daemon=True).start()


def fetch_estadisticas_usuario(usuario_id: str) -> dict:
    """Obtiene y calcula los KPIs del usuario desde Supabase, separando Contrarreloj."""
    try:
        # Obtener todos los resultados del usuario
        response = get_client().table("resultados_codex").select("*").eq("usuario_id", usuario_id).execute()
        resultados = response.data
        
        # Inicializar estructuras base
        stats = {
            "practica": {
                "partidas": 0, "aciertos": 0, "fallos": 0, "tiempo_segundos": 0, "puntos_ciegos": []
            },
            "contrarreloj": {
                "partidas": 0, "aciertos": 0, "fallos": 0, "tiempo_segundos": 0, "mejor_marca": 0
            }
        }
        
        if not resultados:
            return stats
            
        conteo_errores_practica = {}
        
        for r in resultados:
            tipo = r.get("tipo_juego", "desconocido")
            aciertos = r.get("aciertos", 0)
            fallos = r.get("fallos", 0)
            tiempo = r.get("duracion_segundos", 0)
            
            if tipo == "contrarreloj":
                stats["contrarreloj"]["partidas"] += 1
                stats["contrarreloj"]["aciertos"] += aciertos
                stats["contrarreloj"]["fallos"] += fallos
                stats["contrarreloj"]["tiempo_segundos"] += tiempo
                if aciertos > stats["contrarreloj"]["mejor_marca"]:
                    stats["contrarreloj"]["mejor_marca"] = aciertos
            else:
                stats["practica"]["partidas"] += 1
                stats["practica"]["aciertos"] += aciertos
                stats["practica"]["fallos"] += fallos
                stats["practica"]["tiempo_segundos"] += tiempo
                
                # Extraer Top de errores (solo de práctica)
                detalles = r.get("detalle_interacciones") or []
                if isinstance(detalles, str):
                    import json
                    try: detalles = json.loads(detalles)
                    except: detalles = []
                    
                for interaccion in detalles:
                    if not interaccion.get("fue_correcta", True):
                        pregunta = interaccion.get("pregunta", "Desconocido")
                        correcta = interaccion.get("respuesta_correcta", "Desconocido")
                        clave = f"{pregunta} (Debía ser: {correcta})"
                        conteo_errores_practica[clave] = conteo_errores_practica.get(clave, 0) + 1
        
        # Ordenar y sacar el Top 5 de errores en práctica
        top_errores = sorted(conteo_errores_practica.items(), key=lambda x: x[1], reverse=True)[:5]
        stats["practica"]["puntos_ciegos"] = [{"concepto": k, "veces": v} for k, v in top_errores]
        
        return stats
    except Exception as e:
        print(f"Error extrayendo estadísticas: {e}")
        return {
            "practica": {"partidas": 0, "aciertos": 0, "fallos": 0, "tiempo_segundos": 0, "puntos_ciegos": []},
            "contrarreloj": {"partidas": 0, "aciertos": 0, "fallos": 0, "tiempo_segundos": 0, "mejor_marca": 0}
        }

def resetear_estadisticas_usuario(usuario_id: str) -> bool:
    """Elimina todos los resultados y sesiones del usuario en Supabase."""
    try:
        # 1. Eliminar resultados de juegos
        database_client = get_client()
        database_client.table("resultados_codex").delete().eq("usuario_id", usuario_id).execute()
        # 2. Eliminar sesiones de uso (esto reinicia el tiempo de estudio)
        database_client.table("sesiones_uso").delete().eq("usuario_id", usuario_id).execute()
        return True
    except Exception as e:
        print(f"Error reseteando estadísticas: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# FIN DEL MÓDULO
# ══════════════════════════════════════════════════════════════════════════════
