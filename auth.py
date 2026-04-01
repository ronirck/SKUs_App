"""
auth.py — Lógica de autenticación y sesión persistente.
La sesión se guarda en un archivo local session.json al hacer login
y se elimina al cerrar sesión. Al arrancar la app se intenta
restaurar automáticamente sin tocar Supabase.
"""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import atexit
import bcrypt
from datetime import datetime, timezone

from database import fetch_usuario_por_email, insertar_usuario, actualizar_ultimo_acceso

# Ruta del archivo de sesión — mismo directorio que este script
_SESSION_FILE = Path(__file__).parent / "session.json"


# ── Modelo de sesión ──────────────────────────────────────────────────────────

@dataclass
class Sesion:
    id:             str
    nombre:         str
    email:          str
    id_uso:         Optional[str] = None  # ID de la tabla sesiones_uso para tracking de performance


# Estado en memoria
_sesion_activa:    Optional[Sesion]   = None

# ── Seguimiento de actividad ──────────────────────────────────────────────────
_INACTIVIDAD_SEG  = 60          # segundos sin actividad para cerrar segmento
_segmento_inicio: Optional[datetime] = None   # cuándo empezó el tramo activo actual
_ultimo_actividad: Optional[datetime] = None  # última vez que se detectó interacción


# ── Persistencia ──────────────────────────────────────────────────────────────

def _guardar_sesion(sesion: Sesion) -> None:
    """Escribe la sesión en disco para restaurarla al reabrir la app."""
    try:
        with open(_SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(sesion), f)
    except Exception:
        pass  # Si falla el guardado la app sigue funcionando en memoria


