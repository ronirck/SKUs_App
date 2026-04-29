import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database

client = database.get_client()
sede = "COFERSA"

print("--- TEST CATEGORIAS ---")
try:
    res = client.table("categorias").insert({"sede": sede, "codigo": "99", "nombre": "TEST"}).execute()
    print("Insert Categorias OK:", res.data)
except Exception as e:
    print("Insert Categorias FAIL:", e)

print("\n--- TEST PRODUCTOS ---")
try:
    # Probar con codigo de 3 chars
    res = client.table("productos").insert({
        "sede": sede, 
        "categoria_codigo": "99", 
        "subcategoria_codigo": "99", 
        "codigo": "999", 
        "nombre": "TEST PROD",
        "codigo_completo": "99-99-999"
    }).execute()
    print("Insert Productos OK:", res.data)
except Exception as e:
    print("Insert Productos FAIL:", e)
