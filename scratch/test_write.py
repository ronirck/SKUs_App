import sys
import os
sys.path.append(os.getcwd())
import database

def update_config(clave, valor):
    try:
        client = database.get_client()
        res = client.table("app_config").update({"valor": valor}).eq("clave", clave).execute()
        print(f"Update {clave} to {valor}: {res.data}")
    except Exception as e:
        print(f"Error updating {clave}: {e}")

# Esto es solo una prueba para ver si tenemos permisos de escritura
# No cambiaremos nada crítico aún sin la URL del usuario.
update_config("update_message", "Probando permisos de edicion")
