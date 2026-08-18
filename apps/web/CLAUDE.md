# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this directory
(`apps/web/`), part of the SKUs App monorepo — see the root `CLAUDE.md` for how this fits
alongside `apps/mobile/`. All commands below assume `apps/web/` as the working directory.

## Project

Internal Vite + React SPA for browsing the product catalog loaded in Supabase and viewing/editing
each product's `mnemotecnia`. Shares the same Supabase project as `apps/mobile/` — same tables
(`categorias`, `subcategorias`, `productos`, `estatus_producto`); see
`apps/mobile/CLAUDE.md` ("Database schema notes") for schema quirks that apply here too (e.g.
Supabase truncating unpaginated reads at 1000 rows).

**No backend of its own.** Originally a Next.js app with API routes that used the service role
key server-side; migrated to a plain Vite SPA (Turbopack couldn't reliably write to `.next/` when
this repo is accessed from WSL over `/mnt/c/...`). Without a server to hide a secret in, the
browser talks to Supabase directly with the anon key, and access control moved entirely into
Postgres RLS policies for the `anon` role — see "Database access" below.

## Commands

```bash
npm install   # first time / after dependency changes
npm run dev   # http://localhost:5173
npm run build
npm run lint
```

`.env.local` (gitignored) already has real Supabase credentials for local dev; `.env.local.example`
is the template. `VITE_SUPABASE_ANON_KEY` is meant to be public — Vite inlines any `VITE_`-prefixed
var into the client bundle by design. There is no service role key anywhere in this app anymore.

## Architecture

- `src/App.tsx` — the corporate shell: `Encabezado` (logo + "Grupo Mayoreo" cintillo), the table,
  and a footer.
- `src/components/ProductosTable.tsx` — the working UI: sede selector, name/code search, "solo
  infaltables" filter, and inline mnemotecnia editing. **The list is virtualized**
  (`@tanstack/react-virtual`) and is not a `<table>`: header and rows are separate CSS grids
  sharing the `COLUMNAS_GRID` template, with ARIA `table`/`row`/`cell` roles. Rendering the whole
  catalog put ~6,200 rows and 37,000 cells (5 MB) in the DOM, and every filter or edit forced
  React to reconcile all of them — the page froze and Chrome showed "not responding". Virtualized
  it holds ~17 rows / 102 cells (44 KB). Row heights are **measured**, not fixed
  (`measureElement`): product names wrap to two lines and the editing row grows with its textarea.
  Search filtering runs on a `useDeferredValue` copy of the query so typing stays responsive.
- `src/components/EtiquetaEmpresa.tsx` — the canonical "10 px dot + company name" label.
- `src/components/CargarExcel.tsx` + `src/lib/excel.ts` — bulk mnemotecnia upload from an Excel
  with two columns, `Código` (format `xx-xx-xxx`) and `Mnemotecnia`. Parsing is browser-side via
  `read-excel-file`, imported **dynamically inside the parse function** so its ~64 KB (19 KB
  gzipped) ship as their own chunk, loaded only when someone picks a file, instead of weighing on
  every page load; keep it that way — a top-level import puts it back in the entry bundle.
  **Import `readSheet` from `read-excel-file/browser`** — the package exposes
  no root export, and its default export returns `Sheet[]` (`{sheet, data}`), not rows. The file
  carries no sede, so rows are matched against the *currently selected* casa by
  `codigo_completo ?? codigo`, and nothing is written until the user confirms the review panel
  (por aplicar / ya iguales / con problema). Empty mnemotecnia cells are skipped, never used to
  blank an existing value. Writes reuse `updateMnemotecnia` through `updateMnemotecniasEnLote`
  (batches of 5). `ejemplos/mnemotecnias-prueba.xlsx` is a two-row sample for manual testing.
  Note the modal renders through `createPortal` to `document.body`: its trigger sits inside a
  `.animar-entrada` card, and an ancestor running a `transform` animation becomes the containing
  block for `fixed` descendants, which clipped the overlay inside the card.
- `src/theme/marca.ts` — brand palette resolved at runtime (`MARCA`, `COLOR_EMPRESA`,
  `colorEmpresa()`, `suave()`); `src/index.css` holds the same hex as Tailwind `@theme` tokens
  (`marca-negro`, `marca-gris`, …). Change one, change the other.
- `src/lib/api.ts` — `fetchAllProductos` (paginates past Supabase's 1000-row limit, same rule the
  mobile app follows; the first page carries `count: "exact"` and the rest are fetched **in
  parallel**, 6 at a time — each request costs ~1.2 s of latency and only ~75 KB gzipped, so
  serial paging wasted round trips: measured 9.2 s → 2.3 s for FEBECA's 7 pages. Pages are stored
  by index and concatenated so the `order by id` sequence survives),
  `fetchEstatusProducto`, `updateMnemotecnia` (trims to `null` on empty,
  throws if the row didn't come back — same "verify the write, don't trust no-error" discipline
  used elsewhere in this repo).
