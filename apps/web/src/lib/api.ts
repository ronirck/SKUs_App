import { supabase } from "@/lib/supabaseClient";
import type { EstatusProducto, Producto } from "@/lib/types";

// Supabase trunca a 1000 filas por consulta sin avisar — hay que paginar
// siempre en tablas de catálogo (misma regla que sigue la app móvil).
const PAGE_SIZE = 1000;

const COLUMNAS =
  "id, sede, categoria_codigo, subcategoria_codigo, codigo, codigo_completo, nombre, marca, mnemotecnia, imagen_url, estatus";

/** Avance de la descarga: filas ya traídas y total de la casa (null si aún no se sabe). */
export type Progreso = { cargadas: number; total: number | null };

/**
 * Cuántas páginas se piden a la vez. Cada petición tarda ~1,2 s casi toda en
 * latencia, no en transferencia (con gzip la página son ~75 KB), así que
 * pedirlas en serie desperdicia el tiempo de ida y vuelta: medido, las 7
 * páginas de FEBECA bajan de 9,2 s a 2,3 s. El tope evita abrir una decena de
 * conexiones de golpe contra Supabase.
 */
const PAGINAS_EN_PARALELO = 6;

async function pedirPagina(
  sede: string,
  from: number,
  conConteo: boolean
): Promise<{ filas: Producto[]; total: number | null }> {
  const { data, error, count } = await supabase
    .from("productos")
    .select(COLUMNAS, conConteo ? { count: "exact" } : {})
    .eq("sede", sede)
    .order("id", { ascending: true })
    .range(from, from + PAGE_SIZE - 1);

  if (error) throw error;
  return {
    filas: (data ?? []) as Producto[],
    total: typeof count === "number" ? count : null,
  };
}

export async function fetchAllProductos(
  sede: string,
  onProgress?: (progreso: Progreso) => void
): Promise<Producto[]> {
  // La primera página trae además el conteo exacto: con él se sabe de una vez
  // cuántas faltan, y el resto se puede pedir en paralelo en lugar de ir
  // descubriendo el final página por página.
  const primera = await pedirPagina(sede, 0, true);
  let cargadas = primera.filas.length;
  const total = primera.total;
  onProgress?.({ cargadas, total });

  if (total === null) {
    // Sin conteo no se puede repartir el trabajo: se cae al recorrido secuencial.
    const rows = [...primera.filas];
    let from = PAGE_SIZE;
    while (rows.length >= from) {
      const { filas } = await pedirPagina(sede, from, false);
      if (filas.length === 0) break;
      rows.push(...filas);
      onProgress?.({ cargadas: rows.length, total: null });
      if (filas.length < PAGE_SIZE) break;
      from += PAGE_SIZE;
    }
    onProgress?.({ cargadas: rows.length, total: rows.length });
    return rows;
  }

  const inicios: number[] = [];
  for (let from = PAGE_SIZE; from < total; from += PAGE_SIZE) inicios.push(from);

  // Las páginas se guardan por índice y se unen al final: llegan desordenadas,
  // pero el catálogo debe quedar en el mismo orden que pidió el `order by id`.
  const porPagina: Producto[][] = new Array(inicios.length);

  for (let i = 0; i < inicios.length; i += PAGINAS_EN_PARALELO) {
    const tanda = inicios.slice(i, i + PAGINAS_EN_PARALELO);
    await Promise.all(
      tanda.map(async (from, j) => {
        const { filas } = await pedirPagina(sede, from, false);
        porPagina[i + j] = filas;
        cargadas += filas.length;
        onProgress?.({ cargadas, total });
      })
    );
  }

  const rows = [...primera.filas, ...porPagina.flat()];
  onProgress?.({ cargadas: rows.length, total });

  return rows;
}

export async function fetchEstatusProducto(): Promise<EstatusProducto[]> {
  const { data, error } = await supabase
    .from("estatus_producto")
    .select("codigo, es_infaltable");

  if (error) throw error;
  return data as EstatusProducto[];
}

export type ResultadoLote = {
  aplicadas: number;
  fallidas: { id: string; codigo: string; motivo: string }[];
};

/**
 * Aplica varias mnemotecnias reutilizando `updateMnemotecnia`, que ya verifica
 * que la fila haya vuelto. Va en tandas cortas y no en paralelo total: con
 * miles de filas, dispararlo todo de golpe satura la conexión y Supabase
 * empieza a rechazar. Un fallo no aborta el resto: se reporta al final.
 */
export async function updateMnemotecniasEnLote(
  items: { id: string; codigo: string; mnemotecnia: string }[],
  onProgress?: (hechas: number, total: number) => void
): Promise<ResultadoLote> {
  const TANDA = 5;
  const fallidas: ResultadoLote["fallidas"] = [];
  let aplicadas = 0;
  let hechas = 0;

  for (let i = 0; i < items.length; i += TANDA) {
    const tanda = items.slice(i, i + TANDA);
    await Promise.all(
      tanda.map(async (item) => {
        try {
          await updateMnemotecnia(item.id, item.mnemotecnia);
          aplicadas++;
        } catch (err) {
          fallidas.push({
            id: item.id,
            codigo: item.codigo,
            motivo: (err as Error).message,
          });
        } finally {
          hechas++;
          onProgress?.(hechas, items.length);
        }
      })
    );
  }

  return { aplicadas, fallidas };
}

export async function updateMnemotecnia(
  id: string,
  value: string
): Promise<{ id: string; mnemotecnia: string | null }> {
  const mnemotecnia = value.trim() === "" ? null : value;

  const { data, error } = await supabase
    .from("productos")
    .update({ mnemotecnia })
    .eq("id", id)
    .select("id, mnemotecnia");

  if (error) throw error;

  // Verificar que la fila realmente vino de vuelta: con RLS + GRANT acotado a
  // la columna mnemotecnia no debería haber no-ops silenciosos, pero es una
  // verificación barata y evita reportar éxito si el id no existía.
  if (!data || data.length === 0) {
    throw new Error("No se encontró el producto");
  }

  return data[0] as { id: string; mnemotecnia: string | null };
}
