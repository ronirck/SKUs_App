# SKUs App

App de estudio y memorización de catálogo de productos (SKUs) para empleados de
distribuidora. Reconstrucción en Flutter del proyecto original (Flet/Python, archivado
en `_old/`).

## Configuración (variables de entorno)

La app no lee `.env` en runtime — en móvil ese archivo no se empaqueta en el build.
En su lugar, las variables se inyectan **en tiempo de compilación** vía
`--dart-define-from-file` y se leen con `String.fromEnvironment` en
`lib/core/config/app_config.dart` (única fuente de acceso a esta config; no se lee
en ningún otro lugar del código).

Variables requeridas (ver `env.example.json`):

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `GITHUB_REPO` (owner/repo del repositorio de releases en GitHub)
- `GOOGLE_WEB_CLIENT_ID` (OAuth Client ID **tipo Web** del proyecto de Google Cloud, el
  mismo configurado en Supabase → Authentication → Providers → Google; no es secreto, es
  un identificador público, pero igual se centraliza aquí en vez de escribirlo a mano en
  el código de auth)

> No hay `GITHUB_TOKEN`: el repo de releases es público, así que la API de GitHub
> se consulta sin autenticación (límite 60 req/hora por IP, de sobra para un chequeo
> de actualización). Si el repo de releases pasa a ser privado en el futuro, no
> embeber un token de escritura en el APK — un APK siempre se puede descompilar y
> el secreto quedaría expuesto. Usar en su lugar un token de solo lectura acotado
> al repo, o mejor aún, un endpoint intermedio (Supabase Edge Function) que guarde
> el token del lado servidor.

### Desarrollo local

1. Copia `env.example.json` a `env.json` (este archivo está en `.gitignore`, nunca
   se sube al repo).
2. Rellena los valores reales.
3. Corre o compila pasando el archivo:

```bash
flutter run --dart-define-from-file=env.json
flutter build apk --dart-define-from-file=env.json
```

## Ícono de la app

