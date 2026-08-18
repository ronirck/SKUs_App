-- ============================================================
-- CONFIG SQL - SKUs App
-- Ejecutar DESPUÉS de base_schema.sql en Supabase SQL Editor
-- ============================================================

-- ─── perfil_usuario ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS perfil_usuario (
    usuario_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    email TEXT,
    rol TEXT NOT NULL DEFAULT 'user' CHECK (rol IN ('user', 'admin')),
    creado_en TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE perfil_usuario ENABLE ROW LEVEL SECURITY;

CREATE POLICY "perfil_select"
ON perfil_usuario FOR SELECT
USING (
    auth.uid() = usuario_id
    OR EXISTS (
        SELECT 1 FROM perfil_usuario p2
        WHERE p2.usuario_id = auth.uid() AND p2.rol = 'admin'
    )
);

CREATE POLICY "perfil_insert"
ON perfil_usuario FOR INSERT
WITH CHECK (auth.uid() = usuario_id);

CREATE POLICY "perfil_update"
ON perfil_usuario FOR UPDATE
USING (
    auth.uid() = usuario_id
    OR EXISTS (
        SELECT 1 FROM perfil_usuario p2
        WHERE p2.usuario_id = auth.uid() AND p2.rol = 'admin'
    )
)
WITH CHECK (
    auth.uid() = usuario_id
    OR EXISTS (
        SELECT 1 FROM perfil_usuario p2
        WHERE p2.usuario_id = auth.uid() AND p2.rol = 'admin'
    )
);

-- ─── usuario_config ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS usuario_config (
    usuario_id UUID PRIMARY KEY REFERENCES perfil_usuario(usuario_id) ON DELETE CASCADE,
    sede TEXT NOT NULL DEFAULT 'FEBECA'
        CHECK (sede IN ('FEBECA', 'SILLACA', 'BEVAL', 'COFERSA', 'MUNDIAL DE PARTES')),
    marcas_permitidas TEXT[] DEFAULT '{}',
    solo_infaltables BOOLEAN DEFAULT FALSE,
    config_version INTEGER DEFAULT 1
);

ALTER TABLE usuario_config ENABLE ROW LEVEL SECURITY;

CREATE POLICY "config_select"
ON usuario_config FOR SELECT
USING (
    auth.uid() = usuario_id
    OR EXISTS (
        SELECT 1 FROM perfil_usuario p
        WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'
    )
);

CREATE POLICY "config_insert"
ON usuario_config FOR INSERT
WITH CHECK (auth.uid() = usuario_id);

CREATE POLICY "config_update"
ON usuario_config FOR UPDATE
USING (
    auth.uid() = usuario_id
    OR EXISTS (
        SELECT 1 FROM perfil_usuario p
        WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'
    )
)
WITH CHECK (
    auth.uid() = usuario_id
    OR EXISTS (
        SELECT 1 FROM perfil_usuario p
        WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'
    )
);

-- ─── marcas ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS marcas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nombre TEXT NOT NULL,
    sede TEXT NOT NULL CHECK (sede IN ('FEBECA', 'SILLACA', 'BEVAL', 'COFERSA', 'MUNDIAL DE PARTES')),
    UNIQUE (nombre, sede)
);

