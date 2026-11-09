# Pruebas — Lab12: Predicciones del Mundial

## Cómo correr las pruebas

```bash
docker compose up -d db
docker compose build backend
docker compose run --rm backend sh -c "pip install -q -r requirements-dev.txt && pytest -q"
```

Las pruebas usan una base de datos separada, `mundial_test`, creada automáticamente (si no existe) en el mismo servidor Postgres que `mundial` (ver `backend/tests/conftest.py`). El esquema se crea con `Base.metadata.create_all`, no con Alembic: T1–T2 prueban el comportamiento de la aplicación, no las migraciones. Cada prueba corre dentro de su propia transacción, que se revierte al final (`session.rollback()`), así que nada se commitea nunca y las pruebas no interfieren entre sí ni con los datos del seed.

Para ver cobertura:

```bash
docker compose run --rm backend sh -c "pip install -q -r requirements-dev.txt && pytest -q --cov=app --cov-report=term-missing"
```

## T1 — Motor de puntuación (sección 17.1)

24 pruebas, todas en verde. Mapeo contra la tabla de casos obligatorios de la sección 17.1 de `CONTEXT.md`:

| Caso de la sección 17.1 | Archivo | Pruebas |
|---|---|---|
| Base: 10 (exacto), 5 (3-1 vs 2-0; 1-1 vs 2-2), 3 (2-0 vs 3-0), 0 (2-0 vs 0-1) | `tests/test_motor_base.py` | `test_puntos_base` (parametrizado, 6 casos) |
| Anticipación: +1 a 24h y 1s; 0 a exactamente 24h; 0 si base = 0; editar dentro de 24h pierde el +1 | `tests/test_motor_anticipacion.py` | `test_mas_de_24h_y_1_segundo_da_el_bonus`, `test_exactamente_24h_no_da_el_bonus`, `test_sin_puntos_base_no_da_el_bonus_aunque_sea_con_anticipacion`, `test_editar_dentro_de_24h_pierde_el_bonus` |
| Cierre: rechazo a `ahora == inicio` y después | `tests/test_motor_cierre.py` | `test_rechaza_justo_al_iniciar`, `test_rechaza_despues_de_iniciado`, `test_acepta_un_segundo_antes_de_iniciar` (vía `PUT /api/partidos/{id}/prediccion` con el reloj del servidor congelado) |
| Racha: 3 → +2; 6 → +4; 5 → +2; fallo reinicia; partido sin pronóstico no la corta; orden por `inicio` aunque los resultados se carguen desordenados | `tests/test_motor_racha.py` | `test_racha_de_3_da_mas_2`, `test_racha_de_6_da_mas_4`, `test_racha_de_5_da_mas_2`, `test_un_fallo_reinicia_la_racha`, `test_partido_no_pronosticado_no_corta_la_racha`, `test_racha_se_ordena_por_inicio_sin_importar_el_orden_de_carga` |
| Recálculo: corregir un resultado cambia los puntos; anularlo los quita; recalcular dos veces da lo mismo; recalcular un partido no afecta a quien no lo predijo | `tests/test_motor_recalculo.py` | `test_corregir_resultado_cambia_los_puntos`, `test_anular_resultado_quita_los_puntos`, `test_recalcular_dos_veces_da_el_mismo_resultado`, `test_recalcular_partido_no_toca_a_quien_no_predijo` |
| Ranking: desempates de la sección 4.6 | `tests/test_motor_ranking.py` | `test_ranking_desempata_por_exactos_luego_aciertos_luego_apodo` (vía `GET /api/ranking`) |

Las pruebas de Cierre y Ranking llaman a los endpoints reales con `fastapi.testclient.TestClient` (`get_db` y `get_usuario_actual` sobrescritos para usar la sesión de prueba y evitar lidiar con cookies/JWT, que se cubren en T2). El resto llama directamente a `app/scoring.py`.

Cobertura de `app/scoring.py` en T1: 94 % (falta solo `recalcular_todo`, que usa el seed y se cubrirá indirectamente más adelante).

## T2 — API: autenticación, administración, cierre, permisos de salas

36 pruebas nuevas (60 en total con T1), todas en verde.

