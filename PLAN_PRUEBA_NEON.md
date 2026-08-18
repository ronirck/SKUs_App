# Plan de prueba: integración con Neon (paralela a Supabase)

Documento de continuidad para retomar esta tarea después de reiniciar la sesión de Claude Code
(el reinicio es necesario para que el MCP de Neon, agregado a `.mcp.json`, quede activo). No
confundir con `CONTEXTO_DESARROLLO.md` (historia larga del proyecto) — este documento es el plan
de trabajo activo de esta iniciativa específica y puede borrarse/archivarse una vez completada o
descartada.

---

## 1. Objetivo y alcance

Validar cómo se integraría **Neon** (Postgres serverless + Neon Auth) con la app Flutter,
**en paralelo** a Supabase, sin afectar nada existente:

- **No se modifica Supabase** (proyecto `yzlhvabujsyuiqgaffrc`) — ni datos, ni esquema, ni RLS.
- **No se libera a producción** ningún APK de esta prueba — es exclusivamente para validar en el
  teléfono de pruebas ya conectado.
- Se crea un proyecto nuevo en Neon llamado **`aplicacion_sku`** (sin tilde/espacio en el
  identificador interno, para evitar problemas en connection strings).
- Se copian los datos reales de Supabase a ese proyecto Neon para probar con datos reales, no de
  mentira.
- Se prueba el login con Google contra Neon Auth (Better Auth) y se valida que las
  funcionalidades clave de la app (login, guía de estudio, juegos, guardado de resultados/config)
  funcionen igual que contra Supabase.

Este es un ejercicio de **validación técnica**, no una decisión tomada de migrar. Al final se
evalúa si vale la pena seguir adelante con una migración real.

---

## 2. Qué ya se hizo (antes del reinicio de sesión)

1. Se investigó qué implica migrar de Supabase a Neon (pricing, servicios faltantes/nuevos como
   Neon Auth y Neon Object Storage, RLS, Realtime) — ver resumen en la sección 6 de este
   documento.
2. Se agregó el servidor MCP de Neon a `.mcp.json` (mismo patrón que Supabase, sin secretos en el
   archivo):
   ```json
   "neon": {
     "type": "http",
     "url": "https://mcp.neon.tech/mcp"
   }
   ```
3. El usuario **ya autorizó** el MCP de Neon vía OAuth en el navegador.
4. El usuario **ya creó** un nuevo OAuth Client ID **tipo Web** en Google Cloud Console (mismo
   proyecto que el `GOOGLE_WEB_CLIENT_ID` de producción, pero un client separado, dedicado a esta
   prueba) y tiene guardados el **Client ID** y el **Client Secret** (no compartidos en el chat,
   deben quedar en un `env.json` de prueba, gitignoreado — nunca commitear estos valores).
5. Confirmado: el APK de prueba se firmará con el **mismo keystore de debug** que ya se usa hoy
   → **no** hace falta registrar un Client ID tipo Android nuevo en Google Cloud (el SHA-1 ya
   está dado de alta).

