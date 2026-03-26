"""
game_state.py — Lógica pura de los dos modos de juego.
Sin dependencias de Flet ni Supabase.
"""

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
# CÓDIGO ROTO
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class RespuestaCR:
    producto_nombre:   str
    codigo_correcto:   str
    codigo_respondido: str
    intentos:          int
    pista_usada:       bool
    correcta:          bool


@dataclass
class EstadoCodigoRoto:
    productos:       list[dict]
    total_preguntas: int
    indice_actual:   int = 0
    intentos_actuales: int = 0
    pista_activa:    bool = False
    puntos:          int = 0
    respuestas:      list[RespuestaCR] = field(default_factory=list)

    PUNTOS_PRIMER_INTENTO:  int = 100
    PUNTOS_SEGUNDO_INTENTO: int = 50
    PUNTOS_CON_PISTA:       int = 20
    UMBRAL_PISTA:           int = 2

    @property
    def pregunta_actual(self) -> Optional[dict]:
        if self.indice_actual < len(self.productos):
            return self.productos[self.indice_actual]
        return None

    @property
    def terminado(self) -> bool:
        return self.indice_actual >= self.total_preguntas

    @property
    def progreso(self) -> str:
        return f"{self.indice_actual + 1} / {self.total_preguntas}"

    @property
    def porcentaje_aciertos(self) -> int:
        if not self.respuestas:
            return 0
        return round(sum(1 for r in self.respuestas if r.correcta) / len(self.respuestas) * 100)

    def verificar_respuesta(self, cat: str, sub: str, cod: str) -> bool:
        producto = self.pregunta_actual
        if producto is None:
            return False
        correcta = f"{cat}-{sub}-{cod}" == producto["codigo_completo"]
        if correcta:
            pts = (self.PUNTOS_CON_PISTA if self.pista_activa
                   else self.PUNTOS_PRIMER_INTENTO if self.intentos_actuales == 0
                   else self.PUNTOS_SEGUNDO_INTENTO)
            self.puntos += pts
            self.respuestas.append(RespuestaCR(
                producto_nombre=producto["nombre"],
                codigo_correcto=producto["codigo_completo"],
                codigo_respondido=f"{cat}-{sub}-{cod}",
                intentos=self.intentos_actuales + 1,
                pista_usada=self.pista_activa,
                correcta=True,
            ))
            self.indice_actual += 1
            self.intentos_actuales = 0
            self.pista_activa = False
        else:
            self.intentos_actuales += 1
            if self.intentos_actuales >= self.UMBRAL_PISTA:
                self.pista_activa = True
        return correcta

    def saltar_pregunta(self) -> None:
        producto = self.pregunta_actual
        if producto is None:
            return
        self.respuestas.append(RespuestaCR(
            producto_nombre=producto["nombre"],
            codigo_correcto=producto["codigo_completo"],
            codigo_respondido="—",
            intentos=self.intentos_actuales,
            pista_usada=self.pista_activa,
            correcta=False,
        ))
        self.indice_actual += 1
        self.intentos_actuales = 0
        self.pista_activa = False


def crear_partida_cr(productos_vistos: list[dict], cantidad: int) -> EstadoCodigoRoto:
    cantidad = min(cantidad, len(productos_vistos))
    return EstadoCodigoRoto(
        productos=random.sample(productos_vistos, cantidad),
        total_preguntas=cantidad,
    )


# ══════════════════════════════════════════════════════════════════════════════
# QUIZ DE OPCIONES  (nuevo juego)
# ══════════════════════════════════════════════════════════════════════════════

class TipoPreguntaQuiz(Enum):
    CATEGORIA    = auto()   # Muestra nombre de categoría → elegir código XX
    SUBCATEGORIA = auto()   # Muestra nombre de subcategoría → elegir XX-XXX
    PRODUCTO     = auto()   # Muestra nombre de producto → elegir XX-XXX-XXX


@dataclass
class PreguntaQuiz:
    tipo:            TipoPreguntaQuiz
    enunciado:       str        # Texto que se muestra arriba
    respuesta_correcta: str     # Código correcto (XX, XX-XXX o XX-XXX-XXX)
    opciones:        list[str]  # 4 opciones incluyendo la correcta (mezcladas)
    mnemotecnia:     str        # Se muestra al fallar


@dataclass
class RespuestaQuiz:
    enunciado:          str
    respuesta_correcta: str
    respuesta_dada:     str
    correcta:           bool


