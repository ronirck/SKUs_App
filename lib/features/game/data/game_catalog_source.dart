import '../../catalog/data/catalog_repository.dart';
import '../domain/quiz_item.dart';
import '../domain/quiz_type_source.dart';

/// Traduce la caché local del catálogo (Fase 2) a [QuizTypeSource] para el
/// motor de juego — formatea el código de cada tipo (categoría "xx",
/// subcategoría "xx-xx", producto "xx-xx-xxx") y arma el [QuizItem.groupKey]
/// que prioriza distractores del mismo padre.
class GameCatalogSource {
  GameCatalogSource(this._catalogRepository);

  final CatalogRepository _catalogRepository;

  Future<QuizTypeSource> categoriaSource() async {
    final rows = await _catalogRepository.categoriasJugables();
    return QuizTypeSource(
      tipoElemento: 'categoria',
      items: rows
          .map((c) => QuizItem(code: c.codigo, name: c.nombre, mnemotecnia: c.mnemotecnia))
          .toList(),
    );
  }

  Future<QuizTypeSource> subcategoriaSource() async {
    final rows = await _catalogRepository.subcategoriasJugables();
    return QuizTypeSource(
      tipoElemento: 'subcategoria',
      items: rows
          .map((s) => QuizItem(
                code: '${s.categoriaCodigo}-${s.codigo}',
                name: s.nombre,
                mnemotecnia: s.mnemotecnia,
                groupKey: s.categoriaCodigo,
              ))
          .toList(),
    );
  }

  Future<QuizTypeSource> productoSource() async {
    final rows = await _catalogRepository.productosJugables();
    return QuizTypeSource(
      tipoElemento: 'producto',
      items: rows
          .map((p) => QuizItem(
                code: p.codigoCompleto ?? p.codigo,
                name: p.nombre,
                mnemotecnia: p.mnemotecnia,
                groupKey: '${p.categoriaCodigo}-${p.subcategoriaCodigo}',
              ))
          .toList(),
    );
  }

  Future<List<QuizTypeSource>> allSources() async {
    return [await categoriaSource(), await subcategoriaSource(), await productoSource()];
  }
}
