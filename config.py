# config.py — Credenciales de la aplicación
# Valores inyectados por setup.py al inicializar el proyecto.
# En desarrollo los valores vienen del .env via setup.py.
# En producción (APK) están hardcodeados aquí directamente,
# ya que el .env no se empaqueta en el APK.

# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL = ""
SUPABASE_ANON_KEY = ""

# ── GitHub ────────────────────────────────────────────────────────────────────
GITHUB_REPO = ""
GITHUB_TOKEN = ""
