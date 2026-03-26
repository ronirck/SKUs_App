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
_sesion_activa: Optional[Sesion] = None


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

def registrar_inicio_uso() -> None:
    """Inicia sesión de uso, ej. al cargar productos por primera vez."""
    global _sesion_activa
    if _sesion_activa and not _sesion_activa.id_uso:
        from database import iniciar_sesion_uso
        _sesion_activa.id_uso = iniciar_sesion_uso(_sesion_activa.id)
        # Guardar inmediatamente para que el id_uso persista si hay crash
        _guardar_sesion(_sesion_activa)

def registrar_corazon() -> None:
    """Actualiza la hora de fin (heartbeat) para evitar pérdida de datos si hay crash."""
    global _sesion_activa
    if _sesion_activa and _sesion_activa.id_uso:
        from database import finalizar_sesion_uso
        try:
            finalizar_sesion_uso(_sesion_activa.id_uso)
        except Exception:
            pass

def registrar_fin_uso() -> None:
    """Finaliza sesión de uso, ej. al desconectar/cerrar app."""
    global _sesion_activa
    if _sesion_activa and _sesion_activa.id_uso:
        from database import finalizar_sesion_uso
        try:
            finalizar_sesion_uso(_sesion_activa.id_uso)
        except Exception:
            pass
        _sesion_activa.id_uso = None


# Garantizar que se llama al finalizar aunque el proceso termine abruptamente
atexit.register(registrar_fin_uso)


def get_sesion() -> Optional[Sesion]:
    return _sesion_activa


def cerrar_sesion() -> None:
    """Limpia la sesión en memoria y en disco."""
    global _sesion_activa
    _sesion_activa = None
    _borrar_sesion_disco()


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