"""Escenario de estrés (sección 17.2). Cada usuario virtual inicia sesión
como un carga001..cargaNNN (creados por el seed con SEED_USUARIOS_CARGA >
0 y CARGA_PASSWORD) y repite, con pesos, las tareas de un usuario real:

    listar partidos (5), ranking global (3), predecir un partido
    programado al azar (2), ranking de una sala (2), estadísticas
    propias (1). Sin el endpoint de IA (fuera del estrés, sección 10).

Uso:
    locust -f loadtest/locustfile.py --host http://localhost:8080
"""

import itertools
import os
import random

from locust import HttpUser, between, task

NUMERO_USUARIOS_CARGA = int(os.environ.get("NUMERO_USUARIOS_CARGA", "50"))
CARGA_PASSWORD = os.environ.get("CARGA_PASSWORD", "")

_contador_apodos = itertools.count(1)


class UsuarioCarga(HttpUser):
    wait_time = between(1, 3)

    def on_start(self) -> None:
        numero = next(_contador_apodos)
        apodo_num = ((numero - 1) % NUMERO_USUARIOS_CARGA) + 1
        email = f"carga{apodo_num:03d}@carga-mundial.com"
        self.sala_id: int | None = None

        with self.client.post(
            "/api/auth/login",
            json={"email": email, "password": CARGA_PASSWORD},
            name="/api/auth/login",
            catch_response=True,
        ) as respuesta:
            if respuesta.status_code != 200:
                respuesta.failure(f"login falló ({respuesta.status_code}): {email}")
                return

        respuesta_salas = self.client.get("/api/salas", name="/api/salas (on_start)")
        if respuesta_salas.status_code == 200:
            salas = respuesta_salas.json()
            if salas:
                self.sala_id = salas[0]["id"]

    @task(5)
    def listar_partidos(self) -> None:
        self.client.get("/api/partidos", name="/api/partidos")

    @task(3)
    def ranking_global(self) -> None:
        self.client.get("/api/ranking", name="/api/ranking")

    @task(2)
    def predecir_partido_programado(self) -> None:
        respuesta = self.client.get(
            "/api/partidos?estado=PROGRAMADO", name="/api/partidos?estado=PROGRAMADO"
        )
        if respuesta.status_code != 200:
            return
        partidos = respuesta.json()
        if not partidos:
            return
        partido = random.choice(partidos)
        self.client.put(
            f"/api/partidos/{partido['id']}/prediccion",
            json={"goles_local": random.randint(0, 4), "goles_visitante": random.randint(0, 4)},
            name="/api/partidos/[id]/prediccion",
        )

    @task(2)
    def ranking_de_sala(self) -> None:
        if self.sala_id is None:
            return
        self.client.get(f"/api/salas/{self.sala_id}/ranking", name="/api/salas/[id]/ranking")

    @task(1)
    def estadisticas_propias(self) -> None:
        self.client.get("/api/estadisticas/mias", name="/api/estadisticas/mias")
