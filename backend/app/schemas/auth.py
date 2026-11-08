import re

from pydantic import BaseModel, EmailStr, Field, field_validator

PATRON_APODO = re.compile(r"^[A-Za-z0-9_]{3,20}$")


class RegistroEntrada(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    apodo: str

    @field_validator("email")
    @classmethod
    def _email_minusculas(cls, v: str) -> str:
        return v.lower()

    @field_validator("apodo")
    @classmethod
    def _apodo_valido(cls, v: str) -> str:
        if not PATRON_APODO.match(v):
            raise ValueError("El apodo debe tener 3-20 caracteres [A-Za-z0-9_]")
        return v


class LoginEntrada(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def _email_minusculas(cls, v: str) -> str:
        return v.lower()


class UsuarioPublico(BaseModel):
    id: int
    email: str
    apodo: str
    rol: str

    model_config = {"from_attributes": True}
