// La librería se importa de forma dinámica, dentro de la función: son ~70 KB
// que casi ninguna visita usa, y así viajan en su propio chunk que solo se
// descarga cuando alguien elige un archivo, en vez de pesar en el arranque.
//
// Se usa `readSheet` y no el export por defecto: en la v9 el default devuelve
// `Sheet[]` ({ sheet, data }) y aquí solo interesan las filas de la primera
// hoja. El paquete además solo expone subrutas, no la raíz.

/** El código del catálogo va en formato `xx-xx-xxx`, todo dígitos. */
export const FORMATO_CODIGO = /^\d{2}-\d{2}-\d{3}$/;

export type FilaExcel = {
  /** Número de fila en el Excel (contando el encabezado), para poder señalarla. */
  fila: number;
  codigo: string;
  mnemotecnia: string;
};

export type ProblemaExcel = {
  fila: number;
  codigo: string;
  motivo: string;
};

export type LecturaExcel = {
  filas: FilaExcel[];
  problemas: ProblemaExcel[];
};

/** Quita acentos y espacios para comparar encabezados sin depender de cómo se escribieron. */
function normalizar(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase();
}

function comoTexto(valor: unknown): string {
  if (valor === null || valor === undefined) return "";
  if (valor instanceof Date) return valor.toISOString();
  return String(valor).trim();
}

/**
 * Lee un Excel de dos columnas —"Código" y "Mnemotecnia"— y devuelve las filas
 * utilizables junto con los problemas encontrados, para poder mostrarle al
 * usuario qué se va a aplicar y qué se va a ignorar antes de tocar nada.
 *
 * No consulta la base de datos: aquí solo se valida el formato del archivo.
 */
export async function leerMnemotecniasDeExcel(
  archivo: File
): Promise<LecturaExcel> {
  const { readSheet } = await import("read-excel-file/browser");
  const hoja = await readSheet(archivo);

  if (hoja.length === 0) {
    throw new Error("El archivo está vacío");
  }

  const encabezado = hoja[0].map((c) => normalizar(comoTexto(c)));
  const iCodigo = encabezado.indexOf("codigo");
  const iMnemotecnia = encabezado.indexOf("mnemotecnia");

  if (iCodigo === -1 || iMnemotecnia === -1) {
    throw new Error(
      'El Excel debe tener dos columnas con los títulos "Código" y "Mnemotecnia" en la primera fila'
    );
  }

  const filas: FilaExcel[] = [];
  const problemas: ProblemaExcel[] = [];
  const vistos = new Map<string, number>();

  for (let i = 1; i < hoja.length; i++) {
    const numeroFila = i + 1; // 1-indexado y contando el encabezado, como lo ve el usuario
    const codigo = comoTexto(hoja[i][iCodigo]);
    const mnemotecnia = comoTexto(hoja[i][iMnemotecnia]);

    if (!codigo && !mnemotecnia) continue; // fila vacía: no es un problema

    if (!FORMATO_CODIGO.test(codigo)) {
      problemas.push({
        fila: numeroFila,
        codigo: codigo || "(vacío)",
        motivo: "El código no tiene el formato xx-xx-xxx",
      });
      continue;
    }

    if (!mnemotecnia) {
      problemas.push({
        fila: numeroFila,
        codigo,
        // Se ignora en vez de borrar: un campo vacío casi nunca significa
        // "bórrame la mnemotecnia que ya tenía".
        motivo: "Sin mnemotecnia, se ignora",
      });
      continue;
    }

    const filaPrevia = vistos.get(codigo);
    if (filaPrevia !== undefined) {
      problemas.push({
        fila: numeroFila,
        codigo,
        motivo: `Código repetido (ya venía en la fila ${filaPrevia}), se usa el último`,
      });
      const indice = filas.findIndex((f) => f.codigo === codigo);
      filas[indice] = { fila: numeroFila, codigo, mnemotecnia };
      vistos.set(codigo, numeroFila);
      continue;
    }

    vistos.set(codigo, numeroFila);
    filas.push({ fila: numeroFila, codigo, mnemotecnia });
  }

  return { filas, problemas };
}

// ─── Clasificación (estatus) ────────────────────────────────────────────────

export type FilaClasificacion = {
  fila: number;
  codigo: string;
  /** Vacío cuando el archivo no trae columna de clasificación (caso Febeca). */
  estatus: string;
  /** Estos tres solo se usan para avisar de diferencias con la base; nunca se
   * guardan directo — es la revisión la que decide si se aplican. */
  descripcion: string;
  categoria: string;
  subcategoria: string;
};

