"""Análisis con IA (sección 10). Usa el SDK google-genai: el patrón de
llamada actual de la documentación oficial es `client.interactions.create`
(no `client.models.generate_content`, que es el patrón de SDKs anteriores).

Solo se envían números agregados (nunca correos, apodos ni IDs). El
timeout de 20 s se aplica con un hilo aparte en vez de depender de un
parámetro propio del SDK, para no asumir una API que no está documentada.
"""

import concurrent.futures

from google import genai

from app.config import settings

TIMEOUT_SEGUNDOS = 20

PROMPT_INSTRUCCIONES = (
    "Eres un analista breve de un juego educativo de predicciones del "
    "Mundial. Con estos datos agregados y anónimos, escribe un comentario "
    "en español de máximo 120 palabras. No inventes datos que no estén en "
    "la lista."
)


class ErrorAnalisisIA(Exception):
    pass


def _llamar_gemini(datos_agregados: dict) -> str:
    cliente = genai.Client(api_key=settings.gemini_api_key)
    entrada = f"{PROMPT_INSTRUCCIONES}\n\nDatos: {datos_agregados}"
    interaccion = cliente.interactions.create(model=settings.gemini_model, input=entrada)
    return interaccion.output_text


def generar_analisis(datos_agregados: dict) -> str:
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ejecutor:
            future = ejecutor.submit(_llamar_gemini, datos_agregados)
            return future.result(timeout=TIMEOUT_SEGUNDOS)
    except Exception as exc:
        raise ErrorAnalisisIA(str(exc)) from exc
