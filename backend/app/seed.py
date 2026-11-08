"""Datos semilla (sección 13 de CONTEXT.md).

Idempotente: el admin y los equipos se crean solo si no existen. Los datos
de demostración (partidos, predicciones, salas) se crean solo si no hay
partidos. Con --reiniciar se borran y se vuelven a crear con fechas
relativas a "ahora".

Uso:
    python -m app.seed [--reiniciar]
"""

import argparse
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.db import SessionLocal
from app.invitaciones import generar_codigo_invitacion
from app.seguridad import hash_password
from app.models import (
    AnalisisIA,
    Equipo,
    Fase,
    Partido,
    Prediccion,
    Puntaje,
    Rol,
    Sala,
    SalaMiembro,
    Usuario,
)
from app.scoring import recalcular_todo

CONTRASENA_DEMO = "Demo12345"

EQUIPOS = [
    ("Argentina", "ARG"),
    ("Brasil", "BRA"),
    ("Francia", "FRA"),
    ("España", "ESP"),
    ("Alemania", "GER"),
    ("Inglaterra", "ENG"),
    ("Portugal", "POR"),
    ("Países Bajos", "NED"),
    ("Bélgica", "BEL"),
    ("Italia", "ITA"),
    ("Croacia", "CRO"),
    ("Uruguay", "URU"),
    ("México", "MEX"),
    ("Estados Unidos", "USA"),
    ("Japón", "JPN"),
    ("Marruecos", "MAR"),
]

# (offset desde "ahora", resultado (gl, gv) o None). Las primeras 9 ya
# tienen resultado; las siguientes 6 están a más de 24 h; las siguientes 4
# a menos de 24 h; las últimas 2 a pocos minutos (demuestran el cierre).
PARTIDOS_OFFSETS = (
    [(timedelta(days=-10), (2, 0))]
    + [(timedelta(days=-9), (1, 1))]
    + [(timedelta(days=-8), (3, 0))]
    + [(timedelta(days=-7), (0, 0))]
    + [(timedelta(days=-6), (2, 1))]
    + [(timedelta(days=-5), (1, 0))]
    + [(timedelta(days=-4), (3, 1))]
    + [(timedelta(days=-3), (2, 0))]
    + [(timedelta(days=-2), (1, 2))]
    + [(timedelta(days=d), None) for d in (2, 3, 4, 5, 6, 7)]
    + [(timedelta(hours=h), None) for h in (3, 6, 10, 20)]
    + [(timedelta(minutes=m), None) for m in (15, 30)]
)

FASES = (
    [Fase.GRUPOS] * 12
    + [Fase.OCTAVOS] * 4
    + [Fase.CUARTOS] * 2
    + [Fase.SEMIFINAL] * 1
    + [Fase.TERCER_PUESTO] * 1
    + [Fase.FINAL] * 1
)

# Predicciones demo diseñadas para que, tras el recálculo, se vea cada
# regla: marcador exacto (10), ganador+diferencia sin exacto (5), solo
# ganador (3), una racha de 6 (+4) y un +1 por anticipación. Todas se
# registran a menos de 24 h del inicio (sin el +1), salvo "anticipado",
# que se registra 5 días antes para aislar ese bonus.
PREDICCIONES_DEMO = [
    # apodo, índice de partido, goles_local, goles_visitante, anticipación
    ("exacto1", 0, 2, 0, timedelta(hours=12)),
    ("anticipado", 0, 1, 0, timedelta(days=5)),
    ("difer1", 1, 0, 0, timedelta(hours=12)),
    ("ganador1", 2, 2, 0, timedelta(hours=12)),
    ("rachero", 3, 1, 1, timedelta(hours=12)),
    ("rachero", 4, 1, 0, timedelta(hours=12)),
    ("rachero", 5, 2, 0, timedelta(hours=12)),
    ("rachero", 6, 1, 0, timedelta(hours=12)),
    ("rachero", 7, 3, 0, timedelta(hours=12)),
    ("rachero", 8, 2, 3, timedelta(hours=12)),
]

USUARIOS_DEMO = ["exacto1", "difer1", "ganador1", "rachero", "anticipado"]


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _crear_admin(session) -> None:
    if not (settings.admin_email and settings.admin_password and settings.admin_apodo):
        raise RuntimeError(
            "ADMIN_EMAIL, ADMIN_PASSWORD y ADMIN_APODO son obligatorios para el seed"
        )
    if session.query(Usuario).filter_by(email=settings.admin_email).first():
        return
    session.add(
        Usuario(
            email=settings.admin_email,
            apodo=settings.admin_apodo,
            password_hash=hash_password(settings.admin_password),
            rol=Rol.ADMIN,
        )
    )


