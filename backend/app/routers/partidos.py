from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencias import get_db, get_usuario_actual
from app.estado import calcular_estado
from app.models import Equipo, Partido, Prediccion, Usuario
from app.schemas.partidos import (
    EquipoSalida,
    PartidoSalida,
    PrediccionConPartido,
    PrediccionEntrada,
    PrediccionPropia,
)

router = APIRouter(prefix="/api", tags=["partidos"])


def serializar_partido(partido: Partido, prediccion: Prediccion | None) -> PartidoSalida:
    return PartidoSalida(
        id=partido.id,
        equipo_local=EquipoSalida.model_validate(partido.equipo_local),
        equipo_visitante=EquipoSalida.model_validate(partido.equipo_visitante),
        inicio=partido.inicio,
        fase=partido.fase.value,
        estado=calcular_estado(partido),
        goles_local=partido.goles_local,
        goles_visitante=partido.goles_visitante,
        mi_prediccion=PrediccionPropia.model_validate(prediccion) if prediccion else None,
    )


@router.get("/equipos", response_model=list[EquipoSalida])
def listar_equipos(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_usuario_actual),
) -> list[Equipo]:
    return db.query(Equipo).order_by(Equipo.nombre).all()


@router.get("/partidos", response_model=list[PartidoSalida])
def listar_partidos(
    estado: Literal["PROGRAMADO", "EN_JUEGO", "FINALIZADO"] | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> list[PartidoSalida]:
    partidos = db.query(Partido).order_by(Partido.inicio).all()
    predicciones = {
        p.partido_id: p for p in db.query(Prediccion).filter_by(usuario_id=usuario.id).all()
    }
    salida = [serializar_partido(p, predicciones.get(p.id)) for p in partidos]
    if estado is not None:
        salida = [s for s in salida if s.estado == estado]
    return salida


@router.get("/partidos/{partido_id}", response_model=PartidoSalida)
def detalle_partido(
    partido_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> PartidoSalida:
    partido = db.get(Partido, partido_id)
    if partido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partido no encontrado")
    prediccion = db.query(Prediccion).filter_by(usuario_id=usuario.id, partido_id=partido_id).first()
    return serializar_partido(partido, prediccion)


@router.put("/partidos/{partido_id}/prediccion", response_model=PrediccionPropia)
def predecir(
    partido_id: int,
    datos: PrediccionEntrada,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> Prediccion:
    partido = db.get(Partido, partido_id)
    if partido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partido no encontrado")

    ahora = datetime.now(timezone.utc)
    if ahora >= partido.inicio:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Las predicciones están cerradas: el partido ya inició",
        )

    prediccion = db.query(Prediccion).filter_by(usuario_id=usuario.id, partido_id=partido_id).first()
    if prediccion is None:
        prediccion = Prediccion(usuario_id=usuario.id, partido_id=partido_id)
        db.add(prediccion)

    prediccion.goles_local = datos.goles_local
    prediccion.goles_visitante = datos.goles_visitante
    prediccion.registrado_en = ahora

    db.commit()
    db.refresh(prediccion)
    return prediccion


@router.get("/predicciones/mias", response_model=list[PrediccionConPartido])
def mis_predicciones(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> list[PrediccionConPartido]:
    filas = (
        db.query(Prediccion, Partido)
        .join(Partido, Prediccion.partido_id == Partido.id)
        .filter(Prediccion.usuario_id == usuario.id)
        .order_by(Partido.inicio)
        .all()
    )
    return [
        PrediccionConPartido(
            partido=serializar_partido(partido, prediccion),
            goles_local=prediccion.goles_local,
            goles_visitante=prediccion.goles_visitante,
            registrado_en=prediccion.registrado_en,
            puntos_base=prediccion.puntos_base,
            bonus_anticipacion=prediccion.bonus_anticipacion,
        )
        for prediccion, partido in filas
    ]
