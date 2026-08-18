import logoMayoreo from "@/assets/logo-mayoreo.png";

/**
 * Cintillo institucional: logo del grupo (28 px, monocromo — nunca recolorear) más el
 * nombre "Grupo Mayoreo", ya que en este panel el contexto no lo hace obvio.
 *
 * El logo se importa desde `src/assets/` en vez de servirse desde `public/`: en este
 * repo, accedido desde WSL sobre `/mnt/c/...`, `copyFileSync` da EPERM y `vite build`
 * falla al copiar `public/`. Importado, rollup lo emite y el build pasa.
 */
export default function Encabezado({
  correo,
  alSalir,
}: {
  correo: string;
  alSalir: () => void;
}) {
  return (
    <header className="sticky top-0 z-10 border-b border-marca-borde bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center gap-3 px-6">
        <img
          src={logoMayoreo}
          alt="Grupo Mayoreo"
          className="h-7 w-auto"
          width={28}
          height={28}
        />
        <span className="versalita">Grupo Mayoreo</span>
        <span aria-hidden className="h-5 w-px bg-marca-borde" />
        <span className="text-sm font-semibold text-marca-negro">
          Catálogo de productos
        </span>

        <div className="ml-auto flex items-center gap-3">
          <span className="hidden text-sm text-marca-texto sm:inline">{correo}</span>
          <button
            className="rounded-[10px] border border-marca-boton-borde bg-white px-3 py-1.5 text-xs font-semibold text-marca-negro hover:bg-marca-boton"
            onClick={alSalir}
          >
            Salir
          </button>
        </div>
      </div>
    </header>
  );
}
