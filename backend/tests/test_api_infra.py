"""T5: cobertura de app/main.py — health, whoami, y el middleware que
exige application/json en las mutaciones (sección 6 y 8)."""


def test_health(api):
    respuesta = api.get("/api/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


def test_whoami(api):
    respuesta = api.get("/api/whoami")
    assert respuesta.status_code == 200
    assert "servidor" in respuesta.json()


def test_x_servidor_en_toda_respuesta(api):
    respuesta = api.get("/api/health")
    assert "x-servidor" in respuesta.headers


def test_mutacion_sin_content_type_json_da_415(api):
    respuesta = api.post(
        "/api/auth/login",
        content=b'{"email": "a@a.com", "password": "x"}',
    )
    assert respuesta.status_code == 415
