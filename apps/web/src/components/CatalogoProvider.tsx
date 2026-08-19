import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fetchAllProductos, fetchEstatusProducto, type Progreso } from "@/lib/api";
import { ContextoCatalogo, type EstadoCatalogo } from "@/lib/catalogo";
import { SEDES, type EstatusProducto, type Producto } from "@/lib/types";

/**
 * Dueño único del catálogo, montado por encima de las pestañas.
 *
 * La descarga arranca al abrir la app, no al entrar a la pestaña que muestra
 * la tabla: así, cuando el usuario llega a Mnemotecnias, los datos ya están.
 * Antes esto vivía dentro de la tabla y moría con ella, de modo que cambiar de
 * pestaña habría vuelto a descargar todo.
 *
 * El caché es por casa: volver a una ya descargada es inmediato.
 */
export default function CatalogoProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sede, setSede] = useState<string>(SEDES[0]);
  const [estado, setEstado] = useState<EstadoCatalogo>("cargando");
  const [error, setError] = useState<string | null>(null);
  const [progreso, setProgreso] = useState<Progreso>({
    cargadas: 0,
    total: null,
  });
  const [productos, setProductos] = useState<Producto[]>([]);
  const [estatus, setEstatus] = useState<EstatusProducto[]>([]);

  // El caché vive en un ref: cambia sin provocar renders y sobrevive a los
  // cambios de pestaña, que es justo lo que se busca.
  const cache = useRef(new Map<string, Producto[]>());
  const [recarga, setRecarga] = useState(0);

  useEffect(() => {
    let cancelado = false;

    async function cargar() {
      setError(null);

      const enCache = cache.current.get(sede);
      if (enCache) {
        setProductos(enCache);
        setProgreso({ cargadas: enCache.length, total: enCache.length });
        setEstado("listo");
        return;
      }

      setEstado("cargando");
      setProgreso({ cargadas: 0, total: null });
      setProductos([]);

      try {
        const [filas, estatusFilas] = await Promise.all([
          fetchAllProductos(sede, (p) => {
            if (!cancelado) setProgreso(p);
          }),
          fetchEstatusProducto(),
        ]);
        if (cancelado) return;

        cache.current.set(sede, filas);
        setProductos(filas);
        setEstatus(estatusFilas);
        setEstado("listo");
      } catch (err) {
        if (cancelado) return;
        setError((err as Error).message);
        setEstado("error");
      }
    }

    cargar();
    return () => {
      cancelado = true;
    };
  }, [sede, recarga]);

  const aplicarCambios = useCallback(
    (cambios: { id: string; mnemotecnia?: string; estatus?: string }[]) => {
      if (cambios.length === 0) return;
      const porId = new Map(cambios.map((c) => [c.id, c]));

      setProductos((prev) => {
        const siguiente = prev.map((p) => {
          const cambio = porId.get(p.id);
          if (!cambio) return p;
          return {
            ...p,
            ...(cambio.mnemotecnia !== undefined
              ? { mnemotecnia: cambio.mnemotecnia }
              : {}),
            ...(cambio.estatus !== undefined ? { estatus: cambio.estatus } : {}),
          };
        });
        // El caché tiene que quedar igual que el estado: si no, cambiar de casa
        // y volver mostraría los valores viejos.
        cache.current.set(sede, siguiente);
        return siguiente;
      });
    },
    [sede]
  );

  const recargar = useCallback(() => {
    cache.current.delete(sede);
    setRecarga((n) => n + 1);
  }, [sede]);

  const infaltables = useMemo(
    () => new Set(estatus.filter((e) => e.es_infaltable).map((e) => e.codigo)),
    [estatus]
  );

  const valor = useMemo(
    () => ({
      sede,
      setSede,
      estado,
      error,
      progreso,
      productos,
      estatus,
      infaltables,
      aplicarCambios,
      recargar,
    }),
    [
      sede,
      estado,
      error,
      progreso,
      productos,
      estatus,
      infaltables,
      aplicarCambios,
      recargar,
    ]
  );

  return (
    <ContextoCatalogo.Provider value={valor}>
      {children}
    </ContextoCatalogo.Provider>
  );
}
