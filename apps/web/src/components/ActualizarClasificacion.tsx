import { useMemo, useState } from "react";
import { updateEstatusEnLote } from "@/lib/api";
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

const SELECT =
  "rounded-[10px] border border-marca-borde bg-white px-3 py-2 text-sm font-medium " +
  "text-marca-negro focus:border-marca-negro focus:outline-none disabled:opacity-50";

const numero = (n: number) => n.toLocaleString("es-VE");
const codigoDe = (p: Producto) => p.codigo_completo ?? p.codigo;

/** Normaliza para comparar descripciones sin castigar tildes ni espacios. */
function normalizarTexto(t: string): string {
  return t
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

type Asignado = {
  id: string;
  codigo: string;
  nombre: string;
  actual: string;
  nuevo: string;
  /** El nombre del Excel no coincide con el de la base: hay que mirarlo. */
  descripcionDistinta: string | null;
};

type Fase =
  | { tipo: "inactivo" }
  | { tipo: "leyendo" }
  | { tipo: "aplicando"; hechas: number; total: number }
  | { tipo: "resultado"; aplicadas: number; fallidas: ProblemaExcel[] }
  | { tipo: "error"; mensaje: string };

export default function ActualizarClasificacion() {
  const { sede, productos, estatus, infaltables, estado, aplicarCambios } =
    useCatalogo();

  const [lectura, setLectura] = useState<LecturaClasificacion | null>(null);
  const [nombreArchivo, setNombreArchivo] = useState("");
  const [mismoParaTodos, setMismoParaTodos] = useState(false);
  const [estatusUnico, setEstatusUnico] = useState("");
  const [estatusReemplazo, setEstatusReemplazo] = useState("");
  const [fase, setFase] = useState<Fase>({ tipo: "inactivo" });

  const acento = colorEmpresa(sede);
  const codigosInfaltables = useMemo(
    () => estatus.filter((e) => e.es_infaltable).map((e) => e.codigo).sort(),
    [estatus]
  );
  const codigosNoInfaltables = useMemo(
    () => estatus.filter((e) => !e.es_infaltable).map((e) => e.codigo).sort(),
    [estatus]
  );

  async function alElegirArchivo(archivo: File) {
    setFase({ tipo: "leyendo" });
    setNombreArchivo(archivo.name);
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
    const problemas: ProblemaExcel[] = [...lectura.problemas];

    for (const f of lectura.filas) {
      const destino = mismoParaTodos ? estatusUnico : f.estatus;

      if (!destino) {
        if (!faltaElegir) {
          problemas.push({
            fila: f.fila,
            codigo: f.codigo,
            motivo: "Sin clasificación en el archivo",
          });
        }
        continue;
      }
      if (!estatus.some((e) => e.codigo === destino)) {
        problemas.push({
          fila: f.fila,
          codigo: f.codigo,
          motivo: `El estatus "${destino}" no existe en el catálogo`,
        });
        continue;
      }

      const producto = porCodigo.get(f.codigo);
      if (!producto) {
        problemas.push({
          fila: f.fila,
          codigo: f.codigo,
          motivo: `No existe en ${sede}`,
        });
        continue;
      }

      codigosDelArchivo.add(f.codigo);

      const descripcionDistinta =
        f.descripcion &&
        normalizarTexto(f.descripcion) !== normalizarTexto(producto.nombre)
          ? f.descripcion
          : null;

      const fila: Asignado = {
        id: producto.id,
        codigo: f.codigo,
        nombre: producto.nombre,
        actual: producto.estatus,
        nuevo: destino,
        descripcionDistinta,
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
            descripcionDistinta: null,
          }))
      : [];

    const avisos = asignados.filter((a) => a.descripcionDistinta);

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
  ]);

  const listoParaAplicar =
    revision !== null &&
    estatusReemplazo !== "" &&
    (!mismoParaTodos || estatusUnico !== "") &&
    revision.asignados.length + revision.pierden.length > 0 &&
    estado === "listo";

  async function aplicar() {
    if (!revision) return;
    const items = [...revision.asignados, ...revision.pierden].map((a) => ({
      id: a.id,
      codigo: a.codigo,
      estatus: a.nuevo,
    }));

    setFase({ tipo: "aplicando", hechas: 0, total: items.length });
    const { aplicadas, fallidas } = await updateEstatusEnLote(
      items,
      (hechas, total) => setFase({ tipo: "aplicando", hechas, total })
    );

    const fallidosIds = new Set(fallidas.map((f) => f.id));
    aplicarCambios(
      items
        .filter((i) => !fallidosIds.has(i.id))
        .map((i) => ({ id: i.id, estatus: i.estatus }))
    );

    setFase({
      tipo: "resultado",
      aplicadas,
      fallidas: fallidas.map((f) => ({
        fila: 0,
        codigo: f.codigo,
        motivo: f.motivo,
      })),
    });
    setLectura(null);
    setNombreArchivo("");
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
              revision={revision}
              sede={sede}
              acento={acento}
              estatusReemplazo={estatusReemplazo}
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
              onClick={aplicar}
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
    </div>
  );
}

