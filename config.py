"""
config.py
Responsabilidad única: exponer las variables de configuración como
constantes tipadas. En Android no existe .env, se usan valores directos.
"""

# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL: str = "https://kmsonkzumooffvdkeuql.supabase.co"  # ← reemplaza
SUPABASE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imttc29ua3p1bW9vZmZ2ZGtldXFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxOTMxODUsImV4cCI6MjA4OTc2OTE4NX0.wi1h1I4PsCc8hi0dPVyeHgDkvmmzooaNdp5dyxaWTP0"                 # ← reemplaza con anon key

# ── UI / App ──────────────────────────────────────────────────────────────────
APP_TITLE:        str = "Códigos de Producto"
WINDOW_WIDTH:     int = 390
WINDOW_HEIGHT:    int = 844
COLOR_SEED:       str = "blue"

CASA_COLORS: dict[str, str] = {
    "Prisma":  "blue",
    "FEBECA":  "#0a94d2",
    "SILLACA": "#e40873",
    "BEVAL":   "#d1df32",
    "COFERSA": "#0a94d2",
    "MUNDIAL DE PARTES": "#d1df32",
}