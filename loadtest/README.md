# Escenario de estrés (Locust) — sección 17.2

`locustfile.py` simula usuarios reales del juego: cada uno inicia sesión
como `cargaNNN` y repite, con pesos, las acciones más comunes:

| Tarea | Peso |
|---|---|
| Listar partidos (`GET /api/partidos`) | 5 |
| Ranking global (`GET /api/ranking`) | 3 |
| Predecir un partido `PROGRAMADO` al azar (`PUT /api/partidos/{id}/prediccion`) | 2 |
| Ranking de una sala (`GET /api/salas/{id}/ranking`) | 2 |
| Estadísticas propias (`GET /api/estadisticas/mias`) | 1 |

El endpoint de análisis con IA queda **fuera** del estrés (sección 10).

## Preparar los usuarios de carga

El seed crea `carga001`...`cargaNNN` solo si `SEED_USUARIOS_CARGA > 0`.
En `backend/.env`:

```
SEED_USUARIOS_CARGA=50
CARGA_PASSWORD=una-contrasena-cualquiera-de-prueba
```

y luego reseed:

```bash
docker compose run --rm migrate sh -c "alembic upgrade head && python -m app.seed --reiniciar"
```

Todos los usuarios de carga quedan como miembros de una sala llamada
"Carga" (creada por el propio seed), así la tarea de ranking de sala
tiene algo real que consultar.

## Correr localmente (T4): 1 backend vs. 3 backends

```bash
pip install -r loadtest/requirements.txt
```

Contra 1 backend:

```bash
docker compose up -d --scale backend=1
locust -f loadtest/locustfile.py --host http://localhost:8080 \
  --headless -u 50 -r 10 -t 2m \
  --csv docs/locust-1-backend --html docs/locust-1-backend.html
```

Contra 3 backends (esperar ~10 s tras escalar, por el TTL del resolver
de nginx):

```bash
docker compose up -d --scale backend=3
locust -f loadtest/locustfile.py --host http://localhost:8080 \
  --headless -u 50 -r 10 -t 2m \
  --csv docs/locust-3-backends --html docs/locust-3-backends.html
```

`-u` = usuarios concurrentes, `-r` = tasa de arranque (usuarios/segundo),
`-t` = duración. Los resultados (RPS, latencias p50/p95/p99, % de
errores) quedan en `docs/locust-*.html` y `docs/locust-*_stats.csv`, y
se comparan en `docs/PRUEBAS.md`.

## En AWS (Etapa 4 — la ejecuta el usuario)

Mismo `locustfile.py`, apuntando al DNS del ALB, desde el PC del usuario
(respaldo: AWS CloudShell), 10–12 minutos, para observar el
escalamiento de 2 a 3 instancias por `ALBRequestCountPerTarget`.
`docs/PRUEBAS.md` tiene una sección reservada para esos resultados.