@dataclass
class EstadoQuiz:
    preguntas:       list[PreguntaQuiz]
    total_preguntas: int
    indice_actual:   int = 0
    aciertos:        int = 0
    errores:         int = 0
    respuestas:      list[RespuestaQuiz] = field(default_factory=list)

    @property
    def pregunta_actual(self) -> Optional[PreguntaQuiz]:
        if self.indice_actual < len(self.preguntas):
            return self.preguntas[self.indice_actual]
        return None

    @property
    def terminado(self) -> bool:
        return self.indice_actual >= self.total_preguntas

    @property
    def progreso(self) -> str:
        return f"{self.indice_actual + 1} / {self.total_preguntas}"

    @property
    def porcentaje(self) -> int:
        total = self.aciertos + self.errores
        return round(self.aciertos / total * 100) if total else 0

    def responder(self, opcion: str) -> bool:
        """Registra la respuesta y avanza. Retorna True si fue correcta."""
        pregunta = self.pregunta_actual
        if pregunta is None:
            return False
        correcta = opcion == pregunta.respuesta_correcta
        if correcta:
            self.aciertos += 1
        else:
            self.errores += 1
        self.respuestas.append(RespuestaQuiz(
            enunciado=pregunta.enunciado,
            respuesta_correcta=pregunta.respuesta_correcta,
            respuesta_dada=opcion,
            correcta=correcta,
        ))
        self.indice_actual += 1
        return correcta


def _generar_distractores(correcto: str, pool: list[str], n: int = 3) -> list[str]:
    """Elige n valores del pool que sean distintos al correcto."""
    candidatos = [x for x in pool if x != correcto]
    return random.sample(candidatos, min(n, len(candidatos)))


def crear_partida_quiz(datos: dict, cantidad: int, modo: str = "mix", num_opciones: int = 4) -> EstadoQuiz:
    """
    Genera preguntas filtradas por modo y con el número de opciones (dificultad) solicitado.
    modo: "categorias", "subcategorias", "productos", o "mix"
    num_opciones: 2, 4, 6 u 8.
    """
    cats   = datos["categorias"]    # [{codigo, nombre}, ...]
    subs   = datos["subcategorias"] # [{categoria_codigo, codigo, nombre}, ...]
    prods  = datos["productos"]     # lista enriquecida con categoria_nombre etc.

    preguntas: list[PreguntaQuiz] = []

    # ── Preguntas de CATEGORÍA ────────────────────────────────────────────────
    if modo in ("categorias", "mix"):
        codigos_cat = [c["codigo"] for c in cats]
        for cat in cats:
            distractores = _generar_distractores(cat["codigo"], codigos_cat, n=num_opciones-1)
            opciones = [cat["codigo"]] + distractores
            random.shuffle(opciones)
            preguntas.append(PreguntaQuiz(
                tipo=TipoPreguntaQuiz.CATEGORIA,
                enunciado=cat["nombre"],
                respuesta_correcta=cat["codigo"],
                opciones=opciones,
                mnemotecnia=f"Categoría {cat['codigo']}: {cat['nombre']}",
            ))

    # ── Preguntas de SUBCATEGORÍA ─────────────────────────────────────────────
    if modo in ("subcategorias", "mix"):
        codigos_sub_completos = [f"{s['categoria_codigo']}-{s['codigo']}" for s in subs]
        for sub in subs:
            correcto = f"{sub['categoria_codigo']}-{sub['codigo']}"
            distractores = _generar_distractores(correcto, codigos_sub_completos, n=num_opciones-1)
            opciones = [correcto] + distractores
            random.shuffle(opciones)
            preguntas.append(PreguntaQuiz(
                tipo=TipoPreguntaQuiz.SUBCATEGORIA,
                enunciado=sub["nombre"],
                respuesta_correcta=correcto,
                opciones=opciones,
                mnemotecnia=f"Subcategoría {correcto}: {sub['nombre']}",
            ))

    # ── Preguntas de PRODUCTO ─────────────────────────────────────────────────
    if modo in ("productos", "mix"):
        codigos_prod = [p["codigo_completo"] for p in prods]
        for prod in prods:
            distractores = _generar_distractores(prod["codigo_completo"], codigos_prod, n=num_opciones-1)
            if len(distractores) < (num_opciones - 1):
                continue   # no hay suficientes distractores
            opciones = [prod["codigo_completo"]] + distractores
            random.shuffle(opciones)
            preguntas.append(PreguntaQuiz(
                tipo=TipoPreguntaQuiz.PRODUCTO,
                enunciado=prod["nombre"],
                respuesta_correcta=prod["codigo_completo"],
                opciones=opciones,
                mnemotecnia=prod.get("mnemotecnia") or
                            f"Código completo: {prod['codigo_completo']}",
            ))

    # Mezclar y limitar a la cantidad solicitada
    random.shuffle(preguntas)
    seleccion = preguntas[:min(cantidad, len(preguntas))]

    return EstadoQuiz(preguntas=seleccion, total_preguntas=len(seleccion))


