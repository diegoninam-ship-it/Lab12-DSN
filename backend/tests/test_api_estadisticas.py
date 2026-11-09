"""T5: cobertura de estadísticas calculadas y análisis con IA (sección 8
y 10). Gemini siempre se simula (nunca llama a la API real): se
reemplaza `generar_analisis` tal como lo importó el router."""

import app.routers.estadisticas as estadisticas_router
from app.config import settings
from app.gemini import ErrorAnalisisIA

from tests import fabrica


def test_config_ia_no_disponible_por_defecto(cliente):
    respuesta = cliente.get("/api/config")
    assert respuesta.status_code == 200
    assert respuesta.json()["ia_disponible"] is False


def test_config_ia_disponible_con_api_key(cliente, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "clave-de-prueba")
    respuesta = cliente.get("/api/config")
    assert respuesta.json()["ia_disponible"] is True


def test_mis_estadisticas_usuario_sin_predicciones(cliente):
    respuesta = cliente.get("/api/estadisticas/mias")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["predicciones_con_resultado"] == 0
    assert cuerpo["puntos_totales"] == 0


def test_estadisticas_sala_no_miembro_404(como, usuario, session):
    sala = como(usuario).post("/api/salas", json={"nombre": "Sala stats"}).json()
    externo = fabrica.crear_usuario(session)

    respuesta = como(externo).get(f"/api/salas/{sala['id']}/estadisticas")
    assert respuesta.status_code == 404


def test_estadisticas_sala_miembro_ok(como, usuario, session):
    sala = como(usuario).post("/api/salas", json={"nombre": "Sala stats 2"}).json()

    respuesta = como(usuario).get(f"/api/salas/{sala['id']}/estadisticas")
    assert respuesta.status_code == 200
    assert respuesta.json()["miembros"] == 1


def test_analisis_mio_503_sin_api_key(cliente):
    respuesta = cliente.post("/api/estadisticas/mias/analisis")
    assert respuesta.status_code == 503


def test_analisis_sala_503_sin_api_key(como, usuario, session):
    sala = como(usuario).post("/api/salas", json={"nombre": "Sala IA"}).json()
    respuesta = como(usuario).post(f"/api/salas/{sala['id']}/estadisticas/analisis")
    assert respuesta.status_code == 503


def test_analisis_sala_no_miembro_404_antes_que_503(como, usuario, session):
    # Aunque falte la clave, el 404 de "no revela que la sala existe"
    # tiene prioridad sobre el 503 de IA no configurada.
    sala = como(usuario).post("/api/salas", json={"nombre": "Sala privada"}).json()
    externo = fabrica.crear_usuario(session)

    respuesta = como(externo).post(f"/api/salas/{sala['id']}/estadisticas/analisis")
    assert respuesta.status_code == 404


def test_analisis_mio_generado_y_cacheado(cliente, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "clave-de-prueba")
    llamadas = []

    def _generar_falso(datos):
        llamadas.append(datos)
        return "análisis de prueba"

    monkeypatch.setattr(estadisticas_router, "generar_analisis", _generar_falso)

    primera = cliente.post("/api/estadisticas/mias/analisis")
    assert primera.status_code == 200
    assert primera.json()["texto"] == "análisis de prueba"
    assert len(llamadas) == 1

    # version_datos no cambió (sin recálculo de por medio): se sirve el
    # análisis guardado, sin llamar a Gemini otra vez.
    segunda = cliente.post("/api/estadisticas/mias/analisis")
    assert segunda.status_code == 200
    assert len(llamadas) == 1


def test_analisis_mio_502_si_gemini_falla(cliente, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "clave-de-prueba")

    def _falla(datos):
        raise ErrorAnalisisIA("fallo simulado")

    monkeypatch.setattr(estadisticas_router, "generar_analisis", _falla)

    respuesta = cliente.post("/api/estadisticas/mias/analisis")
    assert respuesta.status_code == 502


def test_analisis_sala_generado(como, usuario, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "clave-de-prueba")
    monkeypatch.setattr(
        estadisticas_router, "generar_analisis", lambda datos: "análisis de sala"
    )

    sala = como(usuario).post("/api/salas", json={"nombre": "Sala IA 2"}).json()
    respuesta = como(usuario).post(f"/api/salas/{sala['id']}/estadisticas/analisis")

    assert respuesta.status_code == 200
    assert respuesta.json()["texto"] == "análisis de sala"