ALTER TABLE marcas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "marcas_select"
ON marcas FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE POLICY "marcas_admin"
ON marcas FOR ALL
USING (EXISTS (SELECT 1 FROM perfil_usuario p WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'))
WITH CHECK (EXISTS (SELECT 1 FROM perfil_usuario p WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'));

-- ─── categorias ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS categorias (
    codigo CHAR(2) NOT NULL,
    nombre TEXT NOT NULL,
    mnemotecnia TEXT,
    sede TEXT NOT NULL CHECK (sede IN ('FEBECA', 'SILLACA', 'BEVAL', 'COFERSA', 'MUNDIAL DE PARTES')),
    PRIMARY KEY (codigo, sede)
);

ALTER TABLE categorias ENABLE ROW LEVEL SECURITY;

CREATE POLICY "categorias_select"
ON categorias FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE POLICY "categorias_admin"
ON categorias FOR ALL
USING (EXISTS (SELECT 1 FROM perfil_usuario p WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'))
WITH CHECK (EXISTS (SELECT 1 FROM perfil_usuario p WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'));

-- ─── subcategorias ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS subcategorias (
    categoria_codigo CHAR(2) NOT NULL,
    codigo CHAR(2) NOT NULL,
    nombre TEXT NOT NULL,
    mnemotecnia TEXT,
    sede TEXT NOT NULL CHECK (sede IN ('FEBECA', 'SILLACA', 'BEVAL', 'COFERSA', 'MUNDIAL DE PARTES')),
    PRIMARY KEY (categoria_codigo, codigo, sede),
    FOREIGN KEY (categoria_codigo, sede) REFERENCES categorias(codigo, sede) ON DELETE CASCADE
);

ALTER TABLE subcategorias ENABLE ROW LEVEL SECURITY;

CREATE POLICY "subcategorias_select"
ON subcategorias FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE POLICY "subcategorias_admin"
ON subcategorias FOR ALL
USING (EXISTS (SELECT 1 FROM perfil_usuario p WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'))
WITH CHECK (EXISTS (SELECT 1 FROM perfil_usuario p WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'));

-- ─── productos ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS productos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    categoria_codigo CHAR(2) NOT NULL,
    subcategoria_codigo CHAR(2) NOT NULL,
    codigo CHAR(3) NOT NULL,
    nombre TEXT NOT NULL,
    mnemotecnia TEXT,
    imagen_url TEXT,
    estatus TEXT NOT NULL DEFAULT 'F'
        CHECK (estatus IN ('B','D','E','F','H','J','K','L','M','N','P','S','T','Z','EXTRA','U','SERV')),
    sede TEXT NOT NULL CHECK (sede IN ('FEBECA', 'SILLACA', 'BEVAL', 'COFERSA', 'MUNDIAL DE PARTES')),
    codigo_completo TEXT,
    marca TEXT,
    ref_proveedor TEXT,
    FOREIGN KEY (categoria_codigo, sede) REFERENCES categorias(codigo, sede) ON DELETE CASCADE,
    FOREIGN KEY (categoria_codigo, subcategoria_codigo, sede)
        REFERENCES subcategorias(categoria_codigo, codigo, sede) ON DELETE CASCADE
);

ALTER TABLE productos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "productos_select"
ON productos FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE POLICY "productos_admin"
ON productos FOR ALL
USING (EXISTS (SELECT 1 FROM perfil_usuario p WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'))
WITH CHECK (EXISTS (SELECT 1 FROM perfil_usuario p WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'));

-- ─── resultados_codex ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS resultados_codex (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES perfil_usuario(usuario_id) ON DELETE CASCADE,
    tipo_juego TEXT NOT NULL
        CHECK (tipo_juego IN ('categorias', 'subcategorias', 'productos', 'contrarreloj')),
    aciertos INTEGER DEFAULT 0,
    fallos INTEGER DEFAULT 0,
    total_preguntas INTEGER DEFAULT 0,
    duracion_segundos INTEGER DEFAULT 0,
    sede TEXT NOT NULL,
    configuracion JSONB DEFAULT '{}',
    detalle_interacciones JSONB DEFAULT '[]',
    creado_en TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE resultados_codex ENABLE ROW LEVEL SECURITY;

CREATE POLICY "resultados_select"
ON resultados_codex FOR SELECT USING (auth.uid() = usuario_id);

CREATE POLICY "resultados_insert"
ON resultados_codex FOR INSERT WITH CHECK (auth.uid() = usuario_id);

-- ─── errores_partida ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS errores_partida (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    resultado_id UUID NOT NULL REFERENCES resultados_codex(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES perfil_usuario(usuario_id) ON DELETE CASCADE,
    tipo_elemento TEXT NOT NULL CHECK (tipo_elemento IN ('categoria', 'subcategoria', 'producto')),
    elemento_codigo TEXT NOT NULL,
    elemento_nombre TEXT NOT NULL,
    mnemotecnia TEXT,
    veces_fallado INTEGER DEFAULT 1,
    creado_en TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE errores_partida ENABLE ROW LEVEL SECURITY;

CREATE POLICY "errores_select"
ON errores_partida FOR SELECT USING (auth.uid() = usuario_id);

CREATE POLICY "errores_insert"
ON errores_partida FOR INSERT WITH CHECK (auth.uid() = usuario_id);

-- ─── reportes_error ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS reportes_error (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES perfil_usuario(usuario_id) ON DELETE CASCADE,
    mensaje TEXT NOT NULL,
    estatus TEXT NOT NULL DEFAULT 'sin_revisar'
        CHECK (estatus IN ('sin_revisar', 'en_revision', 'pendiente', 'resuelto')),
    creado_en TIMESTAMPTZ DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE reportes_error ENABLE ROW LEVEL SECURITY;

CREATE POLICY "reportes_select"
ON reportes_error FOR SELECT
USING (
    auth.uid() = usuario_id
    OR EXISTS (SELECT 1 FROM perfil_usuario p WHERE p.usuario_id = auth.uid() AND p.rol = 'admin')
);

CREATE POLICY "reportes_insert"
ON reportes_error FOR INSERT WITH CHECK (auth.uid() = usuario_id);

CREATE POLICY "reportes_update_admin"
ON reportes_error FOR UPDATE
USING (EXISTS (SELECT 1 FROM perfil_usuario p WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'))
WITH CHECK (EXISTS (SELECT 1 FROM perfil_usuario p WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'));

-- ─── notificaciones_admin ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS notificaciones_admin (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tipo TEXT NOT NULL CHECK (tipo IN ('nuevo_registro')),
    payload JSONB DEFAULT '{}',
    leido BOOLEAN DEFAULT FALSE,
    creado_en TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE notificaciones_admin ENABLE ROW LEVEL SECURITY;

CREATE POLICY "notif_admin_all"
ON notificaciones_admin FOR ALL
USING (EXISTS (SELECT 1 FROM perfil_usuario p WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'))
WITH CHECK (EXISTS (SELECT 1 FROM perfil_usuario p WHERE p.usuario_id = auth.uid() AND p.rol = 'admin'));

CREATE POLICY "notif_user_insert"
ON notificaciones_admin FOR INSERT
WITH CHECK (auth.uid() IS NOT NULL);

-- ─── Trigger: crear perfil al registrarse ─────────────────────────────────────

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.perfil_usuario (usuario_id, nombre, email, rol)
    VALUES (NEW.id, split_part(NEW.email, '@', 1), NEW.email, 'user')
    ON CONFLICT (usuario_id) DO NOTHING;

    INSERT INTO public.usuario_config (usuario_id, sede, marcas_permitidas, solo_infaltables, config_version)
    VALUES (NEW.id, 'FEBECA', '{}', FALSE, 1)
    ON CONFLICT (usuario_id) DO NOTHING;

    INSERT INTO public.notificaciones_admin (tipo, payload)
    VALUES ('nuevo_registro', jsonb_build_object(
        'nombre', split_part(NEW.email, '@', 1),
        'email', NEW.email
    ));

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ─── Tablas creadas ────────────────────────────────────────────────────────────
-- perfil_usuario
-- usuario_config
-- marcas
-- categorias
-- subcategorias
-- productos
-- resultados_codex
-- errores_partida
-- reportes_error
-- notificaciones_admin