# ══════════════════════════════════════════════════════════════════════════════
# DESAFÍO CONTRARRELOJ
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class EstadoContrarreloj:
    preguntas:       list[PreguntaQuiz]
    segundos_restantes: int = 90
    indice_actual:   int = 0
    aciertos:        int = 0
    errores:         int = 0
    respuestas:      list[RespuestaQuiz] = field(default_factory=list)

    @property
    def pregunta_actual(self) -> Optional[PreguntaQuiz]:
        if self.indice_actual < len(self.preguntas):
            return self.preguntas[self.indice_actual]
        return None

    @property
    def terminado(self) -> bool:
        return self.segundos_restantes <= 0 or self.indice_actual >= len(self.preguntas)

    def responder(self, opcion: str) -> bool:
        pregunta = self.pregunta_actual
        if pregunta is None: return False
        correcta = (opcion == pregunta.respuesta_correcta)
        if correcta:
            self.aciertos += 1
        else:
            self.errores += 1
        self.respuestas.append(RespuestaQuiz(
            enunciado=pregunta.enunciado,
            respuesta_correcta=pregunta.respuesta_correcta,
            respuesta_dada=opcion,
            correcta=correcta
        ))
        self.indice_actual += 1
        return correcta


def crear_partida_contrarreloj(datos: dict, num_opciones: int = 4) -> EstadoContrarreloj:
    """
    Genera un pool grande de preguntas de categoría para el modo contrarreloj.
    """
    cats = datos["categorias"]
    codigos_cat = [c["codigo"] for c in cats]
    
    pool: list[PreguntaQuiz] = []
    # Generar varias veces el pool para tener suficientes preguntas si el usuario es muy rápido
    for _ in range(5):
        random.shuffle(cats)
        for cat in cats:
            distractores = _generar_distractores(cat["codigo"], codigos_cat, n=num_opciones-1)
            opciones = [cat["codigo"]] + distractores
            random.shuffle(opciones)
            pool.append(PreguntaQuiz(
                tipo=TipoPreguntaQuiz.CATEGORIA,
                enunciado=cat["nombre"],
                respuesta_correcta=cat["codigo"],
                opciones=opciones,
                mnemotecnia=f"Categoría {cat['codigo']}"
            ))
    
    return EstadoContrarreloj(preguntas=pool)


# ══════════════════════════════════════════════════════════════════════════════
# SISTEMA DE NIVELES — 5 tipos de ejercicio
# ══════════════════════════════════════════════════════════════════════════════

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class TipoEjercicio(Enum):
    CUATRO_OPCIONES   = auto()  # Nombre → elegir código entre 4
    COMPLETAR_CODIGO  = auto()  # 13-???-001 → escribir el segmento faltante
    IDENTIFICAR_INTRUSO = auto() # 4 códigos → cuál NO pertenece
    ESCRIBIR_SEGMENTO = auto()  # Nombre → escribir segmento con teclado numérico
    EMPAREJAR         = auto()  # 4 nombres ↔ 4 códigos (drag/tap matching)


# ── Segmento que se oculta en COMPLETAR_CODIGO ────────────────────────────────

class SegmentoOculto(Enum):
    CATEGORIA    = "XX"   # oculta el 13
    SUBCATEGORIA = "XXX"  # oculta el 010-100
    PRODUCTO     = "XXX2" # oculta el código del producto


# ── Pregunta individual ───────────────────────────────────────────────────────

