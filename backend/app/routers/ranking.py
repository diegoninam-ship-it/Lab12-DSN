from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencias import get_db, get_usuario_actual
from app.models import Puntaje, Usuario
from app.schemas.ranking import ItemRanking, RankingSalida

router = APIRouter(prefix="/api", tags=["ranking"])


@router.get("/ranking", response_model=RankingSalida)
def ranking_global(
    pagina: int = Query(1, ge=1),
    tamano: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_usuario_actual),
) -> RankingSalida:
    total_col = func.coalesce(Puntaje.total, 0)
    exactos_col = func.coalesce(Puntaje.exactos, 0)
    aciertos_col = func.coalesce(Puntaje.aciertos, 0)
    racha_actual_col = func.coalesce(Puntaje.racha_actual, 0)
    mejor_racha_col = func.coalesce(Puntaje.mejor_racha, 0)

    total_usuarios = db.query(func.count(Usuario.id)).scalar()

    filas = (
        db.query(
            Usuario.apodo,
            total_col.label("total"),
            exactos_col.label("exactos"),
            aciertos_col.label("aciertos"),
            racha_actual_col.label("racha_actual"),
            mejor_racha_col.label("mejor_racha"),
        )
        .outerjoin(Puntaje, Puntaje.usuario_id == Usuario.id)
        .order_by(total_col.desc(), exactos_col.desc(), aciertos_col.desc(), Usuario.apodo.asc())
        .offset((pagina - 1) * tamano)
        .limit(tamano)
        .all()
    )

    items = [
        ItemRanking(
            posicion=(pagina - 1) * tamano + i + 1,
            apodo=fila.apodo,
            total=fila.total,
            exactos=fila.exactos,
            aciertos=fila.aciertos,
            racha_actual=fila.racha_actual,
            mejor_racha=fila.mejor_racha,
        )
        for i, fila in enumerate(filas)
    ]

    return RankingSalida(pagina=pagina, tamano=tamano, total_usuarios=total_usuarios, items=items)
