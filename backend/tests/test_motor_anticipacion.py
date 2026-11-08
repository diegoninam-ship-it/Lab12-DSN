"""T1 / sección 17.1: bonus de anticipación (regla 5, DEC-4, DEC-5)."""

from datetime import datetime, timedelta, timezone

from app.scoring import bonus_anticipacion, recalcular_usuario

from tests import fabrica

INICIO = datetime(2026, 6, 1, 20, 0, 0, tzinfo=timezone.utc)


def test_mas_de_24h_y_1_segundo_da_el_bonus():
    registrado_en = INICIO - timedelta(hours=24, seconds=1)
    assert bonus_anticipacion(INICIO, registrado_en, base=3) == 1


def test_exactamente_24h_no_da_el_bonus():
    registrado_en = INICIO - timedelta(hours=24)
    assert bonus_anticipacion(INICIO, registrado_en, base=3) == 0


def test_sin_puntos_base_no_da_el_bonus_aunque_sea_con_anticipacion():
    registrado_en = INICIO - timedelta(days=10)
    assert bonus_anticipacion(INICIO, registrado_en, base=0) == 0


def test_editar_dentro_de_24h_pierde_el_bonus(session):
    """Registrar con 5 días de anticipación y luego editar a 1h antes del
    inicio: el `registrado_en` de la última edición es lo único que cuenta
    (DEC-4), así que el bonus desaparece al recalcular."""
    usuario = fabrica.crear_usuario(session)
    partido = fabrica.crear_partido(session, inicio=INICIO, resultado=(2, 0))
    prediccion = fabrica.crear_prediccion(
        session, usuario, partido, 2, 0, registrado_en=INICIO - timedelta(days=5)
    )

    recalcular_usuario(session, usuario.id)
    assert prediccion.puntos_base == 10
    assert prediccion.bonus_anticipacion == 1

    # El usuario edita su predicción una hora antes del inicio.
    prediccion.registrado_en = INICIO - timedelta(hours=1)
    recalcular_usuario(session, usuario.id)

    assert prediccion.puntos_base == 10
    assert prediccion.bonus_anticipacion == 0
