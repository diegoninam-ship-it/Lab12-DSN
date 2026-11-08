"""Fábrica de datos mínimos para las pruebas (contador propio para que
apodos/códigos de equipo sean únicos dentro de cada transacción de test)."""

import itertools
from datetime import datetime, timedelta

from app.models import Equipo, Fase, Partido, Prediccion, Rol, Usuario

_contador = itertools.count(1)


def crear_usuario(session, apodo: str | None = None, rol: Rol = Rol.USER) -> Usuario:
    n = next(_contador)
    usuario = Usuario(
        email=f"test{n}@correo.com",
        apodo=apodo or f"test{n}",
        password_hash="x",
        rol=rol,
    )
    session.add(usuario)
    session.flush()
    return usuario


def crear_equipo(session) -> Equipo:
    n = next(_contador)
    equipo = Equipo(nombre=f"Equipo {n}", codigo=f"E{n:02d}")
    session.add(equipo)
    session.flush()
    return equipo


def crear_partido(
    session,
    inicio: datetime,
    resultado: tuple[int, int] | None = None,
    fase: Fase = Fase.GRUPOS,
) -> Partido:
    local = crear_equipo(session)
    visitante = crear_equipo(session)
    partido = Partido(
        equipo_local_id=local.id,
        equipo_visitante_id=visitante.id,
        inicio=inicio,
        fase=fase,
        goles_local=resultado[0] if resultado else None,
        goles_visitante=resultado[1] if resultado else None,
        resultado_registrado_en=inicio if resultado else None,
    )
    session.add(partido)
    session.flush()
    return partido


def crear_prediccion(
    session,
    usuario: Usuario,
    partido: Partido,
    pl: int,
    pv: int,
    registrado_en: datetime | None = None,
) -> Prediccion:
    prediccion = Prediccion(
        usuario_id=usuario.id,
        partido_id=partido.id,
        goles_local=pl,
        goles_visitante=pv,
        registrado_en=registrado_en or (partido.inicio - timedelta(days=2)),
    )
    session.add(prediccion)
    session.flush()
    return prediccion
