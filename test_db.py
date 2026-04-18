
import os
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno
load_dotenv("c:/Users/arivera/Documents/GitHub/Codex-game/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"URL: {url}")
# key_masked = key[:10] + "..." + key[-10:] if key else "None"
# print(f"KEY: {key_masked}")

if not url or not key:
    print("Error: SUPABASE_URL o SUPABASE_KEY no definidos.")
    exit(1)

supabase = create_client(url, key)

try:
    # 1. Probar conexión básica (count)
    res = supabase.table("productos").select("count", count="exact").limit(0).execute()
    print(f"Total productos en tabla: {res.count}")

    # 2. Probar fetch de una fila
    rows = supabase.table("productos").select("*").limit(1).execute()
    print(f"Fila 1: {rows.data}")
    
    # 3. Probar categorías
    res_cat = supabase.table("categorias").select("count", count="exact").limit(0).execute()
    print(f"Total categorías: {res_cat.count}")

except Exception as e:
    print(f"Error al conectar con Supabase: {e}")
