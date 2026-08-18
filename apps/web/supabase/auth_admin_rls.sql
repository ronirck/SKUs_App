-- Ejecutar una sola vez en el SQL Editor de Supabase (proyecto yzlhvabujsyuiqgaffrc).
--
-- Cierra el panel web: deja de estar abierto al rol anon y pasa a exigir una
-- sesión de Google cuyo perfil sea administrador aprobado. Reemplaza a
-- anon_rls.sql, que era el arreglo temporal para correr solo en localhost.
--
-- Importante: el login del panel es la puerta que ve el usuario; lo que de
-- verdad protege los datos es este archivo. Sin ejecutarlo, cualquiera con la
-- URL desplegada sigue pudiendo leer y editar sin iniciar sesión.

-- 1. ¿Quién es administrador? Misma tabla que usa la app móvil.
--
-- SECURITY DEFINER a propósito: la función se llama desde políticas de otras
-- tablas y, sin esto, leer perfil_usuario volvería a disparar las políticas de
-- perfil_usuario (recursión). Se fija search_path para que no se pueda
-- secuestrar el nombre de la tabla.
create or replace function public.es_admin_aprobado()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.perfil_usuario p
    where p.usuario_id = auth.uid()
      and p.rol = 'admin'
      and p.estado = 'aprobado'
  );
$$;

revoke all on function public.es_admin_aprobado() from public;
grant execute on function public.es_admin_aprobado() to authenticated;

-- 2. Quitar el acceso anónimo que daba anon_rls.sql.
drop policy if exists "web_anon_select_productos" on public.productos;
drop policy if exists "web_anon_select_estatus_producto" on public.estatus_producto;
drop policy if exists "web_anon_update_mnemotecnia" on public.productos;

revoke update (mnemotecnia) on public.productos from anon;
revoke select on public.productos from anon;
revoke select on public.estatus_producto from anon;

-- 3. Lectura del catálogo para cualquier usuario autenticado.
--    (La app móvil ya depende de esto; se declara aquí para que el panel
--     funcione aunque las políticas se hayan creado de otra forma.)
grant select on public.productos to authenticated;
grant select on public.estatus_producto to authenticated;

drop policy if exists "web_auth_select_productos" on public.productos;
create policy "web_auth_select_productos" on public.productos
  for select to authenticated using (true);

drop policy if exists "web_auth_select_estatus_producto" on public.estatus_producto;
create policy "web_auth_select_estatus_producto" on public.estatus_producto
  for select to authenticated using (true);

-- 4. Editar la mnemotecnia: solo administradores aprobados.
--
--    El GRANT de columna es lo único que impide tocar otras columnas de
--    productos; la política por sí sola no puede acotar columnas.
grant update (mnemotecnia) on public.productos to authenticated;

drop policy if exists "web_admin_update_mnemotecnia" on public.productos;
create policy "web_admin_update_mnemotecnia" on public.productos
  for update to authenticated
  using (public.es_admin_aprobado())
  with check (public.es_admin_aprobado());

-- 5. Que cada quien pueda leer su propio perfil (lo que el panel consulta
--    para decidir si deja pasar). Si la app móvil ya tiene una política
--    equivalente, esta simplemente se suma.
grant select on public.perfil_usuario to authenticated;

drop policy if exists "web_auth_select_perfil_propio" on public.perfil_usuario;
create policy "web_auth_select_perfil_propio" on public.perfil_usuario
  for select to authenticated using (usuario_id = auth.uid());

-- Para comprobar que quedó bien, con una sesión iniciada:
--   select public.es_admin_aprobado();          -- true solo para admins
--   update public.productos set mnemotecnia = mnemotecnia where false;
--
-- Para revertir al estado abierto anterior, volver a ejecutar anon_rls.sql
-- y borrar lo de aquí:
--   drop policy "web_admin_update_mnemotecnia" on public.productos;
--   drop policy "web_auth_select_productos" on public.productos;
--   drop policy "web_auth_select_estatus_producto" on public.estatus_producto;
--   drop policy "web_auth_select_perfil_propio" on public.perfil_usuario;
--   drop function public.es_admin_aprobado();
