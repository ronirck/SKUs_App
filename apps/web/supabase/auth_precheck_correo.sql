-- Ejecutar una sola vez en el SQL Editor de Supabase, después de
-- auth_admin_rls.sql.
--
-- Permite que la pantalla de acceso avise "este correo no tiene permiso"
-- ANTES de mandar al usuario a Google, en vez de dejarlo dar toda la vuelta
-- para rebotar al volver.
--
-- Compromiso consciente: al ser llamable por anon, cualquiera puede preguntar
-- si un correo concreto es administrador y obtener sí/no. Es enumeración de
-- correos, hay que saber la dirección exacta y solo devuelve un booleano —
-- nada de nombres, ids ni listados. Si ese riesgo no se acepta, no ejecutes
-- este archivo: la app sigue funcionando, solo que el rechazo ocurre después
-- de pasar por Google.
--
-- Esto NO es el control de acceso: en la pantalla de Google se puede elegir
-- otra cuenta. El permiso real lo decide la verificación posterior al login
-- (es_admin_aprobado + auth_admin_rls.sql).

create or replace function public.correo_puede_entrar(correo text)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from auth.users u
    join public.perfil_usuario p on p.usuario_id = u.id
    where lower(u.email) = lower(trim(correo))
      and p.rol = 'admin'
      and p.estado = 'aprobado'
  );
$$;

revoke all on function public.correo_puede_entrar(text) from public;
grant execute on function public.correo_puede_entrar(text) to anon, authenticated;

-- Comprobación:
--   select public.correo_puede_entrar('un-admin@mayoreo.biz');  -- true
--   select public.correo_puede_entrar('cualquiera@gmail.com');  -- false
--
-- Para revertir:
--   drop function public.correo_puede_entrar(text);
