import { useEffect, useRef, useState } from "react";
import { suave } from "@/theme/marca";

const EXTENSIONES = [".xlsx", ".xls"];

/**
 * Zona para soltar o elegir un archivo. Sigue siendo un `<input type="file">`
 * por debajo: arrastrar es la vía cómoda, pero el clic y el teclado tienen que
 * funcionar igual para quien no arrastra.
 */
export default function ZonaDeArchivo({
  acento,
  archivo,
  detalle,
  ocupado = false,
  onArchivo,
}: {
  acento: string;
  /** Nombre del archivo ya cargado, si lo hay. */
  archivo: string | null;
  /** Línea de contexto bajo el nombre, p. ej. cuántas filas trae. */
  detalle?: string | null;
  ocupado?: boolean;
  onArchivo: (archivo: File) => void;
}) {
  const [encima, setEncima] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  // Arrastrar sobre un hijo dispara dragleave del padre; contar las entradas
  // evita que el resaltado parpadee al pasar por encima del texto.
  const profundidad = useRef(0);

  // Si el archivo cae fuera de la zona, el navegador lo abre y se pierde la
  // página. Anularlo en toda la ventana evita ese susto.
  useEffect(() => {
    const anular = (e: DragEvent) => e.preventDefault();
    window.addEventListener("dragover", anular);
    window.addEventListener("drop", anular);
    return () => {
      window.removeEventListener("dragover", anular);
      window.removeEventListener("drop", anular);
    };
  }, []);

  function recibir(archivo: File | undefined) {
    if (!archivo) return;
    const nombre = archivo.name.toLowerCase();
    if (!EXTENSIONES.some((e) => nombre.endsWith(e))) {
      setError(`"${archivo.name}" no es un Excel. Usa un archivo .xlsx o .xls.`);
      return;
    }
    setError(null);
    onArchivo(archivo);
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept={EXTENSIONES.join(",")}
        className="hidden"
        onChange={(e) => {
          recibir(e.target.files?.[0]);
          e.target.value = "";
        }}
      />

      <div
        role="button"
        tabIndex={0}
        aria-label="Elegir o arrastrar el archivo de Excel"
        aria-busy={ocupado}
        className={
          "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors " +
          (encima ? "" : "border-marca-borde bg-marca-fondo hover:bg-white")
        }
        style={
          encima
            ? { borderColor: acento, backgroundColor: suave(acento) }
            : undefined
        }
        onClick={() => !ocupado && inputRef.current?.click()}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !ocupado) {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragEnter={(e) => {
          e.preventDefault();
          profundidad.current += 1;
          setEncima(true);
        }}
        onDragOver={(e) => e.preventDefault()}
        onDragLeave={(e) => {
          e.preventDefault();
          profundidad.current -= 1;
          if (profundidad.current <= 0) setEncima(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          profundidad.current = 0;
          setEncima(false);
          if (!ocupado) recibir(e.dataTransfer.files?.[0]);
        }}
      >
        <IconoHoja acento={encima ? acento : "#9a9a9a"} />

        {archivo ? (
          <>
            <p className="text-sm font-semibold text-marca-negro">{archivo}</p>
            {detalle && <p className="text-sm text-marca-texto">{detalle}</p>}
            <p className="text-sm text-marca-tenue">
              Arrastra otro archivo o haz clic para cambiarlo
            </p>
          </>
        ) : (
          <>
            <p className="text-sm font-semibold text-marca-negro">
              {ocupado ? "Leyendo el archivo…" : "Arrastra el Excel aquí"}
            </p>
            <p className="text-sm text-marca-texto">
              o haz clic para buscarlo en tu computadora
            </p>
            <p className="text-sm text-marca-tenue">Archivos .xlsx o .xls</p>
          </>
        )}
      </div>

      {error && (
        <p className="mt-3 rounded-[10px] border border-[#fecaca] bg-[#fef2f2] px-4 py-3 text-sm text-[#b91c1c]">
          {error}
        </p>
      )}
    </div>
  );
}

function IconoHoja({ acento }: { acento: string }) {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      className="h-8 w-8"
      fill="none"
      stroke={acento}
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5" />
      <path d="M12 12v6" />
      <path d="m9 15 3-3 3 3" />
    </svg>
  );
}
