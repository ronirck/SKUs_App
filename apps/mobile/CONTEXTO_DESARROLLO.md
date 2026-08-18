# Contexto de desarrollo — SKUs App

Este documento resume la historia, las decisiones de arquitectura, los bugs encontrados y
cómo se resolvieron, y la metodología de trabajo usada para construir esta app. Sirve como
memoria de largo plazo del proyecto, complementaria a `README.md` (que documenta configuración
y estado fase por fase) y a `juego.md` (reglas de negocio).

---

## 1. Qué es la app

SKUs App es una app móvil (Android, Flutter) para que empleados de una distribuidora (varias
"casas"/sedes: FEBECA, SILLACA, BEVAL, COFERSA, MUNDIAL DE PARTES) se aprendan de memoria los
códigos de producto de su catálogo, mediante una guía de estudio navegable y varios modos de
juego tipo quiz. Tiene dos roles: `user` (estudia) y `admin` (además gestiona usuarios,
restricciones de acceso y reportes). Backend: Supabase (Postgres + Auth + RLS).

**Propósito de fondo** (no solo "una app de trivia"): que el personal aprenda los códigos que
necesita para su trabajo diario. Esto también motivó un trabajo paralelo de auditoría de datos
(sección 7) para asegurar que el catálogo que la app enseña sea correcto.

---

## 2. Historia: de Flet (Python) a Flutter

### Era Flet (marzo–junio 2026)

El proyecto arrancó como una app Python con [Flet](https://flet.dev/) (`main.py`, `auth.py`,
`session_manager.py`, `updater.py`, `views/`), con Supabase como backend desde el inicio.
Evolucionó con features incrementales: paleta de colores por sede, selector de casa, filtro de
marca, botón de reseteo de estadísticas, altas de sedes (COFERSA, MUNDIAL DE PARTES), baja de
sede (Prisma), recuperación de contraseña, panel de administración básico, actualización de la
app vía descarga de APK con streaming.

### Migración a Flutter (2026-07-05 en adelante)

**Por qué:** la versión Flet se volvió poco escalable para seguir agregando features.

**Cómo se hizo:**
- Todo el código Flet (`main.py`, `auth.py`, `session_manager.py`, `updater.py`, `config.py`,
  `views/`, `assets/`, `base_schema.sql`, `config.sql`, `.env`, `env/`, `build/`, el `CLAUDE.md`
  viejo) se archivó en `_old/` (`git mv` para lo trackeado, `mv` simple para lo gitignoreado).
  `_old/` se trata como referencia histórica de solo lectura para lógica de negocio y esquema
  de base de datos — nunca se edita, y está excluido de `flutter analyze`
  (`analysis_options.yaml` → `analyzer.exclude: [_old/**]`).
- `juego.md` (documento de reglas de negocio agnóstico de framework: roles, modos de juego,
  filtros) se mantuvo en la raíz, no se archivó — sigue siendo referencia viva.
- Proyecto Flutter nuevo creado en el mismo repo: `flutter create --platforms=android --org
  biz.mayoreo --project-name skus_app` → application ID `biz.mayoreo.skus_app`.
- El proyecto de Supabase también cambió a mitad de la migración: la URL/anon key pasaron a
  apuntar a un proyecto nuevo (`yzlhvabujsyuiqgaffrc.supabase.co`), no el original de la era
  Flet (`nomuvetphjpnwvktywrv`) — el usuario reemplazó el backend por uno actualizado.

La migración se hizo por **fases** (documentadas en detalle en `README.md`, resumidas en la
sección 5 de este documento), siguiendo la metodología de la skill `movil-develop` (sección 8).

### Hallazgo de seguridad durante la migración

Al auditar `config.py` antes de decidir qué variables de entorno migrar, se encontró un
`GITHUB_TOKEN` con scope `repo` completo **hardcodeado y commiteado** en un repositorio
**público** (`ronirck/SKUs_App`) — una fuga activa, no un riesgo futuro. Se reportó al usuario
de inmediato; la decisión fue **diferir la revocación** ("dejarlo por ahora, decidir después").
Al commitear la migración (`8b73a6b`), el token quedó reemplazado por un placeholder en
`_old/config.py`, pero **sigue en el historial de git del repo público** — la revocación nunca
se confirmó. Esto motivó una decisión de diseño explícita: la nueva app **no vuelve a incluir
un `GITHUB_TOKEN`** (ver sección 4). Este episodio también generó una regla de trabajo
permanente: en cualquier migración, revisar los archivos de config reales en busca de secretos
embebidos, no solo confiar en la lista de variables que describe el usuario.

---

## 3. Arquitectura actual (Flutter)

Capas estrictas **datos → dominio → UI**, organizadas en rebanadas verticales por feature bajo
`lib/features/`:

```
lib/
  core/
    config/app_config.dart        # única fuente de config (env compile-time)
    database/app_database.dart    # esquema drift (SQLite local)
    theme/app_theme_controller.dart
    utils/format_duration.dart
  features/
    auth/          # login Google, perfil, máquina de estados de arranque
    catalog/        # guía de estudio, caché offline-first
    game/           # motor de quiz + 4 modos + recorder de resultados
    session/        # cronómetro de sesión, sync de tiempo
    admin/          # gestión de usuarios, stats, filtros
    profile/        # pantalla de Perfil (rol user)
    reportes/       # reporte de problemas
    updates/        # verificador + instalador de actualizaciones
    home/           # HomeShell (bottom nav)
  main.dart
```