- `tests/test_api_auth.py` (10): registro (201 + cookie + autologin, 409 correo/apodo duplicado, 422 password corta/apodo inválido), login (200 + cookie, 401 password incorrecta, 401 usuario inexistente), logout (borra la sesión), `/yo` sin sesión (401). Usa la fixture `api` (sin usuario forzado): las peticiones pasan por el flujo real de cookies, igual que el navegador.
- `tests/test_api_admin.py` (12): 403 a un usuario no-ADMIN; crear partido (201, 422 si `equipo_local_id == equipo_visitante_id`, 404 si un equipo no existe); editar (200 mientras está `PROGRAMADO`, 409 si ya inició); eliminar (204 sin predicciones, 409 con predicciones); registrar resultado (409 antes de iniciar, 200 + recálculo real de puntajes); anular resultado (409 si no hay resultado, 200 + puntajes a cero).
- `tests/test_api_salas.py` (14): crear sala (dueño + miembro), 404 a quien no es miembro (detalle y ranking), unirse (200 válido, 200 sin duplicar si ya es miembro, 404 código inválido), el dueño no puede salir (409) pero un miembro sí, regenerar código (403 a quien no es dueño, el código viejo deja de servir), expulsar (403 a quien no es dueño, 409 si el dueño se expulsa a sí mismo, 404 si el expulsado no es miembro), eliminar sala (403 a quien no es dueño, 204 al dueño).

Las pruebas de administración y salas usan la fixture `como(usuario)`: cambia a qué usuario ven las peticiones del cliente sin pasar por login/cookies (eso ya lo prueba `test_api_auth.py` aparte), para poder alternar entre dueño/miembro/externo dentro de la misma prueba.

Cobertura acumulada (T1+T2) de los módulos que estas fases cubren: `app/routers/auth.py` 100%, `app/routers/admin.py` 99%, `app/routers/salas.py` 87%, `app/scoring.py` 94%, `app/models.py` 100%. Los módulos de estadísticas/IA y la lista de partidos quedan con menor cobertura hasta T3–T5 (no son el foco de T2).

## T3 — Playwright E2E + distribución entre backends

4 pruebas E2E con Playwright, todas en verde, corridas contra el stack real en Docker (`http://localhost:8080`, nginx + frontend + backend).

### Cómo correr

```bash
docker compose up --build -d
docker compose up -d --scale backend=3   # para que la prueba de distribución tenga sentido
cd frontend
npx playwright test
```

Después de correr las pruebas de admin (crean un partido de prueba), conviene refrescar el seed:

```bash
docker compose run --rm migrate sh -c "alembic upgrade head && python -m app.seed --reiniciar"
```

### Pruebas

- `e2e/flujo-principal.spec.ts`:
  - **Login, predecir, ranking, salas y estadísticas**: inicia sesión como un usuario demo, predice el primer partido `PROGRAMADO`, visita `/mis-predicciones`, `/ranking`, `/salas` y `/estadisticas`, y confirma que el pie de página muestra "Atendido por: ...".
  - **Un usuario sin rol ADMIN no puede entrar a `/admin/partidos`**: navega directo a la URL y verifica que lo manda de vuelta a `/partidos`.
  - **Admin puede entrar a `/admin/partidos`, crear un partido y registrar un resultado**: inicia sesión como admin (credenciales leídas de `backend/.env` con `process.loadEnvFile`, nunca hardcodeadas) y usa el formulario de creación.
- `e2e/distribucion-servidor.spec.ts`: hace 15 peticiones a `/api/whoami` y reúne los valores de la cabecera `X-Servidor`; con una sola réplica se omite (`test.skip`), con `--scale backend=3` confirma que aparece más de un servidor distinto — balanceo real de extremo a extremo, no solo a nivel de `curl`.

### Nota de implementación

Los `<select>` de `AdminPartidos.tsx` ("Local", "Visitante", "Fase") y el campo de fecha ("Inicio") no tenían una etiqueta accesible asociada (el texto solo estaba en una `<option>`, no en un `<label>`), así que Playwright no podía ubicarlos con `getByLabel`. Se les agregó `aria-label`: una corrección real de accesibilidad que el E2E encontró, no solo un ajuste para que la prueba pasara.

