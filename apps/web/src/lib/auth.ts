import { supabase } from "@/lib/supabaseClient";

/**
 * Perfil del usuario tal como lo guarda la app móvil en `perfil_usuario`.
 * Ambas apps comparten la misma tabla: quien administra allá administra aquí.
 */
export type Perfil = {
  usuarioId: string;
  nombre: string | null;
  apellido: string | null;
  rol: string;
  estado: string;
};

/** Solo entra al panel un administrador aprobado. */
export function puedeEntrar(perfil: Perfil | null): boolean {
  return perfil?.rol === "admin" && perfil.estado === "aprobado";
}

/**
 * Manda al usuario a Google. El correo escrito viaja como `login_hint`, que
 * es solo una comodidad: Google preselecciona esa cuenta.
 *
 * Ojo, no es el control de acceso — quien inicia sesión puede elegir otra
 * cuenta en la pantalla de Google. Quien decide es `perfil_usuario`, que se
 * consulta con la identidad que Google devuelve, no con este texto.
 */
export async function entrarConGoogle(correo: string): Promise<void> {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: {
      redirectTo: window.location.origin,
      queryParams: {
        login_hint: correo.trim(),
        prompt: "select_account",
      },
    },
  });
  if (error) throw error;
}

/**
 * Pregunta a la base si ese correo corresponde a un administrador aprobado,
 * para poder rechazarlo antes de mandarlo a Google.
 *
 * Devuelve `null` cuando no se pudo comprobar (por ejemplo, si todavía no se
 * ejecutó `supabase/auth_precheck_correo.sql`). En ese caso se deja continuar:
 * el control real es la verificación posterior al login, así que fallar aquí
 * no abre nada — solo hace que el rechazo llegue más tarde. Bloquear el paso
 * ante un error dejaría a los admins fuera por un problema de configuración.
 */
export async function correoPuedeEntrar(correo: string): Promise<boolean | null> {
  const { data, error } = await supabase.rpc("correo_puede_entrar", {
    correo: correo.trim(),
  });

  if (error) {
    console.warn(
      "No se pudo comprobar el correo antes de Google; se continúa y se verifica al volver.",
      error.message
    );
    return null;
  }

  return data === true;
}

export async function cerrarSesion(): Promise<void> {
  await supabase.auth.signOut();
}

/** Perfil del usuario de la sesión; `null` si la fila todavía no existe. */
export async function obtenerPerfil(usuarioId: string): Promise<Perfil | null> {
  const { data, error } = await supabase
    .from("perfil_usuario")
    .select("usuario_id, nombre, apellido, rol, estado")
    .eq("usuario_id", usuarioId)
    .maybeSingle();

  if (error) throw error;
  if (!data) return null;

  return {
    usuarioId: data.usuario_id as string,
    nombre: (data.nombre as string | null) ?? null,
    apellido: (data.apellido as string | null) ?? null,
    rol: (data.rol as string | null) ?? "user",
    estado: (data.estado as string | null) ?? "pendiente",
  };
}
