from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings
from app.routers import admin as admin_router
from app.routers import auth as auth_router
from app.routers import partidos as partidos_router
from app.routers import ranking as ranking_router

app = FastAPI(title="Lab12 - Predicciones del Mundial")

MUTACIONES = {"POST", "PUT", "PATCH", "DELETE"}


class ServidorHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Servidor"] = settings.server_id
        return response


class SoloJSONMiddleware(BaseHTTPMiddleware):
    """Sección 6: las mutaciones solo aceptan application/json."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in MUTACIONES and request.url.path.startswith("/api"):
            content_length = request.headers.get("content-length")
            tiene_cuerpo = content_length not in (None, "0")
            content_type = request.headers.get("content-type", "")
            if tiene_cuerpo and not content_type.startswith("application/json"):
                return JSONResponse(
                    status_code=415,
                    content={"detail": "Las mutaciones solo aceptan application/json"},
                )
        return await call_next(request)


app.add_middleware(SoloJSONMiddleware)
app.add_middleware(ServidorHeaderMiddleware)

app.include_router(auth_router.router)
app.include_router(partidos_router.router)
app.include_router(ranking_router.router)
app.include_router(admin_router.router)


@app.get("/api/health")
async def health() -> dict:
    return {"estado": "ok"}


@app.get("/api/whoami")
async def whoami() -> dict:
    return {"servidor": settings.server_id}
