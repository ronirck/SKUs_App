# Reglas de Negocio — SKUs App

Documento de referencia completo sobre cómo funciona la aplicación: qué puede hacer cada tipo de usuario, cómo funciona el sistema de juego, los filtros de las guías y todas las reglas que gobiernan el comportamiento del sistema.

---

## Roles y Capacidades

### Rol `user` (jugador)

Es el rol predeterminado. Todo usuario nuevo registrado recibe este rol automáticamente.

**Pestañas disponibles:** Guía | Desafíos | Perfil

**Capacidades:**
- Ver la Guía de Estudio filtrada a su sede y marcas asignadas
- Jugar los 4 modos de desafío
- Cambiar su nombre de usuario y contraseña
- Alternar entre tema claro y oscuro
- Forzar un refresh manual del catálogo desde el servidor

**Restricciones:**
- No puede ver usuarios de otras sedes
- Solo ve los productos de su `sede` y `marcas_permitidas`
- Si `solo_infaltables` está activo en su configuración, el switch de infaltables arranca activado pero puede desactivarlo manualmente durante la sesión
- No tiene acceso a las pestañas de administración

---

### Rol `admin`

Asignado manualmente en la base de datos (`perfil_usuario.rol = 'admin'`).

**Pestañas disponibles:** Usuarios | Reportes | Guía Global | Perfil

**Capacidades:**
- Ver todos los usuarios registrados en todas las sedes
- Editar la configuración de cualquier usuario: sede, marcas permitidas, flag solo_infaltables
- Ver estadísticas por usuario: % efectividad, número de partidas, minutos totales de sesión, top 5 de errores frecuentes ("puntos ciegos")
- Gestionar reportes de error enviados por usuarios: leer el mensaje completo y cambiar el estatus (sin_revisar → en_revision → pendiente → resuelto)
- Navegar la Guía Global de cualquier sede sin restricciones de marca
- Ver el badge de notificaciones en la pestaña Usuarios cuando hay registros nuevos (<7 días)

**Color de interfaz:** gris (`GREY_600`) en lugar del color de sede. Es el mismo color sin importar qué sede esté viendo.

**Restricciones:**
- No puede modificar su propio rol desde la app
- El admin no tiene caché de productos propia igual a la de usuario; la Guía Global usa un caché separado por sede (`cache_admin_<sede>.json`)

---

## Registro y Autenticación

### Flujo de registro

1. El usuario ingresa email, contraseña (mínimo 6 caracteres) y nombre de usuario (mínimo 3 caracteres)
2. Supabase Auth crea la cuenta y un trigger `handle_new_user` crea automáticamente las filas en `perfil_usuario` y `usuario_config`
3. La app actualiza el campo `nombre` en `perfil_usuario` con el nombre ingresado
4. Se inserta un registro en `notificaciones_admin` con tipo `nuevo_registro` → el admin ve el badge de "Nuevo" en ese usuario durante 7 días

**Configuración inicial de un usuario nuevo:**
- `sede`: FEBECA
- `marcas_permitidas`: `[]` (vacío = ve todas las marcas de la sede)
- `solo_infaltables`: `false`
- `config_version`: 1
- `rol`: `user`

### Flujo de recuperación de contraseña

1. Usuario ingresa su email → la app llama a Supabase `reset_password_for_email`
2. Supabase envía un OTP de 6 dígitos al correo
3. Usuario ingresa el código (acepta entre 6 y 8 dígitos)
4. Si el código es válido: se abre la pantalla "Nueva contraseña"
5. Usuario ingresa y confirma la nueva contraseña (mínimo 6 caracteres)
6. El código OTP puede reenviarse desde la pantalla de verificación

### Restauración de sesión

Al iniciar la app, antes de mostrar el login, se intenta restaurar la sesión con los tokens guardados localmente (`access_token` y `refresh_token` en `session_data.json`). Si la restauración falla, los tokens se borran y se muestra el login.

---

## Sistema de Sesión y Tiempo

### Cómo se mide el tiempo de sesión

El tiempo no se mide en forma continua sino mediante **intervalos de actividad**:

