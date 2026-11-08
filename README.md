# Lab12-DSN — Predicciones del Mundial

Aplicación educativa para predecir resultados de partidos del Mundial 2026 (simulados) y acumular puntos según reglas de precisión. Incluye salas privadas por invitación, rankings, estadísticas y, opcionalmente, análisis con IA (Gemini).

## Desarrollo local

Requisitos: Docker Desktop.

```bash
cp backend/.env.example backend/.env
# edita backend/.env con tus propios valores (JWT_SECRET >= 32 caracteres)
docker compose up --build
```

- Backend: http://localhost:8000/api/health
- `GET /api/whoami` devuelve `{"servidor": SERVER_ID}` y toda respuesta incluye la cabecera `X-Servidor`.

## Estructura

```
backend/   API FastAPI (app/, alembic/, tests/)
frontend/  SPA React + Vite
loadtest/  Escenario de estrés con Locust
docs/      Documentación de pruebas y arquitectura
```

Ver `docs/ARQUITECTURA.md` y `docs/PRUEBAS.md` (se añaden en fases posteriores).
