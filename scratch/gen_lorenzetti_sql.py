import re

def generar_mnemotecnia(nombre, codigo):
    ultimos = str(codigo)[-3:]
    clean_name = nombre.replace("Lorenzetti", "").replace("  ", " ").strip()
    return f"{clean_name}. Recordar por terminación {ultimos}."

def inferir_subcategoria(nombre):
    nombre_lower = nombre.lower()
    if "ducha" in nombre_lower and "resistencia" not in nombre_lower and "niple" not in nombre_lower and "cernidor" not in nombre_lower:
        return ("01", "Duchas")
    if "resistencia" in nombre_lower:
        return ("02", "Resistencias")
    return ("03", "Accesorios y Repuestos")

def procesar_archivo(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    bloques = content.split("-------------------------------")
    sede = "COFERSA"
    cat_id = "20"
    
    sql = []
    # Categoria
    sql.append(f"INSERT INTO categorias (sede, codigo, nombre, mnemotecnia) VALUES ('{sede}', '{cat_id}', 'Baños', 'El 2 es un grifo y el 0 es el lavabo.') ON CONFLICT DO NOTHING;")
    
    # Subcategorias
    sub_dict = {}
    
    productos_sql = []
    for bloque in bloques:
        lineas = [l.strip() for l in bloque.strip().split("\n") if l.strip()]
        if not lineas: continue
        
        match = re.match(r"(\d+)\s*-\s*(.+?)\s*-\s*(.+)", lineas[0])
        if not match: continue
        
        codigo_num = match.group(1)
        descripcion = match.group(2)
        referencia = match.group(3)
        
        sub_id, sub_nombre = inferir_subcategoria(descripcion)
        sub_dict[sub_id] = sub_nombre
        
        mnemotecnia = generar_mnemotecnia(descripcion, codigo_num)
        short_code = codigo_num[-3:]
        codigo_completo = f"{cat_id}-{sub_id}-{short_code}"
        
        productos_sql.append(f"('{sede}', '{cat_id}', '{sub_id}', '{short_code}', '{descripcion}', '{referencia}', 'Lorenzetti', '{mnemotecnia}', '{codigo_completo}')")
    
    for sid, snombre in sub_dict.items():
        sql.append(f"INSERT INTO subcategorias (sede, categoria_codigo, codigo, nombre) VALUES ('{sede}', '{cat_id}', '{sid}', '{snombre}') ON CONFLICT DO NOTHING;")
    
    if productos_sql:
        sql.append("INSERT INTO productos (sede, categoria_codigo, subcategoria_codigo, codigo, nombre, ref_proveedor, marca, mnemotecnia, codigo_completo) VALUES")
        sql.append(",\n".join(productos_sql) + ";")
    
    return "\n".join(sql)

if __name__ == "__main__":
    print(procesar_archivo("datospruebalorenzetti.txt"))