- `start_interval`: se registra al iniciar sesión; guarda `interval_start` y `last_interaction` como timestamps
- `register_interaction`: se llama en cada toque/interacción del usuario. Si han pasado ≥60 segundos desde la última interacción, el intervalo actual se cierra y se abre uno nuevo
- `close_interval`: suma el tiempo transcurrido desde `interval_start` hasta ahora como `pending_seconds`

El cronómetro visible en la pantalla de Perfil (`00:00:00`) muestra el tiempo acumulado **de la sesión activa** desde el login. Este contador avanza cada 1 segundo y no se pausa.

### Sincronización con Supabase

- Cada 60 segundos de inactividad (sin interacciones), el intervalo se cierra y los segundos pendientes se sincronizan con la tabla `session_logs`
- Si el registro del día ya existe: se **suma** `pending_seconds` al valor existente (`duration_seconds`)
- Si no existe: se **inserta** un nuevo registro para ese `date`
- Al cerrar sesión: se sincroniza el tiempo pendiente antes de hacer `sign_out`
- Al iniciar sesión: se sincronizan datos pendientes que hayan quedado sin enviar en la sesión anterior

### Cruce de medianoche

Cuando el reloj detecta que la fecha actual difiere de la `pending_date` almacenada:
1. Se cierra y sincroniza el intervalo del día anterior
2. Se inicia un nuevo intervalo para el día nuevo

### Tolerancia a interrupciones

Si la app se cierra sin hacer logout (crash, kill del proceso):
- `interval_start` y `last_interaction` quedan guardados en `session_data.json`
- Al próximo inicio, `recover_incomplete_interval()` calcula los segundos del intervalo incompleto y los suma a `pending_seconds`
- Esos segundos se sincronizan en el próximo login

---

## Caché de Productos

### Cuándo se recarga la caché

La caché local (`productos_cache.json`) se invalida y se descarga de nuevo si **cualquiera** de estas condiciones es verdadera:
- No existe caché local
- `config_version` local ≠ `config_version` remota
- La `sede` guardada en caché ≠ la sede del usuario actual
- Las `marcas_permitidas` guardadas ≠ las del usuario actual

### Qué se guarda en la caché

```json
{
  "config_version": 5,
  "sede": "BEVAL",
  "marcas_permitidas": ["MARCA_A", "MARCA_B"],
  "solo_infaltables": false,
  "categorias": [...],
  "subcategorias": [...],
  "productos": [...]
}
```

### Cómo el admin fuerza la recarga del usuario

Cuando el admin edita la configuración de un usuario (sede, marcas, solo_infaltables), incrementa `config_version` en +1. La próxima vez que ese usuario abra la app, la diferencia de versiones fuerza la descarga del catálogo actualizado.

### Caché del admin

La Guía Global del admin usa un sistema de caché separado: un archivo `cache_admin_<sede>.json` por cada sede. No está ligado a `config_version`. El admin puede forzar recarga con el botón de refresh.

---

## Guía de Estudio (rol `user`)

### Estructura del catálogo

Los productos siguen una jerarquía de 3 niveles:
```
Categoría (código 2 dígitos, ej: "AU")
  └── Subcategoría (código 2 dígitos, ej: "01")
        └── Producto (código completo: "AU-01-001")
```

La guía se presenta como un acordeón: categorías colapsadas → al tocar una, se despliegan sus subcategorías → al tocar una subcategoría, se despliegan sus productos.

Cada nivel puede tener una **mnemotecnia** (frase mnemotécnica de apoyo) que se muestra en cursiva al expandir el nivel.

### Imágenes de producto

Solo los productos con `estatus` en el conjunto `{"B", "D", "F"}` (infaltables) y que tengan `imagen_url` muestran una miniatura de 44×44 px. Al tocarla, se abre en pantalla completa sobre un fondo negro. Toca en cualquier parte para cerrar.

### Filtros disponibles

