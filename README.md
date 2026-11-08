# Lab12-DSN — Predicciones del Mundial

Aplicación educativa para predecir resultados de partidos del Mundial 2026 (simulados) y acumular puntos según reglas de precisión. Incluye salas privadas por invitación, rankings, estadísticas y, opcionalmente, análisis con IA (Gemini).

## Desarrollo local (Docker Compose)

Requisitos: Docker Desktop.

```bash
cp backend/.env.example backend/.env
# edita backend/.env con tus propios valores (JWT_SECRET >= 32 caracteres)
docker compose up --build
```

- App: http://localhost:8080 (nginx sirve el frontend y balancea `/api/` hacia el backend)
- `GET /api/whoami` devuelve `{"servidor": SERVER_ID}` y toda respuesta incluye la cabecera `X-Servidor`, visible en el pie de página de la app ("Atendido por: ...").
- La migración de la base de datos y el seed de datos demo corren una sola vez, en el servicio `migrate` (nunca al arrancar `backend`).

### Usuarios demo (creados por el seed)

| Apodo | Correo | Contraseña | Rol |
|---|---|---|---|
| admin | `ADMIN_EMAIL` del `.env` | `ADMIN_PASSWORD` del `.env` | ADMIN |
| exacto1, difer1, ganador1, rachero, anticipado | `<apodo>@demo-mundial.com` | `Demo12345` | USER |

Para refrescar las fechas de los partidos demo (por ejemplo, antes de una demo en vivo):

```bash
docker compose run --rm migrate sh -c "alembic upgrade head && python -m app.seed --reiniciar"
```

### Escalar el backend

```bash
docker compose up -d --scale backend=3
```

nginx (`frontend/nginx.conf`) usa el resolver interno de Docker (`127.0.0.11`) con re-resolución dinámica (`server backend:8000 resolve;`) y una `zone` compartida para el Round Robin, así que **no hace falta reiniciar nginx** al escalar: las nuevas réplicas se detectan solas dentro de los 10 s de TTL del resolver (verificado contra nginx 1.31.6 de la imagen `nginx:alpine`, que soporta `resolve` en open source desde la 1.27.3).

## Desarrollo del frontend por separado (opcional)

```bash
cd frontend
npm install
npm run dev
```

`vite.config.ts` incluye un proxy de `/api` hacia `http://localhost:8000` solo para `vite dev` (el navegador sigue viendo un único origen, igual que en producción detrás de nginx). Requiere el backend corriendo (`docker compose up db migrate backend`).

## Estructura

```
backend/   API FastAPI (app/, alembic/, tests/)
frontend/  SPA React + Vite + TypeScript, Dockerfile y nginx.conf
loadtest/  Escenario de estrés con Locust
docs/      Documentación de pruebas y arquitectura
```

Ver `docs/ARQUITECTURA.md` y `docs/PRUEBAS.md` (se añaden en fases posteriores).

## Despliegue en AWS (Etapa 4 — la ejecuta el usuario)

`docker-compose.aws.yml` (sin `db` ni `migrate`) corre `backend` + `frontend` dentro de cada instancia del Auto Scaling Group, detrás de un ALB. RDS PostgreSQL vive aparte, en subredes privadas.

1. Construir y subir las imágenes a Docker Hub (`linux/amd64`):
   ```bash
   docker buildx build --platform linux/amd64 -t diegozx/lab12-backend:latest --push ./backend
   docker buildx build --platform linux/amd64 -t diegozx/lab12-frontend:latest --push ./frontend
   ```
2. En cada instancia (vía user data o manualmente), exportar las variables de entorno (`DATABASE_URL`, `JWT_SECRET`, `SERVER_ID`, etc., normalmente leídas desde SSM Parameter Store) y correr:
   ```bash
   docker compose -f docker-compose.aws.yml up -d
   ```
3. Migración y seed: **una sola vez**, a mano, desde una instancia vía Session Manager (nunca en el user data de cada instancia):
   ```bash
   docker compose -f docker-compose.aws.yml run --rm backend alembic upgrade head
   docker compose -f docker-compose.aws.yml run --rm backend python -m app.seed
   ```

El resto de la infraestructura (ALB, Auto Scaling Group, RDS, SSM, Session Manager) la provisiona el usuario; el agente no ejecuta nada en AWS.
