import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import {
  fetchAllProductos,
  fetchEstatusProducto,
  updateMnemotecnia,
  type Progreso,
} from "@/lib/api";
import { SEDES, type Producto } from "@/lib/types";
import { colorEmpresa, suave } from "@/theme/marca";
import EtiquetaEmpresa from "@/components/EtiquetaEmpresa";
import CargarExcel from "@/components/CargarExcel";

type LoadState = "idle" | "loading" | "error" | "ready";

const BOTON_PRIMARIO =
  "rounded-[10px] bg-marca-negro px-[22px] py-2.5 text-[.9rem] font-semibold text-white " +
  "hover:bg-black disabled:opacity-50 disabled:cursor-not-allowed";

const BOTON_SECUNDARIO =
  "rounded-[10px] border border-marca-boton-borde bg-white px-[18px] py-2.5 text-[.9rem] " +
  "font-semibold text-marca-negro hover:bg-marca-boton disabled:opacity-50 " +
  "disabled:cursor-not-allowed";

// Encabezado y filas son grids independientes (la tabla está virtualizada, no
// es un <table>), así que comparten esta plantilla para quedar alineados.
const COLUMNAS_GRID =
  "140px minmax(220px, 1fr) 150px 150px minmax(240px, 1.2fr) 200px";

const CAMPO =
  "rounded-[10px] border border-marca-borde bg-white px-3 py-2 text-sm text-marca-negro " +
  "placeholder:text-marca-tenue focus:border-marca-negro focus:outline-none";

