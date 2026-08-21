import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import {
  updateEstatusEnLote,
  updateProductoCamposEnLote,
  type CamposProducto,
} from "@/lib/api";
import { useCatalogo } from "@/lib/catalogo";
import {
  leerClasificacionesDeExcel,
  type LecturaClasificacion,
  type ProblemaExcel,
} from "@/lib/excel";
import type { Producto } from "@/lib/types";
import ZonaDeArchivo from "@/components/ZonaDeArchivo";
import { colorEmpresa, suave } from "@/theme/marca";

const BOTON_PRIMARIO =
  "rounded-[10px] bg-marca-negro px-[22px] py-2.5 text-[.9rem] font-semibold text-white " +
  "hover:bg-black disabled:opacity-50 disabled:cursor-not-allowed";

const BOTON_SECUNDARIO =
  "rounded-[10px] border border-marca-boton-borde bg-white px-[18px] py-2.5 text-[.9rem] " +
  "font-semibold text-marca-negro hover:bg-marca-boton disabled:opacity-50 " +
  "disabled:cursor-not-allowed";

const SELECT =
  "rounded-[10px] border border-marca-borde bg-white px-3 py-2 text-sm font-medium " +
  "text-marca-negro focus:border-marca-negro focus:outline-none disabled:opacity-50";

const CAMPO =
  "rounded-[10px] border border-marca-borde bg-white px-3 py-2 text-sm text-marca-negro " +
  "placeholder:text-marca-tenue focus:border-marca-negro focus:outline-none";

// Botones de acción masiva dentro de una sección de discrepancias: mismo
// ámbar que el resto del aviso, para que se lean como parte del mismo bloque.
const BOTON_MINI_AMBAR =
  "rounded-full border border-[#92400e] bg-white px-3 py-1 text-xs font-semibold " +
  "text-[#92400e] hover:bg-[#fef3c7] disabled:opacity-40 disabled:cursor-not-allowed";

const BOTON_MINI_AMBAR_LLENO =
  "rounded-full bg-[#92400e] px-3 py-1 text-xs font-semibold text-white " +
  "hover:bg-[#7c3609] disabled:opacity-40 disabled:cursor-not-allowed";

// Bordeado simple para la fila que trajo la búsqueda por código: no cambia el
// layout (outline no ocupa espacio) y se ve igual sobre cualquier fondo de
// fila (blanco, ámbar de aviso, rojo de "dejan de ser infaltables").
const RESALTADO_FILA = "relative z-10 outline outline-2 outline-offset-[-2px] outline-[#1d1d1b]";

const numero = (n: number) => n.toLocaleString("es-VE");
const codigoDe = (p: Producto) => p.codigo_completo ?? p.codigo;

type Direccion = "asc" | "desc";

function comparar(a: string | number, b: string | number, direccion: Direccion): number {
  const signo = direccion === "asc" ? 1 : -1;
  if (typeof a === "number" && typeof b === "number") return signo * (a - b);
  return signo * String(a).localeCompare(String(b), "es", { numeric: true, sensitivity: "base" });
}

/** Encabezado de columna ordenable, reutilizado por todas las tablas de esta
 * pantalla (cada una con su propio juego de columnas). */
function EncabezadoOrdenable<T extends string>({
  columna,
  etiqueta,
  activa,
  direccion,
  onClick,
}: {
  columna: T;
  etiqueta: string;
  activa: T;
  direccion: Direccion;
  onClick: (columna: T) => void;
}) {
  const esActiva = columna === activa;
  return (
    <th className="p-0 text-left">
      <button
        type="button"
        role="columnheader"
        aria-sort={esActiva ? (direccion === "asc" ? "ascending" : "descending") : "none"}
        className="versalita flex w-full cursor-pointer items-center gap-1 px-4 py-2 text-left hover:text-marca-negro"
        onClick={() => onClick(columna)}
      >
        {etiqueta}
        <span aria-hidden className={esActiva ? "text-marca-negro" : "text-marca-tenue"}>
          {esActiva ? (direccion === "asc" ? "▲" : "▼") : "▲"}
        </span>
      </button>
    </th>
  );
}

