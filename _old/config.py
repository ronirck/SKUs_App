# config.py — Credenciales de la aplicación
# Valores inyectados por setup.py al inicializar el proyecto.
# En desarrollo los valores vienen del .env via setup.py.
# En producción (APK) están hardcodeados aquí directamente,
# ya que el .env no se empaqueta en el APK.

# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL = "https://nomuvetphjpnwvktywrv.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5vbXV2ZXRwaGpwbnd2a3R5d3J2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkwNDk4MDAsImV4cCI6MjA5NDYyNTgwMH0.ET6_cHAtofUTUqs-EACst_h3aDombYJ5flVhd7Ke9xw"

# ── GitHub ────────────────────────────────────────────────────────────────────
GITHUB_REPO = "ronirck/SKUs_App"
GITHUB_TOKEN = "REVOCADO"  # token retirado del árbol al archivar la app Flet; sigue en el historial de git — revocar en GitHub
