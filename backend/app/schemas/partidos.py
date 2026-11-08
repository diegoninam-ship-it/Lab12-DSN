from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models import Fase


class EquipoSalida(BaseModel):
    id: int
    nombre: str
    codigo: str

    model_config = {"from_attributes": True}


class PrediccionPropia(BaseModel):
    goles_local: int
    goles_visitante: int
    registrado_en: datetime
    puntos_base: int | None
    bonus_anticipacion: int | None

    model_config = {"from_attributes": True}


class PartidoSalida(BaseModel):
    id: int
    equipo_local: EquipoSalida
    equipo_visitante: EquipoSalida
    inicio: datetime
    fase: str
    estado: str
    goles_local: int | None
    goles_visitante: int | None
    mi_prediccion: PrediccionPropia | None = None


class PrediccionConPartido(BaseModel):
    partido: PartidoSalida
    goles_local: int
    goles_visitante: int
    registrado_en: datetime
    puntos_base: int | None
    bonus_anticipacion: int | None


class PrediccionEntrada(BaseModel):
    goles_local: int = Field(ge=0, le=20)
    goles_visitante: int = Field(ge=0, le=20)


def _con_tz_utc(v: datetime) -> datetime:
    if v.tzinfo is None:
        return v.replace(tzinfo=timezone.utc)
    return v


class PartidoCrearEntrada(BaseModel):
    equipo_local_id: int
    equipo_visitante_id: int
    inicio: datetime
    fase: Fase

    @field_validator("inicio")
    @classmethod
    def _inicio_con_tz(cls, v: datetime) -> datetime:
        return _con_tz_utc(v)

    @model_validator(mode="after")
    def _equipos_distintos(self) -> "PartidoCrearEntrada":
        if self.equipo_local_id == self.equipo_visitante_id:
            raise ValueError("equipo_local_id y equipo_visitante_id deben ser distintos")
        return self


class PartidoEditarEntrada(PartidoCrearEntrada):
    pass


class ResultadoEntrada(BaseModel):
    goles_local: int = Field(ge=0)
    goles_visitante: int = Field(ge=0)