@dataclass
class PreguntaNivel:
    tipo:              TipoEjercicio
    # Datos principales
    enunciado:         str            # texto que se muestra arriba
    respuesta_correcta: str           # código o segmento correcto
    opciones:          list[str]      # para tipos de opción múltiple
    mnemotecnia:       str            # se muestra al fallar
    # Solo para COMPLETAR_CODIGO
    codigo_con_hueco:  str = ""       # ej: "13-???-001"
    segmento_oculto:   str = ""       # "XX", "XXX" o "XXX2"
    # Solo para EMPAREJAR
    pares:             list[tuple[str,str]] = field(default_factory=list)
    # Solo para IDENTIFICAR_INTRUSO
    contexto_intruso:  str = ""       # "subcategoría 13-010" etc.


# ── Estado de un nivel ────────────────────────────────────────────────────────

@dataclass
class EstadoNivel:
    numero:        int
    preguntas:     list[PreguntaNivel]
    indice_actual: int = 0
    aciertos:      int = 0
    errores:       int = 0

    @property
    def total(self) -> int:
        return len(self.preguntas)

    @property
    def terminado(self) -> bool:
        return self.indice_actual >= self.total

    @property
    def pregunta_actual(self) -> Optional[PreguntaNivel]:
        if self.indice_actual < self.total:
            return self.preguntas[self.indice_actual]
        return None

    @property
    def progreso(self) -> str:
        return f"{self.indice_actual + 1} / {self.total}"

    @property
    def porcentaje(self) -> int:
        total = self.aciertos + self.errores
        return round(self.aciertos / total * 100) if total else 0

    @property
    def aprobado(self) -> bool:
        return self.aciertos >= 7  # 70% de 10

    def responder(self, correcta: bool) -> None:
        if correcta:
            self.aciertos += 1
        else:
            self.errores += 1
        self.indice_actual += 1


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE NIVELES
# ══════════════════════════════════════════════════════════════════════════════

# Subcategorías de Inflables en orden
SUBS_INFLABLES = [
    ("010", "Inflables de Playa"),
    ("020", "Inflables de Jardín"),
    ("030", "Inflables Deportivos"),
    ("040", "Inflables de Fiesta"),
    ("050", "Inflables Infantiles"),
    ("060", "Inflables de Camping"),
    ("070", "Piscinas Inflables"),
    ("080", "Arcos y Estructuras"),
    ("090", "Accesorios de Inflado"),
    ("100", "Inflables Publicitarios"),
]


def _config_zona1(nivel: int) -> dict:
    """
    Zona 1 (niveles 1-10): solo subcategorías.
    Retorna {subs_activas: [(cod, nom)], solo_subs: True}
    """
    # Niveles 1-5: introduce 2 subs nuevas por nivel
    # Niveles 6-10: repaso de todas
    if nivel <= 5:
        hasta = nivel * 2          # nivel 1 → 2 subs, nivel 5 → 10 subs
        subs  = SUBS_INFLABLES[:hasta]
    else:
        subs  = SUBS_INFLABLES     # todas
    return {"subs_activas": subs, "prods_activos": [], "solo_subs": True}


def _config_zona2(nivel: int, datos: dict) -> dict:
    """
    Zona 2 (niveles 11-20): productos + repaso subs.
    """
    todos_prods = datos["productos"]
    todas_subs  = SUBS_INFLABLES

    # Niveles 11-16: productos de 1-2 subcategorías específicas
    # Niveles 17-20: todos los productos
    mapa = {
        11: ["010"],
        12: ["020"],
        13: ["030", "040"],
        14: ["050", "060"],
        15: ["070", "080"],
        16: ["090", "100"],
    }

    if nivel in mapa:
        subs_nivel = mapa[nivel]
        prods = [p for p in todos_prods if p["subcategoria_codigo"] in subs_nivel]
    else:
        prods = todos_prods  # niveles 17-20

    return {
        "subs_activas":  todas_subs,
        "prods_activos": prods,
        "solo_subs":     False,
    }


# ══════════════════════════════════════════════════════════════════════════════
# GENERADORES DE EJERCICIOS
# ══════════════════════════════════════════════════════════════════════════════

def _distractores_sub(correcto: str, pool: list[tuple[str,str]],
                      n: int = 3) -> list[str]:
    """Elige n códigos de sub distintos al correcto."""
    candidatos = [f"13-{cod}" for cod, _ in pool if cod != correcto]
    return random.sample(candidatos, min(n, len(candidatos)))


