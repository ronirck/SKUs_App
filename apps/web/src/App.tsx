import { useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import Encabezado from "@/components/Encabezado";
import Login from "@/components/Login";
import CatalogoProvider from "@/components/CatalogoProvider";
import Panel from "@/components/Panel";
import { supabase } from "@/lib/supabaseClient";
import { cerrarSesion, obtenerPerfil, puedeEntrar, type Perfil } from "@/lib/auth";

type Estado =
  | { fase: "cargando" }
  | { fase: "sinSesion"; aviso: string | null }
  | { fase: "dentro"; perfil: Perfil; correo: string };

/**
 * Google devuelve los errores en el hash o en la query de la URL. Sin leerlos,
 * un retorno fallido se ve como "no pasó nada": el usuario vuelve a la
 * pantalla de acceso sin explicación.
 */
function errorDeRetorno(): string | null {
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const query = new URLSearchParams(window.location.search);
  const descripcion =
    hash.get("error_description") ?? query.get("error_description");
  const codigo = hash.get("error") ?? query.get("error");
  if (!descripcion && !codigo) return null;

  // Limpia la URL para que el mensaje no reaparezca al recargar.
  window.history.replaceState({}, "", window.location.pathname);
  return descripcion ?? codigo;
}

export default function App() {
  const [estado, setEstado] = useState<Estado>({ fase: "cargando" });

  useEffect(() => {
    let cancelado = false;

    const avisoDeRetorno = errorDeRetorno();

    async function revisar(session: Session | null) {
      if (!session) {
        if (!cancelado) setEstado({ fase: "sinSesion", aviso: avisoDeRetorno });
        return;
      }

      try {
        const perfil = await obtenerPerfil(session.user.id);
        if (cancelado) return;

        if (puedeEntrar(perfil)) {
          setEstado({
            fase: "dentro",
            perfil: perfil!,
            correo: session.user.email ?? "",
          });
          return;
        }

        // Autenticado pero sin permiso: se cierra la sesión para no dejar a
        // medias a alguien que no puede hacer nada aquí, y se dice por qué.
        const correo = session.user.email ?? "esta cuenta";
        await cerrarSesion();
        if (cancelado) return;
        setEstado({
          fase: "sinSesion",
          aviso:
            perfil === null
              ? `${correo} no tiene un perfil en la aplicación. Regístrate primero desde la app móvil.`
              : `${correo} no es administrador aprobado, así que no puede entrar al panel.`,
        });
      } catch (err) {
        if (cancelado) return;
        setEstado({
          fase: "sinSesion",
          aviso: `No se pudo verificar el permiso: ${(err as Error).message}. Intenta de nuevo.`,
        });
      }
    }

    supabase.auth.getSession().then(({ data }) => revisar(data.session));

    const { data: sub } = supabase.auth.onAuthStateChange((_evento, session) => {
      revisar(session);
    });

    return () => {
      cancelado = true;
      sub.subscription.unsubscribe();
    };
  }, []);

  if (estado.fase === "cargando") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-marca-fondo">
        <p className="text-sm text-marca-texto">Verificando tu acceso…</p>
      </div>
    );
  }

  if (estado.fase === "sinSesion") {
    return <Login aviso={estado.aviso} />;
  }

  return (
    // El proveedor envuelve al panel para que la descarga del catálogo empiece
    // al entrar, sin esperar a que se abra la pestaña que muestra la tabla.
    <CatalogoProvider>
    <div className="flex min-h-screen flex-col">
      <Encabezado correo={estado.correo} alSalir={cerrarSesion} />
      <main className="flex-1">
        <Panel />
      </main>
      <footer className="border-t border-marca-borde bg-white">
        <div className="mx-auto w-full max-w-7xl px-6 py-5">
          <p className="versalita">Grupo Mayoreo · Panel interno</p>
        </div>
      </footer>
    </div>
    </CatalogoProvider>
  );
}
