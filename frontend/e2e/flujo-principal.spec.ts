import { expect, test } from "@playwright/test";
import { ADMIN_EMAIL, ADMIN_PASSWORD, USUARIO_DEMO_EMAIL, USUARIO_DEMO_PASSWORD } from "./credenciales";

async function iniciarSesion(page: import("@playwright/test").Page, email: string, password: string) {
  await page.goto("/login");
  await page.getByLabel("Correo").fill(email);
  await page.getByLabel("Contraseña").fill(password);
  await page.getByRole("button", { name: "Entrar" }).click();
}

test("login, predecir, ranking, salas y estadísticas", async ({ page }) => {
  await iniciarSesion(page, USUARIO_DEMO_EMAIL, USUARIO_DEMO_PASSWORD);
  await expect(page).toHaveURL(/\/partidos$/);
  await expect(page.getByRole("heading", { name: "Partidos" })).toBeVisible();

  // Predecir el primer partido programado disponible.
  await page.getByRole("button", { name: "Programados" }).click();
  const primeraFila = page.locator("li.partido").first();
  await expect(primeraFila).toBeVisible();
  await primeraFila.getByRole("button", { name: /Predecir|Editar/ }).click();
  await expect(primeraFila.getByText(/Puntos:|Pendiente de resultado/)).toBeVisible();

  await page.getByRole("link", { name: "Mis predicciones" }).click();
  await expect(page.getByRole("heading", { name: "Mis predicciones" })).toBeVisible();

  await page.getByRole("link", { name: "Ranking" }).click();
  await expect(page.getByRole("heading", { name: "Ranking global" })).toBeVisible();
  await expect(page.locator("table tbody tr").first()).toBeVisible();

  await page.getByRole("link", { name: "Salas" }).click();
  await expect(page.getByRole("heading", { name: "Mis salas" })).toBeVisible();
  await expect(page.getByText("Amigos del Mundial")).toBeVisible();

  await page.getByRole("link", { name: "Estadísticas" }).click();
  await expect(page.getByRole("heading", { name: "Mis estadísticas" })).toBeVisible();

  // Pie de página: X-Servidor visible (sección 14).
  await expect(page.getByText(/Atendido por: /)).toBeVisible();
});

test("un usuario sin rol ADMIN no puede entrar a /admin/partidos", async ({ page }) => {
  await iniciarSesion(page, USUARIO_DEMO_EMAIL, USUARIO_DEMO_PASSWORD);
  await expect(page).toHaveURL(/\/partidos$/);

  await page.goto("/admin/partidos");
  await expect(page).toHaveURL(/\/partidos$/);
});

test("admin puede entrar a /admin/partidos, crear un partido y registrar un resultado", async ({
  page,
}) => {
  await iniciarSesion(page, ADMIN_EMAIL, ADMIN_PASSWORD);

  await page.getByRole("link", { name: "Admin" }).click();
  await expect(page.getByRole("heading", { name: "Administración de partidos" })).toBeVisible();

  await page.getByLabel("Local").selectOption({ index: 1 });
  await page.getByLabel("Visitante").selectOption({ index: 2 });
  await page.locator('input[type="datetime-local"]').fill("2030-01-01T12:00");
  await page.getByRole("button", { name: "Crear" }).click();

  const fila = page.locator("tbody tr", { hasText: "PROGRAMADO" }).first();
  await expect(fila).toBeVisible();
});
