"""T2: administración (sección 5 — permisos ADMIN; sección 8 —
CRUD de partidos y resultado)."""

from datetime import datetime, timedelta, timezone

from app.models import Puntaje
from app.scoring import recalcular_partido

from tests import fabrica

FUTURO = datetime(2030, 1, 1, tzinfo=timezone.utc)
PASADO = datetime(2020, 1, 1, tzinfo=timezone.utc)


def test_no_admin_no_puede_crear_partido(como, usuario, session):
    local = fabrica.crear_equipo(session)
    visitante = fabrica.crear_equipo(session)

    respuesta = como(usuario).post(
        "/api/admin/partidos",
        json={
            "equipo_local_id": local.id,
            "equipo_visitante_id": visitante.id,
            "inicio": "2027-01-01T00:00:00Z",
            "fase": "GRUPOS",
        },
    )

    assert respuesta.status_code == 403


def test_admin_crea_partido(como, admin, session):
    local = fabrica.crear_equipo(session)
    visitante = fabrica.crear_equipo(session)

    respuesta = como(admin).post(
        "/api/admin/partidos",
        json={
            "equipo_local_id": local.id,
            "equipo_visitante_id": visitante.id,
            "inicio": "2027-01-01T00:00:00Z",
            "fase": "GRUPOS",
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "PROGRAMADO"


def test_crear_partido_con_el_mismo_equipo_422(como, admin, session):
    equipo = fabrica.crear_equipo(session)

    respuesta = como(admin).post(
        "/api/admin/partidos",
        json={
            "equipo_local_id": equipo.id,
            "equipo_visitante_id": equipo.id,
            "inicio": "2027-01-01T00:00:00Z",
            "fase": "GRUPOS",
        },
    )

    assert respuesta.status_code == 422


def test_crear_partido_con_equipo_inexistente_404(como, admin, session):
    local = fabrica.crear_equipo(session)

    respuesta = como(admin).post(
        "/api/admin/partidos",
        json={
            "equipo_local_id": local.id,
            "equipo_visitante_id": 999999,
            "inicio": "2027-01-01T00:00:00Z",
            "fase": "GRUPOS",
        },
    )

    assert respuesta.status_code == 404


def test_editar_partido_programado(como, admin, session, ahora_fija):
    partido = fabrica.crear_partido(session, inicio=ahora_fija + timedelta(days=1))

    respuesta = como(admin).put(
        f"/api/admin/partidos/{partido.id}",
        json={
            "equipo_local_id": partido.equipo_local_id,
            "equipo_visitante_id": partido.equipo_visitante_id,
            "inicio": "2030-01-01T00:00:00Z",
            "fase": "FINAL",
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["fase"] == "FINAL"


def test_editar_partido_ya_iniciado_409(como, admin, session, ahora_fija):
    partido = fabrica.crear_partido(session, inicio=ahora_fija - timedelta(hours=1))

    respuesta = como(admin).put(
        f"/api/admin/partidos/{partido.id}",
        json={
            "equipo_local_id": partido.equipo_local_id,
            "equipo_visitante_id": partido.equipo_visitante_id,
            "inicio": "2030-01-01T00:00:00Z",
            "fase": "FINAL",
        },
    )

    assert respuesta.status_code == 409


def test_eliminar_partido_sin_predicciones(como, admin, session):
    partido = fabrica.crear_partido(session, inicio=FUTURO)

    respuesta = como(admin).delete(f"/api/admin/partidos/{partido.id}")

    assert respuesta.status_code == 204


def test_eliminar_partido_con_predicciones_409(como, admin, usuario, session):
    partido = fabrica.crear_partido(session, inicio=FUTURO)
    fabrica.crear_prediccion(session, usuario, partido, 1, 0)

    respuesta = como(admin).delete(f"/api/admin/partidos/{partido.id}")

    assert respuesta.status_code == 409


def test_registrar_resultado_antes_de_iniciar_409(como, admin, session, ahora_fija):
    partido = fabrica.crear_partido(session, inicio=ahora_fija + timedelta(hours=1))

    respuesta = como(admin).put(
        f"/api/admin/partidos/{partido.id}/resultado",
        json={"goles_local": 1, "goles_visitante": 0},
    )

    assert respuesta.status_code == 409


def test_registrar_resultado_recalcula_puntajes(como, admin, usuario, session, ahora_fija):
    partido = fabrica.crear_partido(session, inicio=ahora_fija - timedelta(hours=1))
    fabrica.crear_prediccion(
        session, usuario, partido, 2, 0, registrado_en=ahora_fija - timedelta(hours=2)
    )

    respuesta = como(admin).put(
        f"/api/admin/partidos/{partido.id}/resultado",
        json={"goles_local": 2, "goles_visitante": 0},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "FINALIZADO"
    assert session.get(Puntaje, usuario.id).total == 10


def test_anular_resultado_sin_resultado_409(como, admin, session):
    partido = fabrica.crear_partido(session, inicio=PASADO)

    respuesta = como(admin).delete(f"/api/admin/partidos/{partido.id}/resultado")

    assert respuesta.status_code == 409


def test_anular_resultado(como, admin, usuario, session):
    partido = fabrica.crear_partido(session, inicio=PASADO, resultado=(2, 0))
    fabrica.crear_prediccion(session, usuario, partido, 2, 0)
    recalcular_partido(session, partido.id)
    assert session.get(Puntaje, usuario.id).total > 0

    respuesta = como(admin).delete(f"/api/admin/partidos/{partido.id}/resultado")

    assert respuesta.status_code == 200
    assert respuesta.json()["goles_local"] is None
    assert session.get(Puntaje, usuario.id).total == 0


def test_editar_partido_inexistente_404(como, admin):
    respuesta = como(admin).put(
        "/api/admin/partidos/999999",
        json={
            "equipo_local_id": 1,
            "equipo_visitante_id": 2,
            "inicio": "2030-01-01T00:00:00Z",
            "fase": "GRUPOS",
        },
    )
    assert respuesta.status_code == 404


def test_eliminar_partido_inexistente_404(como, admin):
    respuesta = como(admin).delete("/api/admin/partidos/999999")
    assert respuesta.status_code == 404


def test_crear_partido_inicio_sin_zona_horaria_se_asume_utc(como, admin, session):
    local = fabrica.crear_equipo(session)
    visitante = fabrica.crear_equipo(session)

    respuesta = como(admin).post(
        "/api/admin/partidos",
        json={
            "equipo_local_id": local.id,
            "equipo_visitante_id": visitante.id,
            "inicio": "2030-01-01T00:00:00",
            "fase": "GRUPOS",
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["inicio"].endswith("Z") or "+00:00" in respuesta.json()["inicio"]


def test_registrar_resultado_partido_inexistente_404(como, admin):
    respuesta = como(admin).put(
        "/api/admin/partidos/999999/resultado",
        json={"goles_local": 1, "goles_visitante": 0},
    )
    assert respuesta.status_code == 404
