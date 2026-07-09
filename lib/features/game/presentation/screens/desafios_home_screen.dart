import 'package:flutter/material.dart';

import '../../../catalog/data/catalog_repository.dart';
import '../../data/game_catalog_source.dart';
import '../../data/pending_game_results_syncer.dart';
import '../../data/supabase_game_result_recorder.dart';
import '../../domain/game_result_recorder.dart';
import '../../domain/mode_availability.dart';
import '../../domain/quiz_type_source.dart';
import 'game_play_screen.dart';

class _DesafiosData {
  _DesafiosData({
    required this.categorias,
    required this.subcategorias,
    required this.productos,
    required this.sede,
  });

  final QuizTypeSource categorias;
  final QuizTypeSource subcategorias;
  final QuizTypeSource productos;
  final String sede;
}

class DesafiosHomeScreen extends StatefulWidget {
  const DesafiosHomeScreen({
    super.key,
    required this.catalogRepository,
    required this.userId,
    this.pendingGameResultsSyncer,
    this.recorderOverride,
  });

  final CatalogRepository catalogRepository;
  final String userId;

  /// Requerido en uso normal (construye el recorder real); innecesario
  /// cuando se da [recorderOverride], como en la demo de onboarding.
  final PendingGameResultsSyncer? pendingGameResultsSyncer;

  /// Para la demo de onboarding: evita que las partidas de prueba intenten
  /// escribir en Supabase. `null` (uso normal) construye el recorder real.
  final GameResultRecorder? recorderOverride;

  @override
  State<DesafiosHomeScreen> createState() => _DesafiosHomeScreenState();
}

class _DesafiosHomeScreenState extends State<DesafiosHomeScreen> {
  late final Future<_DesafiosData> _future = _load();
  int _dificultad = 4;

  Future<_DesafiosData> _load() async {
    final source = GameCatalogSource(widget.catalogRepository);
    final categorias = await source.categoriaSource();
    final subcategorias = await source.subcategoriaSource();
    final productos = await source.productoSource();
    final sede = await widget.catalogRepository.cachedSede() ?? '';
    return _DesafiosData(
      categorias: categorias,
      subcategorias: subcategorias,
      productos: productos,
      sede: sede,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Desafíos')),
      body: FutureBuilder<_DesafiosData>(
        future: _future,
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final data = snapshot.data!;
          final contrarrelojSources = [data.categorias, data.subcategorias, data.productos]
              .where((s) => isModePlayable(s.items.length))
              .toList();

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const Text('Dificultad (opciones por pregunta)',
                  style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              SegmentedButton<int>(
                segments: const [
                  ButtonSegment(value: 2, label: Text('2')),
                  ButtonSegment(value: 4, label: Text('4')),
                  ButtonSegment(value: 6, label: Text('6')),
                  ButtonSegment(value: 8, label: Text('8')),
                ],
                selected: {_dificultad},
                onSelectionChanged: (s) => setState(() => _dificultad = s.first),
              ),
              const SizedBox(height: 24),
              _modeCard(
                titulo: 'Categorías',
                icon: Icons.category,
                tipoJuego: 'categorias',
                sources: isModePlayable(data.categorias.items.length) ? [data.categorias] : [],
                sede: data.sede,
              ),
              _modeCard(
                titulo: 'Subcategorías',
                icon: Icons.account_tree,
                tipoJuego: 'subcategorias',
                sources:
                    isModePlayable(data.subcategorias.items.length) ? [data.subcategorias] : [],
                sede: data.sede,
              ),
              _modeCard(
                titulo: 'Productos',
                icon: Icons.inventory_2,
                tipoJuego: 'productos',
                sources: isModePlayable(data.productos.items.length) ? [data.productos] : [],
                sede: data.sede,
              ),
              _modeCard(
                titulo: 'Contrarreloj (90s)',
                icon: Icons.timer,
                tipoJuego: 'contrarreloj',
                sources: contrarrelojSources,
                sede: data.sede,
                timeLimit: const Duration(seconds: 90),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _modeCard({
    required String titulo,
    required IconData icon,
    required String tipoJuego,
    required List<QuizTypeSource> sources,
    required String sede,
    Duration? timeLimit,
  }) {
    final playable = sources.isNotEmpty;
    return Card(
      child: ListTile(
        leading: Icon(icon),
        title: Text(titulo),
        subtitle: playable
            ? null
            : const Text('No hay suficientes elementos en tu catálogo para jugar este modo.'),
        trailing: FilledButton(
          onPressed: playable ? () => _startGame(tipoJuego, sources, sede, timeLimit) : null,
          child: const Text('Jugar'),
        ),
      ),
    );
  }

  void _startGame(String tipoJuego, List<QuizTypeSource> sources, String sede, Duration? timeLimit) {
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => GamePlayScreen(
        tipoJuego: tipoJuego,
        sources: sources,
        dificultad: _dificultad,
        sede: sede,
        recorder: widget.recorderOverride ??
            SupabaseGameResultRecorder(widget.pendingGameResultsSyncer!, widget.userId),
        timeLimit: timeLimit,
      ),
    ));
  }
}
