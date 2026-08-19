-- Ejecutar en el SQL Editor de Supabase, después de auth_admin_rls.sql.
--
-- La pestaña de clasificación escribe productos.estatus, y hasta ahora los
-- administradores solo tenían permiso sobre productos.mnemotecnia. Ese GRANT
-- de columna es justamente lo que impide tocar el resto de la tabla, así que
-- hay que sumar la columna nueva de forma explícita.
--
-- La política de UPDATE ya existente (web_admin_update_mnemotecnia) sigue
-- valiendo: acota QUIÉN puede escribir (solo admin aprobado). El GRANT acota
-- QUÉ columnas. Se necesitan las dos cosas.

grant update (estatus) on public.productos to authenticated;

-- Comprobación, con sesión de administrador:
--   update public.productos set estatus = estatus where false;  -- sin error
--
-- Para revertir:
--   revoke update (estatus) on public.productos from authenticated;