function Revision({
  revision,
  sede,
  acento,
  estatusReemplazo,
}: {
  revision: {
    asignados: Asignado[];
    sinCambio: Asignado[];
    pierden: Asignado[];
    problemas: ProblemaExcel[];
    avisos: Asignado[];
  };
  sede: string;
  acento: string;
  estatusReemplazo: string;
}) {
  const { asignados, sinCambio, pierden, problemas, avisos } = revision;

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

      {avisos.length > 0 && (
        <div className="rounded-[10px] border border-[#fde68a] bg-[#fffbeb] px-4 py-3">
          <p className="text-sm font-semibold text-[#92400e]">
            {numero(avisos.length)}{" "}
            {avisos.length === 1
              ? "producto tiene una descripción distinta"
              : "productos tienen una descripción distinta"}{" "}
            a la de la base
          </p>
          <p className="mt-1 text-sm text-[#92400e]">
            El código coincide pero el nombre no. Revisa que sea el producto que
            esperas antes de aplicar.
          </p>
          <ul className="mt-2 flex flex-col gap-1 text-sm text-[#92400e]">
            {avisos.slice(0, 8).map((a) => (
              <li key={a.id}>
                <span className="font-mono">{a.codigo}</span> · base:{" "}
                <b>{a.nombre}</b> · archivo: <b>{a.descripcionDistinta}</b>
              </li>
            ))}
          </ul>
          {avisos.length > 8 && (
            <p className="mt-1 text-sm">y {numero(avisos.length - 8)} más</p>
          )}
        </div>
      )}

      {asignados.length > 0 && (
        <TablaCambios
          titulo={`Reciben clasificación en ${sede}`}
          filas={asignados}
          acento={acento}
        />
      )}

      {pierden.length > 0 && (
        <TablaCambios
          titulo="Dejan de ser infaltables"
          filas={pierden}
          acento={acento}
          alerta
        />
      )}

      {problemas.length > 0 && <ListaProblemas problemas={problemas} />}
    </section>
  );
}

function TablaCambios({
  titulo,
  filas,
  acento,
  alerta = false,
}: {
  titulo: string;
  filas: Asignado[];
  acento: string;
  alerta?: boolean;
}) {
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
              <th className="versalita px-4 py-2 text-left">Código</th>
              <th className="versalita px-4 py-2 text-left">Producto</th>
              <th className="versalita px-4 py-2 text-left">Cambio</th>
            </tr>
          </thead>
          <tbody>
            {filas.slice(0, 300).map((f) => (
              <tr
                key={f.id}
                className="border-b border-marca-borde last:border-b-0"
              >
                <td className="px-4 py-2 font-mono whitespace-nowrap">
                  {f.codigo}
                </td>
                <td className="px-4 py-2 text-marca-negro">
                  {f.nombre}
                  {f.descripcionDistinta && (
                    <span className="ml-2 text-xs text-[#92400e]">
                      · en el archivo: {f.descripcionDistinta}
                    </span>
                  )}
                </td>
                <td className="px-4 py-2 whitespace-nowrap">
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
        {filas.length > 300 && (
          <p className="px-4 py-2 text-sm text-marca-tenue">
            y {numero(filas.length - 300)} más, que también se aplican
          </p>
        )}
      </div>
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
