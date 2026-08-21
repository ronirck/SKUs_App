export const SEDES = [
  "FEBECA",
  "SILLACA",
  "BEVAL",
  "COFERSA",
  "MUNDIAL DE PARTES",
] as const;

export type Sede = (typeof SEDES)[number];

export type Producto = {
  id: string;
  sede: string;
  categoria_codigo: string;
  subcategoria_codigo: string;
  codigo: string;
  codigo_completo: string | null;
  nombre: string;
  marca: string;
  mnemotecnia: string | null;
  imagen_url: string | null;
  estatus: string;
};

export type EstatusProducto = {
  codigo: string;
  es_infaltable: boolean;
};

export type Categoria = {
  codigo: string;
  nombre: string;
  sede: string;
};

export type Subcategoria = {
  codigo: string;
  categoria_codigo: string;
  nombre: string;
  sede: string;
};
