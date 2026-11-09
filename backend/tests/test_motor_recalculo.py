"""T1 / sección 17.1: recálculo (DEC-7) — corregir, anular, idempotencia."""

from datetime import datetime, timedelta, timezone

from app.models import Puntaje
from app.scoring import recalcular_partido, recalcular_todo, recalcular_usuario

from tests import fabrica

INICIO = datetime(2026, 3, 1, tzinfo=timezone.utc)

# A menos de 24h del inicio: sin bonus de anticipación, así las
# aserciones de estas pruebas se centran solo en los puntos base.
REGISTRADO_SIN_ANTICIPACION = INICIO - timedelta(hours=1)


def test_corregir_resultado_cambia_los_puntos(session):
    usuario = fabrica.crear_usuario(session)
    partido = fabrica.crear_partido(session, inicio=INICIO, resultado=(2, 0))
    fabrica.crear_prediccion(
        session, usuario, partido, 2, 0, registrado_en=REGISTRADO_SIN_ANTICIPACION
    )

    recalcular_partido(session, partido.id)
    assert session.get(Puntaje, usuario.id).total == 10

    # El admin corrige el resultado: ya no es exacto, solo acierta el ganador.
    partido.goles_local = 5
    partido.goles_visitante = 0
    recalcular_partido(session, partido.id)

    assert session.get(Puntaje, usuario.id).total == 3


def test_anular_resultado_quita_los_puntos(session):
    usuario = fabrica.crear_usuario(session)
    partido = fabrica.crear_partido(session, inicio=INICIO, resultado=(2, 0))
    prediccion = fabrica.crear_prediccion(
        session, usuario, partido, 2, 0, registrado_en=REGISTRADO_SIN_ANTICIPACION
    )

    recalcular_partido(session, partido.id)
    assert session.get(Puntaje, usuario.id).total == 10

    # El admin anula el resultado (igual que DELETE .../resultado).
    partido.goles_local = None
    partido.goles_visitante = None
    partido.resultado_registrado_en = None
    prediccion.puntos_base = None
    prediccion.bonus_anticipacion = None
    recalcular_partido(session, partido.id)

    puntaje = session.get(Puntaje, usuario.id)
    assert puntaje.total == 0
    assert puntaje.aciertos == 0
    assert puntaje.exactos == 0


def _foto(session, usuario_id):
    p = session.get(Puntaje, usuario_id)
    return (
        p.total,
        p.puntos_base,
        p.bonus_anticipacion,
        p.bonus_racha,
        p.aciertos,
        p.exactos,
        p.racha_actual,
        p.mejor_racha,
    )


def test_recalcular_dos_veces_da_el_mismo_resultado(session):
    usuario = fabrica.crear_usuario(session)
    partido = fabrica.crear_partido(session, inicio=INICIO, resultado=(1, 0))
    fabrica.crear_prediccion(session, usuario, partido, 1, 0)

    recalcular_usuario(session, usuario.id)
    primero = _foto(session, usuario.id)

    recalcular_usuario(session, usuario.id)
    segundo = _foto(session, usuario.id)

    assert primero == segundo


def test_recalcular_partido_no_toca_a_quien_no_predijo(session):
    """Sección 4.5: 'los demás no cambian' — recalcular un partido solo
    afecta a los usuarios con una predicción en él."""
    usuario_a = fabrica.crear_usuario(session)
    usuario_b = fabrica.crear_usuario(session)
    partido_a = fabrica.crear_partido(session, inicio=INICIO, resultado=(2, 0))
    partido_b = fabrica.crear_partido(session, inicio=INICIO, resultado=(1, 1))
    fabrica.crear_prediccion(
        session, usuario_a, partido_a, 2, 0, registrado_en=REGISTRADO_SIN_ANTICIPACION
    )
    fabrica.crear_prediccion(
        session, usuario_b, partido_b, 1, 1, registrado_en=REGISTRADO_SIN_ANTICIPACION
    )

    recalcular_usuario(session, usuario_a.id)
    recalcular_usuario(session, usuario_b.id)
    assert session.get(Puntaje, usuario_b.id).total == 10

    partido_a.goles_local = 9
    recalcular_partido(session, partido_a.id)

    # usuario_b no tenía predicción en partido_a: su puntaje no cambia.
    assert session.get(Puntaje, usuario_b.id).total == 10


def test_recalcular_todo_recalcula_a_todos_los_usuarios(session):
    """Usado por el seed: recorre todos los usuarios de la base, no solo
    los de un partido o usuario en particular."""
    usuario_a = fabrica.crear_usuario(session)
    usuario_b = fabrica.crear_usuario(session)
    partido = fabrica.crear_partido(session, inicio=INICIO, resultado=(1, 0))
    fabrica.crear_prediccion(
        session, usuario_a, partido, 2, 0, registrado_en=REGISTRADO_SIN_ANTICIPACION
    )
    fabrica.crear_prediccion(
        session, usuario_b, partido, 0, 1, registrado_en=REGISTRADO_SIN_ANTICIPACION
    )

    recalcular_todo(session)

    assert session.get(Puntaje, usuario_a.id).total == 3
    assert session.get(Puntaje, usuario_b.id).total == 0
