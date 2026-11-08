"""Motor de puntuación (sección 4 de CONTEXT.md).

Módulo puro: no depende de la capa HTTP. Los endpoints de administración
(fase D5) llaman a `recalcular_partido` al registrar, corregir o anular un
resultado; el seed llama a `recalcular_todo` tras crear los datos demo.
"""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Partido, Prediccion, Puntaje

UMBRAL_ANTICIPACION = timedelta(hours=24)


def signo(x: int) -> int:
    return (x > 0) - (x < 0)


def puntos_base(pl: int, pv: int, gl: int, gv: int) -> int:
    """Reglas 1, 2 y 3 (acumulables). Resultado en {0, 3, 5, 10}."""
    base = 0
    if signo(pl - pv) == signo(gl - gv):
        base += 3
    if (pl - pv) == (gl - gv):
        base += 2
    if pl == gl and pv == gv:
        base += 5
    return base


def bonus_anticipacion(inicio: datetime, registrado_en: datetime, base: int) -> int:
    """Regla 5: +1 si la predicción tuvo puntos base y fue registrada
    (o su última edición) con más de 24 h de anticipación al inicio."""
    if base <= 0:
        return 0
    if inicio - registrado_en > UMBRAL_ANTICIPACION:
        return 1
    return 0


def recalcular_usuario(session: Session, usuario_id: int) -> None:
    """Recalcula desde cero el puntaje de un usuario (DEC-7): base,
    anticipación y racha sobre todas sus predicciones con resultado,
    ordenadas por inicio del partido (desempate por id)."""
    filas = session.execute(
        select(Prediccion, Partido)
        .join(Partido, Prediccion.partido_id == Partido.id)
        .where(
            Prediccion.usuario_id == usuario_id,
            Partido.goles_local.is_not(None),
            Partido.goles_visitante.is_not(None),
        )
        .order_by(Partido.inicio, Partido.id)
    ).all()

    total_base = 0
    total_anticipacion = 0
    bonus_racha_total = 0
    aciertos = 0
    exactos = 0
    racha = 0
    mejor_racha = 0

    for prediccion, partido in filas:
        base = puntos_base(
            prediccion.goles_local,
            prediccion.goles_visitante,
            partido.goles_local,
            partido.goles_visitante,
        )
        antic = bonus_anticipacion(partido.inicio, prediccion.registrado_en, base)

        prediccion.puntos_base = base
        prediccion.bonus_anticipacion = antic

        total_base += base
        total_anticipacion += antic

        if base == 10:
            exactos += 1

        if base >= 3:
            aciertos += 1
            racha += 1
            if racha % 3 == 0:
                bonus_racha_total += 2
        else:
            racha = 0

        mejor_racha = max(mejor_racha, racha)

    total = total_base + total_anticipacion + bonus_racha_total

    puntaje = session.get(Puntaje, usuario_id)
    if puntaje is None:
        puntaje = Puntaje(usuario_id=usuario_id)
        session.add(puntaje)

    puntaje.total = total
    puntaje.puntos_base = total_base
    puntaje.bonus_anticipacion = total_anticipacion
    puntaje.bonus_racha = bonus_racha_total
    puntaje.aciertos = aciertos
    puntaje.exactos = exactos
    puntaje.racha_actual = racha
    puntaje.mejor_racha = mejor_racha


def recalcular_partido(session: Session, partido_id: int) -> None:
    """Recalcula a todos los usuarios con una predicción en `partido_id`
    (los demás no cambian: sección 4.5)."""
    usuario_ids = session.scalars(
        select(Prediccion.usuario_id).where(Prediccion.partido_id == partido_id)
    ).all()
    for usuario_id in usuario_ids:
        recalcular_usuario(session, usuario_id)


def recalcular_todo(session: Session) -> None:
    """Recalcula a todos los usuarios de la base (usado por el seed)."""
    from app.models import Usuario

    usuario_ids = session.scalars(select(Usuario.id)).all()
    for usuario_id in usuario_ids:
        recalcular_usuario(session, usuario_id)
