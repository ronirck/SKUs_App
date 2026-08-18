-- ============================================================
-- BASE SCHEMA - Flet App Builder
-- Ejecutar este archivo en Supabase SQL Editor
-- antes de ejecutar config.sql
-- ============================================================


-- ─── Tabla profiles ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuario solo ve su propio perfil"
ON profiles FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Usuario solo edita su propio perfil"
ON profiles FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Usuario puede insertar su propio perfil"
ON profiles FOR INSERT
WITH CHECK (auth.uid() = user_id);


-- ─── Tabla session_logs ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS session_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, date)
);

ALTER TABLE session_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuario solo ve sus propios registros"
ON session_logs FOR ALL
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);


-- ─── Columna role (descomentar si la app tiene roles) ────────────────────────

-- ALTER TABLE profiles
-- ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'usuario'
-- CHECK (role IN ('usuario', 'admin'));

-- DROP POLICY IF EXISTS "Usuario solo ve su propio perfil" ON profiles;

-- CREATE POLICY "Admin puede ver todos los perfiles"
-- ON profiles FOR SELECT
-- USING (
--     auth.uid() = user_id
--     OR EXISTS (
--         SELECT 1 FROM profiles
--         WHERE user_id = auth.uid()
--         AND role = 'admin'
--     )
-- );

-- CREATE POLICY "Admin puede editar roles"
-- ON profiles FOR UPDATE
-- USING (
--     EXISTS (
--         SELECT 1 FROM profiles
--         WHERE user_id = auth.uid()
--         AND role = 'admin'
--     )
-- )
-- WITH CHECK (
--     EXISTS (
--         SELECT 1 FROM profiles
--         WHERE user_id = auth.uid()
--         AND role = 'admin'
--     )
-- );