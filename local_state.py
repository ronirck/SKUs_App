"""
local_state.py — Singleton de estado de vidas y progreso.

Reglas:
- El estado vive en memoria (dict _state) y se persiste en local_game_state.json
- Supabase se lee UNA sola vez al iniciar (inicializar_desde_supabase)
- Supabase se escribe solo al perder vida o completar nivel (fire-and-forget)
- El contador de vidas es aritmética pura con datetime — sin red, sin threads propios
- InicioView solo lee de aquí, nunca escribe directamente
"""

import json
import os
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

_STATE_FILE = Path(__file__).parent / "local_game_state.json"

# ── Singleton en memoria ──────────────────────────────────────────────────────
_state: dict = {
    "usuario_id":     None,
    "vidas":          5,
    "ultima_perdida": None,   # ISO string UTC o None
    "niveles":        {},     # {"1": {desbloqueado, completado, mejor_puntaje}}
}
_inicializado: bool  = False
_lock          = threading.Lock()


# ══════════════════════════════════════════════════════════════════════════════
# PERSISTENCIA LOCAL
# ══════════════════════════════════════════════════════════════════════════════

def _guardar() -> None:
    """Escribe el estado en disco. Thread-safe."""
    with _lock:
        try:
            with open(_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(_state, f)
        except Exception:
            pass


def _cargar() -> bool:
    """Lee el estado desde disco. Retorna True si había datos válidos."""
    global _state
    try:
        if not _STATE_FILE.exists():
            return False
        with open(_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        with _lock:
            _state.update(data)
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# ARITMÉTICA DE VIDAS — SIN RED
# ══════════════════════════════════════════════════════════════════════════════

def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _recalcular_vidas_en_memoria() -> None:
    """
    Aplica la recuperación de vidas por tiempo directamente sobre _state.
    1 vida cada 5 minutos desde ultima_perdida. Sin I/O.
    """
    with _lock:
        vidas  = _state["vidas"]
        ultima = _parse_dt(_state.get("ultima_perdida"))

        if vidas >= 5 or ultima is None:
            _state["vidas"] = min(5, vidas)
            if _state["vidas"] >= 5:
                _state["ultima_perdida"] = None
            return

        ahora       = datetime.now(timezone.utc)
        segundos    = (ahora - ultima).total_seconds()
        recuperadas = int(segundos // 300)   # 1 vida cada 300s = 5min

        if recuperadas <= 0:
            return

        nuevas = min(5, vidas + recuperadas)
        _state["vidas"] = nuevas

        if nuevas >= 5:
            _state["ultima_perdida"] = None
        else:
            nueva_ultima = ultima + timedelta(seconds=recuperadas * 300)
            _state["ultima_perdida"] = nueva_ultima.isoformat()


# ══════════════════════════════════════════════════════════════════════════════
# API PÚBLICA — LECTURA
# ══════════════════════════════════════════════════════════════════════════════

def get_vidas() -> int:
    """Devuelve las vidas actuales (ya recalculadas)."""
    _recalcular_vidas_en_memoria()
    return _state.get("vidas", 5)


def get_ultima_perdida() -> Optional[str]:
    return _state.get("ultima_perdida")


def segundos_para_proxima_vida() -> int:
    """
    Segundos restantes para recuperar la próxima vida.
    0 si ya tiene 5. Puro datetime, sin red.
    """
    _recalcular_vidas_en_memoria()
    vidas  = _state.get("vidas", 5)
    ultima = _parse_dt(_state.get("ultima_perdida"))

    if vidas >= 5 or ultima is None:
        return 0

    ahora   = datetime.now(timezone.utc)
    pasados = (ahora - ultima).total_seconds() % 300
    return max(0, int(300 - pasados))


def get_estado_nivel(numero: int) -> dict:
    info = _state["niveles"].get(str(numero))
    if info:
        return dict(info)
    if numero == 1:
        return {"desbloqueado": True, "completado": False, "mejor_puntaje": 0}
    return {"desbloqueado": False, "completado": False, "mejor_puntaje": 0}


def get_todos_niveles() -> dict[int, dict]:
    _recalcular_vidas_en_memoria()
    return {n: get_estado_nivel(n) for n in range(1, 21)}


def ya_inicializado(usuario_id: str) -> bool:
    """True si el estado ya está cargado para este usuario."""
    return _inicializado and _state.get("usuario_id") == usuario_id


# ══════════════════════════════════════════════════════════════════════════════
# API PÚBLICA — ESCRITURA
# ══════════════════════════════════════════════════════════════════════════════

def inicializar_desde_supabase(usuario_id: str) -> None:
    """
    Carga el estado desde Supabase y lo persiste localmente.
    Llamar UNA sola vez al iniciar sesión o al detectar que no hay estado local.
    """
    global _inicializado
    try:
        import database as db
        vidas_data = db.fetch_vidas(usuario_id)
        progreso   = db.fetch_progreso_niveles(usuario_id)

        with _lock:
            _state["usuario_id"]     = usuario_id
            _state["vidas"]          = vidas_data["vidas_actuales"]
            _state["ultima_perdida"] = vidas_data.get("ultima_perdida_en")
            _state["niveles"]        = {str(k): v for k, v in progreso.items()}

        _recalcular_vidas_en_memoria()
        _guardar()
        _inicializado = True
    except Exception:
        # Sin red: marcar como inicializado con lo que hay
        with _lock:
            _state["usuario_id"] = usuario_id
        _inicializado = True


def inicializar(usuario_id: str) -> None:
    """
    Punto de entrada principal. Carga desde disco si es el mismo usuario,
    o desde Supabase si es la primera vez.
    """
    global _inicializado

    if ya_inicializado(usuario_id):
        # Ya está en memoria — solo recalcular vidas por tiempo
        _recalcular_vidas_en_memoria()
        return

    # Intentar cargar desde disco
    hay_local = _cargar()
    mismo_usuario = _state.get("usuario_id") == usuario_id

    if hay_local and mismo_usuario:
        _recalcular_vidas_en_memoria()
        _guardar()
        _inicializado = True
    else:
        # Primera vez o usuario diferente → sync desde Supabase
        inicializar_desde_supabase(usuario_id)


def perder_vida() -> int:
    """
    Descuenta 1 vida. Actualiza memoria y disco inmediatamente.
    Retorna las vidas restantes.
    """
    _recalcular_vidas_en_memoria()
    with _lock:
        nuevas = max(0, _state["vidas"] - 1)
        _state["vidas"] = nuevas
        if nuevas < 5 and not _state.get("ultima_perdida"):
            _state["ultima_perdida"] = datetime.now(timezone.utc).isoformat()
        elif nuevas < _state.get("vidas", 5):
            # Resetear el timer de la última pérdida
            _state["ultima_perdida"] = datetime.now(timezone.utc).isoformat()
    _guardar()
    return _state["vidas"]


def guardar_resultado_nivel(numero: int, aciertos: int) -> bool:
    """
    Guarda el resultado localmente. Retorna True si aprobó (>=7).
    """
    aprobado = aciertos >= 7
    clave    = str(numero)

    with _lock:
        actual = _state["niveles"].get(clave, {
            "desbloqueado": True, "completado": False, "mejor_puntaje": 0})
        actual["mejor_puntaje"] = max(actual.get("mejor_puntaje", 0), aciertos)
        if aprobado:
            actual["completado"] = True
        _state["niveles"][clave] = actual

        if aprobado and numero < 20:
            sig     = str(numero + 1)
            sig_inf = _state["niveles"].get(sig, {
                "desbloqueado": False, "completado": False, "mejor_puntaje": 0})
            sig_inf["desbloqueado"] = True
            _state["niveles"][sig]  = sig_inf

    _guardar()
    return aprobado


def limpiar() -> None:
    """Limpia el estado al cerrar sesión."""
    global _inicializado
    with _lock:
        _state.update({
            "usuario_id": None, "vidas": 5,
            "ultima_perdida": None, "niveles": {},
        })
    _inicializado = False
    try:
        if _STATE_FILE.exists():
            os.remove(_STATE_FILE)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# SISTEMA DE CALLBACKS PARA ACTUALIZAR LA UI
# La UI se suscribe a cambios de vidas con on_vidas_change(callback)
# local_state llama al callback cada vez que las vidas cambian
# ══════════════════════════════════════════════════════════════════════════════

_callback_vidas = None   # función(vidas: int, segundos: int) -> None


def suscribir_ui(callback) -> None:
    """La UI llama a esto para recibir actualizaciones de vidas."""
    global _callback_vidas
    _callback_vidas = callback


def desuscribir_ui() -> None:
    global _callback_vidas
    _callback_vidas = None


def _notificar_ui() -> None:
    if _callback_vidas:
        try:
            _callback_vidas(get_vidas(), segundos_para_proxima_vida())
        except Exception:
            pass


def iniciar_contador_global(page) -> None:
    """
    Loop que actualiza las vidas cada segundo y notifica a la UI.
    Se lanza una sola vez. Si ya hay uno corriendo no lanza otro.
    El loop sobrevive a los cambios de vista porque vive en page.run_thread
    y no depende de referencias a controles específicos.
    """
    global _contador_corriendo
    if getattr(iniciar_contador_global, '_corriendo', False):
        return
    iniciar_contador_global._corriendo = True

    import time as _time

    def loop():
        while True:
            _time.sleep(1)
            _recalcular_vidas_en_memoria()
            _notificar_ui()
            # El loop corre siempre — la UI puede desuscribirse cuando no la necesita
    page.run_thread(loop)