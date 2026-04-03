"""
config.py
Responsabilidad única: exponer las variables de configuración como
constantes tipadas. En Android no existe .env, se usan valores directos.
"""

# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL: str = "https://kmsonkzumooffvdkeuql.supabase.co"  # ← reemplaza
SUPABASE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imttc29ua3p1bW9vZmZ2ZGtldXFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxOTMxODUsImV4cCI6MjA4OTc2OTE4NX0.wi1h1I4PsCc8hi0dPVyeHgDkvmmzooaNdp5dyxaWTP0"                 # ← reemplaza con anon key

# ── UI / App ──────────────────────────────────────────────────────────────────
APP_TITLE:        str = "SKUs app"
WINDOW_WIDTH:     int = 390
WINDOW_HEIGHT:    int = 844
COLOR_SEED:       str = "grey"

# Paleta de color por sede (seed para ft.Theme)
SEDE_COLORES: dict[str, str] = {
    "Prisma":  "grey",
    "FEBECA":  "blue",
    "SILLACA": "pink",
    "BEVAL":   "green",
}