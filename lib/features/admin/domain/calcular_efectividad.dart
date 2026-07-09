/// % de aciertos sobre el total de preguntas respondidas. `0` si el usuario
/// no ha jugado nada todavía — nunca divide por cero.
double calcularEfectividad({required int aciertos, required int totalPreguntas}) {
  if (totalPreguntas <= 0) return 0;
  return (aciertos / totalPreguntas) * 100;
}
