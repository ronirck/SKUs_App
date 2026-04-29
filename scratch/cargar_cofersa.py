import sys
import os
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database

def generar_mnemotecnia(nombre, codigo):
    # Generar una frase sencilla basada en el nombre y los últimos 3 dígitos del código
    ultimos = str(codigo)[-3:]
    # Limpiar nombre de marcas repetitivas o ruidos
    clean_name = nombre.replace("Eagle", "").replace("  ", " ").strip()
    return f"{clean_name}. Recordar por terminación {ultimos}."

def inferir_subcategoria(nombre):
    nombre_lower = nombre.lower()
    if "interruptor" in nombre_lower:
        return ("01", "Interruptores")
    if "toma" in nombre_lower or "enchufe" in nombre_lower:
        return ("02", "Tomas y Enchufes")
    if "socket" in nombre_lower:
        return ("03", "Sockets y Plafones")
    if "timbre" in nombre_lower:
        return ("04", "Timbres")
    if "dimmer" in nombre_lower:
        return ("05", "Dimmers")
    if "canaleta" in nombre_lower:
        return ("06", "Canaletas")
    if "tape" in nombre_lower or "cinta" in nombre_lower:
        return ("07", "Cintas y Tapes")
    return ("99", "Otros")

def cargar_datos(file_path):
    client = database.get_client()
    sede = "COFERSA"
    
    # Asegurar Categoría Base
    cat_id = "04"
    cat_nombre = "Materiales Eléctricos"
    print(f"Intentando crear categoría {cat_id}...")
    try:
        client.table("categorias").insert({
            "sede": sede,
            "codigo": cat_id,
            "nombre": cat_nombre,
            "mnemotecnia": "El 0 es un rollo de cable y el 4 es el soporte."
        }).execute()
        print("Categoría creada.")
    except Exception as e:
        print(f"Aviso Categoría: {e} (Tal vez ya existe o RLS)")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Separar por bloques de guiones
    bloques = content.split("-------------------------------")
    
    productos_a_insertar = []
    subcategorias_vistas = set()

    for bloque in bloques:
        lineas = [l.strip() for l in bloque.strip().split("\n") if l.strip()]
        if not lineas:
            continue
            
        # Linea 1: Código - Descripción - Referencia
        match = re.match(r"(\d+)\s*-\s*(.+?)\s*-\s*(.+)", lineas[0])
        if not match:
            continue
            
        codigo_num = match.group(1)
        descripcion = match.group(2)
        referencia = match.group(3)
        
        sub_id, sub_nombre = inferir_subcategoria(descripcion)
        
        # Insert Subcategoría
        if sub_id not in subcategorias_vistas:
            print(f"Intentando crear subcategoría {sub_id}...")
            try:
                client.table("subcategorias").insert({
                    "sede": sede,
                    "categoria_codigo": cat_id,
                    "codigo": sub_id,
                    "nombre": sub_nombre
                }).execute()
            except Exception as e:
                print(f"Aviso Subcategoría {sub_id}: {e}")
            subcategorias_vistas.add(sub_id)
            
        mnemotecnia = generar_mnemotecnia(descripcion, codigo_num)
        short_code = codigo_num[-3:]
        
        producto = {
            "sede": sede,
            "categoria_codigo": cat_id,
            "subcategoria_codigo": sub_id,
            "codigo": short_code,
            "nombre": descripcion,
            "ref_proveedor": referencia,
            "marca": "Eagle",
            "mnemotecnia": mnemotecnia,
            "codigo_completo": f"{cat_id}-{sub_id}-{short_code}"
        }
        productos_a_insertar.append(producto)
    
    if productos_a_insertar:
        print(f"Insertando {len(productos_a_insertar)} productos...")
        client.table("productos").insert(productos_a_insertar).execute()
        print("Carga completada.")
    else:
        print("No se encontraron productos válidos para cargar.")

if __name__ == "__main__":
    try:
        cargar_datos("datospruebaeagle.txt")
    except Exception as e:
        print(f"Error durante la carga: {e}")