| Filtro | Tipo | Comportamiento |
|---|---|---|
| Marca | Dropdown | Filtra productos de esa marca. Opción "Todas las marcas" para quitar el filtro. Solo visible si hay más de una marca disponible |
| Solo Infaltables | Switch | Muestra únicamente productos con `estatus` en `{"B", "D", "F"}` |
| Buscar categoría | Campo de texto | Filtra categorías por nombre (case-insensitive, búsqueda parcial). Al filtrar categorías, también limita las subcategorías visibles a las que pertenecen a esas categorías |
| Buscar subcategoría | Campo de texto | Filtra subcategorías por nombre. Al filtrar subcategorías, recalcula qué categorías quedan visibles (solo las que tienen subcategorías que coincidan) |

### Lógica interna de los filtros (`filtros.py`)

El orden de aplicación es:
1. Filtrar productos por `solo_infaltables` y `marca`
2. Determinar qué categorías tienen al menos un producto visible
3. Si hay búsqueda de categoría: filtrar categorías por nombre → reducir el conjunto de subcategorías elegibles
4. Filtrar subcategorías que tengan al menos un producto visible (dentro de las categorías elegibles)
5. Si hay búsqueda de subcategoría: filtrar subcategorías por nombre → recalcular qué categorías quedan

Esto garantiza que nunca se muestre una categoría vacía ni una subcategoría sin productos.

### Refresh manual

El botón ↻ del header descarga todo el catálogo desde Supabase (sin caché) y actualiza la caché local con la nueva versión.

---

## Guía Global (rol `admin`)

Funciona igual que la Guía de Estudio pero con estas diferencias:

- **Dropdown de sede**: el admin puede cambiar entre las 5 sedes; cada cambio descarga el catálogo de esa sede
- **Sin filtro de marca**: se muestran todos los productos sin restricción de marca
- **Filtros disponibles**: Solo Infaltables, búsqueda de categoría, búsqueda de subcategoría (idénticos en comportamiento a la guía de usuario)
- **Caché por sede**: primera carga con una sede usa caché si existe; el refresh fuerza descarga del servidor

---

## Modos de Juego (Panel de Desafíos)

### Flujo general

Menú → Selección de dificultad → Partida pregunta a pregunta → Resultados → (Jugar otra vez | Volver al menú)

Los desafíos usan el mismo catálogo cacheado del usuario (categorías, subcategorías y productos de su sede y marcas).

### Dificultad

Se selecciona antes de cada partida. Define cuántas opciones aparecen por pregunta:

| Nivel | Opciones |
|---|---|
| 2 | 2 opciones |
| 4 | 4 opciones (predeterminado) |
| 6 | 6 opciones |
| 8 | 8 opciones |

La respuesta correcta siempre está incluida; el resto son distractores elegidos al azar del mismo pool.

---

### Modo: Reto Categorías

**Instrucción:** "¿A qué categoría principal pertenece?"

El jugador ve el **nombre** de una categoría y debe identificar su **código de 2 dígitos** entre las opciones.

- Pool: hasta 10 categorías aleatorias del catálogo del usuario
- Las opciones son códigos de otras categorías del mismo catálogo
- Al responder mal: se muestra la mnemotecnia de la categoría (si existe) en el feedback

---

### Modo: Reto Subcategorías

**Instrucción:** "¿A qué subcategoría pertenece?"

El jugador ve el **nombre** de una subcategoría y debe identificar su **código de 2 dígitos** entre las opciones.

- Pool: hasta 10 subcategorías aleatorias
- Las opciones son códigos de otras subcategorías
- El código correcto es el código de la subcategoría (no el código completo `CAT-SUB`)
- Al responder mal: **no** se muestra mnemotecnia (solo aplica en categorías y contrarreloj)

---

### Modo: Reto Productos

**Instrucción:** "¿Cuál es el código completo?"

El jugador ve el **nombre** de un producto y debe identificar su **código completo** (`CAT-SUB-PROD`) entre las opciones.

- Pool: hasta 10 productos aleatorios
- Las opciones son códigos completos de otros productos
- Al responder mal: **no** se muestra mnemotecnia

---

### Modo: Contrarreloj

**Instrucción:** "¿A qué categoría pertenece?"

Preguntas mixtas (categorías + subcategorías + productos mezcladas y barajadas), con un **contador regresivo de 90 segundos** visible en pantalla.

