import { useRef, useState } from "react";
import { createPortal } from "react-dom";
import { updateMnemotecniasEnLote } from "@/lib/api";
import {
  leerMnemotecniasDeExcel,
  type ProblemaExcel,
} from "@/lib/excel";
import type { Producto } from "@/lib/types";

const BOTON_PRIMARIO =
  "rounded-[10px] bg-marca-negro px-[22px] py-2.5 text-[.9rem] font-semibold text-white " +
  "hover:bg-black disabled:opacity-50 disabled:cursor-not-allowed";

const BOTON_SECUNDARIO =
  "rounded-[10px] border border-marca-boton-borde bg-white px-[18px] py-2.5 text-[.9rem] " +
  "font-semibold text-marca-negro hover:bg-marca-boton disabled:opacity-50 " +
  "disabled:cursor-not-allowed";

// Botones compactos para las acciones dentro de la tabla del panel: mismos
// colores del sistema, con menos aire porque van en filas densas.
const BOTON_MINI =
  "rounded-[8px] border border-marca-boton-borde bg-white px-2.5 py-1 text-xs " +
  "font-semibold text-marca-negro hover:bg-marca-boton disabled:opacity-50";

const BOTON_MINI_PRIMARIO =
  "rounded-[8px] bg-marca-negro px-2.5 py-1 text-xs font-semibold text-white " +
  "hover:bg-black disabled:opacity-50 disabled:cursor-not-allowed";

const BOTON_MINI_QUITAR =
  "rounded-[8px] border border-[#fecaca] bg-white px-2.5 py-1 text-xs " +
  "font-semibold text-[#b91c1c] hover:bg-[#fef2f2]";

type Cambio = {
  id: string;
  codigo: string;
  nombre: string;
  anterior: string | null;
  nueva: string;
};

type Revision = {
  cambios: Cambio[];
  sinCambio: number;
  problemas: ProblemaExcel[];
};

type Fase =
  | { tipo: "inactivo" }
  | { tipo: "leyendo" }
  | { tipo: "revision"; revision: Revision }
  | { tipo: "aplicando"; hechas: number; total: number }
  | { tipo: "resultado"; aplicadas: number; fallidas: number; problemas: ProblemaExcel[] }
  | { tipo: "error"; mensaje: string };

const numero = (n: number) => n.toLocaleString("es-VE");

/** "1 mnemotecnia" / "2 mnemotecnias" — sin el "1 mnemotecnia(s)" de plantilla. */
const mnemotecnias = (n: number) =>
  `${numero(n)} ${n === 1 ? "mnemotecnia" : "mnemotecnias"}`;

/** El código que ve el usuario en la tabla es `codigo_completo`, con `codigo` de respaldo. */
const codigoDe = (p: Producto) => p.codigo_completo ?? p.codigo;