def _cargar_sesion_disco() -> Optional[Sesion]:
    """Lee session.json y retorna un objeto Sesion, o None si no existe."""
    try:
        if not _SESSION_FILE.exists():
            return None
        with open(_SESSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Sesion(
            id=data["id"],
            nombre=data["nombre"],
            email=data["email"],
            id_uso=data.get("id_uso"),
        )
    except Exception:
        # Archivo corrupto o formato inválido — ignorar
        return None


def _borrar_sesion_disco() -> None:
    """Elimina session.json del disco."""
    try:
        if _SESSION_FILE.exists():
            os.remove(_SESSION_FILE)
    except Exception:
        pass


# ── API pública ───────────────────────────────────────────────────────────────

def restaurar_sesion() -> Optional[Sesion]:
    """
    Llamar al arrancar la app. Carga auth y crea una sesion_uso nueva.
    """
    global _sesion_activa
    if _sesion_activa:
        return _sesion_activa
    
    s = _cargar_sesion_disco()
    if s:
        # Verificar en DB que el usuario sigue existiendo y es válido
        from database import fetch_usuario_por_email
        usuario = fetch_usuario_por_email(s.email)
        if usuario:
            _sesion_activa = s
        else:
            _borrar_sesion_disco()
            _sesion_activa = None
    return _sesion_activa

def registrar_actividad() -> None:
    """
    Llamar ante cualquier interacción del usuario (toque, teclado, navegación).
    Si no hay segmento activo, inicia uno nuevo.
    """
    global _segmento_inicio, _ultimo_actividad
    ahora = datetime.now(timezone.utc)
    _ultimo_actividad = ahora
    if _segmento_inicio is None:
        _segmento_inicio = ahora
        print(f"[ACTIVIDAD] Nuevo segmento iniciado: {ahora.strftime('%H:%M:%S')}")


def _flush_segmento() -> None:
    """Cierra el tramo activo y acumula su duración en la BD."""
    global _segmento_inicio, _ultimo_actividad
    if _segmento_inicio is None or _sesion_activa is None or not _sesion_activa.id_uso:
        return
    fin      = _ultimo_actividad or datetime.now(timezone.utc)
    segundos = max(0, int((fin - _segmento_inicio).total_seconds()))
    _segmento_inicio = None
    print(f"[ACTIVIDAD] Segmento cerrado — duración: {segundos}s, acumulando en BD...")
    if segundos > 0:
        from database import acumular_tiempo_sesion
        try:
            acumular_tiempo_sesion(_sesion_activa.id_uso, segundos)
            print(f"[ACTIVIDAD] BD actualizada: +{segundos}s para sesión {_sesion_activa.id_uso}")
        except Exception as exc:
            print(f"[ACTIVIDAD] Error al acumular tiempo: {exc}")


def registrar_inicio_uso() -> None:
    """
    Obtiene el registro sesiones_uso de HOY o crea uno nuevo si es un día distinto.
    Solo hace la consulta a BD la primera vez en este proceso.
    Llamar cuando los productos se carguen por primera vez.
    """
    global _sesion_activa
    if not _sesion_activa:
        return
    # Si ya inicializamos el id_uso este proceso Y ya hay actividad → solo marcar actividad
    if _sesion_activa.id_uso is not None and _ultimo_actividad is not None:
        registrar_actividad()
        return
    # Primera inicialización: buscar sesión de hoy o crear una nueva
    from database import obtener_sesion_hoy, iniciar_sesion_uso
    try:
        sesion_hoy = obtener_sesion_hoy(_sesion_activa.id)
        _sesion_activa.id_uso = sesion_hoy["id"] if sesion_hoy else iniciar_sesion_uso(_sesion_activa.id)
        _guardar_sesion(_sesion_activa)
    except Exception:
        pass
    registrar_actividad()


def registrar_corazon() -> None:
    """
    Ejecutado periódicamente (cada ~10 s).
    Si el usuario lleva más de _INACTIVIDAD_SEG sin interacción, cierra el segmento activo.
    """
    if _ultimo_actividad is None:
        return
    inactivo = (datetime.now(timezone.utc) - _ultimo_actividad).total_seconds()
    if inactivo >= _INACTIVIDAD_SEG:
        _flush_segmento()


def registrar_fin_uso() -> None:
    """Flushea el tramo activo al cerrar la app o desconectar."""
    _flush_segmento()
    # Marcar timestamp de cierre en el cache de productos para calcular TTL
    try:
        from database import marcar_cierre_cache
        marcar_cierre_cache()
    except Exception:
        pass


# Garantizar que se llama al finalizar aunque el proceso termine abruptamente
atexit.register(registrar_fin_uso)


def get_sesion() -> Optional[Sesion]:
    return _sesion_activa


def cerrar_sesion() -> None:
    """Flushea el segmento activo, limpia sesión en memoria/disco e invalida el cache."""
    global _sesion_activa, _segmento_inicio, _ultimo_actividad
    _flush_segmento()
    _segmento_inicio  = None
    _ultimo_actividad = None
    _sesion_activa    = None
    _borrar_sesion_disco()
    try:
        from database import invalidar_cache_productos
        invalidar_cache_productos()
    except Exception:
        pass


# ── Login ─────────────────────────────────────────────────────────────────────

@dataclass
class ResultadoLogin:
    exitoso: bool
    mensaje: str
    sesion:  Optional[Sesion] = None


def intentar_login(email: str, password: str) -> ResultadoLogin:
    if not email.strip():
        return ResultadoLogin(exitoso=False, mensaje="Ingresa tu correo electrónico.")
    if not password:
        return ResultadoLogin(exitoso=False, mensaje="Ingresa tu contraseña.")

    usuario = fetch_usuario_por_email(email)
    if usuario is None:
        return ResultadoLogin(exitoso=False, mensaje="Correo o contraseña incorrectos.")

    hash_guardado: str = usuario.get("password_hash") or ""
    if not hash_guardado:
        return ResultadoLogin(
            exitoso=False,
            mensaje="Este usuario no tiene contraseña. Usa 'Crear usuario'.",
        )

    if not bcrypt.checkpw(password.encode("utf-8"), hash_guardado.encode("utf-8")):
        return ResultadoLogin(exitoso=False, mensaje="Correo o contraseña incorrectos.")

    global _sesion_activa
    _sesion_activa = Sesion(
        id=usuario["id"],
        nombre=usuario["nombre"],
        email=usuario["email"],
    )
    # Guardar en disco para restaurar al reabrir la app
    _guardar_sesion(_sesion_activa)

    try:
        actualizar_ultimo_acceso(_sesion_activa.id)
    except Exception:
        pass

    return ResultadoLogin(
        exitoso=True,
        mensaje=f"Bienvenido, {_sesion_activa.nombre}",
        sesion=_sesion_activa,
    )


# ── Registro — TEMPORAL ───────────────────────────────────────────────────────

@dataclass
class ResultadoRegistro:
    exitoso: bool
    mensaje: str


def registrar_usuario(nombre: str, email: str, password: str) -> ResultadoRegistro:
    """TEMPORAL: eliminar junto con RegistroView en views.py."""
    if not nombre.strip():
        return ResultadoRegistro(exitoso=False, mensaje="Ingresa tu nombre.")
    if not email.strip():
        return ResultadoRegistro(exitoso=False, mensaje="Ingresa tu correo.")
    if len(password) < 6:
        return ResultadoRegistro(
            exitoso=False, mensaje="La contraseña debe tener al menos 6 caracteres.")

    if fetch_usuario_por_email(email):
        return ResultadoRegistro(exitoso=False, mensaje="Ya existe un usuario con ese correo.")

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(10),
    ).decode("utf-8")

    try:
        insertar_usuario(nombre, email, password_hash)
    except Exception as exc:
        return ResultadoRegistro(exitoso=False, mensaje=f"Error al crear usuario: {exc}")

    return ResultadoRegistro(
        exitoso=True,
        mensaje=f"Usuario '{nombre}' creado. Ahora inicia sesión.",
    )