- La partida termina cuando el tiempo llega a 0 o cuando se agotan las preguntas (lo que ocurra primero)
- El timer corre en background y actualiza el contador cada 1 segundo
- Al responder mal una categoría: se muestra la mnemotecnia si existe

---

### Mecánica de preguntas

- Las preguntas se barajan aleatoriamente al inicio de cada partida
- Al seleccionar una opción: la respuesta correcta se pinta en verde, la incorrecta (si eligió mal) en rojo
- No se puede cambiar la respuesta una vez seleccionada
- Aparece el botón "Siguiente →" (o "Ver resultados →" en la última pregunta)
- Un contador en tiempo real muestra aciertos ✓ y fallos ✗ en la parte superior
- Una barra de progreso muestra el avance dentro de la partida

---

### Pantalla de resultados

| Rango de efectividad | Mensaje |
|---|---|
| ≥ 80% | 🏆 ¡Excelente! |
| ≥ 50% | 👍 ¡Buen trabajo! |
| < 50% | 💪 Sigue practicando |

Se muestran 3 métricas: Aciertos (%), Partidas (total de preguntas respondidas), Efectividad (%).

Si hubo errores, se lista cada elemento fallado con su código, nombre y mnemotecnia (o "Mnemotecnia pendiente" si no tiene). Si no hubo errores: mensaje de "¡Sin errores! Perfecto 🎉".

---

### Guardado de resultados

Al terminar cada partida se inserta en Supabase:

**Tabla `resultados_codex`:**
- `usuario_id`, `tipo_juego`, `aciertos`, `fallos`, `total_preguntas`, `duracion_segundos`, `sede`
- `configuracion`: `{"dificultad": N}` donde N es el número de opciones elegido

**Tabla `errores_partida`** (un registro por error cometido):
- `resultado_id`, `usuario_id`, `tipo_elemento` (categoria/subcategoria/producto)
- `elemento_codigo`, `elemento_nombre`, `mnemotecnia`, `veces_fallado` (siempre 1 por registro)

El guardado ocurre una sola vez por partida (`saved = True` después del primer intento).

---

## Panel de Usuarios (rol `admin`)

### Filtros de la lista

| Filtro | Descripción |
|---|---|
| Todos | Muestra todos los usuarios sin importar rol |
| Usuarios | Solo `rol = 'user'` |
| Admins | Solo `rol = 'admin'` |
| Nuevos | Solo usuarios creados en los últimos 7 días |

Además hay un campo de **búsqueda libre** por nombre o email (búsqueda parcial, case-insensitive).

Los filtros de rol y la búsqueda se aplican en combinación (AND).

### Agrupación por sede

Los usuarios visibles se agrupan en `ExpansionTile` por sede, en el orden fijo: FEBECA → COFERSA → SILLACA → BEVAL → MUNDIAL DE PARTES → Sin sede asignada.

Cada grupo muestra un indicador de color de sede y el conteo de usuarios. Dentro de cada grupo los usuarios aparecen ordenados por `creado_en` ascendente.

### Estadísticas en la tarjeta de usuario

Cada tarjeta de usuario muestra (si tiene actividad):
- **% efectividad**: aciertos / total_preguntas × 100 calculado sobre todos los `resultados_codex`
- **Partidas**: número de registros en `resultados_codex`
- **Tiempo (min)**: suma de `duration_seconds` de `session_logs` / 60

El color del % de efectividad es:
- Verde: ≥ 70%
- Amarillo: ≥ 40%
- Rojo: < 40%

### Edición de configuración de usuario

Al tocar un usuario se abre un `BottomSheet` con:
1. Estadísticas detalladas (cargadas en background) incluyendo top 5 de **puntos ciegos** (elementos más veces fallados)
2. Dropdown de sede (al cambiar la sede, recarga las marcas disponibles de esa sede desde la tabla `marcas`)
3. Lista de marcas disponibles para la sede seleccionada (checkboxes). Si se cambia la sede, las marcas quedan todas desmarcadas
4. Switch "Solo Infaltables"
5. Botón Guardar

Al guardar: se actualiza `usuario_config` en Supabase y se incrementa `config_version` en +1, forzando que el usuario recargue su caché en la próxima sesión.

### Notificaciones de nuevos registros

