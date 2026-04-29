import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database

def limpiar_sede(sede):
    client = database.get_client()
    print(f"\n>>> Iniciando limpieza para sede: {sede}...")
    
    # 1. Eliminar Productos
    res_p = client.table("productos").delete().eq("sede", sede).execute()
    print(f"Productos eliminados.")

    # 2. Eliminar Subcategorías
    res_s = client.table("subcategorias").delete().eq("sede", sede).execute()
    print(f"Subcategorías eliminadas.")

    # 3. Eliminar Categorías
    res_c = client.table("categorias").delete().eq("sede", sede).execute()
    print(f"Categorías eliminadas.")

    print(f">>> Limpieza completada para {sede}.\n")

if __name__ == "__main__":
    try:
        limpiar_sede("COFERSA")
    except Exception as e:
        print(f"Error durante la limpieza: {e}")
