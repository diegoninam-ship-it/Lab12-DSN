from datetime import datetime

from pydantic import BaseModel


class EstadisticasMiasSalida(BaseModel):
    predicciones_con_resultado: int
    porcentaje_aciertos: float
    puntos_totales: int
    puntos_base: int
    bonus_anticipacion: int
    bonus_racha: int
    exactos: int
    aciertos: int
    racha_actual: int
    mejor_racha: int
    promedio_global_total: float
    diferencia_con_promedio: float


class EstadisticasSalaSalida(BaseModel):
    sala_id: int
    miembros: int
    promedio_total: float
    maximo_total: int
    minimo_total: int
    mejor_racha_sala: int


class AnalisisIASalida(BaseModel):
    texto: str
    generado_en: datetime
    version_datos: str

    model_config = {"from_attributes": True}


class ConfigSalida(BaseModel):
    ia_disponible: bool
