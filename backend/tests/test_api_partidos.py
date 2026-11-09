"""T5: cierre de cobertura — endpoints de solo lectura de partidos
(sección 8) que T1/T2 no ejercitaron directamente."""

from datetime import datetime, timedelta, timezone

from tests import fabrica

AHORA = datetime.now(timezone.utc)


def test_listar_equipos(cliente, session):
    fabrica.crear_equipo(session)
    fabrica.crear_equipo(session)

    respuesta = cliente.get("/api/equipos")

    assert respuesta.status_code == 200
    assert len(respuesta.json()) >= 2


def test_listar_partidos_incluye_mi_prediccion(cliente, usuario, session):
    partido = fabrica.crear_partido(session, inicio=AHORA + timedelta(days=1))
    fabrica.crear_prediccion(session, usuario, partido, 1, 1)

    respuesta = cliente.get("/api/partidos")

    assert respuesta.status_code == 200
    item = next(p for p in respuesta.json() if p["id"] == partido.id)
    assert item["mi_prediccion"]["goles_local"] == 1
    assert item["estado"] == "PROGRAMADO"


def test_listar_partidos_filtra_por_estado(cliente, session):
    fabrica.crear_partido(session, inicio=AHORA + timedelta(days=1))
    fabrica.crear_partido(session, inicio=AHORA - timedelta(days=1), resultado=(1, 0))

    respuesta = cliente.get("/api/partidos?estado=FINALIZADO")

    assert respuesta.status_code == 200
    assert all(p["estado"] == "FINALIZADO" for p in respuesta.json())


def test_detalle_partido_404(cliente):
    respuesta = cliente.get("/api/partidos/999999")
    assert respuesta.status_code == 404


def test_detalle_partido_ok(cliente, session):
    partido = fabrica.crear_partido(session, inicio=AHORA + timedelta(days=1))

    respuesta = cliente.get(f"/api/partidos/{partido.id}")

    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == partido.id


def test_predecir_partido_inexistente_404(cliente):
    respuesta = cliente.put(
        "/api/partidos/999999/prediccion", json={"goles_local": 1, "goles_visitante": 0}
    )
    assert respuesta.status_code == 404


def test_mis_predicciones_vacio(cliente):
    respuesta = cliente.get("/api/predicciones/mias")
    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_mis_predicciones_con_datos(cliente, usuario, session):
    partido = fabrica.crear_partido(session, inicio=AHORA + timedelta(days=1))
    fabrica.crear_prediccion(session, usuario, partido, 2, 1)

    respuesta = cliente.get("/api/predicciones/mias")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["goles_local"] == 2
    assert cuerpo[0]["partido"]["id"] == partido.id
