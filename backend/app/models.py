import enum
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


class Rol(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class Fase(str, enum.Enum):
    GRUPOS = "GRUPOS"
    OCTAVOS = "OCTAVOS"
    CUARTOS = "CUARTOS"
    SEMIFINAL = "SEMIFINAL"
    TERCER_PUESTO = "TERCER_PUESTO"
    FINAL = "FINAL"


class AmbitoAnalisis(str, enum.Enum):
    USUARIO = "USUARIO"
    SALA = "SALA"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    apodo: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]
    rol: Mapped[Rol] = mapped_column(SAEnum(Rol, name="rol"), default=Rol.USER, server_default=Rol.USER.value)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Equipo(Base):
    __tablename__ = "equipos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str]
    codigo: Mapped[str] = mapped_column(unique=True)


class Partido(Base):
    __tablename__ = "partidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipo_local_id: Mapped[int] = mapped_column(ForeignKey("equipos.id"))
    equipo_visitante_id: Mapped[int] = mapped_column(ForeignKey("equipos.id"))
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fase: Mapped[Fase] = mapped_column(SAEnum(Fase, name="fase"))
    goles_local: Mapped[int | None]
    goles_visitante: Mapped[int | None]
    resultado_registrado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    equipo_local = relationship("Equipo", foreign_keys=[equipo_local_id])
    equipo_visitante = relationship("Equipo", foreign_keys=[equipo_visitante_id])

    __table_args__ = (
        CheckConstraint("equipo_local_id <> equipo_visitante_id", name="ck_partido_equipos_distintos"),
        CheckConstraint("goles_local IS NULL OR goles_local >= 0", name="ck_partido_goles_local_no_negativo"),
        CheckConstraint(
            "goles_visitante IS NULL OR goles_visitante >= 0", name="ck_partido_goles_visitante_no_negativo"
        ),
    )


class Prediccion(Base):
    __tablename__ = "predicciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    partido_id: Mapped[int] = mapped_column(ForeignKey("partidos.id"))
    goles_local: Mapped[int]
    goles_visitante: Mapped[int]
    registrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    puntos_base: Mapped[int | None]
    bonus_anticipacion: Mapped[int | None]

    __table_args__ = (
        UniqueConstraint("usuario_id", "partido_id", name="uq_prediccion_usuario_partido"),
        CheckConstraint("goles_local >= 0 AND goles_local <= 20", name="ck_prediccion_goles_local_rango"),
        CheckConstraint(
            "goles_visitante >= 0 AND goles_visitante <= 20", name="ck_prediccion_goles_visitante_rango"
        ),
    )


class Puntaje(Base):
    __tablename__ = "puntajes"

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), primary_key=True)
    total: Mapped[int] = mapped_column(default=0, server_default="0")
    puntos_base: Mapped[int] = mapped_column(default=0, server_default="0")
    bonus_anticipacion: Mapped[int] = mapped_column(default=0, server_default="0")
    bonus_racha: Mapped[int] = mapped_column(default=0, server_default="0")
    aciertos: Mapped[int] = mapped_column(default=0, server_default="0")
    exactos: Mapped[int] = mapped_column(default=0, server_default="0")
    racha_actual: Mapped[int] = mapped_column(default=0, server_default="0")
    mejor_racha: Mapped[int] = mapped_column(default=0, server_default="0")
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Sala(Base):
    __tablename__ = "salas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str]
    codigo_invitacion: Mapped[str] = mapped_column(unique=True)
    dueno_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "char_length(nombre) >= 3 AND char_length(nombre) <= 50", name="ck_sala_nombre_longitud"
        ),
    )


class SalaMiembro(Base):
    __tablename__ = "sala_miembros"

    sala_id: Mapped[int] = mapped_column(ForeignKey("salas.id"), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), primary_key=True)
    unido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnalisisIA(Base):
    __tablename__ = "analisis_ia"

    id: Mapped[int] = mapped_column(primary_key=True)
    ambito: Mapped[AmbitoAnalisis] = mapped_column(SAEnum(AmbitoAnalisis, name="ambito_analisis"))
    referencia_id: Mapped[int]
    version_datos: Mapped[str]
    texto: Mapped[str]
    generado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("ambito", "referencia_id", name="uq_analisis_ambito_referencia"),
    )


Index("ix_predicciones_partido_id", Prediccion.partido_id)
Index("ix_predicciones_usuario_id", Prediccion.usuario_id)
Index("ix_partidos_inicio", Partido.inicio)
Index(
    "ix_puntajes_ranking",
    Puntaje.total.desc(),
    Puntaje.exactos.desc(),
    Puntaje.aciertos.desc(),
)
