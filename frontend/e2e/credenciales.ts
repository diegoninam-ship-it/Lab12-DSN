// Credenciales de prueba. Las del admin se leen de backend/.env (nunca
// se versionan); las demo vienen del seed (backend/app/seed.py), que sí
// está versionado, así que no son un secreto.
export const ADMIN_EMAIL = process.env.ADMIN_EMAIL ?? "admin@example.com";
export const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD ?? "cambia-esta-password";

export const USUARIO_DEMO_EMAIL = "exacto1@demo-mundial.com";
export const USUARIO_DEMO_PASSWORD = "Demo12345";
