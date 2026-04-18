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
# ── Seguimiento de actividad ──────────────────────────────────────────────────
_INACTIVIDAD_SEG   = 300       # 5 minutos sin actividad para cerrar segmento
_SYNC_INTERVAL_SEG  = 60        # Sincronizar cada 1 min de actividad acumulada
_segmento_inicio:  Optional[datetime] = None   # cuándo empezó el tramo activo actual
_ultimo_actividad: Optional[datetime] = None   # última vez que se detectó interacción
_acumulado_segmento: int = 0                     # segundos acumulados en el tramo actual


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
            # Asegurar inicio de tracking al restaurar
            registrar_inicio_uso()
        else:
            _borrar_sesion_disco()
            _sesion_activa = None
    return _sesion_activa

def registrar_actividad() -> None:
    """
    Llamar ante cualquier interacción del usuario (toque, teclado, navegación).
    Si no hay segmento activo, inicia uno nuevo.
    Si el acumulado supera el tramo de sincronización, flushea a BD.
    """
    global _segmento_inicio, _ultimo_actividad, _acumulado_segmento
    ahora = datetime.now(timezone.utc)
    
    if _ultimo_actividad is not None and _segmento_inicio is not None:
        lapso = (ahora - _ultimo_actividad).total_seconds()
        if lapso < _INACTIVIDAD_SEG:
            _acumulado_segmento += int(lapso)
        else:
            # Venimos de una inactividad larga que el corazón quizás no capturó aún
            _flush_segmento()
            _segmento_inicio = ahora
            _acumulado_segmento = 0

    _ultimo_actividad = ahora

    if _segmento_inicio is None:
        _segmento_inicio = ahora
        _acumulado_segmento = 0
        print(f"[ACTIVIDAD] Nuevo segmento iniciado: {ahora.strftime('%H:%M:%S')}")

    # Sincronización automática cada 1 minuto de actividad neta
    if _acumulado_segmento >= _SYNC_INTERVAL_SEG:
        _flush_segmento()
        # Reiniciar segmento para seguir contando
        _segmento_inicio = ahora
        _acumulado_segmento = 0



def sincronizar_ahora() -> None:
    """Fuerza el guardado inmediato del tiempo acumulado en la base de datos."""
    _flush_segmento()
    # Reiniciar para que la siguiente actividad empiece limpia
    registrar_actividad()


def _flush_segmento() -> None:
    """Cierra el tramo activo y acumula su duración en la BD usando la lógica de upsert."""
    global _segmento_inicio, _ultimo_actividad, _acumulado_segmento, _sesion_activa
    
    if _segmento_inicio is None or _sesion_activa is None:
        return

    # Si no hubo guardado por sync, calculamos el total desde el inicio
    segundos = _acumulado_segmento
    if segundos <= 0 and _ultimo_actividad:
        segundos = max(0, int((_ultimo_actividad - _segmento_inicio).total_seconds()))
    
    print(f"[ACTIVIDAD] Intentando flush: {segundos}s (Acumulado: {_acumulado_segmento}s)")
    
    _segmento_inicio = None
    _acumulado_segmento = 0
    
    if segundos > 0:


        from database import actualizar_o_crear_sesion_uso
        try:
            nuevo_id_uso = actualizar_o_crear_sesion_uso(_sesion_activa.id, segundos)
            if nuevo_id_uso:
                _sesion_activa.id_uso = nuevo_id_uso
                _guardar_sesion(_sesion_activa)
                print(f"[ACTIVIDAD] BD Sincronizada: +{segundos}s para sesión {_sesion_activa.id_uso}")
        except Exception as exc:
            print(f"[ACTIVIDAD] Error al sincronizar: {exc}")


def registrar_inicio_uso() -> None:
    """
    Garantiza que la sesión esté inicializada. 
    Llamar al abrir la app o iniciar sesión.
    """
    global _sesion_activa
    if not _sesion_activa:
        return
    
    # Forzar una sincronización inicial de 1s para asegurar el registro en DB
    # o simplemente registrar actividad para abrir el primer tramo.
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
    """
    Flushea el tramo activo y marca el timestamp de cierre en el cache de productos.
    El cache se reutiliza si la app se reabre dentro de los 60 min siguientes;
    si pasó más tiempo, _leer_cache_disco() lo descarta automáticamente.
    """
    _flush_segmento()
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
    """Flushea el segmento activo y borra los 3 archivos locales (cache, sesión, preferencias)."""
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
    try:
        import preferences
        preferences.limpiar()
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
    # Registrar inicio de uso para tracking de actividad
    registrar_inicio_uso()

    try:
        actualizar_ultimo_acceso(_sesion_activa.id)
    except Exception:
        pass

    return ResultadoLogin(
        exitoso=True,
        mensaje=f"Bienvenido, {_sesion_activa.nombre}",
        sesion=_sesion_activa,
    )


# ── Registro ──────────────────────────────────────────────────────────────────

@dataclass
class ResultadoRegistro:
    exitoso: bool
    mensaje: str


def registrar_usuario(nombre: str, email: str, password: str) -> ResultadoRegistro:
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