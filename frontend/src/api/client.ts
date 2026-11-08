export let ultimoServidor: string | null = null;

const escuchas = new Set<(servidor: string | null) => void>();

export function suscribirseServidor(fn: (servidor: string | null) => void): () => void {
  escuchas.add(fn);
  return () => escuchas.delete(fn);
}

function notificarServidor(): void {
  for (const fn of escuchas) fn(ultimoServidor);
}

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : JSON.stringify(detail));
    this.status = status;
    this.detail = detail;
  }
}

async function solicitar<T>(metodo: string, ruta: string, cuerpo?: unknown): Promise<T> {
  const opciones: RequestInit = {
    method: metodo,
    credentials: "include",
  };
  if (cuerpo !== undefined) {
    opciones.headers = { "Content-Type": "application/json" };
    opciones.body = JSON.stringify(cuerpo);
  }

  const respuesta = await fetch(`/api${ruta}`, opciones);

  const servidor = respuesta.headers.get("x-servidor");
  if (servidor) {
    ultimoServidor = servidor;
    notificarServidor();
  }

  if (respuesta.status === 204) {
    return undefined as T;
  }

  const texto = await respuesta.text();
  const datos = texto ? JSON.parse(texto) : undefined;

  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, datos?.detail ?? datos ?? respuesta.statusText);
  }
  return datos as T;
}

export const api = {
  get: <T>(ruta: string): Promise<T> => solicitar<T>("GET", ruta),
  post: <T>(ruta: string, cuerpo?: unknown): Promise<T> => solicitar<T>("POST", ruta, cuerpo ?? {}),
  put: <T>(ruta: string, cuerpo?: unknown): Promise<T> => solicitar<T>("PUT", ruta, cuerpo ?? {}),
  delete: <T>(ruta: string): Promise<T> => solicitar<T>("DELETE", ruta),
};
