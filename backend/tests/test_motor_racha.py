"""T1 / sección 17.1: bonus de racha (regla 4, DEC-2)."""

from datetime import datetime, timedelta, timezone

from app.models import Puntaje
from app.scoring import recalcular_usuario

from tests import fabrica

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _predecir_acierto(session, usuario, offset_dias):
    """Predicción que acierta al menos el ganador (base >= 3)."""
    inicio = BASE + timedelta(days=offset_dias)
    partido = fabrica.crear_partido(session, inicio=inicio, resultado=(2, 0))
    fabrica.crear_prediccion(session, usuario, partido, 1, 0)
    return partido


def _predecir_fallo(session, usuario, offset_dias):
    """Predicción que no acierta ni el ganador (base == 0)."""
    inicio = BASE + timedelta(days=offset_dias)
    partido = fabrica.crear_partido(session, inicio=inicio, resultado=(2, 0))
    fabrica.crear_prediccion(session, usuario, partido, 0, 2)
    return partido


def test_racha_de_3_da_mas_2(session):
    usuario = fabrica.crear_usuario(session)
    for i in range(3):
        _predecir_acierto(session, usuario, i)

    recalcular_usuario(session, usuario.id)

    puntaje = session.get(Puntaje, usuario.id)
    assert puntaje.bonus_racha == 2
    assert puntaje.racha_actual == 3
    assert puntaje.mejor_racha == 3


def test_racha_de_6_da_mas_4(session):
    usuario = fabrica.crear_usuario(session)
    for i in range(6):
        _predecir_acierto(session, usuario, i)

    recalcular_usuario(session, usuario.id)

    puntaje = session.get(Puntaje, usuario.id)
    assert puntaje.bonus_racha == 4
    assert puntaje.racha_actual == 6
    assert puntaje.mejor_racha == 6


def test_racha_de_5_da_mas_2(session):
    usuario = fabrica.crear_usuario(session)
    for i in range(5):
        _predecir_acierto(session, usuario, i)

    recalcular_usuario(session, usuario.id)

    puntaje = session.get(Puntaje, usuario.id)
    assert puntaje.bonus_racha == 2
    assert puntaje.racha_actual == 5
    assert puntaje.mejor_racha == 5


def test_un_fallo_reinicia_la_racha(session):
    usuario = fabrica.crear_usuario(session)
    _predecir_acierto(session, usuario, 0)
    _predecir_acierto(session, usuario, 1)
    _predecir_fallo(session, usuario, 2)
    _predecir_acierto(session, usuario, 3)

    recalcular_usuario(session, usuario.id)

    puntaje = session.get(Puntaje, usuario.id)
    assert puntaje.racha_actual == 1
    assert puntaje.mejor_racha == 2
    assert puntaje.bonus_racha == 0


def test_partido_no_pronosticado_no_corta_la_racha(session):
    usuario = fabrica.crear_usuario(session)
    _predecir_acierto(session, usuario, 0)
    _predecir_acierto(session, usuario, 1)
    # Partido con resultado en el día 2, pero el usuario nunca lo predijo:
    # no debe contar ni a favor ni en contra de su racha.
    fabrica.crear_partido(session, inicio=BASE + timedelta(days=2), resultado=(1, 1))
    _predecir_acierto(session, usuario, 3)

    recalcular_usuario(session, usuario.id)

    puntaje = session.get(Puntaje, usuario.id)
    assert puntaje.racha_actual == 3
    assert puntaje.mejor_racha == 3
    assert puntaje.bonus_racha == 2


def test_racha_se_ordena_por_inicio_sin_importar_el_orden_de_carga(session):
    usuario = fabrica.crear_usuario(session)
    # Se crean en orden cronológico inverso: el motor debe ordenar por
    # `inicio`, no por el orden de inserción.
    for i in reversed(range(3)):
        _predecir_acierto(session, usuario, i)

    recalcular_usuario(session, usuario.id)

    puntaje = session.get(Puntaje, usuario.id)
    assert puntaje.racha_actual == 3
    assert puntaje.bonus_racha == 2
