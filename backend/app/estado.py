from datetime import datetime, timezone

from app.models import Partido


def calcular_estado(partido: Partido) -> str:
    if partido.goles_local is not None and partido.goles_visitante is not None:
        return "FINALIZADO"
    if datetime.now(timezone.utc) >= partido.inicio:
        return "EN_JUEGO"
    return "PROGRAMADO"