def _distractores_prod(correcto: str, pool: list[dict],
                       n: int = 3) -> list[str]:
    """Elige n códigos completos de producto distintos al correcto."""
    candidatos = [p["codigo_completo"] for p in pool
                  if p["codigo_completo"] != correcto]
    return random.sample(candidatos, min(n, len(candidatos)))


def _gen_cuatro_opciones_sub(sub: tuple[str,str],
                              pool_subs: list[tuple[str,str]]) -> PreguntaNivel:
    cod, nom = sub
    correcto  = f"13-{cod}"
    opciones  = [correcto] + _distractores_sub(cod, pool_subs)
    random.shuffle(opciones)
    return PreguntaNivel(
        tipo=TipoEjercicio.CUATRO_OPCIONES,
        enunciado=nom,
        respuesta_correcta=correcto,
        opciones=opciones,
        mnemotecnia=f"Subcategoría {correcto}: {nom}",
    )


def _gen_cuatro_opciones_prod(prod: dict,
                               pool_prods: list[dict]) -> PreguntaNivel:
    correcto = prod["codigo_completo"]
    opciones = [correcto] + _distractores_prod(correcto, pool_prods)
    random.shuffle(opciones)
    return PreguntaNivel(
        tipo=TipoEjercicio.CUATRO_OPCIONES,
        enunciado=prod["nombre"],
        respuesta_correcta=correcto,
        opciones=opciones,
        mnemotecnia=prod.get("mnemotecnia") or correcto,
    )


def _gen_completar_sub(sub: tuple[str,str],
                       pool_subs: list[tuple[str,str]]) -> PreguntaNivel:
    """13-???  → escribir el código de la subcategoría."""
    cod, nom  = sub
    correcto  = cod          # el segmento a escribir (3 dígitos)
    opciones  = [cod] + [c for c, _ in random.sample(
        [(c, n) for c, n in pool_subs if c != cod],
        min(3, len(pool_subs) - 1)
    )]
    random.shuffle(opciones)
    return PreguntaNivel(
        tipo=TipoEjercicio.COMPLETAR_CODIGO,
        enunciado=nom,
        respuesta_correcta=correcto,
        opciones=opciones,
        mnemotecnia=f"El código es 13-{cod}",
        codigo_con_hueco="13-???",
        segmento_oculto="XXX",
    )


def _gen_completar_prod(prod: dict,
                        pool_prods: list[dict]) -> PreguntaNivel:
    """13-XXX-??? → escribir el código del producto."""
    partes    = prod["codigo_completo"].split("-")  # ["13","040","001"]
    correcto  = partes[2]
    prefijo   = f"{partes[0]}-{partes[1]}-???"
    # Distractores: otros códigos de producto (últimos 3 dígitos)
    otros = [p["codigo_completo"].split("-")[2] for p in pool_prods
             if p["codigo_completo"] != prod["codigo_completo"]]
    opciones = [correcto] + random.sample(otros, min(3, len(otros)))
    random.shuffle(opciones)
    return PreguntaNivel(
        tipo=TipoEjercicio.COMPLETAR_CODIGO,
        enunciado=prod["nombre"],
        respuesta_correcta=correcto,
        opciones=opciones,
        mnemotecnia=prod.get("mnemotecnia") or prod["codigo_completo"],
        codigo_con_hueco=prefijo,
        segmento_oculto="XXX2",
    )


def _gen_intruso_sub(pool_subs: list[tuple[str,str]]) -> PreguntaNivel:
    """
    Muestra 4 códigos: 3 de la categoría 13 y 1 inventado de otra categoría.
    El usuario identifica el que NO es de Inflables.
    """
    tres   = random.sample(pool_subs, min(3, len(pool_subs)))
    # Intruso: código de otra categoría (01-03)
    cat    = random.choice(["01", "02", "03"])
    sub_i  = f"{random.randint(10,99):03d}"
    intruso = f"{cat}-{sub_i}"
    opciones = [f"13-{cod}" for cod, _ in tres] + [intruso]
    random.shuffle(opciones)
    return PreguntaNivel(
        tipo=TipoEjercicio.IDENTIFICAR_INTRUSO,
        enunciado="¿Cuál de estos códigos NO pertenece a Inflables (13)?",
        respuesta_correcta=intruso,
        opciones=opciones,
        mnemotecnia="Los inflables siempre empiezan con 13-XXX",
        contexto_intruso="categoría 13",
    )


