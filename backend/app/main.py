from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

app = FastAPI(title="Lab12 - Predicciones del Mundial")


class ServidorHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Servidor"] = settings.server_id
        return response


app.add_middleware(ServidorHeaderMiddleware)


@app.get("/api/health")
async def health() -> dict:
    return {"estado": "ok"}


@app.get("/api/whoami")
async def whoami() -> dict:
    return {"servidor": settings.server_id}
