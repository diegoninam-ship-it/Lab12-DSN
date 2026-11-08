"""T1 / sección 17.1: puntos base (10, 5, 3, 0)."""

import pytest

from app.scoring import puntos_base


@pytest.mark.parametrize(
    ("pl", "pv", "gl", "gv", "esperado"),
    [
        # Marcador exacto: 5 (exacto) + 3 (ganador) + 2 (diferencia) = 10
        (2, 0, 2, 0, 10),
        (1, 1, 1, 1, 10),
        # Ganador y diferencia, sin exacto: 3 + 2 = 5
        (3, 1, 2, 0, 5),
        (1, 1, 2, 2, 5),
        # Solo ganador o empate: 3
        (2, 0, 3, 0, 3),
        # Nada: 0
        (2, 0, 0, 1, 0),
    ],
)
def test_puntos_base(pl, pv, gl, gv, esperado):
    assert puntos_base(pl, pv, gl, gv) == esperado