def _gen_intruso_prod(sub: tuple[str,str],
                      pool_prods: list[dict]) -> PreguntaNivel:
    """
    Muestra 4 códigos: 3 de la misma sub y 1 de otra sub.
    El usuario identifica el intruso.
    """
    cod_sub, nom_sub = sub
    de_esta = [p for p in pool_prods if p["subcategoria_codigo"] == cod_sub]
    de_otra = [p for p in pool_prods if p["subcategoria_codigo"] != cod_sub]

    if len(de_esta) < 3 or not de_otra:
        # Fallback a intruso de sub
        return _gen_intruso_sub(
            [(p["subcategoria_codigo"], "") for p in pool_prods])

    tres    = random.sample(de_esta, 3)
    intruso = random.choice(de_otra)
    opciones = [p["codigo_completo"] for p in tres] + [intruso["codigo_completo"]]
    random.shuffle(opciones)
    return PreguntaNivel(
        tipo=TipoEjercicio.IDENTIFICAR_INTRUSO,
        enunciado=f"¿Cuál NO pertenece a '{nom_sub}'?",
        respuesta_correcta=intruso["codigo_completo"],
        opciones=opciones,
        mnemotecnia=f"Los productos de {nom_sub} tienen el código 13-{cod_sub}-XXX",
        contexto_intruso=f"13-{cod_sub}",
    )


def _gen_escribir_sub(sub: tuple[str,str]) -> PreguntaNivel:
    """Nombre de sub → escribir el código de 3 dígitos con teclado numérico."""
    cod, nom = sub
    return PreguntaNivel(
        tipo=TipoEjercicio.ESCRIBIR_SEGMENTO,
        enunciado=nom,
        respuesta_correcta=cod,       # "010", "020", …
        opciones=[],
        mnemotecnia=f"El código es 13-{cod}",
        codigo_con_hueco="13-???",
        segmento_oculto="XXX",
    )


def _gen_escribir_prod(prod: dict) -> PreguntaNivel:
    """Nombre de producto → escribir el último segmento XXX."""
    partes   = prod["codigo_completo"].split("-")
    correcto = partes[2]
    return PreguntaNivel(
        tipo=TipoEjercicio.ESCRIBIR_SEGMENTO,
        enunciado=prod["nombre"],
        respuesta_correcta=correcto,
        opciones=[],
        mnemotecnia=prod.get("mnemotecnia") or prod["codigo_completo"],
        codigo_con_hueco=f"{partes[0]}-{partes[1]}-???",
        segmento_oculto="XXX2",
    )


def _gen_emparejar_subs(pool_subs: list[tuple[str,str]],
                         n: int = 4) -> PreguntaNivel:
    """4 pares nombre ↔ código de subcategoría."""
    seleccion = random.sample(pool_subs, min(n, len(pool_subs)))
    pares     = [(nom, f"13-{cod}") for cod, nom in seleccion]
    return PreguntaNivel(
        tipo=TipoEjercicio.EMPAREJAR,
        enunciado="Empareja cada subcategoría con su código",
        respuesta_correcta="",   # se valida par a par
        opciones=[],
        mnemotecnia="",
        pares=pares,
    )


def _gen_emparejar_prods(pool_prods: list[dict],
                          n: int = 4) -> PreguntaNivel:
    """4 pares nombre ↔ código completo de producto."""
    seleccion = random.sample(pool_prods, min(n, len(pool_prods)))
    pares     = [(p["nombre"], p["codigo_completo"]) for p in seleccion]
    return PreguntaNivel(
        tipo=TipoEjercicio.EMPAREJAR,
        enunciado="Empareja cada producto con su código",
        respuesta_correcta="",
        opciones=[],
        mnemotecnia="",
        pares=pares,
    )


# ══════════════════════════════════════════════════════════════════════════════
# GENERADOR PRINCIPAL DE NIVELES
# ══════════════════════════════════════════════════════════════════════════════

