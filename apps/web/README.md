# SKUs App — Web (panel de catálogo y mnemotecnias)

Panel interno (Vite + React, SPA) para listar el catálogo de productos cargado en Supabase y
ver/editar la mnemotecnia de cada producto. Comparte el mismo backend Supabase que
`apps/mobile/` — mismas tablas (`categorias`, `subcategorias`, `productos`, `estatus_producto`);
ver `apps/mobile/CLAUDE.md` (sección "Database schema notes") para las particularidades del
esquema.

## Cómo levantarlo

```bash
cd apps/web
npm install        # solo la primera vez / cuando cambien las dependencias
npm run dev
```

Abre http://localhost:5173. La tabla carga el catálogo de la casa seleccionada (dropdown),
con buscador por nombre/código, filtro "solo infaltables", y edición de mnemotecnia en línea
(botón "Editar" → "Guardar").

### Configuración

`.env.local` (gitignored) ya está creado con las credenciales reales del proyecto de Supabase —
no hace falta tocarlo para correr en local. Si necesitas recrearlo, usa `.env.local.example`
como plantilla:

- `VITE_SUPABASE_URL` — mismo proyecto Supabase que `apps/mobile`.
- `VITE_SUPABASE_ANON_KEY` — la anon key pública (misma que usa `apps/mobile/env.json`). Vite
  expone cualquier variable con prefijo `VITE_` al bundle del navegador — por diseño, esta key
  **sí** va embebida en el JS que se sirve al cliente. Lo que realmente controla el acceso son
  las políticas RLS del rol `anon`, no el secreto de esta key (ver siguiente sección).

### Base de datos: sin backend propio, todo pasa por RLS

A diferencia de una app Next.js con rutas API, este SPA de Vite **habla directo a Supabase desde
el navegador** con la anon key — no hay servidor propio ni service role key en este directorio.
Eso significa que el catálogo (`productos`, `estatus_producto`) tiene que tener políticas RLS
explícitas para el rol `anon`, que **no existen por defecto** (las tablas ya tienen RLS activo,
pero hoy solo con políticas para `authenticated`, pensadas para la app móvil).

**Antes de que la app funcione**, hay que ejecutar una vez, en el SQL Editor del dashboard de
Supabase, el archivo [`supabase/anon_rls.sql`](supabase/anon_rls.sql). Da al rol `anon`:
lectura de `productos` y `estatus_producto`, y escritura acotada solo a la columna
`productos.mnemotecnia` (vía `GRANT` de columna — la política RLS de `UPDATE` no puede por sí
sola restringir columnas).

**Deliberadamente sin autenticación todavía** — pensado para correr solo en `localhost`. Con las
políticas de `anon_rls.sql` aplicadas, cualquiera que llegue a la URL desplegada (no solo
localhost) podría leer el catálogo completo y editar la mnemotecnia de cualquier producto, ya
que la anon key es pública por diseño. Antes de desplegar en cualquier lugar accesible por red
hace falta resolver quién puede entrar (ver "Pendiente de decidir" abajo) y probablemente
reemplazar estas políticas abiertas por unas que exijan un usuario autenticado.

## Cargar mnemotecnias desde Excel

El botón **"Cargar Excel"** (junto a los filtros) asigna mnemotecnias en masa. El archivo debe
tener dos columnas en la primera fila: **`Código`** (formato `xx-xx-xxx`) y **`Mnemotecnia`**.

El Excel no lleva casa, así que se cruza contra el catálogo de la **casa seleccionada** en ese
momento. Antes de escribir nada se muestra un panel de revisión con cuántas filas se van a
aplicar, cuántas ya estaban iguales y cuáles tienen problema (código mal formado, código que no
existe en esa casa, código repetido). Las filas sin mnemotecnia se ignoran: nunca se usa una
celda vacía para borrar lo que ya estaba. Solo al confirmar se guardan los cambios.

Hay un archivo de ejemplo listo para probar en
[`ejemplos/mnemotecnias-prueba.xlsx`](ejemplos/mnemotecnias-prueba.xlsx) — dos códigos de FEBECA
(`04-10-001` y `30-31-010`), ambos con la mnemotecnia "prueba".

## Formato corporativo

El panel sigue el formato de Grupo Mayoreo definido en `formato-mayoreo/` (raíz del repo):
base en escala de grises con el color de la casa solo como acento, tema claro únicamente,
tipografía del sistema y textos en español venezolano. La paleta vive en dos sitios que hay
que mantener iguales: `src/theme/marca.ts` (colores que se resuelven en runtime) y los tokens
`@theme` de `src/index.css`. Antes de tocar cualquier cosa con apariencia, lee esa carpeta.

Nota de WSL: el logo se importa desde `src/assets/` en vez de servirse desde `public/`, porque
en `/mnt/c/...` `copyFileSync` falla con `EPERM` y `vite build` se cae al copiar `public/`.
Además el watcher de Vite no recibe eventos en `/mnt/c`: si editas un archivo, reinicia
`npm run dev` para ver el cambio.

## Arquitectura (MVP actual)

- `src/App.tsx` — el marco corporativo (encabezado con logo, contenido, pie).
- `src/components/ProductosTable.tsx` — la UI de trabajo: selector de casa, buscador, filtro
  de infaltables, tabla editable. `src/components/EtiquetaEmpresa.tsx` es el patrón canónico
  de punto de color + nombre de la casa.
- `src/lib/api.ts` — `fetchAllProductos` (pagina automáticamente sobre el límite de 1000 filas
  de Supabase, misma regla que sigue la app móvil), `fetchEstatusProducto`, `updateMnemotecnia`.
- `src/lib/supabaseClient.ts` — único punto donde se crea el cliente Supabase, con la anon key.
- `supabase/anon_rls.sql` — la pieza real de seguridad del panel: sin ella la app carga pero
  toda consulta devuelve vacío/error por RLS.

## Pendiente de decidir antes de desplegar en algún entorno compartido

- Autenticación/autorización del panel (¿mismo login de Google + rol `admin` que la app móvil, o
  algo aparte?) — y, con eso, reemplazar las políticas RLS abiertas de `anon_rls.sql` por unas
  que exijan sesión.
- Alcance de edición: hoy solo `mnemotecnia`; definir si se abre a otros campos de `productos`
  (nombre, imagen, estatus).
- Dónde se despliega (Vercel, u otro).