def _crear_equipos(session) -> None:
    existentes = {codigo for (codigo,) in session.query(Equipo.codigo)}
    for nombre, codigo in EQUIPOS:
        if codigo not in existentes:
            session.add(Equipo(nombre=nombre, codigo=codigo))


def _limpiar_demo(session) -> None:
    session.query(AnalisisIA).delete()
    session.query(SalaMiembro).delete()
    session.query(Sala).delete()
    session.query(Puntaje).delete()
    session.query(Prediccion).delete()
    session.query(Partido).delete()


def _crear_partidos(session) -> list[Partido]:
    equipos_por_codigo = {e.codigo: e for e in session.query(Equipo)}
    codigos = [codigo for _, codigo in EQUIPOS]
    ahora = _ahora()
    partidos = []
    for i, (offset, resultado) in enumerate(PARTIDOS_OFFSETS):
        local = equipos_por_codigo[codigos[i % 16]]
        visitante = equipos_por_codigo[codigos[(i + 5) % 16]]
        inicio = ahora + offset
        partido = Partido(
            equipo_local_id=local.id,
            equipo_visitante_id=visitante.id,
            inicio=inicio,
            fase=FASES[i],
            goles_local=resultado[0] if resultado else None,
            goles_visitante=resultado[1] if resultado else None,
            resultado_registrado_en=inicio if resultado else None,
        )
        session.add(partido)
        partidos.append(partido)
    return partidos


def _crear_usuarios_demo(session) -> dict[str, Usuario]:
    usuarios = {}
    for apodo in USUARIOS_DEMO:
        usuario = session.query(Usuario).filter_by(apodo=apodo).first()
        if usuario is None:
            usuario = Usuario(
                email=f"{apodo}@demo-mundial.com",
                apodo=apodo,
                password_hash=hash_password(CONTRASENA_DEMO),
                rol=Rol.USER,
            )
            session.add(usuario)
        usuarios[apodo] = usuario
    return usuarios


def _crear_predicciones_demo(session, partidos: list[Partido], usuarios: dict[str, Usuario]) -> None:
    for apodo, idx, pl, pv, anticipacion in PREDICCIONES_DEMO:
        partido = partidos[idx]
        session.add(
            Prediccion(
                usuario_id=usuarios[apodo].id,
                partido_id=partido.id,
                goles_local=pl,
                goles_visitante=pv,
                registrado_en=partido.inicio - anticipacion,
            )
        )


def _crear_salas_demo(session, usuarios: dict[str, Usuario]) -> None:
    salas = [
        ("Amigos del Mundial", "exacto1", ["exacto1", "difer1", "ganador1"]),
        ("Oficina Backend", "rachero", ["rachero", "anticipado", "exacto1"]),
    ]
    for nombre, dueno_apodo, miembros in salas:
        sala = Sala(
            nombre=nombre,
            codigo_invitacion=generar_codigo_invitacion(),
            dueno_id=usuarios[dueno_apodo].id,
        )
        session.add(sala)
        session.flush()
        for apodo in miembros:
            session.add(SalaMiembro(sala_id=sala.id, usuario_id=usuarios[apodo].id))


def ejecutar(reiniciar: bool = False) -> None:
    session = SessionLocal()
    try:
        _crear_admin(session)
        _crear_equipos(session)
        session.flush()

        if reiniciar:
            _limpiar_demo(session)
            session.flush()

        hay_partidos = session.query(Partido).first() is not None
        if not hay_partidos:
            partidos = _crear_partidos(session)
            session.flush()
            usuarios = _crear_usuarios_demo(session)
            session.flush()
            _crear_predicciones_demo(session, partidos, usuarios)
            _crear_salas_demo(session, usuarios)
            session.flush()

        recalcular_todo(session)
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed de Lab12 - Predicciones del Mundial")
    parser.add_argument(
        "--reiniciar",
        action="store_true",
        help="Borra los datos de demostración (partidos, predicciones, puntajes, salas, análisis) y los vuelve a crear",
    )
    args = parser.parse_args()
    ejecutar(reiniciar=args.reiniciar)
