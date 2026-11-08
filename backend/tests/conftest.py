"""Configuración de pytest para el motor de puntuación (T1) y las pruebas
de API (T2+). Usa una base de datos de pruebas separada ("mundial_test",
en el mismo servidor Postgres que "mundial") para no mezclarse con los
datos del seed. Cada test corre en su propia transacción, que se revierte
al final: nada se commitea nunca, así que los tests no interfieren entre
sí ni dejan residuos.
"""

import psycopg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401  (registra los modelos en Base.metadata)
from app.config import settings
from app.db import Base
from app.dependencias import get_db, get_usuario_actual
from app.main import app
from app.models import Rol

from tests import fabrica


def _url_test(url: str) -> str:
    base, _, _resto = url.rpartition("/")
    return f"{base}/mundial_test"


def _url_sin_driver(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql://")


@pytest.fixture(scope="session")
def test_engine():
    url_admin = _url_sin_driver(settings.database_url)
    with psycopg.connect(url_admin, autocommit=True) as conexion_admin:
        existe = conexion_admin.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", ("mundial_test",)
        ).fetchone()
        if not existe:
            conexion_admin.execute("CREATE DATABASE mundial_test")

    engine = create_engine(_url_test(settings.database_url))
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def session(test_engine):
    conexion = test_engine.connect()
    transaccion = conexion.begin()
    SesionPrueba = sessionmaker(bind=conexion)
    sesion = SesionPrueba()
    try:
        yield sesion
    finally:
        sesion.close()
        transaccion.rollback()
        conexion.close()


@pytest.fixture()
def usuario(session):
    return fabrica.crear_usuario(session)


@pytest.fixture()
def admin(session):
    return fabrica.crear_usuario(session, rol=Rol.ADMIN)


@pytest.fixture()
def api(session):
    """Cliente con la base de datos de pruebas pero SIN forzar un usuario:
    útil para probar el flujo real de autenticación (registro/login con
    cookies de verdad)."""

    def _get_db():
        yield session

    app.dependency_overrides[get_db] = _get_db
    cliente = TestClient(app)
    yield cliente
    app.dependency_overrides.clear()


@pytest.fixture()
def como(api):
    """Factoría: `como(usuario)` hace que las próximas peticiones del
    cliente se autentiquen como ese usuario, sin pasar por login/cookies
    (eso ya se prueba aparte en test_api_auth.py)."""

    def _como(usuario_elegido):
        def _get_usuario_actual():
            return usuario_elegido

        app.dependency_overrides[get_usuario_actual] = _get_usuario_actual
        return api

    return _como


@pytest.fixture()
def cliente(como, usuario):
    return como(usuario)


@pytest.fixture()
def ahora_fija(monkeypatch):
    """Congela `datetime.now(timezone.utc)` para los módulos que lo usan,
    así las pruebas de cierre/anticipación no dependen del reloj real."""
    import datetime as _dt

    fijo = _dt.datetime(2026, 6, 1, 12, 0, 0, tzinfo=_dt.timezone.utc)

    class _DatetimeFijo(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return fijo if tz else fijo.replace(tzinfo=None)

    for modulo in ("app.scoring", "app.estado", "app.routers.partidos", "app.routers.admin"):
        monkeypatch.setattr(f"{modulo}.datetime", _DatetimeFijo)

    return fijo
