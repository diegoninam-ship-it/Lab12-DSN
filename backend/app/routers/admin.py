from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencias import get_admin_actual, get_db
from app.estado import calcular_estado
from app.models import Equipo, Partido, Prediccion, Usuario
from app.schemas.partidos import (
    EquipoSalida,
    PartidoCrearEntrada,
    PartidoEditarEntrada,
    PartidoSalida,
    ResultadoEntrada,
)
from app.scoring import recalcular_partido

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _serializar(partido: Partido) -> PartidoSalida:
    return PartidoSalida(
        id=partido.id,
        equipo_local=EquipoSalida.model_validate(partido.equipo_local),
        equipo_visitante=EquipoSalida.model_validate(partido.equipo_visitante),
        inicio=partido.inicio,
        fase=partido.fase.value,
        estado=calcular_estado(partido),
        goles_local=partido.goles_local,
        goles_visitante=partido.goles_visitante,
        mi_prediccion=None,
    )


def _obtener_equipo(db: Session, equipo_id: int) -> Equipo:
    equipo = db.get(Equipo, equipo_id)
    if equipo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"El equipo {equipo_id} no existe"
        )
    return equipo


def _obtener_partido(db: Session, partido_id: int) -> Partido:
    partido = db.get(Partido, partido_id)
    if partido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partido no encontrado")
    return partido


@router.post("/partidos", response_model=PartidoSalida, status_code=status.HTTP_201_CREATED)
def crear_partido(
    datos: PartidoCrearEntrada,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin_actual),
) -> PartidoSalida:
    _obtener_equipo(db, datos.equipo_local_id)
    _obtener_equipo(db, datos.equipo_visitante_id)

    partido = Partido(
        equipo_local_id=datos.equipo_local_id,
        equipo_visitante_id=datos.equipo_visitante_id,
        inicio=datos.inicio,
        fase=datos.fase,
    )
    db.add(partido)
    db.commit()
    db.refresh(partido)
    return _serializar(partido)


@router.put("/partidos/{partido_id}", response_model=PartidoSalida)
def editar_partido(
    partido_id: int,
    datos: PartidoEditarEntrada,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin_actual),
) -> PartidoSalida:
    partido = _obtener_partido(db, partido_id)

    if datetime.now(timezone.utc) >= partido.inicio:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se puede editar un partido mientras está PROGRAMADO",
        )

    _obtener_equipo(db, datos.equipo_local_id)
    _obtener_equipo(db, datos.equipo_visitante_id)

    partido.equipo_local_id = datos.equipo_local_id
    partido.equipo_visitante_id = datos.equipo_visitante_id
    partido.inicio = datos.inicio
    partido.fase = datos.fase

    db.commit()
    db.refresh(partido)
    return _serializar(partido)


@router.delete("/partidos/{partido_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_partido(
    partido_id: int,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin_actual),
) -> None:
    partido = _obtener_partido(db, partido_id)

    tiene_predicciones = db.query(Prediccion).filter_by(partido_id=partido_id).first() is not None
    if tiene_predicciones:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar un partido con predicciones",
        )

    db.delete(partido)
    db.commit()


@router.put("/partidos/{partido_id}/resultado", response_model=PartidoSalida)
def registrar_resultado(
    partido_id: int,
    datos: ResultadoEntrada,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin_actual),
) -> PartidoSalida:
    partido = _obtener_partido(db, partido_id)

    ahora = datetime.now(timezone.utc)
    if ahora < partido.inicio:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede registrar un resultado antes de que el partido inicie",
        )

    partido.goles_local = datos.goles_local
    partido.goles_visitante = datos.goles_visitante
    partido.resultado_registrado_en = ahora

    db.flush()
    recalcular_partido(db, partido.id)
    db.commit()
    db.refresh(partido)
    return _serializar(partido)


@router.delete("/partidos/{partido_id}/resultado", response_model=PartidoSalida)
def anular_resultado(
    partido_id: int,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin_actual),
) -> PartidoSalida:
    partido = _obtener_partido(db, partido_id)

    if partido.goles_local is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="El partido no tiene resultado registrado"
        )

    partido.goles_local = None
    partido.goles_visitante = None
    partido.resultado_registrado_en = None

    for prediccion in db.query(Prediccion).filter_by(partido_id=partido_id).all():
        prediccion.puntos_base = None
        prediccion.bonus_anticipacion = None

    db.flush()
    recalcular_partido(db, partido.id)
    db.commit()
    db.refresh(partido)
    return _serializar(partido)
