import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  fetchAllProductos,
  fetchCategorias,
  fetchEstatusProducto,
  fetchSubcategorias,
  type Progreso,
} from "@/lib/api";
import { ContextoCatalogo, type EstadoCatalogo } from "@/lib/catalogo";
import {
  SEDES,
  type Categoria,
  type EstatusProducto,
  type Producto,
  type Subcategoria,
} from "@/lib/types";

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
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [subcategorias, setSubcategorias] = useState<Subcategoria[]>([]);

  // El caché vive en un ref: cambia sin provocar renders y sobrevive a los
  // cambios de pestaña, que es justo lo que se busca.
  const cache = useRef(new Map<string, Producto[]>());
  const cacheCategorias = useRef(new Map<string, Categoria[]>());
  const cacheSubcategorias = useRef(new Map<string, Subcategoria[]>());
  const [recarga, setRecarga] = useState(0);

  useEffect(() => {
    let cancelado = false;

    async function cargar() {
      setError(null);

      const enCache = cache.current.get(sede);
      if (enCache) {
        setProductos(enCache);
        setCategorias(cacheCategorias.current.get(sede) ?? []);
        setSubcategorias(cacheSubcategorias.current.get(sede) ?? []);
        setProgreso({ cargadas: enCache.length, total: enCache.length });
        setEstado("listo");
        return;
      }

      setEstado("cargando");
      setProgreso({ cargadas: 0, total: null });
      setProductos([]);

      try {
        const [filas, estatusFilas, categoriasFilas, subcategoriasFilas] =
          await Promise.all([
            fetchAllProductos(sede, (p) => {
              if (!cancelado) setProgreso(p);
            }),
            fetchEstatusProducto(),
            fetchCategorias(sede),
            fetchSubcategorias(sede),
          ]);
        if (cancelado) return;

        cache.current.set(sede, filas);
        cacheCategorias.current.set(sede, categoriasFilas);
        cacheSubcategorias.current.set(sede, subcategoriasFilas);
        setProductos(filas);
        setEstatus(estatusFilas);
        setCategorias(categoriasFilas);
        setSubcategorias(subcategoriasFilas);
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
    (
      cambios: {
        id: string;
        mnemotecnia?: string;
        estatus?: string;
        nombre?: string;
        categoria_codigo?: string;
        subcategoria_codigo?: string;
      }[]
    ) => {
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
            ...(cambio.nombre !== undefined ? { nombre: cambio.nombre } : {}),
            ...(cambio.categoria_codigo !== undefined
              ? { categoria_codigo: cambio.categoria_codigo }
              : {}),
            ...(cambio.subcategoria_codigo !== undefined
              ? { subcategoria_codigo: cambio.subcategoria_codigo }
              : {}),
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
    cacheCategorias.current.delete(sede);
    cacheSubcategorias.current.delete(sede);
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
      categorias,
      subcategorias,
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
      categorias,
      subcategorias,
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
