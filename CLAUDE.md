# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo shape

This is a monorepo with two apps sharing one Supabase backend (Postgres + Auth + RLS):

- **`apps/mobile/`** — the Flutter/Android app (study guide + quiz games for memorizing product
  codes). See **`apps/mobile/CLAUDE.md`** for its commands and architecture — read that file
  before working on anything under `apps/mobile/`.
- **`apps/web/`** — a Vite/React SPA for browsing the loaded product catalog (search by
  name/code, filter by sede/infaltables) and viewing/editing each product's mnemotecnia. No
  backend of its own — talks to Supabase directly with the anon key, access controlled entirely
  by RLS. MVP, deliberately without auth yet (localhost-only). See **`apps/web/README.md`** for
  setup/scope and **`apps/web/CLAUDE.md`** before working on anything under `apps/web/`.

`Data/` (root, gitignored) holds Python scripts that load/reconcile the catalog into Supabase from
per-sede Excel files — shared context for both apps since they read the same catalog. See
`Data/reglas_carga.md` before writing a new load/reconciliation script.

`PLAN_PRUEBA_NEON.md` (root) is an in-progress, non-committal evaluation of Neon as a possible
future replacement for Supabase — relevant to both apps, not mobile-specific.

Both apps read/write the *same* Supabase project — a schema change (tables, RLS) made for one app
affects the other. `apps/mobile/CLAUDE.md`'s "Database schema notes" section documents non-obvious
schema quirks (e.g. Supabase truncating unpaginated reads at 1000 rows) that apply equally to
`apps/web/` and to `Data/` scripts.

## Working in this repo

There is no root-level build/test — each app is self-contained under `apps/<name>/` with its own
commands (see that app's CLAUDE.md/README). `cd` into the relevant app directory before running
its tooling (e.g. `flutter` commands must run from `apps/mobile/`, `npm` commands from
`apps/web/`).

This project has `supabase` (read-only) and `neon` MCP servers configured in `.mcp.json`.