El ícono se genera con [`flutter_launcher_icons`](https://pub.dev/packages/flutter_launcher_icons)
a partir de dos imágenes en `assets/icon/`:

- `icon_legacy.png` — el logo (infinito + birrete, en negro/gris) aplanado sobre fondo
  blanco (`#FFFFFF`), usado como ícono "clásico" (Android < 8 y como ícono de referencia
  general).
- `icon_foreground.png` — solo el logo con fondo transparente, usado como capa de
  primer plano del ícono adaptativo (Android 8+); el fondo de esa capa es el color sólido
  `#FFFFFF` configurado en `pubspec.yaml` (`adaptive_icon_background`), ya que el logo fue
  diseñado para verse sobre blanco (no sobre el navy `#0D2853` usado por el logo anterior).

Ambos archivos ya incluyen su propio margen de "zona segura": el contenido ocupa ~59% del
lienzo de 1024×1024, muy por debajo de los bordes que Android recorta según la forma del
launcher (círculo, squircle, etc.). Por eso `adaptive_icon_foreground_inset: 0` en la
config — el inset por defecto del paquete (16%) es innecesario y encogería el logo más de
la cuenta.

**Para regenerar los íconos** (por ejemplo, si el logo cambia): reemplaza `icon.png` en la
raíz del proyecto (idealmente 1024×1024, con transparencia real — no un checkerboard
"falso" horneado en los píxeles, ver nota abajo) y reconstruye `icon_legacy.png`/
`icon_foreground.png` a partir de él, o edítalos directamente si ya tienes capas separadas
listas. Luego:

```bash
dart run flutter_launcher_icons
```

Esto sobreescribe todos los `mipmap-*/ic_launcher.png`, los `drawable-*/ic_launcher_foreground.png`
y `values/colors.xml` bajo `android/app/src/main/res/`. Hace falta reinstalar la app
(`flutter build apk --release --dart-define-from-file=env.json` + `adb install -r`) para
ver el ícono actualizado en el dispositivo — no basta con hot reload/restart.

> Nota: el `icon.png` original de este proyecto no tenía transparencia real — el fondo
> "cuadriculado" que se ve en un visor de imágenes estaba horneado como píxeles grises/
> blancos opacos (típico error al exportar desde algunas herramientas de diseño sin
> aplanar correctamente). Si vuelve a pasar, verifícalo antes de generar los íconos: un
> PNG con transparencia real tiene un canal alfa variable (no fijo en 255 en toda la
> imagen), y ninguna herramienta de por sí "sabe" qué parte del cuadriculado es realmente
> transparente — ese fondo debe reconstruirse a mano o volver a exportarse bien.

## Firma de release (Android)

`android/keystore/skus-app-release.jks` y `android/key.properties` (ambos gitignored)
contienen el keystore y credenciales de firma de release generados para este proyecto.
**Haz un respaldo externo de esos dos archivos** — sin ellos no se pueden firmar
actualizaciones futuras con la misma identidad de app.

## Estado del proyecto

- **Paso 0** completado: proyecto Flutter limpio, corriendo en dispositivo físico
  Android, clase de configuración verificada.
- **Fase 1** completada: autenticación con Google (`supabase_flutter` + `google_sign_in`),
  máquina de estados de arranque (login → confirmar nombre → onboarding con coach marks
  (`tutorial_coach_mark`) + partida demo aislada de la base de datos → esperando
  aprobación con polling → app aprobada), todo verificado en dispositivo físico incluyendo
  casos de error (login cancelado, sin red) y las tres transiciones de estado
  (pendiente/rechazado/aprobado).
  - Nota de esquema: `perfil_usuario` vincula con el usuario de Auth vía la columna
    `usuario_id` (no `id`) — ver `lib/features/auth/data/profile_repository.dart`.
- **Fase 2** completada: catálogo offline-first con caché local en SQLite (`drift`).
  Al aprobarse el usuario, `CatalogGate` descarga categorías/subcategorías/productos/
  estatus_producto filtrados por sede + marcas_permitidas + solo_infaltables, y la Guía
  de Estudio (categorías → subcategorías → productos) lee siempre de la caché local, nunca
  de red directamente. Arranque en frío instantáneo desde caché (en build **release** —
  en debug el JIT añade unos segundos, normal). Verificado en dispositivo: offline tras
  cachear, `marcas_permitidas=[]` (todas las marcas), marca restringida (con
  categorías/subcategorías vacías ocultas de la navegación), `solo_infaltables=true`, y
  reconstrucción de caché al cambiar `config_version`.
  - Notas de esquema: `subcategorias.codigo` se repite entre categorías (clave real:
    `(categoria_codigo, codigo)`); `estatus_producto` es una tabla de tipos de estatus
    (`productos.estatus` → `estatus_producto.codigo` → `es_infaltable`), no una fila por
    producto; `app_config` es tabla clave-valor (`clave`/`valor`), `version_datos` es una
    fila ahí, no una columna; `usuario_config.marcas_permitidas` es `text[]` con nombres
    de marca, no uuids.
  - El estado de aprobación (`perfil_usuario.estado`) también se cachea localmente
    (`shared_preferences`, vía `ProfileRepository.saveLastKnownProfile`/
    `loadLastKnownProfile`) — sin esto, `AuthGate` necesitaba red en cada arranque para
    verificar el perfil, rompiendo el offline-first del catálogo. Sin red, usa el último
    perfil conocido en vez de bloquear en "Preparando tu cuenta".

- **Fase 3** completada: 4 modos de juego (categorías, subcategorías, productos,
  contrarreloj) reutilizando el motor de quiz de la Fase 1 (`QuizEngine`, extendido con
  múltiples orígenes por tipo y prioridad de distractores "cercanos primero"). Todo corre
  contra la caché local (Fase 2), sin red para jugar. Nueva pestaña "Desafíos" junto a
  "Guía" en `HomeShell` (barra de navegación inferior).
  - Categorías/subcategorías/productos: 10 preguntas fijas, opción múltiple (2/4/6/8
    configurable), nunca repite pregunta en la misma partida salvo que el catálogo tenga
    menos elementos que preguntas. Distractores siempre códigos reales del catálogo,
    nunca inventados; si no hay suficientes, se reduce el número de opciones.
  - Contrarreloj: **por tiempo (90s)**, no de 10 preguntas — corrección sobre la
    especificación original de esta fase tras probarlo en dispositivo (el nombre del modo
    ya lo sugería). Cronómetro visible, mezcla categoría/subcategoría/producto pregunta a
    pregunta, termina solo al agotarse el tiempo.
  - Resultados en `resultados_codex` + fallos acumulados en `errores_partida`
    (upsert por (usuario_id, tipo_elemento, elemento_codigo), incrementando
    `veces_fallado` — alimenta los "puntos ciegos" del admin). Sin red al terminar una
    partida, el resultado se encola en una tabla local (`PendingGameResults`, drift) y se
    reintenta enviar al abrir la app (`PendingGameResultsSyncer.flushPending`, llamado
    desde `CatalogGate`) — nunca se pierde.
  - Notas de esquema: `errores_partida` no tenía unique constraint en
    `(usuario_id, tipo_elemento, elemento_codigo)` ni política RLS de UPDATE — ambas
    tuvieron que agregarse en Supabase durante esta fase para que el upsert acumulativo
    funcionara (una policy de solo INSERT/SELECT deja pasar el UPDATE sin error pero sin
    aplicar el cambio — no lanza excepción, hay que verificarlo en vivo, no asumirlo).

- **Fase 4** completada: medición de tiempo de sesión + sincronización reactiva a la
  conectividad (no solo al abrir la app, como en fases anteriores).
  - `CatalogGate` mide tiempo activo con `WidgetsBindingObserver`: arranca un cronómetro
    en `resumed` (solo si ya se está mostrando `HomeShell`), lo acumula en `paused` y al
    destruirse. `splitByLocalDay` reparte una sesión que cruza medianoche entre ambos días
    (nunca todo el tiempo al día equivocado) antes de sumarlo a `session_logs`, con upsert
    diario por `(usuario_id, fecha)` vía `SessionTimeSyncer`.
  - Sin red, el tiempo se encola en `PendingSessionTime` (drift) igual que los resultados
    de partida en `PendingGameResults`.
  - Nuevo disparador de sincronización: `connectivity_plus` detecta cuándo vuelve la red
    (transición sin-red → con-red) y en ese momento — **incluso con la app en segundo
    plano**, sin que el usuario la reabra — reintenta `PendingGameResultsSyncer.
    flushPending`, `SessionTimeSyncer.flushPending`, y `CatalogRepository.ensureSynced`.
    También se dispara al reanudar la app desde segundo plano. Deliberadamente NO se
    construyó un servicio en background real (WorkManager/tareas programadas) — el
    fabricante puede matarlo igual, y reintentar al reanudar/reconectar es suficiente para
    no perder datos sin esa complejidad.
  - Notas de esquema: `session_logs` ya tenía unique constraint `(usuario_id, fecha)` y las
    3 políticas RLS (INSERT/SELECT/UPDATE) desde el inicio — a diferencia de
    `errores_partida` en la Fase 3, aquí no hubo que agregar nada.

- **Fase 5** completada: pestaña "Perfil" (rol `user`) — 3ra pestaña en `HomeShell`.
  - Editar nombre/apellido (reutiliza `ProfileRepository.confirmNombreApellido` de la Fase 1).
  - Tema claro/oscuro/sistema + paleta de color (magenta, azul, verde, naranja, morado,
    rojo) vía `AppThemeController` (`ChangeNotifier` + `shared_preferences`), aplicado en
    vivo a nivel `MaterialApp` en toda la app, no solo en Perfil.
  - Cronómetro de sesión visible, en vivo — reutiliza el tracking de tiempo en foreground
    de la Fase 4, ahora extraído a una clase propia `SessionClock`
    (`lib/features/session/domain/session_clock.dart`) en vez de vivir ad-hoc dentro de
    `CatalogGate`, para poder exponerlo también a la UI.
  - Botón de refresco manual del catálogo (`CatalogRepository.ensureSynced` ahora devuelve
    `bool` para poder decir "ya estabas al día" vs "catálogo actualizado").
  - "Cerrar sesión" se movió aquí desde el AppBar de Guía. Al cerrar sesión: sincroniza el
    tiempo de sesión pendiente, borra la caché local del catálogo
    (`CatalogRepository.clearCache()`) y el último perfil conocido
    (`ProfileRepository.clearLastKnownProfile()`) — para que si otro usuario inicia sesión
    en el mismo dispositivo sin red no herede datos/estado del anterior. Los resultados de
    partida y tiempo aún pendientes de sincronizar NO se borran (siguen atados a su
    `usuario_id` y se sincronizan igual cuando haya red).
  - **Ajustado respecto al `juego.md` original**: se eliminó "cambio de contraseña" — ya
    no aplica, el login es solo con Google, no hay contraseña que gestionar. El cronómetro
    cuenta tiempo en primer plano (consistente con lo que se sincroniza a `session_logs`),
    no tiempo de reloj total como en la versión Flet.
  - Esta vez el usuario solo dio el título de la fase sin especificación — se acordó que
    yo propusiera el alcance (basado en `juego.md` y lo ya construido) y lo confirmara
    antes de construir, en vez de asumir o exigir una spec completa.

- **Fase 6** completada: panel de administración, integrado en la misma interfaz del rol
  `user` en vez de una app aparte — Guía y Desafíos son idénticos para `admin`, sin
  ninguna rama de código distinta.
  - `HomeShell` agrega una 4ta pestaña "Usuarios" solo cuando `profile.rol == 'admin'`
    (`lib/features/home/presentation/home_shell.dart`); el resto de pestañas y su lógica
    no cambian.
  - `UsuariosScreen`: lista con buscador por nombre/apellido y dos filtros en dropdowns
    separados (Sede, Antigüedad nuevo/antiguo) — no chips, por preferencia explícita tras
    probarlo en dispositivo. `filtrarUsuarios` (dominio puro) combina los tres filtros.
  - `UserDetailScreen`: `SegmentedButton` de estado (Pendiente/Aprobado/Rechazado) editable
    en cualquier momento, no solo cuando el usuario está pendiente — feedback de uso real:
    un admin también necesita poder revocar un usuario ya aprobado o reconsiderar uno
    rechazado. Selector de sede + marcas permitidas con buscador, checkboxes (no chips) y
    orden seleccionadas-primero-luego-alfabético (`filtrarYOrdenarMarcas`, dominio puro),
    todo dentro de un contenedor con scroll propio para no tener que bajar por toda la
    lista de marcas para llegar a "solo infaltables" y "Guardar configuración".
    `AdminRepository.updateUsuarioConfig` incrementa `config_version`, lo que dispara la
    resincronización del catálogo del usuario afectado la próxima vez que su app revisa
    conectividad/reanuda (mecanismo de la Fase 2/4, sin cambios) — verificado en
    dispositivo con dos cuentas reales.
  - Estadísticas por usuario (`AdminRepository.fetchUserStats`): partidas jugadas,
    efectividad, tiempo de sesión total en formato `hh:mm:ss` (`formatHms`, extraído a
    `lib/core/utils/format_duration.dart` y reutilizado también en el cronómetro de
    Perfil de la Fase 5) y "puntos ciegos" (top 5 `errores_partida` por `veces_fallado`).
  - Reportes de error: botón "Reportar un problema" en Perfil, visible para **todos** los
    roles (`ReportesRepository.submitReport`, sin cola offline — es una acción manual y
    deliberada, no algo que deba sobrevivir a estar en curso). Sección "Reportes"
    adicional en Perfil, visible solo para `admin`, con cambio de estatus por reporte
    (`kEstatusReporte`).
  - Notas de esquema: `perfil_usuario` y `usuario_config` son tablas separadas unidas por
    `usuario_id` en el cliente (`AdminRepository.fetchAllUsers`), no un join en la base;
    `errores_partida` requería la política RLS de UPDATE agregada en la Fase 3 para que
    "puntos ciegos" reflejara conteos reales.

- **Fase 7** completada: verificador de actualizaciones + mejoras a la Guía usadas como
  primera versión real de prueba.
  - Al entrar a `HomeShell`, un chequeo único y no bloqueante contra
    `GET /repos/$GITHUB_REPO/releases/latest` (sin autenticación, igual que decidido en
    Paso 0) compara la versión instalada (`package_info_plus`) contra el último release.
    Si hay una versión más nueva y el release aplica al rol del usuario (marcador
    `APP_TARGET`), se muestra un `MaterialBanner` descartable con cambios (marcador
    `APP_CHANGELOG_START/END`) y "Copiar enlace" (copia la URL del `.apk` adjunto); si el
    título incluye `[CRITICAL]`, en su lugar se muestra un diálogo modal no descartable
    (`PopScope(canPop: false)`, sin botón atrás) hasta que el usuario actualice. Toda la
    lógica de parseo/comparación de versión, changelog y segmentación de rol es pura y
    vive en `lib/features/updates/domain/` — sin dependencias de Flutter, portada
    directamente de la lógica ya probada de `_old/updater.py`.
  - `release.py` (raíz del repo, viene de antes de la migración a Flutter) se adaptó a la
    nueva estructura: versión leída de `pubspec.yaml` (antes `main.py`'s `APP_VERSION`),
    APK en `build/app/outputs/flutter-apk/app-release.apk` (antes `build/apk/*.apk`),
    `GITHUB_REPO` leído de `env.json` (ya existente). El `GITHUB_TOKEN` para publicar
    **no** vive en `env.json` — ese archivo se compila dentro del APK — sino en un `.env`
    nuevo en la raíz (gitignored), que el script lee solo para sí mismo.
  - Mejoras a la Guía de Estudio (rol `user` y `admin` por igual, ya que ambos comparten
    la misma pantalla): buscador de un producto específico por nombre/código (resultados
    planos sin importar categoría/subcategoría), dropdown de marca (solo visible si el
    catálogo cacheado tiene más de una) y switch "Solo infaltables" ajustable durante la
    sesión — los tres filtran en SQL sobre la caché local ya descargada, sin red.
  - **Corrección de arquitectura necesaria para que el switch tuviera sentido**: hasta
    ahora, si `usuario_config.solo_infaltables = true`, la sincronización solo
    *descargaba* productos infaltables — los demás nunca llegaban a existir en la caché
    local. Un switch de sesión que se puede apagar habría sido un placebo (apagarlo no
    mostraría nada, porque no había nada más que mostrar). Se quitó esa restricción de
    `_rebuildCache`/`fetchProductos`: ahora el catálogo siempre se descarga completo
    dentro de sede + `marcas_permitidas` (esas sí son restricciones de acceso reales,
    decisión del admin); `solo_infaltables` pasó a ser puramente un filtro de sesión en
    la Guía, sembrado con el valor de config como punto de partida
    (`CacheMeta.soloInfaltablesDefault`, columna nueva) pero cambiable libremente. Sin
    este cambio, el nuevo switch habría sido una feature rota en apariencia funcional.
  - Verificado en dispositivo con un release real (no sintético): se publicó `v1.1.0` en
    GitHub con el changelog de estas mismas mejoras, y se instaló temporalmente una build
    con el número de versión bajado a `1.0.0` (mismo código, sin recompilar lógica vieja)
    para confirmar que el banner aparece con el changelog correcto y los botones
    funcionan; luego se reinstaló la build real de `1.1.0` y se confirmó que, al ser ya la
    versión más reciente, no aparece ningún banner. El diálogo crítico y la segmentación
    por rol quedan cubiertos por tests unitarios (`is_critical_release_test.dart`,
    `should_notify_role_test.dart`) pero no se verificaron con un release real por el
    costo de publicar releases adicionales solo para probar variantes — si se necesita
    confirmar esos dos casos en dispositivo, hace falta publicar un release con
    `[CRITICAL]` en el título o un `APP_TARGET` distinto de `all`.
  - Nota de compatibilidad: bajar el número de versión de un build release-firmado y
    reinstalarlo con `adb install -r` falla con `INSTALL_FAILED_VERSION_DOWNGRADE`
    (Android lo bloquea salvo builds debuggable) — hace falta `adb uninstall` primero.

- **Demo de onboarding rehecha** (ad hoc, no una fase numerada): la partida de
  ejemplo del onboarding (Fase 1) era una mini-quiz aislada de una sola pantalla. Ahora
  reutiliza literalmente las pantallas reales — `GuiaCategoriasScreen`, `DesafiosHomeScreen`
  (con un `recorderOverride: NoopGameResultRecorder()` para no escribir en Supabase) y
  `PerfilScreen` — dentro de un `IndexedStack` + `NavigationBar` propio del onboarding,
  respaldadas por un catálogo ficticio (`buildDemoCatalogRepository()`,
  `lib/features/game/demo/`): un `CatalogRepository` real sobre una base drift en memoria
  (`AppDatabase.forTesting(NativeDatabase.memory())`), sembrada con categorías/
  subcategorías/productos de mentira. Un usuario 'pendiente' ve la app completa —los 4
  modos de juego, el buscador/filtro de marca/toggle de infaltables de la Guía (Fase 7), el
  Perfil real— antes de ser aprobado, sin que RLS se lo impida (nunca toca la base real).
  Los coach marks ahora apuntan a los íconos reales de la barra de navegación en vez de una
  vista previa estática, y "Finalizar recorrido" es un FAB siempre visible en vez de estar
  condicionado a completar una partida.

Pendiente: planificar la siguiente fase antes de construir features.