/** Normaliza para comparar descripciones sin castigar tildes ni espacios. */
function normalizarTexto(t: string): string {
  return t
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

type Campo = "nombre" | "categoria" | "subcategoria";

const ETIQUETA_CAMPO: Record<Campo, string> = {
  nombre: "Nombre",
  categoria: "Categoría",
  subcategoria: "Subcategoría",
};

type Discrepancia = {
  campo: Campo;
  base: string;
  archivo: string;
  /** false cuando el valor del archivo (categoría/subcategoría) no se pudo
   * ubicar en el catálogo de la casa, así que no hay código que guardar. */
  archivoAplicable: boolean;
};

/** id del producto → qué campos, de los que difieren, quedaron en "usar archivo". */
type Elecciones = Map<string, Partial<Record<Campo, boolean>>>;

/** Un problema, con los datos que traía esa fila del archivo — para códigos
 * que no existen en la base no hay con qué comparar, pero sí hay con qué dar
 * contexto: qué decía el Excel para ese producto. */
type ProblemaConDatos = ProblemaExcel & {
  estatusArchivo?: string;
  descripcionArchivo?: string;
  categoriaArchivo?: string;
  subcategoriaArchivo?: string;
};

type Asignado = {
  id: string;
  codigo: string;
  nombre: string;
  actual: string;
  nuevo: string;
  /** Categoría actual del producto en la base: la subcategoría solo es única
   * dentro de su categoría (el mismo código "16" es "Carretillas" bajo una
   * categoría y "Limpieza de autos" bajo otra), así que hace falta este dato
   * para resolver o mostrar bien su subcategoría. */
  categoriaCodigoBase: string;
  discrepancias: Discrepancia[];
};

type Fase =
  | { tipo: "inactivo" }
  | { tipo: "leyendo" }
  | { tipo: "confirmando" }
  | { tipo: "aplicando"; hechas: number; total: number }
  | { tipo: "resultado"; aplicadas: number; fallidas: ProblemaExcel[] }
  | { tipo: "error"; mensaje: string };

export default function ActualizarClasificacion() {
  const {
    sede,
    productos,
    estatus,
    categorias,
    subcategorias,
    infaltables,
    estado,
    aplicarCambios,
  } = useCatalogo();

  const [lectura, setLectura] = useState<LecturaClasificacion | null>(null);
  const [nombreArchivo, setNombreArchivo] = useState("");
  const [mismoParaTodos, setMismoParaTodos] = useState(false);
  const [estatusUnico, setEstatusUnico] = useState("");
  const [estatusReemplazo, setEstatusReemplazo] = useState("");
  const [fase, setFase] = useState<Fase>({ tipo: "inactivo" });
  const [elecciones, setElecciones] = useState<Elecciones>(new Map());

  const acento = colorEmpresa(sede);
  const codigosInfaltables = useMemo(
    () => estatus.filter((e) => e.es_infaltable).map((e) => e.codigo).sort(),
    [estatus]
  );
  const codigosNoInfaltables = useMemo(
    () => estatus.filter((e) => !e.es_infaltable).map((e) => e.codigo).sort(),
    [estatus]
  );

  // Nombre de categoría por código (para comparar contra el archivo) y el
  // cruce inverso (para resolver el nombre del archivo a un código, si el
  // usuario elige "usar archivo"). La categoría sí es única por casa.
  const categoriaNombrePorCodigo = useMemo(
    () => new Map(categorias.map((c) => [c.codigo, c.nombre])),
    [categorias]
  );
  const categoriaCodigoPorNombre = useMemo(
    () => new Map(categorias.map((c) => [normalizarTexto(c.nombre), c.codigo])),
    [categorias]
  );

  // La subcategoría, en cambio, NO es única por casa: el mismo código "16" es
  // "Carretillas" bajo la categoría "10" y "Limpieza de autos" bajo la "37".
  // Por eso ambos mapas van anidados por categoria_codigo — buscar solo por
  // código de subcategoría mezclaba nombres de categorías distintas.
  const subcategoriaNombrePorCategoriaYCodigo = useMemo(() => {
    const mapa = new Map<string, Map<string, string>>();
    for (const s of subcategorias) {
      if (!mapa.has(s.categoria_codigo)) mapa.set(s.categoria_codigo, new Map());
      mapa.get(s.categoria_codigo)!.set(s.codigo, s.nombre);
    }
    return mapa;
  }, [subcategorias]);
  const subcategoriaCodigoPorCategoriaYNombre = useMemo(() => {
    const mapa = new Map<string, Map<string, string>>();
    for (const s of subcategorias) {
      if (!mapa.has(s.categoria_codigo)) mapa.set(s.categoria_codigo, new Map());
      mapa.get(s.categoria_codigo)!.set(normalizarTexto(s.nombre), s.codigo);
    }
    return mapa;
  }, [subcategorias]);

  function alternarEleccion(id: string, campo: Campo, usarArchivo: boolean) {
    setElecciones((prev) => {
      const siguiente = new Map(prev);
      siguiente.set(id, { ...siguiente.get(id), [campo]: usarArchivo });
      return siguiente;
    });
  }

  /** Misma elección, pero para todos los productos de una sección de un solo golpe. */
  function alternarTodos(campo: Campo, ids: string[], usarArchivo: boolean) {
    if (ids.length === 0) return;
    setElecciones((prev) => {
      const siguiente = new Map(prev);
      for (const id of ids) {
        siguiente.set(id, { ...siguiente.get(id), [campo]: usarArchivo });
      }
      return siguiente;
    });
  }

  async function alElegirArchivo(archivo: File) {
    setFase({ tipo: "leyendo" });
    setNombreArchivo(archivo.name);
    setElecciones(new Map());
    try {
      const leida = await leerClasificacionesDeExcel(archivo);
      setLectura(leida);
      // Si el archivo no trae la columna, no hay otra forma de saber qué
      // aplicar: se enciende el interruptor solo.
      setMismoParaTodos(!leida.traeColumnaEstatus);
      setFase({ tipo: "inactivo" });
    } catch (err) {
      setLectura(null);
      setFase({ tipo: "error", mensaje: (err as Error).message });
    }
  }

  /**
   * El cálculo completo: qué recibe clasificación y qué la deja de tener.
   *
   * La premisa es de reemplazo, no de suma: el archivo define el conjunto
   * completo de infaltables de la casa, así que todo producto que hoy sea
   * infaltable y no venga en el archivo pasa al estatus de reemplazo.
   */
  const revision = useMemo(() => {
    if (!lectura) return null;

    // Dos situaciones en las que ninguna fila tiene destino todavía, y que no
    // son errores del archivo sino configuración pendiente: hay que decirlo en
    // una frase, no llenar la pantalla de cientos de "errores" idénticos.
    const sinColumna = !lectura.traeColumnaEstatus;
    const faltaElegir =
      (mismoParaTodos && !estatusUnico) || (sinColumna && !mismoParaTodos);
    const motivoFalta = sinColumna && !mismoParaTodos ? "sinColumna" : "sinEstatus";

    const porCodigo = new Map(productos.map((p) => [codigoDe(p), p]));
    const codigosDelArchivo = new Set<string>();
    const asignados: Asignado[] = [];
    const sinCambio: Asignado[] = [];
    const problemas: ProblemaConDatos[] = [...lectura.problemas];
    // Lo que traía la fila del archivo, para dar contexto en los problemas
    // aunque no haya producto en la base con qué compararlo.
    const datosDeFila = (f: (typeof lectura.filas)[number]) => ({
      estatusArchivo: f.estatus || undefined,
      descripcionArchivo: f.descripcion || undefined,
      categoriaArchivo: f.categoria || undefined,
      subcategoriaArchivo: f.subcategoria || undefined,
    });

    for (const f of lectura.filas) {
      const destino = mismoParaTodos ? estatusUnico : f.estatus;

      if (!destino) {
        if (!faltaElegir) {
          problemas.push({
            fila: f.fila,
            codigo: f.codigo,
            motivo: "Sin clasificación en el archivo",
            ...datosDeFila(f),
          });
        }
        continue;
      }
      if (!estatus.some((e) => e.codigo === destino)) {
        problemas.push({
          fila: f.fila,
          codigo: f.codigo,
          motivo: `El estatus "${destino}" no existe en el catálogo`,
          ...datosDeFila(f),
        });
        continue;
      }

      const producto = porCodigo.get(f.codigo);
      if (!producto) {
        problemas.push({
          fila: f.fila,
          codigo: f.codigo,
          motivo: `No existe en ${sede}`,
          ...datosDeFila(f),
        });
        continue;
      }

      codigosDelArchivo.add(f.codigo);

      const discrepancias: Discrepancia[] = [];

      if (f.descripcion && normalizarTexto(f.descripcion) !== normalizarTexto(producto.nombre)) {
        discrepancias.push({
          campo: "nombre",
          base: producto.nombre,
          archivo: f.descripcion,
          archivoAplicable: true,
        });
      }

      if (lectura.traeColumnaCategoria && f.categoria) {
        const nombreBase = categoriaNombrePorCodigo.get(producto.categoria_codigo) ?? "";
        if (normalizarTexto(f.categoria) !== normalizarTexto(nombreBase)) {
          discrepancias.push({
            campo: "categoria",
            base: nombreBase || "(sin categoría)",
            archivo: f.categoria,
            archivoAplicable: categoriaCodigoPorNombre.has(normalizarTexto(f.categoria)),
          });
        }
      }

      if (lectura.traeColumnaSubcategoria && f.subcategoria) {
        const nombreBase =
          subcategoriaNombrePorCategoriaYCodigo
            .get(producto.categoria_codigo)
            ?.get(producto.subcategoria_codigo) ?? "";
        if (normalizarTexto(f.subcategoria) !== normalizarTexto(nombreBase)) {
          discrepancias.push({
            campo: "subcategoria",
            base: nombreBase || "(sin subcategoría)",
            archivo: f.subcategoria,
            archivoAplicable:
              subcategoriaCodigoPorCategoriaYNombre
                .get(producto.categoria_codigo)
                ?.has(normalizarTexto(f.subcategoria)) ?? false,
          });
        }
      }

      const fila: Asignado = {
        id: producto.id,
        codigo: f.codigo,
        nombre: producto.nombre,
        actual: producto.estatus,
        nuevo: destino,
        categoriaCodigoBase: producto.categoria_codigo,
        discrepancias,
      };

      if (producto.estatus === destino) sinCambio.push(fila);
      else asignados.push(fila);
    }

    // Los que hoy son infaltables y no vienen en el archivo: cambian al
    // estatus de reemplazo. No se borra nada, solo cambia esta columna.
    const pierden: Asignado[] = estatusReemplazo
      ? productos
          .filter(
            (p) =>
              infaltables.has(p.estatus) &&
              !codigosDelArchivo.has(codigoDe(p)) &&
              p.estatus !== estatusReemplazo
          )
          .map((p) => ({
            id: p.id,
            codigo: codigoDe(p),
            nombre: p.nombre,
            actual: p.estatus,
            nuevo: estatusReemplazo,
            categoriaCodigoBase: p.categoria_codigo,
            discrepancias: [],
          }))
      : [];

    const avisos = asignados.filter((a) => a.discrepancias.length > 0);

    return {
      asignados,
      sinCambio,
      pierden,
      problemas,
      avisos,
      faltaElegir,
      motivoFalta,
      filasDelArchivo: lectura.filas.length,
    };
  }, [
    lectura,
    productos,
    estatus,
    infaltables,
    mismoParaTodos,
    estatusUnico,
    estatusReemplazo,
    sede,
    categoriaNombrePorCodigo,
    subcategoriaNombrePorCategoriaYCodigo,
    categoriaCodigoPorNombre,
    subcategoriaCodigoPorCategoriaYNombre,
  ]);

  const listoParaAplicar =
    revision !== null &&
    estatusReemplazo !== "" &&
    (!mismoParaTodos || estatusUnico !== "") &&
    revision.asignados.length + revision.pierden.length > 0 &&
    estado === "listo";

  // Cuántas sobrescrituras de nombre/categoría/subcategoría quedaron listas
  // para aplicarse (el usuario eligió "archivo" y, si aplica, se pudo
  // resolver el código): se usa tanto para el resumen de confirmación como
  // para armar los items a guardar.
  const sobrescrituras = useMemo(() => {
    if (!revision) return [];
    const items: { id: string; codigo: string; campos: CamposProducto }[] = [];
    for (const a of revision.asignados) {
      const elegido = elecciones.get(a.id);
      if (!elegido) continue;
      const campos: CamposProducto = {};
      for (const d of a.discrepancias) {
        if (!elegido[d.campo] || !d.archivoAplicable) continue;
        if (d.campo === "nombre") campos.nombre = d.archivo;
        else if (d.campo === "categoria") {
          const codigo = categoriaCodigoPorNombre.get(normalizarTexto(d.archivo));
          if (codigo) campos.categoria_codigo = codigo;
        } else if (d.campo === "subcategoria") {
          // Se resuelve dentro de la categoría ACTUAL del producto, no de la
          // que traiga el archivo: si además se está cambiando la categoría,
          // ese es un campo aparte que el usuario elige por su cuenta.
          const codigo = subcategoriaCodigoPorCategoriaYNombre
            .get(a.categoriaCodigoBase)
            ?.get(normalizarTexto(d.archivo));
          if (codigo) campos.subcategoria_codigo = codigo;
        }
      }
      if (Object.keys(campos).length > 0) items.push({ id: a.id, codigo: a.codigo, campos });
    }
    return items;
  }, [revision, elecciones, categoriaCodigoPorNombre, subcategoriaCodigoPorCategoriaYNombre]);

  async function aplicar() {
    if (!revision) return;
    const items = [...revision.asignados, ...revision.pierden].map((a) => ({
      id: a.id,
      codigo: a.codigo,
      estatus: a.nuevo,
    }));
    const total = items.length + sobrescrituras.length;

    setFase({ tipo: "aplicando", hechas: 0, total });
    const { aplicadas: aplicadasEstatus, fallidas: fallidasEstatus } =
      await updateEstatusEnLote(items, (hechas) =>
        setFase({ tipo: "aplicando", hechas, total })
      );

    let aplicadasCampos = 0;
    let fallidasCampos: { id: string; codigo: string; motivo: string }[] = [];
    if (sobrescrituras.length > 0) {
      const resultado = await updateProductoCamposEnLote(
        sobrescrituras,
        (hechas) =>
          setFase({ tipo: "aplicando", hechas: items.length + hechas, total })
      );
      aplicadasCampos = resultado.aplicadas;
      fallidasCampos = resultado.fallidas;
    }

    const fallidosEstatusIds = new Set(fallidasEstatus.map((f) => f.id));
    const fallidosCamposIds = new Set(fallidasCampos.map((f) => f.id));

    // Estatus y campos se guardan por separado y pueden fallar por separado:
    // si el estatus de un producto no se pudo escribir pero su nombre/categoría
    // sí, la caché local igual tiene que reflejar lo que de verdad se guardó
    // (y viceversa) — de ahí que se combinen por id en vez de descartar la fila
    // completa cuando una de las dos partes falla.
    const cambiosPorId = new Map<
      string,
      { id: string } & Partial<CamposProducto> & { estatus?: string }
    >();
    for (const i of items) {
      if (fallidosEstatusIds.has(i.id)) continue;
      cambiosPorId.set(i.id, { id: i.id, estatus: i.estatus });
    }
    for (const s of sobrescrituras) {
      if (fallidosCamposIds.has(s.id)) continue;
      cambiosPorId.set(s.id, { ...cambiosPorId.get(s.id), id: s.id, ...s.campos });
    }

    aplicarCambios([...cambiosPorId.values()]);

    setFase({
      tipo: "resultado",
      aplicadas: aplicadasEstatus + aplicadasCampos,
      fallidas: [...fallidasEstatus, ...fallidasCampos].map((f) => ({
        fila: 0,
        codigo: f.codigo,
        motivo: f.motivo,
      })),
    });
    setLectura(null);
    setNombreArchivo("");
    setElecciones(new Map());
  }

  return (
    <div className="flex flex-col gap-5">
      {/* Paso 1: el archivo */}
      <section className="animar-entrada rounded-xl border border-marca-borde bg-white p-5">
        <h2 className="text-sm font-semibold text-marca-negro">
          1 · Archivo de clasificación
        </h2>
        <p className="mt-1 mb-4 text-sm text-marca-texto">
          Un Excel con la columna <b>Código</b>. La columna de clasificación
          (<b>BDF</b> o <b>Estatus</b>) es opcional.
        </p>

        <ZonaDeArchivo
          acento={acento}
          archivo={nombreArchivo || null}
          detalle={
            lectura
              ? `${numero(lectura.filas.length)} filas · ${
                  lectura.traeColumnaEstatus
                    ? "trae columna de clasificación"
                    : "sin columna de clasificación"
                }`
              : null
          }
          ocupado={fase.tipo === "leyendo"}
          onArchivo={alElegirArchivo}
        />

        {fase.tipo === "error" && (
          <p className="mt-3 rounded-[10px] border border-[#fecaca] bg-[#fef2f2] px-4 py-3 text-sm text-[#b91c1c]">
            {fase.mensaje}
          </p>
        )}
      </section>

      {lectura && (
        <>
          {/* Paso 2: qué se aplica */}
          <section
            className="animar-entrada rounded-xl border border-marca-borde bg-white p-5"
            style={{ animationDelay: "60ms" }}
          >
            <h2 className="text-sm font-semibold text-marca-negro">
              2 · Qué clasificación se aplica
            </h2>

            <label className="mt-3 flex cursor-pointer items-start gap-3">
              <input
                type="checkbox"
                className="mt-0.5 h-4 w-4 accent-[#1d1d1b]"
                checked={mismoParaTodos}
                onChange={(e) => setMismoParaTodos(e.target.checked)}
              />
              <span className="text-sm text-marca-negro">
                Todos los productos del archivo llevan la misma clasificación
                {!lectura.traeColumnaEstatus && (
                  <span className="text-marca-texto">
                    {" "}
                    — el archivo no trae columna, así que hace falta
                  </span>
                )}
              </span>
            </label>

            <div className="mt-3 flex flex-wrap items-end gap-5">
              <label className="flex flex-col gap-1.5">
                <span className="versalita">Clasificación del archivo</span>
                <select
                  className={SELECT}
                  value={estatusUnico}
                  disabled={!mismoParaTodos}
                  onChange={(e) => setEstatusUnico(e.target.value)}
                >
                  <option value="">Elegir…</option>
                  {codigosInfaltables.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </label>

              <label className="flex flex-col gap-1.5">
                <span className="versalita">Los demás infaltables pasan a</span>
                <select
                  className={SELECT}
                  value={estatusReemplazo}
                  onChange={(e) => setEstatusReemplazo(e.target.value)}
                >
                  <option value="">Elegir…</option>
                  {codigosNoInfaltables.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <p className="mt-3 text-sm text-marca-texto">
              El archivo define la lista completa de infaltables de {sede}: todo
              producto que hoy sea infaltable y no aparezca en él cambia al
              estatus elegido a la derecha. No se borra ningún producto.
            </p>
          </section>

          {revision?.faltaElegir && (
            <p className="rounded-[10px] border border-marca-borde bg-marca-fondo px-4 py-3 text-sm text-marca-texto">
              {revision.motivoFalta === "sinColumna"
                ? `Este archivo no trae columna de clasificación, así que no hay de dónde sacar el estatus de sus ${numero(
                    revision.filasDelArchivo
                  )} filas. Marca la casilla de arriba y elige cuál aplicarles a todas.`
                : `Elige arriba la clasificación que llevarán las ${numero(
                    revision.filasDelArchivo
                  )} filas del archivo para ver la revisión.`}
            </p>
          )}

          {/* Paso 3: revisión */}
          {revision && !revision.faltaElegir && (
            <Revision
              key={nombreArchivo}
              revision={revision}
              sede={sede}
              acento={acento}
              estatusReemplazo={estatusReemplazo}
              elecciones={elecciones}
              onAlternar={alternarEleccion}
              onAlternarTodos={alternarTodos}
            />
          )}

          <div className="flex flex-wrap items-center justify-end gap-3">
            {fase.tipo === "aplicando" && (
              <span className="text-sm tabular-nums text-marca-texto">
                Guardando {numero(fase.hechas)} de {numero(fase.total)}…
              </span>
            )}
            <button
              className={BOTON_PRIMARIO}
              disabled={!listoParaAplicar || fase.tipo === "aplicando"}
              onClick={() => setFase({ tipo: "confirmando" })}
            >
              {fase.tipo === "aplicando"
                ? "Guardando…"
                : `Aplicar a ${numero(
                    (revision?.asignados.length ?? 0) +
                      (revision?.pierden.length ?? 0)
                  )} productos`}
            </button>
          </div>
        </>
      )}

      {fase.tipo === "resultado" && (
        <section className="animar-entrada rounded-xl border border-marca-borde bg-white p-5">
          <h2 className="text-sm font-semibold text-marca-negro">
            Se actualizaron {numero(fase.aplicadas)} productos
          </h2>
          {fase.fallidas.length > 0 && (
            <>
              <p className="mt-2 text-sm text-[#b91c1c]">
                {numero(fase.fallidas.length)} no se pudieron guardar:
              </p>
              <ListaProblemas problemas={fase.fallidas} sinFila />
            </>
          )}
        </section>
      )}

      {fase.tipo === "confirmando" && revision && (
        <ModalConfirmacion
          sede={sede}
          acento={acento}
          revision={revision}
          sobrescrituras={sobrescrituras}
          estatusReemplazo={estatusReemplazo}
          onCancelar={() => setFase({ tipo: "inactivo" })}
          onConfirmar={aplicar}
        />
      )}
    </div>
  );
}

function ModalConfirmacion({
  sede,
  acento,
  revision,
  sobrescrituras,
  estatusReemplazo,
  onCancelar,
  onConfirmar,
}: {
  sede: string;
  acento: string;
  revision: {
    asignados: Asignado[];
    sinCambio: Asignado[];
    pierden: Asignado[];
    problemas: ProblemaExcel[];
  };
  sobrescrituras: { id: string; codigo: string; campos: CamposProducto }[];
  estatusReemplazo: string;
  onCancelar: () => void;
  onConfirmar: () => void;
}) {
  const total = revision.asignados.length + revision.pierden.length;

  // Igual que en CargarExcel: por portal al <body>, para no quedar recortado
  // dentro de una tarjeta con `.animar-entrada` (transform crea un bloque
  // contenedor que rompe el `fixed` del overlay).
  return createPortal(
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/30 p-6">
      <section className="animar-entrada mt-10 w-full max-w-lg rounded-xl border border-marca-borde bg-white p-6">
        <h2 className="text-lg font-semibold text-marca-negro">
          Confirmar antes de aplicar
        </h2>
        <p className="mt-1 text-sm text-marca-texto">
          Se va a escribir en la base de{" "}
          <span className="inline-flex items-center gap-1.5 font-medium text-marca-negro">
            <span
              aria-hidden
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: acento }}
            />
            {sede}
          </span>
          . Esto no se puede deshacer desde aquí.
        </p>

        <div className="mt-4 grid grid-cols-2 gap-3">
          <Cifra valor={revision.asignados.length} etiqueta="Reciben clasificación" />
          <Cifra
            valor={revision.pierden.length}
            etiqueta={
              estatusReemplazo
                ? `Dejan de ser infaltables → ${estatusReemplazo}`
                : "Dejan de ser infaltables"
            }
            alerta
          />
        </div>

        {sobrescrituras.length > 0 && (
          <p className="mt-3 rounded-[10px] border border-[#fde68a] bg-[#fffbeb] px-4 py-3 text-sm text-[#92400e]">
            Además, {numero(sobrescrituras.length)}{" "}
            {sobrescrituras.length === 1 ? "producto" : "productos"} recibirán
            el nombre, categoría y/o subcategoría del archivo, según elegiste
            en la revisión.
          </p>
        )}

        {revision.problemas.length > 0 && (
          <p className="mt-3 text-sm text-marca-texto">
            {numero(revision.problemas.length)}{" "}
            {revision.problemas.length === 1 ? "fila" : "filas"} del archivo
            no se van a aplicar por tener algún problema — revísalas abajo si
            cierras este cuadro.
          </p>
        )}

        <div className="mt-6 flex flex-wrap justify-end gap-2">
          <button className={BOTON_SECUNDARIO} onClick={onCancelar}>
            Volver a revisar
          </button>
          <button className={BOTON_PRIMARIO} onClick={onConfirmar}>
            Confirmar y aplicar a {numero(total)} productos
          </button>
        </div>
      </section>
    </div>,
    document.body
  );
}

/** Una fila de discrepancia para UNA sección (una por campo): el producto,
 * su cambio de estatus (para dar contexto) y el valor base/archivo de ese
 * campo en particular. */
type FilaCampo = {
  id: string;
  codigo: string;
  producto: string;
  actual: string;
  nuevo: string;
  base: string;
  archivo: string;
  archivoAplicable: boolean;
};

function filasPorCampo(avisos: Asignado[], campo: Campo): FilaCampo[] {
  const filas: FilaCampo[] = [];
  for (const a of avisos) {
    const d = a.discrepancias.find((x) => x.campo === campo);
    if (!d) continue;
    filas.push({
      id: a.id,
      codigo: a.codigo,
      producto: a.nombre,
      actual: a.actual,
      nuevo: a.nuevo,
      base: d.base,
      archivo: d.archivo,
      archivoAplicable: d.archivoAplicable,
    });
  }
  return filas;
}

function Revision({
  revision,
  sede,
  acento,
  estatusReemplazo,
  elecciones,
  onAlternar,
  onAlternarTodos,
}: {
  revision: {
    asignados: Asignado[];
    sinCambio: Asignado[];
    pierden: Asignado[];
    problemas: ProblemaConDatos[];
    avisos: Asignado[];
  };
  sede: string;
  acento: string;
  estatusReemplazo: string;
  elecciones: Elecciones;
  onAlternar: (id: string, campo: Campo, usarArchivo: boolean) => void;
  onAlternarTodos: (campo: Campo, ids: string[], usarArchivo: boolean) => void;
}) {
  const { asignados, sinCambio, pierden, problemas, avisos } = revision;
  const sinDiferencias = asignados.filter((a) => a.discrepancias.length === 0);
  const filasCategoria = filasPorCampo(avisos, "categoria");
  const filasSubcategoria = filasPorCampo(avisos, "subcategoria");
  const filasNombre = filasPorCampo(avisos, "nombre");

  const [busqueda, setBusqueda] = useState("");
  const [resaltado, setResaltado] = useState<string | null>(null);
  const [busquedaError, setBusquedaError] = useState<string | null>(null);

  // Todo código visible en alguna tabla de esta revisión — "ya estaban
  // iguales" no se lista en ninguna tabla, así que buscar uno de esos no
  // encuentra dónde saltar.
  const codigosVisibles = useMemo(() => {
    const set = new Set<string>();
    for (const f of filasCategoria) set.add(f.codigo);
    for (const f of filasSubcategoria) set.add(f.codigo);
    for (const f of filasNombre) set.add(f.codigo);
    for (const f of sinDiferencias) set.add(f.codigo);
    for (const f of pierden) set.add(f.codigo);
    for (const p of problemas) set.add(p.codigo);
    return set;
  }, [filasCategoria, filasSubcategoria, filasNombre, sinDiferencias, pierden, problemas]);

  function buscar(e: React.FormEvent) {
    e.preventDefault();
    const codigo = busqueda.trim();
    if (!codigo) return;
    if (codigosVisibles.has(codigo)) {
      setBusquedaError(null);
      setResaltado(codigo);
      return;
    }
    setResaltado(null);
    setBusquedaError(
      sinCambio.some((s) => s.codigo === codigo)
        ? `"${codigo}" ya estaba igual y no cambia — por eso no aparece en ninguna tabla.`
        : `No se encontró "${codigo}" en esta revisión.`
    );
  }

  // Recorre las tablas: cada fila lleva `data-codigo-fila`, así que alcanza
  // con encontrar la primera coincidencia en el documento. `scrollIntoView`
  // sube por todos los contenedores con scroll propio (la tabla y la
  // página), así que basta esta llamada para las dos cosas.
  useEffect(() => {
    if (!resaltado) return;
    const el = document.querySelector(
      `[data-codigo-fila="${CSS.escape(resaltado)}"]`
    );
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [resaltado]);

  return (
    <section
      className="animar-entrada flex flex-col gap-4"
      style={{ animationDelay: "120ms" }}
    >
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Cifra valor={asignados.length} etiqueta="Reciben clasificación" />
        <Cifra valor={sinCambio.length} etiqueta="Ya estaban iguales" />
        <Cifra
          valor={pierden.length}
          etiqueta={
            estatusReemplazo
              ? `Dejan de ser infaltables → ${estatusReemplazo}`
              : "Dejan de ser infaltables"
          }
          alerta
        />
        <Cifra valor={problemas.length} etiqueta="Con problema" />
      </div>

      <form onSubmit={buscar} className="flex flex-wrap items-end gap-3">
        <label className="flex min-w-[220px] flex-1 flex-col gap-1.5">
          <span className="versalita">Buscar código en esta revisión</span>
          <input
            className={CAMPO}
            placeholder="Ej. 01-07-005"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
        </label>
        <button type="submit" className={BOTON_SECUNDARIO}>
          Buscar
        </button>
        {resaltado && (
          <button
            type="button"
            className={BOTON_SECUNDARIO}
            onClick={() => {
              setResaltado(null);
              setBusqueda("");
              setBusquedaError(null);
            }}
          >
            Quitar resaltado
          </button>
        )}
      </form>
      {busquedaError && (
        <p className="text-sm text-[#b91c1c]">{busquedaError}</p>
      )}

      {avisos.length > 0 && (
        <div className="rounded-[10px] border border-[#fde68a] bg-[#fffbeb] px-4 py-3">
          <p className="text-sm font-semibold text-[#92400e]">
            {numero(avisos.length)}{" "}
            {avisos.length === 1
              ? "producto tiene datos distintos a los de la base"
              : "productos tienen datos distintos a los de la base"}
          </p>
          <p className="mt-1 text-sm text-[#92400e]">
            Separados abajo por tipo de cambio. En cada sección puedes decidir
            producto por producto, o usar el botón de arriba para aplicar la
            misma elección a toda la sección de una vez.
          </p>
        </div>
      )}

      {filasCategoria.length > 0 && (
        <SeccionCampo
          campo="categoria"
          titulo="Cambios de categoría"
          filas={filasCategoria}
          elecciones={elecciones}
          onAlternar={onAlternar}
          onAlternarTodos={onAlternarTodos}
          resaltado={resaltado}
        />
      )}

      {filasSubcategoria.length > 0 && (
        <SeccionCampo
          campo="subcategoria"
          titulo="Cambios de subcategoría"
          filas={filasSubcategoria}
          elecciones={elecciones}
          onAlternar={onAlternar}
          onAlternarTodos={onAlternarTodos}
          resaltado={resaltado}
        />
      )}

      {filasNombre.length > 0 && (
        <SeccionCampo
          campo="nombre"
          titulo="Cambios de nombre / descripción"
          filas={filasNombre}
          mostrarProducto={false}
          elecciones={elecciones}
          onAlternar={onAlternar}
          onAlternarTodos={onAlternarTodos}
          resaltado={resaltado}
        />
      )}

      {sinDiferencias.length > 0 && (
        <TablaCambios
          titulo={`Reciben clasificación en ${sede} — sin diferencias`}
          filas={sinDiferencias}
          acento={acento}
          resaltado={resaltado}
        />
      )}

      {pierden.length > 0 && (
        <TablaCambios
          titulo="Dejan de ser infaltables"
          filas={pierden}
          acento={acento}
          alerta
          resaltado={resaltado}
        />
      )}

      {problemas.length > 0 && (
        <TablaProblemas problemas={problemas} resaltado={resaltado} />
      )}
    </section>
  );
}

type ColumnaCampo = "codigo" | "producto" | "estatus" | "valor";

function SeccionCampo({
  campo,
  titulo,
  filas,
  mostrarProducto = true,
  elecciones,
  onAlternar,
  onAlternarTodos,
  resaltado,
}: {
  campo: Campo;
  titulo: string;
  filas: FilaCampo[];
  mostrarProducto?: boolean;
  elecciones: Elecciones;
  onAlternar: (id: string, campo: Campo, usarArchivo: boolean) => void;
  onAlternarTodos: (campo: Campo, ids: string[], usarArchivo: boolean) => void;
  resaltado?: string | null;
}) {
  const idsAplicables = filas.filter((f) => f.archivoAplicable).map((f) => f.id);
  const idsTodos = filas.map((f) => f.id);

  const [columnaOrden, setColumnaOrden] = useState<ColumnaCampo>("codigo");
  const [direccionOrden, setDireccionOrden] = useState<Direccion>("asc");

  function ordenarPor(columna: ColumnaCampo) {
    if (columna === columnaOrden) setDireccionOrden((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setColumnaOrden(columna);
      setDireccionOrden("asc");
    }
  }

  const valorDe = (f: FilaCampo, columna: ColumnaCampo): string => {
    switch (columna) {
      case "codigo":
        return f.codigo;
      case "producto":
        return f.producto;
      case "estatus":
        return f.nuevo;
      case "valor":
        return f.archivo;
    }
  };

  const filasOrdenadas = useMemo(
    () =>
      [...filas].sort((a, b) =>
        comparar(valorDe(a, columnaOrden), valorDe(b, columnaOrden), direccionOrden)
      ),
    [filas, columnaOrden, direccionOrden]
  );

  return (
    <div className="overflow-hidden rounded-xl border border-[#fde68a] bg-white">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#fde68a] bg-[#fffbeb] px-4 py-3">
        <div className="flex items-baseline gap-2">
          <h3 className="text-sm font-semibold text-[#92400e]">{titulo}</h3>
          <span className="text-sm text-[#92400e]">({numero(filas.length)})</span>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className={BOTON_MINI_AMBAR}
            onClick={() => onAlternarTodos(campo, idsTodos, false)}
          >
            Usar base en todos
          </button>
          <button
            type="button"
            className={BOTON_MINI_AMBAR_LLENO}
            disabled={idsAplicables.length === 0}
            title={
              idsAplicables.length === 0
                ? "Ninguno de estos valores del archivo se pudo ubicar en el catálogo"
                : undefined
            }
            onClick={() => onAlternarTodos(campo, idsAplicables, true)}
          >
            Usar archivo en{" "}
            {idsAplicables.length < filas.length
              ? `los ${numero(idsAplicables.length)} aplicables`
              : "todos"}
          </button>
        </div>
      </div>
      <div className="max-h-80 overflow-y-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-marca-borde bg-marca-fondo">
              <EncabezadoOrdenable
                columna="codigo"
                etiqueta="Código"
                activa={columnaOrden}
                direccion={direccionOrden}
                onClick={ordenarPor}
              />
              {mostrarProducto && (
                <EncabezadoOrdenable
                  columna="producto"
                  etiqueta="Producto"
                  activa={columnaOrden}
                  direccion={direccionOrden}
                  onClick={ordenarPor}
                />
              )}
              <EncabezadoOrdenable
                columna="estatus"
                etiqueta="Estatus"
                activa={columnaOrden}
                direccion={direccionOrden}
                onClick={ordenarPor}
              />
              <EncabezadoOrdenable
                columna="valor"
                etiqueta={ETIQUETA_CAMPO[campo]}
                activa={columnaOrden}
                direccion={direccionOrden}
                onClick={ordenarPor}
              />
            </tr>
          </thead>
          <tbody>
            {filasOrdenadas.map((f) => (
              <tr
                key={f.id}
                data-codigo-fila={f.codigo}
                className={
                  "border-b border-marca-borde last:border-b-0 " +
                  (resaltado === f.codigo ? RESALTADO_FILA : "")
                }
              >
                <td className="px-4 py-2 font-mono whitespace-nowrap align-top">
                  {f.codigo}
                </td>
                {mostrarProducto && (
                  <td className="px-4 py-2 text-marca-negro align-top">
                    {f.producto}
                  </td>
                )}
                <td className="px-4 py-2 whitespace-nowrap align-top">
                  <span className="text-marca-texto">{f.actual}</span>
                  <span aria-hidden className="mx-1.5 text-marca-tenue">
                    →
                  </span>
                  <span className="font-semibold text-marca-negro">
                    {f.nuevo}
                  </span>
                </td>
                <td className="px-4 py-2 align-top">
                  <SelectorCampo
                    base={f.base}
                    archivo={f.archivo}
                    archivoAplicable={f.archivoAplicable}
                    usarArchivo={elecciones.get(f.id)?.[campo] ?? false}
                    onCambiar={(usarArchivo) => onAlternar(f.id, campo, usarArchivo)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

type ColumnaSimple = "codigo" | "producto" | "estatus";

function TablaCambios({
  titulo,
  filas,
  acento,
  alerta = false,
  resaltado,
}: {
  titulo: string;
  filas: Asignado[];
  acento: string;
  alerta?: boolean;
  resaltado?: string | null;
}) {
  const [columnaOrden, setColumnaOrden] = useState<ColumnaSimple>("codigo");
  const [direccionOrden, setDireccionOrden] = useState<Direccion>("asc");

  function ordenarPor(columna: ColumnaSimple) {
    if (columna === columnaOrden) setDireccionOrden((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setColumnaOrden(columna);
      setDireccionOrden("asc");
    }
  }

  const valorDe = (f: Asignado, columna: ColumnaSimple): string => {
    switch (columna) {
      case "codigo":
        return f.codigo;
      case "producto":
        return f.nombre;
      case "estatus":
        return f.nuevo;
    }
  };

  const filasOrdenadas = useMemo(
    () =>
      [...filas].sort((a, b) =>
        comparar(valorDe(a, columnaOrden), valorDe(b, columnaOrden), direccionOrden)
      ),
    [filas, columnaOrden, direccionOrden]
  );

  return (
    <div className="overflow-hidden rounded-xl border border-marca-borde bg-white">
      <div
        className="flex items-center gap-2 border-b border-marca-borde px-4 py-3"
        style={{ backgroundColor: alerta ? "#fef2f2" : suave(acento) }}
      >
        <h3 className="text-sm font-semibold text-marca-negro">{titulo}</h3>
        <span className="text-sm text-marca-texto">({numero(filas.length)})</span>
      </div>
      <div className="max-h-72 overflow-y-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-marca-borde bg-marca-fondo">
              <EncabezadoOrdenable
                columna="codigo"
                etiqueta="Código"
                activa={columnaOrden}
                direccion={direccionOrden}
                onClick={ordenarPor}
              />
              <EncabezadoOrdenable
                columna="producto"
                etiqueta="Producto"
                activa={columnaOrden}
                direccion={direccionOrden}
                onClick={ordenarPor}
              />
              <EncabezadoOrdenable
                columna="estatus"
                etiqueta="Cambio"
                activa={columnaOrden}
                direccion={direccionOrden}
                onClick={ordenarPor}
              />
            </tr>
          </thead>
          <tbody>
            {filasOrdenadas.map((f) => (
              <tr
                key={f.id}
                data-codigo-fila={f.codigo}
                className={
                  "border-b border-marca-borde last:border-b-0 " +
                  (resaltado === f.codigo ? RESALTADO_FILA : "")
                }
              >
                <td className="px-4 py-2 font-mono whitespace-nowrap align-top">
                  {f.codigo}
                </td>
                <td className="px-4 py-2 text-marca-negro align-top">
                  {f.nombre}
                </td>
                <td className="px-4 py-2 whitespace-nowrap align-top">
                  <span className="text-marca-texto">{f.actual}</span>
                  <span aria-hidden className="mx-2 text-marca-tenue">
                    →
                  </span>
                  <span className="font-semibold text-marca-negro">
                    {f.nuevo}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SelectorCampo({
  base,
  archivo,
  archivoAplicable,
  usarArchivo,
  onCambiar,
}: {
  base: string;
  archivo: string;
  archivoAplicable: boolean;
  usarArchivo: boolean;
  onCambiar: (usarArchivo: boolean) => void;
}) {
  return (
    <div className="inline-flex overflow-hidden rounded-full border border-[#fde68a]">
      <button
        type="button"
        className={
          "px-2 py-0.5 text-xs font-medium transition-colors " +
          (!usarArchivo
            ? "bg-[#92400e] text-white"
            : "bg-white text-[#92400e] hover:bg-[#fffbeb]")
        }
        onClick={() => onCambiar(false)}
      >
        Base: {base}
      </button>
      <button
        type="button"
        disabled={!archivoAplicable}
        title={
          archivoAplicable
            ? undefined
            : "No se pudo ubicar en el catálogo de esta casa: no se puede aplicar"
        }
        className={
          "px-2 py-0.5 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40 " +
          (usarArchivo
            ? "bg-[#92400e] text-white"
            : "bg-white text-[#92400e] hover:bg-[#fffbeb]")
        }
        onClick={() => onCambiar(true)}
      >
        Archivo: {archivo}
      </button>
    </div>
  );
}

function Cifra({
  valor,
  etiqueta,
  alerta = false,
}: {
  valor: number;
  etiqueta: string;
  alerta?: boolean;
}) {
  return (
    <div
      className="rounded-[10px] border px-3 py-2"
      style={{
        borderColor: alerta && valor > 0 ? "#fecaca" : "#e5e5e5",
        backgroundColor: alerta && valor > 0 ? "#fef2f2" : "#ffffff",
      }}
    >
      <p className="text-[1.35rem] font-bold tabular-nums text-marca-negro">
        {numero(valor)}
      </p>
      <p className="versalita">{etiqueta}</p>
    </div>
  );
}

/**
 * Los códigos que no existen en la casa (o con algún otro problema) no tienen
 * producto de la base con qué compararse, pero sí traen datos del Excel: se
 * muestran en la misma forma de tabla que el resto de la revisión, en vez de
 * una lista de texto, para no perder esos datos por no tener con qué cruzarlos.
 */
type ColumnaProblema =
  | "fila"
  | "codigo"
  | "descripcion"
  | "categoria"
  | "subcategoria"
  | "estatus"
  | "motivo";

function TablaProblemas({
  problemas,
  resaltado,
}: {
  problemas: ProblemaConDatos[];
  resaltado?: string | null;
}) {
  const [columnaOrden, setColumnaOrden] = useState<ColumnaProblema>("fila");
  const [direccionOrden, setDireccionOrden] = useState<Direccion>("asc");

  function ordenarPor(columna: ColumnaProblema) {
    if (columna === columnaOrden) setDireccionOrden((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setColumnaOrden(columna);
      setDireccionOrden("asc");
    }
  }

  const valorDe = (p: ProblemaConDatos, columna: ColumnaProblema): string | number => {
    switch (columna) {
      case "fila":
        return p.fila;
      case "codigo":
        return p.codigo;
      case "descripcion":
        return p.descripcionArchivo ?? "";
      case "categoria":
        return p.categoriaArchivo ?? "";
      case "subcategoria":
        return p.subcategoriaArchivo ?? "";
      case "estatus":
        return p.estatusArchivo ?? "";
      case "motivo":
        return p.motivo;
    }
  };

  const problemasOrdenados = useMemo(
    () =>
      [...problemas].sort((a, b) =>
        comparar(valorDe(a, columnaOrden), valorDe(b, columnaOrden), direccionOrden)
      ),
    [problemas, columnaOrden, direccionOrden]
  );

  return (
    <div className="overflow-hidden rounded-xl border border-marca-borde bg-white">
      <div className="flex items-center gap-2 border-b border-marca-borde bg-marca-fondo px-4 py-3">
        <h3 className="text-sm font-semibold text-marca-negro">Con problema</h3>
        <span className="text-sm text-marca-texto">({numero(problemas.length)})</span>
      </div>
      <div className="max-h-80 overflow-y-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-marca-borde bg-marca-fondo">
              <EncabezadoOrdenable
                columna="fila"
                etiqueta="Fila"
                activa={columnaOrden}
                direccion={direccionOrden}
                onClick={ordenarPor}
              />
              <EncabezadoOrdenable
                columna="codigo"
                etiqueta="Código"
                activa={columnaOrden}
                direccion={direccionOrden}
                onClick={ordenarPor}
              />
              <EncabezadoOrdenable
                columna="descripcion"
                etiqueta="Descripción"
                activa={columnaOrden}
                direccion={direccionOrden}
                onClick={ordenarPor}
              />
              <EncabezadoOrdenable
                columna="categoria"
                etiqueta="Categoría"
                activa={columnaOrden}
                direccion={direccionOrden}
                onClick={ordenarPor}
              />
              <EncabezadoOrdenable
                columna="subcategoria"
                etiqueta="Subcategoría"
                activa={columnaOrden}
                direccion={direccionOrden}
                onClick={ordenarPor}
              />
              <EncabezadoOrdenable
                columna="estatus"
                etiqueta="Clasif."
                activa={columnaOrden}
                direccion={direccionOrden}
                onClick={ordenarPor}
              />
              <EncabezadoOrdenable
                columna="motivo"
                etiqueta="Motivo"
                activa={columnaOrden}
                direccion={direccionOrden}
                onClick={ordenarPor}
              />
            </tr>
          </thead>
          <tbody>
            {problemasOrdenados.map((p, i) => (
              <tr
                key={`${p.fila}-${p.codigo}-${i}`}
                data-codigo-fila={p.codigo}
                className={
                  "border-b border-marca-borde last:border-b-0 " +
                  (resaltado === p.codigo ? RESALTADO_FILA : "")
                }
              >
                <td className="px-4 py-2 text-marca-tenue whitespace-nowrap align-top">
                  {p.fila}
                </td>
                <td className="px-4 py-2 font-mono whitespace-nowrap align-top">
                  {p.codigo}
                </td>
                <td className="px-4 py-2 text-marca-negro align-top">
                  {p.descripcionArchivo ?? <span className="text-marca-tenue">—</span>}
                </td>
                <td className="px-4 py-2 text-marca-negro align-top">
                  {p.categoriaArchivo ?? <span className="text-marca-tenue">—</span>}
                </td>
                <td className="px-4 py-2 text-marca-negro align-top">
                  {p.subcategoriaArchivo ?? <span className="text-marca-tenue">—</span>}
                </td>
                <td className="px-4 py-2 text-marca-negro align-top">
                  {p.estatusArchivo ?? <span className="text-marca-tenue">—</span>}
                </td>
                <td className="px-4 py-2 text-marca-texto align-top">{p.motivo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ListaProblemas({
  problemas,
  sinFila = false,
}: {
  problemas: ProblemaExcel[];
  sinFila?: boolean;
}) {
  const visibles = problemas.slice(0, 12);
  return (
    <div className="rounded-[10px] border border-marca-borde bg-marca-fondo px-4 py-3">
      <ul className="flex flex-col gap-1 text-sm text-marca-texto">
        {visibles.map((p, i) => (
          <li key={`${p.fila}-${p.codigo}-${i}`}>
            {!sinFila && <span className="text-marca-tenue">Fila {p.fila}: </span>}
            <span className="font-mono">{p.codigo}</span> — {p.motivo}
          </li>
        ))}
      </ul>
      {problemas.length > visibles.length && (
        <p className="mt-2 text-sm text-marca-tenue">
          y {numero(problemas.length - visibles.length)} más
        </p>
      )}
    </div>
  );
}
