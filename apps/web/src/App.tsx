import { useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import Encabezado from "@/components/Encabezado";
import Login from "@/components/Login";
import ProductosTable from "@/components/ProductosTable";
import { supabase } from "@/lib/supabaseClient";
import { cerrarSesion, obtenerPerfil, puedeEntrar, type Perfil } from "@/lib/auth";

type Estado =
  | { fase: "cargando" }
  | { fase: "sinSesion"; aviso: string | null }
  | { fase: "dentro"; perfil: Perfil; correo: string };

export default function App() {
  const [estado, setEstado] = useState<Estado>({ fase: "cargando" });

  useEffect(() => {
    let cancelado = false;

    async function revisar(session: Session | null) {
      if (!session) {
        if (!cancelado) setEstado({ fase: "sinSesion", aviso: null });
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
    <div className="flex min-h-screen flex-col">
      <Encabezado correo={estado.correo} alSalir={cerrarSesion} />
      <main className="flex-1">
        <ProductosTable />
      </main>
      <footer className="border-t border-marca-borde bg-white">
        <div className="mx-auto w-full max-w-7xl px-6 py-5">
          <p className="versalita">Grupo Mayoreo · Panel interno</p>
        </div>
      </footer>
    </div>
  );
}
