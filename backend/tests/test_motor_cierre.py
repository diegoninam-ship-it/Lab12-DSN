"""T1 / sección 17.1: cierre de predicciones al inicio del partido
(DEC-3). `ahora_fija` congela el reloj del servidor en 2026-06-01 12:00
UTC para poder probar el límite exacto."""

from datetime import timedelta

from tests import fabrica


def test_rechaza_justo_al_iniciar(cliente, session, usuario, ahora_fija):
    partido = fabrica.crear_partido(session, inicio=ahora_fija)

    respuesta = cliente.put(
        f"/api/partidos/{partido.id}/prediccion",
        json={"goles_local": 1, "goles_visitante": 0},
    )

    assert respuesta.status_code == 409


def test_rechaza_despues_de_iniciado(cliente, session, usuario, ahora_fija):
    partido = fabrica.crear_partido(session, inicio=ahora_fija - timedelta(seconds=1))

    respuesta = cliente.put(
        f"/api/partidos/{partido.id}/prediccion",
        json={"goles_local": 1, "goles_visitante": 0},
    )

    assert respuesta.status_code == 409


def test_acepta_un_segundo_antes_de_iniciar(cliente, session, usuario, ahora_fija):
    partido = fabrica.crear_partido(session, inicio=ahora_fija + timedelta(seconds=1))

    respuesta = cliente.put(
        f"/api/partidos/{partido.id}/prediccion",
        json={"goles_local": 1, "goles_visitante": 0},
    )

    assert respuesta.status_code == 200
