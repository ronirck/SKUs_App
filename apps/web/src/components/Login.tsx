import { useState } from "react";
import logoMayoreo from "@/assets/logo-mayoreo.png";
import { correoPuedeEntrar, entrarConGoogle } from "@/lib/auth";

const CORREO_VALIDO = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Pantalla de acceso: correo + Google. El correo solo preselecciona la cuenta
 * en Google; el permiso lo decide `perfil_usuario` (ver `puedeEntrar`).
 */
export default function Login({ aviso }: { aviso?: string | null }) {
  const [correo, setCorreo] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const habilitado = CORREO_VALIDO.test(correo.trim()) && !enviando;

  async function entrar() {
    setEnviando(true);
    setError(null);
    try {
      // Se comprueba el permiso antes de salir a Google: si el correo no es
      // de un administrador, no tiene sentido hacerle dar toda la vuelta para
      // rebotarlo al volver.
      const permitido = await correoPuedeEntrar(correo);
      if (permitido === false) {
        setError(
          `${correo.trim()} no es un administrador aprobado, así que no puede entrar al panel. Pide el acceso desde la aplicación.`
        );
        setEnviando(false);
        return;
      }

      await entrarConGoogle(correo);
    } catch (err) {
      setError(`No se pudo abrir el acceso con Google: ${(err as Error).message}`);
      setEnviando(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-marca-fondo px-6">
      <section className="animar-entrada w-full max-w-md rounded-xl border border-marca-borde bg-white p-8">
        <img
          src={logoMayoreo}
          alt="Grupo Mayoreo"
          className="h-10 w-auto"
          width={40}
          height={40}
        />
        <h1 className="mt-5 text-[1.4rem] font-bold text-marca-negro">
          Catálogo de productos
        </h1>
        <p className="mt-1 text-sm text-marca-texto">
          El panel es solo para administradores. Entra con la cuenta de Google
          con la que usas la aplicación.
        </p>

        {aviso && (
          <p className="mt-5 rounded-[10px] border border-[#fecaca] bg-[#fef2f2] px-4 py-3 text-sm text-[#b91c1c]">
            {aviso}
          </p>
        )}

        <label className="mt-6 flex flex-col gap-1.5">
          <span className="versalita">Correo</span>
          <input
            type="email"
            autoComplete="email"
            className="rounded-[10px] border border-marca-borde bg-white px-3 py-2.5 text-sm text-marca-negro placeholder:text-marca-tenue focus:border-marca-negro focus:outline-none"
            placeholder="tu-correo@mayoreo.biz"
            value={correo}
            onChange={(e) => {
              setCorreo(e.target.value);
              setError(null);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && habilitado) entrar();
            }}
          />
        </label>

        <button
          className="mt-3 flex w-full items-center justify-center gap-2.5 rounded-[10px] bg-marca-negro px-[22px] py-2.5 text-[.9rem] font-semibold text-white hover:bg-black disabled:cursor-not-allowed disabled:opacity-50"
          disabled={!habilitado}
          onClick={entrar}
        >
          <LogoGoogle />
          {enviando ? "Verificando…" : "Conectar con Google"}
        </button>

        {error && (
          <p className="mt-3 text-sm text-[#b91c1c]">{error}</p>
        )}

        <p className="mt-5 text-sm text-marca-tenue">
          Si no tienes acceso, pídeselo a un administrador desde la aplicación.
        </p>
      </section>
    </div>
  );
}

/** Isotipo de Google, en su color oficial: es marca ajena y no se recolorea. */
function LogoGoogle() {
  return (
    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white">
      <svg viewBox="0 0 48 48" className="h-3.5 w-3.5" aria-hidden>
        <path
          fill="#EA4335"
          d="M24 9.5c3.5 0 6.6 1.2 9 3.6l6.7-6.7C35.6 2.6 30.2 0 24 0 14.6 0 6.5 5.4 2.6 13.2l7.8 6.1C12.3 13.2 17.7 9.5 24 9.5z"
        />
        <path
          fill="#4285F4"
          d="M46.1 24.6c0-1.6-.1-3.1-.4-4.6H24v9.1h12.4c-.5 2.9-2.2 5.3-4.7 6.9l7.3 5.7c4.3-3.9 6.8-9.8 6.8-17.1z"
        />
        <path
          fill="#FBBC05"
          d="M10.4 28.7c-.5-1.5-.8-3-.8-4.7s.3-3.2.8-4.7l-7.8-6.1C1 16.3 0 20 0 24s1 7.7 2.6 10.8l7.8-6.1z"
        />
        <path
          fill="#34A853"
          d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.3-5.7c-2 1.4-4.7 2.3-8.6 2.3-6.3 0-11.7-3.7-13.6-9.1l-7.8 6.1C6.5 42.6 14.6 48 24 48z"
        />
      </svg>
    </span>
  );
}