export default function ProductosTable() {
  const [sede, setSede] = useState<string>(SEDES[0]);
  const [query, setQuery] = useState("");
  const [soloInfaltables, setSoloInfaltables] = useState(false);

  const [productos, setProductos] = useState<Producto[]>([]);
  const [infaltableCodigos, setInfaltableCodigos] = useState<Set<string>>(
    new Set()
  );
  // Arranca en "loading", no en "idle": el efecto corre después de la primera
  // pintura, y con "idle" se veía un instante sin tabla ni barra.
  const [state, setState] = useState<LoadState>("loading");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [progreso, setProgreso] = useState<Progreso>({
    cargadas: 0,
    total: null,
  });

  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [savingId, setSavingId] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  const acento = colorEmpresa(sede);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setState("loading");
      setErrorMsg(null);
      setProgreso({ cargadas: 0, total: null });
      try {
        const [productos, estatus] = await Promise.all([
          // En desarrollo StrictMode monta el efecto dos veces: sin este guardia
          // la corrida abortada seguiría empujando su avance a la barra.
          fetchAllProductos(sede, (p) => {
            if (!cancelled) setProgreso(p);
          }),
          fetchEstatusProducto(),
        ]);
        if (cancelled) return;
        setProductos(productos);
        setInfaltableCodigos(
          new Set(estatus.filter((e) => e.es_infaltable).map((e) => e.codigo))
        );
        setState("ready");
      } catch (err) {
        if (cancelled) return;
        setErrorMsg((err as Error).message);
        setState("error");
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [sede]);

  // El filtrado recorre miles de productos: con `useDeferredValue` React deja
  // que la tecla se pinte de inmediato y recalcula la lista después, en vez de
  // bloquear el campo en cada pulsación.
  const queryDiferida = useDeferredValue(query);

  const filtered = useMemo(() => {
    const q = queryDiferida.trim().toLowerCase();
    return productos.filter((p) => {
      if (soloInfaltables && !infaltableCodigos.has(p.estatus)) return false;
      if (!q) return true;
      return (
        p.nombre.toLowerCase().includes(q) ||
        (p.codigo_completo ?? "").toLowerCase().includes(q) ||
        p.codigo.toLowerCase().includes(q)
      );
    });
  }, [productos, queryDiferida, soloInfaltables, infaltableCodigos]);

  // Virtualización: se renderizan solo las filas visibles. Con el catálogo
  // completo en el DOM eran ~6.200 filas y 37.000 celdas (5 MB), y cada
  // filtrado o edición obligaba a React a reconciliarlas todas de golpe —
  // de ahí el congelamiento y el "Chrome no responde".
  const contenedorRef = useRef<HTMLDivElement>(null);
  const virtualizador = useVirtualizer({
    count: filtered.length,
    getScrollElement: () => contenedorRef.current,
    // Alto estimado; el real se mide por fila, porque los nombres largos
    // ocupan dos líneas y la fila en edición crece con el textarea.
    estimateSize: () => 57,
    overscan: 8,
    getItemKey: (i) => filtered[i]?.id ?? i,
  });

  // Al cambiar de casa o de filtro la lista es otra: si no se vuelve arriba,
  // el scroll queda apuntando a una posición que ya no existe.
  useEffect(() => {
    contenedorRef.current?.scrollTo({ top: 0 });
  }, [sede, queryDiferida, soloInfaltables]);

  /** Refleja en la tabla lo que la carga masiva ya guardó, sin volver a bajar el catálogo. */
  function aplicarCambiosLocales(
    cambios: { id: string; mnemotecnia: string }[]
  ) {
    if (cambios.length === 0) return;
    const porId = new Map(cambios.map((c) => [c.id, c.mnemotecnia]));
    setProductos((prev) =>
      prev.map((p) =>
        porId.has(p.id) ? { ...p, mnemotecnia: porId.get(p.id)! } : p
      )
    );
  }

  function startEdit(p: Producto) {
    setEditingId(p.id);
    setDraft(p.mnemotecnia ?? "");
    setSaveError(null);
  }

  function cancelEdit() {
    setEditingId(null);
    setDraft("");
    setSaveError(null);
  }

  async function saveEdit(id: string) {
    setSavingId(id);
    setSaveError(null);
    try {
      const producto = await updateMnemotecnia(id, draft);
      setProductos((prev) =>
        prev.map((p) =>
          p.id === id ? { ...p, mnemotecnia: producto.mnemotecnia } : p
        )
      );
      setEditingId(null);
      setDraft("");
    } catch (err) {
      setSaveError(
        `No se guardó la mnemotecnia: ${(err as Error).message}. Intenta de nuevo.`
      );
    } finally {
      setSavingId(null);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-6 py-8">
      <div className="animar-entrada flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-[1.6rem] font-bold text-marca-negro">
            Catálogo de productos
          </h1>
          <p className="mt-1 text-sm text-marca-texto">
            Consulta los códigos de la casa y edita su mnemotecnia.
          </p>
        </div>
        <EtiquetaEmpresa empresa={sede} className="pb-1 font-medium" />
      </div>

      {/* Filtros */}
      <section
        className="animar-entrada rounded-xl border border-marca-borde bg-white p-4"
        style={{ animationDelay: "60ms" }}
      >
        <div className="flex flex-wrap items-end gap-4">
          <label className="flex flex-col gap-1.5">
            <span className="versalita">Casa</span>
            <span
              className="flex items-center gap-2 rounded-[10px] border border-marca-borde bg-white px-3 py-2 focus-within:border-marca-negro"
              style={{ borderLeft: `3px solid ${acento}` }}
            >
              <span
                aria-hidden
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: acento }}
              />
              <select
                className="appearance-none bg-transparent pr-1 text-sm font-medium text-marca-negro focus:outline-none"
                value={sede}
                onChange={(e) => setSede(e.target.value)}
              >
                {SEDES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              <svg
                aria-hidden
                viewBox="0 0 12 12"
                className="h-3 w-3 shrink-0 text-marca-texto"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M3 4.5 6 7.5 9 4.5" />
              </svg>
            </span>
          </label>

          <label className="flex min-w-[240px] flex-1 flex-col gap-1.5">
            <span className="versalita">Buscar</span>
            <input
              className={CAMPO}
              placeholder="Nombre o código del producto"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>

          <label className="flex cursor-pointer items-center gap-2 rounded-[10px] border border-marca-borde bg-white px-3 py-2.5 text-sm text-marca-negro hover:bg-marca-boton">
            <input
              type="checkbox"
              className="h-4 w-4 accent-[#1d1d1b]"
              checked={soloInfaltables}
              onChange={(e) => setSoloInfaltables(e.target.checked)}
            />
            Solo infaltables
          </label>

          <CargarExcel
            sede={sede}
            acento={acento}
            productos={productos}
            onAplicado={aplicarCambiosLocales}
          />
        </div>
      </section>

      {state === "loading" && (
        <TablaCargando sede={sede} acento={acento} progreso={progreso} />
      )}

      {state === "error" && (
        <section className="rounded-xl border border-[#fecaca] bg-[#fef2f2] p-5">
          <h2 className="text-sm font-semibold text-[#b91c1c]">
            No se pudo cargar el catálogo
          </h2>
          <p className="mt-1 text-sm text-[#b91c1c]">
            {errorMsg}. Revisa tu conexión y vuelve a cargar la página.
          </p>
        </section>
      )}

      {state === "ready" && (
        <section
          className="animar-entrada flex flex-col gap-3"
          style={{ animationDelay: "120ms" }}
        >
          <p className="text-sm text-marca-texto">
            <span className="font-semibold text-marca-negro">
              {filtered.length}
            </span>{" "}
            de {productos.length} productos
          </p>

          {saveError && (
            <p className="rounded-[10px] border border-[#fecaca] bg-[#fef2f2] px-4 py-3 text-sm text-[#b91c1c]">
              {saveError}
            </p>
          )}

          {filtered.length === 0 ? (
            <div className="rounded-xl border border-marca-borde bg-white px-6 py-14 text-center">
              <p className="text-sm font-semibold text-marca-negro">
                Ningún producto coincide con la búsqueda
              </p>
              <p className="mt-1 text-sm text-marca-texto">
                Cambia el texto o quita el filtro de infaltables.
              </p>
            </div>
          ) : (
            <div
              ref={contenedorRef}
              role="table"
              aria-rowcount={filtered.length}
              className="h-[70vh] overflow-auto rounded-xl border border-marca-borde bg-white"
            >
              <div className="min-w-[1100px] text-sm">
                <div
                  role="row"
                  className="sticky top-0 z-10 grid border-b border-marca-borde bg-marca-fondo"
                  style={{ gridTemplateColumns: COLUMNAS_GRID }}
                >
                  <div role="columnheader" className="versalita px-4 py-3">
                    Código
                  </div>
                  <div role="columnheader" className="versalita px-4 py-3">
                    Nombre
                  </div>
                  <div role="columnheader" className="versalita px-4 py-3">
                    Marca
                  </div>
                  <div role="columnheader" className="versalita px-4 py-3">
                    Estatus
                  </div>
                  <div role="columnheader" className="versalita px-4 py-3">
                    Mnemotecnia
                  </div>
                  <div role="columnheader" className="px-4 py-3">
                    <span className="sr-only">Acciones</span>
                  </div>
                </div>

                <div
                  className="relative"
                  style={{ height: virtualizador.getTotalSize() }}
                >
                  {virtualizador.getVirtualItems().map((virtual) => {
                    const p = filtered[virtual.index];
                    const isEditing = editingId === p.id;
                    const isInfaltable = infaltableCodigos.has(p.estatus);
                    return (
                      <div
                        key={virtual.key}
                        role="row"
                        aria-rowindex={virtual.index + 1}
                        data-index={virtual.index}
                        ref={virtualizador.measureElement}
                        className="absolute top-0 left-0 grid w-full items-start border-b border-marca-borde hover:bg-marca-fondo"
                        style={{
                          gridTemplateColumns: COLUMNAS_GRID,
                          transform: `translateY(${virtual.start}px)`,
                        }}
                      >
                        <div
                          role="cell"
                          className="px-4 py-3 font-mono whitespace-nowrap text-marca-negro"
                        >
                          {p.codigo_completo ?? p.codigo}
                        </div>
                        <div role="cell" className="px-4 py-3 text-marca-negro">
                          {p.nombre}
                        </div>
                        <div
                          role="cell"
                          className="px-4 py-3 whitespace-nowrap text-marca-texto"
                        >
                          {p.marca || <span className="text-marca-tenue">—</span>}
                        </div>
                        <div role="cell" className="px-4 py-3 whitespace-nowrap">
                          <span className="text-marca-texto">{p.estatus}</span>
                          {isInfaltable && (
                            <span
                              className="ml-2 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold text-marca-negro"
                              style={{ backgroundColor: suave(acento) }}
                            >
                              ★ Infaltable
                            </span>
                          )}
                        </div>
                        <div role="cell" className="px-4 py-3">
                          {isEditing ? (
                            <textarea
                              className={`${CAMPO} w-full`}
                              rows={2}
                              value={draft}
                              onChange={(e) => setDraft(e.target.value)}
                              autoFocus
                            />
                          ) : (
                            <span className="whitespace-pre-wrap text-marca-negro">
                              {p.mnemotecnia || (
                                <span className="text-marca-tenue">—</span>
                              )}
                            </span>
                          )}
                        </div>
                        <div role="cell" className="px-4 py-3 whitespace-nowrap">
                          {isEditing ? (
                            <div className="flex gap-2">
                              <button
                                className={BOTON_PRIMARIO}
                                disabled={savingId === p.id}
                                onClick={() => saveEdit(p.id)}
                              >
                                {savingId === p.id ? "Guardando…" : "Guardar"}
                              </button>
                              <button
                                className={BOTON_SECUNDARIO}
                                disabled={savingId === p.id}
                                onClick={cancelEdit}
                              >
                                Cancelar
                              </button>
                            </div>
                          ) : (
                            <button
                              className={BOTON_SECUNDARIO}
                              onClick={() => startEdit(p)}
                            >
                              Editar
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

const numero = (n: number) => n.toLocaleString("es-VE");

function TablaCargando({
  sede,
  acento,
  progreso,
}: {
  sede: string;
  acento: string;
  progreso: Progreso;
}) {
  const { cargadas, total } = progreso;
  // Hasta que vuelve la primera página no se sabe el total: mostrar un
  // porcentaje ahí sería inventarlo, así que la barra va indeterminada.
  const porcentaje =
    total && total > 0 ? Math.min(100, Math.round((cargadas / total) * 100)) : null;

  return (
    <div className="animar-entrada flex flex-col gap-4" aria-busy="true">
      <section className="rounded-xl border border-marca-borde bg-white p-5">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <p className="text-sm font-semibold text-marca-negro">
            Cargando el catálogo de {sede}
          </p>
          <p className="text-[1.35rem] font-bold tabular-nums text-marca-negro">
            {porcentaje === null ? "…" : `${porcentaje} %`}
          </p>
        </div>

        <div
          className="mt-3 h-2 w-full overflow-hidden rounded-full bg-marca-gris-claro"
          role="progressbar"
          aria-label={`Cargando el catálogo de ${sede}`}
          aria-valuemin={0}
          aria-valuemax={100}
          {...(porcentaje === null ? {} : { "aria-valuenow": porcentaje })}
        >
          {/* Las `key` distintas son necesarias: sin ellas React reutiliza el
              mismo <div> al pasar de indeterminada a determinada, el nodo
              conserva el ancho completo del skeleton y la transición anima
              desde 100 % hacia abajo — la barra se veía llena y encogiéndose. */}
          {porcentaje === null ? (
            <div key="indeterminada" className="skeleton h-full w-full rounded-full" />
          ) : (
            <div
              key="determinada"
              className="h-full rounded-full transition-[width] duration-[320ms]"
              style={{
                width: `${porcentaje}%`,
                backgroundColor: acento,
                transitionTimingFunction: "var(--ease-salida)",
              }}
            />
          )}
        </div>

        <p className="mt-2 text-sm tabular-nums text-marca-texto" aria-live="polite">
          {total === null
            ? "Consultando cuántos productos tiene la casa…"
            : `${numero(cargadas)} de ${numero(total)} productos`}
        </p>
      </section>

      <div className="rounded-xl border border-marca-borde bg-white p-4">
        <div className="flex flex-col gap-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex gap-3">
              <div className="skeleton h-5 w-28" />
              <div className="skeleton h-5 flex-1" />
              <div className="skeleton h-5 w-24" />
              <div className="skeleton h-5 w-40" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
