import secrets

ALFABETO_CODIGO_INVITACION = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
LONGITUD_CODIGO_INVITACION = 8


def generar_codigo_invitacion() -> str:
    return "".join(
        secrets.choice(ALFABETO_CODIGO_INVITACION) for _ in range(LONGITUD_CODIGO_INVITACION)
    )
