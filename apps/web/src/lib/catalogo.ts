import { createContext, useContext } from "react";
import type { Progreso } from "@/lib/api";
import type { Categoria, EstatusProducto, Producto, Subcategoria } from "@/lib/types";

export type EstadoCatalogo = "cargando" | "listo" | "error";

export type Catalogo = {
  /** Casa seleccionada; la comparten todas las pestañas. */
  sede: string;
  setSede: (sede: string) => void;

  estado: EstadoCatalogo;
  error: string | null;
  progreso: Progreso;

  productos: Producto[];
  estatus: EstatusProducto[];
  /** Categorías y subcategorías de la casa seleccionada, para comparar contra
   * lo que traiga un Excel (ninguna se descarga completa: van filtradas por
   * `sede`, como `productos`). */
  categorias: Categoria[];
  subcategorias: Subcategoria[];
  /** Códigos de estatus marcados como infaltables (B, D, F). */
  infaltables: Set<string>;

  /** Refleja en memoria lo que ya se guardó, sin volver a bajar el catálogo. */
  aplicarCambios: (
    cambios: {
      id: string;
      mnemotecnia?: string;
      estatus?: string;
      nombre?: string;
      categoria_codigo?: string;
      subcategoria_codigo?: string;
    }[]
  ) => void;
  /** Vuelve a descargar la casa actual, ignorando lo que haya en caché. */
  recargar: () => void;
};

export const ContextoCatalogo = createContext<Catalogo | null>(null);

export function useCatalogo(): Catalogo {
  const ctx = useContext(ContextoCatalogo);
  if (!ctx) {
    throw new Error("useCatalogo debe usarse dentro de <CatalogoProvider>");
  }
  return ctx;
}
