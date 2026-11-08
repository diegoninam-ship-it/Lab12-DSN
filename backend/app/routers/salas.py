from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencias import get_db, get_usuario_actual
from app.invitaciones import generar_codigo_invitacion
from app.models import Puntaje, Sala, SalaMiembro, Usuario
from app.schemas.ranking import ItemRanking
from app.schemas.salas import (
    MiembroSalida,
    SalaCrearEntrada,
    SalaDetalle,
    SalaItem,
    SalaRankingSalida,
    SalaUnirseEntrada,
)

router = APIRouter(prefix="/api/salas", tags=["salas"])


def _sala_como_miembro(db: Session, sala_id: int, usuario: Usuario) -> Sala:
    sala = db.get(Sala, sala_id)
    if sala is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sala no encontrada")
    es_miembro = (
        db.query(SalaMiembro).filter_by(sala_id=sala_id, usuario_id=usuario.id).first()
    )
    if es_miembro is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sala no encontrada")
    return sala


def _serializar_item(sala: Sala, usuario: Usuario) -> SalaItem:
    return SalaItem(
        id=sala.id,
        nombre=sala.nombre,
        dueno_id=sala.dueno_id,
        es_dueno=sala.dueno_id == usuario.id,
        creada_en=sala.creada_en,
    )


def _serializar_detalle(db: Session, sala: Sala, usuario: Usuario) -> SalaDetalle:
    filas = (
        db.query(SalaMiembro, Usuario.apodo)
        .join(Usuario, Usuario.id == SalaMiembro.usuario_id)
        .filter(SalaMiembro.sala_id == sala.id)
        .order_by(SalaMiembro.unido_en)
        .all()
    )
    return SalaDetalle(
        id=sala.id,
        nombre=sala.nombre,
        dueno_id=sala.dueno_id,
        es_dueno=sala.dueno_id == usuario.id,
        creada_en=sala.creada_en,
        codigo_invitacion=sala.codigo_invitacion,
        miembros=[
            MiembroSalida(
                usuario_id=miembro.usuario_id,
                apodo=apodo,
                unido_en=miembro.unido_en,
                es_dueno=miembro.usuario_id == sala.dueno_id,
            )
            for miembro, apodo in filas
        ],
    )


@router.post("", response_model=SalaDetalle, status_code=status.HTTP_201_CREATED)
def crear_sala(
    datos: SalaCrearEntrada,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> SalaDetalle:
    sala = Sala(
        nombre=datos.nombre,
        codigo_invitacion=generar_codigo_invitacion(),
        dueno_id=usuario.id,
    )
    db.add(sala)
    db.flush()
    db.add(SalaMiembro(sala_id=sala.id, usuario_id=usuario.id))
    db.commit()
    db.refresh(sala)
    return _serializar_detalle(db, sala, usuario)


@router.get("", response_model=list[SalaItem])
def listar_mis_salas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> list[SalaItem]:
    salas = (
        db.query(Sala)
        .join(SalaMiembro, SalaMiembro.sala_id == Sala.id)
        .filter(SalaMiembro.usuario_id == usuario.id)
        .order_by(Sala.creada_en.desc())
        .all()
    )
    return [_serializar_item(s, usuario) for s in salas]


@router.post("/unirse", response_model=SalaDetalle)
def unirse_sala(
    datos: SalaUnirseEntrada,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> SalaDetalle:
    sala = db.query(Sala).filter_by(codigo_invitacion=datos.codigo).first()
    if sala is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código inválido")

    ya_es_miembro = (
        db.query(SalaMiembro).filter_by(sala_id=sala.id, usuario_id=usuario.id).first()
    )
    if ya_es_miembro is None:
        db.add(SalaMiembro(sala_id=sala.id, usuario_id=usuario.id))
        db.commit()

    return _serializar_detalle(db, sala, usuario)


@router.get("/{sala_id}", response_model=SalaDetalle)
def detalle_sala(
    sala_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> SalaDetalle:
    sala = _sala_como_miembro(db, sala_id, usuario)
    return _serializar_detalle(db, sala, usuario)


@router.get("/{sala_id}/ranking", response_model=SalaRankingSalida)
def ranking_sala(
    sala_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> SalaRankingSalida:
    _sala_como_miembro(db, sala_id, usuario)

    total_col = func.coalesce(Puntaje.total, 0)
    exactos_col = func.coalesce(Puntaje.exactos, 0)
    aciertos_col = func.coalesce(Puntaje.aciertos, 0)
    racha_actual_col = func.coalesce(Puntaje.racha_actual, 0)
    mejor_racha_col = func.coalesce(Puntaje.mejor_racha, 0)

    filas = (
        db.query(
            Usuario.apodo,
            total_col.label("total"),
            exactos_col.label("exactos"),
            aciertos_col.label("aciertos"),
            racha_actual_col.label("racha_actual"),
            mejor_racha_col.label("mejor_racha"),
        )
        .join(SalaMiembro, SalaMiembro.usuario_id == Usuario.id)
        .outerjoin(Puntaje, Puntaje.usuario_id == Usuario.id)
        .filter(SalaMiembro.sala_id == sala_id)
        .order_by(total_col.desc(), exactos_col.desc(), aciertos_col.desc(), Usuario.apodo.asc())
        .all()
    )

    items = [
        ItemRanking(
            posicion=i + 1,
            apodo=fila.apodo,
            total=fila.total,
            exactos=fila.exactos,
            aciertos=fila.aciertos,
            racha_actual=fila.racha_actual,
            mejor_racha=fila.mejor_racha,
        )
        for i, fila in enumerate(filas)
    ]
    return SalaRankingSalida(sala_id=sala_id, items=items)


@router.post("/{sala_id}/salir")
def salir_sala(
    sala_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> dict:
    sala = _sala_como_miembro(db, sala_id, usuario)
    if sala.dueno_id == usuario.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El dueño no puede salir de la sala; debe eliminarla",
        )

    db.query(SalaMiembro).filter_by(sala_id=sala_id, usuario_id=usuario.id).delete()
    db.commit()
    return {"ok": True}


@router.post("/{sala_id}/codigo", response_model=SalaDetalle)
def regenerar_codigo(
    sala_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> SalaDetalle:
    sala = _sala_como_miembro(db, sala_id, usuario)
    if sala.dueno_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Solo el dueño puede regenerar el código"
        )

    sala.codigo_invitacion = generar_codigo_invitacion()
    db.commit()
    db.refresh(sala)
    return _serializar_detalle(db, sala, usuario)


@router.delete("/{sala_id}/miembros/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def expulsar_miembro(
    sala_id: int,
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> None:
    sala = _sala_como_miembro(db, sala_id, usuario)
    if sala.dueno_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Solo el dueño puede expulsar miembros"
        )
    if usuario_id == sala.dueno_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="El dueño no puede expulsarse a sí mismo"
        )

    membresia = db.query(SalaMiembro).filter_by(sala_id=sala_id, usuario_id=usuario_id).first()
    if membresia is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="El usuario no es miembro de la sala"
        )

    db.delete(membresia)
    db.commit()


@router.delete("/{sala_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sala(
    sala_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
) -> None:
    sala = _sala_como_miembro(db, sala_id, usuario)
    if sala.dueno_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Solo el dueño puede eliminar la sala"
        )

    db.query(SalaMiembro).filter_by(sala_id=sala_id).delete()
    db.delete(sala)
    db.commit()
