/**
 * Paleta oficial de Grupo Mayoreo.
 *
 * Fuente autoritativa: la pantonera del grupo (`formato-mayoreo/assets/`), que confirma
 * estos hex. Regla que define todo el sistema: **base en escala de grises + color vivo
 * solo como acento por empresa**. El color identifica casas, no decora.
 *
 * Estos mismos valores están replicados en `src/index.css` como tokens `@theme` de
 * Tailwind; si cambia uno hay que tocar los dos.
 */
export const MARCA = {
  negro: "#1d1d1b",
  gris: "#c6c6c6",
  grisClaro: "#f2f2f1",
  fondo: "#fafafa",
  blanco: "#ffffff",
  textoSecundario: "#6b6b6b",
  textoTenue: "#9a9a9a",
  borde: "#e5e5e5",
  botonGris: "#ececeb",
  botonGrisBorde: "#d8d8d6",
  teal: "#00a885",
  error: "#dc2626",
  advertencia: "#d97706",
} as const;

/**
 * Acento por empresa. Las claves son los valores de `productos.sede` tal como vienen de
 * Supabase (ver `SEDES` en `@/lib/types`); "MUNDIAL DE PARTES" es Mundipartes.
 *
 * Ojo: **los colores se repiten entre empresas** — cian es Febeca *y* Cofersa, lima es
 * Beval *y* Mundipartes. Por eso el color nunca puede ser el único identificador: siempre
 * punto de color + nombre en texto (ver `EtiquetaEmpresa`).
 */
export const COLOR_EMPRESA: Record<string, string> = {
  FEBECA: "#009ee3",
  COFERSA: "#009ee3",
  BEVAL: "#ccdb2a",
  MUNDIPARTES: "#ccdb2a",
  "MUNDIAL DE PARTES": "#ccdb2a",
  SILLACA: "#e5007d",
  PRISMA: MARCA.gris,
  "GRUPO MAYOREO": MARCA.gris,
};

/** Acento de una empresa; gris del grupo si no se reconoce. */
export function colorEmpresa(empresa: string | null | undefined): string {
  if (!empresa) return MARCA.gris;
  return COLOR_EMPRESA[empresa.trim().toUpperCase()] ?? MARCA.gris;
}

/**
 * Versión suave de un color: el mismo acento al 14 % de opacidad, para fondos de chips e
 * indicadores. No inventar tonos pastel a mano — siempre derivar del acento.
 */
export function suave(hex: string, alpha = 0.14): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