export default function CargarExcel({
  sede,
  acento,
  productos,
  onAplicado,
}: {
  sede: string;
  acento: string;
  productos: Producto[];
  onAplicado: (cambios: { id: string; mnemotecnia: string }[]) => void;
}) {
  const [fase, setFase] = useState<Fase>({ tipo: "inactivo" });
  const inputRef = useRef<HTMLInputElement>(null);

  // El lote es editable antes de aplicarse: si el Excel trae algo mal, se
  // corrige o se quita la fila aquí en vez de tener que rehacer el archivo.
  function editarCambio(id: string, nueva: string) {
    setFase((actual) => {
      if (actual.tipo !== "revision") return actual;
      const cambios = actual.revision.cambios.map((c) =>
        c.id === id ? { ...c, nueva } : c
      );
      return { tipo: "revision", revision: { ...actual.revision, cambios } };
    });
  }

  function quitarCambio(id: string) {
    setFase((actual) => {
      if (actual.tipo !== "revision") return actual;
      const cambios = actual.revision.cambios.filter((c) => c.id !== id);
      return { tipo: "revision", revision: { ...actual.revision, cambios } };
    });
  }

  async function alElegirArchivo(archivo: File) {
    setFase({ tipo: "leyendo" });
    try {
      const { filas, problemas } = await leerMnemotecniasDeExcel(archivo);

      // El Excel no trae casa: se cruza contra el catálogo de la casa que está
      // seleccionada, y lo que no aparezca ahí se reporta en vez de aplicarse.
      const porCodigo = new Map(productos.map((p) => [codigoDe(p), p]));
      const cambios: Cambio[] = [];
      const problemasCruce = [...problemas];
      let sinCambio = 0;

      for (const f of filas) {
        const producto = porCodigo.get(f.codigo);
        if (!producto) {
          problemasCruce.push({
            fila: f.fila,
            codigo: f.codigo,
            motivo: `No existe en ${sede}`,
          });
          continue;
        }
        if ((producto.mnemotecnia ?? "") === f.mnemotecnia) {
          sinCambio++;
          continue;
        }
        cambios.push({
          id: producto.id,
          codigo: f.codigo,
          nombre: producto.nombre,
          anterior: producto.mnemotecnia,
          nueva: f.mnemotecnia,
        });
      }

      problemasCruce.sort((a, b) => a.fila - b.fila);
      setFase({
        tipo: "revision",
        revision: { cambios, sinCambio, problemas: problemasCruce },
      });
    } catch (err) {
      setFase({ tipo: "error", mensaje: (err as Error).message });
    }
  }

  async function aplicar(revision: Revision) {
    const items = revision.cambios.map((c) => ({
      id: c.id,
      codigo: c.codigo,
      mnemotecnia: c.nueva,
    }));
    setFase({ tipo: "aplicando", hechas: 0, total: items.length });

    const { aplicadas, fallidas } = await updateMnemotecniasEnLote(
      items,
      (hechas, total) => setFase({ tipo: "aplicando", hechas, total })
    );

    // Solo se refleja en la tabla lo que de verdad se guardó.
    const fallidosIds = new Set(fallidas.map((f) => f.id));
    onAplicado(
      items
        .filter((i) => !fallidosIds.has(i.id))
        .map((i) => ({ id: i.id, mnemotecnia: i.mnemotecnia }))
    );

    setFase({
      tipo: "resultado",
      aplicadas,
      fallidas: fallidas.length,
      problemas: fallidas.map((f) => ({
        fila: 0,
        codigo: f.codigo,
        motivo: f.motivo,
      })),
    });
  }

  function cerrar() {
    setFase({ tipo: "inactivo" });
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls"
        className="hidden"
        onChange={(e) => {
          const archivo = e.target.files?.[0];
          if (archivo) alElegirArchivo(archivo);
        }}
      />
      <button
        className={BOTON_SECUNDARIO}
        onClick={() => inputRef.current?.click()}
        disabled={fase.tipo === "leyendo" || fase.tipo === "aplicando"}
      >
        Cargar Excel
      </button>

      {/* Va por portal al <body>: el botón vive dentro de la tarjeta de filtros,
          que tiene `.animar-entrada`, y una animación con `transform` convierte
          al ancestro en bloque contenedor de los descendientes `fixed` — el
          modal quedaba recortado dentro de la tarjeta en vez de cubrir la
          pantalla. */}
      {fase.tipo !== "inactivo" &&
        createPortal(
        <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/30 p-6">
          <section className="animar-entrada mt-10 w-full max-w-2xl rounded-xl border border-marca-borde bg-white p-6">
            <h2 className="text-lg font-semibold text-marca-negro">
              Cargar mnemotecnias desde Excel
            </h2>
            <p className="mt-1 text-sm text-marca-texto">
              Se aplicará al catálogo de{" "}
              <span className="inline-flex items-center gap-1.5 font-medium text-marca-negro">
                <span
                  aria-hidden
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: acento }}
                />
                {sede}
              </span>
              .
            </p>

            <div className="mt-5">
              {fase.tipo === "leyendo" && (
                <p className="text-sm text-marca-texto">Leyendo el archivo…</p>
              )}

              {fase.tipo === "error" && (
                <p className="rounded-[10px] border border-[#fecaca] bg-[#fef2f2] px-4 py-3 text-sm text-[#b91c1c]">
                  {fase.mensaje}
                </p>
              )}

              {fase.tipo === "revision" && (
                <Resumen
                  revision={fase.revision}
                  onEditar={editarCambio}
                  onQuitar={quitarCambio}
                />
              )}

              {fase.tipo === "aplicando" && (
                <Aplicando
                  hechas={fase.hechas}
                  total={fase.total}
                  acento={acento}
                />
              )}

              {fase.tipo === "resultado" && (
                <div className="flex flex-col gap-3">
                  <p className="text-sm font-semibold text-marca-negro">
                    {fase.aplicadas === 1
                      ? "Se guardó 1 mnemotecnia"
                      : `Se guardaron ${mnemotecnias(fase.aplicadas)}`}
                  </p>
                  {fase.fallidas > 0 && (
                    <>
                      <p className="text-sm text-[#b91c1c]">
                        {fase.fallidas === 1
                          ? "1 no se pudo guardar:"
                          : `${numero(fase.fallidas)} no se pudieron guardar:`}
                      </p>
                      <ListaProblemas problemas={fase.problemas} sinFila />
                    </>
                  )}
                </div>
              )}
            </div>

            <div className="mt-6 flex flex-wrap justify-end gap-2">
              {fase.tipo === "revision" && (
                <>
                  <button className={BOTON_SECUNDARIO} onClick={cerrar}>
                    Cancelar
                  </button>
                  <button
                    className={BOTON_PRIMARIO}
                    disabled={fase.revision.cambios.length === 0}
                    onClick={() => aplicar(fase.revision)}
                  >
                    {fase.revision.cambios.length === 0
                      ? "No hay nada que aplicar"
                      : `Aplicar ${mnemotecnias(fase.revision.cambios.length)}`}
                  </button>
                </>
              )}
              {(fase.tipo === "resultado" || fase.tipo === "error") && (
                <button className={BOTON_PRIMARIO} onClick={cerrar}>
                  Listo
                </button>
              )}
            </div>
          </section>
        </div>,
          document.body
        )}
    </>
  );
}

