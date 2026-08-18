class FailedItem {
  FailedItem({
    required this.tipoElemento,
    required this.elementoCodigo,
    required this.elementoNombre,
    this.mnemotecnia,
  });

  final String tipoElemento;
  final String elementoCodigo;
  final String elementoNombre;
  final String? mnemotecnia;

  Map<String, dynamic> toJson() => {
        'tipo_elemento': tipoElemento,
        'elemento_codigo': elementoCodigo,
        'elemento_nombre': elementoNombre,
        'mnemotecnia': mnemotecnia,
      };

  factory FailedItem.fromJson(Map<String, dynamic> json) => FailedItem(
        tipoElemento: json['tipo_elemento'] as String,
        elementoCodigo: json['elemento_codigo'] as String,
        elementoNombre: json['elemento_nombre'] as String,
        mnemotecnia: json['mnemotecnia'] as String?,
      );
}

class PendingGameResultPayload {
  PendingGameResultPayload({
    required this.usuarioId,
    required this.tipoJuego,
    required this.aciertos,
    required this.fallos,
    required this.totalPreguntas,
    required this.duracionSegundos,
    required this.sede,
    required this.configuracion,
    required this.detalleInteracciones,
    required this.errores,
  });

  final String usuarioId;
  final String tipoJuego;
  final int aciertos;
  final int fallos;
  final int totalPreguntas;
  final int duracionSegundos;
  final String sede;
  final Map<String, dynamic> configuracion;
  final List<Map<String, dynamic>> detalleInteracciones;
  final List<FailedItem> errores;
}
