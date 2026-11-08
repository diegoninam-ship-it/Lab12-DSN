import socket

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _hostname_ascii() -> str:
    try:
        return socket.gethostname().encode("ascii").decode("ascii")
    except UnicodeEncodeError:
        return "servidor"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret: str
    server_id: str = ""
    cookie_secure: bool = False
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    admin_email: str | None = None
    admin_password: str | None = None
    admin_apodo: str | None = None
    seed_usuarios_carga: int = 0
    carga_password: str | None = None

    @field_validator("jwt_secret")
    @classmethod
    def _jwt_secret_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET debe tener al menos 32 caracteres")
        return v

    @field_validator("server_id")
    @classmethod
    def _server_id_default_and_validate(cls, v: str) -> str:
        if not v:
            v = _hostname_ascii()
        try:
            v.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError("SERVER_ID debe ser ASCII") from exc
        if not (1 <= len(v) <= 100):
            raise ValueError("SERVER_ID debe tener entre 1 y 100 caracteres")
        return v

    @model_validator(mode="after")
    def _carga_password_required_if_seed(self) -> "Settings":
        if self.seed_usuarios_carga > 0 and not self.carga_password:
            raise ValueError(
                "CARGA_PASSWORD es obligatorio cuando SEED_USUARIOS_CARGA > 0"
            )
        return self


settings = Settings()