function Resumen({
  revision,
  onEditar,
  onQuitar,
}: {
  revision: Revision;
  onEditar: (id: string, nueva: string) => void;
  onQuitar: (id: string) => void;
}) {
  const { cambios, sinCambio, problemas } = revision;
  const [editandoId, setEditandoId] = useState<string | null>(null);
  const [borrador, setBorrador] = useState("");

  function empezarEdicion(c: Cambio) {
    setEditandoId(c.id);
    setBorrador(c.nueva);
  }

  function guardarEdicion(id: string) {
    onEditar(id, borrador.trim());
    setEditandoId(null);
    setBorrador("");
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-3 gap-3">
        <Cifra valor={cambios.length} etiqueta="Por aplicar" />
        <Cifra valor={sinCambio} etiqueta="Ya estaban iguales" />
        <Cifra valor={problemas.length} etiqueta="Con problema" />
      </div>

      {cambios.length > 0 && (
        <div className="overflow-hidden rounded-[10px] border border-marca-borde">
          <div className="max-h-56 overflow-y-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-marca-borde bg-marca-fondo">
                  <th className="versalita px-3 py-2 text-left">Código</th>
                  <th className="versalita px-3 py-2 text-left">Antes</th>
                  <th className="versalita px-3 py-2 text-left">Después</th>
                  <th className="px-3 py-2">
                    <span className="sr-only">Acciones</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {cambios.map((c) => {
                  const editando = editandoId === c.id;
                  return (
                    <tr
                      key={c.id}
                      className="border-b border-marca-borde align-top last:border-b-0"
                    >
                      <td className="px-3 py-2 font-mono whitespace-nowrap">
                        {c.codigo}
                      </td>
                      <td className="px-3 py-2 text-marca-texto">
                        {c.anterior || <span className="text-marca-tenue">—</span>}
                      </td>
                      <td className="px-3 py-2 text-marca-negro">
                        {editando ? (
                          <input
                            className="w-full rounded-[8px] border border-marca-negro px-2 py-1 text-sm focus:outline-none"
                            value={borrador}
                            autoFocus
                            onChange={(e) => setBorrador(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter" && borrador.trim())
                                guardarEdicion(c.id);
                              if (e.key === "Escape") setEditandoId(null);
                            }}
                          />
                        ) : (
                          c.nueva
                        )}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        <div className="flex justify-end gap-1">
                          {editando ? (
                            <>
                              <button
                                className={BOTON_MINI_PRIMARIO}
                                disabled={!borrador.trim()}
                                onClick={() => guardarEdicion(c.id)}
                              >
                                Guardar
                              </button>
                              <button
                                className={BOTON_MINI}
                                onClick={() => setEditandoId(null)}
                              >
                                Cancelar
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                className={BOTON_MINI}
                                onClick={() => empezarEdicion(c)}
                              >
                                Editar
                              </button>
                              <button
                                className={BOTON_MINI_QUITAR}
                                onClick={() => onQuitar(c.id)}
                                title={`Quitar ${c.codigo} del lote`}
                              >
                                Quitar
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {problemas.length > 0 && <ListaProblemas problemas={problemas} />}
    </div>
  );
}

function Cifra({ valor, etiqueta }: { valor: number; etiqueta: string }) {
  return (
    <div className="rounded-[10px] border border-marca-borde px-3 py-2">
      <p className="text-[1.35rem] font-bold tabular-nums text-marca-negro">
        {numero(valor)}
      </p>
      <p className="versalita">{etiqueta}</p>
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

function Aplicando({
  hechas,
  total,
  acento,
}: {
  hechas: number;
  total: number;
  acento: string;
}) {
  const porcentaje = total > 0 ? Math.round((hechas / total) * 100) : 100;
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-sm font-semibold text-marca-negro">
          Guardando mnemotecnias
        </p>
        <p className="text-[1.35rem] font-bold tabular-nums text-marca-negro">
          {porcentaje} %
        </p>
      </div>
      <div
        className="mt-3 h-2 w-full overflow-hidden rounded-full bg-marca-gris-claro"
        role="progressbar"
        aria-label="Guardando mnemotecnias"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={porcentaje}
      >
        <div
          className="h-full rounded-full transition-[width] duration-[320ms]"
          style={{
            width: `${porcentaje}%`,
            backgroundColor: acento,
            transitionTimingFunction: "var(--ease-salida)",
          }}
        />
      </div>
      <p className="mt-2 text-sm tabular-nums text-marca-texto" aria-live="polite">
        {numero(hechas)} de {numero(total)}
      </p>
    </div>
  );
}
