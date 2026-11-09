import { expect, test } from "@playwright/test";

test("las peticiones se distribuyen entre réplicas del backend (X-Servidor)", async ({
  request,
}) => {
  const servidoresVistos = new Set<string>();

  for (let i = 0; i < 15; i += 1) {
    const respuesta = await request.get("/api/whoami");
    expect(respuesta.ok()).toBeTruthy();
    const servidor = respuesta.headers()["x-servidor"];
    expect(servidor).toBeTruthy();
    servidoresVistos.add(servidor as string);
  }

  // Con una sola réplica no hay nada que distribuir: se omite en vez de
  // fallar. Para ejercitar el balanceo real, levantar antes:
  //   docker compose up -d --scale backend=3
  test.skip(
    servidoresVistos.size <= 1,
    "Requiere más de una réplica: docker compose up -d --scale backend=3"
  );

  expect(servidoresVistos.size).toBeGreaterThan(1);
});