def generar_nivel(numero: int, datos: dict) -> EstadoNivel:
    """
    Genera las 10 preguntas de un nivel mezclando los 5 tipos de ejercicio.

    Reglas de repetición:
    - Un mismo concepto aparece máximo 2 veces en el nivel.
    - Las 2 apariciones siempre son de tipos diferentes.
    - El orden final es aleatorio (random.shuffle).

    datos = resultado de database.fetch_datos_inflables()
    """
    if numero <= 10:
        cfg = _config_zona1(numero)
    else:
        cfg = _config_zona2(numero, datos)

    subs_activas  = cfg["subs_activas"]    # [(cod, nom), ...]
    prods_activos = cfg["prods_activos"]   # [dict, ...]
    solo_subs     = cfg["solo_subs"]

    preguntas: list[PreguntaNivel] = []

    # ── Distribución de 10 preguntas ─────────────────────────────────────────
    # Emparejamiento: 1 ejercicio de 4 pares = "1 pregunta"
    # Resto: 9 preguntas individuales de tipos variados

    # 1. Emparejamiento (siempre 1)
    if solo_subs or not prods_activos:
        preguntas.append(_gen_emparejar_subs(subs_activas))
    else:
        if random.random() < 0.5 and len(prods_activos) >= 4:
            preguntas.append(_gen_emparejar_prods(prods_activos))
        else:
            preguntas.append(_gen_emparejar_subs(subs_activas))

    # Concepto tracker: {concepto: tipos_usados}
    usados: dict[str, list[TipoEjercicio]] = {}

    def puede_usar(concepto: str, tipo: TipoEjercicio) -> bool:
        usos = usados.get(concepto, [])
        return len(usos) < 2 and tipo not in usos

    def registrar(concepto: str, tipo: TipoEjercicio) -> None:
        usados.setdefault(concepto, []).append(tipo)

    # Pool de generadores disponibles según el nivel
    def gen_aleatorio() -> Optional[PreguntaNivel]:
        """Intenta generar una pregunta aleatoria respetando el límite de repetición."""
        # Tipos disponibles (sin emparejamiento — ya se añadió)
        tipos_posibles = [
            TipoEjercicio.CUATRO_OPCIONES,
            TipoEjercicio.COMPLETAR_CODIGO,
            TipoEjercicio.IDENTIFICAR_INTRUSO,
            TipoEjercicio.ESCRIBIR_SEGMENTO,
        ]

        # Elegir si la pregunta es de sub o de producto
        usar_prod = (not solo_subs and prods_activos and random.random() < 0.6)

        tipo = random.choice(tipos_posibles)

        if usar_prod:
            prod = random.choice(prods_activos)
            concepto = prod["codigo_completo"]
            if not puede_usar(concepto, tipo):
                return None
            registrar(concepto, tipo)
            if tipo == TipoEjercicio.CUATRO_OPCIONES:
                return _gen_cuatro_opciones_prod(prod, prods_activos)
            elif tipo == TipoEjercicio.COMPLETAR_CODIGO:
                return _gen_completar_prod(prod, prods_activos)
            elif tipo == TipoEjercicio.IDENTIFICAR_INTRUSO:
                sub = random.choice(subs_activas)
                return _gen_intruso_prod(sub, prods_activos)
            else:  # ESCRIBIR_SEGMENTO
                return _gen_escribir_prod(prod)
        else:
            sub = random.choice(subs_activas)
            concepto = sub[0]
            if not puede_usar(concepto, tipo):
                return None
            registrar(concepto, tipo)
            if tipo == TipoEjercicio.CUATRO_OPCIONES:
                return _gen_cuatro_opciones_sub(sub, subs_activas)
            elif tipo == TipoEjercicio.COMPLETAR_CODIGO:
                return _gen_completar_sub(sub, subs_activas)
            elif tipo == TipoEjercicio.IDENTIFICAR_INTRUSO:
                return _gen_intruso_sub(subs_activas)
            else:  # ESCRIBIR_SEGMENTO
                return _gen_escribir_sub(sub)

    # Generar las 9 preguntas restantes
    intentos = 0
    while len(preguntas) < 10 and intentos < 200:
        intentos += 1
        p = gen_aleatorio()
        if p is not None:
            preguntas.append(p)

    # Si no se completaron 10 (pool muy pequeño), rellenar con 4 opciones simples
    while len(preguntas) < 10:
        sub = random.choice(subs_activas)
        preguntas.append(_gen_cuatro_opciones_sub(sub, subs_activas))

    # Barajar manteniendo el emparejamiento primero si el nivel es 1 o 11
    # (primeros niveles de cada zona: el emparejamiento introduce el concepto)
    if numero in (1, 11):
        resto = preguntas[1:]
        random.shuffle(resto)
        preguntas = [preguntas[0]] + resto
    else:
        random.shuffle(preguntas)

    return EstadoNivel(numero=numero, preguntas=preguntas)