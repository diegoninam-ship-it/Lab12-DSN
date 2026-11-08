from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.ranking import ItemRanking


class SalaCrearEntrada(BaseModel):
    nombre: str = Field(min_length=3, max_length=50)


class SalaUnirseEntrada(BaseModel):
    codigo: str


class SalaItem(BaseModel):
    id: int
    nombre: str
    dueno_id: int
    es_dueno: bool
    creada_en: datetime


class MiembroSalida(BaseModel):
    usuario_id: int
    apodo: str
    unido_en: datetime
    es_dueno: bool


class SalaDetalle(SalaItem):
    codigo_invitacion: str
    miembros: list[MiembroSalida]


class SalaRankingSalida(BaseModel):
    sala_id: int
    items: list[ItemRanking]
