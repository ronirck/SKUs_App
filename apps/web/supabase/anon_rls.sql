-- Ejecutar una sola vez en el SQL Editor de Supabase (proyecto yzlhvabujsyuiqgaffrc).
-- Da al rol anon lectura del catálogo y escritura acotada a productos.mnemotecnia,
-- para que apps/web (SPA sin backend propio) pueda funcionar sin la service role key.
--
-- La política RLS de UPDATE no puede por sí sola restringir qué columnas se tocan
-- — esa restricción la da únicamente el GRANT de columna. Sin auth todavía, esto
-- significa que cualquiera con la URL desplegada puede editar la mnemotecnia de
-- cualquier producto: aceptable mientras el panel corra solo en localhost (ver
-- README.md), no antes de desplegarlo en un entorno compartido.

grant select on public.productos to anon;
grant select on public.estatus_producto to anon;
grant update (mnemotecnia) on public.productos to anon;

create policy "web_anon_select_productos" on public.productos
  for select to anon using (true);

create policy "web_anon_select_estatus_producto" on public.estatus_producto
  for select to anon using (true);

create policy "web_anon_update_mnemotecnia" on public.productos
  for update to anon using (true) with check (true);

-- Para revertir:
-- drop policy "web_anon_select_productos" on public.productos;
-- drop policy "web_anon_select_estatus_producto" on public.estatus_producto;
-- drop policy "web_anon_update_mnemotecnia" on public.productos;
-- revoke select on public.productos from anon;
-- revoke select on public.estatus_producto from anon;
-- revoke update (mnemotecnia) on public.productos from anon;