export type LecturaClasificacion = {
  filas: FilaClasificacion[];
  problemas: ProblemaExcel[];
  /** Si el archivo trae la columna, se usa; si no, hay que elegir un estatus único. */
  traeColumnaEstatus: boolean;
  traeColumnaCategoria: boolean;
  traeColumnaSubcategoria: boolean;
};

/** Encabezados equivalentes: los archivos vienen como vienen. */
const ALIAS_CODIGO = ["codigo"];
const ALIAS_ESTATUS = ["estatus", "bdf", "clasificacion", "status", "estado"];
const ALIAS_DESCRIPCION = [
  "descripcion",
  "nombre",
  "nombre articulo",
  "nombre del articulo",
  "producto",
  "articulo",
];
const ALIAS_CATEGORIA = ["categoria"];
const ALIAS_SUBCATEGORIA = ["sub-categoria", "subcategoria", "sub categoria"];

function buscarColumna(encabezado: string[], alias: string[]): number {
  return encabezado.findIndex((h) => alias.includes(h));
}

/**
 * Lee un Excel de clasificación. Solo `Código` es obligatorio: la columna de
 * estatus puede faltar (entonces se aplica uno solo a todo el archivo) y la
 * descripción es opcional, únicamente para avisar de diferencias con la base.
 */
export async function leerClasificacionesDeExcel(
  archivo: File
): Promise<LecturaClasificacion> {
  const { readSheet } = await import("read-excel-file/browser");
  const hoja = await readSheet(archivo);

  if (hoja.length === 0) throw new Error("El archivo está vacío");

  const encabezado = hoja[0].map((c) => normalizar(comoTexto(c)));
  const iCodigo = buscarColumna(encabezado, ALIAS_CODIGO);
  const iEstatus = buscarColumna(encabezado, ALIAS_ESTATUS);
  const iDescripcion = buscarColumna(encabezado, ALIAS_DESCRIPCION);
  const iCategoria = buscarColumna(encabezado, ALIAS_CATEGORIA);
  const iSubcategoria = buscarColumna(encabezado, ALIAS_SUBCATEGORIA);

  if (iCodigo === -1) {
    throw new Error(
      'El Excel debe tener una columna "Código" en la primera fila'
    );
  }

  const filas: FilaClasificacion[] = [];
  const problemas: ProblemaExcel[] = [];
  const vistos = new Map<string, number>();

  for (let i = 1; i < hoja.length; i++) {
    const numeroFila = i + 1;
    const codigo = comoTexto(hoja[i][iCodigo]);
    const estatus =
      iEstatus === -1 ? "" : comoTexto(hoja[i][iEstatus]).toUpperCase();
    const descripcion =
      iDescripcion === -1 ? "" : comoTexto(hoja[i][iDescripcion]);
    const categoria =
      iCategoria === -1 ? "" : comoTexto(hoja[i][iCategoria]);
    const subcategoria =
      iSubcategoria === -1 ? "" : comoTexto(hoja[i][iSubcategoria]);

    if (!codigo && !estatus && !descripcion && !categoria && !subcategoria)
      continue;

    if (!FORMATO_CODIGO.test(codigo)) {
      problemas.push({
        fila: numeroFila,
        codigo: codigo || "(vacío)",
        motivo: "El código no tiene el formato xx-xx-xxx",
      });
      continue;
    }

    const fila: FilaClasificacion = {
      fila: numeroFila,
      codigo,
      estatus,
      descripcion,
      categoria,
      subcategoria,
    };

    const filaPrevia = vistos.get(codigo);
    if (filaPrevia !== undefined) {
      problemas.push({
        fila: numeroFila,
        codigo,
        motivo: `Código repetido (ya venía en la fila ${filaPrevia}), se usa el último`,
      });
      const indice = filas.findIndex((f) => f.codigo === codigo);
      filas[indice] = fila;
      vistos.set(codigo, numeroFila);
      continue;
    }

    vistos.set(codigo, numeroFila);
    filas.push(fila);
  }

  return {
    filas,
    problemas,
    traeColumnaEstatus: iEstatus !== -1,
    traeColumnaCategoria: iCategoria !== -1,
    traeColumnaSubcategoria: iSubcategoria !== -1,
  };
}