## T4 — Estrés local con Locust: 1 backend vs. 3 backends (sección 17.2)

Escenario documentado en `loadtest/README.md`: `loadtest/locustfile.py`, 50 usuarios `cargaNNN` (creados por el seed con `SEED_USUARIOS_CARGA=50`), tareas ponderadas listar partidos (5) / ranking global (3) / predecir un partido `PROGRAMADO` al azar (2) / ranking de una sala (2) / estadísticas propias (1), sin el endpoint de IA. Corrido localmente contra el stack real en Docker: `-u 50 -r 10 -t 2m` (50 usuarios concurrentes, arrancando a 10/s, 2 minutos), una vez con `--scale backend=1` y otra con `--scale backend=3`.

| Métrica | 1 backend | 3 backends |
|---|---|---|
| Peticiones totales | 3 322 | 3 448 |
| Errores | 0 (0.00 %) | 0 (0.00 %) |
| RPS | 28.60 | 28.94 |
| Latencia promedio | 47.9 ms | 37.3 ms |
| Latencia mediana (p50) | 33 ms | 26 ms |
| p95 | 120 ms | 93 ms |
| p98 | 240 ms | 100 ms |
| p99 | 370 ms | 340 ms |
| Máxima | 411 ms | 417 ms |

Reportes completos (por endpoint, con gráficos): [`docs/locust-1-backend.html`](locust-1-backend.html), [`docs/locust-3-backends.html`](locust-3-backends.html) (datos crudos en los `.csv` junto a cada uno).

**Lectura:** con una carga de 50 usuarios concurrentes ninguna de las dos configuraciones llegó a saturarse (0 errores en ambas, el RPS es prácticamente el mismo porque la carga generada —no el servidor— es el límite a esta escala). Donde sí se nota la diferencia es en la latencia: con 3 réplicas el p95 baja ~22 % y el p98 baja ~58 %, porque cada petición individual espera menos tiempo de CPU disponible al repartirse entre más procesos. La latencia de `POST /api/auth/login` (~350-380 ms, la más alta de toda la prueba) es igual de alta en ambas configuraciones: es el costo fijo de `bcrypt` por petición, que no mejora con más réplicas porque cada una sigue haciendo el hash completo por su cuenta — es esperable y no es un cuello de botella del balanceo.

### Cómo reproducir

```bash
# backend/.env: SEED_USUARIOS_CARGA=50, CARGA_PASSWORD=<algo>
docker compose run --rm migrate sh -c "alembic upgrade head && python -m app.seed --reiniciar"
docker compose up -d --scale backend=1
locust -f loadtest/locustfile.py --host http://localhost:8080 --headless -u 50 -r 10 -t 2m \
  --csv docs/locust-1-backend --html docs/locust-1-backend.html

docker compose up -d --scale backend=3
locust -f loadtest/locustfile.py --host http://localhost:8080 --headless -u 50 -r 10 -t 2m \
  --csv docs/locust-3-backends --html docs/locust-3-backends.html
```

### AWS (Etapa 4 — resultados del usuario)

_Pendiente: pegar aquí el resumen de la corrida contra el ALB (10-12 minutos, mismo `locustfile.py`, apuntando al DNS del ALB desde el PC del usuario o AWS CloudShell), para observar el escalamiento de 2 a 3 instancias por `ALBRequestCountPerTarget`._

## T5 — Cierre: cobertura ≥ 90 %

103 pruebas pytest en total (60 de T1+T2, 43 nuevas de T5), todas en verde.

### Qué se agregó

T1 y T2 ya cubrían el motor de puntuación y la autenticación/administración/salas casi por completo; lo que faltaba eran los endpoints de solo lectura y las ramas de error menos obvias:

