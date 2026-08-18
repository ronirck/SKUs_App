import { colorEmpresa } from "@/theme/marca";

/**
 * Patrón canónico para nombrar una casa: punto de color de 10 px + nombre en texto,
 * nunca uno sin el otro. Los acentos se repiten entre empresas (cian es Febeca y
 * Cofersa, lima es Beval y Mundipartes), así que el color por sí solo no identifica
 * nada. Sin empresa se muestra "—" en gris tenue, no un punto sin color.
 */
export default function EtiquetaEmpresa({
  empresa,
  className = "",
}: {
  empresa: string | null | undefined;
  className?: string;
}) {
  if (!empresa) {
    return <span className="text-marca-tenue">—</span>;
  }

  return (
    <span
      className={`inline-flex items-center gap-2 text-sm text-marca-negro ${className}`}
    >
      <span
        aria-hidden
        className="h-2.5 w-2.5 shrink-0 rounded-full"
        style={{ backgroundColor: colorEmpresa(empresa) }}
      />
      {empresa}
    </span>
  );
}