- Al ingresar a la pestaña Usuarios, todos los registros de `notificaciones_admin` con `leido = false` se marcan como leídos automáticamente
- El badge numérico en el ícono de la pestaña desaparece al entrar a la vista

---

## Panel de Reportes (rol `admin`)

Lista de reportes enviados por usuarios desde la tabla `reportes_error`, ordenados del más reciente al más antiguo.

Al tocar un reporte se abre un `BottomSheet` con:
- Nombre del usuario, email y fecha/hora del reporte
- Mensaje completo del reporte
- Dropdown para cambiar el estatus

**Ciclo de estatus:**
- `sin_revisar` → `en_revision` → `pendiente` → `resuelto`

El cambio de estatus se guarda inmediatamente al seleccionar una opción en el dropdown. La lista principal se actualiza con el nuevo estatus en tiempo real.

---

## Actualizaciones de la App

Al iniciar sesión, la app consulta el último release de GitHub. Si hay una versión más nueva, el comportamiento depende del tipo de actualización:

### Actualización opcional

Se muestra un **banner** en la parte superior con:
- Texto: "Nueva versión X.X.X disponible"
- Items del changelog (si los hay)
- Botón "Copiar" (copia la URL del APK al portapapeles)
- Botón "Ignorar" (cierra el banner)

### Actualización crítica (`[CRITICAL]` en el título del release)

Se muestra un **diálogo modal** que **no se puede cerrar**:
- Texto: "Esta versión (X.X.X) ya no es compatible. Descarga la versión Y.Y.Y para continuar."
- Items del changelog
- Solo el botón "Copiar enlace"

El usuario queda bloqueado en el diálogo hasta que descargue e instale la nueva versión.

### Segmentación por rol

Los releases pueden incluir `<!-- APP_TARGET: admin -->`, `<!-- APP_TARGET: user -->` o `<!-- APP_TARGET: all -->`. Si el target no coincide con el rol del usuario logueado, no se muestra la notificación de actualización.

---

## Perfil de Usuario

Disponible tanto para `user` como para `admin`.

- **Cambio de nombre de usuario**: actualiza `perfil_usuario.nombre`
- **Cambio de contraseña**: llama a `auth.update_user()` de Supabase; no requiere contraseña actual
- **Tema**: toggle claro/oscuro; persiste en `session_data.json` como `is_dark`; recarga la vista de Perfil al cambiar
- **Cronómetro de sesión**: muestra el tiempo total acumulado de la sesión actual (`clock_text`)
- **Logout**: cierra el intervalo de sesión activo, sincroniza el tiempo pendiente, hace `sign_out` en Supabase y borra todos los tokens y cachés locales

---

## Colores por Sede

| Sede | Color |
|---|---|
| FEBECA | Azul (`BLUE_400`) |
| COFERSA | Azul (`BLUE_400`) |
| SILLACA | Rosa (`PINK_400`) |
| BEVAL | Verde (`GREEN_400`) |
| MUNDIAL DE PARTES | Verde (`GREEN_400`) |
| Admin (cualquier sede) | Gris (`GREY_600`) |

El color de sede se usa como `primary_color` en toda la interfaz del usuario: headers de categorías, bordes, iconos, indicadores de progreso, colores de botones.

---

## Estructura del Código de Producto

```
XX  -  XX  -  XXX
↑      ↑       ↑
Cat   Sub    Producto
```

El código completo puede venir en el campo `codigo_completo` o se construye concatenando `categoria_codigo + '-' + subcategoria_codigo + '-' + codigo`.

---

## Infaltables

Los productos con `estatus` dentro del conjunto `{"B", "D", "F"}` son considerados **infaltables** (productos esenciales). Esta misma constante se define independientemente en `guia_estudio.py`, `guia_global.py` y `panel_desafios.py` — los tres usan `{"B", "D", "F"}`.

Impacto de ser infaltable:
- Aparecen con imagen en miniatura en la guía (si tienen `imagen_url`)
- Pueden ser filtrados con el switch "Solo Infaltables"
- Los usuarios con `solo_infaltables = true` en su config tienen el switch activado por defecto al entrar a la guía
