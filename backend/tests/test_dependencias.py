"""T5: cobertura de app/dependencias.py — ramas no ejercitadas por las
pruebas de endpoints (token de un usuario que ya no existe, get_db en sí)."""

from fastapi import HTTPException
import pytest

from app.dependencias import get_db, get_usuario_actual
from app.seguridad import crear_token


class _RequestFalso:
    def __init__(self, cookies: dict[str, str]):
        self.cookies = cookies


def test_get_db_entrega_una_sesion_y_la_cierra():
    generador = get_db()
    sesion = next(generador)
    assert sesion is not None

    with pytest.raises(StopIteration):
        next(generador)


def test_get_usuario_actual_con_token_de_usuario_inexistente_401(session):
    # Token válido (firmado correctamente), pero el usuario del `sub` ya
    # no existe en la base: debe tratarse igual que "no autenticado".
    token = crear_token(usuario_id=999999)
    request = _RequestFalso(cookies={"mundial_token": token})

    with pytest.raises(HTTPException) as exc_info:
        get_usuario_actual(request, db=session)

    assert exc_info.value.status_code == 401
