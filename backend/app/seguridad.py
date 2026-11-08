from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, Response, status

from app.config import settings

NOMBRE_COOKIE = "mundial_token"
DURACION_SESION = timedelta(hours=8)
ALGORITMO_JWT = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def crear_token(usuario_id: int) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {"sub": str(usuario_id), "iat": ahora, "exp": ahora + DURACION_SESION}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITMO_JWT)


def decodificar_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITMO_JWT])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida"
        ) from exc


def establecer_cookie(response: Response, usuario_id: int) -> None:
    token = crear_token(usuario_id)
    response.set_cookie(
        key=NOMBRE_COOKIE,
        value=token,
        httponly=True,
        samesite="strict",
        secure=settings.cookie_secure,
        path="/api",
        max_age=int(DURACION_SESION.total_seconds()),
    )


def borrar_cookie(response: Response) -> None:
    response.delete_cookie(
        key=NOMBRE_COOKIE,
        path="/api",
        httponly=True,
        samesite="strict",
        secure=settings.cookie_secure,
    )
