class DemoCategoria {
  const DemoCategoria(this.codigo, this.nombre, this.mnemotecnia);

  final String codigo;
  final String nombre;
  final String mnemotecnia;
}

class DemoSubcategoria {
  const DemoSubcategoria(this.categoriaCodigo, this.codigo, this.nombre, this.mnemotecnia);

  final String categoriaCodigo;
  final String codigo;
  final String nombre;
  final String mnemotecnia;
}

class DemoProducto {
  const DemoProducto(
    this.categoriaCodigo,
    this.subcategoriaCodigo,
    this.codigo,
    this.nombre,
    this.marca,
  );

  final String categoriaCodigo;
  final String subcategoriaCodigo;
  final String codigo;
  final String nombre;
  final String marca;

  String get codigoCompleto => '$categoriaCodigo-$subcategoriaCodigo-$codigo';
}

/// Catálogo ficticio para la demo de onboarding — nunca toca Supabase (un
/// usuario 'pendiente' no puede leer el catálogo real, RLS lo bloquea) ni
/// persiste nada; se recrea en memoria cada vez que arranca la demo.
const demoCategorias = [
  DemoCategoria('01', 'Tornillería', 'Todo lo que rosca y aprieta'),
  DemoCategoria('02', 'Cables y Conectores', 'La parte que casi nunca se ve'),
  DemoCategoria('03', 'Pilas y Baterías', 'Energía portátil'),
  DemoCategoria('04', 'Cintas Adhesivas', 'Pega, sella o aísla'),
  DemoCategoria('05', 'Herramientas Manuales', 'Sin motor, sin batería'),
];

const demoSubcategorias = [
  DemoSubcategoria('01', '01', 'Tornillos Phillips', 'Cabeza en cruz'),
  DemoSubcategoria('01', '02', 'Tornillos Planos', 'Cabeza ranurada'),
  DemoSubcategoria('02', '01', 'Cables USB', 'Carga y datos'),
  DemoSubcategoria('02', '02', 'Conectores RJ45', 'Redes cableadas'),
  DemoSubcategoria('03', '01', 'Pilas AA', 'El tamaño más común'),
  DemoSubcategoria('03', '02', 'Baterías Recargables', 'Se reusan cientos de veces'),
  DemoSubcategoria('04', '01', 'Cinta Doble Cara', 'Pega dos superficies'),
  DemoSubcategoria('04', '02', 'Cinta Aislante', 'Aísla conexiones eléctricas'),
  DemoSubcategoria('05', '01', 'Desarmadores', 'Uno por cada tipo de tornillo'),
  DemoSubcategoria('05', '02', 'Llaves Ajustables', 'Se adaptan a varias medidas'),
];

const demoProductos = [
  DemoProducto('01', '01', '001', 'Tornillo Phillips 1/2"', 'Marca Genérica A'),
  DemoProducto('01', '01', '002', 'Tornillo Phillips 1"', 'Marca Genérica A'),
  DemoProducto('01', '01', '003', 'Tornillo Phillips 2"', 'Marca Genérica B'),
  DemoProducto('01', '02', '001', 'Tornillo Plano 3/4"', 'Marca Genérica A'),
  DemoProducto('01', '02', '002', 'Tornillo Plano 1"', 'Marca Genérica B'),
  DemoProducto('02', '01', '001', 'Cable USB-A a USB-C 1m', 'Marca Genérica B'),
  DemoProducto('02', '01', '002', 'Cable USB-A a Micro-USB 1m', 'Marca Genérica A'),
  DemoProducto('02', '02', '001', 'Conector RJ45 Cat5e', 'Marca Genérica A'),
  DemoProducto('02', '02', '002', 'Conector RJ45 Cat6', 'Marca Genérica B'),
  DemoProducto('03', '01', '001', 'Pila AA Alcalina', 'Marca Genérica A'),
  DemoProducto('03', '01', '002', 'Pila AA Zinc-Carbono', 'Marca Genérica B'),
  DemoProducto('03', '02', '001', 'Batería AA Recargable 2000mAh', 'Marca Genérica A'),
  DemoProducto('04', '01', '001', 'Cinta Doble Cara 18mm', 'Marca Genérica B'),
  DemoProducto('04', '02', '001', 'Cinta Aislante Negra', 'Marca Genérica A'),
  DemoProducto('04', '02', '002', 'Cinta Aislante Roja', 'Marca Genérica B'),
  DemoProducto('05', '01', '001', 'Desarmador Phillips #2', 'Marca Genérica A'),
  DemoProducto('05', '01', '002', 'Desarmador Plano 1/4"', 'Marca Genérica B'),
  DemoProducto('05', '02', '001', 'Llave Ajustable 8"', 'Marca Genérica A'),
];
