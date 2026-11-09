"""T5: cobertura de app/config.py — validaciones de la sección 12."""

import pytest
from pydantic import ValidationError

from app.config import Settings, _hostname_ascii


def _datos(**overrides):
    base = {
        "database_url": "postgresql+psycopg://u:p@h/db",
        "jwt_secret": "x" * 32,
    }
    base.update(overrides)
    return base


def test_jwt_secret_corto_falla():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **_datos(jwt_secret="corto"))


def test_server_id_vacio_usa_el_hostname_por_defecto():
    s = Settings(_env_file=None, **_datos())
    assert s.server_id


def test_server_id_no_ascii_falla():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **_datos(server_id="ñoño"))


def test_server_id_muy_largo_falla():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **_datos(server_id="x" * 101))


def test_carga_password_obligatorio_si_hay_seed_de_carga():
    # carga_password="" fuerza el caso vacío, por si el entorno real
    # (fuera del test) ya trae un CARGA_PASSWORD configurado.
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **_datos(seed_usuarios_carga=5, carga_password=""))

    s = Settings(_env_file=None, **_datos(seed_usuarios_carga=5, carga_password="x"))
    assert s.seed_usuarios_carga == 5


def test_hostname_ascii_cae_a_servidor_si_el_hostname_no_es_ascii(monkeypatch):
    import socket

    monkeypatch.setattr(socket, "gethostname", lambda: "ñoño")
    assert _hostname_ascii() == "servidor"
