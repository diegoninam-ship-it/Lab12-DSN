from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencias import get_db, get_usuario_actual
from app.estadisticas import calcular_estadisticas_sala, calcular_estadisticas_usuario
from app.gemini import ErrorAnalisisIA, generar_analisis
from app.models import AmbitoAnalisis, AnalisisIA, Puntaje, SalaMiembro, Usuario
from app.routers.salas import _sala_como_miembro
from app.schemas.estadisticas import (
    AnalisisIASalida,
    ConfigSalida,
    EstadisticasMiasSalida,
    EstadisticasSalaSalida,
)

router = APIRouter(prefix="/api", tags=["estadisticas"])


@router.get("/config", response_model=ConfigSalida)
def config() -> ConfigSalida:
    return ConfigSalida(ia_disponible=bool(settings.gemini_api_key))


@router.get("/estadisticas/mias", response_model=EstadisticasMiasSalida)
def mis_estadisticas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> EstadisticasMiasSalida:
    return EstadisticasMiasSalida(**calcular_estadisticas_usuario(db, usuario.id))


@router.get("/salas/{sala_id}/estadisticas", response_model=EstadisticasSalaSalida)
def estadisticas_sala(
    sala_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> EstadisticasSalaSalida:
    _sala_como_miembro(db, sala_id, usuario)
    return EstadisticasSalaSalida(sala_id=sala_id, **calcular_estadisticas_sala(db, sala_id))


def _version_datos_usuario(db: Session, usuario_id: int) -> str:
    puntaje = db.get(Puntaje, usuario_id)
    return puntaje.actualizado_en.isoformat() if puntaje else "sin-datos"


def _version_datos_sala(db: Session, sala_id: int) -> str:
    max_ts = (
        db.query(func.max(Puntaje.actualizado_en))
        .join(SalaMiembro, SalaMiembro.usuario_id == Puntaje.usuario_id)
        .filter(SalaMiembro.sala_id == sala_id)
        .scalar()
    )
    return max_ts.isoformat() if max_ts else "sin-datos"


def _obtener_o_generar(
    db: Session,
    ambito: AmbitoAnalisis,
    referencia_id: int,
    version_datos: str,
    datos_agregados: dict,
) -> AnalisisIA:
    existente = db.query(AnalisisIA).filter_by(ambito=ambito, referencia_id=referencia_id).first()
    if existente is not None and existente.version_datos == version_datos:
        return existente

    try:
        texto = generar_analisis(datos_agregados)
    except ErrorAnalisisIA as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo generar el análisis con IA, intenta de nuevo más tarde",
        ) from exc

    if existente is None:
        existente = AnalisisIA(ambito=ambito, referencia_id=referencia_id)
        db.add(existente)

    existente.texto = texto
    existente.version_datos = version_datos
    existente.generado_en = datetime.now(timezone.utc)
    db.commit()
    db.refresh(existente)
    return existente


@router.post("/estadisticas/mias/analisis", response_model=AnalisisIASalida)
def analizar_mis_estadisticas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> AnalisisIA:
    if not settings.gemini_api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="IA no configurada")

    datos = calcular_estadisticas_usuario(db, usuario.id)
    version = _version_datos_usuario(db, usuario.id)
    return _obtener_o_generar(db, AmbitoAnalisis.USUARIO, usuario.id, version, datos)


@router.post("/salas/{sala_id}/estadisticas/analisis", response_model=AnalisisIASalida)
def analizar_estadisticas_sala(
    sala_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> AnalisisIA:
    _sala_como_miembro(db, sala_id, usuario)
    if not settings.gemini_api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="IA no configurada")

    datos = calcular_estadisticas_sala(db, sala_id)
    version = _version_datos_sala(db, sala_id)
    return _obtener_o_generar(db, AmbitoAnalisis.SALA, sala_id, version, datos)
