"""T5: cobertura de app/gemini.py. Nunca llama a la API real de Gemini
(sección 10: "en las pruebas automatizadas, Gemini siempre se simula");
se reemplaza `_llamar_gemini`, el único punto que toca el SDK."""

import pytest

import app.gemini as gemini_modulo
from app.gemini import ErrorAnalisisIA, generar_analisis


def test_generar_analisis_devuelve_el_texto_del_modelo(monkeypatch):
    monkeypatch.setattr(gemini_modulo, "_llamar_gemini", lambda datos: "texto generado")

    assert generar_analisis({"porcentaje_aciertos": 50.0}) == "texto generado"


def test_generar_analisis_envuelve_cualquier_falla_en_error_analisis_ia(monkeypatch):
    def _falla(_datos):
        raise RuntimeError("fallo simulado de Gemini")

    monkeypatch.setattr(gemini_modulo, "_llamar_gemini", _falla)

    with pytest.raises(ErrorAnalisisIA):
        generar_analisis({"porcentaje_aciertos": 50.0})