Cada feature sigue `data/` (repositorios, fuentes remotas/locales) → `domain/` (lógica pura,
sin dependencias de Flutter, la más testeada) → `presentation/` (pantallas y widgets).

**Stack clave:** `supabase_flutter` (backend), `google_sign_in` v7 (auth), `drift` sobre
`sqlite3_flutter_libs` (caché local reactiva vía `.watch()`), `shared_preferences` (perfil
cacheado + preferencias de tema), `connectivity_plus` (sync reactiva a la red),
`package_info_plus` + `http` + `open_filex` (verificación/instalación de actualizaciones),
`tutorial_coach_mark` (onboarding).

---

## 4. Decisiones de diseño clave

### Configuración: sin `.env` en runtime
La app no lee `.env` en el dispositivo (un APK no empaqueta ese archivo). Toda config
(`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `GITHUB_REPO`, `GOOGLE_WEB_CLIENT_ID`) se inyecta en
**tiempo de compilación** vía `--dart-define-from-file=env.json`, leída únicamente en
`lib/core/config/app_config.dart`. `env.example.json` es la plantilla trackeada; `env.json`
tiene los valores reales y está gitignoreado.

### Sin `GITHUB_TOKEN` en la app
Decisión directa consecuencia del hallazgo de seguridad (sección 2): como el repo de releases
es público, el chequeo de actualizaciones llama a la API de GitHub **sin autenticación** (60
req/hora por IP, suficiente para un chequeo ocasional). Un token de escritura embebido en un
APK siempre es recuperable descompilando el binario — nunca se debe repetir ese patrón. Si el
repo de releases pasara a ser privado, la alternativa documentada en `README.md` es un token
de solo lectura acotado, o mejor, un endpoint intermedio (Supabase Edge Function) que guarde el
token del lado servidor.

### Auth: Google OAuth únicamente
`supabase_flutter` + `google_sign_in` v7 (API nueva `GoogleSignIn.instance.initialize(...)` +
`authenticate()`, no el patrón v6 `GoogleSignIn().signIn()`). Consecuencia: features del
`juego.md` original que asumían login por contraseña (ej. "cambio de contraseña") se
descartaron explícitamente por no aplicar — no hay contraseña que gestionar.

### Offline-first como postura por defecto
El catálogo completo (dentro de sede + marcas permitidas del usuario) se descarga una vez y se
cachea en SQLite local vía `drift`; toda la Guía de Estudio y los modos de juego leen de esa
caché, nunca de red directamente. El estado de aprobación del perfil también se cachea
(`shared_preferences`) para que `AuthGate` no dependa de red en cada arranque — sin esto, la
app quedaba bloqueada indefinidamente en "Preparando tu cuenta" sin conexión, anulando el
propósito de cachear el catálogo.

### Sincronización reactiva, sin servicio de background real
Los resultados de partidas y el tiempo de sesión se encolan localmente (`PendingGameResults`,
`PendingSessionTime` en drift) cuando no hay red, y se reintentan al reanudar la app y en la
transición sin-red→con-red (`connectivity_plus`), incluso con la app en segundo plano (no
matada). Se decidió **deliberadamente no construir** un servicio de background real
(WorkManager/tareas programadas): los optimizadores de batería agresivos de ciertos fabricantes
(Honor/Xiaomi) pueden matarlo de todas formas, así que esa complejidad no compraría fiabilidad
real — la mitigación "reintentar al reanudar/reconectar" cubre el requisito real de "no perder
datos" sin la falsa sensación de garantía de un servicio persistente.

### Rol admin: misma interfaz, no una app aparte
Corrección del usuario a la primera propuesta de scope: Guía y Desafíos deben ser
**pixel-idénticos** entre `user` y `admin`, cero ramas de código distintas. Las diferencias son
puramente aditivas (una 4ª pestaña "Usuarios", una sección "Reportes" en Perfil), gateadas solo
por `profile.rol == 'admin'`. Regla aplicada desde entonces a cualquier feature admin nueva.

### `solo_infaltables`: de restricción de descarga a filtro de sesión, y de vuelta
Historia interesante de ida y vuelta:
1. Originalmente (Fase 2), `solo_infaltables=true` en `usuario_config` restringía qué se
   **descargaba** — el resto de productos nunca llegaba a existir localmente.
2. En Fase 7 se agregó un switch de sesión "Solo infaltables" en la Guía. Se detectó que, tal
   como estaba, sería un placebo: apagar el switch no mostraría nada porque el resto de
   productos nunca se había descargado. Se corrigió quitando esa restricción de la descarga —
   el catálogo pasó a bajarse siempre completo dentro de sede + marcas permitidas, y
   `solo_infaltables` se volvió un filtro SQL de sesión, libremente cambiable.
2. En v1.2.0 (post-migración) se revirtió ese punto por decisión de producto: cuando un
   **admin** asigna `solo_infaltables` a un usuario, ahora es una restricción real otra vez (el
   catálogo se descarga acotado a infaltables — guía, búsqueda y juegos — y ese usuario ya no
   ve el toggle). Lección: una misma bandera de config puede necesitar comportarse distinto
   según quién la fija (admin vs. el propio usuario en su sesión) — no asumir que "restricción
   de acceso" y "preferencia de sesión" son mutuamente excluyentes para siempre.

---

## 5. Fases de desarrollo (resumen)

Detalle completo, verificaciones en dispositivo y notas de esquema por fase en `README.md`
("Estado del proyecto"). Resumen aquí:

| Fase | Contenido | Fecha |
|---|---|---|
| Paso 0 | Proyecto Flutter limpio + config compile-time | 2026-07-05 |
| Fase 1 | Auth Google, máquina de estados de arranque, onboarding + demo | 2026-07-05 |
| Fase 2 | Catálogo offline-first, caché SQLite (drift) | 2026-07-05 |
| Fase 3 | 4 modos de juego (categorías/subcategorías/productos/contrarreloj) | 2026-07-05 |
| Fase 4 | Medición de tiempo de sesión + sync reactiva a conectividad | 2026-07-05 |
| Fase 5 | Perfil (rol user): tema, paleta, cronómetro, refresco manual | 2026-07-05 |
| Fase 6 | Panel de admin: usuarios, stats, reportes | 2026-07-05 |
| Fase 7 | Verificador de actualizaciones + mejoras a la Guía | 2026-07-06 |
| Ad hoc | Ícono de la app (`flutter_launcher_icons`) | 2026-07-06 |
| Ad hoc | Rebuild del demo de onboarding (reuso de pantallas reales) | 2026-07-06 |
| v1.2.0 | Migración a Flutter commiteada; restricción real de infaltables; fixes admin | 2026-07-08 |
| v1.3.0 | Contador de productos en la Guía; admin no puede tocar a otro admin; changelog por rol | 2026-07-09 |
| v1.4.0 | Actualización in-app con progreso; fix paginación 1000 filas; selector de casa (admin) | 2026-07-10 |

Nota de fase 5/6: en dos ocasiones (Fase 4 y Fase 5) el usuario dio solo el título de la fase
sin especificación detallada. El patrón que se estableció y confirmó como correcto: proponer el
alcance basado en el contexto ya construido (`juego.md`, lo existente), ajustar según feedback
puntual del usuario, confirmar, y recién entonces construir — en vez de exigir una spec
completa o asumir sin preguntar.

### v1.2.0 – v1.4.0 (detalle, no cubierto en README)

**v1.2.0** (`8b73a6b`, 2026-07-08) — primer commit que fija la migración completa a Flutter en
el historial de git:
- "Solo infaltables" fijado por un admin pasa a ser restricción real de descarga (ver sección 4).
- Un admin deja de verse a sí mismo en la lista de usuarios.
- Fix: crash de `setState` async al recargar la lista de usuarios.
- Fix: overflow visual en los dropdowns de filtros de la vista Usuarios.
- El guardado de configuración de usuario ahora **verifica la escritura** después de guardar,
  como protección explícita ante no-ops silenciosos de RLS (aplicación directa de la lección de
  la sección 6.2).
- Fix: test de widget que colgaba por `SharedPreferences` sin mock.
- Token de GitHub confirmado retirado del código archivado.

**v1.3.0** (`3ee4b89`, 2026-07-09):
- La Guía de Estudio muestra el total de productos visibles como subtítulo del AppBar (respeta
  búsqueda, marca y solo-infaltables activos); mismo patrón al entrar a una subcategoría. Este
  contador fue lo que expuso en producción el bug de paginación de 1000 filas (ver sección 6.1).
- Un admin ya no puede cambiar el estado (pendiente/aprobado/rechazado) de **otro admin**:
  selector deshabilitado en la UI + guard defensivo en `_setEstado`.
- `extract_changelog` soporta bloques de changelog por rol (`APP_CHANGELOG_USER`/
  `APP_CHANGELOG_ADMIN`) con fallback al bloque genérico; `release.py` los genera desde
  `release_info.json`.

**v1.4.0** (`7834a05`, 2026-07-10):
- Actualización desde la propia app: descarga del APK con barra de progreso (streaming HTTP) +
  instalador del sistema (`open_filex` + permiso `REQUEST_INSTALL_PACKAGES`); errores con causa
  visible, reintento sin volver a descargar, y "Copiar enlace" como fallback manual.
- **Fix crítico**: paginar la descarga del catálogo — Supabase/PostgREST cortaba a 1000 filas
  silenciosamente, dejando cacheado un catálogo incompleto en sedes grandes (detalle en 6.1).
- Perfil (rol admin): nueva sección "Casa" para ver y cambiar la propia sede; reconstruye la
  caché de forma transaccional y remonta Guía/Desafíos vía `watchCacheKey`.
- Al terminar un desafío, ahora se vuelca el tiempo de sesión acumulado y se sube lo encolado
  pendiente (antes solo ocurría al pausar/reanudar la app).
- `AdminRepository.updateOwnSede`, con verificación de escritura (mismo patrón de la sección 6.2).

---

## 6. Bugs importantes y cómo se resolvieron

### 6.1 Supabase/PostgREST trunca cualquier lectura a 1000 filas — sin error

**Síntoma:** usuarios reportaron que el contador de infaltables (agregado en v1.3.0) mostraba
126/101 cuando debía mostrar 200/629.

**Causa:** PostgREST (`db-max-rows`) corta cualquier `SELECT` a 1000 filas aunque no se pida
límite explícito, **sin ningún error** — la respuesta simplemente llega incompleta. La app
cacheaba solo ~1000 de los 3.276–10.973 productos por sede desde la migración a Flutter; el bug
estuvo silencioso hasta que el nuevo contador lo hizo visible.

**Diagnóstico:** se confirmó reproduciendo la consulta exacta sin paginar, que devolvió
exactamente 126 filas.

**Fix (v1.4.0):** paginación obligatoria en toda lectura que pueda superar 1000 filas —
`fetchAllPages` en Dart (`lib/features/catalog/data/fetch_all_pages.dart`, bucle `.range()` con
`.order()` estable) y un patrón `get_all` equivalente por límite/offset en los scripts Python de
`Data/`.

**Regla derivada:** al depurar "faltan datos" contra Supabase, verificar primero si la
respuesta tiene *exactamente* 1000 filas — es la huella del truncamiento.

### 6.2 RLS silencia UPDATEs sin lanzar error

**Síntoma:** en Fase 3, el upsert acumulativo de `errores_partida` (incrementar
`veces_fallado` en fallos repetidos) parecía funcionar (no creaba filas duplicadas, no lanzaba
excepción) pero el contador nunca cambiaba de valor.

**Causa:** la tabla solo tenía políticas RLS de `INSERT`/`SELECT`, ninguna de `UPDATE`.
Postgrest, al no encontrar filas que la política permita tocar, hace match de 0 filas y
**devuelve éxito igual** — sin excepción, sin campo de error.

**Fix:** se agregó la política RLS de `UPDATE` (owner-scoped) y un unique constraint
`(usuario_id, tipo_elemento, elemento_codigo)` que faltaba, en Supabase directamente.

**Regla derivada, aplicada después en repetidas ocasiones** (v1.2.0 `updateUsuarioConfig`,
v1.4.0 `updateOwnSede`): cualquier UPDATE/upsert contra Supabase debe **verificar el valor real
post-escritura**, no inferir éxito de la ausencia de excepción.

### 6.3 Fuga de `GITHUB_TOKEN` en repo público

Ver sección 2 y sección 4. Resuelto en el diseño de la nueva app (nunca se vuelve a embeber un
token de escritura); la revocación del token viejo en el historial de git sigue **sin
confirmar** por decisión explícita y diferida del usuario — si el tema resurge, no asumir que
fue rotado.

### 6.4 "Transparencia" falsa en el ícono de la app

**Síntoma:** al procesar `icon.png` para generar los íconos adaptativos de Android, el fondo
"cuadriculado" (indicador visual típico de transparencia) resultó ser **píxeles opacos reales**
— `alpha.getextrema()` devolvía `(255, 255)`, es decir, opacidad total en toda la imagen. El
cuadriculado era un error de exportación horneado directamente en los píxeles, no transparencia
real interpretada por un visor.

**Fix:** se reconstruyó el canal alfa real con una heurística de escala de grises (el
cuadriculado de fondo es gris/blanco neutro; el logo navy/cian está lejos de ser neutro), con
una erosión de 2px para eliminar el halo de anti-aliasing que sobrevivía en los bordes.

**Regla derivada:** antes de confiar en un PNG "transparente" para procesamiento programático,
verificar que el canal alfa realmente varíe — un cuadriculado renderizado por un visor es
indistinguible a simple vista de uno horneado en los píxeles.

### 6.5 Placebo de "solo infaltables" (Fase 7)

Ver sección 4 ("solo_infaltables: de restricción de descarga a filtro de sesión, y de vuelta").
Bug de diseño, no de código: un toggle de sesión sobre datos que nunca se descargaron es
decorativo. Detectado jugando la feature en dispositivo, no por revisión de código.

### 6.6 Gotcha de firma de release vs. debug en el mismo dispositivo

`flutter run` (debug) instala un APK firmado en debug; un `adb install -r` posterior de un APK
firmado en **release** falla con `INSTALL_FAILED_UPDATE_INCOMPATIBLE` (firmas distintas). Fix:
`adb uninstall biz.mayoreo.skus_app` antes de instalar el release. De forma relacionada,
**bajar** el número de versión de un build release-firmado y reinstalarlo falla con
`INSTALL_FAILED_VERSION_DOWNGRADE` — también requiere desinstalar primero.

### 6.7 `AuthException` de Supabase filtrando errores crudos a la UI

`gotrue`'s `AuthException` envuelve errores de bajo nivel (p. ej. sin red) ocurridos *antes* de
recibir una respuesta HTTP — en ese caso `statusCode`/`code` son `null` y `message` es el
`toString()` crudo de la excepción subyacente (ej. `"ClientException with
SocketException: Failed host lookup..."`). Esto llegó a mostrarse tal cual en la pantalla de
login hasta que se corrigió `SupabaseAuthRepository.signInWithGoogle()` para chequear
`statusCode == null` y sustituir un mensaje amigable en ese caso. Regla aplicada luego a
cualquier llamada Supabase cuyo error pudiera llegar a la UI.

---

## 7. Trabajo de datos y calidad del catálogo

### Carga de productos FEBECA/SILLACA (ejecutada 2026-07-08)

Se cargaron `Data/FEBECA.xlsx` y `Data/SILLACA.xlsx` a Supabase con `Data/cargar_datos.py`
(soporta `--dry-run`), verificando después releyendo (200 B/D/F en FEBECA, 629 en SILLACA,
idénticos al Excel) y bumpeando `version_datos` de "1" a "2". Reglas acordadas (documentadas
también en `Data/reglas_carga.md`, carpeta gitignoreada):
- El Excel es fuente de verdad para nombres de producto; comparaciones siempre dentro de la
  misma sede.
- Los productos del Excel deben ser **los únicos** con estatus B/D/F (= infaltable) en su sede;
  los B/D/F existentes en Supabase que no estén en el Excel pasan a estatus `Z` (no se
  eliminan).
- Los scripts de `Data/` usan `SUPABASE_SERVICE_ROLE_KEY` (la anon key devuelve 0 filas por
  RLS).

### Auditoría de inconsistencias de categoría/subcategoría (en curso)

Hallazgo clave (2026-07-12): las inconsistencias de clasificación **no son solo del Excel de
infaltables** — el catálogo oficial de cada casa las tiene también, y peor: el código embebido
del producto (formato `CC-SS-NNN`) no siempre corresponde a una única (categoría, subcategoría)
real en el catálogo de la casa.

Validación completa vía ADB contra la app de catálogo oficial de cada casa
(`validar_catalogo.py`, reutilizable entre casas cambiando hoja/CSV):
- **SILLACA** (629/629 códigos): 535 OK, 87 no encontrados (~14%, posibles productos
  inactivos/migrados), 7 discrepantes que confirman que el catálogo mismo es inconsistente.
  Taxonomía completa recorrida: 18 categorías en catálogo vs. 25 en Supabase; 7 subcategorías
  con prefijos de código mezclados.
- **FEBECA** (200/200 códigos): 126 OK, 52 no encontrados (26%), 22 discrepantes — incluyendo
  bloques completos de productos codificados en el prefijo contrario a su propia descripción
  (breakers 04-07↔04-10).

**Entregable final** (2026-07-13, en `Data extra/`): "Informe de Inconsistencias de
Clasificación - Catálogos.docx" + soporte en Excel, acotado por decisión del usuario a **solo
SILLACA** (FEBECA queda pendiente de una entrega de datos adicional del negocio), comparando
únicamente catálogo-vs-Excel — sin mencionar Supabase, para mantener el reporte como
comparación fuente-contra-fuente. Objetivo: que el negocio decida la taxonomía canónica antes
de seguir corrigiendo la app o la base de datos.

---

## 8. La skill `movil-develop`

Todo el desarrollo de esta app se guio por la skill de Claude Code `movil-develop`
(`~/.claude/skills/movil-develop/`), invocada automáticamente por el asistente desde el primer
mensaje de la migración a Flutter, no solo cuando ya había un bug. Vale explicarla porque es la
razón detrás de decisiones que de otro modo parecerían arbitrarias (por qué se probó primero el
caso de error, por qué no hay un servicio de background, por qué cada fase se verificó en
dispositivo físico antes de seguir).

### Qué es
Una guía de metodología (no específica de Flutter, aunque los ejemplos lo usan) que prioriza
**integridad de datos y mantenibilidad de largo plazo por encima de velocidad inicial**. Su
premisa central: una app que se usa a diario durante años no fracasa por un feature que falta
(eso se agrega después), sino por **datos que no se capturaron bien desde el día uno** — eso es
irrecuperable. Toda la skill gira alrededor de esa asimetría de costos.

### Cómo arranca un proyecto bajo esta skill (antes de escribir código)
1. **Definir alcance y fases** — separar un MVP mínimo usable de mejoras posteriores, pero con
   el modelo de datos del MVP ya contemplando las fases futuras, para no migrar el esquema
   después.
2. **Diseñar el modelo de datos primero** — entidades, campos, relaciones, incluso los que la
   pantalla que los muestra todavía no existe.
3. **Preparar el entorno de prueba en dispositivo físico real** antes de construir.

### Los cuatro pilares operativos
1. **Arquitectura por capas datos → dominio → UI**, en ese orden estricto — invertir el orden
   garantiza retrabajo porque el esquema termina cambiando para acomodar lo que la UI pide.
2. **Rebanadas verticales, no capas horizontales** — cada módulo se construye de punta a punta
   (esquema, repositorio, modelo, pantalla, prueba) antes de pasar al siguiente. Así, un bug de
   esquema descubierto con un solo módulo construido cuesta un commit, no una arqueología
   entre cinco módulos con UI ya construida.
3. **Probar el caso de error antes que el caso correcto** — para cada operación que modifica
   estado, primero la prueba que verifica que se *rechaza* una entrada inválida, luego el
   camino feliz. Obliga a pensar la invariante antes de implementarla.
4. **Cada paso queda ejecutable y verificado en dispositivo real** antes de avanzar — cadencia:
   feature → análisis estático limpio → tests en verde → correr en el dispositivo → recién
   entonces la siguiente feature.

### Principios de arquitectura y datos (`references/architecture-principles.md`)
Ocho reglas para evitar las categorías de bug más caras (las que corrompen datos en silencio):
única fuente de verdad para todo agregado (con función de recálculo desde el origen), cantidades
precisas como enteros nunca float, guardar en UTC pero agrupar/filtrar en hora local (aplicado
directamente en `split_by_local_day.dart` para que una sesión que cruza medianoche no se
atribuya entera a un solo día), propiedades de comportamiento como campos tipados nunca
inferencia de texto libre, entidades de sistema garantizadas vía buscar-o-crear idempotente,
capturar el dato aunque la pantalla venga después (evitar "campos huérfanos"), un único
responsable por cada modificación de estado, y filtros de historial que contemplan ambos lados
de una relación.

### Trampas del entorno móvil y producción (`references/platform-and-production.md`)
Offline-first y permisos mínimos por defecto (solicitados en contexto, nunca al arrancar);
tareas en segundo plano chocan con la optimización de batería de ciertos fabricantes — no es un
bug del código, es una decisión del fabricante, y la mitigación es reprogramar al abrir la app
más que depender de un servicio persistente (exactamente el razonamiento detrás de la decisión
de sync de la sección 4); probar features no deterministas con un botón que dispare la lógica
real, no una simulación; fricciones de empaquetado (desugaring de librerías Java 8+ para
plugins nativos); checklist de producción (auditar antes de cargar datos reales, ocultar
herramientas destructivas detrás de flags de debug, garantizar seeds, plan de respaldo de datos
locales).

### Cómo se aplicó concretamente en este proyecto
- El orden de fases (auth → catálogo/caché → juegos → sesión/sync → perfil → admin →
  actualizaciones) sigue el pilar de rebanadas verticales: cada fase es una feature completa de
  punta a punta, verificada en un dispositivo físico Android real antes de pasar a la siguiente
  — nunca en un emulador.
- La decisión de no construir un servicio de background real (sección 4) es una aplicación
  literal de la trampa "tareas en segundo plano vs. optimización de batería".
- `split_by_local_day.dart` es una aplicación directa y explícita del principio "guardar en
  UTC, agrupar en hora local".
- El hallazgo del `GITHUB_TOKEN` expuesto surgió de aplicar la disciplina de "auditar el estado
  real antes de tomar decisiones de diseño", no de que el usuario lo pidiera explícitamente.
- Los tests unitarios del motor de quiz (`quiz_engine_test.dart`,
  `distractor_picker_test.dart`) y de los módulos de dominio de `updates/` cubren primero los
  casos límite (catálogo con menos elementos que preguntas, versión igual/menor, release sin
  changelog) antes que el camino feliz.

---

## 9. Sistema de actualizaciones — la feature más problemática, historia completa

De todas las features de la app, la de actualizaciones es la que más iteraciones y bugs de
producción ha tenido, en ambas eras del proyecto. Vale la pena rastrearla completa en vez de
solo su estado final.

### Era Flet
- **2026-04-03, "Fix pantalla en blanco en APK Android"**: `page.window.on_event` y la
  configuración de íconos de ventana (`favicon`, `window.icon`, `window_icon`) no existen en
  Android — solo en escritorio. Ese código corría antes de montar cualquier vista, lanzaba una
  excepción no capturada, y dejaba la app en pantalla blanca en Android específicamente (no en
  desktop, donde sí funcionaba, lo que hizo el bug más difícil de sospechar). Fix: todo ese
  bloque se limitó a plataformas desktop (Windows/macOS/Linux) y además se envolvió en
  `try/except` como capa extra de seguridad.
- **2026-04-03, "Migrar descarga de APK a requests stream + changelog post-instalación"**:
  la descarga pasó a usar `requests.get(stream=True)` con chunks de 256 KB y timeouts
  diferenciados (15s para conectar, 600s para la descarga completa); progreso real en MB
  descargados/total; el archivo parcial se borra automáticamente si la descarga falla; errores
  de red distinguidos por tipo (timeout, conexión, HTTP, genérico) en vez de un mensaje
  genérico. Se agregó también un changelog post-instalación: el changelog de la versión se
  guarda en `update_state.json` tras una descarga exitosa y se muestra una sola vez, como
  diálogo, al arrancar ya la nueva versión (no antes de instalarla).
- Commits posteriores de la era Flet (`5f657fc` "Update config and updater", `4cf4298`
  "Actualización para el release", `c8db22f` "Correcciones en la función de actualización",
  todos 2026-06-02/03) siguieron ajustando esta misma función — evidencia de que ya en Flet era
  un punto de fricción recurrente, no una feature que se terminó de una vez.

### Migración a Flutter (Fase 7, 2026-07-06)
Toda esa lógica ya probada (parseo de versión, extracción de changelog/marcador de rol,
detección de release crítico) se **portó 1:1 a Dart puro** bajo
`lib/features/updates/domain/` — sin dependencias de Flutter, justamente para poder reusar el
diseño ya validado en vez de rediseñarlo. En esta fase la app solo **verificaba** si había una
versión nueva (`GithubReleaseDataSource`, GET sin autenticación a
`/repos/$GITHUB_REPO/releases/latest`) y ofrecía un botón "Copiar enlace" — el usuario todavía
tenía que descargar e instalar el APK manualmente fuera de la app.

### v1.4.0 (2026-07-10) — instalación real desde la app
Se agregó la descarga + instalación completa dentro de la app, con manejo de errores explícito
en cada etapa:

- **`ApkDownloader`** (`lib/features/updates/data/apk_downloader.dart`): descarga por streaming
  HTTP (`http.Client.send` sobre un `Request` GET; GitHub responde 302 hacia el CDN de release
  assets, que el cliente `http` sigue automáticamente). Reporta progreso byte a byte vía
  callback. Clasifica los fallos en 4 causas explícitas (`ApkDownloadError`):
  `sinConexion` (no se pudo ni conectar), `respuestaInvalida` (HTTP ≠ 200),
  `interrumpida` (se cortó a mitad de la descarga) y `archivoDanado` (el tamaño final no
  coincide con el publicado, vía `isApkDownloadComplete`, dominio puro). En cualquier falla
  borra el archivo parcial — nunca deja un `.apk` a medias en disco.
- **`ApkInstaller`** (`apk_installer.dart`): envoltorio fino sobre `open_filex`
  (`OpenFilex.open` con `type: 'application/vnd.android.package-archive'`, que aporta su propio
  `FileProvider`), mapeado a 3 resultados: `lanzado`, `permisoDenegado` (falta autorizar
  "instalar apps desconocidas" para esta app específica) y `error` genérico.
- **`UpdateInstallSection`** (widget compartido entre el banner y el diálogo crítico) orquesta
  una máquina de 4 fases (`inicial → descargando → instalando → error`):
  - Si ya existe un APK descargado y **íntegro** en caché (mismo tamaño esperado), salta
    directo a instalar sin volver a descargar.
  - Si la instalación falla por `permisoDenegado`, el APK descargado se conserva
    (`_apkListo`) para que "Reintentar" no tenga que re-descargar — solo reabre el instalador,
    una vez que el usuario autorizó el permiso en Ajustes.
  - El destino de descarga es el **directorio de caché de la app**
    (`getTemporaryDirectory`, inyectable para tests), deliberadamente para no requerir permisos
    de almacenamiento — el sistema puede limpiarlo solo. Antes de cada descarga se eliminan APKs
    de versiones anteriores que hubieran quedado ahí, para no acumular basura.
  - Cada tipo de `ApkDownloadError` se traduce a un mensaje accionable distinto para el usuario
    (no un genérico "hubo un error"); "Copiar enlace" queda como fallback manual si la
    instalación in-app sigue fallando.
- En el mismo release se corrigió, además, el bug de paginación a 1000 filas (sección 6.1) —
  no relacionado al mecanismo de actualización en sí, pero coincidió en la misma versión porque
  el nuevo contador de productos (que sí depende de la paginación) fue agregado un release
  antes (v1.3.0) y expuso el bug justo antes de esta entrega.

**Por qué esta feature concentra tantos bugs**: cruza descarga de red, manejo de archivos,
permisos del sistema operativo (instalar paquetes desconocidos) y el instalador nativo de
Android — la superficie con más puntos de falla externos al propio código Dart/Python de toda
la app. Cada iteración (Flet → Fase 7 Flutter → v1.4.0) fue ampliando la robustez ante esos
puntos de falla en vez de asumir que "descargar un archivo" es una operación simple.

---

## 10. Recorrido guiado (coach marks) — cómo funciona

La feature de "resaltar/oscurecer el resto de la pantalla para señalar un botón o control
específico con una explicación" es el **recorrido de onboarding** (`OnboardingScreen`,
`lib/features/auth/presentation/screens/onboarding/onboarding_screen.dart`), implementada con
el paquete [`tutorial_coach_mark`](https://pub.dev/packages/tutorial_coach_mark).

**Mecánica del paquete:** un `TutorialCoachMark` recibe una lista de `TargetFocus` (cada uno
apunta a un `GlobalKey` de un widget real ya construido en el árbol) y, al llamarse `.show()`,
dibuja un overlay que oscurece toda la pantalla (`colorShadow: Colors.black`,
`opacityShadow: 0.85` en esta app) excepto un recorte alrededor del widget objetivo
(`ShapeLightFocus.RRect`, con `paddingFocus: 8` de margen), junto con un bloque de texto
(`TargetContent`) que explica ese control.

**Cómo se integró en esta app:**
- Los objetivos son las 3 pestañas reales de la barra de navegación del propio onboarding
  (Guía/Desafíos/Perfil), identificadas con `GlobalKey`s (`_keyGuia`, `_keyDesafios`,
  `_keyPerfil`) asignadas directamente al ícono de cada `NavigationDestination` — no una
  maqueta ni una captura estática. El tutorial se dispara una sola vez, en
  `initState` vía `WidgetsBinding.instance.addPostFrameCallback`, para garantizar que los
  widgets objetivo ya estén posicionados en el layout antes de que el paquete intente medirlos
  (mostrarlo antes del primer frame haría que no encuentre las coordenadas del `GlobalKey`).
- Cada `TargetContent` es un `Column` con título en negrita + texto explicativo en blanco sobre
  el overlay oscuro, alineado arriba del recorte (`ContentAlign.top`).
- Esta versión reemplazó una implementación anterior más simple: originalmente (Fase 1) el
  onboarding era una mini-quiz aislada de una sola tarjeta, con los coach marks apuntando a una
  fila de íconos **estática y de mentira** construida solo para la vista previa. Se rehizo (ver
  sección 5, "Rebuild del demo de onboarding") para que los coach marks señalaran los íconos
  **reales** de la barra de navegación de la app real, no una maqueta — de modo que el
  recorrido y la app posterior sean visualmente y funcionalmente el mismo lugar.
- El botón "Saltar" (`textSkip: 'Saltar'`) permite descartar el recorrido en cualquier punto sin
  bloquear el acceso al resto del onboarding.
- Detrás de las pestañas resaltadas hay una app real navegable con datos ficticios en memoria
  (ver `buildDemoCatalogRepository()`, sección 5) — el coach mark señala botones reales que ya
  funcionan, no una ilustración.

---

## 11. Permisos y control de acceso

Dos sistemas de permisos coexisten en la app, con propósitos distintos: permisos del sistema
operativo (Android) y control de acceso a datos (roles + restricciones de negocio vía RLS).

### 11.1 Permisos de Android (`AndroidManifest.xml`)
Deliberadamente mínimos, alineados con la postura "offline-first y permisos mínimos" de la
skill `movil-develop` (sección 8):
- `INTERNET` — el único permiso "normal" (no peligroso) necesario para hablar con Supabase y
  GitHub.
- `REQUEST_INSTALL_PACKAGES` — agregado en v1.4.0 exclusivamente para la instalación in-app de
  actualizaciones (sección 9). Es un permiso "especial" en Android 8+: no se concede con un
  diálogo al arrancar, sino que el usuario debe autorizarlo explícitamente para esta app en
  Ajustes → "Instalar apps desconocidas" — la primera vez que se necesita, el sistema lo
  bloquea (`ApkInstallResult.permisoDenegado`) y la app muestra un mensaje que indica
  exactamente dónde autorizarlo, en vez de fallar en silencio.
- Deliberadamente **no** se pide ningún permiso de almacenamiento: el APK descargado se guarda
  en el directorio de caché propio de la app (`getTemporaryDirectory`), que no requiere
  permisos y que el sistema puede limpiar solo.
- No hay permisos de ubicación, cámara, contactos ni notificaciones push — ninguna feature de
  la app los necesita.

### 11.2 Login: alcance de Google Sign-In
`GoogleSignIn.instance.initialize(serverClientId: ...)` seguido de `.authenticate()` (API v7)
solo solicita identidad (para obtener un `idToken` que Supabase valida vía
`signInWithIdToken`) — ningún scope adicional (contactos, Drive, calendario). El único dato que
la app usa del login es el nombre para prellenar `NameConfirmationScreen`, extraído de forma
defensiva por `google_name_extractor.dart` (Fase 1) en vez de asumir un formato fijo.

### 11.3 Control de acceso a datos (roles y restricciones de negocio)
Este es el sistema de "permisos" más importante del punto de vista del negocio, y vive
enteramente en Supabase (RLS) + la config por usuario, no en el cliente:
- **Rol** (`perfil_usuario.rol`: `user`/`admin`) — gatea únicamente la pestaña "Usuarios" y la
  sección "Reportes" de Perfil (sección 4, "misma interfaz"). No hay ninguna feature de
  guía/juego distinta por rol.
- **Estado de aprobación** (`perfil_usuario.estado`: pendiente/aprobado/rechazado) — controla
  si el usuario ve la app real o queda en onboarding/espera/rechazo (`resolveAppRoute`, Fase 1).
- **Sede** (`usuario_config`/columna `sede` en categorías/subcategorías/productos) — cada
  consulta al catálogo filtra explícitamente por sede (`.eq('sede', ...)`); no es algo que RLS
  resuelva solo, cada query lo declara.
- **`marcas_permitidas`** (`usuario_config`, `text[]` de nombres de marca) — si está vacío, el
  usuario ve todas las marcas; si tiene valores, el catálogo se descarga acotado a esas marcas
  y la navegación oculta categorías/subcategorías que quedarían vacías bajo ese filtro (sección
  "Fase 2" del historial de fases).
- **`solo_infaltables`** — historia de ida y vuelta ya documentada en la sección 4: hoy, cuando
  un admin la fija para un usuario, es una restricción real de descarga (el usuario ni siquiera
  ve el toggle); el propio usuario puede además tener su propio filtro de sesión sobre lo que sí
  se descargó.
- **RLS de Postgres** es la capa de aplicación real de todo lo anterior del lado servidor — la
  sección 6.2 documenta el bug más importante de este sistema: una tabla sin política de
  `UPDATE` deja pasar la escritura como "éxito" pero sin aplicar el cambio, sin lanzar
  excepción. Por eso, desde ese incidente, todo guardado de configuración de acceso
  (`AdminRepository.updateUsuarioConfig`, `updateOwnSede`) **verifica el valor real
  post-escritura** en vez de confiar en la ausencia de error.
- **Restricción admin-sobre-admin** (v1.3.0): un admin no puede cambiar el estado de otro admin
  (selector deshabilitado en la UI + guard en `_setEstado`) — la única regla de acceso que
  distingue entre dos usuarios del mismo rol.

---

## 12. Estado y pendientes

- Versión actual: **v1.4.0** (`pubspec.yaml` → `1.4.0+6`), commit `7834a05` (2026-07-10).
- El esquema de `drift` sigue en `schemaVersion: 1` sin estrategia real de migración — durante
  el desarrollo activo, un cambio de forma de tabla se resuelve desinstalando la app en el
  dispositivo de prueba (caché 100% desechable, se resincroniza de Supabase). **Pendiente antes
  de un cambio de esquema post-lanzamiento real**: escribir una migración o al menos un
  `onUpgrade` destructivo con bump de versión.
- La revocación del `GITHUB_TOKEN` expuesto en el historial de git público sigue sin
  confirmarse (sección 2/6.3) — si el tema resurge, no asumir que fue rotado.
- El análisis de inconsistencias de catálogo de FEBECA quedó pendiente de una entrega adicional
  de datos por parte del negocio (sección 7); el reporte final entregado cubre solo SILLACA.
- No hay plan de respaldo de datos locales aún (recomendado por la skill antes de que se
  acumulen meses de datos de uso) — no es urgente pre-lanzamiento, pero está en el radar.
- Siguiente fase de desarrollo: no había ninguna planificada al cierre de la última sesión
  registrada — confirmar con el usuario antes de asumir el próximo alcance.
