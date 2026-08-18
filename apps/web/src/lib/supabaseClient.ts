import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    "Faltan VITE_SUPABASE_URL o VITE_SUPABASE_ANON_KEY. Copia .env.local.example a .env.local y completa los valores."
  );
}

// Cliente browser con la anon key: queda embebida en el bundle público, así
// que el acceso real lo controlan las políticas RLS del rol anon (ver
// supabase/anon_rls.sql), no el secreto de esta key.
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: { persistSession: false },
});
