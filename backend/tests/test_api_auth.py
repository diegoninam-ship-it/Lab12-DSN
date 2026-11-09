"""T2: autenticación (sección 6) — registro, login, logout, /yo.

Usa `api` (sin usuario forzado): las peticiones pasan por el flujo real
de cookies, como lo haría el navegador.
"""

from app.seguridad import hash_password

from tests import fabrica

NOMBRE_COOKIE = "mundial_token"


def _crear_usuario_con_clave(session, apodo, password):
    usuario = fabrica.crear_usuario(session, apodo=apodo)
    usuario.password_hash = hash_password(password)
    session.flush()
    return usuario


def test_registro_crea_usuario_y_autentica(api):
    respuesta = api.post(
        "/api/auth/registro",
        json={"email": "Nueva@Correo.com", "password": "clave1234", "apodo": "nueva1"},
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["email"] == "nueva@correo.com"  # normalizado a minúsculas
    assert cuerpo["apodo"] == "nueva1"
    assert cuerpo["rol"] == "USER"
    assert respuesta.cookies.get(NOMBRE_COOKIE) is not None

    # El registro deja autenticado: /yo debe devolver el mismo usuario.
    yo = api.get("/api/auth/yo")
    assert yo.status_code == 200
    assert yo.json()["apodo"] == "nueva1"


def test_registro_correo_duplicado_409(api):
    datos = {"email": "dup@correo.com", "password": "clave1234", "apodo": "dup1"}
    api.post("/api/auth/registro", json=datos)

    respuesta = api.post(
        "/api/auth/registro",
        json={"email": "dup@correo.com", "password": "clave1234", "apodo": "dup2"},
    )
    assert respuesta.status_code == 409


def test_registro_apodo_duplicado_409(api):
    api.post(
        "/api/auth/registro",
        json={"email": "a1@correo.com", "password": "clave1234", "apodo": "mismoapodo"},
    )
    respuesta = api.post(
        "/api/auth/registro",
        json={"email": "a2@correo.com", "password": "clave1234", "apodo": "mismoapodo"},
    )
    assert respuesta.status_code == 409


def test_registro_password_corta_422(api):
    respuesta = api.post(
        "/api/auth/registro",
        json={"email": "corta@correo.com", "password": "123", "apodo": "cortapw"},
    )
    assert respuesta.status_code == 422


def test_registro_apodo_invalido_422(api):
    respuesta = api.post(
        "/api/auth/registro",
        json={"email": "malapodo@correo.com", "password": "clave1234", "apodo": "a"},
    )
    assert respuesta.status_code == 422


def test_login_correcto(api, session):
    usuario = _crear_usuario_con_clave(session, "loginok", "clave1234")

    respuesta = api.post(
        "/api/auth/login", json={"email": usuario.email, "password": "clave1234"}
    )

    assert respuesta.status_code == 200
    assert respuesta.cookies.get(NOMBRE_COOKIE) is not None


def test_login_password_incorrecta_401(api, session):
    usuario = _crear_usuario_con_clave(session, "loginmal", "clave1234")

    respuesta = api.post(
        "/api/auth/login", json={"email": usuario.email, "password": "otraclave"}
    )

    assert respuesta.status_code == 401


def test_login_usuario_inexistente_401(api):
    respuesta = api.post(
        "/api/auth/login", json={"email": "no-existe@correo.com", "password": "clave1234"}
    )
    assert respuesta.status_code == 401


def test_logout_borra_la_sesion(api):
    api.post(
        "/api/auth/registro",
        json={"email": "logout1@correo.com", "password": "clave1234", "apodo": "logout1"},
    )

    api.post("/api/auth/logout")
    respuesta = api.get("/api/auth/yo")

    assert respuesta.status_code == 401


def test_yo_sin_sesion_401(api):
    respuesta = api.get("/api/auth/yo")
    assert respuesta.status_code == 401


def test_yo_con_cookie_invalida_401(api):
    api.cookies.set(NOMBRE_COOKIE, "token-invalido-y-mal-formado")
    respuesta = api.get("/api/auth/yo")
    assert respuesta.status_code == 401
