import re

def generar_mnemotecnia(nombre, codigo):
    ultimos = str(codigo)[-3:]
    clean_name = nombre.replace("Cable THHN", "Cable").replace("Conducen", "").replace("  ", " ").strip()
    return f"{clean_name}. Recordar por terminación {ultimos}."

def procesar_archivo(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    bloques = content.split("-------------------------------")
    sede = "COFERSA"
    cat_id = "04"
    sub_id = "08"
    sub_nombre = "Cables y Conductores"
    
    sql = []
    # Categoria (ya debe existir pero por si acaso)
    sql.append(f"INSERT INTO categorias (sede, codigo, nombre, mnemotecnia) VALUES ('{sede}', '{cat_id}', 'Materiales Eléctricos', 'El 0 es un rollo de cable y el 4 es el soporte.') ON CONFLICT DO NOTHING;")
    
    # Subcategoria
    sql.append(f"INSERT INTO subcategorias (sede, categoria_codigo, codigo, nombre) VALUES ('{sede}', '{cat_id}', '{sub_id}', '{sub_nombre}') ON CONFLICT DO NOTHING;")
    
    productos_sql = []
    for bloque in bloques:
        lineas = [l.strip() for l in bloque.strip().split("\n") if l.strip()]
        if not lineas: continue
        
        # Saltarse el encabezado de marca si es la primera linea del archivo
        if "Phelps Dodge" in lineas[0]: 
            lineas = lineas[1:]
            if not lineas: continue

        match = re.match(r"(\d+)\s*-\s*(.+?)\s*-\s*(.+)", lineas[0])
        if not match: continue
        
        codigo_num = match.group(1)
        descripcion = match.group(2).replace("'", "''") # Escapar comillas
        referencia = match.group(3)
        
        mnemotecnia = generar_mnemotecnia(descripcion, codigo_num)
        short_code = codigo_num[-3:]
        codigo_completo = f"{cat_id}-{sub_id}-{short_code}"
        
        productos_sql.append(f"('{sede}', '{cat_id}', '{sub_id}', '{short_code}', '{descripcion}', '{referencia}', 'Phelps Dodge', '{mnemotecnia}', '{codigo_completo}')")
    
    if productos_sql:
        sql.append("INSERT INTO productos (sede, categoria_codigo, subcategoria_codigo, codigo, nombre, ref_proveedor, marca, mnemotecnia, codigo_completo) VALUES")
        sql.append(",\n".join(productos_sql) + ";")
    
    return "\n".join(sql)

if __name__ == "__main__":
    print(procesar_archivo("datospruebacable.txt"))
