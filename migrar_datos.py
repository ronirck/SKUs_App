import database

def duplicar_sede(origen, destino):
    client = database.get_client()
    print(f"\n>>> Duplicando {origen} -> {destino}...")
    
    # Categorías
    cats = client.table("categorias").select("*").eq("sede", origen).execute().data
    for c in cats:
        c.pop("id", None)
        c["sede"] = destino
    if cats: client.table("categorias").insert(cats).execute()
    print(f"Categorías: {len(cats)}")

    # Subcategorías
    subs = client.table("subcategorias").select("*").eq("sede", origen).execute().data
    for s in subs:
        s.pop("id", None)
        s["sede"] = destino
    if subs: client.table("subcategorias").insert(subs).execute()
    print(f"Subcategorías: {len(subs)}")

    # Productos (en bloques para evitar errores de red)
    offset = 0
    total = 0
    while True:
        prods = client.table("productos").select("*").eq("sede", origen).range(offset, offset + 999).execute().data
        if not prods: break
        for p in prods:
            p.pop("id", None)
            p["sede"] = destino
        client.table("productos").insert(prods).execute()
        total += len(prods)
        offset += 1000
    print(f"Productos: {total}")

if __name__ == "__main__":
    try:
        duplicar_sede("FEBECA", "COFERSA")
        duplicar_sede("BEVAL", "MUNDIAL DE PARTES")
        print("\n¡Bases de datos actualizadas!")
    except Exception as e:
        print(f"Error: {e}")