- `src/lib/supabaseClient.ts` — the one place the Supabase client is created, with the anon key.

## Visual format: the Grupo Mayoreo brand system

This panel follows the corporate format defined in `formato-mayoreo/` at the repo root (SKILL.md
plus `references/paleta.md`, `interfaz.md`, `voz.md`; the authoritative pantonera PDF lives in its
`assets/`). **Read it before changing anything that has appearance.** The rules that shape this
app's code:

- **Grayscale base + company color only as an accent.** Black `#1d1d1b` / gray `#c6c6c6` / white,
  app background `#fafafa`. If a screen looks colorful, it's wrong. The primary button is always
  black — never the company accent.
- **The accent never identifies a house on its own**: cyan is Febeca *and* Cofersa, lime is Beval
  *and* Mundipartes. Always dot + name in text (`EtiquetaEmpresa`). Lime `#ccdb2a` never carries
  white text — chips use the accent at 14 % opacity (`suave()`) with black text.
- **Light theme only**, deliberately: the panel must match the mobile app regardless of the OS
  setting. Don't add a dark mode without agreeing on it.
- No brand font — `system-ui, "Segoe UI", Roboto, sans-serif`, and no Google Fonts. Headings get
  `letter-spacing: -0.01em`; institutional labels use the `.versalita` class.
- Motion tokens (`--ease-salida`, `--dur-*`), the `.animar-entrada` / `.skeleton` / `.elevar`
  utilities and the `prefers-reduced-motion` override live in `src/index.css`.
- UI text is Venezuelan Spanish, `tú`, buttons in the infinitive with no trailing period; errors
  say what happened and what to do.

**The logo is imported from `src/assets/`, not served from `public/`** — on this repo accessed
from WSL over `/mnt/c/...`, `copyFileSync` fails with `EPERM`, so anything in `public/` breaks
`vite build` when it copies the folder. Importing it makes rollup emit the asset instead. Same
family of WSL/DrvFs problem that pushed this app off Next.js. Related: Vite's file watcher gets no
inotify events on `/mnt/c`, so HMR doesn't pick up edits — restart `npm run dev` to see changes.

## Authentication: Google login, admins only

`src/App.tsx` is the auth gate: no session → `Login.tsx` (email field + "Conectar con Google").
The typed email is passed to Google as `login_hint` and is **not** an access check — the user can
pick any account on Google's screen. Authorization happens after the redirect, against
`perfil_usuario` (the same table the mobile app uses): `rol = 'admin'` and `estado = 'aprobado'`
(`puedeEntrar` in `src/lib/auth.ts`). An authenticated non-admin is signed out again with an
explanation rather than left in a half-usable panel.

The Supabase client needs `persistSession: true` and `detectSessionInUrl: true` — the OAuth
tokens come back in the URL hash and the session must survive the redirect and reloads.

**The login is only the visible door.** What actually protects the data is
`supabase/auth_admin_rls.sql` (run once in the SQL Editor): it revokes the `anon` grants from
`anon_rls.sql` and scopes `update (mnemotecnia)` to admins via `es_admin_aprobado()`, a
`security definer` function — reading `perfil_usuario` from inside another table's policy would
otherwise re-trigger `perfil_usuario`'s own policies and recurse. Supabase's dashboard also needs
the Google provider enabled and the app's URLs in the redirect allowlist; neither can be done from
an agent session here (the MCP is read-only).

## Database access: RLS is the whole security model here

`supabase/anon_rls.sql` is not optional setup — without it the app loads but every query returns
empty/errors, since `productos`/`estatus_producto` have RLS enabled with policies only for
`authenticated` (written for the mobile app), nothing for `anon`. It grants `anon`: `SELECT` on
`productos` and `estatus_producto`, and `UPDATE` scoped to `productos.mnemotecnia` only via a
column-level `GRANT` (an RLS `UPDATE` policy alone cannot restrict which columns get touched —
only the column `GRANT` can). Run it once in the Supabase SQL Editor for the project; it can't be
applied from an agent session in this repo (the `supabase` MCP in `.mcp.json` is `read_only=true`,
and there's no Postgres connection string or Management API token checked in).

**Deliberately no authentication yet** — this is meant to run on `localhost` only. Because the
anon key is public by design and the RLS policies above are wide open (`using (true)`), anyone who
reaches a deployed URL of this app could read the full catalog and edit any product's mnemotecnia.
Before deploying anywhere network-accessible, auth needs to be decided (same Google + `admin` role
login as mobile, or something separate) and the RLS policies in `anon_rls.sql` need to be tightened
to require an authenticated session instead of being open to `anon`.
