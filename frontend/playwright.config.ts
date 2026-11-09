import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { defineConfig, devices } from "@playwright/test";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

try {
  // Credenciales de ADMIN_EMAIL/ADMIN_PASSWORD para las pruebas que
  // inician sesión como admin (nunca se versionan en el código de
  // prueba). Si no existe backend/.env (por ejemplo en CI sin ese
  // archivo), se usan los valores de ejemplo de backend/.env.example.
  process.loadEnvFile(path.resolve(__dirname, "../backend/.env"));
} catch {
  // Sin backend/.env disponible: los tests caen en sus valores por defecto.
}

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  reporter: "html",
  use: {
    baseURL: "http://localhost:8080",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
