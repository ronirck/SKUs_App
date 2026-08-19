import { useCatalogo } from "@/lib/catalogo";
import { SEDES } from "@/lib/types";
import { colorEmpresa } from "@/theme/marca";

/** Selector de casa del marco: lo comparten las dos pestañas. */
export default function SelectorCasa() {
  const { sede, setSede } = useCatalogo();
  const acento = colorEmpresa(sede);

  return (
    <label className="flex items-center gap-2">
      <span className="versalita">Casa</span>
      <span
        className="flex items-center gap-2 rounded-[10px] border border-marca-borde bg-white px-3 py-1.5 focus-within:border-marca-negro"
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
  );
}
