# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
directory (`apps/mobile/`), part of the SKUs App monorepo — see the root `CLAUDE.md` for how this
fits alongside `apps/web/`. All commands below assume `apps/mobile/` as the working directory.

## Project

**SKUs App** — a mobile learning app that helps distributor employees memorize a product/SKU
catalog through a study guide and quiz games. Built with **Flutter/Dart**, backed by **Supabase**
(Postgres + Auth + RLS). This is a full rewrite of an earlier Flet/Python version, which is
archived (read-only reference, excluded from analysis) in `_old/`.

## Commands

```bash
# Local dev — env vars are compiled in, not read from .env at runtime
flutter run --dart-define-from-file=env.json
flutter build apk --dart-define-from-file=env.json

# Tests
flutter test
flutter test test/features/game/domain/quiz_engine_test.dart   # single file

# Lint/analyze
flutter analyze

# Regenerate drift database code after editing app_database.dart
dart run build_runner build --delete-conflicting-outputs

# Regenerate app icon (after replacing assets/icon/icon_legacy.png or icon_foreground.png)
dart run flutter_launcher_icons

# Publish a GitHub release (reads version from pubspec.yaml, APK from
# build/app/outputs/flutter-apk/app-release.apk, GITHUB_TOKEN from root .env)
python release.py
```

Before first run, copy `env.example.json` to `env.json` (gitignored) and fill in
`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `GITHUB_REPO`, `GOOGLE_WEB_CLIENT_ID` — see README.md for
what each is and why. There is no `GITHUB_TOKEN` in `env.json` (that file is compiled into the
APK); the token used by `release.py` to publish releases lives only in a root `.env`.

## Architecture

### Layout: feature-first, layered within each feature

`lib/features/<feature>/{data,domain,presentation}/`. `domain/` holds pure Dart (no Flutter
imports) — testable in isolation and where business rules live (filtering, scoring, version
comparison, distractor selection, etc.). `data/` holds repositories and remote/local data
sources. `presentation/` holds screens and widgets. Shared infra lives in `lib/core/`
(`config/app_config.dart`, `database/app_database.dart` (drift), `theme/`, `utils/`).

Features: `auth`, `catalog`, `game`, `session`, `profile`, `admin`, `reportes`, `updates`, `home`.

### Offline-first catalog

The catalog (categorías → subcategorías → productos) is cached locally in SQLite via `drift`
(`lib/core/database/app_database.dart`). `CatalogGate` downloads/refreshes the cache after
approval, filtered by the user's `sede` + `marcas_permitidas`; the Guía de Estudio and all quiz
modes read only from this local cache, never from the network directly. Cache rebuilds are
triggered by a `config_version` bump (admin changed a user's config) or `version_datos` bump
(catalog data changed). `solo_infaltables` is a session-only UI filter over the full cached
catalog, not a download restriction — sede/marcas_permitidas are the only real access
restrictions applied at download time.

### Sync model

Game results (`resultados_codex`, `errores_partida`) and session time (`session_logs`) are
written to Supabase, but writes are queued locally (drift tables `PendingGameResults`,
`PendingSessionTime`) when offline and flushed on: app resume, app open (`CatalogGate`), and
network reconnection detected via `connectivity_plus` (including while the app is backgrounded —
no real background service is used; retry-on-resume/reconnect was judged sufficient). See
`PendingGameResultsSyncer`, `SessionTimeSyncer`.

### Auth & roles

Google sign-in only (`supabase_flutter` + `google_sign_in`), no passwords. `perfil_usuario` links
to the Supabase Auth user via `usuario_id` (not `id`). Roles are `user` and `admin`; both share
the exact same `HomeShell` navigation and screens (Guía, Desafíos, Perfil) — `admin` just gets an
extra "Usuarios" tab, with no other code branching by role. New users pass through
pendiente → aprobado/rechazado, with polling and a locally cached last-known profile
(`shared_preferences`) so the app doesn't require network on every launch to check approval
status. The onboarding demo (`lib/features/game/demo/`) runs the real screens against an
in-memory drift database seeded with fake data, so pending users can explore the actual UI
without touching the real backend or RLS.

### Game engine

`QuizEngine` (`lib/features/game/domain/quiz_engine.dart`) powers all 4 modes (categorías,
subcategorías, productos, contrarreloj) by varying the item source and priority-ordered
distractor picking (`distractor_picker.dart`) — distractors are always real catalog codes, never
invented. Contrarreloj is time-boxed (90s), not question-count-boxed like the other three modes.

### In-app updates

`UpdateChecker` compares the installed version (`package_info_plus`) against
`GET /repos/$GITHUB_REPO/releases/latest` on the public GitHub API (no auth needed, 60 req/hr/IP
limit). Version parsing/comparison, changelog extraction, and role targeting (`APP_TARGET`
marker in the release body) are pure functions in `lib/features/updates/domain/`, ported from the
old Python `updater.py`. A release titled with `[CRITICAL]` shows a non-dismissible blocking
dialog instead of a dismissible banner.

### Database schema notes (Supabase)

These are non-obvious things learned by hitting them, not visible from the Dart code alone:

- `perfil_usuario` and `usuario_config` are separate tables joined client-side by `usuario_id`,
  not joined in the database.
- `subcategorias.codigo` repeats across categories — the real key is
  `(categoria_codigo, codigo)`.
- `estatus_producto` is a lookup table of status *types* (`productos.estatus` →
  `estatus_producto.codigo` → `es_infaltable`), not one row per product.
- `app_config` is a key-value table (`clave`/`valor`); `version_datos` is a row there, not a
  column.
- `usuario_config.marcas_permitidas` is `text[]` of brand *names*, not uuids.
- A Postgres RLS policy that allows INSERT/SELECT but not UPDATE lets an `UPDATE` statement
  execute without error while silently not applying the change — always verify writes by
  re-reading, don't trust the absence of an error.
- Supabase truncates unpaginated reads at 1000 rows with no error/warning — any full-table read
  (in the app or in one-off scripts) must paginate. See `fetch_all_pages.dart` and the
  `get_all`-style pattern used in `Data/*.py` scripts.

### Data loading scripts (`Data/`)

One-off/repeatable Python scripts for bulk-loading and reconciling the product catalog from
distributor Excel files (`FEBECA.xlsx`, `SILLACA.xlsx`) into Supabase — `cargar_datos.py`
(load, has a dry-run mode), `verificar_datos.py`/`verificar_estatus.py` (post-load verification),
`reconciliar_nombres.py` (name conflict resolution, has a read-only mode and `--aplicar`). Rules
and precedent for these loads (which source wins on conflicts, how "infaltable" status is
assigned, per-sede scoping) are recorded in `Data/reglas_carga.md` — read it before writing a new
load/reconciliation script, since the conventions there aren't otherwise derivable from the code.

## Also present

- `CONTEXTO_DESARROLLO.md` — long-form development history/journal of the Flutter rebuild,
  phase by phase, including decisions and their rationale. Consult it for *why* something is
  built the way it is; not needed for routine changes.
- `PLAN_PRUEBA_NEON.md` — active working notes for an in-progress, non-committal technical
  evaluation of Neon (Postgres + Neon Auth) as a possible future replacement for Supabase.
  Supabase remains the only backend actually used by the app; nothing here is wired up yet.
