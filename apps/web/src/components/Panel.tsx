import { useState } from "react";
import ActualizarClasificacion from "@/components/ActualizarClasificacion";
import EtiquetaEmpresa from "@/components/EtiquetaEmpresa";
import ProductosTable from "@/components/ProductosTable";
import SelectorCasa from "@/components/SelectorCasa";
import { useCatalogo } from "@/lib/catalogo";

type Pestana = "clasificacion" | "mnemotecnias";

const PESTANAS: { id: Pestana; etiqueta: string; descripcion: string }[] = [
  {
    id: "clasificacion",
    etiqueta: "Clasificación",
    descripcion: "Actualiza desde un Excel qué productos son infaltables.",
  },
  {
    id: "mnemotecnias",
    etiqueta: "Mnemotecnias",
    descripcion: "Consulta los códigos de la casa y edita su mnemotecnia.",
  },
];

/**
 * Marco con pestañas. La clasificación abre primero por ser el trabajo
 * principal; el catálogo se descarga aparte, en `CatalogoProvider`, así que
 * cambiar de pestaña no vuelve a pedir nada.
 */
export default function Panel() {
  const [activa, setActiva] = useState<Pestana>("clasificacion");
  const { sede, estado, progreso } = useCatalogo();
  const actual = PESTANAS.find((p) => p.id === activa)!;

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-6 py-8">
      <div className="animar-entrada flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-[1.6rem] font-bold text-marca-negro">
            Catálogo de productos
          </h1>
          <p className="mt-1 text-sm text-marca-texto">{actual.descripcion}</p>
        </div>
        <div className="flex items-center gap-4 pb-1">
          {/* Señal discreta de que el catálogo sigue bajando: el trabajo de
              clasificación no lo necesita, así que no vale la pena bloquear. */}
          {estado === "cargando" && (
            <span className="text-sm text-marca-tenue">
              Cargando catálogo
              {progreso.total
                ? ` · ${Math.round((progreso.cargadas / progreso.total) * 100)} %`
                : "…"}
            </span>
          )}
          <EtiquetaEmpresa empresa={sede} className="font-medium" />
        </div>
      </div>

      <div
        className="animar-entrada flex flex-wrap items-end gap-4 border-b border-marca-borde"
        style={{ animationDelay: "60ms" }}
      >
        <nav className="flex gap-1" role="tablist">
          {PESTANAS.map((p) => {
            const seleccionada = p.id === activa;
            return (
              <button
                key={p.id}
                role="tab"
                aria-selected={seleccionada}
                className={
                  "-mb-px border-b-2 px-4 py-2.5 text-sm font-semibold transition-colors " +
                  (seleccionada
                    ? "border-marca-negro text-marca-negro"
                    : "border-transparent text-marca-texto hover:text-marca-negro")
                }
                onClick={() => setActiva(p.id)}
              >
                {p.etiqueta}
              </button>
            );
          })}
        </nav>
        <div className="ml-auto pb-2">
          <SelectorCasa />
        </div>
      </div>

      {activa === "clasificacion" ? <ActualizarClasificacion /> : <ProductosTable />}
    </div>
  );
}
