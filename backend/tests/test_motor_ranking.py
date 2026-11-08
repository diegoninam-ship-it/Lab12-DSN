"""T1 / sección 17.1: desempates del ranking (sección 4.6) —
`total` desc, `exactos` desc, `aciertos` desc, `apodo` asc."""

from app.models import Puntaje

from tests import fabrica


def _con_puntaje(session, apodo, total, exactos, aciertos):
    usuario = fabrica.crear_usuario(session, apodo=apodo)
    session.add(Puntaje(usuario_id=usuario.id, total=total, exactos=exactos, aciertos=aciertos))
    session.flush()
    return usuario


def test_ranking_desempata_por_exactos_luego_aciertos_luego_apodo(session, cliente):
    # beta y alfa empatan en todo salvo el apodo -> alfa va primero (asc).
    _con_puntaje(session, "beta", total=10, exactos=2, aciertos=5)
    _con_puntaje(session, "alfa", total=10, exactos=2, aciertos=5)
    # gamma tiene más aciertos que alfa/beta pero menos exactos -> va después.
    _con_puntaje(session, "gamma", total=10, exactos=1, aciertos=9)
    # delta tiene más exactos que todos pero menos total -> va al final.
    _con_puntaje(session, "delta", total=5, exactos=5, aciertos=5)

    respuesta = cliente.get("/api/ranking?tamano=100")
    assert respuesta.status_code == 200

    apodos_esperados = ["alfa", "beta", "gamma", "delta"]
    orden = [
        item["apodo"] for item in respuesta.json()["items"] if item["apodo"] in apodos_esperados
    ]
    assert orden == apodos_esperados
