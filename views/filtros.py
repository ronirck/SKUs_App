INFALTABLES = {"B", "D", "F"}


def get_elementos_visibles(
    categorias: list,
    subcategorias: list,
    productos: list,
    marca_filtro: str = None,
    solo_infaltables: bool = False,
    busqueda_cat: str = "",
    busqueda_sub: str = "",
):
    # 1. Filtrar productos por infaltables y marca
    prods = productos
    if solo_infaltables:
        prods = [p for p in prods if p.get("estatus") in INFALTABLES]
    if marca_filtro and marca_filtro != "Todas las marcas":
        prods = [p for p in prods if p.get("marca") == marca_filtro]

    # 2. Claves de cats y subs con al menos un producto visible
    cats_con_prods = set(
        (p.get("categoria_codigo"), p.get("sede")) for p in prods
        if p.get("categoria_codigo") and p.get("sede")
    )
    subs_con_prods = set(
        (p.get("categoria_codigo"), p.get("subcategoria_codigo"), p.get("sede"))
        for p in prods
        if p.get("categoria_codigo") and p.get("subcategoria_codigo") and p.get("sede")
    )

    # 3. Cats con al menos un producto
    cats_visibles = [
        c for c in categorias
        if (c.get("codigo"), c.get("sede")) in cats_con_prods
    ]

    # 4. Búsqueda de categoría — recalcula subs elegibles
    if busqueda_cat.strip():
        cats_visibles = [
            c for c in cats_visibles
            if busqueda_cat.lower() in (c.get("nombre") or "").lower()
        ]
        codigos_cats = set((c.get("codigo"), c.get("sede")) for c in cats_visibles)
        subs_con_prods = {s for s in subs_con_prods if (s[0], s[2]) in codigos_cats}

    # 5. Subs con al menos un producto visible (y en una cat visible)
    subs_visibles = [
        s for s in subcategorias
        if (s.get("categoria_codigo"), s.get("codigo"), s.get("sede")) in subs_con_prods
    ]

    # 6. Búsqueda de subcategoría — recalcula cats que tengan esas subs
    if busqueda_sub.strip():
        subs_visibles = [
            s for s in subs_visibles
            if busqueda_sub.lower() in (s.get("nombre") or "").lower()
        ]
        cats_de_subs = set((s.get("categoria_codigo"), s.get("sede")) for s in subs_visibles)
        cats_visibles = [
            c for c in cats_visibles
            if (c.get("codigo"), c.get("sede")) in cats_de_subs
        ]

    return cats_visibles, subs_visibles, prods
