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

## T3–T5

Pendientes.
