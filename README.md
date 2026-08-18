# SKUs App (monorepo)

Herramientas para que el personal de una distribuidora (varias sedes: FEBECA, COFERSA, SILLACA,
BEVAL, MUNDIAL DE PARTES) aprenda y gestione el catálogo de códigos de producto (SKUs). Backend
común: Supabase (Postgres + Auth + RLS).

## Apps

- **[apps/mobile](apps/mobile/README.md)** — app Android (Flutter) de estudio y memorización del
  catálogo: guía de estudio, modos de juego/quiz, panel de administración de usuarios. Ver también
  [apps/mobile/CLAUDE.md](apps/mobile/CLAUDE.md) y
  [apps/mobile/CONTEXTO_DESARROLLO.md](apps/mobile/CONTEXTO_DESARROLLO.md) para la historia y
  arquitectura completa.
- **[apps/web](apps/web/README.md)** — panel web para listar el catálogo cargado (búsqueda por
  nombre/código, filtros por casa/infaltables) y ver/editar la mnemotecnia de cada producto. En
  planeación, aún sin scaffold.

## Recursos compartidos (raíz, fuera de `apps/`)

- **`Data/`** — scripts Python de carga/reconciliación del catálogo hacia Supabase desde los Excel
  de cada casa. No versionado en git (información interna). Ver `Data/reglas_carga.md` para las
  reglas y precedentes de carga antes de escribir un script nuevo.
- **`PLAN_PRUEBA_NEON.md`** — evaluación técnica en curso (no decidida) de Neon como posible
  reemplazo de Supabase; afecta a ambas apps si se llegara a migrar.

Ambas apps comparten el mismo proyecto de Supabase — cualquier cambio de esquema (tablas, RLS)
afecta a las dos.
