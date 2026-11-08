"""Cálculos de estadísticas (sección 8: GET /api/estadisticas/mias y
GET /api/salas/{id}/estadisticas). Devuelven solo valores agregados: los
mismos que luego se envían a Gemini, nunca correos, apodos ni IDs."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Prediccion, Puntaje, SalaMiembro, Usuario


def calcular_estadisticas_usuario(db: Session, usuario_id: int) -> dict:
    predicciones_con_resultado = (
        db.query(func.count(Prediccion.id))
        .filter(Prediccion.usuario_id == usuario_id, Prediccion.puntos_base.is_not(None))
        .scalar()
    )

    puntaje = db.get(Puntaje, usuario_id)
    aciertos = puntaje.aciertos if puntaje else 0
    total_usuario = puntaje.total if puntaje else 0

    porcentaje_aciertos = (
        round(aciertos / predicciones_con_resultado * 100, 2) if predicciones_con_resultado else 0.0
    )

    total_usuarios = db.query(func.count(Usuario.id)).scalar() or 0
    suma_totales = db.query(func.coalesce(func.sum(Puntaje.total), 0)).scalar() or 0
    promedio_global_total = round(suma_totales / total_usuarios, 2) if total_usuarios else 0.0

    return {
        "predicciones_con_resultado": predicciones_con_resultado,
        "porcentaje_aciertos": porcentaje_aciertos,
        "puntos_totales": total_usuario,
        "puntos_base": puntaje.puntos_base if puntaje else 0,
        "bonus_anticipacion": puntaje.bonus_anticipacion if puntaje else 0,
        "bonus_racha": puntaje.bonus_racha if puntaje else 0,
        "exactos": puntaje.exactos if puntaje else 0,
        "aciertos": aciertos,
        "racha_actual": puntaje.racha_actual if puntaje else 0,
        "mejor_racha": puntaje.mejor_racha if puntaje else 0,
        "promedio_global_total": promedio_global_total,
        "diferencia_con_promedio": round(total_usuario - promedio_global_total, 2),
    }


def calcular_estadisticas_sala(db: Session, sala_id: int) -> dict:
    filas = (
        db.query(
            func.coalesce(Puntaje.total, 0).label("total"),
            func.coalesce(Puntaje.mejor_racha, 0).label("mejor_racha"),
        )
        .select_from(Usuario)
        .join(SalaMiembro, SalaMiembro.usuario_id == Usuario.id)
        .outerjoin(Puntaje, Puntaje.usuario_id == Usuario.id)
        .filter(SalaMiembro.sala_id == sala_id)
        .all()
    )

    miembros = len(filas)
    totales = [fila.total for fila in filas]
    promedio_total = round(sum(totales) / miembros, 2) if miembros else 0.0
    maximo_total = max(totales) if totales else 0
    minimo_total = min(totales) if totales else 0
    mejor_racha_sala = max((fila.mejor_racha for fila in filas), default=0)

    return {
        "miembros": miembros,
        "promedio_total": promedio_total,
        "maximo_total": maximo_total,
        "minimo_total": minimo_total,
        "mejor_racha_sala": mejor_racha_sala,
    }
