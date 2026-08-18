import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    "Faltan VITE_SUPABASE_URL o VITE_SUPABASE_ANON_KEY. Copia .env.local.example a .env.local y completa los valores."
  );
}

// Cliente browser con la anon key: queda embebida en el bundle público, así
// que el acceso real lo controlan las políticas RLS (ver
// supabase/auth_admin_rls.sql), no el secreto de esta key.
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    // La sesión debe sobrevivir al redirect de Google y a recargar la página.
    persistSession: true,
    autoRefreshToken: true,
    // Al volver de Google, los tokens llegan en el hash de la URL: el cliente
    // los canjea y limpia la barra de direcciones.
    detectSessionInUrl: true,
  },
});