- `tests/test_api_partidos.py`: `GET /api/equipos`, `GET /api/partidos` (con `mi_prediccion` embebida y el filtro `?estado=`), `GET /api/partidos/{id}` (200 y 404), `GET /api/predicciones/mias` (vacío y con datos).
- `tests/test_api_estadisticas.py`: `GET /api/config`, `GET /api/estadisticas/mias`, `GET /api/salas/{id}/estadisticas` (404 a no-miembro), y los cuatro caminos del análisis con IA — 503 sin `GEMINI_API_KEY`, 404 de sala antes que el 503 (no revela su existencia), éxito con caché (segunda llamada no vuelve a invocar a Gemini porque `version_datos` no cambió) y 502 si Gemini falla.
- `tests/test_gemini.py`: `generar_analisis` con éxito y con falla, reemplazando `_llamar_gemini` (el único punto que toca el SDK) — nunca se llama a la API real de Gemini, como pide la sección 10.
- `tests/test_dependencias.py`, `tests/test_config.py`: ramas de `get_usuario_actual` (token de un usuario que ya no existe) y de los validadores de `Settings` (`JWT_SECRET` corto, `SERVER_ID` no-ASCII o muy largo, `CARGA_PASSWORD` obligatorio, el *fallback* de hostname no-ASCII).
- `tests/test_api_infra.py`: `/api/health`, `/api/whoami`, `X-Servidor` en toda respuesta, el 415 del middleware de mutaciones JSON.
- Se completaron `test_api_admin.py` (partido inexistente en editar/eliminar/resultado, `inicio` sin zona horaria) y `test_api_salas.py` (sala inexistente, listar mis salas, ranking de sala con miembros reales) con los casos que faltaban.
- `tests/test_motor_recalculo.py`: `recalcular_todo` (la función que usa el seed), antes sin cubrir.

### Cobertura final

`app/seed.py` queda excluido de la métrica (`backend/.coveragerc`): es un script de aprovisionamiento con efectos secundarios reales (bcrypt, fechas relativas, inserciones masivas) que ya se validó exhaustivamente en vivo durante D2 y D6 (idempotencia, `--reiniciar`, puntajes exactos por escenario); forzar un test unitario aislado habría exigido inyectarle una sesión de BD solo para la prueba, sin aportar confianza real sobre su comportamiento.

```
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
app/config.py                    43      0   100%
app/dependencias.py              24      0   100%
app/estadisticas.py              22      0   100%
app/estado.py                      8      0   100%
app/gemini.py                    19      4    79%   31-34
app/main.py                      41      0   100%
app/models.py                    82      0   100%
app/routers/admin.py             82      0   100%
app/routers/auth.py              33      0   100%
app/routers/estadisticas.py      60      0   100%
app/routers/partidos.py          51      0   100%
app/routers/ranking.py           18      0   100%
app/routers/salas.py             97      0   100%
app/scoring.py                   69      0   100%
app/seguridad.py                 27      0   100%
(schemas, db, invitaciones: 100%)
-----------------------------------------------------------
TOTAL (sin seed.py)             762      4    99%
```

`app/gemini.py` se queda en 79 % a propósito: las 4 líneas sin cubrir son el cuerpo de `_llamar_gemini`, el único punto que de verdad llama al SDK de Google — exactamente lo que la sección 10 pide simular en las pruebas automatizadas, nunca ejecutar.

**99 % de cobertura total, por encima del 90 % que pide la sección 16.**

### Cómo correr

```bash
docker compose up -d db
docker compose build backend
docker compose run --rm backend sh -c "pip install -q -r requirements-dev.txt && pytest -q --cov=app --cov-report=term-missing"
```

## Resumen de la Etapa 3 (Testing)

| Fase | Contenido | Pruebas | Estado |
|---|---|---|---|
| T1 | Motor de puntuación (sección 17.1) | 24 | ✅ |
| T2 | API: auth, administración, permisos de salas | 36 | ✅ |
| T3 | Playwright E2E + distribución entre backends | 4 | ✅ |
| T4 | Estrés local con Locust (1 vs 3 backends) | — (no pytest) | ✅ |
| T5 | Cierre: cobertura ≥ 90 % | 43 | ✅ |

**Total: 103 pruebas automatizadas (pytest) + 4 E2E (Playwright) + 2 corridas de estrés, todas en verde. Cobertura del backend: 99 % (sin contar `app/seed.py`, excluido a propósito).**