**Pendiente inmediato al reiniciar sesión:** verificar que el MCP de Neon responde (ej. "listar
mis proyectos de Neon") y crear el proyecto `aplicacion_sku`.

## 2.1. Progreso tras el reinicio (2026-07-31)

1. **MCP de Neon verificado** — responde correctamente.
2. **Proyecto Neon creado**: `aplicacion_sku`, `projectId` = `bold-thunder-99588334`, branch
   `main` (`br-muddy-rain-au7n7dgs`), database `neondb`. Connection string con contraseña real
   generada por Neon — no está en ningún archivo trackeado del repo.
3. **Esquema migrado completo**: las 13 tablas de `public`, con los mismos tipos, checks,
   constraints y FKs compuestos exactos que en Supabase (extraídos con
   `pg_get_constraintdef`, no adivinados). Única diferencia deliberada: `perfil_usuario.usuario_id`
   **no tiene todavía** el FK hacia `auth.users(id)` — Neon Auth aún no está configurado (paso 5).
   Se debe agregar ese FK una vez exista el esquema de auth de Neon.
4. **Datos reales migrados y verificados** (conteo exacto Neon == Supabase en las 13 tablas):
   `estatus_producto` 17, `categorias` 98, `subcategorias` 623, `marcas` 547, `productos` 31646,
   `app_config` 1, `perfil_usuario` 14, `usuario_config` 14, `session_logs` 76,
   `resultados_codex` 512, `errores_partida` 427, `reportes_error` 0, `notificaciones_admin` 17.
   Los `usuario_id` (uuid) se preservaron exactamente iguales a los de Supabase.
   - Tablas pequeñas migradas generando INSERTs completos vía `format('%L',...)` +
     `string_agg` desde Supabase, ejecutados tal cual contra Neon.
   - `productos`/`resultados_codex`/`errores_partida` (volumen alto) se migraron con un script
     ad hoc (`migrate_to_neon.py`, en un scratchpad de sesión, **no** en el repo) que lee de
     Supabase vía su REST API (con la `SUPABASE_SERVICE_ROLE_KEY` ya existente en `Data/.env`,
     solo lectura) y escribe a Neon vía `psycopg2` directamente, evitando pasar ~9 MB de datos
     por el contexto del asistente. Si hace falta re-ejecutar la migración de datos desde cero,
     reutilizar ese patrón en vez de generar INSERTs fila por fila.

**Pendiente inmediato ahora:** paso 5, configurar Neon Auth (Better Auth) con Google.

## 2.2. Progreso adicional: Neon Auth, Data API y RLS (2026-07-31/08-01)

5. **Neon Auth provisionado.** Base URL y JWKS URL generados. El proveedor Google se agregó vía
   `add_oauth_provider`, pero **la herramienta MCP no pudo cargar el Client ID/Secret propio**
   (la operación `update_oauth_provider` requiere un parámetro anidado `oauth_provider_config`
   que esta sesión no logra serializar como objeto — falla siempre con "expected object, received
   string", probado con múltiples formatos). El usuario configuró el Client ID/Secret
   manualmente en `console.neon.tech` → proyecto `aplicacion_sku` → Auth → proveedor Google.
   Credenciales guardadas en `env.neon.json` (gitignoreado): `GOOGLE_WEB_CLIENT_ID_NEON`,
   `GOOGLE_CLIENT_SECRET_NEON`.
6. **Hallazgo importante:** Neon (extensión `pg_session_jwt`) expone **`auth.uid()` con la misma
   firma que Supabase** (retorna `uuid` directamente), además de `auth.user_id()` (retorna
   `text`). Esto significa que **no hizo falta reescribir las policies** cambiando `auth.uid()`
   por `auth.user_id()` como se asumía originalmente en la sección 3.6 — se reutilizó `auth.uid()`
   tal cual, sin casts.
7. **RLS migrado**: se recrearon `is_admin()`/`is_approved()` (idénticas a Supabase, mismo body)
   y las 29 políticas de las 13 tablas, con USING/WITH CHECK idénticos a Supabase.
8. **Pieza de arquitectura no contemplada en el plan original: Neon Data API.** Para que la app
   consuma Postgres vía HTTP con JWT (como `supabase_flutter` hace con PostgREST), hace falta
   provisionar el **Data API** de Neon (`provision_neon_data_api`, integrado con Neon Auth). URL:
   guardada en `env.neon.json` como `NEON_DATA_API_URL`. Esto crea los roles Postgres
   `authenticated`/`anonymous`/`authenticator` (no existían antes).
9. **Gotcha descubierto y corregido:** a diferencia de Supabase (donde `anon`/`authenticated` ya
   vienen con GRANTs por defecto sobre las tablas), en Neon **RLS por sí solo no alcanza** — sin
   `GRANT ... ON ALL TABLES IN SCHEMA public TO authenticated` el Data API devuelve
   `permission denied for table` (código `42501`) antes de que la policy de RLS siquiera se
   evalúe. Ya se aplicó el GRANT necesario (incluyendo `ALTER DEFAULT PRIVILEGES` para tablas
   futuras).
10. **RLS verificado extremo a extremo** (no solo "no dio error" — se probó con un JWT real):
    se creó un usuario de prueba vía email/password de Better Auth (método habilitado por
    defecto), se obtuvo un JWT real vía `POST /token` con la cookie de sesión, y se confirmó:
    sin perfil → 0 filas en `categorias`/`perfil_usuario`; con perfil `aprobado` → sí ve
    `categorias`; `INSERT` en `session_logs` con el propio `usuario_id` → 201; `INSERT` con
    `usuario_id` ajeno → 403 "new row violates row-level security policy" (el `with_check`
    funciona). Usuario y filas de prueba ya eliminados de Neon.
11. **Gotcha de continuidad de identidad (pendiente de resolver en el paso 7):** los 14
    `usuario_id` migrados en `perfil_usuario` son los `auth.users.id` de **Supabase**. Cuando un
    usuario real inicie sesión por primera vez vía Neon Auth (Google), Better Auth generará un
    **uuid nuevo y distinto** para ese usuario — no reutiliza el id de Supabase. Sin una
    reconciliación (ej. buscar `perfil_usuario` por `email` en el primer login y re-vincular
    `usuario_id` al nuevo id, o mantener `email` como llave de reconciliación), cada usuario
    existente aparecería como "nuevo" sin su historial. Este es un punto de diseño real para
    `NeonAuthRepository`, no solo una molestia menor de "hay que volver a iniciar sesión".

**Pendiente inmediato ahora:** paso 7, `NeonAuthRepository` en Flutter (incluye resolver el
gotcha de reconciliación de identidad del punto 11).

## 2.3. Hallazgo final y decisión de pausar la prueba (2026-08-01)

Antes de escribir `NeonAuthRepository`, se auditaron los 7 archivos que en realidad dependen de
`supabase_flutter` (no solo `auth_repository.dart` — también `profile_repository.dart`,
`catalog_remote_data_source.dart`, `admin_repository.dart`, `reportes_repository.dart`,
`session_time_syncer.dart`, `pending_game_results_syncer.dart`, todos reciben un
`SupabaseClient` directo en el constructor). El usuario confirmó ir por el swap completo de los
7, no un subconjunto mínimo.

Antes de acometer ese swap, se verificó empíricamente el supuesto central del punto 5 de este
documento ("Better Auth soporta el patrón `signInWithIdToken`"), porque la documentación oficial
de Neon (`docs/auth/guides/setup-oauth.md`) solo describe `signIn.social()` como un **flujo de
navegador/redirect** (abre la página de Google, redirige a `{NEON_AUTH_BASE_URL}/callback/google`,
y de ahí a un `callbackURL` de la app) — nunca menciona el patrón nativo de `idToken` que usa hoy
la app (`google_sign_in` → `idToken` → verificación server-side, sin navegador).

**Prueba realizada:** `POST {NEON_AUTH_BASE_URL}/sign-in/social` con
`{"provider":"google","idToken":{"token":"<JWT con forma válida, firma falsa>"}}`. Resultado:
Neon **ignoró el campo `idToken` por completo** y devolvió siempre el flujo de redirect
(`{"url":"...sign-in/social/init?token=...","redirect":true}`), sin ningún intento de
verificación ni error de token inválido. Se probó dos veces (token simple y JWT con `aud`
coincidiendo con nuestro Client ID) con el mismo resultado.

**Conclusión:** Neon Managed Better Auth (Beta, al 2026-08-01) **no soporta el inicio de sesión
nativo vía `idToken`** para Google — solo el flujo de navegador/redirect. Esto contradice la
asunción original del punto 5 y tiene una consecuencia real de UX: migrar el login de esta app a
Neon significaría cambiar de "botón nativo de Google, un toque" a "abrir un navegador/Custom Tab,
elegir cuenta ahí, volver a la app por un deep link" — un cambio de experiencia de usuario, no
solo un cambio de backend.

**Decisión del usuario:** tratar este hallazgo como el resultado final de la prueba de login y
**pausar aquí** — no se construyó el flujo de navegador/deep-link ni el swap de los 7
repositorios. `NeonAuthRepository` y el resto del código Flutter específico de Neon **no se
implementaron**.

## 3. Evaluación final (responde a la pregunta de la sección 1)

**¿Qué se validó y funcionó bien?**
- Esquema completo migrado 1:1 (13 tablas, mismos tipos/checks/FKs compuestos).
- Datos reales migrados y verificados por conteo exacto (incluye `productos` con 31,646 filas).
- RLS migrado y probado extremo a extremo con un JWT real (no solo "no dio error"): bloqueo sin
  perfil aprobado, acceso correcto con perfil aprobado, `with_check` rechazando escritura a
  nombre de otro usuario.
- Data API (PostgREST-compatible) provisionado y funcional una vez agregados los `GRANT`
  necesarios (gotcha no documentado: Neon no otorga privilegios de tabla por defecto a
  `authenticated`, a diferencia de Supabase).
- Costo en el free tier: sigue siendo $0 a esta escala.

**¿Qué fricción real se encontró (la pregunta central del ejercicio)?**
1. La herramienta MCP de Neon no permite configurar el Client ID/Secret propio de OAuth vía
   automatización en este entorno (bug de serialización) — requirió configuración manual del
   usuario en la consola.
2. Neon Auth no expone por defecto un rol con permisos de tabla — hay que otorgarlos
   explícitamente (`GRANT ... TO authenticated`), a diferencia de Supabase.
3. **El hallazgo más importante:** Neon Managed Better Auth no soporta login nativo por
   `idToken` en Android — solo redirect de navegador. Adaptar la app a esto es un cambio de UX
   real (agregar un flujo de navegador/deep-link), no un simple cambio de repositorio de datos.
4. Continuidad de identidad de usuarios existentes (sección 2.2, punto 11): los `usuario_id`
   migrados no coincidirán con los ids que Better Auth genere en el primer login real; requiere
   una reconciliación por email que no se llegó a implementar.
5. No hay SDK oficial de Better Auth para Flutter/Dart (confirmado, ya se sabía de antemano).

**¿Vale la pena seguir adelante con una migración real?** Con la información recogida hasta
aquí: la migración de datos/esquema/RLS es mecánica y de bajo riesgo (ya validada). El punto que
cambia el cálculo es el de login — no es un simple intercambio de backend, sino un rediseño de la
pantalla de login y del flujo de autenticación en Android. Decisión pendiente del usuario sobre
si esa fricción de UX justifica seguir, dado lo demás ya validado favorablemente.

**Estado del proyecto Neon de prueba:** ~~queda intacto en Neon~~ **descartado y eliminado**
(ver sección 4).

---

## 4. Cierre (2026-08-01): prueba descartada

Se intentó construir el flujo de login vía navegador (la alternativa al `idToken` nativo, ver
2.3) y se encontró un bloqueo aún más duro y concluyente: la API de Neon Auth
(`add_trusted_origin`) **rechaza explícitamente cualquier esquema que no sea `http`/`https`** en
el destino del login (`"Scheme \"skusappneon\" is not allowed; use http or https"`). Esto
descarta un deep link con esquema personalizado (`miapp://...`) — el mecanismo que usa hoy la
app y cualquier app nativa Android/iOS sin dominio propio. La única vía que la API permite es un
**Android App Link** real (URL `https://` bajo un dominio propio, con `assetlinks.json`
publicado y verificación de Android) — infraestructura real (dominio + hosting), no un ajuste de
código.

**Decisión final del usuario:** no vale la pena esa inversión de infraestructura solo para esta
prueba técnica. Se descartó la migración a Neon y se revirtió todo:
- Proyecto Neon `aplicacion_sku` (`bold-thunder-99588334`) **eliminado por completo** (esquema,
  datos, Neon Auth, RLS, Data API — todo).
- `env.neon.json` (con el Client ID/Secret de Google de prueba) **eliminado** del repo.
- Ningún archivo de código Flutter llegó a modificarse (`NeonAuthRepository` nunca se escribió) —
  no hubo nada que revertir ahí.
- Supabase (producción) no se tocó en ningún momento de este ejercicio.

**Para consulta futura si el tema resurge:** las secciones 2–3 documentan en detalle lo que sí
se validó bien (esquema, datos, RLS con `auth.uid()` nativo, Data API con `GRANT`s explícitos) y
las dos fricciones de login encontradas (sin `idToken` nativo; sin soporte de esquemas custom en
el callback). Este documento puede archivarse o borrarse — ya cumplió su propósito.

---

## 3. Próximos pasos (en orden)

1. **Verificar acceso a Neon** vía MCP (listar proyectos) tras el reinicio.
2. **Crear el proyecto Neon `aplicacion_sku`.**
3. **Migrar el esquema** de Supabase a Neon: las 13 tablas de `public` (ver sección 5) con sus
   mismos tipos, constraints, checks y foreign keys. Es esquema puro Postgres, no hay nada
   Supabase-específico en las tablas de negocio (sí lo hay en `auth.*`, ver punto 5).
4. **Migrar los datos reales**, preservando exactamente los mismos `usuario_id` (uuid) para no
   romper ninguna relación — este es el punto más delicado, no los datos de negocio en sí.
   Volúmenes reales (verificados por consulta directa, no por el conteo estimado de la UI):
   - `auth.users`: 14 (100% login por Google, ninguna contraseña)
   - `perfil_usuario` / `usuario_config`: 14 / 14
   - `session_logs`: 74
   - `resultados_codex`: 511
   - `errores_partida`: 417
   - `notificaciones_admin`: 17
   - `reportes_error`: 0
   - Tamaño total de datos de negocio: ~10 MB (cabe holgadamente en el free tier de Neon: 0.5 GB).
5. **Configurar Neon Auth (Better Auth)** con el Client ID/Secret de Google ya creados, replicando
   el flujo nativo que ya usa la app: `GoogleSignIn.instance.authenticate()` → `idToken` →
   verificación server-side. Better Auth soporta este mismo patrón (`signInWithIdToken`).
6. **Reescribir las políticas RLS** para Neon: hoy todas usan `auth.uid()` (mecanismo de
   Supabase); en Neon el equivalente es `auth.user_id()` (extensión `pg_session_jwt`). Sin esto,
   el riesgo real no es un error visible sino un **no-op silencioso** (ya nos pasó una vez con
   Supabase — sección 6.2 de `CONTEXTO_DESARROLLO.md`, tabla `errores_partida` sin política de
   UPDATE). Cada tabla con RLS debe probarse explícitamente después de migrar la política, no
   asumir que "no dio error" significa que funcionó.
7. **Nueva implementación de `AuthRepository`** para Neon (ej. `NeonAuthRepository`), sin tocar
   `SupabaseAuthRepository` — la interfaz abstracta `AuthRepository` ya existe
   (`lib/features/auth/data/auth_repository.dart`) y está pensada justo para esto: intercambiar
   la implementación sin tocar el resto de la app. Evaluar paquetes de comunidad `better_auth_flutter`
   o `flutter_better_auth` (pub.dev) — no hay SDK oficial de Better Auth para Flutter, a
   diferencia de `supabase_flutter` que sí es oficial.
8. **Nuevo `env.json` de prueba** (no tocar el actual) con las variables de Neon + el nuevo
   `GOOGLE_WEB_CLIENT_ID` de prueba, compilando un APK de prueba aparte
   (`--dart-define-from-file=env.neon.json` o similar) para no interferir con builds normales.
9. **Probar en el teléfono ya conectado** (`MTN NX3`, Android 16 arm64, device id
   `ASNUVB5C12002875`, ya autorizado para `flutter run`): login con Google, guardado de
   resultados de juego, configuración de usuario, y verificar cada escritura contra la base real
   (no solo "no tiró error" — aplicar la misma disciplina que ya se usa con Supabase).
10. **Evaluar resultado**: ¿funcionalidades equivalentes? ¿qué fricción real hubo? ¿vale la pena
    seguir? — esto no está decidido de antemano.

---

## 4. Restricciones duras (no negociables durante esta prueba)

- Cero escrituras/cambios en el proyecto Supabase de producción (`yzlhvabujsyuiqgaffrc`).
- Cero distribución del APK de prueba fuera del dispositivo de pruebas.
- Los usuarios reales de producción siguen operando 100% sobre Supabase mientras dure esta
  validación.

---

## 5. Esquema de referencia (Supabase, `public`, todas con RLS activo)

```
categorias (PK: codigo, sede)
subcategorias (PK: categoria_codigo, codigo, sede) → FK categorias
marcas (PK: id)
productos (PK: id) → FK subcategorias, FK estatus_producto
app_config (PK: clave)
estatus_producto (PK: codigo)
perfil_usuario (PK: usuario_id) → FK auth.users.id  ← puente hacia el esquema de Auth
usuario_config (PK: usuario_id) → FK perfil_usuario
session_logs (PK: id) → FK perfil_usuario
resultados_codex (PK: id) → FK perfil_usuario
errores_partida (PK: id) → FK perfil_usuario, FK resultados_codex
reportes_error (PK: id) → FK perfil_usuario
notificaciones_admin (PK: id) → FK perfil_usuario (nullable)
```

Todas las tablas de negocio cuelgan, directa o indirectamente, de `perfil_usuario.usuario_id`,
que a su vez es FK a `auth.users.id` (el esquema interno de Supabase Auth). Esa es la única pieza
que no es "solo datos" — es el punto donde el mecanismo de autenticación entra al modelo de
datos.

---

## 6. Resumen de la investigación previa (contexto, ya no hace falta rehacerla)

- **Pricing:** Neon free tier (0.5 GB storage, 100 CU-hora/mes) cubre de sobra el volumen actual
  (~10 MB). El costo de hosting en sí sería $0/mes en esta escala.
- **Lo que Neon no tiene:** Realtime nativo (no se usa en esta app, así que no aplica). RLS no
  viene habilitado por defecto, hay que activarlo y escribir las políticas.
- **Lo que Neon sí tiene (agregado recientemente, en Beta):** Neon Auth (Better Auth) y Neon
  Object Storage (S3-compatible). Al estar en Beta, hay riesgo de cambios de API/estabilidad
  frente a Supabase Auth ya maduro.
- **Usuarios 100% Google OAuth** (confirmado: 14/14 identidades en `auth.identities` son
  `google`, ninguna tiene contraseña) → el problema típico de migrar hashes de contraseña
  (bcrypt vs. scrypt) **no aplica**. Sí aplica igual, sin importar el proveedor de auth elegido:
  las sesiones activas se invalidan y los 14 usuarios deben volver a iniciar sesión una vez
  (fricción baja porque no hay contraseña que recordar, solo tocar "Continuar con Google" de
  nuevo).
- **Fricción real esperada:** reescribir la capa de auth en Flutter con un paquete de comunidad
  (no oficial), reconfigurar/verificar el client de Google en la nueva plataforma, y reescribir
  las políticas RLS — no la migración de los datos en sí, que es mecánica y de bajo riesgo.
